from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator, MaxLengthValidator
from uuid import uuid4
from accounts.models import CustomUser
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage


class HelpDeskCategory(models.Model):
    """Categories for help requests"""
    
    CATEGORY_CHOICES = [
        ('academic', 'Academic Help'),
        ('technical', 'Technical Support'),
        ('society', 'Society & Events'),
        ('codequest', 'CodeQuest Support'),
        ('career', 'Career & Internships'),
        ('general', 'General Help'),
    ]
    
    id = models.CharField(
        max_length=20, 
        primary_key=True, 
        choices=CATEGORY_CHOICES
    )
    name = models.CharField(max_length=100)
    emoji = models.CharField(max_length=10)
    icon = models.CharField(max_length=50)
    description = models.TextField()
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'helpdesk_categories'
        verbose_name = 'HelpDesk Category'
        verbose_name_plural = 'HelpDesk Categories'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


class HelpDeskRequest(models.Model):
    """Main help request model"""
    
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('deleted', 'Deleted'),
    ]
    
    # Primary Key
    id = models.UUIDField(
        primary_key=True, 
        default=uuid4, 
        editable=False
    )
    
    # Tracking ID (user-friendly)
    tracking_id = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False,
        db_index=True
    )
    
    # Content
    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(10)]
    )
    description = models.TextField(
        validators=[
            MinLengthValidator(50),
            MaxLengthValidator(5000)
        ]
    )
    
    # Classification
    category = models.ForeignKey(
        HelpDeskCategory,
        on_delete=models.PROTECT,
        related_name='requests'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )
    
    # Optional fields
    course = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    tags = models.JSONField(
        default=list,
        blank=True
    )
    
    # Author (anonymous to public)
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='helpdesk_requests'
    )
    
    # Stats (denormalized for performance)
    view_count = models.IntegerField(default=0)
    response_count = models.IntegerField(default=0)
    helpful_response_count = models.IntegerField(default=0)
    bookmark_count = models.IntegerField(default=0)
    
    # Flags
    is_resolved = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    last_response_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'helpdesk_requests'
        verbose_name = 'Help Request'
        verbose_name_plural = 'Help Requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Generate tracking ID if new
        if not self.tracking_id:
            year = timezone.now().year
            # Get last tracking number for this year
            last_request = HelpDeskRequest.objects.filter(
                tracking_id__startswith=f'HD-{year}-'
            ).order_by('-tracking_id').first()
            
            if last_request:
                last_number = int(last_request.tracking_id.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.tracking_id = f'HD-{year}-{str(new_number).zfill(4)}'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.tracking_id}: {self.title}'


class CodeSnippet(models.Model):
    """Code snippets attached to requests"""
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    request = models.ForeignKey(
        HelpDeskRequest,
        on_delete=models.CASCADE,
        related_name='code_snippets'
    )
    language = models.CharField(max_length=50)
    code = models.TextField(validators=[MaxLengthValidator(10000)])
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'helpdesk_code_snippets'
        ordering = ['created_at']
    
    def __str__(self):
        return f'{self.language} snippet for {self.request.tracking_id}'


class RequestImage(MediaUrlMixin, models.Model):
    """Images attached to requests"""
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'image': 'image_url',
        'thumbnail': 'thumbnail_url',
    }
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    request = models.ForeignKey(
        HelpDeskRequest,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(storage=DynamicStorage(), upload_to='helpdesk/requests/%Y/%m/', blank=True, null=True)
    image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide image URL instead of uploading"
    )
    thumbnail = models.ImageField(
        storage=DynamicStorage(),
        upload_to='helpdesk/requests/thumbnails/%Y/%m/',
        null=True,
        blank=True
    )
    thumbnail_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide thumbnail URL instead of uploading"
    )
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'helpdesk_request_images'
        ordering = ['created_at']
    
    def __str__(self):
        return f'Image for {self.request.tracking_id}'


class HelpDeskResponse(models.Model):
    """Responses to help requests"""
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    request = models.ForeignKey(
        HelpDeskRequest,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='helpdesk_responses'
    )
    content = models.TextField(
        validators=[
            MinLengthValidator(20),
            MaxLengthValidator(10000)
        ]
    )
    
    # Stats (denormalized)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    follow_up_count = models.IntegerField(default=0)
    
    # Flags
    is_marked_helpful = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    marked_helpful_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'helpdesk_responses'
        verbose_name = 'Help Response'
        verbose_name_plural = 'Help Responses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['request', '-created_at']),
            models.Index(fields=['request', '-upvotes']),
            models.Index(fields=['author', '-created_at']),
        ]
    
    def __str__(self):
        return f'Response to {self.request.tracking_id} by {self.author.phone}'


