"""
Device and Session Tracking Models
Tracks all devices and sessions where user accounts are logged in
"""
from django.db import models
from django.utils import timezone
from accounts.models import CustomUser
import uuid


class UserDevice(models.Model):
    """
    Tracks devices/sessions where users have logged in
    """
    DEVICE_TYPE_CHOICES = [
        ('mobile', 'Mobile Device'),
        ('tablet', 'Tablet'),
        ('desktop', 'Desktop/Laptop'),
        ('web', 'Web Browser'),
        ('unknown', 'Unknown'),
    ]
    
    PLATFORM_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('windows', 'Windows'),
        ('macos', 'macOS'),
        ('linux', 'Linux'),
        ('web', 'Web Browser'),
        ('unknown', 'Unknown'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='devices'
    )
    
    # Device Information
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPE_CHOICES,
        default='unknown',
        help_text="Type of device (mobile, tablet, desktop, web)"
    )
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        default='unknown',
        help_text="Operating system or platform"
    )
    device_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Device model or name (e.g., iPhone 15, Samsung Galaxy S23)"
    )
    browser = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Browser name and version"
    )
    
    # Session Information
    is_current = models.BooleanField(
        default=False,
        help_text="Is this the current active device?"
    )
    last_active = models.DateTimeField(
        auto_now=True,
        help_text="Last time this device was active"
    )
    first_login = models.DateTimeField(
        auto_now_add=True,
        help_text="First time this device logged in"
    )
    
    # Location Information
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="IP address of the device"
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Country from IP geolocation"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="City from IP geolocation"
    )
    
    # Technical Details
    user_agent = models.TextField(
        blank=True,
        null=True,
        help_text="Full user agent string"
    )
    device_fingerprint = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Unique identifier for this device"
    )
    
    # Token tracking for session management
    refresh_token_jti = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="JWT refresh token JTI for session management"
    )
    
    # Status
    is_trusted = models.BooleanField(
        default=False,
        help_text="Has user marked this device as trusted?"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this session still active?"
    )
    is_blocked = models.BooleanField(
        default=False,
        help_text="Is this device blocked from accessing the account?"
    )
    blocked_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When was this device blocked?"
    )
    block_reason = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Reason for blocking this device"
    )
    
    class Meta:
        verbose_name = "User Device"
        verbose_name_plural = "User Devices"
        ordering = ['-last_active']
        indexes = [
            models.Index(fields=['user', '-last_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device_fingerprint']),
        ]
    
    def __str__(self):
        device_info = self.device_name or f"{self.get_platform_display()} {self.get_device_type_display()}"
        return f"{self.user.get_full_name()} - {device_info}"
    
    def mark_as_current(self):
        """Mark this device as the current active device"""
        # Unmark all other devices for this user
        UserDevice.objects.filter(user=self.user).exclude(id=self.id).update(is_current=False)
        self.is_current = True
        self.is_active = True
        self.save()
    
    def get_location_display(self):
        """Get formatted location string"""
        if self.city and self.country:
            return f"{self.city}, {self.country}"
        elif self.country:
            return self.country
        return "Unknown Location"
    
    def get_device_display(self):
        """Get user-friendly device description"""
        if self.device_name:
            return self.device_name
        return f"{self.get_platform_display()} {self.get_device_type_display()}"
    
    def deactivate(self):
        """Deactivate this device session (logout)"""
        self.is_active = False
        self.is_current = False
        self.save()
    
    def block(self, reason=None):
        """Block this device from accessing the account"""
        self.is_blocked = True
        self.is_active = False
        self.is_current = False
        self.blocked_at = timezone.now()
        if reason:
            self.block_reason = reason
        self.save()
    
    def unblock(self):
        """Unblock this device"""
        self.is_blocked = False
        self.blocked_at = None
        self.block_reason = None
        self.save()


class DeviceLoginHistory(models.Model):
    """
    Tracks login history for each device
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(
        UserDevice,
        on_delete=models.CASCADE,
        related_name='login_history'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='login_history'
    )
    
    # Login Details
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    
    # Status
    success = models.BooleanField(
        default=True,
        help_text="Was the login successful?"
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Reason for failed login (if applicable)"
    )
    
    class Meta:
        verbose_name = "Device Login History"
        verbose_name_plural = "Device Login Histories"
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', '-login_time']),
            models.Index(fields=['device', '-login_time']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.user.get_full_name()} - {status} - {self.login_time}"
