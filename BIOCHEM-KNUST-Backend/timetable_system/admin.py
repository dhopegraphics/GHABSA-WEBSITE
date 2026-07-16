from django.contrib import admin
from django_google_maps import widgets as map_widgets
from django_google_maps import fields as map_fields
from timetable_system.models import ExaminationSchedule
from django import forms


# Register your models here.
class ExaminationScheduleAdmin(admin.ModelAdmin):
    list_display = ["course", "college", "room", "time", "action"]
    list_filter = ["course", "college", "room", "action"]
    change_list_template = 'admin/timetable_system/examinationschedule/change_list.html'
    
    # Make Google Maps optional - use regular text input as fallback
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'address':
            try:
                # Try to use Google Maps widget
                return db_field.formfield(widget=map_widgets.GoogleMapsAddressWidget())
            except:
                # Fallback to regular text input if Google Maps fails
                kwargs['widget'] = forms.TextInput(attrs={'size': '50'})
                return db_field.formfield(**kwargs)
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    fieldsets = (
        (
            "Examination Schedule",
            {
                "fields": (
                    "course",
                    "college",
                    "room",
                    "time",
                    "index_number_start",
                    "index_number_end",
                ),
            },
        ),
        (
            "Messaging Schedule",
            {
                "fields": (
                    "action",
                    "message_schedule",
                ),
            },
        ),
        (
            "Location (Optional)",
            {
                "fields": (
                    "address",
                    "geolocation",
                ),
                "description": "Address and geolocation are optional. You can leave these blank if Google Maps is not working.",
            },
        ),
    )


admin.site.register(ExaminationSchedule, ExaminationScheduleAdmin)


from timetable_system.models import ClassSchedule


class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ["course", "program", "year", "group", "day_of_week", "start_time", "room"]
    list_filter = ["program", "year", "group", "day_of_week", "room"]
    change_list_template = 'admin/timetable_system/classschedule/change_list.html'


admin.site.register(ClassSchedule, ClassScheduleAdmin)