class ResponseCodeSnippet(models.Model):
    """Code snippets in responses"""
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    response = models.ForeignKey(
        HelpDeskResponse,
        on_delete=models.CASCADE,
        related_name='code_snippets'
    )
    language = models.CharField(max_length=50)
    code = models.TextField(validators=[MaxLengthValidator(10000)])
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'helpdesk_response_code_snippets'
        ordering = ['created_at']
    
    def __str__(self):
        return f'{self.language} snippet in response'


class ResponseLink(models.Model):
    """External links in responses"""
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    response = models.ForeignKey(
        HelpDeskResponse,
        on_delete=models.CASCADE,
        related_name='links'
    )
    url = models.URLField(max_length=500)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'helpdesk_response_links'
        ordering = ['created_at']
    
    def __str__(self):
        return f'Link: {self.url}'


class ResponseReply(models.Model):
    """Replies/follow-up questions to responses"""
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    response = models.ForeignKey(
        HelpDeskResponse,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    parent_reply = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='nested_replies'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='helpdesk_replies'
    )
    content = models.TextField(
        validators=[
            MinLengthValidator(5),
            MaxLengthValidator(2000)
        ]
    )
    
    # Flags
    is_deleted = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'helpdesk_response_replies'
        verbose_name = 'Response Reply'
        verbose_name_plural = 'Response Replies'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['response', 'created_at']),
            models.Index(fields=['author', '-created_at']),
        ]
    
    def __str__(self):
        return f'Reply to response by {self.author.phone}'


class ResponseVote(models.Model):
    """Votes on responses"""
    
    VOTE_CHOICES = [
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    response = models.ForeignKey(
        HelpDeskResponse,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='helpdesk_votes'
    )
    vote_type = models.CharField(max_length=10, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'helpdesk_votes'
        unique_together = [['response', 'user']]
        indexes = [
            models.Index(fields=['response', 'vote_type']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.vote_type} on response by {self.user.phone}'


class RequestBookmark(models.Model):
    """User bookmarks of requests"""
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    request = models.ForeignKey(
        HelpDeskRequest,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='helpdesk_bookmarks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'helpdesk_bookmarks'
        unique_together = [['request', 'user']]
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f'Bookmark: {self.request.tracking_id} by {self.user.phone}'


class RequestView(models.Model):
    """Track request views"""
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    request = models.ForeignKey(
        HelpDeskRequest,
        on_delete=models.CASCADE,
        related_name='views'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='helpdesk_views',
        null=True,
        blank=True  # Allow anonymous views
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'helpdesk_views'
        indexes = [
            models.Index(fields=['request', '-viewed_at']),
            models.Index(fields=['user', '-viewed_at']),
        ]
    
    def __str__(self):
        return f'View of {self.request.tracking_id}'


class HelpDeskNotification(models.Model):
    """Notifications for helpdesk activities"""
    
    NOTIFICATION_TYPES = [
        ('new_response', 'New Response'),
        ('response_marked_helpful', 'Response Marked Helpful'),
        ('response_upvoted', 'Response Upvoted'),
        ('request_resolved', 'Request Resolved'),
        ('follow_up', 'Follow-up Question'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='helpdesk_notifications'
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # References
    request = models.ForeignKey(
        HelpDeskRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    response = models.ForeignKey(
        HelpDeskResponse,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    # State
    is_read = models.BooleanField(default=False, db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'helpdesk_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.notification_type} for {self.user.phone}'


class ContentReport(models.Model):
    """Reports of inappropriate content"""
    
    REASON_CHOICES = [
        ('spam', 'Spam or Advertising'),
        ('inappropriate', 'Inappropriate Content'),
        ('duplicate', 'Duplicate'),
        ('off_topic', 'Off Topic'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('actioned', 'Actioned'),
        ('dismissed', 'Dismissed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    reporter = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='helpdesk_reports'
    )
    
    # What's being reported (one must be set)
    request = models.ForeignKey(
        HelpDeskRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports'
    )
    response = models.ForeignKey(
        HelpDeskResponse,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports'
    )
    
    # Report details
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Admin action
    reviewed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_helpdesk_reports'
    )
    admin_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'helpdesk_reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f'Report by {self.reporter.phone}: {self.reason}'


class UserReputation(models.Model):
    """Track user reputation in HelpDesk (future feature)"""
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='helpdesk_reputation'
    )
    
    # Stats
    points = models.IntegerField(default=0)
    requests_created = models.IntegerField(default=0)
    requests_resolved = models.IntegerField(default=0)
    responses_posted = models.IntegerField(default=0)
    helpful_responses = models.IntegerField(default=0)
    upvotes_received = models.IntegerField(default=0)
    downvotes_received = models.IntegerField(default=0)
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'helpdesk_user_reputation'
    
    def __str__(self):
        return f'{self.user.phone}: {self.points} points'

