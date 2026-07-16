from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission, Group
# CloudinaryField replaced with ImageField using DynamicStorage
# from cloudinary.models import CloudinaryField
from accounts.models import CustomUser
from django.contrib.auth.models import Permission
from uuid import uuid4
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage

# Create your models here.

TITLE_CHOICES = [
    ('Mr', 'Mr'),
    ('Mrs', 'Mrs'),
    ('Ms', 'Ms'),
    ('Dr', 'Dr'),
    ('Prof', 'Prof'),
    ('Mx', 'Mx'),
    ('Other', 'Other'),
]


class ExecutivePosition(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    # Lower value = higher display priority (1 = top)
    priority = models.IntegerField(
        default=999,
        help_text="Lower value = higher display priority (1 = top)."
    )
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True, auto_now_add=False)

    def __str__(self) -> str:
        return str(self.name)

    class Meta:
        ordering = ['priority', 'name']


class Executive(MediaUrlMixin, models.Model):
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'image': 'image_url',
    }
    
    executive_id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        unique=True,
    )
    image = models.ImageField(
        storage=DynamicStorage(),
        upload_to="ExecutiveImages/",
        blank=True,
        null=True,
    )
    image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide image URL (Google Drive, Dropbox, etc.) instead of uploading"
    )
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(
        max_length=20,
        choices=TITLE_CHOICES,
        blank=True,
        null=True,
        help_text="Optional title (e.g., Mr, Ms, Dr)"
    )
    position = models.ForeignKey(ExecutivePosition, on_delete=models.CASCADE)
    office_from = models.DateTimeField(auto_now=False, auto_now_add=False, null=True)
    office_to = models.DateTimeField(auto_now=False, auto_now_add=False, null=True, blank=True)
    office_year = models.CharField(
        max_length=20,
        help_text="Academic year (e.g., 2024/2025)",
        null=True,
        blank=True
    )
    bio = models.TextField(
        blank=True,
        null=True,
        help_text="Biography/About section for the executive"
    )
    skills = models.JSONField(
        default=list,
        blank=True,
        help_text="List of skills (e.g., ['Python', 'Leadership', 'Public Speaking'])"
    )
    achievements = models.JSONField(
        default=list,
        blank=True,
        help_text="List of achievements and accomplishments"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        name = f"{self.user.first_name} {self.user.last_name}".strip()
        if self.title:
            # Some titles (Dr, Prof) are typically written without a trailing dot
            if self.title in ('Dr', 'Prof'):
                return f"{self.title} {name}"
            return f"{self.title}. {name}"
        return name
    
    class Meta:
        ordering = ['position__priority', '-office_from']
        verbose_name = "Executive"
        verbose_name_plural = "Executives"
        permissions = (
            ("can_access_mobile_dashboard", "Can access executive/admin dashboard from mobile"),
        )
        constraints = [
            models.UniqueConstraint(
                fields=['position', 'office_year'],
                condition=Q(is_active=True),
                name='unique_position_office_year_active'
            ),
        ]

    def clean(self):
        """
        Ensure there is only one active Executive per position for the same office_year.
        """
        # Only validate when this executive is active and an office_year is provided
        if getattr(self, 'is_active', True) and self.office_year and self.position:
            qs = type(self).objects.filter(
                position=self.position,
                office_year=self.office_year,
                is_active=True,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({
                    'position': 'This position already has an active executive for the specified office year.'
                })


platform_choices = [
    ("facebook", "Facebook"),
    ("twitter", "Twitter"),
    ("instagram", "Instagram"),
    ("linkedin", "LinkedIn"),
    ("youtube", "YouTube"),
    ("snapchat", "Snapchat"),
    ("tiktok", "TikTok"),
    ("pinterest", "Pinterest"),
    ("reddit", "Reddit"),
    ("whatsapp", "WhatsApp"),
    ("telegram", "Telegram"),
    ("discord", "Discord"),
    ("twitch", "Twitch"),
    ("flickr", "Flickr"),
    ("quora", "Quora"),
    ("medium", "Medium"),
    ("github", "GitHub"),
    ("slack", "Slack"),
]


class ExecutiveSocialLinks(models.Model):
    executive = models.ForeignKey(
        Executive,
        on_delete=models.CASCADE,
        related_name="social_media_links",
    )
    platform = models.CharField(max_length=255, choices=platform_choices)
    link = models.URLField()

    class Meta:
        db_table = "executives_social_links"
        verbose_name = "Executive social links"
        verbose_name_plural = "Executive social links"


# Committee Models
class Committee(models.Model):
    committee_id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        unique=True,
    )
    name = models.CharField(max_length=200, help_text="Committee name (e.g., Technical Committee, Welfare Committee)")
    description = models.TextField(help_text="Brief description of the committee's purpose and responsibilities")
    is_active = models.BooleanField(default=True, help_text="Whether this committee is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Committee"
        verbose_name_plural = "Committees"


ROLE_CHOICES = [
    ("head", "Head"),
    ("deputy_head", "Deputy Head"),
    ("member", "Member"),
]


class Appointee(MediaUrlMixin, models.Model):
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'image': 'image_url',
    }
    
    appointee_id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        unique=True,
    )
    image = models.ImageField(
        storage=DynamicStorage(),
        upload_to="AppointeeImages/",
        blank=True,
        null=True,
    )
    image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide image URL (Google Drive, Dropbox, etc.) instead of uploading"
    )
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name="appointee_roles"
    )
    committee = models.ForeignKey(
        Committee,
        on_delete=models.CASCADE,
        related_name="members"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="member",
        help_text="Role in the committee (Head, Deputy Head, or Member)"
    )
    portfolio = models.TextField(
        blank=True,
        help_text="Specific responsibilities and duties of this appointee"
    )
    bio = models.TextField(
        blank=True,
        null=True,
        help_text="Biography/About section for the appointee"
    )
    skills = models.JSONField(
        default=list,
        blank=True,
        help_text="List of skills (e.g., ['Python', 'Leadership', 'Public Speaking'])"
    )
    achievements = models.JSONField(
        default=list,
        blank=True,
        help_text="List of achievements and accomplishments"
    )
    appointed_from = models.DateTimeField(auto_now_add=False, null=True)
    appointed_to = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    office_year = models.CharField(
        max_length=20,
        help_text="Academic year (e.g., 2024/2025)",
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.committee.name} ({self.get_role_display()})"

    class Meta:
        ordering = ['committee', 'role', 'user__first_name']
        verbose_name = "Appointee"
        verbose_name_plural = "Appointees"
        # Ensure a user cannot have more than one active appointee role in the same office year.
        # Also ensure there is only one active `head` and one active `deputy_head` per committee per office_year.
        # The constraints below are conditional on `is_active=True` so historical/inactive entries don't block re-appointments.
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'office_year'],
                condition=Q(is_active=True),
                name='unique_user_office_year_active'
            ),
            models.UniqueConstraint(
                fields=['committee', 'office_year'],
                condition=Q(is_active=True, role='head'),
                name='unique_head_per_committee_year'
            ),
            models.UniqueConstraint(
                fields=['committee', 'office_year'],
                condition=Q(is_active=True, role='deputy_head'),
                name='unique_deputy_per_committee_year'
            ),
        ]

    def clean(self):
        """
        Business validation:
        - A user must not hold more than one active appointee role in the same office_year.
        This method raises ValidationError which will be surfaced in admin and serializer flows.
        """
        # Only validate when this appointee is active and an office_year is provided
        if self.is_active and self.office_year:
            # 1) Prevent same user holding multiple active appointee roles in same office_year
            qs = type(self).objects.filter(
                user=self.user,
                office_year=self.office_year,
                is_active=True,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {
                        'user': 'This user already has an active appointee role for the specified office year.'
                    }
                )

            # 2) If role is head or deputy_head, ensure there's only one for the committee in the same office year
            if self.role in ('head', 'deputy_head') and self.committee:
                role_qs = type(self).objects.filter(
                    committee=self.committee,
                    role=self.role,
                    office_year=self.office_year,
                    is_active=True,
                )
                if self.pk:
                    role_qs = role_qs.exclude(pk=self.pk)
                if role_qs.exists():
                    raise ValidationError(
                        {
                            'role': f"There is already an active '{self.get_role_display()}' for this committee in the specified office year."
                        }
                    )

    def save(self, *args, **kwargs):
        # Run full_clean to ensure model-level validation (clean) is enforced everywhere
        self.full_clean()
        return super().save(*args, **kwargs)


