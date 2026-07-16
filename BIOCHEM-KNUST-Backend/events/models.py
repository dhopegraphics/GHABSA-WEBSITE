from django.db import models
from uuid import uuid4
import secrets
import string
# CloudinaryField replaced with ImageField using DynamicStorage
# from cloudinary.models import CloudinaryField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage

User = get_user_model()


# Create your models here.
class Event(MediaUrlMixin, models.Model):
    """
    Main Event model - MAINTAINS BACKWARD COMPATIBILITY with frontend
    All original fields preserved for website compatibility
    """
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'event_image_1': 'event_image_1_url',
        'event_image_2': 'event_image_2_url',
    }
    
    # ========== ORIGINAL FIELDS (DO NOT MODIFY - USED BY WEBSITE FRONTEND) ==========
    event_name = models.CharField(max_length=200)
    event_id = models.UUIDField(
        primary_key=True, unique=True, default=uuid4, editable=False
    )
    description = models.TextField()
    registration_link = models.URLField(
        null=True,
        blank=True,
        help_text="Registration link for event if any (external registration)",
    )
    event_image_1 = models.ImageField(storage=DynamicStorage(), upload_to="EventsImages/", null=True, blank=True)
    event_image_1_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide image URL instead of uploading"
    )
    event_image_2 = models.ImageField(storage=DynamicStorage(), upload_to="EventsImages/", null=True, blank=True)
    event_image_2_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide image URL instead of uploading"
    )
    event_date = models.DateTimeField(null=True, blank=False, help_text="Event start date and time")
    event_end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Event end date and time. If not set, event is assumed to be a single-day event"
    )
    organised_by = models.CharField(max_length=200)
    media_link = models.URLField(
        null=True,
        blank=True,
        help_text="Url for more pictures and videos taken at the event (e.g., Google Drive, Dropbox)",
    )
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True, auto_now_add=False)
    # ========== END ORIGINAL FIELDS ==========
    
    # ========== NEW FIELDS FOR MOBILE APP ENHANCEMENT ==========
    # Event Type & Category
    EVENT_TYPES = (
        ('workshop', 'Workshop'),
        ('meeting', 'Meeting'),
        ('competition', 'Competition'),
        ('social', 'Social'),
        ('talk', 'Tech Talk'),
        ('seminar', 'Seminar'),
        ('conference', 'Conference'),
        ('other', 'Other'),
    )
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPES,
        default='other',
        help_text="Category of event for mobile app filtering"
    )
    
    # Location Information
    LOCATION_TYPES = (
        ('physical', 'Physical Location'),
        ('virtual', 'Virtual Event'),
        ('hybrid', 'Hybrid Event'),
    )
    location_type = models.CharField(
        max_length=20,
        choices=LOCATION_TYPES,
        default='physical'
    )
    venue = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        help_text="Physical venue name (e.g., 'NB LT1')"
    )
    building = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Building name (e.g., 'New Block')"
    )
    virtual_link = models.URLField(
        blank=True,
        null=True,
        help_text="Virtual meeting link (Google Meet, Zoom, etc.)"
    )
    
    # Registration Details (for internal CSS-managed registrations)
    requires_registration = models.BooleanField(
        default=False,
        help_text="Does this event require registration? (Different from external registration_link)"
    )
    max_attendees = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Maximum number of attendees (null = unlimited)"
    )
    registration_deadline = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Deadline for registration"
    )
    allows_team_registration = models.BooleanField(
        default=False,
        help_text="Allow team registrations (for competitions/hackathons)"
    )
    min_team_size = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    max_team_size = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    
    # RSVP Settings
    allows_rsvp = models.BooleanField(
        default=True,
        help_text="Allow users to RSVP to this event"
    )
    
    # Event Display
    emoji = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Emoji icon for event (e.g., 🎓, 🚀, 💻)"
    )
    featured = models.BooleanField(
        default=False,
        help_text="Feature this event in mobile app"
    )
    
    # Sync Memo (Photo Gallery)
    sync_memo_enabled = models.BooleanField(
        default=True,
        help_text="Enable photo uploads for this event"
    )
    
    # ========== PAYMENT SETTINGS ==========
    requires_payment = models.BooleanField(
        default=False,
        help_text="Does this event require payment for registration?"
    )
    payment_description = models.TextField(
        blank=True,
        null=True,
        help_text="Description of what the payment covers (e.g., 'Includes lunch, materials, and certificate')"
    )
    early_bird_deadline = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Deadline for early bird pricing (if applicable)"
    )
    payment_deadline = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Deadline for payment. After this, registration closes."
    )
    allow_partial_payment = models.BooleanField(
        default=False,
        help_text="Allow users to pay in installments"
    )
    minimum_deposit_percentage = models.IntegerField(
        default=50,
        validators=[MinValueValidator(10), MaxValueValidator(100)],
        help_text="Minimum deposit percentage if partial payment is allowed"
    )
    # ========== END PAYMENT SETTINGS ==========
    
    # Capacity tracking (computed properties will be in serializer)
    
    def __str__(self) -> str:
        return self.event_name
    
    @property
    def is_past(self):
        """Check if event has ended"""
        now = timezone.now()
        if self.event_end_date:
            return self.event_end_date < now
        return self.event_date < now.replace(hour=0, minute=0, second=0, microsecond=0) if self.event_date else False
    
    @property
    def is_registration_open(self):
        """Check if registration is still open"""
        if not self.requires_registration:
            return False
        if self.registration_deadline:
            return timezone.now() < self.registration_deadline
        return not self.is_past
    
    @property
    def attendee_count(self):
        """Get total confirmed attendees (RSVP attending + registrations)"""
        rsvp_count = self.rsvps.filter(status='attending').count()
        reg_count = self.registrations.filter(status='confirmed').count()
        return rsvp_count + reg_count
    
    @property
    def is_full(self):
        """Check if event is at capacity"""
        if not self.max_attendees:
            return False
        return self.attendee_count >= self.max_attendees
    
    @property
    def is_early_bird_active(self):
        """Check if early bird pricing is active"""
        if not self.early_bird_deadline:
            return False
        return timezone.now() < self.early_bird_deadline
    
    @property
    def is_payment_deadline_passed(self):
        """Check if payment deadline has passed"""
        if not self.payment_deadline:
            return False
        return timezone.now() > self.payment_deadline
    
    @property
    def lowest_package_price(self):
        """Get the lowest available package price"""
        packages = self.payment_packages.filter(is_active=True)
        if not packages.exists():
            return None
        if self.is_early_bird_active:
            return min(p.early_bird_price or p.price for p in packages)
        return min(p.price for p in packages)
    
    @property
    def has_available_packages(self):
        """Check if there are available packages"""
        return self.payment_packages.filter(is_active=True).exists()
    
    @property
    def total_revenue(self):
        """Calculate total revenue from successful payments"""
        from django.db.models import Sum
        total = self.payment_transactions.filter(
            status='success'
        ).aggregate(total=Sum('amount'))['total']
        return total or Decimal('0.00')
    
    @property
    def paid_registrations_count(self):
        """Count of fully paid registrations"""
        return self.registrations.filter(payment_status='paid').count()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Event"
        verbose_name_plural = "Events"
        indexes = [
            models.Index(fields=['event_date', '-created_at']),
            models.Index(fields=['event_type', 'event_date']),
            models.Index(fields=['requires_payment', 'event_date']),
        ]


