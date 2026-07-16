from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    HelpDeskCategory, HelpDeskRequest, CodeSnippet, RequestImage,
    HelpDeskResponse, ResponseCodeSnippet, ResponseLink, ResponseVote,
    ResponseReply, RequestBookmark, RequestView, HelpDeskNotification, 
    ContentReport, UserReputation
)


@admin.register(HelpDeskCategory)
class HelpDeskCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'emoji', 'display_order', 'is_active', 'get_active_count', 'get_total_count']
    list_editable = ['display_order', 'is_active']
    ordering = ['display_order', 'name']
    
    def get_active_count(self, obj):
        count = obj.requests.filter(status='active', is_deleted=False).count()
        if count > 10:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', count)
        elif count > 5:
            return format_html('<span style="color: orange; font-weight: bold;">{}</span>', count)
        return count
    get_active_count.short_description = '🔴 Active Requests'
    
    def get_total_count(self, obj):
        return obj.requests.filter(is_deleted=False).count()
    get_total_count.short_description = '📊 Total Requests'


class CodeSnippetInline(admin.TabularInline):
    model = CodeSnippet
    extra = 0
    readonly_fields = ['language', 'code', 'description', 'created_at']
    can_delete = True
    
    # Admins can view but not add code snippets directly
    def has_add_permission(self, request, obj=None):
        return False


