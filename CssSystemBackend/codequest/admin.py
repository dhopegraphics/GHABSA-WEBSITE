"""
Admin interface for Code Quest Management System
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.db.models import Count, Q
from django import forms
from utils.media_mixins import make_media_admin_mixin

from codequest.models import (
    CodeQuestEvent,
    CodeQuestParticipant,
    CodeQuestGroup,
    ProjectManagerCandidate,
    ProjectManagerVote,
    GroupMemberRole,
    CodeQuestProject,
    CodeQuestConsultant,
    ConsultantGroupAssignment,
    ScoringCriteria,
    CodeQuestFacilitator,
    ProjectScore,
    FinalProjectScore,
    ProjectTask,
    # Self-Grouping Models
    SelfGroupingTeam,
    SelfGroupingMembership,
    GroupInvitation,
    JoinRequest
)
from codequest import utils as codequest_utils

# Create media admin mixins for models with file fields
CodeQuestProjectMediaAdminMixin = make_media_admin_mixin(['app_logo'])
CodeQuestConsultantMediaAdminMixin = make_media_admin_mixin(['profile_image'])


# ===============================
# Inline Admin Classes
# ===============================

class CodeQuestParticipantInline(admin.TabularInline):
    model = CodeQuestParticipant
    extra = 0
    fields = ('student_id', 'student_name', 'email', 'year', 'group', 'access_key', 'user')
    readonly_fields = ('student_id', 'student_name', 'email', 'year', 'access_key', 'user')
    can_delete = False
    
    # Admins cannot add participants - students register themselves
    def has_add_permission(self, request, obj=None):
        return False


class CodeQuestGroupInline(admin.TabularInline):
    model = CodeQuestGroup
    extra = 0
    fields = ('group_number', 'category', 'project_manager', 'consultant')
    readonly_fields = ('group_number',)
    can_delete = False


class GroupMemberRoleInline(admin.TabularInline):
    model = GroupMemberRole
    extra = 0
    fields = ('participant', 'role_type', 'is_lead', 'assigned_by', 'assigned_date')
    readonly_fields = ('participant', 'role_type', 'is_lead', 'assigned_by', 'assigned_date')
    
    # Admins cannot add roles - Project Manager assigns roles
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


class ProjectManagerCandidateInline(admin.TabularInline):
    model = ProjectManagerCandidate
    extra = 0
    fields = ('participant', 'vote_count', 'is_winner', 'nomination_date')
    readonly_fields = ('participant', 'nomination_statement', 'vote_count', 'nomination_date')
    
    # Admins cannot add PM candidates - students nominate themselves
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


class ProjectTaskInline(admin.TabularInline):
    model = ProjectTask
    extra = 0
    fields = ('task_title', 'assigned_to', 'priority', 'status', 'due_date', 'created_at')
    readonly_fields = ('task_title', 'assigned_to', 'priority', 'status', 'due_date', 'created_at', 'created_by')
    
    # Admins cannot add tasks - Project Manager creates tasks
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


class ConsultantGroupAssignmentInline(admin.TabularInline):
    model = ConsultantGroupAssignment
    extra = 0
    fields = ('group', 'assigned_by', 'assigned_date', 'is_active')
    readonly_fields = ('assigned_by', 'assigned_date')


class ScoringCriteriaInline(admin.StackedInline):
    model = ScoringCriteria
    extra = 0
    fields = ('criteria_name', 'max_points', 'percentage_weight', 'order')


class ProjectScoreInline(admin.TabularInline):
    model = ProjectScore
    extra = 0
    fields = ('facilitator', 'criteria', 'score', 'created_at')
    readonly_fields = ('facilitator', 'criteria', 'score', 'created_at')
    
    # Admins cannot add scores - Facilitators score projects
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ===============================
# Main Admin Classes
# ===============================

@admin.register(CodeQuestEvent)
class CodeQuestEventAdmin(admin.ModelAdmin):
    list_display = (
        'event_name',
        'academic_year',
        'status_badge',
        'participant_count',
        'group_count',
        'registration_dates',
        'venue_details'
    )
    list_filter = ('status', 'academic_year', 'semester')
    search_fields = ('event__title', 'academic_year', 'course_code', 'course_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event', 'academic_year', 'semester', 'course_code', 'course_name', 'status')
        }),
        ('Timeline', {
            'fields': (
                'registration_start_date',
                'registration_end_date',
                'grouping_date',
                'voting_start_date',
                'voting_end_date',
                'project_submission_deadline',
                'presentation_date'
            )
        }),
        ('Event Details', {
            'fields': ('venue_details',)
        }),
        ('Configuration', {
            'fields': ('max_group_size', 'min_group_size', 'allow_self_grouping')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ScoringCriteriaInline]
    
    actions = ['activate_event', 'complete_event', 'group_participants', 'assign_consultants']
    
    def event_name(self, obj):
        return obj.event.event_name
    event_name.short_description = 'Event'
    
    def status_badge(self, obj):
        colors = {
            'draft': '#9E9E9E',
            'registration_open': '#4CAF50',
            'grouping': '#2196F3',
            'voting': '#9C27B0',
            'development': '#00BCD4',
            'presentation': '#FF9800',
            'completed': '#757575',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def participant_count(self, obj):
        count = CodeQuestParticipant.objects.filter(event=obj).count()
        return format_html('<strong>{}</strong> participants', count)
    participant_count.short_description = 'Participants'
    
    def group_count(self, obj):
        count = CodeQuestGroup.objects.filter(event=obj).count()
        return format_html('<strong>{}</strong> groups', count)
    group_count.short_description = 'Groups'
    
    def registration_dates(self, obj):
        return f"{obj.registration_start_date.strftime('%b %d')} - {obj.registration_end_date.strftime('%b %d, %Y')}"
    registration_dates.short_description = 'Registration Period'
    
    def activate_event(self, request, queryset):
        queryset.update(status='development')
        self.message_user(request, f"{queryset.count()} event(s) activated")
    activate_event.short_description = "Activate selected events"
    
    def complete_event(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"{queryset.count()} event(s) marked as completed")
    complete_event.short_description = "Mark as completed"
    
    def group_participants(self, request, queryset):
        for event in queryset:
            participants = CodeQuestParticipant.objects.filter(event=event, group__isnull=True)
            if participants.exists():
                groups = codequest_utils.group_participants_automatically(event, participants)
                self.message_user(request, f"Created {len(groups)} groups for {event.event.event_name}")
            else:
                self.message_user(request, f"No ungrouped participants for {event.event.event_name}", level='warning')
    group_participants.short_description = "Auto-group participants"
    
    def assign_consultants(self, request, queryset):
        for event in queryset:
            consultants = CodeQuestConsultant.objects.filter(event=event, is_approved=True)
            groups = CodeQuestGroup.objects.filter(event=event, consultant__isnull=True)
            if consultants.exists() and groups.exists():
                assignments = codequest_utils.assign_consultants_randomly(event, consultants, groups)
                self.message_user(request, f"Assigned consultants to {len(assignments)} groups for {event.event.title}")
            else:
                self.message_user(request, f"No consultants or groups available for {event.event.title}", level='warning')
    assign_consultants.short_description = "Auto-assign consultants"


@admin.register(CodeQuestParticipant)
class CodeQuestParticipantAdmin(admin.ModelAdmin):
    list_display = (
        'student_name',
        'student_id',
        'email',
        'year',
        'linked_user_display',
        'group_info',
        'pm_status',
        'access_key_display',
        'registration_date'
    )
    list_filter = ('event', 'year', 'is_deferred')
    search_fields = ('student_name', 'student_id', 'email', 'access_key')
    readonly_fields = ('student_id', 'student_name', 'email', 'phone_number', 'user', 'access_key', 'registration_date')
    
    # 🚫 Admins CANNOT create participants - students register themselves
    def has_add_permission(self, request):
        return False
    
    def linked_user_display(self, obj):
        if obj.user:
            return format_html('<span style="color: green;">✓ {}</span>', f"{obj.user.first_name} {obj.user.last_name}")
        return format_html('<span style="color: gray;">—</span>')
    linked_user_display.short_description = 'Linked User'
    
    fieldsets = (
        ('Linked User Account', {
            'fields': ('user',),
            'description': 'The CSS user account linked to this registration'
        }),
        ('Student Information', {
            'fields': ('student_id', 'student_name', 'email', 'phone_number')
        }),
        ('Academic Details', {
            'fields': ('event', 'year', 'is_deferred')
        }),
        ('Preferences & Skills', {
            'fields': ('preferred_role', 'skills')
        }),
        ('Group Assignment', {
            'fields': ('group',)
        }),
        ('Access Information', {
            'fields': ('access_key', 'registration_date'),
            'classes': ('collapse',)
        }),
    )
    
    def group_info(self, obj):
        if obj.group:
            return f"Group {obj.group.group_number}"
        return format_html('<span style="color: red;">Not grouped</span>')
    group_info.short_description = 'Group'
    
    def pm_status(self, obj):
        if obj.group and obj.group.project_manager == obj:
            return format_html('<span style="color: green; font-weight: bold;">✓ PM</span>')
        return '-'
    pm_status.short_description = 'PM'
    
    def access_key_display(self, obj):
        return format_html('<code>{}</code>', obj.access_key)
    access_key_display.short_description = 'Access Key'


class CodeQuestProjectInline(admin.StackedInline):
    model = CodeQuestProject
    extra = 0
    fields = ('app_name', 'app_description', 'is_approved', 'admin_feedback')
    readonly_fields = ('app_name', 'app_description', 'tech_stack_frontend', 'tech_stack_backend', 'repository_url')
    can_delete = False
    
    # Admins cannot create projects - groups submit their own projects
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CodeQuestGroup)
class CodeQuestGroupAdmin(admin.ModelAdmin):
    list_display = (
        'group_display',
        'event',
        'category',
        'member_count',
        'pm_display',
        'consultant_display',
        'project_status',
        'formation_date'
    )
    list_filter = ('event', 'category')
    search_fields = ('group_number', 'project_manager__student_name', 'consultant__name')
    readonly_fields = ('formation_date',)
    
    fieldsets = (
        ('Group Information', {
            'fields': ('event', 'group_number', 'group_name', 'category')
        }),
        ('Leadership', {
            'fields': ('project_manager',)
        }),
        ('Mentorship', {
            'fields': ('consultant',)
        }),
        ('Status', {
            'fields': ('is_complete',)
        }),
        ('Metadata', {
            'fields': ('formation_date',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [GroupMemberRoleInline, ProjectManagerCandidateInline, CodeQuestProjectInline]
    
    actions = ['end_pm_elections']
    
    def group_display(self, obj):
        return f"Group {obj.group_number}"
    group_display.short_description = 'Group'
    
    def member_count(self, obj):
        count = obj.members.count()
        return format_html('<strong>{}</strong> members', count)
    member_count.short_description = 'Members'
    
    def pm_display(self, obj):
        if obj.project_manager:
            return obj.project_manager.student_name
        return format_html('<span style="color: orange;">No PM</span>')
    pm_display.short_description = 'Project Manager'
    
    def consultant_display(self, obj):
        if obj.consultant:
            return obj.consultant.name
        return format_html('<span style="color: orange;">No Consultant</span>')
    consultant_display.short_description = 'Consultant'
    
    def project_status(self, obj):
        try:
            project = obj.project
            if project.is_approved:
                return format_html('<span style="color: green;">✓ Approved</span>')
            return format_html('<span style="color: orange;">Pending</span>')
        except:
            return format_html('<span style="color: red;">No Project</span>')
    project_status.short_description = 'Project'
    
    def end_pm_elections(self, request, queryset):
        for group in queryset:
            winner = codequest_utils.end_pm_election(group)
            if winner:
                self.message_user(request, f"{winner.participant.student_name} is now PM of Group {group.group_number}")
            else:
                self.message_user(request, f"No candidates for Group {group.group_number}", level='warning')
    end_pm_elections.short_description = "End PM election and declare winner"


@admin.register(ProjectManagerCandidate)
class ProjectManagerCandidateAdmin(admin.ModelAdmin):
    list_display = (
        'participant_name',
        'group',
        'vote_count',
        'winner_badge',
        'nomination_date'
    )
    list_filter = ('is_winner', 'group__event')
    search_fields = ('participant__student_name', 'participant__student_id')
    readonly_fields = ('participant', 'group', 'nomination_statement', 'vote_count', 'nomination_date', 'is_winner')
    
    # 🚫 Admins CANNOT create PM candidates - students nominate themselves
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def participant_name(self, obj):
        return obj.participant.student_name
    participant_name.short_description = 'Candidate'
    
    def winner_badge(self, obj):
        if obj.is_winner:
            return format_html('<span style="color: gold; font-weight: bold;">★ WINNER</span>')
        return '-'
    winner_badge.short_description = 'Status'


@admin.register(ProjectManagerVote)
class ProjectManagerVoteAdmin(admin.ModelAdmin):
    list_display = ('voter', 'candidate', 'group', 'vote_date')
    list_filter = ('group__event', 'group')
    search_fields = ('voter__student_name', 'candidate__participant__student_name')
    readonly_fields = ('voter', 'candidate', 'group', 'vote_date')
    
    # 🚫 Admins CANNOT create or edit votes - students vote for their PM
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    # ✅ Admins CAN delete fraudulent votes
    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(GroupMemberRole)
class GroupMemberRoleAdmin(admin.ModelAdmin):
    list_display = ('participant_display', 'group', 'role_type', 'lead_badge', 'assigned_by_display', 'assigned_date')
    list_filter = ('role_type', 'is_lead', 'group__event')
    search_fields = ('participant__student_name', 'group__group_number')
    readonly_fields = ('participant', 'group', 'role_type', 'assigned_by', 'assigned_date', 'is_lead')
    
    # 🚫 Admins CANNOT create or edit roles - Project Manager assigns roles
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    # ✅ Admins CAN delete roles if needed
    def has_delete_permission(self, request, obj=None):
        return True
    
    def participant_display(self, obj):
        return obj.participant.student_name
    participant_display.short_description = 'Member'
    
    def lead_badge(self, obj):
        if obj.is_lead:
            return format_html('<span style="color: blue;">★ LEAD</span>')
        return '-'
    lead_badge.short_description = 'Lead'
    
    def assigned_by_display(self, obj):
        if obj.assigned_by:
            return obj.assigned_by.student_name
        return 'System'
    assigned_by_display.short_description = 'Assigned By'


@admin.register(CodeQuestProject)
class CodeQuestProjectAdmin(CodeQuestProjectMediaAdminMixin, admin.ModelAdmin):
    list_display = (
        'app_name',
        'group',
        'category_badge',
        'approval_status',
        'logo_preview',
        'submission_date'
    )
    list_filter = ('is_approved', 'group__event', 'group__category')
    search_fields = ('app_name', 'group__group_number', 'app_description')
    readonly_fields = ('group', 'app_name', 'app_description', 'inspiration_app', 'app_logo', 'app_logo_url',
                      'tech_stack_frontend', 'tech_stack_backend', 'repository_url', 'live_demo_url',
                      'submission_date', 'logo_preview_large')
    
    # 🚫 Admins CANNOT create projects - groups submit their own projects
    def has_add_permission(self, request):
        return False
    
    fieldsets = (
        ('Project Information', {
            'fields': ('group', 'app_name', 'app_description', 'inspiration_app', ('app_logo', 'app_logo_url')),
            'description': 'Upload logo OR provide Google Drive/Dropbox link'
        }),
        ('Technical Details', {
            'fields': (
                'tech_stack_frontend',
                'tech_stack_backend',
                'repository_url',
                'live_demo_url'
            )
        }),
        ('Approval', {
            'fields': ('is_approved', 'admin_feedback')
        }),
        ('Metadata', {
            'fields': ('submission_date', 'logo_preview_large'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_projects', 'reject_projects']
    
    def category_badge(self, obj):
        colors = {
            'REGULAR': '#4CAF50',
            'DEFERRED_MIXED': '#FF9800',
            'DEFERRED_ONLY': '#f44336',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.group.category, '#000'),
            obj.group.get_category_display()
        )
    category_badge.short_description = 'Category'
    
    def approval_status(self, obj):
        if obj.is_approved:
            return format_html('<span style="color: green; font-weight: bold;">✓ APPROVED</span>')
        return format_html('<span style="color: orange;">PENDING</span>')
    approval_status.short_description = 'Status'
    
    def logo_preview(self, obj):
        if obj.app_logo:
            return format_html('<img src="{}" width="40" height="40" style="border-radius: 5px;" />', obj.app_logo.url)
        return '-'
    logo_preview.short_description = 'Logo'
    
    def logo_preview_large(self, obj):
        if obj.app_logo:
            return format_html('<img src="{}" width="200" style="border-radius: 10px;" />', obj.app_logo.url)
        return 'No logo uploaded'
    logo_preview_large.short_description = 'App Logo Preview'
    
    def approve_projects(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} project(s) approved")
    approve_projects.short_description = "Approve selected projects"
    
    def reject_projects(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} project(s) rejected")
    reject_projects.short_description = "Reject selected projects"


@admin.register(CodeQuestConsultant)
class CodeQuestConsultantAdmin(CodeQuestConsultantMediaAdminMixin, admin.ModelAdmin):
    list_display = (
        'student_name',
        'student_id',
        'year',
        'email',
        'linked_user_display',
        'approval_badge',
        'assigned_groups_count',
        'access_key_display',
        'registration_date'
    )
    list_filter = ('event', 'is_approved', 'year')
    search_fields = ('student_name', 'student_id', 'email', 'access_key')
    readonly_fields = ('student_name', 'student_id', 'email', 'phone_number', 'year', 
                      'expertise_areas', 'bio', 'profile_image', 'profile_image_url',
                      'access_key', 'registration_date', 'user')
    
    # 🚫 Admins CANNOT create consultants - students register themselves as consultants
    def has_add_permission(self, request):
        return False
    
    fieldsets = (
        ('Linked User Account', {
            'fields': ('user',),
            'description': 'The CSS user account linked to this registration'
        }),
        ('Student Information', {
            'fields': ('student_name', 'student_id', 'email', 'phone_number', ('profile_image', 'profile_image_url')),
            'description': 'Upload image OR provide Google Drive/Dropbox link'
        }),
        ('Academic & Expertise Details', {
            'fields': ('year', 'expertise_areas', 'bio')
        }),
        ('Event & Approval', {
            'fields': ('event', 'is_approved')
        }),
        ('Access Information', {
            'fields': ('access_key', 'registration_date'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ConsultantGroupAssignmentInline]
    
    actions = ['approve_consultants', 'reject_consultants']
    
    def linked_user_display(self, obj):
        if obj.user:
            return format_html('<span style="color: green;">✓ {}</span>', f"{obj.user.first_name} {obj.user.last_name}")
        return format_html('<span style="color: gray;">—</span>')
    linked_user_display.short_description = 'Linked User'
    
    def approval_badge(self, obj):
        if obj.is_approved:
            return format_html('<span style="color: green;">✓ APPROVED</span>')
        return format_html('<span style="color: red;">✗ PENDING</span>')
    approval_badge.short_description = 'Approval'
    
    def assigned_groups_count(self, obj):
        count = obj.assigned_groups.filter(is_active=True).count()
        return format_html('<strong>{}</strong> group(s)', count)
    assigned_groups_count.short_description = 'Groups'
    
    def access_key_display(self, obj):
        return format_html('<code>{}</code>', obj.access_key)
    access_key_display.short_description = 'Access Key'
    
    def approve_consultants(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} consultant(s) approved")
    approve_consultants.short_description = "Approve selected consultants"
    
    def reject_consultants(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} consultant(s) rejected")
    reject_consultants.short_description = "Reject selected consultants"


@admin.register(ConsultantGroupAssignment)
class ConsultantGroupAssignmentAdmin(admin.ModelAdmin):
    list_display = ('consultant', 'group', 'assigned_by', 'assigned_date', 'active_badge')
    list_filter = ('is_active', 'group__event')
    search_fields = ('consultant__student_name', 'consultant__student_id', 'group__group_number')
    readonly_fields = ('assigned_date',)
    
    def active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ ACTIVE</span>')
        return format_html('<span style="color: gray;">INACTIVE</span>')
    active_badge.short_description = 'Status'


@admin.register(ScoringCriteria)
class ScoringCriteriaAdmin(admin.ModelAdmin):
    list_display = (
        'criteria_name',
        'event',
        'max_points',
        'weight_display',
        'order'
    )
    list_filter = ('event',)
    search_fields = ('criteria_name', 'description')
    list_editable = ('max_points', 'order')
    
    def weight_display(self, obj):
        return f"{obj.percentage_weight}%"
    weight_display.short_description = 'Weight'


@admin.register(CodeQuestFacilitator)
class CodeQuestFacilitatorAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'email',
        'role_title',
        'scored_projects_count',
        'access_code_display'
    )
    list_filter = ('event',)
    search_fields = ('name', 'email', 'role_title', 'access_code')
    readonly_fields = ('access_code',)
    
    def scored_projects_count(self, obj):
        count = ProjectScore.objects.filter(facilitator=obj).values('project').distinct().count()
        return format_html('<strong>{}</strong> project(s)', count)
    scored_projects_count.short_description = 'Scored'
    
    def access_code_display(self, obj):
        return format_html('<code>{}</code>', obj.access_code)
    access_code_display.short_description = 'Access Code'


@admin.register(ProjectScore)
class ProjectScoreAdmin(admin.ModelAdmin):
    list_display = (
        'project',
        'facilitator',
        'criteria',
        'score_display',
        'scored_date'
    )
    list_filter = ('facilitator', 'criteria', 'project__group__event')
    search_fields = ('project__app_name', 'facilitator__name')
    readonly_fields = ('project', 'facilitator', 'criteria', 'score', 'comments', 'scored_date')
    
    # 🚫 Admins CANNOT create scores - Facilitators score projects during judging
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    # ✅ Admins CAN delete scores if needed (e.g., mistakes)
    def has_delete_permission(self, request, obj=None):
        return True
    
    def score_display(self, obj):
        percentage = (obj.score / obj.criteria.max_points) * 100
        color = '#4CAF50' if percentage >= 70 else '#FF9800' if percentage >= 50 else '#f44336'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} / {}</span>',
            color,
            obj.score,
            obj.criteria.max_points
        )
    score_display.short_description = 'Score'


@admin.register(FinalProjectScore)
class FinalProjectScoreAdmin(admin.ModelAdmin):
    list_display = (
        'rank_display',
        'project',
        'group',
        'total_score_display',
        'published_badge',
        'calculation_date'
    )
    list_filter = ('is_published', 'project__group__event')
    search_fields = ('project__app_name', 'project__group__group_number')
    readonly_fields = ('total_score', 'rank', 'calculation_date')
    
    # No inline - ProjectScore has FK to project, not final_score
    
    actions = ['publish_results', 'unpublish_results', 'recalculate_scores']
    
    def rank_display(self, obj):
        if obj.rank == 1:
            return format_html('<span style="color: gold; font-size: 18px; font-weight: bold;">🥇 #{}</span>', obj.rank)
        elif obj.rank == 2:
            return format_html('<span style="color: silver; font-size: 16px; font-weight: bold;">🥈 #{}</span>', obj.rank)
        elif obj.rank == 3:
            return format_html('<span style="color: #CD7F32; font-size: 16px; font-weight: bold;">🥉 #{}</span>', obj.rank)
        return format_html('<strong>#{}</strong>', obj.rank)
    rank_display.short_description = 'Rank'
    
    def group(self, obj):
        return f"Group {obj.project.group.group_number}"
    group.short_description = 'Group'
    
    def total_score_display(self, obj):
        return format_html('<span style="font-size: 16px; font-weight: bold; color: #2196F3;">{:.2f}</span>', obj.total_score)
    total_score_display.short_description = 'Total Score'
    
    def published_badge(self, obj):
        if obj.is_published:
            return format_html('<span style="color: green;">✓ PUBLISHED</span>')
        return format_html('<span style="color: gray;">DRAFT</span>')
    published_badge.short_description = 'Status'
    
    def publish_results(self, request, queryset):
        count = queryset.update(is_published=True, published_date=timezone.now())
        self.message_user(request, f"{count} result(s) published")
    publish_results.short_description = "Publish selected results"
    
    def unpublish_results(self, request, queryset):
        count = queryset.update(is_published=False, published_date=None)
        self.message_user(request, f"{count} result(s) unpublished")
    unpublish_results.short_description = "Unpublish selected results"
    
    def recalculate_scores(self, request, queryset):
        for final_score in queryset:
            event = final_score.project.group.event
            codequest_utils.calculate_project_scores(event)
            codequest_utils.rank_all_projects(event)
        self.message_user(request, f"Recalculated scores for {queryset.count()} project(s)")
    recalculate_scores.short_description = "Recalculate scores and ranks"


@admin.register(ProjectTask)
class ProjectTaskAdmin(admin.ModelAdmin):
    list_display = (
        'task_title',
        'project',
        'assigned_to',
        'priority_badge',
        'status_badge',
        'due_date',
        'overdue_badge'
    )
    list_filter = ('status', 'priority', 'project__group__event')
    search_fields = ('task_title', 'task_description', 'assigned_to__student_name')
    readonly_fields = ('project', 'task_title', 'task_description', 'assigned_to', 'assigned_by', 
                      'priority', 'status', 'due_date', 'created_date', 'completed_date')
    
    # 🚫 Admins CANNOT create tasks - Project Manager manages project tasks
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    # ✅ Admins CAN delete tasks if needed
    def has_delete_permission(self, request, obj=None):
        return True
    
    def priority_badge(self, obj):
        colors = {
            'LOW': '#4CAF50',
            'MEDIUM': '#FF9800',
            'HIGH': '#f44336',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.priority, '#000'),
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def status_badge(self, obj):
        colors = {
            'TODO': '#9E9E9E',
            'IN_PROGRESS': '#2196F3',
            'COMPLETED': '#4CAF50',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def overdue_badge(self, obj):
        if obj.status != 'COMPLETED' and obj.due_date and obj.due_date < timezone.now().date():
            return format_html('<span style="color: red; font-weight: bold;">⚠ OVERDUE</span>')
        return '-'
    overdue_badge.short_description = 'Overdue'


# ===============================
# Self-Grouping Admin Classes
# ===============================

class SelfGroupingMembershipInline(admin.TabularInline):
    model = SelfGroupingMembership
    extra = 0
    fields = ('participant', 'is_creator', 'status', 'joined_at')
    readonly_fields = ('participant', 'is_creator', 'status', 'joined_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class GroupInvitationInline(admin.TabularInline):
    model = GroupInvitation
    extra = 0
    fields = ('sender', 'recipient', 'status', 'created_at', 'responded_at')
    readonly_fields = ('sender', 'recipient', 'status', 'created_at', 'responded_at')
    can_delete = False
    fk_name = 'team'
    
    def has_add_permission(self, request, obj=None):
        return False


class JoinRequestInline(admin.TabularInline):
    model = JoinRequest
    extra = 0
    fields = ('requester', 'status', 'responded_by', 'created_at', 'responded_at')
    readonly_fields = ('requester', 'status', 'responded_by', 'created_at', 'responded_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(SelfGroupingTeam)
class SelfGroupingTeamAdmin(admin.ModelAdmin):
    list_display = (
        'team_display',
        'event',
        'creator_display',
        'member_count_display',
        'status_badge',
        'finalized_group_link',
        'created_at'
    )
    list_filter = ('status', 'event')
    search_fields = ('team_name', 'creator__student_name', 'creator__student_id')
    readonly_fields = ('creator', 'created_at', 'updated_at', 'finalized_at', 'finalized_group')
    
    fieldsets = (
        ('Team Information', {
            'fields': ('event', 'team_name', 'status')
        }),
        ('Creator Details', {
            'fields': ('creator',),
            'description': 'The participant who created this team'
        }),
        ('Finalization', {
            'fields': ('finalized_group', 'finalized_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [SelfGroupingMembershipInline, GroupInvitationInline, JoinRequestInline]
    
    actions = ['finalize_teams', 'disband_teams']
    
    # 🚫 Admins CANNOT create teams - participants create their own teams
    def has_add_permission(self, request):
        return False
    
    def team_display(self, obj):
        return obj.team_name or f"Team by {obj.creator.student_name}"
    team_display.short_description = 'Team Name'
    
    def creator_display(self, obj):
        return format_html(
            '<div style="line-height: 1.4;">'
            '<strong>{}</strong><br>'
            '<span style="color: #666; font-size: 11px;">{}</span><br>'
            '<span style="color: #888; font-size: 11px;">{}</span>'
            '</div>',
            obj.creator.student_name,
            obj.creator.student_id,
            obj.creator.email
        )
    creator_display.short_description = 'Creator'
    
    def member_count_display(self, obj):
        count = obj.member_count()
        min_size = obj.event.min_group_size or 5
        max_size = obj.event.max_group_size or 10
        
        if count >= min_size:
            color = '#4CAF50'  # Green - ready
        elif count >= min_size - 2:
            color = '#FF9800'  # Orange - almost ready
        else:
            color = '#f44336'  # Red - needs more members
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span> / {} (min: {})',
            color, count, max_size, min_size
        )
    member_count_display.short_description = 'Members'
    
    def status_badge(self, obj):
        colors = {
            'forming': '#2196F3',      # Blue
            'ready': '#FF9800',         # Orange
            'finalized': '#4CAF50',     # Green
            'disbanded': '#9E9E9E',     # Gray
        }
        icons = {
            'forming': '🔨',
            'ready': '✅',
            'finalized': '🎉',
            'disbanded': '❌',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{} {}</span>',
            colors.get(obj.status, '#000'),
            icons.get(obj.status, ''),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def finalized_group_link(self, obj):
        if obj.finalized_group:
            url = reverse('admin:codequest_codequestgroup_change', args=[obj.finalized_group.pk])
            return format_html(
                '<a href="{}" style="color: #4CAF50; font-weight: bold;">Group {}</a>',
                url, obj.finalized_group.group_number
            )
        return format_html('<span style="color: #999;">Not finalized</span>')
    finalized_group_link.short_description = 'Official Group'
    
    def finalize_teams(self, request, queryset):
        # Only finalize teams that are ready
        finalized = 0
        for team in queryset.filter(status__in=['forming', 'ready']):
            if team.is_ready_to_finalize():
                # Mark as finalized (actual group creation handled elsewhere)
                team.status = 'finalized'
                team.finalized_at = timezone.now()
                team.save()
                finalized += 1
        self.message_user(request, f"{finalized} team(s) marked for finalization")
    finalize_teams.short_description = "Finalize selected teams"
    
    def disband_teams(self, request, queryset):
        count = queryset.exclude(status='finalized').update(status='disbanded')
        self.message_user(request, f"{count} team(s) disbanded")
    disband_teams.short_description = "Disband selected teams"


@admin.register(SelfGroupingMembership)
class SelfGroupingMembershipAdmin(admin.ModelAdmin):
    list_display = (
        'participant_display',
        'team_display',
        'creator_badge',
        'status_badge',
        'joined_at'
    )
    list_filter = ('status', 'is_creator', 'team__event')
    search_fields = ('participant__student_name', 'participant__student_id', 'team__team_name')
    readonly_fields = ('team', 'participant', 'is_creator', 'status', 'joined_at')
    
    # 🚫 Admins CANNOT create memberships - handled through self-grouping flow
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def participant_display(self, obj):
        return format_html(
            '<strong>{}</strong><br><span style="color: #666; font-size: 11px;">{}</span>',
            obj.participant.student_name,
            obj.participant.student_id
        )
    participant_display.short_description = 'Participant'
    
    def team_display(self, obj):
        team_name = obj.team.team_name or f"Team by {obj.team.creator.student_name}"
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:codequest_selfgroupingteam_change', args=[obj.team.pk]),
            team_name
        )
    team_display.short_description = 'Team'
    
    def creator_badge(self, obj):
        if obj.is_creator:
            return format_html('<span style="background-color: #FFD700; color: #000; padding: 2px 6px; border-radius: 3px; font-weight: bold;">👑 CREATOR</span>')
        return format_html('<span style="color: #666;">Member</span>')
    creator_badge.short_description = 'Role'
    
    def status_badge(self, obj):
        if obj.status == 'accepted':
            return format_html('<span style="color: #4CAF50;">✓ Active</span>')
        return format_html('<span style="color: #9E9E9E;">Left</span>')
    status_badge.short_description = 'Status'


@admin.register(GroupInvitation)
class GroupInvitationAdmin(admin.ModelAdmin):
    list_display = (
        'invitation_display',
        'team_display',
        'sender_display',
        'recipient_display',
        'status_badge',
        'created_at',
        'responded_at'
    )
    list_filter = ('status', 'team__event')
    search_fields = (
        'sender__student_name', 'sender__student_id',
        'recipient__student_name', 'recipient__student_id',
        'team__team_name'
    )
    readonly_fields = ('team', 'sender', 'recipient', 'message', 'status', 'created_at', 'responded_at')
    
    # 🚫 Admins CANNOT create invitations - participants invite each other
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def invitation_display(self, obj):
        return format_html(
            '{} → {}',
            obj.sender.student_name.split()[0] if obj.sender.student_name else 'Unknown',
            obj.recipient.student_name.split()[0] if obj.recipient.student_name else 'Unknown'
        )
    invitation_display.short_description = 'Invitation'
    
    def team_display(self, obj):
        team_name = obj.team.team_name or f"Team by {obj.team.creator.student_name}"
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:codequest_selfgroupingteam_change', args=[obj.team.pk]),
            team_name
        )
    team_display.short_description = 'Team'
    
    def sender_display(self, obj):
        return format_html(
            '<strong>{}</strong><br><span style="color: #666; font-size: 11px;">{}</span>',
            obj.sender.student_name,
            obj.sender.student_id
        )
    sender_display.short_description = 'Sender'
    
    def recipient_display(self, obj):
        return format_html(
            '<strong>{}</strong><br><span style="color: #666; font-size: 11px;">{}</span>',
            obj.recipient.student_name,
            obj.recipient.student_id
        )
    recipient_display.short_description = 'Recipient'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FF9800',
            'accepted': '#4CAF50',
            'declined': '#f44336',
            'cancelled': '#9E9E9E',
            'expired': '#795548',
        }
        icons = {
            'pending': '⏳',
            'accepted': '✓',
            'declined': '✗',
            'cancelled': '🚫',
            'expired': '⌛',
        }
        return format_html(
            '<span style="color: {};">{} {}</span>',
            colors.get(obj.status, '#000'),
            icons.get(obj.status, ''),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(JoinRequest)
class JoinRequestAdmin(admin.ModelAdmin):
    list_display = (
        'request_display',
        'team_display',
        'requester_display',
        'status_badge',
        'responded_by_display',
        'created_at',
        'responded_at'
    )
    list_filter = ('status', 'team__event')
    search_fields = (
        'requester__student_name', 'requester__student_id',
        'team__team_name', 'team__creator__student_name'
    )
    readonly_fields = ('team', 'requester', 'message', 'status', 'responded_by', 'created_at', 'responded_at')
    
    # 🚫 Admins CANNOT create join requests - participants request to join teams
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def request_display(self, obj):
        team_name = obj.team.team_name or f"Team by {obj.team.creator.student_name}"
        return format_html(
            '{} → {}',
            obj.requester.student_name.split()[0] if obj.requester.student_name else 'Unknown',
            team_name[:20] + '...' if len(team_name) > 20 else team_name
        )
    request_display.short_description = 'Request'
    
    def team_display(self, obj):
        team_name = obj.team.team_name or f"Team by {obj.team.creator.student_name}"
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:codequest_selfgroupingteam_change', args=[obj.team.pk]),
            team_name
        )
    team_display.short_description = 'Team'
    
    def requester_display(self, obj):
        return format_html(
            '<strong>{}</strong><br><span style="color: #666; font-size: 11px;">{}</span>',
            obj.requester.student_name,
            obj.requester.student_id
        )
    requester_display.short_description = 'Requester'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FF9800',
            'accepted': '#4CAF50',
            'declined': '#f44336',
            'cancelled': '#9E9E9E',
        }
        icons = {
            'pending': '⏳',
            'accepted': '✓',
            'declined': '✗',
            'cancelled': '🚫',
        }
        return format_html(
            '<span style="color: {};">{} {}</span>',
            colors.get(obj.status, '#000'),
            icons.get(obj.status, ''),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def responded_by_display(self, obj):
        if obj.responded_by:
            return format_html(
                '<span style="color: #666;">{}</span>',
                obj.responded_by.student_name
            )
        return format_html('<span style="color: #999;">-</span>')
    responded_by_display.short_description = 'Responded By'

