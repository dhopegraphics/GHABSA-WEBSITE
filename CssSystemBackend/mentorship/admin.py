"""
Mentorship System - Admin Configuration

Provides comprehensive admin interface for managing:
- Mentorship Areas and Skill Tags
- Interviewers and their Schedules
- Mentor Applications (view, interview, approve/reject)
- Mentee Applications
- Mentorship Relationships
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from mentorship.models import (
    MentorshipArea,
    SkillTag,
    Interviewer,
    InterviewerSchedule,
    MentorApplication,
    ApprovedMentor,
    MenteeApplication,
    MentorshipRelationship,
    MentorshipSession,
    MentorPayment,
)


# ===========================
# Inline Admin Classes
# ===========================

class SkillTagInline(admin.TabularInline):
    """Inline for managing skill tags within an area"""
    model = SkillTag
    extra = 3
    fields = ['name', 'description', 'is_active', 'order']
    ordering = ['order', 'name']


class InterviewerScheduleInline(admin.TabularInline):
    """Inline for managing interviewer schedules"""
    model = InterviewerSchedule
    extra = 1
    fields = ['date', 'start_time', 'end_time', 'interview_type', 'location', 'meeting_link', 'is_booked', 'is_active']
    ordering = ['date', 'start_time']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Show only future schedules by default
        return qs.filter(date__gte=timezone.now().date())


class MentorshipSessionInline(admin.TabularInline):
    """Inline for viewing sessions within a relationship"""
    model = MentorshipSession
    extra = 0
    fields = ['date', 'start_time', 'end_time', 'session_type', 'status', 'rating']
    readonly_fields = ['rating']
    ordering = ['-date']


# ===========================
# Mentorship Area Admin
# ===========================

@admin.register(MentorshipArea)
class MentorshipAreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'color_preview', 'mentor_count', 'tag_count', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']
    inlines = [SkillTagInline]
    change_list_template = 'admin/mentorship/mentorshiparea_changelist.html'
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        ('Display Settings', {
            'fields': ('icon', 'color', 'order', 'is_active')
        }),
    )
    
    def color_preview(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 5px 15px; border-radius: 3px; color: white;">{}</span>',
            obj.color, obj.color
        )
    color_preview.short_description = 'Color'
    
    def mentor_count(self, obj):
        count = obj.approved_mentors.filter(is_active=True).count()
        return format_html('<b>{}</b>', count)
    mentor_count.short_description = 'Active Mentors'
    
    def tag_count(self, obj):
        return obj.tags.count()
    tag_count.short_description = 'Tags'


# ===========================
# Skill Tag Admin
# ===========================

@admin.register(SkillTag)
class SkillTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'area', 'is_active', 'order', 'mentor_usage', 'mentee_usage']
    list_filter = ['area', 'is_active']
    search_fields = ['name', 'description', 'area__name']
    list_editable = ['order', 'is_active']
    autocomplete_fields = ['area']
    
    def mentor_usage(self, obj):
        return obj.mentor_applications.count()
    mentor_usage.short_description = 'Mentors Using'
    
    def mentee_usage(self, obj):
        return obj.mentee_learning_goals.count()
    mentee_usage.short_description = 'Mentees Learning'


# ===========================
# Interviewer Admin
# ===========================

@admin.register(Interviewer)
class InterviewerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user_email', 'areas_list', 'schedule_count', 'pending_interviews', 'is_active']
    list_filter = ['is_active', 'areas']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone']
    filter_horizontal = ['areas']
    inlines = [InterviewerScheduleInline]
    
    fieldsets = (
        ('Staff Member', {
            'fields': ('user',)
        }),
        ('Profile', {
            'fields': ('bio', 'profile_image', 'areas')
        }),
        ('Settings', {
            'fields': ('max_daily_interviews', 'is_active')
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Name'
    
    def user_email(self, obj):
        return obj.user.personal_email or obj.user.student_email or '-'
    user_email.short_description = 'Email'
    
    def areas_list(self, obj):
        areas = obj.areas.all()[:3]
        names = ', '.join([a.name for a in areas])
        if obj.areas.count() > 3:
            names += f' (+{obj.areas.count() - 3} more)'
        return names
    areas_list.short_description = 'Areas'
    
    def schedule_count(self, obj):
        future = obj.schedules.filter(date__gte=timezone.now().date(), is_active=True).count()
        return format_html('<b>{}</b> upcoming', future)
    schedule_count.short_description = 'Schedules'
    
    def pending_interviews(self, obj):
        count = obj.assigned_applications.filter(status='interview_scheduled').count()
        if count > 0:
            return format_html('<span style="color: orange;"><b>{}</b></span>', count)
        return '0'
    pending_interviews.short_description = 'Pending'


# ===========================
# Interviewer Schedule Admin
# ===========================

@admin.register(InterviewerSchedule)
class InterviewerScheduleAdmin(admin.ModelAdmin):
    list_display = ['interviewer', 'date', 'time_slot', 'interview_type', 'status_badge', 'booked_by']
    list_filter = ['interview_type', 'is_booked', 'is_active', 'date', 'interviewer']
    search_fields = ['interviewer__user__first_name', 'interviewer__user__last_name']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Interviewer', {
            'fields': ('interviewer',)
        }),
        ('Schedule', {
            'fields': ('date', 'start_time', 'end_time', 'interview_type')
        }),
        ('Location', {
            'fields': ('location', 'meeting_link'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_booked', 'is_active', 'notes')
        }),
    )
    
    def time_slot(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_slot.short_description = 'Time'
    
    def status_badge(self, obj):
        if obj.is_booked:
            return format_html('<span style="color: red;">Booked</span>')
        elif not obj.is_active:
            return format_html('<span style="color: gray;">Inactive</span>')
        elif obj.date < timezone.now().date():
            return format_html('<span style="color: gray;">Past</span>')
        return format_html('<span style="color: green;">Available</span>')
    status_badge.short_description = 'Status'
    
    def booked_by(self, obj):
        if hasattr(obj, 'booked_application') and obj.booked_application:
            app = obj.booked_application
            return format_html(
                '<a href="{}">{} {}</a>',
                reverse('admin:mentorship_mentorapplication_change', args=[app.id]),
                app.applicant.first_name,
                app.applicant.last_name
            )
        return '-'
    booked_by.short_description = 'Booked By'


# ===========================
# Mentor Application Admin
# ===========================

@admin.register(MentorApplication)
class MentorApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'applicant_name', 'applicant_year', 'areas_list', 'status_badge', 
        'assigned_interviewer', 'interview_date', 'created_at'
    ]
    list_filter = ['status', 'session_type', 'mentee_capacity', 'areas', 'created_at']
    search_fields = ['applicant__first_name', 'applicant__last_name', 'applicant__phone']
    readonly_fields = [
        'created_at', 'updated_at', 'submitted_at', 'interview_completed_at',
        'approved_at', 'rejected_at', 'applicant_details'
    ]
    filter_horizontal = ['areas', 'skills']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Applicant Information', {
            'fields': ('applicant', 'applicant_details', 'status')
        }),
        ('Mentorship Areas & Skills', {
            'fields': ('areas', 'skills', 'additional_skills', 'experience_description')
        }),
        ('Incentive Preferences', {
            'fields': ('incentive_preferences',),
            'classes': ('collapse',)
        }),
        ('Session Preferences', {
            'fields': ('session_type', 'mentee_capacity')
        }),
        ('Availability', {
            'fields': ('available_days', 'sessions_per_semester', 'available_time_start', 'available_time_end'),
            'classes': ('collapse',)
        }),
        ('Resource Requirements', {
            'fields': ('needs_classroom', 'needs_data_support', 'other_resources'),
            'classes': ('collapse',)
        }),
        ('Interview', {
            'fields': (
                'assigned_interviewer', 'interview_schedule', 'interview_link',
                'interview_notes', 'interview_completed_at'
            )
        }),
        ('Approval', {
            'fields': ('approved_by', 'approval_notes', 'approved_at', 'rejection_reason', 'rejected_at')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_applications', 'reject_applications', 'send_interview_reminder']
    
    def applicant_name(self, obj):
        return f"{obj.applicant.first_name} {obj.applicant.last_name}"
    applicant_name.short_description = 'Applicant'
    
    def applicant_year(self, obj):
        return obj.applicant.get_year()
    applicant_year.short_description = 'Year'
    
    def applicant_details(self, obj):
        user = obj.applicant
        return format_html(
            '<div style="line-height: 1.8;">'
            '<b>Name:</b> {} {} {}<br>'
            '<b>Phone:</b> {}<br>'
            '<b>Year:</b> {}<br>'
            '<b>Program:</b> {}<br>'
            '</div>',
            user.first_name, user.middle_name or '', user.last_name,
            user.phone,
            user.get_year(),
            user.get_program_display_name()
        )
    applicant_details.short_description = 'Applicant Details'
    
    def areas_list(self, obj):
        areas = obj.areas.all()[:2]
        names = ', '.join([a.name for a in areas])
        if obj.areas.count() > 2:
            names += f' (+{obj.areas.count() - 2})'
        return names
    areas_list.short_description = 'Areas'
    
    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'submitted': 'blue',
            'interview_scheduled': 'orange',
            'interview_completed': 'purple',
            'approved': 'green',
            'rejected': 'red',
            'withdrawn': 'gray',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def interview_date(self, obj):
        if obj.interview_schedule:
            return obj.interview_schedule.date
        return '-'
    interview_date.short_description = 'Interview Date'
    
    def approve_applications(self, request, queryset):
        """Bulk approve applications (only for interview_completed status)"""
        if not request.user.is_superuser:
            self.message_user(request, "Only superusers can bulk approve.", level=messages.ERROR)
            return
        
        approved = 0
        for app in queryset.filter(status='interview_completed'):
            if app.assigned_interviewer:
                try:
                    app.status = 'approved'
                    app.approved_at = timezone.now()
                    app.save()
                    
                    # Create ApprovedMentor profile
                    mentor_profile, created = ApprovedMentor.objects.get_or_create(
                        user=app.applicant,
                        defaults={'application': app}
                    )
                    mentor_profile.areas.set(app.areas.all())
                    mentor_profile.skills.set(app.skills.all())
                    approved += 1
                except Exception:
                    pass
        
        self.message_user(request, f"Approved {approved} applications.", level=messages.SUCCESS)
    approve_applications.short_description = "Approve selected applications"
    
    def reject_applications(self, request, queryset):
        """Bulk reject applications"""
        rejected = queryset.filter(status__in=['submitted', 'interview_scheduled', 'interview_completed']).update(
            status='rejected',
            rejected_at=timezone.now()
        )
        self.message_user(request, f"Rejected {rejected} applications.", level=messages.WARNING)
    reject_applications.short_description = "Reject selected applications"
    
    def send_interview_reminder(self, request, queryset):
        """Send interview reminder to scheduled applicants"""
        # This would integrate with your notification system
        count = queryset.filter(status='interview_scheduled').count()
        self.message_user(request, f"Reminder sent to {count} applicants.", level=messages.INFO)
    send_interview_reminder.short_description = "Send interview reminder"


# ===========================
# Approved Mentor Admin
# ===========================

@admin.register(ApprovedMentor)
class ApprovedMentorAdmin(admin.ModelAdmin):
    """
    ApprovedMentor admin - Created automatically when mentor application is approved.
    Only status fields can be edited.
    """
    list_display = [
        'full_name', 'areas_list', 'current_mentees', 'available_slots',
        'average_rating', 'is_active', 'is_accepting_mentees'
    ]
    list_filter = ['is_active', 'is_accepting_mentees', 'areas']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone']
    readonly_fields = [
        'user', 'application', 'total_mentees', 'current_mentees', 
        'completed_sessions', 'average_rating', 'total_ratings', 'created_at', 'updated_at'
    ]
    filter_horizontal = ['areas', 'skills']
    
    fieldsets = (
        ('Mentor', {
            'fields': ('user', 'application')
        }),
        ('Expertise', {
            'fields': ('areas', 'skills'),
            'description': 'Areas and skills can be updated by admin if needed.'
        }),
        ('Status (Editable)', {
            'fields': ('is_active', 'is_accepting_mentees'),
            'description': 'Toggle these to control mentor visibility and availability.'
        }),
        ('Statistics (Read Only)', {
            'fields': ('total_mentees', 'current_mentees', 'completed_sessions', 'average_rating', 'total_ratings')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Approved mentors are created when applications are approved, not manually"""
        return False
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Name'
    
    def areas_list(self, obj):
        return ', '.join([a.name for a in obj.areas.all()[:3]])
    areas_list.short_description = 'Areas'
    
    def available_slots(self, obj):
        slots = obj.available_slots
        if slots > 0:
            return format_html('<span style="color: green;">{}</span>', slots)
        return format_html('<span style="color: red;">0</span>')
    available_slots.short_description = 'Slots'