class AppointeeSocialLinks(models.Model):
    appointee = models.ForeignKey(
        Appointee,
        on_delete=models.CASCADE,
        related_name="social_media_links",
    )
    platform = models.CharField(max_length=255, choices=platform_choices)
    link = models.URLField()

    class Meta:
        db_table = "appointee_social_links"
        verbose_name = "Appointee social links"
        verbose_name_plural = "Appointee social links"


class AppointeeContactDetails(models.Model):
    appointee = models.OneToOneField(
        Appointee,
        on_delete=models.CASCADE,
        related_name="contact_details"
    )
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    office_location = models.CharField(max_length=200, blank=True, null=True)
    office_hours = models.CharField(max_length=200, blank=True, null=True, help_text="e.g., Mon-Fri 9AM-5PM")

    def __str__(self):
        return f"Contact for {self.appointee.user.first_name} {self.appointee.user.last_name}"

    class Meta:
        verbose_name = "Appointee Contact Details"
        verbose_name_plural = "Appointee Contact Details"


class AppointeePermission(models.Model):
    """
    Stores additional permissions granted to committee members by heads/deputies.
    This allows heads and deputies to grant subset of their permissions to members.
    Uses Django's built-in Permission model to access all backend permissions.
    """
    permission_id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        unique=True,
    )
    appointee = models.ForeignKey(
        Appointee,
        on_delete=models.CASCADE,
        related_name="granted_permissions"
    )
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        help_text="Select permissions from all available backend permissions. Use Ctrl/Cmd to select multiple.",
        related_name="appointee_permissions"
    )
    groups = models.ManyToManyField(
        Group,
        blank=True,
        help_text="Optionally assign permission groups to the user along with individual permissions.",
        related_name='appointee_permission_groups'
    )
    granted_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="permissions_granted",
        help_text="User (Head/Deputy) who granted these permissions"
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to temporarily disable all permissions without deleting"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional expiration date for temporary permissions"
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional notes about why these permissions were granted"
    )

    def __str__(self):
        perm_count = self.permissions.count()
        return f"{self.appointee.user.first_name} {self.appointee.user.last_name} - {perm_count} permissions"
    
    def get_permission_list(self):
        """Returns a list of permission codenames"""
        return list(self.permissions.values_list('codename', flat=True))
    
    def get_permission_display(self):
        """Returns a formatted string of all permissions"""
        return ", ".join(self.permissions.values_list('name', flat=True))

    class Meta:
        verbose_name = "Appointee Permission"
        verbose_name_plural = "Appointee Permissions"
        unique_together = ['appointee']
        ordering = ['-granted_at']

    def save(self, *args, **kwargs):
        """
        Persist the AppointeePermission record and reflect its active grants on the
        related user's account. When `is_active=True` we add the listed permissions
        and groups to the user. When deactivated we remove individual permissions
        that are no longer provided by any other active AppointeePermission for
        that appointee and are not supplied via the user's groups.
        Note: group removal is intentionally conservative (we do not auto-remove groups)
        to avoid accidentally removing groups assigned for other reasons.
        """
        super().save(*args, **kwargs)
        # Apply grants after save; note: permissions/groups m2m may be set later
        # so we also attach m2m_changed handlers below to ensure apply_grants runs
        try:
            self.apply_grants()
        except Exception:
            # swallow to avoid breaking save paths; errors are surfaced elsewhere
            pass


    def apply_grants(self):
        """Apply or remove granted permissions/groups on the related user's account
        based on the current state of this AppointeePermission instance.
        This method is safe to call multiple times and will only add/remove what
        is necessary.
        """
        try:
            user = self.appointee.user
        except Exception:
            return

        if not user:
            return

        # Active: add permissions and groups
        if self.is_active:
            for perm in self.permissions.all():
                if not user.user_permissions.filter(pk=perm.pk).exists():
                    user.user_permissions.add(perm)

            for grp in self.groups.all():
                if not user.groups.filter(pk=grp.pk).exists():
                    user.groups.add(grp)

        else:
            # Deactivated: remove permissions only if no other active grant or group provides them
            for perm in self.permissions.all():
                other_active = AppointeePermission.objects.filter(
                    appointee=self.appointee,
                    permissions=perm,
                    is_active=True
                ).exclude(pk=self.pk).exists()

                provided_by_group = user.groups.filter(permissions=perm).exists()

                if not other_active and not provided_by_group:
                    user.user_permissions.remove(perm)

        user.save()


