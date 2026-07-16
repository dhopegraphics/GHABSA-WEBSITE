from django.contrib import admin
from django import forms
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
import datetime
from django.core.exceptions import ValidationError as DjangoValidationError, ObjectDoesNotExist
from executives.models import (
    Executive, ExecutivePosition, ExecutiveSocialLinks,
    Committee, Appointee, AppointeeSocialLinks, AppointeeContactDetails,
    AppointeePermission, PermissionAuditLog,
    # Meeting models
    Meeting, MeetingAttendance, MeetingMinutes, MeetingAgendaItem, AttendanceReport,
)
from utils.media_mixins import make_media_admin_mixin

# Create media admin mixins for models with file fields
ExecutiveMediaAdminMixin = make_media_admin_mixin(['image'])
AppointeeMediaAdminMixin = make_media_admin_mixin(['image'])
MeetingMinutesMediaAdminMixin = make_media_admin_mixin(['minutes_file'])

# Register your models here.


@admin.register(ExecutivePosition)
class ExecutivePositionAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at", "last_updated"]

@admin.register(ExecutiveSocialLinks)
class ExecutiveSocialLinksAdmin(admin.ModelAdmin):
    list_display = ["executive", "platform"]


@admin.register(Executive)
class ExecutiveAdmin(ExecutiveMediaAdminMixin, admin.ModelAdmin):
    class ExecutiveAdminForm(forms.ModelForm):
        user_is_staff = forms.BooleanField(required=False, label="Grant staff status to user")

        class Meta:
            model = Executive
            fields = "__all__"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            now = timezone.now()
            # Default new executives to grant staff status
            if self.instance and getattr(self.instance, 'user', None):
                # existing instance -> reflect actual user's is_staff
                self.fields['user_is_staff'].initial = getattr(self.instance.user, 'is_staff', False)
            else:
                # new instance defaults
                self.fields['user_is_staff'].initial = True

            # Determine base year for academic selection correctly around Sept 15.
            # Rule: The academic/office year runs from Sept 15 of year N to Sept 15 of year N+1.
            # If today is on or after Sept 15 of the current year, the default office year
            # should be "current_year/current_year+1". Otherwise it should be
            # "current_year-1/current_year".
            try:
                tz = timezone.get_current_timezone()
                current_year = now.year
                sept15_current = datetime.datetime(current_year, 9, 15, 0, 0, tzinfo=tz)
                if now >= sept15_current:
                    base_year = current_year
                else:
                    base_year = current_year - 1

                # Default office_year (e.g., "2025/2026") and provide a dropdown range
                default_office_year = f"{base_year}/{base_year + 1}"
                years = [y for y in range(base_year - 2, base_year + 6)]
                choices = [(f"{y}/{y+1}", f"{y}/{y+1}") for y in years]
                if 'office_year' in self.fields:
                    # provide select widget choices and set initial
                    self.fields['office_year'].widget = forms.Select(choices=choices)
                    self.fields['office_year'].initial = default_office_year

                # Default office_from and office_to to Sept 15 of base year -> next year
                sept15_from = datetime.datetime(base_year, 9, 15, 9, 0, tzinfo=tz)
                sept15_to = datetime.datetime(base_year + 1, 9, 15, 17, 0, tzinfo=tz)
                if 'office_from' in self.fields:
                    self.fields['office_from'].initial = sept15_from
                if 'office_to' in self.fields:
                    self.fields['office_to'].initial = sept15_to
            except Exception:
                # if anything fails, don't block admin; keep defaults blank
                pass

    form = ExecutiveAdminForm
    def official_name(self, obj):
        name = f"{obj.user.first_name} {obj.user.last_name}"
        t = getattr(obj, 'title', None)
        if t:
            if t in ('Dr', 'Prof'):
                return f"{t} {name}"
            return f"{t}. {name}"
        return name

    list_display = ["official_name", "position", "office_year", "is_active", "office_from", "office_to"]
    list_filter = ["is_active", "office_year", "position"]
    search_fields = ["user__first_name", "user__last_name", "office_year"]
    fieldsets = (
        ("Basic Information", {
            "fields": ("user", "position", "title")
        }),
        ("Image (Choose one option)", {
            "fields": ("image", "image_url"),
            "description": "Upload an image OR provide a URL (Google Drive, Dropbox, etc.). URL takes priority if both are provided."
        }),
        ("Portfolio & Biography", {
            "fields": ("bio", "skills", "achievements"),
            "description": "Skills and achievements should be entered as JSON arrays. Example: [\"Python\", \"Leadership\", \"Public Speaking\"]"
        }),
        ("Office Period", {
            "fields": ("office_from", "office_to", "office_year")
        }),
        ("Status", {
            "fields": ("is_active", 'user_is_staff')
        }),
    )

    def save_model(self, request, obj, form, change):
        # Update linked user's is_staff based on admin checkbox, but only if the field was editable
        if 'user_is_staff' in form.cleaned_data:
            user_is_staff = form.cleaned_data['user_is_staff']
            if obj.user:
                obj.user.is_staff = user_is_staff
                obj.user.save()
        super().save_model(request, obj, form, change)


# Committee Admin
@admin.register(Committee)
class CommitteeAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "description"]
    fieldsets = (
        (None, {
            "fields": ("name", "description", "is_active")
        }),
    )


# Appointee Admin with inline for contact details
class AppointeeContactDetailsInline(admin.StackedInline):
    model = AppointeeContactDetails
    extra = 0
    
    def get_parent_appointee(self, request):
        """Extract parent appointee from the URL"""
        try:
            # Get appointee_id from URL path
            path = request.path
            # URL format: /executive-dashboard-cb/executives/appointee/{appointee_id}/change/
            if '/appointee/' in path and '/change/' in path:
                appointee_id = path.split('/appointee/')[1].split('/')[0]
                return Appointee.objects.get(appointee_id=appointee_id)
        except Exception:
            pass
        return None
    
    def has_change_permission(self, request, obj=None):
        """Only allow editing contact details for own profile - NOT for others"""
        if request.user.is_superuser or Executive.objects.filter(user=request.user).exists():
            return True
        
        # Get the parent appointee object from URL
        parent_appointee = self.get_parent_appointee(request)
        if not parent_appointee:
            return False  # If we can't determine parent, deny access
        
        # Users can ONLY edit their own contact details
        if parent_appointee.user == request.user:
            return True
        
        # Heads/Deputies CANNOT edit other people's contact details
        return False
    
    def has_add_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)


class AppointeeSocialLinksInline(admin.TabularInline):
    model = AppointeeSocialLinks
    extra = 1
    
    def get_parent_appointee(self, request):
        """Extract parent appointee from the URL"""
        try:
            # Get appointee_id from URL path
            path = request.path
            # URL format: /executive-dashboard-cb/executives/appointee/{appointee_id}/change/
            if '/appointee/' in path and '/change/' in path:
                appointee_id = path.split('/appointee/')[1].split('/')[0]
                return Appointee.objects.get(appointee_id=appointee_id)
        except Exception:
            pass
        return None
    
    def has_change_permission(self, request, obj=None):
        """Only allow editing social links for own profile - NOT for others"""
        if request.user.is_superuser or Executive.objects.filter(user=request.user).exists():
            return True
        
        # Get the parent appointee object from URL
        parent_appointee = self.get_parent_appointee(request)
        if not parent_appointee:
            return False  # If we can't determine parent, deny access
        
        # Users can ONLY edit their own social links
        if parent_appointee.user == request.user:
            return True
        
        # Heads/Deputies CANNOT edit other people's social links
        return False
    
    def has_add_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)


