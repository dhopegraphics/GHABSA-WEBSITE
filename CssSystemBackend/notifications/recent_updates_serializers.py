"""
Recent Updates Serializers
Serializes aggregated notifications from various models without storing them
"""
from rest_framework import serializers
from django.utils.timesince import timesince


class RecentUpdateSerializer(serializers.Serializer):
    """
    Unified serializer for all types of recent updates/notifications
    No model backing - aggregates data from multiple sources
    """
    id = serializers.CharField(read_only=True, help_text="Unique identifier for this update")
    type = serializers.ChoiceField(
        choices=[
            ('task_created', 'Task Created'),
            ('task_completed', 'Task Completed'),
            ('task_due_soon', 'Task Due Soon'),
            ('event_created', 'Event Created'),
            ('event_upcoming', 'Event Upcoming'),
            ('helpdesk_status_changed', 'Helpdesk Status Changed'),
            ('helpdesk_response_added', 'Helpdesk Response Added'),
            ('payment_success', 'Payment Success'),
            ('payment_failed', 'Payment Failed'),
            ('payment_uncollected', 'Payment Uncollected'),
            ('merchandise_collected', 'Merchandise Collected'),
            ('merchandise_partial_collected', 'Merchandise Partially Collected'),
            ('security_password_changed', 'Security Password Changed'),
            ('security_profile_updated', 'Security Profile Updated'),
        ],
        read_only=True,
        help_text="Type of update"
    )
    category = serializers.CharField(read_only=True, help_text="Display category (Tasks, Events, HelpDesk, etc.)")
    title = serializers.CharField(read_only=True, help_text="Update title")
    description = serializers.CharField(read_only=True, help_text="Detailed message")
    
    # Priority
    priority = serializers.ChoiceField(
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')],
        read_only=True,
        default='medium',
        help_text="Notification priority"
    )
    
    # Additional data
    metadata = serializers.JSONField(read_only=True, default=dict, help_text="Additional contextual data")
    related_object_id = serializers.CharField(read_only=True, allow_null=True, help_text="ID of related object")
    
    # Read status
    is_read = serializers.SerializerMethodField(help_text="Whether user has read this update")
    
    # Timestamps
    created_at = serializers.DateTimeField(read_only=True, help_text="When the update occurred")
    time_ago = serializers.SerializerMethodField(help_text="Human-readable time")
    
    def get_is_read(self, obj):
        """Check if user has read this update"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from notifications.models import RecentUpdateReadStatus
            return RecentUpdateReadStatus.objects.filter(
                user=request.user,
                update_id=obj.get('id'),
                is_deleted=False
            ).exists()
        return False
    
    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        created_at = obj.get('created_at')
        if created_at:
            return timesince(created_at) + ' ago'
        return 'Just now'


class TaskUpdateSerializer(serializers.Serializer):
    """Serializer for task-related updates"""
    task_id = serializers.UUIDField()
    title = serializers.CharField()
    status = serializers.CharField()
    priority = serializers.CharField()
    due_date = serializers.DateField()
    due_time = serializers.TimeField(allow_null=True)
    emoji = serializers.CharField()
    completed = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class EventUpdateSerializer(serializers.Serializer):
    """Serializer for event-related updates"""
    event_id = serializers.UUIDField()
    title = serializers.CharField()
    event_type = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    location = serializers.CharField(allow_null=True)
    is_featured = serializers.BooleanField()
    registration_required = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class HelpdeskUpdateSerializer(serializers.Serializer):
    """Serializer for helpdesk ticket updates"""
    ticket_id = serializers.UUIDField()
    subject = serializers.CharField()
    status = serializers.CharField()
    category = serializers.CharField()
    priority = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    has_new_response = serializers.BooleanField(default=False)
    response_count = serializers.IntegerField(default=0)


class PaymentUpdateSerializer(serializers.Serializer):
    """Serializer for payment-related updates"""
    transaction_id = serializers.UUIDField()
    reference = serializers.CharField()
    product_name = serializers.CharField()
    product_image = serializers.CharField(allow_null=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.IntegerField(default=1)
    status = serializers.CharField()
    validation_code = serializers.CharField(allow_null=True)
    is_collected = serializers.BooleanField(default=False)
    payment_method = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()


class SecurityUpdateSerializer(serializers.Serializer):
    """Serializer for security-related updates"""
    type = serializers.ChoiceField(
        choices=[
            ('password_change', 'Password Changed'),
            ('email_change', 'Email Changed'),
            ('profile_update', 'Profile Updated'),
            ('login_attempt', 'Login Attempt'),
        ]
    )
    message = serializers.CharField()
    timestamp = serializers.DateTimeField()
    ip_address = serializers.CharField(allow_null=True)
    device = serializers.CharField(allow_null=True)


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    total = serializers.IntegerField(help_text="Total number of updates")
    unread = serializers.IntegerField(help_text="Number of unread updates")
    by_type = serializers.DictField(help_text="Count by update type")
    by_priority = serializers.DictField(help_text="Count by priority")
    today_count = serializers.IntegerField(help_text="Updates from today")
    this_week_count = serializers.IntegerField(help_text="Updates from this week")
    urgent_count = serializers.IntegerField(help_text="Urgent updates requiring action")


class RecentUpdatesResponseSerializer(serializers.Serializer):
    """Response serializer for recent updates list"""
    count = serializers.IntegerField(help_text="Total count of updates")
    next = serializers.CharField(allow_null=True, help_text="Next page URL")
    previous = serializers.CharField(allow_null=True, help_text="Previous page URL")
    results = RecentUpdateSerializer(many=True, help_text="List of updates")
    stats = NotificationStatsSerializer(help_text="Update statistics")