# m2m_changed handlers to apply grants after permissions/groups are updated
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


@receiver(m2m_changed, sender=AppointeePermission.permissions.through)
def appointeepermission_permissions_changed(sender, instance, action, **kwargs):
    if action in ('post_add', 'post_remove', 'post_clear'):
        try:
            instance.apply_grants()
        except Exception:
            pass


@receiver(m2m_changed, sender=AppointeePermission.groups.through)
def appointeepermission_groups_changed(sender, instance, action, **kwargs):
    if action in ('post_add', 'post_remove', 'post_clear'):
        try:
            instance.apply_grants()
        except Exception:
            pass


# Ensure when an Appointee is created we add the default AppointeePermission
from django.db.models.signals import post_save


@receiver(post_save, sender=Appointee)
def create_default_appointee_permission(sender, instance, created, **kwargs):
    """
    Auto-create AppointeePermission ONLY for heads and deputy heads.
    Members should NOT get automatic AppointeePermission - their head/deputy
    will create it manually through the admin when granting permissions.
    """
    if not created:
        return

    # ONLY create AppointeePermission for heads and deputy heads
    # Members will have their AppointeePermission created by the head/deputy via admin
    if instance.role not in ['head', 'deputy_head']:
        return

    try:
        from django.contrib.auth.models import Group
        # find the default group by name
        grp = Group.objects.filter(name__iexact='Head/Deputy Appointee').first()
        if not grp:
            return

        # If there is already an AppointeePermission for this appointee, skip
        if AppointeePermission.objects.filter(appointee=instance).exists():
            return

        perm = AppointeePermission.objects.create(
            appointee=instance,
            granted_by=None,  # Will be set by admin or can be superuser
            is_active=True,
        )
        
        # Assign the group to heads and deputy heads
        perm.groups.add(grp)
        perm.save()
        try:
            perm.apply_grants()
        except Exception:
            pass
    except Exception:
        # Do not raise — just avoid failing appointee creation
        pass


