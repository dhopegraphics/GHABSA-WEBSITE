from django.db import models
# CloudinaryField replaced with ImageField using DynamicStorage
# from cloudinary.models import CloudinaryField
from uuid import uuid4
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage

# Create your models here.


class SocietyHistory(MediaUrlMixin, models.Model):
    """
    Model to store the rich history of CSS KNUST
    Includes founding stories, past administrations, milestones, achievements, etc.
    """
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'image': 'image_url',
    }
    
    history_id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        unique=True,
    )
    title = models.CharField(
        max_length=300,
        help_text="Title of the historical record (e.g., 'Foundation Era', '2020/2021 Administration')"
    )
    session_year = models.CharField(
        max_length=20,
        help_text="Academic year or period (e.g., 2024/2025)",
        null=True,
        blank=True
    )
    category = models.CharField(
        max_length=50,
        choices=[
            ('founding', 'Founding & Early Years'),
            ('administration', 'Past Administration'),
            ('milestone', 'Major Milestone'),
            ('achievement', 'Notable Achievement'),
            ('event', 'Historic Event'),
            ('lecture', 'Past Lecturer'),
            ('other', 'Other'),
        ],
        default='administration',
        help_text="Category of this historical record"
    )
    description = models.TextField(
        help_text="Detailed description of this historical period or event"
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Start date of this period"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date of this period (leave blank for ongoing)"
    )
    image = models.ImageField(
        storage=DynamicStorage(),
        upload_to="HistoryImages/",
        blank=True,
        null=True,
        help_text="Upload an image for this historical record"
    )
    image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide image URL (Google Drive, Dropbox, etc.) instead of uploading"
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first in same category)"
    )
    is_published = models.BooleanField(
        default=True,
        help_text="Whether this record is visible on the website"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.session_year or 'No year specified'})"

    class Meta:
        ordering = ['-start_date', 'order']
        verbose_name = "Society History Record"
        verbose_name_plural = "Society History Records"
        db_table = "history_society_history"


class HistoricalLeader(MediaUrlMixin, models.Model):
    """
    Model to store key figures associated with historical periods
    Can be past presidents, lecturers, HODs, or other notable figures
    """
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'image': 'image_url',
    }
    
    leader_id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        unique=True,
    )
    history = models.ForeignKey(
        SocietyHistory,
        on_delete=models.CASCADE,
        related_name="leaders",
        help_text="The historical period this leader belongs to"
    )
    name = models.CharField(
        max_length=200,
        help_text="Full name of the leader/executive/lecturer"
    )
    position = models.CharField(
        max_length=200,
        help_text="Position held (e.g., President, HOD, Senior Lecturer, Founder)"
    )
    image = models.ImageField(
        storage=DynamicStorage(),
        upload_to="HistoricalLeaders/",
        blank=True,
        null=True,
        help_text="Upload a profile photo"
    )
    image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide image URL instead of uploading"
    )
    bio = models.TextField(
        blank=True,
        help_text="Brief biography, achievements, or contributions"
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order within the historical period"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.position}"

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Historical Leader"
        verbose_name_plural = "Historical Leaders"
        db_table = "history_historical_leader"


class HistoricalMilestone(models.Model):
    """
    Model to store specific achievements or milestones within a historical period
    """
    milestone_id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        unique=True,
    )
    history = models.ForeignKey(
        SocietyHistory,
        on_delete=models.CASCADE,
        related_name="milestones",
        help_text="The historical period this milestone belongs to"
    )
    title = models.CharField(
        max_length=300,
        help_text="Title of the milestone or achievement"
    )
    description = models.TextField(
        help_text="Description of what was achieved"
    )
    date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when this milestone was achieved"
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order', 'date']
        verbose_name = "Historical Milestone"
        verbose_name_plural = "Historical Milestones"
        db_table = "history_milestone"

