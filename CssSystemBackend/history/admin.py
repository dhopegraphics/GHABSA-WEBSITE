from django.contrib import admin
from .models import SocietyHistory, HistoricalLeader, HistoricalMilestone
from utils.media_mixins import make_media_admin_mixin

# Create media admin mixins for models with file fields
SocietyHistoryMediaAdminMixin = make_media_admin_mixin(['image'])
HistoricalLeaderMediaAdminMixin = make_media_admin_mixin(['image'])


class HistoricalLeaderInline(admin.TabularInline):
    model = HistoricalLeader
    extra = 1
    fields = ["name", "position", "image", "image_url", "bio", "order"]


class HistoricalMilestoneInline(admin.TabularInline):
    model = HistoricalMilestone
    extra = 1
    fields = ["title", "description", "date", "order"]


@admin.register(SocietyHistory)
class SocietyHistoryAdmin(SocietyHistoryMediaAdminMixin, admin.ModelAdmin):
    list_display = ["title", "session_year", "category", "start_date", "end_date", "is_published", "order"]
    list_filter = ["category", "is_published", "session_year"]
    search_fields = ["title", "description", "session_year"]
    inlines = [HistoricalLeaderInline, HistoricalMilestoneInline]
    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "session_year", "category", "description")
        }),
        ("Timeline", {
            "fields": ("start_date", "end_date")
        }),
        ("Image (Choose one option)", {
            "fields": ("image", "image_url"),
            "description": "Upload an image OR provide a URL. URL takes priority if both are provided."
        }),
        ("Display Settings", {
            "fields": ("order", "is_published")
        }),
    )


@admin.register(HistoricalLeader)
class HistoricalLeaderAdmin(HistoricalLeaderMediaAdminMixin, admin.ModelAdmin):
    list_display = ["name", "position", "history", "order"]
    list_filter = ["position", "history__category"]
    search_fields = ["name", "position", "bio"]
    fieldsets = (
        ("Basic Information", {
            "fields": ("history", "name", "position", "bio")
        }),
        ("Image (Choose one option)", {
            "fields": ("image", "image_url"),
        }),
        ("Display Settings", {
            "fields": ("order",)
        }),
    )


@admin.register(HistoricalMilestone)
class HistoricalMilestoneAdmin(admin.ModelAdmin):
    list_display = ["title", "history", "date", "order"]
    list_filter = ["history__category", "date"]
    search_fields = ["title", "description"]
    fieldsets = (
        ("Basic Information", {
            "fields": ("history", "title", "description", "date")
        }),
        ("Display Settings", {
            "fields": ("order",)
        }),
    )