# Keep Executive user groups in sync with their position where applicable
@receiver(post_save, sender=Executive)
def sync_executive_groups(sender, instance, created, **kwargs):
    """
    When an Executive is created or updated, add the corresponding Group
    to the linked user based on the Executive position name. This is
    intentionally additive (we do not remove groups) to avoid accidental
    removal of other roles.
    """
    try:
        if not instance or not getattr(instance, 'position', None) or not getattr(instance, 'user', None):
            return

        # Normalize position name for matching
        pos_name = (instance.position.name or '').strip().lower()

        # Mapping from position keywords to Group names in the system
        position_to_group = {
            'president': 'President Role',
            'vice president': 'Vice President',
            'general secretary': 'General Secretary',
            'financial secretary': 'Financial',
            'organizing secretary': 'Organizing Secretary',
            'organiser': 'Organizing Secretary',
            'organiser secretary': 'Organizing Secretary',
            'women': 'Wocom',
            'womens': 'Wocom',
            'women\'s commissioner': 'Wocom',
            'wocom': 'Wocom',
        }

        matched_group_name = None
        for key, grp_name in position_to_group.items():
            if key in pos_name:
                matched_group_name = grp_name
                break

        if not matched_group_name:
            return

        grp = Group.objects.filter(name__iexact=matched_group_name).first()
        if not grp:
            return

        user = instance.user
        if instance.is_active:
            if not user.groups.filter(pk=grp.pk).exists():
                user.groups.add(grp)
                user.save()
    except Exception:
        # Avoid raising errors during save; failure to sync groups is non-fatal
        pass


