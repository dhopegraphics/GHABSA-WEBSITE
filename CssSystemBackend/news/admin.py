from django.contrib import admin
from news.models import News
from utils.media_mixins import make_media_admin_mixin

# Create media admin mixin for News model
NewsMediaAdminMixin = make_media_admin_mixin(['head_image', 'back_image'])


# Register your models here.
@admin.register(News)
class NewsAdmin(NewsMediaAdminMixin, admin.ModelAdmin):
    list_display = ["reported_by", "title", "created_at"]
    fieldsets = (
        (
            "Meta Data",
            {
                "fields": ("reported_by",),
            },
        ),
        (
            "Content",
            {
                "fields": (
                    "title",
                    "report",
                    "minutes_read",
                ),
            },
        ),
        (
            "Media",
            {
                "fields": (
                    ("head_image", "head_image_url"),
                    ("back_image", "back_image_url"),
                ),
                "description": "Upload images OR provide Google Drive/Dropbox links"
            },
        ),
    )