class RequestImageInline(admin.TabularInline):
    model = RequestImage
    extra = 0
    readonly_fields = ['image', 'image_url', 'thumbnail', 'thumbnail_url', 'caption', 'created_at']
    can_delete = True
    
    # Admins can view but not add images directly
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(HelpDeskRequest)
class HelpDeskRequestAdmin(admin.ModelAdmin):
    list_display = ['tracking_id_link', 'title_short', 'category_badge', 'priority_badge', 
                    'status_badge', 'author_info', 'response_count_badge', 
                    'is_resolved', 'age', 'created_at']
    list_filter = [
        'category', 
        'priority', 
        'status', 
        'is_resolved', 
        ('created_at', admin.DateFieldListFilter),
        'tags'
    ]
    search_fields = ['tracking_id', 'title', 'description', 'author__phone', 'author__first_name', 'author__last_name', 'tags']
    readonly_fields = ['tracking_id', 'author', 'view_count', 'response_count', 
                      'helpful_response_count', 'bookmark_count', 'created_at', 'updated_at',
                      'get_response_rate', 'get_engagement_score']
    inlines = [CodeSnippetInline, RequestImageInline]
    actions = ['mark_as_priority', 'mark_as_resolved', 'send_to_executives', 'delete_selected_requests']
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    # 🚫 Admins CANNOT create help requests on behalf of students
    def has_add_permission(self, request):
        return False
    
    fieldsets = (
        ('🎯 Request Info', {
            'fields': ('tracking_id', 'title', 'description', 'category', 'priority', 'status')
        }),
        ('👤 Author', {
            'fields': ('author',),
            'description': '⚠️ Author cannot be changed. Requests belong to the original user.'
        }),
        ('📚 Academic Info', {
            'fields': ('course', 'tags'),
            'classes': ('collapse',)
        }),
        ('📊 Statistics & Engagement', {
            'fields': ('view_count', 'response_count', 'helpful_response_count', 
                      'bookmark_count', 'get_response_rate', 'get_engagement_score'),
            'description': '📈 These statistics are automatically calculated and cannot be edited.'
        }),
        ('⏱️ Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at', 'last_response_at'),
            'classes': ('collapse',)
        }),
        ('🚩 Flags', {
            'fields': ('is_resolved', 'is_deleted')
        }),
    )
    
    def tracking_id_link(self, obj):
        url = reverse('admin:helpdesk_helpdeskrequest_change', args=[obj.id])
        return format_html('<a href="{}" style="font-weight: bold; color: #007bff;">{}</a>', url, obj.tracking_id)
    tracking_id_link.short_description = '🔖 Tracking ID'
    
    def title_short(self, obj):
        if len(obj.title) > 50:
            return format_html('<span title="{}">{}</span>', obj.title, obj.title[:50] + '...')
        return obj.title
    title_short.short_description = '📝 Title'
    
    def category_badge(self, obj):
        return format_html(
            '<span style="background: #007bff; color: white; padding: 3px 8px; border-radius: 12px;">{} {}</span>',
            obj.category.emoji, obj.category.name
        )
    category_badge.short_description = '🏷️ Category'
    
    def priority_badge(self, obj):
        colors = {
            'normal': '#28a745',
            'high': '#ffc107',
            'urgent': '#dc3545'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-weight: bold;">{}</span>',
            colors.get(obj.priority, '#6c757d'), obj.priority.upper()
        )
    priority_badge.short_description = '⚡ Priority'
    
    def status_badge(self, obj):
        colors = {
            'active': '#17a2b8',
            'resolved': '#28a745',
            'deleted': '#6c757d'
        }
        icons = {
            'active': '🔴',
            'resolved': '✅',
            'deleted': '🗑️'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px;">{} {}</span>',
            colors.get(obj.status, '#6c757d'), icons.get(obj.status, ''), obj.status.upper()
        )
    status_badge.short_description = '📊 Status'
    
    def author_info(self, obj):
        return format_html(
            '<span title="Phone: {}">{} {}</span>',
            obj.author.phone,
            obj.author.first_name,
            obj.author.last_name
        )
    author_info.short_description = '👤 Author'
    
    def response_count_badge(self, obj):
        count = obj.response_count
        if count == 0:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ {}</span>', count)
        elif count < 3:
            return format_html('<span style="color: orange; font-weight: bold;">💬 {}</span>', count)
        return format_html('<span style="color: green; font-weight: bold;">✅ {}</span>', count)
    response_count_badge.short_description = '💬 Responses'
    
    def age(self, obj):
        delta = timezone.now() - obj.created_at
        if delta.days > 7:
            return format_html('<span style="color: red; font-weight: bold;">🔥 {} days</span>', delta.days)
        elif delta.days > 3:
            return format_html('<span style="color: orange;">⚠️ {} days</span>', delta.days)
        elif delta.days > 0:
            return f'{delta.days} days'
        return f'{delta.seconds // 3600} hours'
    age.short_description = '⏰ Age'
    
    def get_response_rate(self, obj):
        if obj.view_count == 0:
            return '0%'
        rate = (obj.response_count / obj.view_count) * 100
        return f'{rate:.1f}%'
    get_response_rate.short_description = '📈 Response Rate'
    
    def get_engagement_score(self, obj):
        score = (obj.view_count * 0.3) + (obj.response_count * 2) + (obj.helpful_response_count * 5) + (obj.bookmark_count * 1.5)
        if score > 50:
            return format_html('<span style="color: green; font-weight: bold;">🔥 {:.0f}</span>', score)
        elif score > 20:
            return format_html('<span style="color: orange;">⚡ {:.0f}</span>', score)
        return f'{score:.0f}'
    get_engagement_score.short_description = '⭐ Engagement Score'
    
    # Admin Actions
    def mark_as_priority(self, request, queryset):
        updated = queryset.update(priority='urgent')
        self.message_user(request, f'{updated} request(s) marked as URGENT priority.')
    mark_as_priority.short_description = '⚡ Mark as URGENT priority'
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True, status='resolved', resolved_at=timezone.now())
        self.message_user(request, f'{updated} request(s) marked as RESOLVED.')
    mark_as_resolved.short_description = '✅ Mark as RESOLVED'
    
    def send_to_executives(self, request, queryset):
        # Create notifications for executives (you can enhance this)
        count = queryset.count()
        self.message_user(request, f'{count} request(s) flagged for executive attention.')
    send_to_executives.short_description = '🚨 Flag for Executive Review'
    
    def delete_selected_requests(self, request, queryset):
        updated = queryset.update(is_deleted=True, status='deleted')
        self.message_user(request, f'{updated} request(s) marked as deleted.')
    delete_selected_requests.short_description = '🗑️ Soft Delete Selected'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('category', 'author')


class ResponseCodeSnippetInline(admin.TabularInline):
    model = ResponseCodeSnippet
    extra = 0
    readonly_fields = ['language', 'code', 'description', 'created_at']
    can_delete = True
    
    # Admins can view but not add code snippets to responses
    def has_add_permission(self, request, obj=None):
        return False


