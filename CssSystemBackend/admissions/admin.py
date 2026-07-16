from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import (
    AdmissionCriteria, SubjectGradeMapping, AdmissionGuideline,
    EligibilityCheck, FAQ, ImportantDate, WhatsAppHelpdesk, 
    WhatsAppAccessLog, KNUSTAdmission
)
from utils.media_mixins import make_media_admin_mixin

# Create media admin mixin for AdmissionGuideline model
AdmissionGuidelineMediaAdminMixin = make_media_admin_mixin(['image'])


class AdmissionsAdminSite(admin.ModelAdmin):
    """Base admin class with scraper dashboard link"""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('knust-scraper/', self.admin_site.admin_view(self.scraper_dashboard_view), name='knust_scraper'),
        ]
        return custom_urls + urls
    
    def scraper_dashboard_view(self, request):
        from .scraper_views import scraper_dashboard
        return scraper_dashboard(request)
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['scraper_button'] = format_html(
            '<a class="button" href="{}" style="background-color: #4CAF50; color: white; padding: 10px 20px; '
            'text-decoration: none; border-radius: 5px; margin: 10px 0; display: inline-block;">'
            '🔄 KNUST Admissions Scraper</a>',
            '../knust-scraper/'
        )
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(AdmissionCriteria)
class AdmissionCriteriaAdmin(admin.ModelAdmin):
    list_display = ['program', 'academic_year', 'aggregate_cutoff', 'is_active', 'updated_at']
    list_filter = ['program', 'academic_year', 'is_active']
    search_fields = ['program', 'academic_year']
    readonly_fields = ['created_at', 'updated_at', 'updated_by']
    
    fieldsets = (
        ('Program Information', {
            'fields': ('program', 'academic_year', 'is_active')
        }),
        ('Aggregate Requirements', {
            'fields': ('aggregate_cutoff',)
        }),
        ('Core Subject Requirements', {
            'fields': (
                'core_math_min_grade',
                'english_min_grade',
                'integrated_science_min_grade',
                'social_studies_min_grade'
            )
        }),
        ('Elective Subject Requirements', {
            'fields': (
                'elective_math_required',
                'elective_math_min_grade',
                'physics_required',
                'physics_min_grade',
                'science_electives_required'
            )
        }),
        ('Additional Information', {
            'fields': ('additional_requirements',)
        }),
        ('Metadata', {
            'fields': ('updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SubjectGradeMapping)
class SubjectGradeMappingAdmin(admin.ModelAdmin):
    list_display = ['grade', 'numerical_value', 'description']
    list_editable = ['numerical_value', 'description']
    ordering = ['numerical_value']


@admin.register(AdmissionGuideline)
class AdmissionGuidelineAdmin(AdmissionGuidelineMediaAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'guide_type', 'order', 'is_active', 'updated_at']
    list_filter = ['guide_type', 'is_active']
    search_fields = ['title', 'content']
    list_editable = ['order', 'is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'guide_type', 'order', 'is_active')
        }),
        ('Content', {
            'fields': ('content', 'portal_url')
        }),
        ('Rich Media', {
            'fields': ('video_url', 'image'),
            'classes': ('collapse',)
        })
    )


@admin.register(EligibilityCheck)
class EligibilityCheckAdmin(AdmissionsAdminSite):
    change_list_template = 'admin/admissions/eligibilitycheck/change_list.html'
    
    list_display = [
        'full_name', 'shs_school', 'completion_year', 'preferred_program', 
        'admission_type', 'aggregate_score', 'is_eligible',
        'meets_regular_requirements', 'meets_feepaying_requirements',
        'email', 'phone', 'checked_at'
    ]
    
    list_filter = ['preferred_program', 'admission_type', 'is_eligible', 
                   'meets_regular_requirements', 'meets_feepaying_requirements', 
                   'completion_year', 'checked_at']
    search_fields = ['full_name', 'email', 'phone', 'shs_school']
    readonly_fields = [
        'checked_at', 'is_eligible', 'meets_regular_requirements', 
        'meets_feepaying_requirements', 'eligibility_details',
        'recommendations', 'ip_address', 'user_agent'
    ]
    date_hierarchy = 'checked_at'
    list_per_page = 50
    
    # Enable column selection
    list_display_links = ['full_name', 'email']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('full_name', 'email', 'phone', 'shs_school', 'completion_year', 
                      'preferred_program', 'admission_type')
        }),
        ('Aggregate', {
            'fields': ('aggregate_score',)
        }),
        ('Core Subjects', {
            'fields': (
                'core_math_grade',
                'english_grade',
                'integrated_science_grade',
                'social_studies_grade'
            )
        }),
        ('Elective Subjects', {
            'fields': (
                'elective_math_grade',
                'physics_grade',
                'chemistry_grade',
                'biology_grade',
                'elective_ict_grade'
            )
        }),
        ('Other Electives', {
            'fields': (
                'other_elective_1', 'other_elective_1_grade',
                'other_elective_2', 'other_elective_2_grade'
            ),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('is_eligible', 'meets_regular_requirements', 
                      'meets_feepaying_requirements', 'eligibility_details', 'recommendations')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'checked_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'order', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer']
    list_editable = ['order', 'is_active']
    
    fieldsets = (
        ('Question', {
            'fields': ('question', 'category', 'order', 'is_active')
        }),
        ('Answer', {
            'fields': ('answer',)
        })
    )


@admin.register(ImportantDate)
class ImportantDateAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'event_date', 'academic_year', 'is_active']
    list_filter = ['event_type', 'academic_year', 'is_active', 'event_date']
    search_fields = ['title', 'description']
    date_hierarchy = 'event_date'
    list_editable = ['is_active']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('title', 'event_type', 'event_date', 'academic_year')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )


@admin.register(WhatsAppHelpdesk)
class WhatsAppHelpdeskAdmin(admin.ModelAdmin):
    list_display = ['program', 'group_type', 'academic_year', 'access_count', 'is_active', 'created_at', 'updated_at']
    list_filter = ['program', 'group_type', 'academic_year', 'is_active', 'created_at']
    search_fields = ['program', 'academic_year', 'group_description']
    readonly_fields = ['access_count', 'created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Program Information', {
            'fields': ('program', 'group_type', 'academic_year', 'is_active'),
            'description': 'ADMISSION groups are for helpdesk. ACADEMIC groups are official class groups shown after accommodation registration.'
        }),
        ('WhatsApp Group', {
            'fields': ('whatsapp_group_link', 'group_description')
        }),
        ('Statistics', {
            'fields': ('access_count',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(WhatsAppAccessLog)
class WhatsAppAccessLogAdmin(admin.ModelAdmin):
    list_display = ['application_id', 'student_name', 'helpdesk', 'accessed_at', 'ip_address']
    list_filter = ['helpdesk', 'accessed_at']
    search_fields = ['application_id', 'student_name']
    readonly_fields = ['helpdesk', 'application_id', 'student_name', 'accessed_at', 'ip_address']
    date_hierarchy = 'accessed_at'
    
    def has_add_permission(self, request):
        """Prevent manual addition - created automatically via API"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make read-only"""
        return False


@admin.register(KNUSTAdmission)
class KNUSTAdmissionAdmin(admin.ModelAdmin):
    list_display = [
        'applicant_id', 'name', 'programme_code', 'academic_year', 
        'admission_status', 'accommodation_type', 'campus_status', 
        'accommodation_verified', 'source', 'fetched_at'
    ]
    list_filter = [
        'academic_year', 'programme_code', 'admission_status', 'source',
        'accommodation_type', 'campus_status', 'hall_name', 'accommodation_verified',
        'fetched_at'
    ]
    search_fields = ['applicant_id', 'name', 'programme', 'phone_number', 'room_number', 'hostel_name']
    readonly_fields = ['fetched_at', 'updated_at', 'accommodation_updated_at']
    date_hierarchy = 'fetched_at'
    list_per_page = 50
    
    fieldsets = (
        ('Applicant Information', {
            'fields': ('applicant_id', 'name', 'programme', 'programme_code')
        }),
        ('Admission Details', {
            'fields': ('academic_year', 'admission_status', 'status')
        }),
        ('Accommodation Details', {
            'fields': (
                'accommodation_type', 'campus_status', 
                'hall_name', 'hostel_name', 'room_number',
                'phone_number', 'accommodation_verified', 'accommodation_updated_at'
            ),
            'description': 'Student accommodation information'
        }),
        ('Source & Timestamps', {
            'fields': ('source', 'fetched_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        """Allow manual addition for edge cases"""
        return True
    
    def has_change_permission(self, request, obj=None):
        """Allow editing"""
        return True