class PermissionAuditLog(models.Model):
    """
    Audit trail for all permission changes.
    Tracks who granted/revoked permissions and when.
    """
    ACTION_CHOICES = [
        ('grant', 'Permission Granted'),
        ('revoke', 'Permission Revoked'),
        ('modify', 'Permission Modified'),
    ]
    
    log_id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        unique=True,
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    permissions = models.ManyToManyField(
        Permission,
        help_text="Permissions that were granted/revoked/modified",
        related_name="audit_logs"
    )
    
    # Who was affected
    target_user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="permission_changes_received",
        help_text="User who received the permission change (kept for audit trail even if user deleted)"
    )
    target_committee = models.ForeignKey(
        Committee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="permission_audit_logs",
        help_text="Committee affected by the permission change"
    )
    
    # Who made the change
    performed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="permission_changes_made"
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        action_display = self.get_action_display()
        target_name = f"{self.target_user.first_name} {self.target_user.last_name}"
        return f"{action_display} - {target_name} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Permission Audit Log"
        verbose_name_plural = "Permission Audit Logs"
        ordering = ['-timestamp']


# ============================================
# MEETING AND ATTENDANCE SYSTEM
# ============================================

MEETING_TYPE_CHOICES = [
    ('executive', 'Executive Meeting'),
    ('committee', 'Committee Meeting'),
    ('general', 'General Meeting'),
    ('emergency', 'Emergency Meeting'),
    ('agm', 'Annual General Meeting'),
    ('joint', 'Joint Meeting'),
    ('other', 'Other'),
]

MEETING_STATUS_CHOICES = [
    ('scheduled', 'Scheduled'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
    ('postponed', 'Postponed'),
]

ATTENDANCE_STATUS_CHOICES = [
    ('present', 'Present'),
    ('absent', 'Absent'),
    ('excused', 'Excused'),
    ('late', 'Late'),
    ('left_early', 'Left Early'),
]


class Meeting(models.Model):
    """
    Represents a meeting for executives, committees, or both.
    Supports scheduling, tracking attendance, and storing minutes.
    """
    meeting_id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        unique=True,
    )
    
    # Meeting details
    title = models.CharField(
        max_length=255,
        help_text="Title/subject of the meeting"
    )
    meeting_type = models.CharField(
        max_length=20,
        choices=MEETING_TYPE_CHOICES,
        default='executive'
    )
    description = models.TextField(
        blank=True,
        help_text="Brief description or purpose of the meeting"
    )
    agenda = models.TextField(
        blank=True,
        help_text="Meeting agenda items (can be formatted as bullet points)"
    )
    
    # Scope - who is this meeting for?
    # If committee is set, it's a committee meeting
    # If committee is null and is_executive_meeting is True, it's for all executives
    committee = models.ForeignKey(
        Committee,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="meetings",
        help_text="Committee this meeting is for (leave empty for executive meetings)"
    )
    is_executive_meeting = models.BooleanField(
        default=False,
        help_text="Check if this is an executive-level meeting (all executives invited)"
    )
    
    # Additional invitees (for joint meetings or special guests)
    additional_invitees = models.ManyToManyField(
        CustomUser,
        blank=True,
        related_name="invited_meetings",
        help_text="Additional people invited to this meeting"
    )
    
    # Schedule
    scheduled_date = models.DateField(
        help_text="Date of the meeting"
    )
    scheduled_time = models.TimeField(
        help_text="Start time of the meeting"
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Expected/actual end time"
    )
    duration_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Expected duration in minutes"
    )
    
    # Location
    venue = models.CharField(
        max_length=255,
        blank=True,
        help_text="Physical location of the meeting"
    )
    virtual_link = models.URLField(
        blank=True,
        help_text="Link for virtual/online meeting (Zoom, Google Meet, etc.)"
    )
    is_virtual = models.BooleanField(
        default=False,
        help_text="Is this meeting virtual/online?"
    )
    is_hybrid = models.BooleanField(
        default=False,
        help_text="Is this a hybrid meeting (both physical and virtual)?"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=MEETING_STATUS_CHOICES,
        default='scheduled'
    )
    
    # Academic year context
    office_year = models.CharField(
        max_length=20,
        help_text="Academic year (e.g., 2024/2025)",
        null=True,
        blank=True
    )
    
    # Organizer/Creator
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="meetings_created",
        help_text="Person who created/scheduled this meeting"
    )
    chaired_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meetings_chaired",
        help_text="Person chairing/leading this meeting"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Meeting"
        verbose_name_plural = "Meetings"
        ordering = ['-scheduled_date', '-scheduled_time']
        indexes = [
            models.Index(fields=['scheduled_date', 'status']),
            models.Index(fields=['committee', 'status']),
            models.Index(fields=['meeting_type', 'status']),
        ]
    
    def __str__(self):
        date_str = self.scheduled_date.strftime('%b %d, %Y') if self.scheduled_date else 'TBD'
        return f"{self.title} - {date_str}"
    
    @property
    def is_upcoming(self):
        """Check if meeting is in the future"""
        from django.utils import timezone
        from datetime import datetime
        meeting_datetime = datetime.combine(self.scheduled_date, self.scheduled_time)
        return timezone.make_aware(meeting_datetime) > timezone.now()
    
    @property
    def expected_attendees(self):
        """Get list of expected attendees based on meeting type"""
        attendees = set()
        
        if self.is_executive_meeting:
            # All active executives
            for exec in Executive.objects.filter(is_active=True, office_year=self.office_year):
                attendees.add(exec.user)
        
        if self.committee:
            # All active committee members
            for appointee in self.committee.members.filter(is_active=True, office_year=self.office_year):
                attendees.add(appointee.user)
        
        # Additional invitees
        for user in self.additional_invitees.all():
            attendees.add(user)
        
        return list(attendees)
    
    @property
    def attendance_stats(self):
        """Get attendance statistics"""
        attendances = self.attendances.all()
        total = attendances.count()
        if total == 0:
            return {'total': 0, 'present': 0, 'absent': 0, 'excused': 0, 'rate': 0}
        
        present = attendances.filter(status__in=['present', 'late']).count()
        absent = attendances.filter(status='absent').count()
        excused = attendances.filter(status='excused').count()
        
        return {
            'total': total,
            'present': present,
            'absent': absent,
            'excused': excused,
            'rate': round((present / total) * 100, 1) if total > 0 else 0
        }


