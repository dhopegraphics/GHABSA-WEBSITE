from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.conf import settings
from notifications.models import (
    PushNotificationDevice,
    PushNotification,
    NotificationPreference,
)
from notifications.serializers import (
    PushNotificationDeviceSerializer,
    PushNotificationSerializer,
    NotificationPreferenceSerializer,
    SendPushNotificationSerializer,
)
from notifications.services import PushNotificationService


class RegisterDeviceView(generics.CreateAPIView):
    """Register a device for push notifications"""
    
    serializer_class = PushNotificationDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Override to return existing device if already registered"""
        device_token = request.data.get('device_token')
        
        if device_token:
            # Check if device already exists for this user
            existing_device = PushNotificationDevice.objects.filter(
                user=request.user,
                device_token=device_token
            ).first()
            
            if existing_device:
                # Reactivate and update device info
                existing_device.is_active = True
                existing_device.platform = request.data.get('platform', existing_device.platform)
                existing_device.device_name = request.data.get('device_name', existing_device.device_name)
                existing_device.save()
                
                serializer = self.get_serializer(existing_device)
                return Response(serializer.data, status=status.HTTP_200_OK)
        
        return super().create(request, *args, **kwargs)


class DeviceListView(generics.ListAPIView):
    """List user's registered devices"""
    
    serializer_class = PushNotificationDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PushNotificationDevice.objects.filter(user=self.request.user)


class DeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Manage a specific device"""
    
    serializer_class = PushNotificationDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PushNotificationDevice.objects.filter(user=self.request.user)


class CheckDeviceView(APIView):
    """Check if a device token is registered for the current user"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        device_token = request.data.get('device_token')
        
        if not device_token:
            return Response(
                {'error': 'device_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        device = PushNotificationDevice.objects.filter(
            user=request.user,
            device_token=device_token
        ).first()
        
        if device:
            return Response({
                'registered': True,
                'is_active': device.is_active,
                'device_id': str(device.id),
                'platform': device.platform,
                'device_name': device.device_name,
                'last_used': device.last_used.isoformat(),
            })
        
        return Response({
            'registered': False,
            'is_active': False,
            'device_id': None,
        })


class DeactivateCurrentDeviceView(APIView):
    """Deactivate (soft delete) the current device when disabling push notifications"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        device_token = request.data.get('device_token')
        
        if not device_token:
            return Response(
                {'error': 'device_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        device = PushNotificationDevice.objects.filter(
            user=request.user,
            device_token=device_token
        ).first()
        
        if device:
            device.is_active = False
            device.save()
            
            # Check if user has any other active devices
            has_other_devices = PushNotificationDevice.objects.filter(
                user=request.user,
                is_active=True
            ).exclude(id=device.id).exists()
            
            # If no other active devices, disable push in preferences
            if not has_other_devices:
                preference, _ = NotificationPreference.objects.get_or_create(
                    user=request.user
                )
                preference.push_enabled = False
                preference.save()
            
            return Response({
                'success': True,
                'message': 'Device deactivated successfully',
                'has_other_active_devices': has_other_devices,
            })
        
        return Response({
            'success': False,
            'error': 'Device not found'
        }, status=status.HTTP_404_NOT_FOUND)


class NotificationListView(generics.ListAPIView):
    """List user's notifications"""
    
    serializer_class = PushNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = PushNotification.objects.filter(user=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by trigger_type
        trigger_type = self.request.query_params.get('trigger_type', None)
        if trigger_type:
            queryset = queryset.filter(trigger_type=trigger_type)
        
        return queryset.order_by('-created_at')


class NotificationPreferenceView(APIView):
    """Get or update user's notification preferences"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        preferences, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferenceSerializer(preferences)
        
        # Include device info for frontend to check
        active_devices = PushNotificationDevice.objects.filter(
            user=request.user,
            is_active=True
        )
        
        response_data = serializer.data
        response_data['has_active_devices'] = active_devices.exists()
        response_data['active_device_count'] = active_devices.count()
        
        return Response(response_data)
    
    def patch(self, request):
        preferences, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        
        # Validate: Cannot enable push_enabled without registered devices
        if request.data.get('push_enabled') is True:
            active_devices = PushNotificationDevice.objects.filter(
                user=request.user,
                is_active=True
            ).exists()
            
            if not active_devices:
                return Response(
                    {
                        'error': 'Cannot enable push notifications without a registered device',
                        'code': 'NO_DEVICE_REGISTERED',
                        'detail': 'You must register at least one device before enabling push notifications'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = NotificationPreferenceSerializer(
            preferences,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendTestNotificationView(APIView):
    """Send a test push notification to the current user"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = SendPushNotificationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        result = PushNotificationService.send_to_user(
            user=request.user,
            title=data['title'],
            body=data['body'],
            data=data.get('data', {}),
            sound=data.get('sound', 'default'),
            priority=data.get('priority', 'default'),
            badge=data.get('badge', 1),
            category=data.get('category', None),
        )
        
        if result.get('success'):
            return Response({
                'success': True,
                'message': 'Notification sent successfully'
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_stats(request):
    """Get notification statistics for the current user"""
    
    user = request.user
    
    total = PushNotification.objects.filter(user=user).count()
    sent = PushNotification.objects.filter(user=user, status='sent').count()
    pending = PushNotification.objects.filter(user=user, status='scheduled').count()
    failed = PushNotification.objects.filter(user=user, status='failed').count()
    
    # Get all devices with detailed info
    devices = PushNotificationDevice.objects.filter(user=user, is_active=True)
    device_list = [{
        'id': str(device.id),
        'platform': device.platform,
        'device_name': device.device_name,
        'last_used': device.last_used.isoformat(),
        'created_at': device.created_at.isoformat(),
    } for device in devices]
    
    return Response({
        'total_notifications': total,
        'sent': sent,
        'pending': pending,
        'failed': failed,
        'active_devices': devices.count(),
        'devices': device_list,
    })


@api_view(['GET'])
def get_vapid_public_key(request):
    """
    Get VAPID public key for Web Push subscriptions
    This endpoint is public so users can subscribe before authentication
    """
    vapid_public_key = getattr(settings, 'WEBPUSH_SETTINGS', {}).get('VAPID_PUBLIC_KEY', '')
    
    if not vapid_public_key:
        return Response(
            {'error': 'VAPID public key not configured'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response({
        'publicKey': vapid_public_key
    })
