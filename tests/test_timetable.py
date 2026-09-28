import unittest
from datetime import date, datetime

from lib.timetable import MALFORMED, TimetableError, last_slot, needs_fetch, parse_week, target_week


HOURS = [12, 18]

WEEK = date(2026, 9, 28)

# invented names; the ids and shapes follow a real Timetables response
CLASSROOMS = {30018: "M18", 30019: "M44", 30022: "M22", 30031: "SG4"}
SUBJECTS = {42573: "Język polski", 42575: "Wychowanie fizyczne", 42576: "Matematyka", 42577: "Przyroda"}
TEACHERS = {
	1001: {"FirstName": "Anna", "LastName": "Nowak"},
	1002: {"FirstName": "Jan", "LastName": "Kowalski"},
	1003: {"FirstName": "Ewa", "LastName": "Wiśniewska"},
	1004: {"FirstName": "Piotr", "LastName": "Zieliński"},
}


def ref(id_):
	return {"Id": str(id_), "Url": "https://api.librus.pl/2.0/Things/%s" % id_}


def entry(entry_id, lesson_no, hours, subject_id, teacher_id, classroom_id = None, **extra):
	teacher = TEACHERS[teacher_id]
	e = {
		"Lesson": ref(5000000 + entry_id),
		"DateFrom": "2026-09-02",
		"DateTo": "2027-06-24",
		"LessonNo": str(lesson_no),
		"TimetableEntry": ref(entry_id),
		"DayNo": "1",
		"Subject": {"Id": str(subject_id), "Name": SUBJECTS[subject_id], "Short": "x", "Url": "u"},
		"Teacher": {"Id": str(teacher_id), "FirstName": teacher["FirstName"], "LastName": teacher["LastName"], "Url": "u"},
		"Class": {"Id": 1, "Url": "u"},
		"IsSubstitutionClass": False,
		"IsCanceled": False,
		"SubstitutionNote": None,
		"HourFrom": hours[0],
		"HourTo": hours[1],
	}
	if classroom_id is not None:
		e["Classroom"] = ref(classroom_id)
	e.update(extra)
	return e


def week_response():
	normal = entry(659881, 1, ("07:45", "08:30"), 42576, 1001, 30019)
	substitution = entry(341434, 4, ("10:20", "11:05"), 42576, 1001,
		IsSubstitutionClass = True,
		OrgDate = "2026-09-28", OrgLessonNo = "4", OrgHourFrom = "10:20", OrgHourTo = "11:05",
		OrgLesson = ref(5478630), OrgSubject = ref(42577), OrgTeacher = ref(1002), OrgClassroom = ref(30018),
		SubstitutionClassUrl = "https://api.librus.pl/2.0/SubstitutionClass/1")
	group = entry(383777, 6, ("12:15", "13:00"), 42575, 1004, 30031,
		VirtualClass = {"Id": 2163862, "Url": "u"}, VirtualClassName = "4a1")
	cancelled = entry(650336, 2, ("08:35", "09:20"), 42573, 1003, 30022, IsCanceled = True)
	return {
		"Timetable": {
			"2026-09-28": [[], [normal], [], [], [substitution], [], [group]],
			"2026-09-29": [[], [], [cancelled]],
			"2026-09-30": [],
			"2026-10-01": [],
			"2026-10-02": [],
			"2026-10-03": [],
			"2026-10-04": [],
		},
		"Pages": {"Next": "n", "Prev": "p"},
		"Resources": {},
		"Url": "u",
	}


def empty_week():
	return {"Timetable": {d: [] for d in ["2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04"]}}


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


class ParseWeekTest(unittest.TestCase):
	def parse(self, response = None):
		return parse_week(response if response is not None else week_response(), WEEK, CLASSROOMS, SUBJECTS, TEACHERS)

	def by_key(self):
		return {lesson["key"]: lesson for lesson in self.parse()}

	def test_normal_lesson(self):
		self.assertEqual(self.by_key()["659881:2026-09-28"], {
			"key": "659881:2026-09-28",
			"date": "2026-09-28",
			"start": "07:45",
			"end": "08:30",
			"lesson_no": 1,
			"subject": "Matematyka",
			"teacher": "Anna Nowak",
			"classroom": "M44",
			"group": None,
			"status": "normal",
			"note": None,
			"original": None,
		})

	def test_substitution_keeps_original(self):
		lesson = self.by_key()["341434:2026-09-28"]
		self.assertEqual(lesson["status"], "substitution")
		self.assertEqual(lesson["subject"], "Matematyka")
		self.assertEqual(lesson["teacher"], "Anna Nowak")
		self.assertIsNone(lesson["classroom"])
		self.assertEqual(lesson["original"], {
			"subject": "Przyroda",
			"teacher": "Jan Kowalski",
			"classroom": "M18",
			"date": "2026-09-28",
			"start": "10:20",
			"end": "11:05",
			"lesson_no": 4,
		})

	def test_cancelled_without_org_fields_falls_back_to_own_values(self):
		lesson = self.by_key()["650336:2026-09-29"]
		self.assertEqual(lesson["status"], "cancelled")
		self.assertEqual(lesson["original"], {
			"subject": "Język polski",
			"teacher": "Ewa Wiśniewska",
			"classroom": "M22",
			"date": "2026-09-29",
			"start": "08:35",
			"end": "09:20",
			"lesson_no": 2,
		})

	def test_group_lesson(self):
		lesson = self.by_key()["383777:2026-09-28"]
		self.assertEqual(lesson["group"], "4a1")
		self.assertEqual(lesson["classroom"], "SG4")
		self.assertEqual(lesson["status"], "normal")

	def test_sorted_by_date_then_start(self):
		self.assertEqual([lesson["key"] for lesson in self.parse()], [
			"659881:2026-09-28", "341434:2026-09-28", "383777:2026-09-28", "650336:2026-09-29",
		])

	def test_unknown_classroom_is_none(self):
		response = week_response()
		response["Timetable"]["2026-09-28"][1][0]["Classroom"] = ref(99999)
		self.assertIsNone(self.parse(response)[0]["classroom"])

	def test_empty_week(self):
		self.assertEqual(self.parse(empty_week()), [])

	def assertMalformed(self, response):
		with self.assertRaises(TimetableError) as cm:
			self.parse(response)
		self.assertEqual(str(cm.exception), MALFORMED)

	def test_missing_timetable_key(self):
		self.assertMalformed({"Pages": {}})

	def test_not_a_dict(self):
		self.assertMalformed([])

	def test_wrong_week(self):
		response = empty_week()
		del response["Timetable"]["2026-10-04"]
		response["Timetable"]["2026-10-05"] = []
		self.assertMalformed(response)

	def test_lesson_missing_field(self):
		response = week_response()
		del response["Timetable"]["2026-09-28"][1][0]["HourFrom"]
		self.assertMalformed(response)


if __name__ == "__main__":
	unittest.main()
