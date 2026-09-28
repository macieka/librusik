"""Timetable snapshots: which week to fetch, when, and how it is stored.

Standard library only, so it can be tested without the app's dependencies.
Design: docs/superpowers/specs/2026-09-28-timetable-snapshots-design.md
"""
from datetime import datetime, timedelta

# from this hour on Friday the weekend is near enough to want next week
NEXT_WEEK_FROM_FRIDAY_HOUR = 15
RETRY_SECONDS = 30 * 60


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
