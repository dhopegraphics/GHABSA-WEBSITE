from django.contrib import admin
from academics.models import (
    Course,
    Lecturer,
    OnlineTutorialTips,
    AcademicSlides,
    PastQuestions,
    InternshipOpportunities,
)
from django.utils import timezone
from django.db.models import Q
from utils.media_mixins import make_media_admin_mixin

# Create media admin mixins for models with file fields
LecturerMediaAdminMixin = make_media_admin_mixin(['profile_image'])
AcademicSlidesMediaAdminMixin = make_media_admin_mixin(['file'])
PastQuestionsMediaAdminMixin = make_media_admin_mixin(['file'])
InternshipOpportunitiesMediaAdminMixin = make_media_admin_mixin(['image'])

# Register your models here.


@admin.register(Lecturer)
class LecturerAdmin(LecturerMediaAdminMixin, admin.ModelAdmin):
    list_display = [
        "get_full_name",
        "email",
        "phone",
        "specialization",
        "get_course_count",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "title", "created_at"]
    search_fields = ["first_name", "last_name", "email", "specialization"]
    ordering = ["last_name", "first_name"]
    list_per_page = 25

    fieldsets = (
        (
            "Personal Information",
            {
                "fields": (
                    "title",
                    "first_name",
                    "last_name",
                    ("profile_image", "profile_image_url"),
                ),
                "description": "Upload image OR provide Google Drive/Dropbox link"
            },
        ),
        (
            "Contact Information",
            {
                "fields": ("email", "phone", "office_location"),
            },
        ),
        (
            "Professional Details",
            {
                "fields": ("specialization", "bio"),
            },
        ),
        (
            "Status",
            {
                "fields": ("is_active",),
            },
        ),
    )

    def get_full_name(self, obj):
        return obj.full_name

    get_full_name.short_description = "Full Name"
    get_full_name.admin_order_field = "last_name"
    
    def get_course_count(self, obj):
        """Display number of courses taught by this lecturer"""
        count = obj.courses.count()
        return f"{count} course{'s' if count != 1 else ''}"
    
    get_course_count.short_description = "Courses Teaching"

    actions = ["mark_as_active", "mark_as_inactive"]

    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} lecturer(s) marked as active.")

    mark_as_active.short_description = "Mark selected lecturers as active"

    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} lecturer(s) marked as inactive.")

    mark_as_inactive.short_description = "Mark selected lecturers as inactive"


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        "course_code",
        "course_name",
        "year",
        "semester",
        "program",
        "credit_hours",
        "get_lecturer",
        "created_at",
    ]

    # Add filters for easy navigation by year/semester/program
    list_filter = ["year", "semester", "program", "lecturer", "created_at"]

    # Enable search functionality
    search_fields = ["course_code", "course_name", "lecturer__first_name", "lecturer__last_name"]

    # Group by year, semester, and program for better organization
    ordering = ["year", "semester", "program", "course_code"]

    # Add fieldsets for better form organization
    fieldsets = (
        (
            "Course Information",
            {
                "fields": ("course_code", "course_name", "credit_hours", "description")
            },
        ),
        (
            "Academic Details",
            {
                "fields": ("year", "semester", "program", "lecturer", "prerequisites"),
            },
        ),
    )

    # Configure many-to-many field display
    filter_horizontal = ["prerequisites"]
    
    # Use autocomplete for lecturer field - allows search as you type
    autocomplete_fields = ["lecturer"]

    # Add list per page for better performance
    list_per_page = 25

    # Custom action to duplicate courses and change programs
    actions = [
        "duplicate_course",
        "export_to_first_semester",
        "export_to_second_semester",
        "set_program_to_cs",
        "set_program_to_it",
    ]

    def get_lecturer(self, obj):
        """Display lecturer teaching the course"""
        if obj.lecturer:
            return str(obj.lecturer)
        return "Not Assigned"

    get_lecturer.short_description = "Lecturer"
    get_lecturer.admin_order_field = "lecturer__last_name"

    def duplicate_course(self, request, queryset):
        for course in queryset:
            # Store relationships
            lecturer = course.lecturer
            prerequisites = list(course.prerequisites.all())
            
            course.pk = None
            course.course_code = f"{course.course_code}_COPY"
            course.lecturer = lecturer
            course.save()
            
            # Restore many-to-many relationships
            course.prerequisites.set(prerequisites)
            
        self.message_user(request, f"{queryset.count()} course(s) duplicated successfully.")

    duplicate_course.short_description = "Duplicate selected courses"

    def export_to_first_semester(self, request, queryset):
        updated = queryset.update(semester="1")
        self.message_user(request, f"{updated} course(s) moved to First Semester.")

    export_to_first_semester.short_description = "Move to First Semester"

    def export_to_second_semester(self, request, queryset):
        updated = queryset.update(semester="2")
        self.message_user(request, f"{updated} course(s) moved to Second Semester.")

    export_to_second_semester.short_description = "Move to Second Semester"

    def set_program_to_cs(self, request, queryset):
        updated = queryset.update(program="CS")
        self.message_user(request, f"{updated} course(s) set to Computer Science program.")

    set_program_to_cs.short_description = "Set program to Computer Science"

    def set_program_to_it(self, request, queryset):
        updated = queryset.update(program="IT")
        self.message_user(request, f"{updated} course(s) set to Information Technology program.")

    set_program_to_it.short_description = "Set program to Information Technology"

    # Override save to check for duplicates
    def save_model(self, request, obj, form, change):
        # Check if course with same code already exists (excluding current object if editing)
        if not change:  # Only for new courses
            if Course.objects.filter(course_code__iexact=obj.course_code).exists():
                from django.contrib import messages

                messages.error(
                    request,
                    f'A course with code "{obj.course_code}" already exists. Please use a different code.',
                )
                return
        super().save_model(request, obj, form, change)


