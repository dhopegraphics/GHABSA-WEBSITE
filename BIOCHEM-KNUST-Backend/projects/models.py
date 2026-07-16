from django.db import models
from django.utils import timezone
from uuid import uuid4
from datetime import datetime
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage

# Create your models here.


def get_year_choices():
    """Generate year choices dynamically from 2020 to current year + 2"""
    current_year = datetime.now().year
    start_year = 2020
    end_year = current_year + 2  # Allow submissions for next 2 years
    return [(str(year), str(year)) for year in range(start_year, end_year + 1)]


class ApprovedProjectManager(models.Manager):
    """Manager that returns only approved projects"""
    def get_queryset(self):
        return super().get_queryset().filter(is_approved=True, is_active=True)


class Project(MediaUrlMixin, models.Model):
    """
    Model to store student projects and showcase their work
    """
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'image': 'image_url',
        'image2': 'image2_url',
        'image3': 'image3_url',
    }
    
    CATEGORY_CHOICES = [
        ('WEB', 'Web Development'),
        ('MOBILE', 'Mobile Development'),
        ('AI_ML', 'Artificial Intelligence & Machine Learning'),
        ('DATA_SCIENCE', 'Data Science & Analytics'),
        ('CYBERSECURITY', 'Cybersecurity'),
        ('IOT', 'Internet of Things'),
        ('GAME', 'Game Development'),
        ('BLOCKCHAIN', 'Blockchain'),
        ('CLOUD', 'Cloud Computing'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=255, help_text="Project title")
    description = models.TextField(help_text="Detailed project description")
    short_description = models.CharField(max_length=200, help_text="Brief summary for cards", blank=True)
    academic_year = models.CharField(
        max_length=10, 
        help_text="Year project was completed"
    )  # Removed choices to allow any valid year
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, help_text="Project category")
    technologies = models.TextField(help_text="Technologies/tools used (comma-separated)")
    
    # Project Links
    github_url = models.URLField(blank=True, null=True, help_text="GitHub repository URL")
    demo_url = models.URLField(blank=True, null=True, help_text="Live demo or video URL")
    
    # Images
    image = models.ImageField(storage=DynamicStorage(), upload_to='projects/', blank=True, null=True, help_text="Main project image/screenshot")
    image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide image URL instead of uploading"
    )
    image2 = models.ImageField(storage=DynamicStorage(), upload_to='projects/', blank=True, null=True, help_text="Additional image (optional)")
    image2_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide image 2 URL instead of uploading"
    )
    image3 = models.ImageField(storage=DynamicStorage(), upload_to='projects/', blank=True, null=True, help_text="Additional image (optional)")
    image3_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide image 3 URL instead of uploading"
    )
    
    # Display settings
    is_featured = models.BooleanField(default=False, help_text="Feature this project on homepage/top")
    is_active = models.BooleanField(default=True, help_text="Show/hide on public website")
    order = models.IntegerField(default=0, help_text="Display order (lower numbers first)")
    
    # Approval system
    is_approved = models.BooleanField(default=False, help_text="Project must be approved by an executive")
    approved_by = models.ForeignKey(
        'executives.Executive',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_projects',
        help_text="Executive who approved this project"
    )
    approved_at = models.DateTimeField(null=True, blank=True, help_text="When the project was approved")
    
    # Submission tracking
    submitted_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_projects',
        help_text="User who submitted this project"
    )
    
    # Update request system (for approved projects)
    UPDATE_STATUS_CHOICES = [
        ('none', 'No Update Requested'),
        ('pending', 'Update Requested'),
        ('approved', 'Update Approved'),
        ('in_progress', 'Update In Progress'),
    ]
    
    update_status = models.CharField(
        max_length=20,
        choices=UPDATE_STATUS_CHOICES,
        default='none',
        help_text="Status of update request for approved projects"
    )
    update_request_reason = models.TextField(
        blank=True,
        default='',
        help_text="Reason for requesting an update"
    )
    update_requested_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the update was requested"
    )
    update_approved_by = models.ForeignKey(
        'executives.Executive',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_project_updates',
        help_text="Executive who approved the update request"
    )
    update_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the update request was approved"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Managers
    objects = models.Manager()  # Default manager returns all projects
    approved = ApprovedProjectManager()  # Returns only approved projects
    
    class Meta:
        db_table = 'projects'
        verbose_name = 'Student Project'
        verbose_name_plural = 'Student Projects'
        ordering = ['-is_featured', 'order', '-academic_year', '-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.academic_year})"
    
    def get_technology_list(self):
        """Returns list of technologies"""
        return [tech.strip() for tech in self.technologies.split(',') if tech.strip()]


class ProjectMember(models.Model):
    """
    Model to store individual team members for each project
    Each student can have their own year information
    Can optionally link to a registered user account
    """
    YEAR_CHOICES = [
        ('1', 'Year 1'),
        ('2', 'Year 2'),
        ('3', 'Year 3'),
        ('4', 'Year 4'),
        ('MASTERS', 'Masters'),
        ('PHD', 'PhD'),
        ('ALUMNI', 'Alumni'),
    ]
    
    PROGRAM_CHOICES = [
        ('CS', 'Computer Science'),
        ('IT', 'Information Technology'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    
    # Link to registered user (optional - for team members who have accounts)
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_memberships',
        help_text="Link to registered user account (if they have one)"
    )
    
    # Member details (can be auto-filled from user if linked)
    name = models.CharField(max_length=255, help_text="Student full name")
    year = models.CharField(max_length=20, choices=YEAR_CHOICES, default='4', help_text="Student's year during project")
    program = models.CharField(max_length=10, choices=PROGRAM_CHOICES, default='CS', help_text="CS or IT program")
    role = models.CharField(max_length=100, blank=True, help_text="Role in project (e.g., Team Lead, Backend Developer)")
    student_id = models.CharField(max_length=50, blank=True, help_text="Student ID number (optional)")
    email = models.EmailField(blank=True, help_text="Student email (optional)")
    phone = models.CharField(max_length=20, blank=True, help_text="Phone number (optional)")
    order = models.IntegerField(default=0, help_text="Display order (lower numbers first, e.g., team lead first)")
    
    # Track if this member is the one who submitted the project
    is_submitter = models.BooleanField(default=False, help_text="Is this the person who submitted the project?")
    
    class Meta:
        db_table = 'project_members'
        verbose_name = 'Project Member'
        verbose_name_plural = 'Project Members'
        ordering = ['order', 'name']
        unique_together = ['project', 'name']  # Prevent duplicate names in same project
    
    def __str__(self):
        return f"{self.name} - {self.project.title}"
