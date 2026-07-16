from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from django.utils.html import format_html
from executives.models import Executive
from .models import Project, ProjectMember
from utils.media_mixins import make_media_admin_mixin

# Create the media admin mixin for Project's file fields
ProjectMediaAdminMixin = make_media_admin_mixin(['image', 'image2', 'image3'])


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 1
    fields = ['name', 'year', 'program', 'role', 'student_id', 'email', 'phone', 'user', 'is_submitter', 'order']
    readonly_fields = ['user', 'is_submitter']
    ordering = ['order', 'name']
    autocomplete_fields = ['user']


@admin.register(Project)
class ProjectAdmin(ProjectMediaAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'category', 'academic_year', 'get_member_count', 'submitted_by_display', 'is_approved', 'update_status_badge', 'is_featured', 'is_active', 'created_at']
    list_filter = ['category', 'academic_year', 'is_approved', 'update_status', 'is_featured', 'is_active']
    search_fields = ['title', 'description', 'technologies', 'submitted_by__first_name', 'submitted_by__last_name', 'submitted_by__phone']
    list_editable = ['is_featured', 'is_active']
    readonly_fields = ['submitted_by', 'approved_by', 'approved_at', 'update_requested_at', 'update_approved_at']
    inlines = [ProjectMemberInline]
    actions = ['approve_projects', 'approve_update_requests', 'reject_update_requests']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'short_description', 'description')
        }),
        ('Project Details', {
            'fields': ('academic_year', 'category', 'technologies')
        }),
        ('Links', {
            'fields': ('github_url', 'demo_url')
        }),
        ('Images', {
            'fields': (
                ('image', 'image_url'),
                ('image2', 'image2_url'),
                ('image3', 'image3_url')
            ),
            'description': 'Upload images OR provide Google Drive/Dropbox links'
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'is_active', 'order'),
            'classes': ('collapse',)
        }),
        ('Submission & Approval', {
            'fields': ('submitted_by', 'is_approved', 'approved_by', 'approved_at'),
            'description': 'Tracks who submitted the project and approval status.'
        }),
        ('Update Requests', {
            'fields': ('update_status', 'update_request_reason', 'update_requested_at', 'update_approved_by', 'update_approved_at'),
            'description': 'Manage update requests from project owners.',
            'classes': ('collapse',)
        }),
    )
    
    def get_member_count(self, obj):
        return obj.members.count()
    get_member_count.short_description = 'Team Size'
    
    def submitted_by_display(self, obj):
        if obj.submitted_by:
            return f"{obj.submitted_by.first_name} {obj.submitted_by.last_name}"
        return "-"
    submitted_by_display.short_description = 'Submitted By'
    
    def update_status_badge(self, obj):
        """Display update status with colored badge"""
        colors = {
            'none': '#6c757d',
            'pending': '#ffc107',
            'approved': '#17a2b8',
            'in_progress': '#fd7e14',
        }
        labels = {
            'none': 'No Request',
            'pending': '⏳ Pending',
            'approved': '✅ Approved',
            'in_progress': '🔄 In Progress',
        }
        color = colors.get(obj.update_status, '#6c757d')
        label = labels.get(obj.update_status, obj.update_status)
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            color, label
        )
    update_status_badge.short_description = 'Update Status'
    
    def approve_projects(self, request, queryset):
        """Bulk approve selected projects"""
        try:
            executive = Executive.objects.get(user=request.user, is_active=True)
            count = 0
            for project in queryset.filter(is_approved=False):
                project.is_approved = True
                project.approved_by = executive
                project.approved_at = timezone.now()
                project.save()
                count += 1
            messages.success(request, f'{count} project(s) approved successfully.')
        except Executive.DoesNotExist:
            messages.error(request, 'Only active executives can approve projects.')
    approve_projects.short_description = 'Approve selected projects'
    
    def approve_update_requests(self, request, queryset):
        """Bulk approve update requests - sets project to temporarily unapproved"""
        try:
            executive = Executive.objects.get(user=request.user, is_active=True)
            count = 0
            for project in queryset.filter(update_status='pending'):
                project.update_status = 'in_progress'
                project.update_approved_by = executive
                project.update_approved_at = timezone.now()
                project.is_approved = False  # Temporarily unapprove
                project.approved_by = None
                project.approved_at = None
                project.save()
                count += 1
            messages.success(request, f'{count} update request(s) approved. Projects are now editable and temporarily hidden from public.')
        except Executive.DoesNotExist:
            messages.error(request, 'Only active executives can approve update requests.')
    approve_update_requests.short_description = 'Approve update requests (allow editing)'
    
    def reject_update_requests(self, request, queryset):
        """Reject update requests"""
        count = 0
        for project in queryset.filter(update_status='pending'):
            project.update_status = 'none'
            project.update_request_reason = ''
            project.update_requested_at = None
            project.save()
            count += 1
        messages.success(request, f'{count} update request(s) rejected.')
    reject_update_requests.short_description = 'Reject update requests'
    
    def save_model(self, request, obj, form, change):
        # Auto-generate short description if not provided
        if not obj.short_description and obj.description:
            obj.short_description = obj.description[:197] + '...' if len(obj.description) > 200 else obj.description
        
        # Handle approval logic
        if 'is_approved' in form.changed_data and obj.is_approved:
            # Check if user is an active executive
            try:
                executive = Executive.objects.get(user=request.user, is_active=True)
                obj.approved_by = executive
                obj.approved_at = timezone.now()
                messages.success(request, f'Project approved by {executive}')
            except Executive.DoesNotExist:
                # If not an executive, don't allow approval
                obj.is_approved = False
                obj.approved_by = None
                obj.approved_at = None
                messages.error(request, 'Only active executives can approve projects.')
        
        # If unmarking approval, clear approval data
        if 'is_approved' in form.changed_data and not obj.is_approved:
            obj.approved_by = None
            obj.approved_at = None
            
        super().save_model(request, obj, form, change)


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'year', 'program', 'role', 'user_linked', 'is_submitter', 'order']
    list_filter = ['year', 'program', 'project', 'is_submitter']
    search_fields = ['name', 'student_id', 'email', 'phone', 'project__title', 'user__first_name', 'user__last_name']
    ordering = ['project', 'order', 'name']
    readonly_fields = ['user', 'is_submitter']
    
    def user_linked(self, obj):
        if obj.user:
            return f"✅ {obj.user.first_name}"
        return "❌"
    user_linked.short_description = 'Linked'