class ResponseLinkInline(admin.TabularInline):
    model = ResponseLink
    extra = 0
    readonly_fields = ['url', 'title', 'description', 'image_url', 'created_at']
    can_delete = True
    
    # Admins can view but not add links to responses
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(HelpDeskResponse)
class HelpDeskResponseAdmin(admin.ModelAdmin):
    list_display = ['response_id', 'request_link', 'author_info', 'content_preview', 
                    'vote_summary', 'is_marked_helpful', 'created_at']
    list_filter = ['is_marked_helpful', 'created_at', 'is_deleted']
    search_fields = ['content', 'author__phone', 'author__first_name', 'request__tracking_id']
    readonly_fields = ['author', 'request', 'upvotes', 'downvotes', 'follow_up_count', 'created_at', 
                      'updated_at', 'marked_helpful_at', 'get_vote_ratio', 'get_quality_score']
    inlines = [ResponseCodeSnippetInline, ResponseLinkInline]
    actions = ['mark_as_helpful', 'remove_spam_responses']
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    # 🚫 Admins CANNOT create responses on behalf of students
    def has_add_permission(self, request):
        return False
    
    fieldsets = (
        ('📝 Response Info', {
            'fields': ('request', 'author', 'content'),
            'description': '⚠️ Request and Author cannot be changed. Responses belong to the original user.'
        }),
        ('👍 Voting & Engagement', {
            'fields': ('upvotes', 'downvotes', 'get_vote_ratio', 'get_quality_score', 
                      'follow_up_count', 'is_marked_helpful', 'marked_helpful_at'),
            'description': '📈 Vote counts are automatically calculated from user votes.'
        }),
        ('⏱️ Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('🚩 Status', {
            'fields': ('is_deleted',),
            'description': '🗑️ Use this to remove spam or inappropriate responses.'
        }),
    )
    
    def response_id(self, obj):
        return str(obj.id)[:8] + '...'
    response_id.short_description = 'ID'
    
    def request_link(self, obj):
        url = reverse('admin:helpdesk_helpdeskrequest_change', args=[obj.request.id])
        return format_html('<a href="{}" style="font-weight: bold;">{}</a>', url, obj.request.tracking_id)
    request_link.short_description = '🔗 Request'
    
    def author_info(self, obj):
        return format_html('{} {}', obj.author.first_name, obj.author.last_name)
    author_info.short_description = '👤 Author'
    
    def content_preview(self, obj):
        preview = obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
        return format_html('<div style="max-width: 300px;">{}</div>', preview)
    content_preview.short_description = '💬 Content'
    
    def vote_summary(self, obj):
        total = obj.upvotes + obj.downvotes
        if total == 0:
            return '—'
        ratio = (obj.upvotes / total) * 100
        color = 'green' if ratio > 80 else 'orange' if ratio > 50 else 'red'
        return format_html(
            '<span style="color: {};">👍 {} 👎 {} ({:.0f}%)</span>',
            color, obj.upvotes, obj.downvotes, ratio
        )
    vote_summary.short_description = '📊 Votes'
    
    def get_vote_ratio(self, obj):
        total = obj.upvotes + obj.downvotes
        if total == 0:
            return '0%'
        return f'{(obj.upvotes / total) * 100:.1f}%'
    get_vote_ratio.short_description = '📈 Upvote Ratio'
    
    def get_quality_score(self, obj):
        score = (obj.upvotes * 2) - (obj.downvotes * 1) + (10 if obj.is_marked_helpful else 0)
        if score > 20:
            return format_html('<span style="color: green; font-weight: bold;">⭐⭐⭐ {}</span>', score)
        elif score > 10:
            return format_html('<span style="color: orange;">⭐⭐ {}</span>', score)
        elif score > 0:
            return format_html('<span>⭐ {}</span>', score)
        return format_html('<span style="color: red;">❌ {}</span>', score)
    get_quality_score.short_description = '⭐ Quality Score'
    
    def mark_as_helpful(self, request, queryset):
        updated = queryset.update(is_marked_helpful=True, marked_helpful_at=timezone.now())
        self.message_user(request, f'{updated} response(s) marked as helpful.')
    mark_as_helpful.short_description = '⭐ Mark as Helpful'
    
    def remove_spam_responses(self, request, queryset):
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f'{updated} response(s) removed as spam.')
    remove_spam_responses.short_description = '🗑️ Remove as Spam'


@admin.register(ResponseVote)
class ResponseVoteAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'response_link', 'vote_badge', 'created_at']
    list_filter = ['vote_type', 'created_at']
    search_fields = ['user__phone', 'user__first_name', 'response__request__tracking_id']
    readonly_fields = ['user', 'response', 'vote_type', 'created_at', 'updated_at']
    
    # 🚫 Admins CANNOT create or edit votes - this would manipulate the voting system
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    # ✅ Admins CAN delete fraudulent votes
    def has_delete_permission(self, request, obj=None):
        return True
    
    def user_info(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'
    user_info.short_description = '👤 User'
    
    def response_link(self, obj):
        url = reverse('admin:helpdesk_helpdeskresponse_change', args=[obj.response.id])
        return format_html('<a href="{}">Response</a>', url)
    response_link.short_description = '🔗 Response'
    
    def vote_badge(self, obj):
        color = '#28a745' if obj.vote_type == 'upvote' else '#dc3545'
        icon = '👍' if obj.vote_type == 'upvote' else '👎'
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px;">{} {}</span>',
            color, icon, obj.vote_type.upper()
        )
    vote_badge.short_description = '🗳️ Vote'


