from django.contrib import admin
from timeline.models import Timeline
from django.utils.html import format_html
from utils.media_mixins import make_media_admin_mixin

# Create media admin mixin for Timeline model
TimelineMediaAdminMixin = make_media_admin_mixin(['image'])

# Register your models here.


@admin.register(Timeline)
class TimelineAdmin(TimelineMediaAdminMixin, admin.ModelAdmin):
    def timeline(self, obj):
        # Prioritize URL over upload
        img_url = obj.image_url if obj.image_url else (obj.image.url if obj.image else None)
        if img_url:
            return format_html(
                '<a href={}><img src="{}" width="50" height="50" /></a>',
                img_url,
                img_url,
            )
        return "-"

    list_display = ["event", "timeline", "created_at"]
    
    fieldsets = (
        ('Timeline Entry', {
            'fields': ('event', ('image', 'image_url')),
            'description': 'Upload image OR provide Google Drive/Dropbox link'
        }),
    )
