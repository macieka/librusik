import unittest
from datetime import date, datetime

from lib.timetable import last_slot, needs_fetch, target_week


HOURS = [12, 18]


class TargetWeekTest(unittest.TestCase):
	def check(self, now, monday):
		self.assertEqual(target_week(now), monday)

	def test_monday_morning_is_current_week(self):
		self.check(datetime(2026, 9, 28, 9, 0), date(2026, 9, 28))

	def test_thursday_evening_is_current_week(self):
		self.check(datetime(2026, 10, 1, 18, 0), date(2026, 9, 28))

	def test_friday_before_cutoff_is_current_week(self):
		self.check(datetime(2026, 10, 2, 14, 59), date(2026, 9, 28))

	def test_friday_at_cutoff_is_next_week(self):
		self.check(datetime(2026, 10, 2, 15, 0), date(2026, 10, 5))

	def test_saturday_is_next_week(self):
		self.check(datetime(2026, 10, 3, 12, 0), date(2026, 10, 5))

	def test_sunday_night_is_next_week(self):
		self.check(datetime(2026, 10, 4, 23, 59), date(2026, 10, 5))

	def test_monday_midnight_is_that_week(self):
		self.check(datetime(2026, 10, 5, 0, 0), date(2026, 10, 5))


class LastSlotTest(unittest.TestCase):
	def test_before_first_slot_is_yesterdays_last(self):
		self.assertEqual(last_slot(datetime(2026, 9, 28, 11, 59), HOURS), datetime(2026, 9, 27, 18, 0))

	def test_exactly_on_a_slot(self):
		self.assertEqual(last_slot(datetime(2026, 9, 28, 12, 0), HOURS), datetime(2026, 9, 28, 12, 0))

	def test_between_slots(self):
		self.assertEqual(last_slot(datetime(2026, 9, 28, 15, 30), HOURS), datetime(2026, 9, 28, 12, 0))

	def test_after_last_slot(self):
		self.assertEqual(last_slot(datetime(2026, 9, 28, 23, 0), HOURS), datetime(2026, 9, 28, 18, 0))

	def test_hours_in_any_order(self):
		self.assertEqual(last_slot(datetime(2026, 9, 28, 13, 0), [18, 12]), datetime(2026, 9, 28, 12, 0))


class NeedsFetchTest(unittest.TestCase):
	NOW = datetime(2026, 9, 28, 12, 5)

	def test_never_fetched(self):
		self.assertTrue(needs_fetch(None, self.NOW, HOURS))

	def test_fetched_before_last_slot(self):
		self.assertTrue(needs_fetch("2026-09-28T11:59:00", self.NOW, HOURS))

	def test_fetched_after_last_slot(self):
		self.assertFalse(needs_fetch("2026-09-28T12:01:00", self.NOW, HOURS))

	def test_timestamp_with_offset(self):
		after = datetime(2026, 9, 28, 12, 1).astimezone().isoformat(timespec = "seconds")
		before = datetime(2026, 9, 28, 11, 0).astimezone().isoformat(timespec = "seconds")
		self.assertFalse(needs_fetch(after, self.NOW, HOURS))
		self.assertTrue(needs_fetch(before, self.NOW, HOURS))

	def test_unparseable_is_due(self):
		self.assertTrue(needs_fetch("garbage", self.NOW, HOURS))


if __name__ == "__main__":
	unittest.main()
