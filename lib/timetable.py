"""Timetable snapshots: which week to fetch, when, and how it is stored.

Standard library only, so it can be tested without the app's dependencies.
Design: docs/superpowers/specs/2026-09-28-timetable-snapshots-design.md
"""
import json
import os
import re
import shutil
from datetime import datetime, timedelta

# from this hour on Friday the weekend is near enough to want next week
NEXT_WEEK_FROM_FRIDAY_HOUR = 15
RETRY_SECONDS = 30 * 60

MALFORMED = "Synergia returned an unexpected timetable."
UNREACHABLE = "Could not reach Synergia."

# same rule registration enforces; usernames become directory names
USERNAME_RE = re.compile("[a-z0-9]+")


class TimetableError(Exception):
	"""A fetch failed; str(e) is what ends up in tt_last_error."""


def target_week(now):
	monday = now.date() - timedelta(days = now.weekday())
	if now.weekday() >= 5 or (now.weekday() == 4 and now.hour >= NEXT_WEEK_FROM_FRIDAY_HOUR):
		monday += timedelta(days = 7)
	return monday


def last_slot(now, hours):
	today = [now.replace(hour = h, minute = 0, second = 0, microsecond = 0) for h in hours]
	past = [slot for slot in today if slot <= now]
	if past:
		return max(past)
	return now.replace(hour = max(hours), minute = 0, second = 0, microsecond = 0) - timedelta(days = 1)


def needs_fetch(last_ok, now, hours):
	if not last_ok:
		return True
	try:
		last = datetime.fromisoformat(last_ok)
	except (TypeError, ValueError):
		return True
	if last.tzinfo is not None:
		# stored with an offset, compared in the process's local time
		last = last.astimezone().replace(tzinfo = None)
	return last < last_slot(now, hours)


def week_dates(week_start):
	return [(week_start + timedelta(days = i)).isoformat() for i in range(7)]


def _ref_id(e, field):
	# lesson entries carry ids as strings, the lookup maps use ints
	ref = e.get(field)
	if not ref or "Id" not in ref:
		return None
	return int(ref["Id"])


def _teacher_name(teacher):
	if not teacher:
		return None
	return ("%s %s" % (teacher.get("FirstName", ""), teacher.get("LastName", ""))).strip() or None


def _parse_lesson(date_str, e, classrooms, subjects, teachers):
	room = _ref_id(e, "Classroom")
	if e["IsCanceled"]:
		status = "cancelled"
	elif e["IsSubstitutionClass"]:
		status = "substitution"
	else:
		status = "normal"
	lesson = {
		"key": "%s:%s" % (e["TimetableEntry"]["Id"], date_str),
		"date": date_str,
		"start": e["HourFrom"],
		"end": e["HourTo"],
		"lesson_no": int(e["LessonNo"]),
		"subject": e["Subject"]["Name"],
		"teacher": _teacher_name(e["Teacher"]),
		"classroom": classrooms.get(room) if room is not None else None,
		"group": e.get("VirtualClassName"),
		"status": status,
		"note": e.get("SubstitutionNote"),
		"original": None
	}
	if status != "normal":
		org_subject = _ref_id(e, "OrgSubject")
		org_teacher = _ref_id(e, "OrgTeacher")
		org_room = _ref_id(e, "OrgClassroom")
		lesson["original"] = {
			"subject": subjects.get(org_subject) if org_subject is not None else lesson["subject"],
			"teacher": _teacher_name(teachers.get(org_teacher)) if org_teacher is not None else lesson["teacher"],
			"classroom": classrooms.get(org_room) if org_room is not None else lesson["classroom"],
			"date": e.get("OrgDate", date_str),
			"start": e.get("OrgHourFrom", lesson["start"]),
			"end": e.get("OrgHourTo", lesson["end"]),
			"lesson_no": int(e["OrgLessonNo"]) if "OrgLessonNo" in e else lesson["lesson_no"]
		}
	return lesson


def parse_week(timetable, week_start, classrooms, subjects, teachers):
	dates = week_dates(week_start)
	days = timetable.get("Timetable") if isinstance(timetable, dict) else None
	# anything but exactly the requested week must not replace a stored one
	if not isinstance(days, dict) or sorted(days) != dates:
		raise TimetableError(MALFORMED)
	lessons = []
	try:
		for date_str in dates:
			for slot in days[date_str] or []:
				for e in slot or []:
					lessons.append(_parse_lesson(date_str, e, classrooms, subjects, teachers))
	except (AttributeError, KeyError, TypeError, ValueError):
		raise TimetableError(MALFORMED)
	lessons.sort(key = lambda lesson: (lesson["date"], lesson["start"]))
	return lessons


async def fetch_week(lib, week_start):
	"""Fetch and parse one week through a logged-in Librus client."""
	week = await lib.get_data("Timetables?weekStart=%s" % week_start.isoformat())
	rooms = await lib.get_data("Classrooms")
	subjects = await lib.get_subjects()
	teachers = await lib.get_teachers()
	# a week with blank rooms or names would make calendar events flicker,
	# so any missing piece fails the whole fetch
	if week is None or rooms is None or subjects is None or teachers is None:
		raise TimetableError(UNREACHABLE)
	try:
		classrooms = {int(room["Id"]): room["Symbol"] for room in rooms["Classrooms"]}
	except (KeyError, TypeError, ValueError):
		raise TimetableError(MALFORMED)
	return parse_week(week, week_start, classrooms, subjects, teachers)


def user_dir(base, username):
	if not isinstance(username, str) or not USERNAME_RE.fullmatch(username):
		raise ValueError("unsafe username: %r" % (username,))
	return os.path.join(base, username)


def _week_path(directory, week_start):
	return os.path.join(directory, "%s.json" % week_start.isoformat())


def save_week(directory, week_start, lessons, fetched_at):
	os.makedirs(directory, exist_ok = True)
	path = _week_path(directory, week_start)
	tmp = path + ".tmp"
	snapshot = {
		"week_start": week_start.isoformat(),
		"fetched_at": fetched_at.isoformat(timespec = "seconds"),
		"lessons": lessons
	}
	try:
		with open(tmp, "w", encoding = "utf-8") as f:
			json.dump(snapshot, f, ensure_ascii = False, indent = 2)
		# a crash mid-write must never leave a truncated week in place
		os.replace(tmp, path)
	except:
		if os.path.exists(tmp):
			os.remove(tmp)
		raise


def load_week(directory, week_start):
	try:
		with open(_week_path(directory, week_start), encoding = "utf-8") as f:
			return json.load(f)
	except FileNotFoundError:
		return None


def delete_user(base, username):
	try:
		directory = user_dir(base, username)
	except ValueError:
		# nothing can have been stored under a name user_dir refuses
		return
	shutil.rmtree(directory, ignore_errors = True)
