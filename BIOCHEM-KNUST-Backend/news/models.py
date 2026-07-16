from django.db import models
# CloudinaryField replaced with ImageField using DynamicStorage
# from cloudinary.models import CloudinaryField
from uuid import uuid4
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage

# Create your models here.


# this model handles both blogs and news though the name suggest otherwise
class News(MediaUrlMixin, models.Model):
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'head_image': 'head_image_url',
        'back_image': 'back_image_url',
    }
    
    news_id = models.UUIDField(
        primary_key=True,
        unique=True,
        default=uuid4,
        editable=False,
    )
    title = models.CharField(max_length=100)
    reported_by = models.CharField(max_length=100)
    report = models.TextField()
    minutes_read = models.IntegerField(default=0)
    head_image = models.ImageField(storage=DynamicStorage(), upload_to="NewsImages/", null=True, blank=True)
    head_image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide head image URL instead of uploading"
    )
    back_image = models.ImageField(storage=DynamicStorage(), upload_to="NewsImages/", null=True, blank=True)
    back_image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide back image URL instead of uploading"
    )
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True, null=True)
    last_updted = models.DateTimeField(auto_now=True, auto_now_add=False, null=True)

    class Meta:
        db_table = "news_blogs"
        verbose_name = "News/Blogs"
        verbose_name_plural = "News/Blogs"