@admin.register(RequestBookmark)
class RequestBookmarkAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'request_link', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__phone', 'user__first_name', 'request__tracking_id', 'request__title']
    readonly_fields = ['user', 'request', 'created_at']
    
    # 🚫 Admins CANNOT create bookmarks for users - this is personal user data
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    # ✅ Admins CAN delete bookmarks if needed (e.g., data cleanup)
    def has_delete_permission(self, request, obj=None):
        return True
    
    def user_info(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'
    user_info.short_description = '👤 User'
    
    def request_link(self, obj):
        url = reverse('admin:helpdesk_helpdeskrequest_change', args=[obj.request.id])
        return format_html('<a href="{}">{}</a>', url, obj.request.tracking_id)
    request_link.short_description = '🔖 Request'


@admin.register(RequestView)
class RequestViewAdmin(admin.ModelAdmin):
    list_display = ['request_link', 'user_info', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['user__phone', 'request__tracking_id', 'ip_address']
    readonly_fields = ['request', 'user', 'ip_address', 'user_agent', 'viewed_at']
    
    # 🚫 Admins CANNOT create or edit views - these are system-generated tracking data
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    # ✅ Admins CAN delete views for data cleanup
    def has_delete_permission(self, request, obj=None):
        return True
    
    def user_info(self, obj):
        if obj.user:
            return f'{obj.user.first_name} {obj.user.last_name}'
        return 'Anonymous'
    user_info.short_description = '👤 User'
    
    def request_link(self, obj):
        url = reverse('admin:helpdesk_helpdeskrequest_change', args=[obj.request.id])
        return format_html('<a href="{}">{}</a>', url, obj.request.tracking_id)
    request_link.short_description = '👁️ Request'


@admin.register(HelpDeskNotification)
class HelpDeskNotificationAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'notification_type_badge', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__phone', 'user__first_name', 'title', 'message']
    readonly_fields = ['user', 'notification_type', 'title', 'message', 'request', 'response', 'created_at', 'read_at']
    actions = ['mark_as_read']
    
    # 🚫 Admins CANNOT create notifications manually - these are system-generated
    def has_add_permission(self, request):
        return False
    
    # ✅ Admins CAN mark notifications as read or delete them
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True
    
    def user_info(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'
    user_info.short_description = '👤 User'
    
    def notification_type_badge(self, obj):
        colors = {
            'new_response': '#17a2b8',
            'response_marked_helpful': '#28a745',
            'response_upvoted': '#ffc107',
            'request_resolved': '#007bff',
            'follow_up': '#6c757d'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px;">{}</span>',
            colors.get(obj.notification_type, '#6c757d'), obj.get_notification_type_display()
        )
    notification_type_badge.short_description = '🔔 Type'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notification(s) marked as read.')
    mark_as_read.short_description = '✅ Mark as Read'


@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    list_display = ['reporter_info', 'reason_badge', 'status_badge', 'content_link', 'created_at']
    list_filter = ['reason', 'status', 'created_at']
    search_fields = ['reporter__phone', 'reporter__first_name', 'description']
    readonly_fields = ['reporter', 'reason', 'description', 'request', 'response', 'created_at', 'reviewed_at']
    actions = ['mark_as_reviewed', 'mark_as_actioned', 'dismiss_reports']
    
    # 🚫 Admins CANNOT create reports - users report content
    def has_add_permission(self, request):
        return False
    
    # ✅ Admins CAN review and action reports
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True
    
    fieldsets = (
        ('🚨 Report Info', {
            'fields': ('reporter', 'reason', 'description', 'status')
        }),
        ('📝 Content', {
            'fields': ('request', 'response')
        }),
        ('👨‍💼 Admin Action', {
            'fields': ('reviewed_by', 'admin_notes', 'reviewed_at')
        }),
        ('⏱️ Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def reporter_info(self, obj):
        return f'{obj.reporter.first_name} {obj.reporter.last_name}'
    reporter_info.short_description = '👤 Reporter'
    
    def reason_badge(self, obj):
        colors = {
            'spam': '#dc3545',
            'inappropriate': '#ffc107',
            'duplicate': '#17a2b8',
            'off_topic': '#6c757d',
            'other': '#6c757d'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px;">{}</span>',
            colors.get(obj.reason, '#6c757d'), obj.get_reason_display()
        )
    reason_badge.short_description = '⚠️ Reason'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'reviewed': '#17a2b8',
            'actioned': '#28a745',
            'dismissed': '#6c757d'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px;">{}</span>',
            colors.get(obj.status, '#6c757d'), obj.get_status_display().upper()
        )
    status_badge.short_description = '📊 Status'
    
    def content_link(self, obj):
        if obj.request:
            url = reverse('admin:helpdesk_helpdeskrequest_change', args=[obj.request.id])
            return format_html('<a href="{}">Request: {}</a>', url, obj.request.tracking_id)
        elif obj.response:
            url = reverse('admin:helpdesk_helpdeskresponse_change', args=[obj.response.id])
            return format_html('<a href="{}">Response</a>', url)
        return '—'
    content_link.short_description = '🔗 Content'
    
    def mark_as_reviewed(self, request, queryset):
        updated = queryset.update(status='reviewed', reviewed_at=timezone.now(), reviewed_by=request.user)
        self.message_user(request, f'{updated} report(s) marked as reviewed.')
    mark_as_reviewed.short_description = '👁️ Mark as Reviewed'
    
    def mark_as_actioned(self, request, queryset):
        updated = queryset.update(status='actioned', reviewed_at=timezone.now(), reviewed_by=request.user)
        self.message_user(request, f'{updated} report(s) marked as actioned.')
    mark_as_actioned.short_description = '✅ Mark as Actioned'
    
    def dismiss_reports(self, request, queryset):
        updated = queryset.update(status='dismissed', reviewed_at=timezone.now(), reviewed_by=request.user)
        self.message_user(request, f'{updated} report(s) dismissed.')
    dismiss_reports.short_description = '❌ Dismiss Reports'


@admin.register(UserReputation)
class UserReputationAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'points_badge', 'requests_created', 'responses_posted', 
                    'helpful_responses', 'reputation_level', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['user__phone', 'user__first_name', 'user__last_name']
    readonly_fields = ['user', 'points', 'requests_created', 'responses_posted', 
                      'helpful_responses', 'updated_at']
    ordering = ['-points']
    
    # 🚫 Admins CANNOT create or edit reputation - it's calculated from user activity
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    # ✅ Admins CAN view reputation for monitoring
    def has_delete_permission(self, request, obj=None):
        return False
    
    def user_info(self, obj):
        return format_html(
            '<strong>{} {}</strong><br/><small>{}</small>',
            obj.user.first_name, obj.user.last_name, obj.user.phone
        )
    user_info.short_description = '👤 User'
    
    def points_badge(self, obj):
        if obj.points > 500:
            return format_html('<span style="color: gold; font-weight: bold; font-size: 16px;">🏆 {}</span>', obj.points)
        elif obj.points > 200:
            return format_html('<span style="color: silver; font-weight: bold; font-size: 16px;">🥈 {}</span>', obj.points)
        elif obj.points > 50:
            return format_html('<span style="color: #cd7f32; font-weight: bold; font-size: 16px;">🥉 {}</span>', obj.points)
        return format_html('<span style="font-weight: bold;">⭐ {}</span>', obj.points)
    points_badge.short_description = '⭐ Points'
    
    def reputation_level(self, obj):
        if obj.points > 500:
            return format_html('<span style="color: gold; font-weight: bold;">🏆 Expert</span>')
        elif obj.points > 200:
            return format_html('<span style="color: silver; font-weight: bold;">🥈 Advanced</span>')
        elif obj.points > 50:
            return format_html('<span style="color: #cd7f32; font-weight: bold;">🥉 Intermediate</span>')
        return format_html('<span>⭐ Beginner</span>')
    reputation_level.short_description = '🎯 Level'


@admin.register(ResponseReply)
class ResponseReplyAdmin(admin.ModelAdmin):
    list_display = ['id', 'response', 'author', 'content_preview', 'parent_reply', 'created_at', 'is_deleted']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['content', 'author__phone', 'author__first_name']
    readonly_fields = ['author', 'response', 'parent_reply', 'created_at', 'updated_at']
    
    # 🚫 Admins CANNOT create replies on behalf of users
    def has_add_permission(self, request):
        return False
    
    # ✅ Admins CAN moderate content (mark as deleted for spam/inappropriate content)
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

