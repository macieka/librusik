"""Timetable snapshots: which week to fetch, when, and how it is stored.

Standard library only, so it can be tested without the app's dependencies.
Design: docs/superpowers/specs/2026-09-28-timetable-snapshots-design.md
"""
from datetime import datetime, timedelta

# from this hour on Friday the weekend is near enough to want next week
NEXT_WEEK_FROM_FRIDAY_HOUR = 15
RETRY_SECONDS = 30 * 60

MALFORMED = "Synergia returned an unexpected timetable."
UNREACHABLE = "Could not reach Synergia."


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
