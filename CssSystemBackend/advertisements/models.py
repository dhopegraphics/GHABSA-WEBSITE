from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4
# CloudinaryField replaced with ImageField using DynamicStorage
# from cloudinary.models import CloudinaryField
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage


# Create your models here.
class Advertisement(MediaUrlMixin, models.Model):
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'flyer': 'flyer_url',
    }
    
    ad_id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        unique=True,
    )
    brand = models.CharField(max_length=100)
    flyer = models.ImageField(storage=DynamicStorage(), upload_to="Ads/", blank=True, null=True)
    flyer_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide flyer URL (Google Drive, Dropbox, etc.) instead of uploading"
    )
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Advertisement")
        verbose_name_plural = _("Advertisements")

    def __str__(self):
        return self.brand
