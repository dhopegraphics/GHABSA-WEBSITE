from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html
from django.http import JsonResponse
from core.models import NotifyUser, ContactUs, EmailBatch, EmailBatchRecipient

# Register your models here.


class NotifyUserAdmin(admin.ModelAdmin):
    list_display = [
        "recipient",
        "channel",
        "delivery_status",
        "action",
        "is_priority",
        "retry_count",
        "created_at",
        "last_updated",
    ]
    list_filter = ["channel", "action", "sent", "sms_sent", "push_sent", "email_sent", "is_priority", "created_at"]
    search_fields = ["recipient__username", "recipient__phone", "message"]
    readonly_fields = [
        "sent",
        "sms_sent",
        "push_sent",
        "email_sent",
        "sms_campaign_id",
        "sms_error",
        "push_error",
        "email_error",
        "retry_count",
        "created_at",
        "last_updated",
    ]
    
    fieldsets = (
        ("Recipient", {
            "fields": ("recipient", "channel")
        }),
        ("Message", {
            "fields": ("title", "message", "push_data")
        }),
        ("Sending", {
            "fields": ("action", "is_priority")
        }),
        ("Status", {
            "fields": (
                "sent",
                "sms_sent",
                "push_sent",
                "email_sent",
                "sms_campaign_id",
                "retry_count",
            ),
            "classes": ("collapse",)
        }),
        ("Errors", {
            "fields": ("sms_error", "push_error", "email_error"),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "last_updated"),
            "classes": ("collapse",)
        }),
    )
    
    def get_urls(self):
        """Add custom URL for bulk notification"""
        urls = super().get_urls()
        custom_urls = [
            path('bulk-notify/', self.admin_site.admin_view(self.bulk_notify_view), name='core_notifyuser_bulk_notify'),
        ]
        return custom_urls + urls
    
    def bulk_notify_view(self, request):
        """Redirect to bulk notification view"""
        from core.views import bulk_notify_view
        return bulk_notify_view(request)
    
    def changelist_view(self, request, extra_context=None):
        """Add bulk notify button to changelist"""
        extra_context = extra_context or {}
        extra_context['show_bulk_notify_button'] = True
        return super().changelist_view(request, extra_context=extra_context)
    
    def delivery_status(self, obj):
        """Show delivery status with icons"""
        if obj.action == "draft":
            return "📝 Draft"
        
        priority_flag = "⚡" if obj.is_priority else ""
        statuses = []
        
        # SMS status
        if obj.channel in ["sms", "both", "sms_email", "all"]:
            if obj.sms_sent:
                statuses.append(f"✅ SMS {priority_flag} (ID: {obj.sms_campaign_id or 'N/A'})")
            else:
                error = obj.sms_error[:50] if obj.sms_error else "Pending"
                statuses.append(f"❌ SMS {priority_flag} ({error})")
        
        # Push status
        if obj.channel in ["push", "both", "push_email", "all"]:
            if obj.push_sent:
                statuses.append("✅ Push")
            else:
                error = obj.push_error[:30] if obj.push_error else "Pending"
                statuses.append(f"❌ Push ({error})")
        
        # Email status
        if obj.channel in ["email", "sms_email", "push_email", "all"]:
            if obj.email_sent:
                statuses.append("✅ Email")
            else:
                error = obj.email_error[:30] if obj.email_error else "Pending"
                statuses.append(f"❌ Email ({error})")
        
        return " | ".join(statuses) if statuses else "⏳ Pending"
    
    delivery_status.short_description = "Delivery Status"


class ContactUsAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "phone",
        "message_preview",
        "created_at",
    ]
    list_filter = ["created_at"]
    search_fields = ["name", "phone", "message"]
    readonly_fields = ["name", "phone", "message", "created_at"]
    ordering = ["-created_at"]
    actions = ["delete_selected"]
    
    def message_preview(self, obj):
        """Show first 50 characters of message"""
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = "Message"
    
    def has_add_permission(self, request):
        """Disable adding new contact messages from admin"""
        return False


admin.site.register(ContactUs, ContactUsAdmin)
admin.site.register(NotifyUser, NotifyUserAdmin)


