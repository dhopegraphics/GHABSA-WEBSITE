"""
Admin configuration for Device Management

SECURITY RESTRICTIONS:
----------------------
1. UserDevice Records:
   - Admins CANNOT add new device records (has_add_permission = False)
   - Device records are automatically created during user login/authentication
   - Admins CAN view all device information for monitoring
   - Admins CAN modify ONLY security settings: is_trusted, is_active, is_blocked, block_reason
   - All other fields (user, device_type, platform, IP, location, etc.) are READ-ONLY
   - Admins CAN delete devices to force re-authentication

2. DeviceLoginHistory Records:
   - Admins CANNOT add new login history records
   - Admins CANNOT modify login history records
   - Login history is automatically created during authentication attempts
   - Admins CAN view login history for security auditing
   - Admins CAN delete old login history records

These restrictions ensure:
- Device fingerprinting integrity (cannot be manually manipulated)
- Accurate login history for security audits
- Admins can only manage security controls, not spoof devices
"""
from django.contrib import admin
from accounts.device_models import UserDevice, DeviceLoginHistory


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'device_display',
        'platform',
        'device_type',
        'location_display',
        'is_current',
        'is_trusted',
        'is_blocked',
        'is_active',
        'last_active',
    ]
    list_filter = [
        'device_type',
        'platform',
        'is_current',
        'is_trusted',
        'is_blocked',
        'is_active',
        'country',
    ]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__phone',
        'device_name',
        'browser',
        'ip_address',
        'country',
        'city',
    ]
    readonly_fields = [
        'id',
        'user',
        'device_type',
        'platform',
        'device_name',
        'browser',
        'device_fingerprint',
        'user_agent',
        'ip_address',
        'country',
        'city',
        'first_login',
        'last_active',
        'refresh_token_jti',
        'is_current',
    ]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'is_current')
        }),
        ('Device Information', {
            'fields': (
                'device_type',
                'platform',
                'device_name',
                'browser',
                'device_fingerprint',
            )
        }),
        ('Location Information', {
            'fields': ('ip_address', 'country', 'city')
        }),
        ('Session Information', {
            'fields': (
                'first_login',
                'last_active',
                'refresh_token_jti',
            )
        }),
        ('Security Controls', {
            'fields': ('is_trusted', 'is_active', 'is_blocked', 'blocked_at', 'block_reason'),
            'description': 'Admins can only modify security settings (trust, active status, blocking). All other fields are auto-generated during login.'
        }),
        ('Technical Details', {
            'fields': ('user_agent',),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """
        Make all fields readonly except security controls.
        Device records are auto-created during login.
        """
        if obj:  # Editing existing device
            # Only allow modifying security-related fields
            return [f for f in self.readonly_fields]
        # When adding (which shouldn't happen), make everything readonly
        return self.readonly_fields
    
    def has_add_permission(self, request):
        """
        Prevent admins from manually creating device records.
        Devices are automatically created during user authentication.
        """
        return False
    
    def has_change_permission(self, request, obj=None):
        """
        Allow viewing and modifying only security settings.
        """
        return True
    
    def device_display(self, obj):
        return obj.get_device_display()
    device_display.short_description = 'Device'
    
    def location_display(self, obj):
        return obj.get_location_display()
    location_display.short_description = 'Location'


@admin.register(DeviceLoginHistory)
class DeviceLoginHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'device',
        'login_time',
        'ip_address',
        'location',
        'success',
    ]
    list_filter = [
        'success',
        'login_time',
    ]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__phone',
        'ip_address',
        'location',
    ]
    readonly_fields = [
        'id',
        'device',
        'user',
        'login_time',
        'ip_address',
        'location',
        'success',
        'reason',
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
