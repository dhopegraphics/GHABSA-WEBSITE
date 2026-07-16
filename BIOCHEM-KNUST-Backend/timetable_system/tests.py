from django.test import TestCase
from academics.models import Course
from timetable_system.models import ClassSchedule


class ClassScheduleRepositoryTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(
            course_name="Intro to Testing",
            course_code="TEST101",
            year=1,
            semester="1",
            program="CS",
        )

    def test_create_and_query_class_schedule(self):
        cs = ClassSchedule.objects.create(
            program="CS",
            year=1,
            group="G1",
            course=self.course,
            day_of_week=1,
            start_time="09:00",
            end_time="10:30",
            room="Room 1",
        )

        found = ClassSchedule.objects.filter(year=1, group="G1", program="CS")
        self.assertEqual(found.count(), 1)
        self.assertEqual(found.first().course.course_code, "TEST101")
