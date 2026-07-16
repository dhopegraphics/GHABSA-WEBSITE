from django.db import models
from events.models import Event
from django.utils.translation import gettext_lazy as _
from uuid import uuid4
# CloudinaryField replaced with ImageField using DynamicStorage
# from cloudinary.models import CloudinaryField
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage

# Create your models here.


class Timeline(MediaUrlMixin, models.Model):
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'image': 'image_url',
    }
    
    timeline_id = models.UUIDField(
        primary_key=True,
        unique=True,
        default=uuid4,
        editable=False,
    )
    event = models.ForeignKey(
        Event,
        verbose_name=_("Event"),
        on_delete=models.CASCADE,
        related_name="timeline",
    )
    image = models.ImageField(storage=DynamicStorage(), upload_to="TimelineImages/", blank=True, null=True)
    image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide image URL instead of uploading"
    )
    decription = models.TextField()
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True, null=True)

    def __str__(self) -> str:
        return f"{self.event.event_name} Timeline"