class AppointeePermissionInline(admin.StackedInline):
    model = AppointeePermission
    extra = 0
    fields = ["permissions", "granted_by", "granted_at", "is_active", "expires_at", "notes"]
    readonly_fields = ["granted_at", "granted_by"]
    can_delete = True
    filter_horizontal = ['permissions']
    classes = ['collapse']
    verbose_name = "Permission Grant"
    verbose_name_plural = "Permission Grants"
    
    def get_queryset(self, request):
        """
        Filter to show only permission grants created by the logged-in user.
        Heads/Deputies see only members they granted permissions to.
        """
        qs = super().get_queryset(request)
        
        # Superusers and Executives see all
        if request.user.is_superuser or Executive.objects.filter(user=request.user).exists():
            return qs
        
        # Heads/Deputies see only what they granted
        if Appointee.objects.filter(user=request.user, role__in=['head', 'deputy_head'], is_active=True).exists():
            return qs.filter(granted_by=request.user)
        
        # Regular appointees see nothing (they shouldn't be here anyway)
        return qs.none()
    
    def has_add_permission(self, request, obj=None):
        """
        Only heads/deputies can add permission grants, and only for appointees in their committee.
        """
        # Superusers and Executives always can
        if request.user.is_superuser or Executive.objects.filter(user=request.user).exists():
            return True
        
        # Check if user is head/deputy
        return Appointee.objects.filter(
            user=request.user,
            role__in=['head', 'deputy_head'],
            is_active=True
        ).exists()
    
    def has_change_permission(self, request, obj=None):
        """
        Can only change permission grants they created.
        """
        if request.user.is_superuser or Executive.objects.filter(user=request.user).exists():
            return True
        
        # obj here is the inline object (AppointeePermission), not the parent (Appointee)
        # Only allow change if they created this permission grant
        if obj and isinstance(obj, AppointeePermission) and obj.granted_by == request.user:
            return True
        
        # If obj is None or Appointee (parent), check if user is head/deputy
        if Appointee.objects.filter(user=request.user, role__in=['head', 'deputy_head'], is_active=True).exists():
            return True
        
        return False
    
    def has_delete_permission(self, request, obj=None):
        """
        Can only delete permission grants they created.
        """
        if request.user.is_superuser or Executive.objects.filter(user=request.user).exists():
            return True
        
        # obj here can be either the parent Appointee or the inline AppointeePermission
        # Only allow delete if it's an AppointeePermission they created
        if obj and isinstance(obj, AppointeePermission) and obj.granted_by == request.user:
            return True
        
        # If obj is None or Appointee (parent), check if user is head/deputy
        if Appointee.objects.filter(user=request.user, role__in=['head', 'deputy_head'], is_active=True).exists():
            return True
        
        return False