class MeetingAttendance(models.Model):
    """
    Tracks attendance for each person at a meeting.
    """
    attendance_id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        unique=True,
    )
    
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="attendances"
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="meeting_attendances"
    )
    
    # Attendance status
    status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_STATUS_CHOICES,
        default='present'
    )
    
    # Time tracking
    arrival_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Actual arrival time"
    )
    departure_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Actual departure time (if left early)"
    )
    
    # Additional info
    excuse_reason = models.TextField(
        blank=True,
        help_text="Reason for absence or excuse (if applicable)"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this attendance"
    )
    
    # Who recorded this
    recorded_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="attendances_recorded",
        help_text="Person who recorded this attendance"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Meeting Attendance"
        verbose_name_plural = "Meeting Attendances"
        unique_together = ['meeting', 'user']
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.meeting.title} ({self.get_status_display()})"
    
    def clean(self):
        """Validate attendance record"""
        if self.status == 'excused' and not self.excuse_reason:
            raise ValidationError({
                'excuse_reason': 'Please provide a reason for the excused absence.'
            })


class MeetingMinutes(MediaUrlMixin, models.Model):
    """
    Stores meeting minutes, including uploaded documents and text content.
    """
    MEDIA_URL_FIELDS = {
        'minutes_file': 'minutes_file_url',
    }
    
    minutes_id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        unique=True,
    )
    
    meeting = models.OneToOneField(
        Meeting,
        on_delete=models.CASCADE,
        related_name="minutes"
    )
    
    # Text content of minutes
    content = models.TextField(
        blank=True,
        help_text="Full text content of the meeting minutes"
    )
    summary = models.TextField(
        blank=True,
        help_text="Brief summary of key points and decisions"
    )
    
    # File upload for minutes document
    minutes_file = models.FileField(
        storage=DynamicStorage(),
        upload_to="MeetingMinutes/",
        blank=True,
        null=True,
        help_text="Upload the minutes document (PDF, DOCX, etc.)"
    )
    minutes_file_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide URL to minutes document (Google Drive, Dropbox, etc.)"
    )
    
    # Decisions and action items
    decisions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of decisions made during the meeting"
    )
    action_items = models.JSONField(
        default=list,
        blank=True,
        help_text="List of action items with assignees and deadlines. Format: [{'task': '...', 'assignee': '...', 'deadline': '...'}]"
    )
    
    # Approval status
    is_approved = models.BooleanField(
        default=False,
        help_text="Have these minutes been approved?"
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="minutes_approved",
        help_text="Person who approved the minutes"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Who prepared the minutes
    prepared_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="minutes_prepared",
        help_text="Person who prepared the minutes (usually secretary)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Meeting Minutes"
        verbose_name_plural = "Meeting Minutes"
    
    def __str__(self):
        return f"Minutes: {self.meeting.title}"
    
    def approve(self, user):
        """Approve the minutes"""
        from django.utils import timezone
        self.is_approved = True
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()


class MeetingAgendaItem(models.Model):
    """
    Individual agenda items for a meeting with time allocation.
    """
    item_id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        unique=True,
    )
    
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="agenda_items"
    )
    
    order = models.PositiveIntegerField(
        default=1,
        help_text="Order of this item in the agenda"
    )
    title = models.CharField(
        max_length=255,
        help_text="Title of the agenda item"
    )
    description = models.TextField(
        blank=True,
        help_text="Details about this agenda item"
    )
    duration_minutes = models.PositiveIntegerField(
        default=10,
        help_text="Allocated time in minutes"
    )
    presenter = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agenda_presentations",
        help_text="Person presenting/leading this item"
    )
    
    # Tracking
    is_discussed = models.BooleanField(
        default=False,
        help_text="Was this item discussed in the meeting?"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes/outcomes from discussing this item"
    )
    
    class Meta:
        verbose_name = "Meeting Agenda Item"
        verbose_name_plural = "Meeting Agenda Items"
        ordering = ['meeting', 'order']
        unique_together = ['meeting', 'order']
    
    def __str__(self):
        return f"{self.order}. {self.title}"


