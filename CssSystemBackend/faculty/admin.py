from django.contrib import admin
from faculty.models import Staff, ResearchArea
from utils.media_mixins import make_media_admin_mixin

# Create media admin mixin for Staff model
StaffMediaAdminMixin = make_media_admin_mixin(['image'])

# Register your models here.


class ResearchAreaInline(admin.TabularInline):
    model = ResearchArea
    extra = 1


@admin.register(Staff)
class StaffAdmin(StaffMediaAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'position', 'status', 'specialization', 'email', 'office_location', 'publications_count', 'awards_count', 'is_active', 'order']
    list_filter = ['position', 'status', 'is_active']
    search_fields = ['name', 'email', 'specialization']
    ordering = ['order', 'name']
    inlines = [ResearchAreaInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'position', 'status', 'email', 'office_location', ('image', 'image_url')),
            'description': 'Upload image OR provide Google Drive/Dropbox link'
        }),
        ('Academic Details', {
            'fields': ('specialization', 'bio', 'publications_count', 'awards_count')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
    )


@admin.register(ResearchArea)
class ResearchAreaAdmin(admin.ModelAdmin):
    list_display = ['staff', 'name']
    list_filter = ['staff']
    search_fields = ['name', 'staff__name']
