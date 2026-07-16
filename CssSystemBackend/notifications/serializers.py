from rest_framework import serializers
from notifications.models import (
    PushNotificationDevice,
    PushNotificationTemplate,
    PushNotification,
    NotificationTrigger,
    NotificationPreference,
)


class PushNotificationDeviceSerializer(serializers.ModelSerializer):
    """Serializer for registering/updating device tokens"""
    
    class Meta:
        model = PushNotificationDevice
        fields = ['id', 'device_token', 'platform', 'device_name', 'web_subscription', 'is_active', 'last_used', 'created_at']
        read_only_fields = ['id', 'last_used', 'created_at']
    
    def validate(self, data):
        """Validate platform-specific requirements"""
        platform = data.get('platform')
        device_token = data.get('device_token')
        web_subscription = data.get('web_subscription')
        
        # For web platform, ensure we have proper subscription data
        if platform == 'web':
            if not web_subscription:
                raise serializers.ValidationError({
                    'web_subscription': 'Web push subscription object is required for web platform'
                })
            
            # Validate subscription structure
            required_fields = ['endpoint', 'keys']
            for field in required_fields:
                if field not in web_subscription:
                    raise serializers.ValidationError({
                        'web_subscription': f'Missing required field: {field}'
                    })
            
            # Validate keys structure
            if 'keys' in web_subscription:
                required_keys = ['p256dh', 'auth']
                for key in required_keys:
                    if key not in web_subscription['keys']:
                        raise serializers.ValidationError({
                            'web_subscription': f'Missing required key: {key}'
                        })
            
            # For web, use endpoint as device_token if not provided
            if not device_token:
                data['device_token'] = web_subscription['endpoint']
        
        # For mobile platforms, ensure device_token is provided
        elif platform in ['ios', 'android']:
            if not device_token:
                raise serializers.ValidationError({
                    'device_token': f'Device token is required for {platform} platform'
                })
        
        return data
    
    def create(self, validated_data):
        # Support multiple devices per user by using device_token as unique identifier
        # If same device_token exists (regardless of user), update it to current user
        # This handles device token reuse (e.g., user logs out, different user logs in on same device)
        # OR if same user + device_token exists, just refresh the device info
        device, created = PushNotificationDevice.objects.update_or_create(
            device_token=validated_data['device_token'],  # Device token is globally unique
            defaults={
                'user': validated_data['user'],  # Update to current user
                'platform': validated_data.get('platform'),
                'device_name': validated_data.get('device_name', ''),
                'web_subscription': validated_data.get('web_subscription'),  # Add web_subscription
                'is_active': True,  # Always reactivate on registration
            }
        )
        return device


class PushNotificationSerializer(serializers.ModelSerializer):
    """Serializer for viewing notifications"""
    
    template_name = serializers.CharField(source='template.name', read_only=True, allow_null=True)
    
    class Meta:
        model = PushNotification
        fields = [
            'id', 'title', 'body', 'data', 'status',
            'scheduled_at', 'sent_at', 'created_at',
            'template_name', 'trigger_type', 'sound', 'category'
        ]
        read_only_fields = ['id', 'status', 'sent_at', 'created_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user notification preferences"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'push_enabled', 'sms_enabled', 'email_enabled',
            'class_reminders', 'exam_reminders', 'event_notifications',
            'deadline_reminders', 'general_announcements',
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end'
        ]


class SendPushNotificationSerializer(serializers.Serializer):
    """Serializer for sending immediate push notifications"""
    
    title = serializers.CharField(max_length=100)
    body = serializers.CharField()
    data = serializers.JSONField(required=False, default=dict)
    sound = serializers.CharField(default='default', required=False)
    priority = serializers.ChoiceField(
        choices=['default', 'high', 'low'],
        default='default',
        required=False
    )
    badge = serializers.IntegerField(default=1, required=False)
    category = serializers.CharField(required=False, allow_null=True, allow_blank=True)