class EventRSVP(models.Model):
    """
    Track user RSVP responses to events
    Mobile app feature for event attendance tracking
    """
    RSVP_STATUS = (
        ('attending', 'Attending'),
        ('maybe', 'Maybe'),
        ('not_attending', 'Not Attending'),
    )
    
    REMINDER_CHOICES = (
        ('none', 'No Reminder'),
        ('1_hour', '1 Hour Before'),
        ('1_day', '1 Day Before'),
        ('1_week', '1 Week Before'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_rsvps')
    status = models.CharField(max_length=20, choices=RSVP_STATUS)
    reminder = models.CharField(
        max_length=20,
        choices=REMINDER_CHOICES,
        default='none'
    )
    notes = models.TextField(blank=True, null=True, help_text="User's notes about attendance")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-created_at']
        verbose_name = "Event RSVP"
        verbose_name_plural = "Event RSVPs"
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.event.event_name} ({self.status})"


class EventRegistration(models.Model):
    """
    Internal event registrations managed by CSS
    For events that require formal registration (competitions, workshops)
    """
    REGISTRATION_STATUS = (
        ('pending', 'Pending'),
        ('pending_payment', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('waitlist', 'Waitlist'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_STATUS = (
        ('not_required', 'Not Required'),
        ('pending', 'Payment Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
        ('refunded', 'Refunded'),
        ('failed', 'Payment Failed'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    registration_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique registration number for tracking"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_registrations')
    status = models.CharField(max_length=20, choices=REGISTRATION_STATUS, default='pending')
    
    # Payment Information
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='not_required'
    )
    payment_package = models.ForeignKey(
        'EventPaymentPackage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registrations',
        help_text="Selected payment package for this registration"
    )
    amount_due = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total amount due for registration"
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total amount paid so far"
    )
    payment_completed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When payment was fully completed"
    )
    
    # Personal Information
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    student_id = models.CharField(max_length=20, blank=True, null=True)
    year_group = models.CharField(max_length=50, blank=True, null=True)
    program = models.CharField(max_length=200, blank=True, null=True)
    
    # Team Information (for team-based events)
    is_team_leader = models.BooleanField(default=False)
    team_name = models.CharField(max_length=200, blank=True, null=True)
    
    # Additional Fields
    dietary_restrictions = models.TextField(blank=True, null=True)
    special_requirements = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Admin fields
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(blank=True, null=True)
    admin_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Internal notes for admins"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-created_at']
        verbose_name = "Event Registration"
        verbose_name_plural = "Event Registrations"
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['event', 'payment_status']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['team_name']),
            models.Index(fields=['registration_number']),
        ]
    
    def save(self, *args, **kwargs):
        # Generate registration number if not set
        if not self.registration_number:
            self.registration_number = self._generate_registration_number()
        super().save(*args, **kwargs)
    
    def _generate_registration_number(self):
        """Generate unique registration number like EVT-ABC123"""
        prefix = "EVT"
        while True:
            chars = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            reg_num = f"{prefix}-{chars}"
            if not EventRegistration.objects.filter(registration_number=reg_num).exists():
                return reg_num
    
    def __str__(self):
        return f"{self.full_name} - {self.event.event_name} ({self.status})"
    
    @property
    def balance_due(self):
        """Calculate remaining balance"""
        return self.amount_due - self.amount_paid
    
    @property
    def is_fully_paid(self):
        """Check if registration is fully paid"""
        return self.amount_paid >= self.amount_due and self.amount_due > 0
    
    @property
    def payment_percentage(self):
        """Calculate payment percentage"""
        if self.amount_due <= 0:
            return 100
        return int((self.amount_paid / self.amount_due) * 100)
    
    def update_payment_status(self):
        """Update payment status based on amounts"""
        if not self.event.requires_payment or self.amount_due == 0:
            self.payment_status = 'not_required'
        elif self.amount_paid >= self.amount_due:
            self.payment_status = 'paid'
            if not self.payment_completed_at:
                self.payment_completed_at = timezone.now()
            # Auto-confirm registration when fully paid
            if self.status == 'pending_payment':
                self.status = 'confirmed'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'pending'
        self.save()


class TeamMember(models.Model):
    """
    Team members for team-based event registrations
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    registration = models.ForeignKey(
        EventRegistration,
        on_delete=models.CASCADE,
        related_name='team_members'
    )
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    student_id = models.CharField(max_length=20, blank=True, null=True)
    year_group = models.CharField(max_length=50, blank=True, null=True)
    program = models.CharField(max_length=200, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True, help_text="Role in team")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"
    
    def __str__(self):
        return f"{self.full_name} ({self.registration.team_name})"


class SyncMemoAlbum(MediaUrlMixin, models.Model):
    """
    Photo albums for events (Sync Memo feature)
    Each event can have one album where users upload photos
    """
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'cover_photo': 'cover_photo_url',
    }
    
    ALBUM_STATUS = (
        ('live', 'Live'),
        ('ended', 'Ended'),
        ('archived', 'Archived'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='sync_memo_album')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=ALBUM_STATUS, default='live')
    cover_photo = models.ImageField(storage=DynamicStorage(), upload_to="SyncMemo/Covers/", blank=True, null=True)
    cover_photo_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide cover photo URL instead of uploading"
    )
    
    # Settings
    allow_uploads = models.BooleanField(default=True)
    allow_comments = models.BooleanField(default=True)
    require_approval = models.BooleanField(
        default=False,
        help_text="Photos require admin approval before being visible"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Sync Memo Album"
        verbose_name_plural = "Sync Memo Albums"
    
    def __str__(self):
        return f"{self.event.event_name} - Album"
    
    @property
    def photo_count(self):
        return self.photos.filter(is_approved=True).count()
    
    @property
    def contributor_count(self):
        return self.photos.values('uploaded_by').distinct().count()


class SyncMemoPhoto(MediaUrlMixin, models.Model):
    """
    Individual photos in Sync Memo albums
    """
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'photo': 'photo_url',
    }
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    album = models.ForeignKey(SyncMemoAlbum, on_delete=models.CASCADE, related_name='photos')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sync_memo_photos')
    photo = models.ImageField(storage=DynamicStorage(), upload_to="SyncMemo/Photos/", blank=True, null=True)
    photo_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide photo URL instead of uploading"
    )
    caption = models.TextField(blank=True, null=True)
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_photos'
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    
    # Sharing
    share_to_feed = models.BooleanField(
        default=False,
        help_text="Share this photo to the news feed"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Sync Memo Photo"
        verbose_name_plural = "Sync Memo Photos"
        indexes = [
            models.Index(fields=['album', '-created_at']),
            models.Index(fields=['uploaded_by', '-created_at']),
        ]
    
    def __str__(self):
        return f"Photo by {self.uploaded_by.username} in {self.album.event.event_name}"
    
    @property
    def like_count(self):
        return self.likes.count()
    
    @property
    def comment_count(self):
        return self.comments.count()


class SyncMemoLike(models.Model):
    """
    Track photo likes
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    photo = models.ForeignKey(SyncMemoPhoto, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sync_memo_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('photo', 'user')
        ordering = ['-created_at']
        verbose_name = "Photo Like"
        verbose_name_plural = "Photo Likes"
    
    def __str__(self):
        return f"{self.user.username} liked photo {self.photo.id}"


class SyncMemoComment(models.Model):
    """
    Comments on photos
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    photo = models.ForeignKey(SyncMemoPhoto, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sync_memo_comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Photo Comment"
        verbose_name_plural = "Photo Comments"
        indexes = [
            models.Index(fields=['photo', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} commented on {self.photo.id}"
    
    @property
    def like_count(self):
        return self.comment_likes.count()


class SyncMemoCommentLike(models.Model):
    """
    Track comment likes
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    comment = models.ForeignKey(SyncMemoComment, on_delete=models.CASCADE, related_name='comment_likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('comment', 'user')
        ordering = ['-created_at']
        verbose_name = "Comment Like"
        verbose_name_plural = "Comment Likes"
    
    def __str__(self):
        return f"{self.user.username} liked comment {self.comment.id}"


# ========== EVENT PAYMENT MODELS ==========

class EventPaymentPackage(models.Model):
    """
    Payment packages/tiers for events
    Allows events to have different pricing options (e.g., Standard, VIP, Early Bird)
    """
    PACKAGE_TYPES = (
        ('standard', 'Standard'),
        ('vip', 'VIP'),
        ('student', 'Student'),
        ('group', 'Group'),
        ('early_bird', 'Early Bird'),
        ('late', 'Late Registration'),
        ('custom', 'Custom'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='payment_packages'
    )
    
    # Package Details
    name = models.CharField(
        max_length=100,
        help_text="Package name (e.g., 'Standard Ticket', 'VIP Access')"
    )
    package_type = models.CharField(
        max_length=20,
        choices=PACKAGE_TYPES,
        default='standard'
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="What's included in this package"
    )
    
    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Regular price in GHS"
    )
    early_bird_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Early bird price (uses event's early_bird_deadline)"
    )
    
    # Capacity
    max_slots = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Maximum slots for this package (null = unlimited)"
    )
    
    # Benefits/Perks
    benefits = models.JSONField(
        default=list,
        blank=True,
        help_text="List of benefits included in this package"
    )
    
    # Availability
    is_active = models.BooleanField(default=True)
    available_from = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When this package becomes available"
    )
    available_until = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When this package expires"
    )
    
    # Display
    display_order = models.IntegerField(
        default=0,
        help_text="Order in which packages are displayed (lower = first)"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Highlight this package as recommended"
    )
    badge_text = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Badge text to display (e.g., 'Most Popular', 'Best Value')"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'price']
        verbose_name = "Event Payment Package"
        verbose_name_plural = "Event Payment Packages"
        indexes = [
            models.Index(fields=['event', 'is_active']),
            models.Index(fields=['event', 'display_order']),
        ]
    
    def __str__(self):
        return f"{self.event.event_name} - {self.name} (GHS {self.price})"
    
    @property
    def current_price(self):
        """Get current applicable price (early bird or regular)"""
        if self.early_bird_price and self.event.is_early_bird_active:
            return self.early_bird_price
        return self.price
    
    @property
    def slots_taken(self):
        """Count confirmed registrations for this package"""
        return self.registrations.filter(
            payment_status__in=['paid', 'partial']
        ).count()
    
    @property
    def slots_available(self):
        """Calculate available slots"""
        if not self.max_slots:
            return None  # Unlimited
        return max(0, self.max_slots - self.slots_taken)
    
    @property
    def is_sold_out(self):
        """Check if package is sold out"""
        if not self.max_slots:
            return False
        return self.slots_taken >= self.max_slots
    
    @property
    def is_available(self):
        """Check if package is currently available for purchase"""
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.is_sold_out:
            return False
        
        if self.available_from and now < self.available_from:
            return False
        
        if self.available_until and now > self.available_until:
            return False
        
        return True
    
    @property
    def savings_amount(self):
        """Calculate savings if early bird is active"""
        if self.early_bird_price and self.event.is_early_bird_active:
            return self.price - self.early_bird_price
        return Decimal('0.00')


class EventPaymentTransaction(models.Model):
    """
    Payment transactions for event registrations
    Separate from main payment system but follows similar structure
    """
    TRANSACTION_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
        ('expired', 'Expired'),
    )
    
    PAYMENT_METHODS = (
        ('card', 'Card Payment'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('ussd', 'USSD'),
        ('cash', 'Cash'),
        ('manual', 'Manual Payment'),
    )
    
    PAYMENT_GATEWAYS = (
        ('paystack', 'Paystack'),
        ('flutterwave', 'Flutterwave'),
        ('stripe', 'Stripe'),
        ('momo', 'Mobile Money Direct'),
        ('manual', 'Manual/Cash'),
    )
    
    TRANSACTION_TYPES = (
        ('payment', 'Payment'),
        ('partial_payment', 'Partial Payment'),
        ('balance_payment', 'Balance Payment'),
        ('refund', 'Refund'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    reference = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique transaction reference"
    )
    
    # Relations
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='payment_transactions'
    )
    registration = models.ForeignKey(
        EventRegistration,
        on_delete=models.CASCADE,
        related_name='payment_transactions'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='event_payment_transactions'
    )
    package = models.ForeignKey(
        EventPaymentPackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    
    # Transaction Details
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        default='payment'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3, default='GHS')
    
    # Payment Method & Gateway
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        blank=True
    )
    payment_gateway = models.CharField(
        max_length=20,
        choices=PAYMENT_GATEWAYS,
        default='paystack'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=TRANSACTION_STATUS,
        default='pending',
        db_index=True
    )
    status_message = models.TextField(
        blank=True,
        help_text="Detailed status message or error"
    )
    
    # Gateway Response
    gateway_reference = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Reference from payment gateway"
    )
    gateway_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full response from payment gateway"
    )
    authorization_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL for payment authorization (for redirect-based payments)"
    )
    access_code = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Access code for payment (Paystack)"
    )
    
    # Customer Info (for record keeping)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_name = models.CharField(max_length=255, blank=True)
    
    # Fees
    gateway_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fee charged by payment gateway"
    )
    net_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount after gateway fees"
    )
    
    # IP and metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional transaction metadata"
    )
    
    # Refund tracking
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount refunded"
    )
    refund_reason = models.TextField(blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    refunded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='event_refunds_processed'
    )
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this payment session expires"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    # Verification
    verified = models.BooleanField(
        default=False,
        help_text="Has this transaction been verified with gateway"
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-initiated_at']
        verbose_name = "Event Payment Transaction"
        verbose_name_plural = "Event Payment Transactions"
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['registration', 'status']),
            models.Index(fields=['user', '-initiated_at']),
            models.Index(fields=['reference']),
            models.Index(fields=['gateway_reference']),
            models.Index(fields=['status', '-initiated_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Generate reference if not set
        if not self.reference:
            self.reference = self._generate_reference()
        
        # Calculate net amount
        if self.status == 'success' and self.net_amount == 0:
            self.net_amount = self.amount - self.gateway_fee
        
        # Set completed timestamp
        if self.status == 'success' and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Update registration payment status
        if self.registration:
            self._update_registration_payment()
    
    def _generate_reference(self):
        """Generate unique transaction reference like EVTPAY-ABC123XYZ"""
        prefix = "EVTPAY"
        while True:
            chars = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))
            ref = f"{prefix}-{chars}"
            if not EventPaymentTransaction.objects.filter(reference=ref).exists():
                return ref
    
    def _update_registration_payment(self):
        """Update registration payment status based on successful transactions"""
        if self.status == 'success':
            total_paid = EventPaymentTransaction.objects.filter(
                registration=self.registration,
                status='success',
                transaction_type__in=['payment', 'partial_payment', 'balance_payment']
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
            
            # Subtract refunds
            total_refunded = EventPaymentTransaction.objects.filter(
                registration=self.registration,
                status='success',
                transaction_type='refund'
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
            
            self.registration.amount_paid = total_paid - total_refunded
            self.registration.update_payment_status()
    
    def __str__(self):
        return f"{self.reference} - {self.event.event_name} - GHS {self.amount} ({self.status})"
    
    @property
    def is_successful(self):
        return self.status == 'success'
    
    @property
    def is_pending(self):
        return self.status in ['pending', 'processing']
    
    @property
    def is_failed(self):
        return self.status in ['failed', 'cancelled', 'expired']
    
    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at and self.status == 'pending'
    
    @property
    def can_be_refunded(self):
        return (
            self.status == 'success' and
            self.transaction_type in ['payment', 'partial_payment', 'balance_payment'] and
            self.refund_amount < self.amount
        )
    
    @property
    def refundable_amount(self):
        return self.amount - self.refund_amount


class EventPaymentRefund(models.Model):
    """
    Refund records for event payments
    """
    REFUND_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('rejected', 'Rejected'),
    )
    
    REFUND_REASONS = (
        ('event_cancelled', 'Event Cancelled'),
        ('user_request', 'User Request'),
        ('duplicate_payment', 'Duplicate Payment'),
        ('event_rescheduled', 'Event Rescheduled'),
        ('dissatisfaction', 'User Dissatisfaction'),
        ('admin_decision', 'Admin Decision'),
        ('other', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    reference = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )
    
    # Relations
    original_transaction = models.ForeignKey(
        EventPaymentTransaction,
        on_delete=models.CASCADE,
        related_name='refund_records'
    )
    registration = models.ForeignKey(
        EventRegistration,
        on_delete=models.CASCADE,
        related_name='refunds'
    )
    
    # Refund Details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Amount to refund"
    )
    reason = models.CharField(max_length=30, choices=REFUND_REASONS)
    reason_details = models.TextField(
        blank=True,
        help_text="Additional details about refund reason"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=REFUND_STATUS,
        default='pending'
    )
    status_message = models.TextField(blank=True)
    
    # Gateway Response
    gateway_reference = models.CharField(max_length=255, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Admin tracking
    initiated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='initiated_event_refunds'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_event_refunds'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Event Payment Refund"
        verbose_name_plural = "Event Payment Refunds"
        indexes = [
            models.Index(fields=['original_transaction', 'status']),
            models.Index(fields=['registration', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generate_reference()
        super().save(*args, **kwargs)
    
    def _generate_reference(self):
        """Generate unique refund reference"""
        prefix = "EVTREF"
        while True:
            chars = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))
            ref = f"{prefix}-{chars}"
            if not EventPaymentRefund.objects.filter(reference=ref).exists():
                return ref
    
    def __str__(self):
        return f"{self.reference} - Refund GHS {self.amount} ({self.status})"
    
    @property
    def is_successful(self):
        return self.status == 'success'
    
    @property
    def is_partial(self):
        return self.amount < self.original_transaction.amount
