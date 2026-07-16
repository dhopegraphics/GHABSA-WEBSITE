from django.db import models
from academics.models import Course
from uuid import uuid4
from django_google_maps import fields as map_fields
from accounts.repository import UserRepository
from utils.utils import send_examination_schedule_message
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# Create your models here.


class ExaminationSchedule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    index_number_start = models.CharField(
        default=0000,
        max_length=230,
        help_text="Starting index number for that particular room",
    )
    index_number_end = models.CharField(
        default=0000,
        max_length=230,
        help_text="Last index number for that particular room",
    )
    time = models.DateTimeField(null=True)
    college = models.CharField(
        max_length=255,
        help_text="The college where the exam is suppose to take place",
    )
    room = models.CharField(max_length=230, null=True, blank=True)
    address = map_fields.AddressField(max_length=200, blank=True, null=True)
    message_schedule = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The time a message is suppose to be sent all students who have this exam; If no time is set the system will send message 1 hour before the paper",
    )
    action = models.CharField(
        max_length=255,
        choices=[
            ("hold_scheduling", "Hold Scheduling"),
            ("schedule_message", "Schedule Message"),
        ],
        default="hold_scheduling",
        help_text="Schedule Message Should Only Be Selected When Every Detail Of The Examination Like Time And Location Is Confirm",
    )
    geolocation = map_fields.GeoLocationField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        # fetch students within year and index number range
        students = UserRepository.fetch_examination_students_phone(
            year=self.course.year,
            index_number_start=self.index_number_start,
            index_number_end=self.index_number_end,
        )
        logger.info(f"Fetched {len(students) if students else 0} students for exam: {self.course.course_code}")
        if students and self.action == "schedule_message":
            # only run when we have students in the list and list is not empty
            msg_scheduled_at = (
                self.message_schedule
                if self.message_schedule
                else (self.time - timezone.timedelta(hours=2))
            ).strftime("%Y-%m-%d %H:%M")
            context = {
                "exam_date": self.time.date(),
                "exam_time": self.time.time(),
                "course": self.course.course_name,
                "college": self.college,
                "room": self.room,
            }
            send_examination_schedule_message(students, msg_scheduled_at, context)
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Examination Schedule Per Class"
        verbose_name_plural = "Examination Schedules"


# --- Class Schedule model ---
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


def get_academic_year_choices(count=6):
    """Return a list of academic year tuples to use in dropdowns.

    Rule: include the current academic year only when current month is Jan..Sep (<=9).
    - If month <= 9: start from (year - 1) so current academic year (e.g., 2024/2025 in Mar 2025) is included.
    - If month > 9: start from year (so the next academic year is the first option).

    Returns: list of tuples [("2025/2026","2025/2026"), ...]
    """
    today = timezone.now().date()
    if today.month <= 9:
        start = today.year - 1
    else:
        start = today.year

    choices = []
    for y in range(start, start + count):
        label = f"{y}/{y+1}"
        choices.append((label, label))
    return choices


class ProgramChoices(models.TextChoices):
    COMPUTER_SCIENCE = "CS", _("Computer Science")
    INFORMATION_TECH = "IT", _("Information Technology")


class GroupChoices(models.TextChoices):
    GROUP_1 = "G1", _("Group 1")
    GROUP_2 = "G2", _("Group 2")


class DayOfWeek(models.IntegerChoices):
    MONDAY = 1, _("Monday")
    TUESDAY = 2, _("Tuesday")
    WEDNESDAY = 3, _("Wednesday")
    THURSDAY = 4, _("Thursday")
    FRIDAY = 5, _("Friday")
    SATURDAY = 6, _("Saturday")
    SUNDAY = 7, _("Sunday")


class ClassSchedule(models.Model):
    """Schedule for classes grouped by program/year/group.

    - program: CS or IT
    - year: academic year (1..n)
    - group: G1 or G2
    - course: FK to academics.Course
    - day_of_week: integer 1..7
    - start_time, end_time: time fields
    - room, optional address/geolocation
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    academic_year = models.CharField(
        max_length=9,
        choices=get_academic_year_choices(),
        help_text="Academic year for this class schedule (e.g., 2025/2026)",
    )
    program = models.CharField(max_length=10, choices=ProgramChoices.choices)
    year = models.PositiveSmallIntegerField(help_text="Academic year (e.g., 1,2,3)")
    group = models.CharField(
        max_length=2, 
        choices=GroupChoices.choices,
        null=True,
        blank=True,
        help_text="Student group (G1/G2) - Required for Computer Science, optional for IT"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    day_of_week = models.PositiveSmallIntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=128, null=True, blank=True)
    address = map_fields.AddressField(max_length=200, null=True, blank=True)
    geolocation = map_fields.GeoLocationField(max_length=100, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Class Schedule"
        verbose_name_plural = "Class Schedules"
        ordering = ["day_of_week", "start_time"]

    @classmethod
    def program_requires_group(cls, program):
        """
        Check if a program requires group separation.
        Currently only CS has groups (G1, G2), IT does not.
        This can be easily modified in the future if IT gets groups.
        
        Args:
            program: Program code ("CS" or "IT")
            
        Returns:
            bool: True if program requires groups, False otherwise
        """
        # Programs that require group separation
        PROGRAMS_WITH_GROUPS = ["CS"]
        return program in PROGRAMS_WITH_GROUPS

    def __str__(self):
        group_display = f" {self.get_group_display()}" if self.group else ""
        return f"{self.course} — Year {self.year} {self.get_program_display()}{group_display} on {self.get_day_of_week_display()}"

