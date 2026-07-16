from django.db import models
from uuid import uuid4
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage

# Create your models here.


class Staff(MediaUrlMixin, models.Model):
    """
    Model to store faculty and staff information
    """
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'image': 'image_url',
    }
    
    POSITION_CHOICES = [
        ('PROFESSOR', 'Professor'),
        ('ASSOCIATE_PROFESSOR', 'Associate Professor'),
        ('SENIOR_LECTURER', 'Senior Lecturer'),
        ('LECTURER', 'Lecturer'),
        ('ASSISTANT_LECTURER', 'Assistant Lecturer'),
        ('PART_TIME_LECTURER', 'Part-Time Lecturer'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Currently Active'),
        ('ON_LEAVE', 'On Leave'),
        ('RETIRED', 'Retired'),
        ('FORMER', 'Former Staff'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=50, choices=POSITION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', help_text="Current employment status")
    specialization = models.CharField(max_length=255, help_text="e.g., Artificial Intelligence, Computer Networks")
    bio = models.TextField(help_text="Brief description of research focus and expertise")
    publications_count = models.IntegerField(default=0)
    awards_count = models.IntegerField(default=0)
    email = models.EmailField()
    office_location = models.CharField(max_length=255, help_text="e.g., CS Building, Room 302")
    image = models.ImageField(storage=DynamicStorage(), upload_to='faculty/', null=True, blank=True)
    image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide image URL instead of uploading"
    )
    order = models.IntegerField(default=0, help_text="Order of display (lower numbers appear first)")
    is_active = models.BooleanField(default=True, help_text="Show/hide on public website")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'faculty_staff'
        verbose_name = 'Staff Member'
        verbose_name_plural = 'Department & Staff'
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.get_position_display()}"


class ResearchArea(models.Model):
    """
    Model to store research areas/tags for staff members
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='research_areas')
    name = models.CharField(max_length=100, help_text="e.g., Machine Learning, Network Security")
    
    class Meta:
        db_table = 'faculty_research_areas'
        verbose_name = 'Research Area'
        verbose_name_plural = 'Research Areas'
    
    def __str__(self):
        return f"{self.staff.name} - {self.name}"
