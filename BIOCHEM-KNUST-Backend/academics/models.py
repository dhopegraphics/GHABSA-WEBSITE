from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4
# CloudinaryField replaced with ImageField/FileField using DynamicStorage
# from cloudinary.models import CloudinaryField
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage

# Create your models here.

type_of_resource = [
    ("slides", "slides"),
    ("video", "video"),
    ("article", "article"),
    ("audio", "audio"),
    ("file", "file"),
]

SEMESTER_CHOICES = [
    ("1", "First Semester"),
    ("2", "Second Semester"),
    ("both", "Both Semesters"),
]

PROGRAM_CHOICES = [
    ("CS", "Computer Science"),
    ("IT", "Information Technology"),
]


class Lecturer(MediaUrlMixin, models.Model):
    """Model to store lecturer information"""
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'profile_image': 'profile_image_url',
    }
    
    lecturer_id = models.UUIDField(
        primary_key=True, unique=True, default=uuid4, editable=False
    )
    title = models.CharField(
        max_length=50,
        choices=[
            ("Prof.", "Professor"),
            ("Dr.", "Doctor"),
            ("Mr.", "Mister"),
            ("Mrs.", "Mistress"),
            ("Ms.", "Miss"),
        ],
        default="Mr.",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    office_location = models.CharField(max_length=200, null=True, blank=True)
    specialization = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Area of expertise (e.g., Artificial Intelligence, Networks)",
    )
    bio = models.TextField(
        null=True, blank=True, help_text="Brief biography of the lecturer"
    )
    profile_image = models.ImageField(
        storage=DynamicStorage(), upload_to="LecturerProfiles/", null=True, blank=True
    )
    profile_image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide profile image URL instead of uploading"
    )
    is_active = models.BooleanField(
        default=True, help_text="Is the lecturer currently active?"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = "Lecturer"
        verbose_name_plural = "Lecturers"

    def __str__(self) -> str:
        return f"{self.title} {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.title} {self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        # Auto-populate profile_image_url from Cloudinary if image is uploaded and profile_image_url is empty
        if self.profile_image and not self.profile_image_url:
            self.profile_image_url = self.profile_image.url
        super().save(*args, **kwargs)


class Course(models.Model):
    course_id = models.UUIDField(
        primary_key=True, unique=True, default=uuid4, editable=False
    )
    credit_hours = models.IntegerField(null=True)
    course_name = models.CharField(max_length=200, null=True, blank=False)
    course_code = models.CharField(max_length=200, unique=True)
    year = models.IntegerField(help_text="Year 1, 2, 3, or 4")
    semester = models.CharField(
        max_length=10,
        choices=SEMESTER_CHOICES,
        default="1",
        help_text="Which semester is this course offered?",
    )
    program = models.CharField(
        max_length=10,
        choices=PROGRAM_CHOICES,
        default="CS",
        help_text="Which program does this course belong to? (Computer Science or Information Technology)",
    )
    lecturer = models.ForeignKey(
        Lecturer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
        help_text="Lecturer teaching this course",
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Brief description of the course content",
    )
    prerequisites = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="required_for",
        help_text="Courses that must be completed before taking this course",
    )
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        ordering = ["year", "semester", "course_code"]
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        indexes = [
            models.Index(fields=['year', 'semester']),
            models.Index(fields=['program']),
            models.Index(fields=['lecturer']),
            models.Index(fields=['course_code']),
        ]

    def __str__(self) -> str:
        semester_display = dict(SEMESTER_CHOICES).get(self.semester, "")
        program_display = dict(PROGRAM_CHOICES).get(self.program, "")
        return f"{self.course_name} - Year {self.year} ({semester_display}) - {program_display}"

    @property
    def lecturer_name(self):
        """Returns the lecturer's name if assigned"""
        return str(self.lecturer) if self.lecturer else "Not Assigned"


class OnlineTutorialTips(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="online_tips",
    )
    title = models.CharField(
        null=True, max_length=255, help_text="A simple title about the resource"
    )
    link = models.URLField(("resource_link"), max_length=200)
    type_of_resource = models.CharField(choices=type_of_resource, max_length=50)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True, auto_now_add=False)
    approved = models.BooleanField(default=True)

    class Meta:
        # verbose_name = _("")
        verbose_name_plural = _("Online Tutorial Tips")
        indexes = [
            models.Index(fields=['course', 'approved']),
        ]

    def __str__(self) -> str:
        return f"{self.course.course_name} Online Tip"


class AcademicSlides(MediaUrlMixin, models.Model):
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'file': 'file_url',
    }
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="slides")
    title = models.CharField(
        null=True, max_length=255, help_text="A simple title about the resource"
    )
    file = models.FileField(storage=DynamicStorage(), upload_to="AcademicSlides/", blank=True, null=True)
    file_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide file URL (Google Drive, Dropbox, etc.) instead of uploading"
    )
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True, auto_now_add=False)
    approved = models.BooleanField(default=True)

    class Meta:
        # verbose_name = _("")
        # db_table = "academics slides"
        verbose_name_plural = _("Academic Slides")
        indexes = [
            models.Index(fields=['course', 'approved']),
        ]

    def __str__(self) -> str:
        return f"{self.course.course_name} Slide"
    
    def get_file_url(self):
        """Get the proper file URL, prioritizing file_url over local file"""
        if self.file_url:
            return self.file_url
        if self.file:
            try:
                return self.file.url
            except:
                return None
        return None
    
    # Note: save() is handled by MediaUrlMixin - no custom save needed


class PastQuestions(MediaUrlMixin, models.Model):
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'file': 'file_url',
    }
    
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="past_questions"
    )
    title = models.CharField(
        null=True, max_length=255, help_text="A simple title about the resource"
    )
    file = models.FileField(storage=DynamicStorage(), upload_to="PastQuestions/", blank=True, null=True)
    file_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide file URL (Google Drive, Dropbox, etc.) instead of uploading"
    )
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True, auto_now_add=False)
    approved = models.BooleanField(default=True)

    class Meta:
        # verbose_name = _("")
        verbose_name_plural = _("Past Questions")
        indexes = [
            models.Index(fields=['course', 'approved']),
        ]

    def __str__(self) -> str:
        return f"{self.course.course_name} Past Questions"
    
    def get_file_url(self):
        """Get the proper file URL, prioritizing file_url over local file"""
        if self.file_url:
            return self.file_url
        if self.file:
            try:
                return self.file.url
            except:
                return None
        return None
    
    # Note: save() is handled by MediaUrlMixin - no custom save needed


class InternshipOpportunities(MediaUrlMixin, models.Model):
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'image': 'image_url',
    }
    
    internship_id = models.UUIDField(
        editable=False,
        default=uuid4,
        primary_key=True,
        unique=True,
    )
    campany_name = models.CharField(max_length=255)
    image = models.ImageField(storage=DynamicStorage(), upload_to="InternshipFlyers/", blank=True, null=True)
    image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide flyer URL instead of uploading"
    )
    description = models.TextField()
    registration_link = models.URLField()
    application_deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.campany_name

    class Meta:
        verbose_name = "Internship"
        verbose_name_plural = "Internships"
    
    # Note: save() is handled by MediaUrlMixin - no custom save needed