# ===========================
# Mentee Application Admin
# ===========================

@admin.register(MenteeApplication)
class MenteeApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant_name', 'mentor_name', 'area', 'status_badge', 'offering_type', 'created_at']
    list_filter = ['status', 'area', 'offering_type', 'created_at']
    search_fields = [
        'applicant__first_name', 'applicant__last_name',
        'mentor__user__first_name', 'mentor__user__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'responded_at']
    filter_horizontal = ['current_skills', 'skills_to_learn']
    
    fieldsets = (
        ('Application', {
            'fields': ('applicant', 'mentor', 'area', 'status')
        }),
        ('Current Skills', {
            'fields': ('current_skills', 'skills_description')
        }),
        ('Learning Goals', {
            'fields': ('skills_to_learn', 'learning_goals')
        }),
        ('Offering to Mentor', {
            'fields': ('offering_type', 'offering_description', 'offering_amount'),
            'classes': ('collapse',)
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Mentor Response', {
            'fields': ('mentor_response', 'responded_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def applicant_name(self, obj):
        return f"{obj.applicant.first_name} {obj.applicant.last_name}"
    applicant_name.short_description = 'Applicant'
    
    def mentor_name(self, obj):
        return obj.mentor.full_name
    mentor_name.short_description = 'Mentor'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'accepted': 'green',
            'rejected': 'red',
            'withdrawn': 'gray',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# ===========================
# Mentorship Relationship Admin
# ===========================

@admin.register(MentorshipRelationship)
class MentorshipRelationshipAdmin(admin.ModelAdmin):
    """
    MentorshipRelationship admin - Created automatically when mentee application is accepted.
    Status and session tracking can be updated by admin.
    """
    list_display = ['mentor_name', 'mentee_name', 'area', 'status_badge', 'sessions_completed', 'started_at']
    list_filter = ['status', 'area', 'started_at']
    search_fields = [
        'mentor__user__first_name', 'mentor__user__last_name',
        'mentee__first_name', 'mentee__last_name'
    ]
    readonly_fields = ['mentor', 'mentee', 'area', 'from_application', 'started_at', 'completed_at', 'updated_at']
    inlines = [MentorshipSessionInline]
    
    fieldsets = (
        ('Relationship (Read Only)', {
            'fields': ('mentor', 'mentee', 'area', 'from_application'),
            'description': 'Relationships are created when mentee applications are accepted.'
        }),
        ('Status (Editable)', {
            'fields': ('status',),
            'description': 'Change status to pause, complete, or terminate the relationship.'
        }),
        ('Session Tracking', {
            'fields': ('sessions_completed', 'last_session_date', 'next_session_date')
        }),
        ('Notes', {
            'fields': ('mentor_notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Relationships are created when mentee applications are accepted, not manually"""
        return False
    
    def mentor_name(self, obj):
        return obj.mentor.full_name
    mentor_name.short_description = 'Mentor'
    
    def mentee_name(self, obj):
        return f"{obj.mentee.first_name} {obj.mentee.last_name}"
    mentee_name.short_description = 'Mentee'
    
    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'paused': 'orange',
            'completed': 'blue',
            'terminated': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# ===========================
# Mentorship Session Admin
# ===========================

@admin.register(MentorshipSession)
class MentorshipSessionAdmin(admin.ModelAdmin):
    list_display = ['relationship', 'mentor_name', 'mentee_name', 'date', 'time_slot', 'session_type', 'status', 'rating']
    list_filter = ['status', 'session_type', 'date']
    search_fields = [
        'relationship__mentor__user__first_name',
        'relationship__mentee__first_name'
    ]
    date_hierarchy = 'date'
    autocomplete_fields = ['relationship']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('relationship', 'date', 'start_time', 'end_time', 'session_type', 'status')
        }),
        ('Location', {
            'fields': ('location', 'meeting_link'),
            'classes': ('collapse',)
        }),
        ('Notes & Feedback', {
            'fields': ('agenda', 'mentor_notes', 'mentee_feedback', 'rating'),
            'classes': ('collapse',)
        }),
    )
    
    def time_slot(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_slot.short_description = 'Time'
    
    def mentor_name(self, obj):
        return obj.relationship.mentor.full_name
    mentor_name.short_description = 'Mentor'
    
    def mentee_name(self, obj):
        return f"{obj.relationship.mentee.first_name} {obj.relationship.mentee.last_name}"
    mentee_name.short_description = 'Mentee'


# ===========================
# Mentor Payment Admin
# ===========================

@admin.register(MentorPayment)
class MentorPaymentAdmin(admin.ModelAdmin):
    """
    MentorPayment admin - READ ONLY.
    Payments are created through the payment system, not manually.
    """
    list_display = ['mentor_name', 'amount', 'payment_type', 'status_badge', 'mentee_name', 'transaction_link', 'created_at']
    list_filter = ['status', 'payment_type', 'created_at']
    search_fields = ['mentor__user__first_name', 'mentee__first_name', 'transaction_reference']
    readonly_fields = [
        'mentor', 'mentee', 'relationship', 'amount', 'payment_type', 
        'status', 'transaction', 'transaction_reference', 'description',
        'callback_url', 'created_at', 'completed_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('mentor', 'mentee', 'relationship', 'amount', 'payment_type', 'status')
        }),
        ('Transaction (Linked to Payment System)', {
            'fields': ('transaction', 'transaction_reference')
        }),
        ('Additional Info', {
            'fields': ('description', 'callback_url'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Payments are created through the payment system, not admin"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of payment records"""
        return False
    
    def mentor_name(self, obj):
        return obj.mentor.full_name
    mentor_name.short_description = 'Mentor'
    
    def mentee_name(self, obj):
        if obj.mentee:
            return f"{obj.mentee.first_name} {obj.mentee.last_name}"
        return '-'
    mentee_name.short_description = 'Mentee'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'refunded': 'purple',
            'cancelled': 'gray',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def transaction_link(self, obj):
        if obj.transaction:
            url = reverse('admin:payments_transaction_change', args=[obj.transaction.id])
            return format_html('<a href="{}">{}</a>', url, obj.transaction_reference)
        elif obj.transaction_reference:
            return obj.transaction_reference
        return '-'
    transaction_link.short_description = 'Transaction'


# ===========================
# Analytics Dashboard
# ===========================

@staff_member_required
def mentorship_analytics(request):
    """Analytics dashboard for the mentorship system"""
    
    # Basic counts
    total_areas = MentorshipArea.objects.filter(is_active=True).count()
    total_mentors = ApprovedMentor.objects.filter(is_active=True).count()
    total_mentees = MentorshipRelationship.objects.values('mentee').distinct().count()
    active_relationships = MentorshipRelationship.objects.filter(status='active').count()
    
    # Application stats
    pending_mentor_apps = MentorApplication.objects.filter(
        status__in=['submitted', 'interview_scheduled']
    ).count()
    pending_mentee_apps = MenteeApplication.objects.filter(status='pending').count()
    
    # Recent applications
    recent_mentor_apps = MentorApplication.objects.order_by('-created_at')[:5]
    recent_mentee_apps = MenteeApplication.objects.order_by('-created_at')[:5]
    
    # Area popularity
    area_stats = MentorshipArea.objects.annotate(
        mentor_count=Count('approved_mentors', filter=Q(approved_mentors__is_active=True)),
        relationship_count=Count('mentorship_relationships', filter=Q(mentorship_relationships__status='active'))
    ).order_by('-mentor_count')[:10]
    
    context = {
        'total_areas': total_areas,
        'total_mentors': total_mentors,
        'total_mentees': total_mentees,
        'active_relationships': active_relationships,
        'pending_mentor_apps': pending_mentor_apps,
        'pending_mentee_apps': pending_mentee_apps,
        'recent_mentor_apps': recent_mentor_apps,
        'recent_mentee_apps': recent_mentee_apps,
        'area_stats': area_stats,
    }
    
    return render(request, 'admin/mentorship/analytics.html', context)


# Register the analytics URL in the default admin site
# Override get_urls to add custom analytics view
original_get_urls = admin.site.get_urls

def get_urls_with_analytics():
    urls = original_get_urls()
    custom_urls = [
        path('mentorship/analytics/', admin.site.admin_view(mentorship_analytics), name='mentorship-analytics'),
    ]
    return custom_urls + urls

admin.site.get_urls = get_urls_with_analytics
