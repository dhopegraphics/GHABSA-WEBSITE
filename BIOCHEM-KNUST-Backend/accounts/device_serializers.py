"""
Serializers for Device Management
"""
from rest_framework import serializers
from accounts.device_models import UserDevice, DeviceLoginHistory
from django.utils import timezone


class UserDeviceSerializer(serializers.ModelSerializer):
    """Serializer for user devices"""
    location = serializers.SerializerMethodField()
    device_display = serializers.SerializerMethodField()
    last_active_humanized = serializers.SerializerMethodField()
    is_this_device = serializers.SerializerMethodField()
    
    class Meta:
        model = UserDevice
        fields = [
            'id',
            'device_type',
            'platform',
            'device_name',
            'browser',
            'device_display',
            'is_current',
            'is_trusted',
            'is_active',
            'is_blocked',
            'blocked_at',
            'block_reason',
            'last_active',
            'last_active_humanized',
            'first_login',
            'location',
            'ip_address',
            'is_this_device',
        ]
        read_only_fields = [
            'id',
            'device_type',
            'platform',
            'device_name',
            'browser',
            'last_active',
            'first_login',
            'ip_address',
            'blocked_at',
        ]
    
    def get_location(self, obj):
        """Get formatted location"""
        return obj.get_location_display()
    
    def get_device_display(self, obj):
        """Get user-friendly device name"""
        return obj.get_device_display()
    
    def get_last_active_humanized(self, obj):
        """Get human-readable last active time"""
        now = timezone.now()
        diff = now - obj.last_active
        
        if diff.days > 30:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
    def get_is_this_device(self, obj):
        """Check if this is the current request's device"""
        request = self.context.get('request')
        if request and hasattr(request, 'current_device_id'):
            return str(obj.id) == str(request.current_device_id)
        return obj.is_current


class DeviceLoginHistorySerializer(serializers.ModelSerializer):
    """Serializer for device login history"""
    device_display = serializers.CharField(source='device.get_device_display', read_only=True)
    
    class Meta:
        model = DeviceLoginHistory
        fields = [
            'id',
            'device',
            'device_display',
            'login_time',
            'ip_address',
            'location',
            'success',
            'reason',
        ]
        read_only_fields = fields


class DeviceActionSerializer(serializers.Serializer):
    """Serializer for device actions (deactivate, block, trust, etc.)"""
    device_id = serializers.UUIDField(required=True)
    action = serializers.ChoiceField(
        choices=['deactivate', 'block', 'unblock', 'trust', 'untrust'],
        required=True
    )
    reason = serializers.CharField(
        required=False,
        max_length=255,
        help_text="Reason for blocking (required when action=block)"
    )


class DeviceListResponseSerializer(serializers.Serializer):
    """Response serializer for device list"""
    devices = UserDeviceSerializer(many=True)
    total_devices = serializers.IntegerField()
    active_devices = serializers.IntegerField()