# =====================
# BATCH EMAIL ADMIN
# =====================

class EmailBatchRecipientInline(admin.TabularInline):
    model = EmailBatchRecipient
    extra = 0
    max_num = 50  # Limit display to first 50 recipients
    per_page = 50  # Paginate for performance
    readonly_fields = ["user", "email", "status", "sent_at", "error_message", "retry_count"]
    can_delete = False
    show_change_link = True
    ordering = ["-sent_at", "status"]
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        # Don't slice here - let max_num handle the limit
        # The slice was causing "Cannot filter a query once a slice has been taken"
        qs = super().get_queryset(request)
        return qs.select_related("user")


@admin.register(EmailBatch)
class EmailBatchAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "subject",
        "status_display",
        "progress_display",
        "sent_count",
        "failed_count",
        "created_at",
        "batch_actions",
    ]
    list_filter = ["status", "channel", "created_at"]
    search_fields = ["title", "subject", "message"]
    readonly_fields = [
        "status",
        "total_recipients",
        "sent_count",
        "failed_count",
        "skipped_count",
        "created_at",
        "started_at",
        "completed_at",
        "last_processed_at",
        "last_error",
        "progress_display_detail",
    ]
    
    fieldsets = (
        ("Batch Info", {
            "fields": ("title", "subject", "message", "channel", "filter_description")
        }),
        ("Status", {
            "fields": (
                "status",
                "progress_display_detail",
                "total_recipients",
                "sent_count",
                "failed_count",
                "skipped_count",
            )
        }),
        ("Timing", {
            "fields": ("created_at", "started_at", "completed_at", "last_processed_at"),
            "classes": ("collapse",)
        }),
        ("Errors", {
            "fields": ("last_error",),
            "classes": ("collapse",)
        }),
    )
    
    inlines = [EmailBatchRecipientInline]
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:batch_id>/resume/', self.admin_site.admin_view(self.resume_batch), name='core_emailbatch_resume'),
            path('<int:batch_id>/pause/', self.admin_site.admin_view(self.pause_batch), name='core_emailbatch_pause'),
            path('<int:batch_id>/cancel/', self.admin_site.admin_view(self.cancel_batch), name='core_emailbatch_cancel'),
            path('<int:batch_id>/status/', self.admin_site.admin_view(self.batch_status_api), name='core_emailbatch_status'),
            path('create-batch/', self.admin_site.admin_view(self.create_batch_view), name='core_emailbatch_create'),
        ]
        return custom_urls + urls
    
    def status_display(self, obj):
        status_colors = {
            "pending": "#6b7280",
            "in_progress": "#2563eb",
            "paused": "#f59e0b",
            "completed": "#10b981",
            "cancelled": "#6b7280",
            "failed": "#ef4444",
        }
        status_icons = {
            "pending": "⏳",
            "in_progress": "🔄",
            "paused": "⏸️",
            "completed": "✅",
            "cancelled": "🚫",
            "failed": "❌",
        }
        color = status_colors.get(obj.status, "#6b7280")
        icon = status_icons.get(obj.status, "")
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_display.short_description = "Status"
    status_display.admin_order_field = "status"
    
    def progress_display(self, obj):
        progress = obj.progress_percentage
        if progress >= 100:
            color = "#10b981"
        elif progress >= 50:
            color = "#2563eb"
        else:
            color = "#f59e0b"
        
        return format_html(
            '<div style="width: 100px; background: #e5e7eb; border-radius: 4px;">'
            '<div style="width: {}%; background: {}; height: 20px; border-radius: 4px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{}%</div></div>',
            progress, color, progress
        )
    progress_display.short_description = "Progress"
    
    def progress_display_detail(self, obj):
        return f"{obj.sent_count} sent, {obj.failed_count} failed, {obj.skipped_count} skipped, {obj.pending_count} pending of {obj.total_recipients} total ({obj.progress_percentage}%)"
    progress_display_detail.short_description = "Progress Details"
    
    def batch_actions(self, obj):
        buttons = []
        
        if obj.can_resume:
            buttons.append(
                f'<a class="button" href="{obj.id}/resume/" style="background: #10b981; color: white; padding: 4px 8px; margin: 2px; border-radius: 4px; text-decoration: none;">▶️ Resume</a>'
            )
        
        if obj.can_pause:
            buttons.append(
                f'<a class="button" href="{obj.id}/pause/" style="background: #f59e0b; color: white; padding: 4px 8px; margin: 2px; border-radius: 4px; text-decoration: none;">⏸️ Pause</a>'
            )
        
        if obj.status not in ["completed", "cancelled"]:
            buttons.append(
                f'<a class="button" href="{obj.id}/cancel/" style="background: #ef4444; color: white; padding: 4px 8px; margin: 2px; border-radius: 4px; text-decoration: none;" onclick="return confirm(\'Cancel this batch?\');">🚫 Cancel</a>'
            )
        
        return format_html(" ".join(buttons)) if buttons else "-"
    batch_actions.short_description = "Actions"
    
    def resume_batch(self, request, batch_id):
        from utils.utils import resume_email_batch
        from django.contrib import messages
        
        result = resume_email_batch(batch_id)
        if result.get("success"):
            messages.success(request, f"✅ Batch {batch_id} is resuming in the background")
        else:
            messages.error(request, f"❌ {result.get('message')}")
        
        return redirect(f"/executive-dashboard-cb/core/emailbatch/{batch_id}/change/")
    
    def pause_batch(self, request, batch_id):
        from utils.utils import pause_email_batch
        from django.contrib import messages
        
        result = pause_email_batch(batch_id)
        if result.get("success"):
            messages.success(request, f"⏸️ Batch {batch_id} paused")
        else:
            messages.error(request, f"❌ {result.get('message')}")
        
        return redirect(f"/executive-dashboard-cb/core/emailbatch/{batch_id}/change/")
    
    def cancel_batch(self, request, batch_id):
        from utils.utils import cancel_email_batch
        from django.contrib import messages
        
        result = cancel_email_batch(batch_id)
        if result.get("success"):
            messages.success(request, f"🚫 Batch {batch_id} cancelled")
        else:
            messages.error(request, f"❌ {result.get('message')}")
        
        return redirect(f"/executive-dashboard-cb/core/emailbatch/{batch_id}/change/")
    
    def batch_status_api(self, request, batch_id):
        from utils.utils import get_batch_status
        return JsonResponse(get_batch_status(batch_id))
    
    def create_batch_view(self, request):
        from core.views import create_email_batch_view
        return create_email_batch_view(request)
    
    def changelist_view(self, request, extra_context=None):
        """Custom changelist with dashboard-style display"""
        from utils.utils import get_email_rate_status
        from django.db.models import Count
        
        extra_context = extra_context or {}
        
        # Get all batches ordered by creation date
        batches = EmailBatch.objects.all().order_by('-created_at')[:20]
        extra_context['batches'] = batches
        
        # Get rate status
        extra_context['rate_status'] = get_email_rate_status()
        
        # Get stats by status
        status_counts = EmailBatch.objects.values('status').annotate(count=Count('id'))
        stats = {
            'pending': 0,
            'in_progress': 0,
            'completed': 0,
            'failed_paused': 0,
        }
        for item in status_counts:
            if item['status'] == 'pending':
                stats['pending'] = item['count']
            elif item['status'] == 'in_progress':
                stats['in_progress'] = item['count']
            elif item['status'] == 'completed':
                stats['completed'] = item['count']
            elif item['status'] in ['failed', 'paused']:
                stats['failed_paused'] += item['count']
        
        extra_context['stats'] = stats
        extra_context['has_in_progress'] = stats['in_progress'] > 0
        
        # Use custom template
        self.change_list_template = 'admin/core/emailbatch/change_list.html'
        
        return super().changelist_view(request, extra_context=extra_context)
    
    def has_add_permission(self, request):
        # Use the custom create form instead
        return False


@admin.register(EmailBatchRecipient)
class EmailBatchRecipientAdmin(admin.ModelAdmin):
    list_display = ["batch", "user", "email", "status", "sent_at", "retry_count"]
    list_filter = ["status", "batch"]
    search_fields = ["email", "user__username", "batch__title"]
    readonly_fields = ["batch", "user", "email", "status", "sent_at", "error_message", "retry_count"]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