@admin.register(Appointee)
class AppointeeAdmin(AppointeeMediaAdminMixin, admin.ModelAdmin):
    class AppointeeAdminForm(forms.ModelForm):
        # Default initial True for add form; existing instances will be set to actual user.is_staff
        user_is_staff = forms.BooleanField(required=False, label="Grant staff status to user", initial=True)

        class Meta:
            model = Appointee
            fields = "__all__"

        def __init__(self, *args, **kwargs):
            self.request = kwargs.pop('request', None)
            super().__init__(*args, **kwargs)
            # Default: when creating a new Appointee, pre-fill appointment period and office year,
            # and default the 'Grant staff status' checkbox to True.
            now = timezone.now()
            next_year = now.year + 1
            next_academic = f"{now.year}/{next_year}"

            if self.instance and self.instance.pk:
                # existing instance -> reflect actual user's is_staff
                if 'user_is_staff' in self.fields:
                    try:
                        user = self.instance.user
                        self.fields['user_is_staff'].initial = user.is_staff
                    except ObjectDoesNotExist:
                        self.fields['user_is_staff'].initial = False
            else:
                # new instance -> sensible defaults for ALL users (superusers/executives/heads/deputies)
                if 'user_is_staff' in self.fields:
                    self.fields['user_is_staff'].initial = True
                
                # CRITICAL: Set initial values for date fields (these will show in the form)
                # appointed_from default to now
                if 'appointed_from' in self.fields:
                    self.fields['appointed_from'].initial = now
                
                # appointed_to default to 15 September of next year
                sept15 = datetime.datetime(next_year, 9, 15, 0, 0, tzinfo=timezone.get_current_timezone())
                if 'appointed_to' in self.fields:
                    self.fields['appointed_to'].initial = sept15
                
                # office_year default to next academic year
                if 'office_year' in self.fields:
                    self.fields['office_year'].initial = next_academic
                
                # IMPORTANT: For heads/deputies, these fields will be readonly but still show defaults
                # For superusers/executives, these fields will be editable with defaults

            # Auto-fill committee and role for heads/deputies adding new appointees
            if self.request and not self.instance.pk:
                # Check if user is head/deputy
                head_or_deputy_appointee = Appointee.objects.filter(
                    user=self.request.user,
                    role__in=['head', 'deputy_head'],
                    is_active=True
                ).first()
                
                if head_or_deputy_appointee:
                    # Auto-fill committee from head/deputy's committee
                    if 'committee' in self.fields:
                        self.fields['committee'].initial = head_or_deputy_appointee.committee
                        self.fields['committee'].widget.attrs['readonly'] = True
                        self.fields['committee'].disabled = True
                        self.fields['committee'].help_text = f"Auto-filled: You can only add members to your committee ({head_or_deputy_appointee.committee.name})"
                    
                    # Auto-fill role as 'member' (heads/deputies can only create members, not other heads)
                    if 'role' in self.fields:
                        self.fields['role'].initial = 'member'
                        self.fields['role'].widget.attrs['readonly'] = True
                        self.fields['role'].disabled = True
                        self.fields['role'].help_text = "Auto-filled: You can only create regular members (not heads or deputies)"
            
            # Note: Readonly fields are now handled in get_readonly_fields method
            # This allows proper permission checking and cleaner logic

    form = AppointeeAdminForm
    
    def has_full_power(self, request):
        """Check if user has full administrative power over appointees"""
        return request.user.is_superuser or Executive.objects.filter(user=request.user).exists()
    
    def get_form(self, request, obj=None, **kwargs):
        # Pass request to the form
        form_class = super().get_form(request, obj, **kwargs)
        # Ensure the form class includes our extra 'user_is_staff' field and default it to True on add
        try:
            base = getattr(form_class, 'base_fields', {})
            if 'user_is_staff' not in base:
                # add a boolean field to the generated form class so admin includes it
                from django import forms as _forms
                form_class.base_fields['user_is_staff'] = _forms.BooleanField(required=False, label="Grant staff status to user", initial=True)
            else:
                if obj is None:
                    form_class.base_fields['user_is_staff'].initial = True
        except Exception:
            pass

        class FormWithRequest(form_class):
            def __init__(self, *args, **kwargs):
                kwargs['request'] = request
                super().__init__(*args, **kwargs)
                # If this is an unbound add form and the field exists, ensure the checkbox shows checked
                try:
                    if not getattr(self.instance, 'pk', None) and 'user_is_staff' in self.fields:
                        self.fields['user_is_staff'].initial = True
                except Exception:
                    pass

        return FormWithRequest
    
    def get_exclude(self, request, obj=None):
        """
        Exclude user_is_staff field from form when user shouldn't be able to edit it.
        
        Who CAN see and edit user_is_staff:
        1. Superusers and Executives (full power)
        2. Users with change_appointee permission (can edit anyone)
        3. Heads/Deputies editing members they created (but NOT their own record)
        
        Who CANNOT see user_is_staff:
        1. Users editing their own record (even heads/deputies)
        2. Regular appointees with only edit_own_* permissions
        3. Heads/Deputies editing members they didn't create
        """
        exclude = super().get_exclude(request, obj) or []
        exclude = list(exclude)  # Make it mutable
        
        # Tier 1: Superusers and Executives can always see and edit user_is_staff
        if self.has_full_power(request):
            return exclude
        
        # Tier 2: Users with change_appointee permission can see user_is_staff for everyone
        if request.user.has_perm('executives.change_appointee'):
            return exclude
        
        # For ADD form - heads/deputies can set staff status for new members
        if obj is None:
            is_head_or_deputy = Appointee.objects.filter(
                user=request.user,
                role__in=['head', 'deputy_head'],
                is_active=True
            ).exists()
            if is_head_or_deputy:
                return exclude  # Allow heads/deputies to see user_is_staff in add form
            else:
                # Regular users can't add members anyway, so hide it
                if 'user_is_staff' not in exclude:
                    exclude.append('user_is_staff')
                return exclude
        
        # For EDIT form
        # CRITICAL: Check if editing their own record (NOBODY can change their own staff status)
        if obj.user == request.user:
            # Cannot change own staff status - hide the field
            if 'user_is_staff' not in exclude:
                exclude.append('user_is_staff')
            return exclude
        
        # Tier 3: Check if head/deputy editing a member they created
        is_head_or_deputy = Appointee.objects.filter(
            user=request.user,
            role__in=['head', 'deputy_head'],
            is_active=True
        ).exists()
        
        if is_head_or_deputy:
            from executives.models import AppointeePermission
            created_by_them = AppointeePermission.objects.filter(
                appointee=obj,
                granted_by=request.user
            ).exists()
            
            if created_by_them:
                # Can edit user_is_staff for members they created (but not themselves)
                return exclude
        
        # Everyone else can't see user_is_staff
        if 'user_is_staff' not in exclude:
            exclude.append('user_is_staff')
        return exclude
    
    def get_readonly_fields(self, request, obj=None):
        """
        Make certain fields readonly based on user permissions.
        - Superusers/Executives: Can edit everything
        - change_appointee permission: Can edit all fields on any appointee
        - edit_own_* permissions: Can edit specific fields on own record only
        - Heads/Deputies adding new members: Can edit user, image, portfolio, contact details (NOT admin fields)
        - Heads/Deputies editing existing: Can edit profile fields only of members they created
        """
        readonly_fields = []
        
        # Superusers and Executives have full power
        if self.has_full_power(request):
            return readonly_fields
        
        # Users with change_appointee permission can edit everything
        if request.user.has_perm('executives.change_appointee'):
            return readonly_fields
        
        # Check if user is a head/deputy
        is_head_or_deputy = Appointee.objects.filter(
            user=request.user,
            role__in=['head', 'deputy_head'],
            is_active=True
        ).exists()
        
        if obj is None:
            # ADD FORM: Head/Deputy can create new appointees
            if is_head_or_deputy:
                # Allow editing: user, image, portfolio, bio, skills, achievements
                # Make readonly: admin fields, committee, and role (auto-filled)
                readonly_fields.extend([
                    'committee',  # Auto-filled with head/deputy's committee
                    'role',       # Auto-filled as 'member'
                    'is_active', 
                    'appointed_from', 
                    'appointed_to', 
                    'office_year'
                ])
            else:
                # Regular appointees cannot add others
                readonly_fields.extend([
                    'user', 'committee', 'role', 'is_active', 
                    'appointed_from', 'appointed_to', 'office_year',
                    'bio', 'portfolio', 'skills', 'achievements', 
                    'image', 'image_url'
                ])
        else:
            # EDIT FORM: Check permissions
            if request.user == obj.user:
                # Editing own record - always readonly for admin fields
                # CRITICAL: Make user_is_staff readonly AND excluded to prevent changes
                readonly_fields.extend([
                    'user', 'committee', 'role', 'is_active',
                    'appointed_from', 'appointed_to', 'office_year',
                    'user_is_staff'  # CRITICAL: Prevent editing own staff status
                ])
                
                # Check granular edit_own_* permissions for profile fields
                # Define field-to-permission mapping
                field_permission_map = {
                    'bio': 'executives.edit_own_bio',
                    'image': 'executives.edit_own_image',
                    'image_url': 'executives.edit_own_image',
                    'portfolio': 'executives.edit_own_portfolio',
                    'skills': 'executives.edit_own_portfolio',
                    'achievements': 'executives.edit_own_concepts',
                }
                
                # Make fields readonly if user lacks the specific permission
                for field, permission in field_permission_map.items():
                    if not request.user.has_perm(permission):
                        readonly_fields.append(field)
                
            elif is_head_or_deputy:
                # Heads/Deputies can edit members they created in their committee
                # Check if this appointee was created by them (has permission grant from them)
                from executives.models import AppointeePermission
                created_by_them = AppointeePermission.objects.filter(
                    appointee=obj,
                    granted_by=request.user
                ).exists()
                
                if created_by_them and obj.user != request.user:
                    # Can edit profile fields AND user_is_staff for members they created (but not themselves)
                    readonly_fields.extend([
                        'user', 'committee', 'role', 'is_active',
                        'appointed_from', 'appointed_to', 'office_year'
                    ])
                    # user_is_staff is NOT in readonly, so they can edit it
                elif obj.user == request.user:
                    # Editing their own record - cannot change admin fields
                    # CRITICAL: Make user_is_staff readonly AND excluded to prevent changes
                    readonly_fields.extend([
                        'user', 'committee', 'role', 'is_active',
                        'appointed_from', 'appointed_to', 'office_year',
                        'user_is_staff'  # CRITICAL: Prevent editing own staff status
                    ])
                else:
                    # Cannot edit appointees they didn't create
                    readonly_fields.extend([
                        'user', 'committee', 'role', 'is_active',
                        'appointed_from', 'appointed_to', 'office_year',
                        'bio', 'portfolio', 'skills', 'achievements',
                        'image', 'image_url'
                    ])
            else:
                # Regular appointees can't edit others
                readonly_fields.extend([
                    'user', 'committee', 'role', 'is_active',
                    'appointed_from', 'appointed_to', 'office_year',
                    'bio', 'portfolio', 'skills', 'achievements',
                    'image', 'image_url'
                ])
        
        return readonly_fields

    def get_changeform_initial_data(self, request):
        """Provide default initial data for the add form in the admin."""
        initial = super().get_changeform_initial_data(request) or {}
        
        # Default new appointees to have staff status checked in the add form
        initial.setdefault('user_is_staff', True)
        
        # CRITICAL: Set default values for appointment period and office year
        # This ensures all users (superusers, executives, heads, deputies) see these defaults
        now = timezone.now()
        next_year = now.year + 1
        next_academic = f"{now.year}/{next_year}"
        sept15 = datetime.datetime(next_year, 9, 15, 0, 0, tzinfo=timezone.get_current_timezone())
        
        initial.setdefault('appointed_from', now)
        initial.setdefault('appointed_to', sept15)
        initial.setdefault('office_year', next_academic)
        
        return initial
    
    def get_object(self, request, object_id, from_field=None):
        """
        Override to dynamically add user_is_staff attribute to the instance.
        This allows Django admin to display the current value without "None".
        """
        obj = super().get_object(request, object_id, from_field)
        if obj and hasattr(obj, 'user') and obj.user:
            # Dynamically add user_is_staff as an instance attribute
            # This allows Django's lookup_field to find it and display the current value
            obj.user_is_staff = obj.user.is_staff
        return obj
    
    def get_form(self, request, obj=None, change=False, **kwargs):
        """
        Override get_form to properly set initial data for user_is_staff field.
        This ensures the checkbox shows the current user.is_staff value.
        """
        form = super().get_form(request, obj, change=change, **kwargs)
        
        # For existing objects, set the initial value for user_is_staff
        if obj and obj.pk and hasattr(obj, 'user') and obj.user:
            # We need to set this on the form class's base_fields
            if 'user_is_staff' in form.base_fields:
                # Store the actual value to use as initial
                form._user_is_staff_initial = obj.user.is_staff
        
        return form
    
    def user_staff_status(self, obj):
        """Display user's staff status as readonly field (used when user_is_staff should be readonly)"""
        if obj and obj.user:
            return obj.user.is_staff
        return False
    user_staff_status.short_description = "User is staff"
    user_staff_status.boolean = True  # Display as boolean icon
    
    def grant_staff_status(self, request, queryset):
        """Admin action to grant staff status to selected appointees"""
        count = 0
        skipped = 0
        for appointee in queryset:
            # Skip if trying to grant to self
            if appointee.user == request.user:
                skipped += 1
                continue
            
            # Skip if trying to grant to head or deputy
            if appointee.role in ['head', 'deputy']:
                skipped += 1
                continue
            
            if appointee.user:
                appointee.user.is_staff = True
                appointee.user.save()
                count += 1
        
        if count > 0:
            self.message_user(request, f"Successfully granted staff status to {count} member(s).")
        if skipped > 0:
            self.message_user(
                request, 
                f"Skipped {skipped} appointee(s): Cannot grant staff status to yourself, heads, or deputies.",
                level='warning'
            )
    grant_staff_status.short_description = "Grant staff status to selected members"
    
    def revoke_staff_status(self, request, queryset):
        """Admin action to revoke staff status from selected appointees"""
        count = 0
        skipped = 0
        for appointee in queryset:
            # Skip if trying to revoke from self
            if appointee.user == request.user:
                skipped += 1
                continue
            
            # Skip if trying to revoke from head or deputy
            if appointee.role in ['head', 'deputy']:
                skipped += 1
                continue
            
            if appointee.user:
                appointee.user.is_staff = False
                appointee.user.save()
                count += 1
        
        if count > 0:
            self.message_user(request, f"Successfully revoked staff status from {count} member(s).")
        if skipped > 0:
            self.message_user(
                request, 
                f"Skipped {skipped} appointee(s): Cannot revoke staff status from yourself, heads, or deputies.",
                level='warning'
            )
    revoke_staff_status.short_description = "Revoke staff status from selected members"
    
    actions = ['grant_staff_status', 'revoke_staff_status']
    
    def appointee_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    list_display = ["appointee_name", "committee", "role", "user_staff_status", "office_year", "is_active"]
    list_filter = ["is_active", "role", "committee", "office_year"]
    search_fields = ["user__first_name", "user__last_name", "committee__name"]
    inlines = [AppointeeContactDetailsInline, AppointeeSocialLinksInline, AppointeePermissionInline]
    # Allow selecting the user by name in the admin add/change form
    autocomplete_fields = ["user", "committee"]
    fieldsets = (
        ("Basic Information", {
            "fields": ("user", "committee", "role", "portfolio")
        }),
        ("Image (Choose one option)", {
            "fields": ("image", "image_url"),
        }),
        ("Portfolio & Biography", {
            "fields": ("bio", "skills", "achievements"),
            "description": "Skills and achievements should be entered as JSON arrays. Example: [\"Python\", \"Leadership\", \"Public Speaking\"]"
        }),
        ("Appointment Period", {
            "fields": ("appointed_from", "appointed_to", "office_year")
        }),
        ("Status", {
            "fields": ("is_active", 'user_is_staff')
        }),
    )

    def get_fieldsets(self, request, obj=None):
        """
        Dynamically modify fieldsets to handle user_is_staff field properly.
        - If excluded: Remove it completely from fieldsets
        - If not excluded: Keep it (form field will be rendered)
        """
        fieldsets = super().get_fieldsets(request, obj)
        
        # Get the exclude list to see if user_is_staff should be hidden
        exclude = self.get_exclude(request, obj) or []
        
        # If user_is_staff is in exclude list, remove it from fieldsets
        if 'user_is_staff' in exclude:
            # Create a mutable copy of fieldsets
            fieldsets = list(fieldsets)
            new_fieldsets = []
            
            for name, options in fieldsets:
                # Make a mutable copy of options dict
                options = dict(options)
                fields = options.get('fields', ())
                
                # If this fieldset contains user_is_staff, remove it
                if 'user_is_staff' in fields:
                    fields = tuple(f for f in fields if f != 'user_is_staff')
                    options['fields'] = fields
                
                new_fieldsets.append((name, options))
            
            return tuple(new_fieldsets)
        
        return fieldsets

    def get_search_results(self, request, queryset, search_term):
        """Override autocomplete search to exclude appointees that already have
        AppointeePermission when the autocomplete is being used from the
        AppointeePermission add view. This uses a heuristic on HTTP_REFERER
        to detect that context.
        """
        # First run the default search
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        try:
            referer = (request.META.get('HTTP_REFERER') or '').lower()
            if 'appointeepermission' in referer and '/add' in referer:
                from executives.models import AppointeePermission
                excluded_ids = AppointeePermission.objects.values_list('appointee_id', flat=True)
                queryset = queryset.exclude(pk__in=excluded_ids)
        except Exception:
            pass

        return queryset, use_distinct

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # Superusers and Executives see all
        if self.has_full_power(request):
            return qs
        
        # Check if user is a head/deputy
        user_appointee = Appointee.objects.filter(
            user=request.user,
            role__in=['head', 'deputy_head'],
            is_active=True
        ).first()
        
        if user_appointee:
            # Heads/Deputies see all members in their committee
            # This includes themselves and all members they've added
            return qs.filter(committee=user_appointee.committee)
        
        # Regular appointees see only their own record
        if Appointee.objects.filter(user=request.user).exists():
            return qs.filter(user=request.user)
        
        return qs
    
    def has_add_permission(self, request):
        """
        Allow adding appointees if user has either:
        - add_appointee permission (full access)
        - add_committee_members permission (heads/deputies)
        """
        # Superusers and Executives have full power
        if self.has_full_power(request):
            return True
        
        # Check for explicit permissions
        has_add_appointee = request.user.has_perm('executives.add_appointee')
        has_add_committee_members = request.user.has_perm('executives.add_committee_members')
        
        if has_add_appointee:
            return True
        
        # Check if user is a head/deputy with add_committee_members permission
        if has_add_committee_members:
            user_appointee = Appointee.objects.filter(
                user=request.user,
                role__in=['head', 'deputy_head'],
                is_active=True
            ).first()
            
            if user_appointee:
                return True
        
        return False
    
    def has_change_permission(self, request, obj=None):
        """
        Allow changing appointees if user has either:
        - change_appointee permission (full access to edit anyone)
        - edit_own_* permissions (self-service - edit own record only)
        
        This follows the same permission-based logic as the API views.
        """
        # Superusers and Executives have full power
        if self.has_full_power(request):
            return True
        
        # Check for change_appointee permission (full access)
        if request.user.has_perm('executives.change_appointee'):
            return True
        
        # If viewing/editing a specific appointee (obj is provided)
        if obj:
            # Check if editing own record
            if obj.user == request.user:
                # Check if they have ANY edit_own_* permission
                edit_own_perms = [
                    'executives.edit_own_bio',
                    'executives.edit_own_image',
                    'executives.edit_own_portfolio',
                    'executives.edit_own_concepts',
                    'executives.edit_own_social_links',
                    'executives.edit_own_contact_details'
                ]
                
                # If they have at least one edit_own_* permission, allow access
                if any(request.user.has_perm(perm) for perm in edit_own_perms):
                    return True
        else:
            # No specific object - general change permission check
            # If they have ANY edit_own_* permission, they can at least access their own record
            edit_own_perms = [
                'executives.edit_own_bio',
                'executives.edit_own_image',
                'executives.edit_own_portfolio',
                'executives.edit_own_concepts',
                'executives.edit_own_social_links',
                'executives.edit_own_contact_details'
            ]
            
            if any(request.user.has_perm(perm) for perm in edit_own_perms):
                return True
        
        return False
    
    def has_delete_permission(self, request, obj=None):
        """
        Allow deletion based on permissions.
        - Superusers/Executives can delete anyone
        - Heads/Deputies can delete members they added (tracked via AppointeePermission OR same committee)
        - Cannot delete yourself
        - Cannot delete other heads/deputies
        
        HYBRID APPROACH:
        1. First check if AppointeePermission.granted_by exists (accurate tracking)
        2. Fall back to committee membership for legacy/existing members
        """
        # Superusers and Executives can delete anyone
        if self.has_full_power(request):
            return True
        
        if obj is None:
            # General permission check - allow heads/deputies
            return Appointee.objects.filter(
                user=request.user,
                role__in=['head', 'deputy_head'],
                is_active=True
            ).exists()
        
        # Cannot delete yourself
        if obj.user == request.user:
            return False
        
        # Cannot delete heads or deputy heads (only members)
        if obj.role in ['head', 'deputy_head']:
            return False
        
        # Check if user is head/deputy
        user_appointee = Appointee.objects.filter(
            user=request.user,
            role__in=['head', 'deputy_head'],
            is_active=True
        ).first()
        
        if user_appointee:
            # HYBRID APPROACH:
            # 1. Check if they created this member (via AppointeePermission) - most accurate
            from executives.models import AppointeePermission
            created_by_them = AppointeePermission.objects.filter(
                appointee=obj,
                granted_by=request.user
            ).exists()
            
            # 2. Fall back to committee membership (for existing members without tracking)
            in_same_committee = (obj.committee == user_appointee.committee)
            
            # Can delete if:
            # - They created them (tracked via AppointeePermission), OR
            # - Member is in same committee (legacy/existing members)
            if created_by_them or (in_same_committee and obj.role == 'member'):
                return True
        
        return False
    
    def has_delete_permission_for_related(self, request, obj, related_model):
        """
        Check if user has permission to delete related objects when deleting an appointee.
        This is needed because Django checks permissions for cascade deletes.
        """
        # Import related models
        from executives.models import AppointeeContactDetails, AppointeeSocialLinks, AppointeePermission
        
        # If they can delete the main appointee, they can delete its related objects
        if self.has_delete_permission(request, obj):
            # Only allow deleting these specific related models
            if related_model in [AppointeeContactDetails, AppointeeSocialLinks, AppointeePermission]:
                return True
        
        return False
    
    def get_deleted_objects(self, objs, request):
        """
        Override to allow heads/deputies to delete related objects when deleting appointees they created.
        HYBRID APPROACH: Check both AppointeePermission.granted_by AND committee membership.
        """
        from django.contrib.admin.utils import get_deleted_objects as django_get_deleted_objects
        from django.contrib.admin import site
        
        # For heads/deputies, we need to bypass the permission check for related objects
        if not self.has_full_power(request):
            # Check if user is head/deputy
            user_appointee = Appointee.objects.filter(
                user=request.user,
                role__in=['head', 'deputy_head'],
                is_active=True
            ).first()
            
            if user_appointee:
                # First, filter objs to only include appointees they can delete
                from executives.models import AppointeePermission
                
                allowed_objs = []
                for obj in objs:
                    # Check if they can delete this specific appointee
                    if obj.user != request.user and obj.role == 'member':
                        # HYBRID APPROACH:
                        # 1. Check if they created this member (most accurate)
                        created_by_them = AppointeePermission.objects.filter(
                            appointee=obj,
                            granted_by=request.user
                        ).exists()
                        
                        # 2. Fall back to committee membership (legacy members)
                        in_same_committee = (obj.committee == user_appointee.committee)
                        
                        # Allow deletion if either condition is met
                        if created_by_them or in_same_committee:
                            allowed_objs.append(obj)
                
                # If no objects are allowed, return empty with permission error
                if not allowed_objs:
                    from django.contrib.admin.utils import NestedObjects
                    collector = NestedObjects(using='default')
                    collector.collect(objs)
                    perms_needed = {'executives.delete_appointee'}
                    return [], {}, perms_needed, []
                
                # Get deleted objects only for allowed appointees
                deleted_objects, model_count, perms_needed, protected = django_get_deleted_objects(
                    allowed_objs, request, site
                )
                
                # For heads/deputies, clear ALL permission requirements since we've already
                # validated they can delete these specific appointees through has_delete_permission
                # and the allowed_objs filtering above
                filtered_perms = set()  # Empty set = no permissions needed
                
                return deleted_objects, model_count, filtered_perms, protected
        
        # For superusers/executives, use default behavior
        return super().get_deleted_objects(objs, request)
    
    def delete_queryset(self, request, queryset):
        """
        Handle bulk deletion for heads/deputies.
        This method is called when deleting multiple objects via the admin action.
        HYBRID APPROACH: Check both AppointeePermission.granted_by AND committee membership.
        """
        if not self.has_full_power(request):
            # Check if user is head/deputy
            user_appointee = Appointee.objects.filter(
                user=request.user,
                role__in=['head', 'deputy_head'],
                is_active=True
            ).first()
            
            if user_appointee:
                from executives.models import AppointeePermission
                
                # Filter to only delete appointees they can delete
                allowed_to_delete = []
                for obj in queryset:
                    if obj.user != request.user and obj.role == 'member':
                        # HYBRID APPROACH:
                        # 1. Check if they created this member (most accurate)
                        created_by_them = AppointeePermission.objects.filter(
                            appointee=obj,
                            granted_by=request.user
                        ).exists()
                        
                        # 2. Fall back to committee membership (legacy members)
                        in_same_committee = (obj.committee == user_appointee.committee)
                        
                        # Allow deletion if either condition is met
                        if created_by_them or in_same_committee:
                            allowed_to_delete.append(obj.pk)
                
                # Only delete the ones they're allowed to delete
                if allowed_to_delete:
                    queryset = queryset.filter(pk__in=allowed_to_delete)
                else:
                    # Don't delete anything if they don't have permission
                    return
        
        # Perform the deletion
        super().delete_queryset(request, queryset)

    def save_model(self, request, obj, form, change):
        # For new appointees, ensure defaults are set
        if not change:  # Only for new objects
            now = timezone.now()
            next_year = now.year + 1
            next_academic = f"{now.year}/{next_year}"
            sept15 = datetime.datetime(next_year, 9, 15, 0, 0, tzinfo=timezone.get_current_timezone())
            
            # Check if user is head/deputy
            head_or_deputy_appointee = Appointee.objects.filter(
                user=request.user,
                role__in=['head', 'deputy_head'],
                is_active=True
            ).first()
            
            if head_or_deputy_appointee:
                # Force committee to be the head/deputy's committee
                obj.committee = head_or_deputy_appointee.committee
                # Force role to be 'member' (heads/deputies cannot create other heads/deputies)
                obj.role = 'member'
            
            # CRITICAL: Set appointment period defaults for ALL new appointees
            # This ensures dates are set even when fields are readonly (heads/deputies)
            # or when superusers/executives leave them empty
            if not obj.appointed_from:
                obj.appointed_from = now
            if not obj.appointed_to:
                obj.appointed_to = sept15
            if not obj.office_year:
                obj.office_year = next_academic
        
        # Update linked user's is_staff based on admin checkbox, but only if the field was editable
        # CRITICAL: Also prevent users from changing their own staff status
        if 'user_is_staff' in form.cleaned_data and obj.user != request.user:
            user_is_staff = form.cleaned_data['user_is_staff']
            if obj.user:
                obj.user.is_staff = user_is_staff
                obj.user.save()
        # Run model validation to catch duplicate active appointees etc.
        try:
            obj.full_clean()
        except DjangoValidationError as e:
            # Convert to a form-level ValidationError so admin surfaces it
            raise forms.ValidationError(e.message_dict)

        super().save_model(request, obj, form, change)
        
        # IMPORTANT: After saving, handle AppointeePermission records
        if not change:  # Only for new objects
            from executives.models import AppointeePermission
            
            # For HEADS and DEPUTY HEADS: The signal creates AppointeePermission with granted_by=None
            # We need to update it to set granted_by to the current user (superuser/executive who created them)
            if obj.role in ['head', 'deputy_head']:
                # The post_save signal should have already created the AppointeePermission
                # Update the granted_by field to track who created this head/deputy
                perm = AppointeePermission.objects.filter(appointee=obj).first()
                if perm:
                    if perm.granted_by is None:
                        perm.granted_by = request.user
                        perm.notes = f'Auto-created when {request.user.get_full_name()} added this {obj.role}'
                        perm.save(update_fields=['granted_by', 'notes'])
            
            # For MEMBERS: Only heads/deputies can create members
            # Create an AppointeePermission to track that this head/deputy created this member
            else:  # obj.role == 'member'
                head_or_deputy_appointee = Appointee.objects.filter(
                    user=request.user,
                    role__in=['head', 'deputy_head'],
                    is_active=True
                ).first()
                
                if head_or_deputy_appointee:
                    # Note: appointee_id is UNIQUE, so we can only have one permission record per appointee
                    # Check if permission already exists (shouldn't for members, but check anyway)
                    if not AppointeePermission.objects.filter(appointee=obj).exists():
                        AppointeePermission.objects.create(
                            appointee=obj,
                            granted_by=request.user,
                            is_active=True,
                            notes=f'Auto-created when {request.user.get_full_name()} added this member'
                        )


