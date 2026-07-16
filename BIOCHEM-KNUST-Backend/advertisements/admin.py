from django.contrib import admin
from advertisements.models import Advertisement
from utils.media_mixins import make_media_admin_mixin

# Create media admin mixin for Advertisement model
AdvertisementMediaAdminMixin = make_media_admin_mixin(['flyer'])

# Register your models here.


@admin.register(Advertisement)
class AdvertisementAdmin(AdvertisementMediaAdminMixin, admin.ModelAdmin):
    list_display = ["brand", "flyer", "created_at"]
    
    fieldsets = (
        ('Advertisement Details', {
            'fields': ('brand', ('flyer', 'flyer_url'), 'is_active'),
            'description': 'Upload flyer OR provide Google Drive/Dropbox link'
        }),
    )