class AttendanceReport(models.Model):
    """
    Aggregate attendance statistics for a user over a period.
    Used for generating attendance reports and tracking patterns.
    """
    report_id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        unique=True,
    )
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="attendance_reports"
    )
    
    # Report period
    period_start = models.DateField()
    period_end = models.DateField()
    office_year = models.CharField(
        max_length=20,
        help_text="Academic year for this report"
    )
    
    # Statistics
    total_meetings = models.PositiveIntegerField(default=0)
    meetings_attended = models.PositiveIntegerField(default=0)
    meetings_absent = models.PositiveIntegerField(default=0)
    meetings_excused = models.PositiveIntegerField(default=0)
    meetings_late = models.PositiveIntegerField(default=0)
    
    attendance_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Attendance rate as percentage"
    )
    
    # Generated info
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reports_generated"
    )
    
    class Meta:
        verbose_name = "Attendance Report"
        verbose_name_plural = "Attendance Reports"
        ordering = ['-period_end', 'user__first_name']
    
    def __str__(self):
        return f"Attendance Report: {self.user.first_name} {self.user.last_name} ({self.period_start} - {self.period_end})"
    
    @classmethod
    def generate_for_user(cls, user, period_start, period_end, office_year, generated_by=None):
        """Generate attendance report for a user"""
        attendances = MeetingAttendance.objects.filter(
            user=user,
            meeting__scheduled_date__gte=period_start,
            meeting__scheduled_date__lte=period_end,
            meeting__office_year=office_year,
            meeting__status='completed'
        )
        
        total = attendances.count()
        attended = attendances.filter(status__in=['present', 'late']).count()
        absent = attendances.filter(status='absent').count()
        excused = attendances.filter(status='excused').count()
        late = attendances.filter(status='late').count()
        
        rate = (attended / total * 100) if total > 0 else 0
        
        report, _ = cls.objects.update_or_create(
            user=user,
            period_start=period_start,
            period_end=period_end,
            office_year=office_year,
            defaults={
                'total_meetings': total,
                'meetings_attended': attended,
                'meetings_absent': absent,
                'meetings_excused': excused,
                'meetings_late': late,
                'attendance_rate': round(rate, 2),
                'generated_by': generated_by,
            }
        )
        return report