# Permission Management Admin
@admin.register(AppointeePermission)
class AppointeePermissionAdmin(admin.ModelAdmin):
    def appointee_name(self, obj):
        return f"{obj.appointee.user.first_name} {obj.appointee.user.last_name}"
    
    def committee_name(self, obj):
        return obj.appointee.committee.name
    
    def granted_by_name(self, obj):
        if obj.granted_by:
            return f"{obj.granted_by.first_name} {obj.granted_by.last_name}"
        return "Unknown"
    
    def permission_count(self, obj):
        return obj.permissions.count()
    
    def permissions_display(self, obj):
        perms = obj.permissions.all()[:5]
        perm_names = [p.name for p in perms]
        if obj.permissions.count() > 5:
            return ", ".join(perm_names) + f" (+{obj.permissions.count() - 5} more)"
        return ", ".join(perm_names)
    
    appointee_name.short_description = "Appointee"
    committee_name.short_description = "Committee"
    granted_by_name.short_description = "Granted By"
    permission_count.short_description = "# Permissions"
    permissions_display.short_description = "Permissions"
    
    list_display = ["appointee_name", "committee_name", "permission_count", "granted_by_name", "granted_at", "is_active"]
    list_filter = ["is_active", "granted_at", "appointee__committee", "expires_at"]
    search_fields = [
        "appointee__user__first_name", 
        "appointee__user__last_name",
        "appointee__committee__name",
        "granted_by__first_name", 
        "granted_by__last_name",
        "permissions__name",
        "permissions__codename"
    ]
    readonly_fields = ["granted_at", "permission_count", "permissions_display", "granted_by"]
    filter_horizontal = ['permissions', 'groups']
    autocomplete_fields = ['appointee', 'granted_by']
    date_hierarchy = 'granted_at'
    
    # Note: fieldsets will be dynamically modified in get_fieldsets() to hide 'groups' for heads/deputies
    fieldsets = (
        ("Appointee Information", {
            "fields": ("appointee",),
            "description": "Select the committee member to grant permissions to"
        }),
        ("Permissions", {
            "fields": ("permissions", "groups", "permission_count", "permissions_display"),
            "description": "Select permissions to grant. Only permissions you have will be available."
        }),
        ("Grant Information", {
            # granted_by is readonly and will be set automatically to the current admin user
            "fields": ("granted_by", "granted_at", "notes")
        }),
        ("Status & Expiration", {
            "fields": ("is_active", "expires_at"),
            "description": "Set expiration date for temporary permissions or uncheck active to disable"
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        """Dynamically hide 'groups' field for heads/deputies"""
        fieldsets = super().get_fieldsets(request, obj)
        
        # Check if user is head/deputy
        is_head_or_deputy = Appointee.objects.filter(
            user=request.user,
            role__in=['head', 'deputy_head'],
            is_active=True
        ).exists()
        
        if is_head_or_deputy:
            # Remove 'groups' from the Permissions fieldset
            new_fieldsets = []
            for name, options in fieldsets:
                if name == "Permissions":
                    # Create new fields tuple without 'groups'
                    new_fields = tuple(f for f in options['fields'] if f != 'groups')
                    new_options = options.copy()
                    new_options['fields'] = new_fields
                    new_fieldsets.append((name, new_options))
                else:
                    new_fieldsets.append((name, options))
            return new_fieldsets
        
        return fieldsets
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('appointee__user', 'appointee__committee', 'granted_by').prefetch_related('permissions', 'groups')
        
        # Superusers and Executives see all permission grants
        if request.user.is_superuser or Executive.objects.filter(user=request.user).exists():
            return qs
        
        # Heads/Deputies see permission grants for members in their committee
        user_appointee = Appointee.objects.filter(
            user=request.user, 
            role__in=['head', 'deputy_head'], 
            is_active=True
        ).first()
        
        if user_appointee:
            # Show AppointeePermission records for all members in their committee
            # This includes members they added and existing members
            return qs.filter(appointee__committee=user_appointee.committee)
        
        # Regular appointees see nothing
        return qs.none()

    def get_form(self, request, obj=None, **kwargs):
        # Customize form based on user role
        form = super().get_form(request, obj, **kwargs)
        
        # Check if user is head/deputy (not superuser/executive)
        is_head_or_deputy = Appointee.objects.filter(
            user=request.user,
            role__in=['head', 'deputy_head'],
            is_active=True
        ).exists()
        
        if is_head_or_deputy:
            # REQUIREMENT 1: Hide groups field for heads/deputies
            # They should not see or assign group permissions
            if 'groups' in form.base_fields:
                del form.base_fields['groups']
            
            # REQUIREMENT 2: Filter permissions to only what the appointee has
            # Get all permissions the head/deputy currently has (from groups and direct permissions)
            if 'permissions' in form.base_fields:
                from django.contrib.auth.models import Permission
                from django.db.models import Q
                
                # Get permission IDs from user's groups
                group_perm_ids = Permission.objects.filter(
                    group__user=request.user
                ).values_list('id', flat=True)
                
                # Get permission IDs directly assigned to user
                direct_perm_ids = request.user.user_permissions.values_list('id', flat=True)
                
                # Combine IDs
                all_perm_ids = set(list(group_perm_ids) + list(direct_perm_ids))
                
                # Filter permissions queryset
                form.base_fields['permissions'].queryset = Permission.objects.filter(
                    id__in=all_perm_ids
                )
        
        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # REQUIREMENT 3: Restrict appointee selection based on who created them
        from executives.models import Appointee, AppointeePermission

        if db_field.name == "appointee":
            try:
                path = request.path
                is_change_view = "/change/" in path
                
                # Check if user is head/deputy
                user_appointee = Appointee.objects.filter(
                    user=request.user,
                    role__in=['head', 'deputy_head'],
                    is_active=True
                ).first()
                
                if user_appointee:
                    # For heads/deputies: Only show members in their committee who are:
                    # 1. Members (not heads/deputies)
                    # 2. Don't already have an AppointeePermission record (for add form)
                    # 3. OR editing existing record (change view)
                    
                    if is_change_view:
                        # Allow editing existing - show all members in their committee
                        kwargs['queryset'] = Appointee.objects.filter(
                            committee=user_appointee.committee,
                            role='member',
                            is_active=True
                        ).order_by('user__first_name')
                    else:
                        # Add form: Show only members without AppointeePermission in their committee
                        kwargs['queryset'] = Appointee.objects.filter(
                            committee=user_appointee.committee,
                            role='member',
                            is_active=True
                        ).exclude(
                            pk__in=AppointeePermission.objects.values_list('appointee_id', flat=True)
                        ).order_by('user__first_name')
                else:
                    # Superuser/Executive: Original behavior
                    if not is_change_view:
                        kwargs['queryset'] = Appointee.objects.exclude(
                            pk__in=AppointeePermission.objects.values_list('appointee_id', flat=True)
                        ).order_by('user__first_name')
            except Exception:
                pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request):
        """
        Only heads/deputies and admins can add permission grants.
        """
        if request.user.is_superuser or Executive.objects.filter(user=request.user).exists():
            return True
        
        return Appointee.objects.filter(
            user=request.user,
            role__in=['head', 'deputy_head'],
            is_active=True
        ).exists()
    
    def has_change_permission(self, request, obj=None):
        """
        Heads/deputies can change permission grants for members in their committee.
        """
        if request.user.is_superuser or Executive.objects.filter(user=request.user).exists():
            return True
        
        # Check if user is head/deputy
        user_appointee = Appointee.objects.filter(
            user=request.user,
            role__in=['head', 'deputy_head'],
            is_active=True
        ).first()
        
        if user_appointee:
            if obj is None:
                # List view - allow heads/deputies to see the change page
                return True
            
            # Check if the permission record is for a member in their committee
            if obj.appointee.committee == user_appointee.committee:
                return True
        
        return False
    
    def has_delete_permission(self, request, obj=None):
        """
        Heads/deputies can delete permission grants for members in their committee.
        """
        if request.user.is_superuser or Executive.objects.filter(user=request.user).exists():
            return True
        
        # Check if user is head/deputy
        user_appointee = Appointee.objects.filter(
            user=request.user,
            role__in=['head', 'deputy_head'],
            is_active=True
        ).first()
        
        if user_appointee and obj:
            # Check if the permission record is for a member in their committee
            if obj.appointee.committee == user_appointee.committee:
                return True
        
        return False
    
    def save_model(self, request, obj, form, change):
        # Capture old permissions before saving (for audit log)
        old_permissions = set()
        old_groups = set()
        if change and obj.pk:
            try:
                old_obj = AppointeePermission.objects.get(pk=obj.pk)
                old_permissions = set(old_obj.permissions.all())
                old_groups = set(old_obj.groups.all())
            except AppointeePermission.DoesNotExist:
                pass
        
        # Only set granted_by when creating a new permission record
        # When editing, preserve the original granter
        if not change:  # New object
            obj.granted_by = request.user
        
        super().save_model(request, obj, form, change)

        # CRITICAL FIX: Only add default group for heads/deputies, NOT members
        # Members should NOT get the "Head/Deputy Appointee" group automatically
        try:
            # Check if this is for a head or deputy head (not a member)
            if obj.appointee.role in ['head', 'deputy_head']:
                from django.contrib.auth.models import Group
                grp = Group.objects.filter(name__iexact='Head/Deputy Appointee').first()
                if grp:
                    # If groups were disabled in the form, set them here
                    if not obj.groups.exists():
                        obj.groups.set([grp])
                    # If groups already exist, don't overwrite
        except Exception:
            pass
        
        # CREATE AUDIT LOG
        try:
            from executives.models import PermissionAuditLog
            
            # Determine action type
            if not change:
                action = 'grant'
                details = f"New permission grant created for {obj.appointee.user.get_full_name()}"
            else:
                action = 'modify'
                # Check what changed
                new_permissions = set(obj.permissions.all())
                new_groups = set(obj.groups.all())
                
                added_perms = new_permissions - old_permissions
                removed_perms = old_permissions - new_permissions
                added_groups = new_groups - old_groups
                removed_groups = old_groups - new_groups
                
                changes = []
                if added_perms:
                    changes.append(f"Added {len(added_perms)} permissions")
                if removed_perms:
                    changes.append(f"Removed {len(removed_perms)} permissions")
                if added_groups:
                    changes.append(f"Added {len(added_groups)} groups")
                if removed_groups:
                    changes.append(f"Removed {len(removed_groups)} groups")
                
                details = f"Modified permissions for {obj.appointee.user.get_full_name()}: " + ", ".join(changes) if changes else f"Updated permission settings for {obj.appointee.user.get_full_name()}"
            
            # Get IP address
            ip_address = self._get_client_ip(request)
            
            # Create audit log
            audit_log = PermissionAuditLog.objects.create(
                action=action,
                target_user=obj.appointee.user,
                target_committee=obj.appointee.committee,
                performed_by=request.user,
                details=details,
                ip_address=ip_address
            )
            
            # Add permissions to audit log
            audit_log.permissions.set(obj.permissions.all())
            
        except Exception as e:
            # Don't fail the save if audit logging fails
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log: {e}")
    
    def delete_model(self, request, obj):
        """Create audit log when permission is deleted"""
        try:
            from executives.models import PermissionAuditLog
            
            # Capture permissions before deletion
            permissions = list(obj.permissions.all())
            
            details = f"Permission grant revoked for {obj.appointee.user.get_full_name()}"
            ip_address = self._get_client_ip(request)
            
            # Create audit log
            audit_log = PermissionAuditLog.objects.create(
                action='revoke',
                target_user=obj.appointee.user,
                target_committee=obj.appointee.committee,
                performed_by=request.user,
                details=details,
                ip_address=ip_address
            )
            
            # Add permissions to audit log
            audit_log.permissions.set(permissions)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for deletion: {e}")
        
        # Perform the actual deletion
        super().delete_model(request, obj)
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@admin.register(PermissionAuditLog)
class PermissionAuditLogAdmin(admin.ModelAdmin):
    def target_user_name(self, obj):
        if obj.target_user:
            return f"{obj.target_user.first_name} {obj.target_user.last_name}"
        return "(Deleted User)"
    
    def performed_by_name(self, obj):
        if obj.performed_by:
            return f"{obj.performed_by.first_name} {obj.performed_by.last_name}"
        return "System"
    
    def permission_count(self, obj):
        return obj.permissions.count()
    
    def permissions_display(self, obj):
        perms = obj.permissions.all()[:3]
        perm_names = [p.name for p in perms]
        if obj.permissions.count() > 3:
            return ", ".join(perm_names) + f" (+{obj.permissions.count() - 3} more)"
        return ", ".join(perm_names)
    
    target_user_name.short_description = "Target User"
    performed_by_name.short_description = "Performed By"
    permission_count.short_description = "# Permissions"
    permissions_display.short_description = "Permissions"
    
    list_display = ["target_user_name", "action", "permission_count", "performed_by_name", "timestamp"]
    list_filter = ["action", "timestamp", "target_committee"]
    search_fields = [
        "target_user__first_name", 
        "target_user__last_name", 
        "performed_by__first_name", 
        "performed_by__last_name",
        "permissions__name",
        "permissions__codename"
    ]
    readonly_fields = ["timestamp", "ip_address", "permission_count", "permissions_display"]
    filter_horizontal = ['permissions']
    
    fieldsets = (
        ("Action Details", {
            "fields": ("action", "permissions", "permission_count", "permissions_display")
        }),
        ("Involved Parties", {
            "fields": ("target_user", "target_committee", "performed_by")
        }),
        ("Audit Information", {
            "fields": ("timestamp", "details", "ip_address")
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('target_user', 'target_committee', 'performed_by').prefetch_related('permissions')
    
    def has_add_permission(self, request):
        # Audit logs should not be manually created
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Audit logs should not be deleted
        return False


# ============================================
# MEETING AND ATTENDANCE ADMIN
# ============================================

class MeetingAgendaItemInline(admin.TabularInline):
    """Inline for managing agenda items"""
    model = MeetingAgendaItem
    extra = 1
    fields = ['order', 'title', 'description', 'duration_minutes', 'presenter', 'is_discussed']
    autocomplete_fields = ['presenter']
    ordering = ['order']


class MeetingAttendanceInline(admin.TabularInline):
    """Inline for recording attendance"""
    model = MeetingAttendance
    extra = 0
    fields = ['user', 'status', 'arrival_time', 'departure_time', 'excuse_reason', 'notes']
    autocomplete_fields = ['user']
    readonly_fields = []
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == 'completed':
            # After meeting is completed, only allow viewing
            return ['user', 'status', 'arrival_time', 'departure_time', 'excuse_reason', 'notes']
        return []


class MeetingMinutesInline(MeetingMinutesMediaAdminMixin, admin.StackedInline):
    """Inline for meeting minutes"""
    model = MeetingMinutes
    extra = 0
    max_num = 1
    fields = [
        'summary', 'content', 
        ('minutes_file', 'minutes_file_url'),
        'decisions', 'action_items',
        ('is_approved', 'approved_by', 'approved_at'),
        'prepared_by'
    ]
    readonly_fields = ['approved_at']
    autocomplete_fields = ['prepared_by', 'approved_by']


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    """Admin for managing meetings"""
    
    def attendance_summary(self, obj):
        """Show attendance rate"""
        stats = obj.attendance_stats
        if stats['total'] == 0:
            return "No attendance recorded"
        return format_html(
            '<span style="color: {};">{}/{} ({}%)</span>',
            'green' if stats['rate'] >= 80 else 'orange' if stats['rate'] >= 60 else 'red',
            stats['present'],
            stats['total'],
            stats['rate']
        )
    attendance_summary.short_description = "Attendance"
    
    def meeting_scope(self, obj):
        """Show what group this meeting is for"""
        if obj.committee:
            return f"Committee: {obj.committee.name}"
        elif obj.is_executive_meeting:
            return "All Executives"
        return "General"
    meeting_scope.short_description = "Scope"
    
    def has_minutes(self, obj):
        """Check if minutes exist"""
        return hasattr(obj, 'minutes')
    has_minutes.boolean = True
    has_minutes.short_description = "Minutes"
    
    list_display = [
        'title', 'meeting_type', 'meeting_scope', 'scheduled_date', 
        'scheduled_time', 'status', 'attendance_summary', 'has_minutes'
    ]
    list_filter = [
        'meeting_type', 'status', 'is_executive_meeting', 
        'is_virtual', 'committee', 'office_year', 'scheduled_date'
    ]
    search_fields = ['title', 'description', 'agenda', 'venue']
    date_hierarchy = 'scheduled_date'
    autocomplete_fields = ['committee', 'created_by', 'chaired_by', 'additional_invitees']
    filter_horizontal = ['additional_invitees']
    inlines = [MeetingAgendaItemInline, MeetingAttendanceInline, MeetingMinutesInline]
    
    fieldsets = (
        ("Meeting Details", {
            "fields": ('title', 'meeting_type', 'description', 'agenda')
        }),
        ("Scope & Invitees", {
            "fields": ('committee', 'is_executive_meeting', 'additional_invitees'),
            "description": "Select committee for committee meetings, or check 'Executive meeting' for all executives"
        }),
        ("Schedule", {
            "fields": (
                ('scheduled_date', 'scheduled_time', 'end_time'),
                'duration_minutes'
            )
        }),
        ("Location", {
            "fields": (
                'venue',
                ('is_virtual', 'is_hybrid'),
                'virtual_link'
            )
        }),
        ("Status & Organization", {
            "fields": ('status', 'office_year', 'created_by', 'chaired_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['mark_completed', 'mark_cancelled', 'generate_attendance_sheet']
    
    @admin.action(description='Mark selected meetings as completed')
    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"Marked {queryset.count()} meetings as completed")
    
    @admin.action(description='Mark selected meetings as cancelled')
    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f"Marked {queryset.count()} meetings as cancelled")
    
    @admin.action(description='Generate attendance sheet for selected meetings')
    def generate_attendance_sheet(self, request, queryset):
        """Pre-populate attendance records for expected attendees"""
        count = 0
        for meeting in queryset:
            for user in meeting.expected_attendees:
                MeetingAttendance.objects.get_or_create(
                    meeting=meeting,
                    user=user,
                    defaults={
                        'status': 'absent',  # Default to absent until marked present
                        'recorded_by': request.user
                    }
                )
                count += 1
        self.message_user(request, f"Generated {count} attendance records")


@admin.register(MeetingAttendance)
class MeetingAttendanceAdmin(admin.ModelAdmin):
    """Standalone admin for attendance (for bulk operations)"""
    
    def user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    user_name.short_description = "Attendee"
    
    def meeting_info(self, obj):
        return f"{obj.meeting.title} ({obj.meeting.scheduled_date})"
    meeting_info.short_description = "Meeting"
    
    list_display = ['user_name', 'meeting_info', 'status', 'arrival_time', 'recorded_by', 'updated_at']
    list_filter = ['status', 'meeting__meeting_type', 'meeting__scheduled_date', 'meeting__committee']
    search_fields = [
        'user__first_name', 'user__last_name',
        'meeting__title'
    ]
    autocomplete_fields = ['user', 'meeting', 'recorded_by']
    list_editable = ['status']
    
    fieldsets = (
        (None, {
            "fields": ('meeting', 'user', 'status')
        }),
        ("Time Details", {
            "fields": (('arrival_time', 'departure_time'),)
        }),
        ("Additional Info", {
            "fields": ('excuse_reason', 'notes', 'recorded_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.recorded_by:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['mark_present', 'mark_absent', 'mark_excused']
    
    @admin.action(description='Mark selected as Present')
    def mark_present(self, request, queryset):
        queryset.update(status='present')
        self.message_user(request, f"Marked {queryset.count()} as present")
    
    @admin.action(description='Mark selected as Absent')
    def mark_absent(self, request, queryset):
        queryset.update(status='absent')
        self.message_user(request, f"Marked {queryset.count()} as absent")
    
    @admin.action(description='Mark selected as Excused')
    def mark_excused(self, request, queryset):
        queryset.update(status='excused')
        self.message_user(request, f"Marked {queryset.count()} as excused")


@admin.register(MeetingMinutes)
class MeetingMinutesAdmin(MeetingMinutesMediaAdminMixin, admin.ModelAdmin):
    """Standalone admin for meeting minutes"""
    
    def meeting_info(self, obj):
        return f"{obj.meeting.title} ({obj.meeting.scheduled_date})"
    meeting_info.short_description = "Meeting"
    
    def approval_status(self, obj):
        if obj.is_approved:
            return format_html(
                '<span style="color: green;">✓ Approved by {} on {}</span>',
                obj.approved_by.first_name if obj.approved_by else "Unknown",
                obj.approved_at.strftime('%Y-%m-%d') if obj.approved_at else "N/A"
            )
        return format_html('<span style="color: orange;">Pending Approval</span>')
    approval_status.short_description = "Status"
    
    def has_file(self, obj):
        return bool(obj.minutes_file or obj.minutes_file_url)
    has_file.boolean = True
    has_file.short_description = "File"
    
    list_display = ['meeting_info', 'prepared_by', 'approval_status', 'has_file', 'created_at']
    list_filter = ['is_approved', 'meeting__meeting_type', 'meeting__scheduled_date']
    search_fields = ['meeting__title', 'content', 'summary']
    autocomplete_fields = ['meeting', 'prepared_by', 'approved_by']
    
    fieldsets = (
        ("Meeting", {
            "fields": ('meeting',)
        }),
        ("Content", {
            "fields": ('summary', 'content')
        }),
        ("File Upload", {
            "fields": (('minutes_file', 'minutes_file_url'),),
            "description": "Upload a file OR provide a URL (Google Drive, Dropbox, etc.)"
        }),
        ("Decisions & Actions", {
            "fields": ('decisions', 'action_items'),
            "description": "Enter as JSON arrays. Action items format: [{'task': '...', 'assignee': '...', 'deadline': '...'}]"
        }),
        ("Approval", {
            "fields": (('is_approved', 'approved_by', 'approved_at'),)
        }),
        ("Prepared By", {
            "fields": ('prepared_by',)
        }),
    )
    readonly_fields = ['approved_at']
    
    def save_model(self, request, obj, form, change):
        if not obj.prepared_by:
            obj.prepared_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['approve_minutes']
    
    @admin.action(description='Approve selected minutes')
    def approve_minutes(self, request, queryset):
        for minutes in queryset:
            minutes.approve(request.user)
        self.message_user(request, f"Approved {queryset.count()} meeting minutes")


@admin.register(MeetingAgendaItem)
class MeetingAgendaItemAdmin(admin.ModelAdmin):
    """Standalone admin for agenda items"""
    
    list_display = ['title', 'meeting', 'order', 'duration_minutes', 'presenter', 'is_discussed']
    list_filter = ['is_discussed', 'meeting__meeting_type', 'meeting__scheduled_date']
    search_fields = ['title', 'description', 'meeting__title']
    autocomplete_fields = ['meeting', 'presenter']
    list_editable = ['order', 'is_discussed']
    ordering = ['meeting', 'order']


@admin.register(AttendanceReport)
class AttendanceReportAdmin(admin.ModelAdmin):
    """Admin for viewing attendance reports"""
    
    def user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    user_name.short_description = "User"
    
    def rate_display(self, obj):
        rate = float(obj.attendance_rate)
        color = 'green' if rate >= 80 else 'orange' if rate >= 60 else 'red'
        return format_html('<span style="color: {};">{}%</span>', color, rate)
    rate_display.short_description = "Attendance Rate"
    
    list_display = [
        'user_name', 'office_year', 'period_start', 'period_end',
        'total_meetings', 'meetings_attended', 'meetings_absent', 
        'meetings_excused', 'rate_display'
    ]
    list_filter = ['office_year', 'period_start']
    search_fields = ['user__first_name', 'user__last_name']
    readonly_fields = [
        'total_meetings', 'meetings_attended', 'meetings_absent',
        'meetings_excused', 'meetings_late', 'attendance_rate',
        'generated_at', 'generated_by'
    ]
    
    fieldsets = (
        ("User & Period", {
            "fields": ('user', 'office_year', ('period_start', 'period_end'))
        }),
        ("Statistics", {
            "fields": (
                ('total_meetings', 'meetings_attended'),
                ('meetings_absent', 'meetings_excused', 'meetings_late'),
                'attendance_rate'
            )
        }),
        ("Generation Info", {
            "fields": ('generated_at', 'generated_by')
        }),
    )
    
    actions = ['regenerate_reports']
    
    @admin.action(description='Regenerate selected reports')
    def regenerate_reports(self, request, queryset):
        for report in queryset:
            AttendanceReport.generate_for_user(
                user=report.user,
                period_start=report.period_start,
                period_end=report.period_end,
                office_year=report.office_year,
                generated_by=request.user
            )
        self.message_user(request, f"Regenerated {queryset.count()} reports")