@admin.register(OnlineTutorialTips)
class OnlineTutorialTipsAdmin(admin.ModelAdmin):
    list_display = ["course", "created_at", "approved"]


@admin.register(InternshipOpportunities)
class InternshipOpportunitiesAdmin(InternshipOpportunitiesMediaAdminMixin, admin.ModelAdmin):
    # Define which fields to display in the list view
    list_display = (
        "campany_name",
        "application_deadline",
        "created_at",
        "get_application_status",
    )

    # Add filtering options in the list view
    list_filter = ("application_deadline", "created_at")

    # Allow searching by company name and description
    search_fields = ("campany_name", "description")

    # Sort the list by application deadline by default
    ordering = ("-application_deadline",)

    # Add a method to show the application status (if deadline is passed)
    def get_application_status(self, obj):
        if obj.application_deadline and obj.application_deadline < timezone.now():
            return "Expired"
        return "Active"

    get_application_status.short_description = "Application Status"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "campany_name",
                    "description",
                    "registration_link",
                    ("image", "image_url"),
                ),
                "description": "Upload image OR provide Google Drive/Dropbox link"
            },
        ),
        (
            "Important Dates",
            {
                "fields": ("application_deadline",),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["mark_as_expired"]

    def mark_as_expired(self, request, queryset):
        updated_count = queryset.update(application_deadline=timezone.now())
        self.message_user(request, f"{updated_count} internship(s) marked as expired.")

    mark_as_expired.short_description = "Mark selected internships as expired"


@admin.register(AcademicSlides)
class AcademicSlidesAdmin(AcademicSlidesMediaAdminMixin, admin.ModelAdmin):
    list_display = [
        "course",
        "file",
        "created_at",
        "approved",
    ]
    fieldsets = (
        (
            "Course",
            {
                "fields": (
                    "course",
                    "title",
                ),
            },
        ),
        (
            "Slides",
            {
                "fields": (
                    ("file", "file_url"),
                    "approved",
                ),
                "description": "Upload file OR provide Google Drive/Dropbox link"
            },
        ),
    )


@admin.register(PastQuestions)
class PastQuestionsAdmin(PastQuestionsMediaAdminMixin, admin.ModelAdmin):
    list_display = [
        "course",
        "file",
        "created_at",
        "approved",
    ]
    fieldsets = (
        (
            "Course",
            {
                "fields": (
                    "course",
                    "title",
                ),
            },
        ),
        (
            "Pasco",
            {
                "fields": (
                    ("file", "file_url"),
                    "approved",
                ),
                "description": "Upload file OR provide Google Drive/Dropbox link"
            },
        ),
    )
