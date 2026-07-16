"""
Views for Device Management
"""
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.device_serializers import (
    UserDeviceSerializer,
    DeviceLoginHistorySerializer,
    DeviceActionSerializer,
    DeviceListResponseSerializer
)
from accounts.device_repository import UserDeviceRepository, DeviceLoginHistoryRepository
from accounts.device_utils import get_device_info_from_request


class UserDevicesListView(ListAPIView):
    """
    GET: List all devices for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserDeviceSerializer
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Get device info from current request
        device_info = get_device_info_from_request(request)
        current_device_fingerprint = device_info.get('device_fingerprint')
        
        # Get all devices
        devices = UserDeviceRepository.get_user_devices(user, active_only=False)
        
        # Add current device info to context
        # First try exact fingerprint match
        request.current_device_id = None
        for device in devices:
            if device.device_fingerprint == current_device_fingerprint:
                request.current_device_id = device.id
                break
        
        # If no exact match, try to find by is_current flag (for backwards compatibility)
        if not request.current_device_id:
            for device in devices:
                if device.is_current and device.is_active:
                    # Update the fingerprint for this device since it's likely the same device
                    # but with a new fingerprint after app update
                    device.device_fingerprint = current_device_fingerprint
                    device.save(update_fields=['device_fingerprint'])
                    request.current_device_id = device.id
                    break
        
        # Serialize
        serializer = self.serializer_class(
            devices,
            many=True,
            context={'request': request}
        )
        
        # Count active devices
        active_count = sum(1 for d in devices if d.is_active)
        
        return Response({
            'status': 'success',
            'message': 'Devices retrieved successfully',
            'data': {
                'devices': serializer.data,
                'total_devices': devices.count(),
                'active_devices': active_count,
            }
        }, status=status.HTTP_200_OK)


class DeviceActionView(APIView):
    """
    POST: Perform actions on devices (deactivate, trust, untrust)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = DeviceActionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid request data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        device_id = serializer.validated_data['device_id']
        action = serializer.validated_data['action']
        user = request.user
        
        # Get the device
        device = UserDeviceRepository.get_device_by_id(device_id, user)
        
        if not device:
            return Response({
                'status': 'error',
                'message': 'Device not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Perform action
        if action == 'deactivate':
            if device.is_current:
                return Response({
                    'status': 'error',
                    'message': 'Cannot deactivate your current device'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            device.deactivate()
            message = 'Device deactivated successfully (logged out)'
        
        elif action == 'block':
            if device.is_current:
                return Response({
                    'status': 'error',
                    'message': 'Cannot block your current device'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            reason = serializer.validated_data.get('reason', 'Blocked by user')
            device.block(reason=reason)
            message = 'Device blocked successfully. This device cannot access your account anymore.'
        
        elif action == 'unblock':
            device.unblock()
            message = 'Device unblocked successfully'
        
        elif action == 'trust':
            device.is_trusted = True
            device.save()
            message = 'Device marked as trusted'
        
        elif action == 'untrust':
            device.is_trusted = False
            device.save()
            message = 'Device unmarked as trusted'
        
        return Response({
            'status': 'success',
            'message': message,
            'data': UserDeviceSerializer(device, context={'request': request}).data
        }, status=status.HTTP_200_OK)


class DeactivateAllDevicesView(APIView):
    """
    POST: Deactivate all devices except the current one
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        
        # Get current device
        device_info = get_device_info_from_request(request)
        fingerprint = device_info.get('device_fingerprint')
        
        # Find current device by fingerprint first
        current_device = UserDeviceRepository.get_user_devices(user).filter(
            device_fingerprint=fingerprint
        ).first()
        
        # If no exact match, try to find by is_current flag
        if not current_device:
            current_device = UserDeviceRepository.get_user_devices(user).filter(
                is_current=True, is_active=True
            ).first()
            
            # Update fingerprint if found
            if current_device:
                current_device.device_fingerprint = fingerprint
                current_device.save(update_fields=['device_fingerprint'])
        
        if not current_device:
            return Response({
                'status': 'error',
                'message': 'Current device not found. Please login again.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Deactivate all except current
        UserDeviceRepository.deactivate_all_except_current(user, current_device.id)
        
        return Response({
            'status': 'success',
            'message': 'All other devices have been logged out'
        }, status=status.HTTP_200_OK)


class LoginHistoryView(ListAPIView):
    """
    GET: Get login history for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DeviceLoginHistorySerializer
    
    def get(self, request, *args, **kwargs):
        user = request.user
        limit = int(request.query_params.get('limit', 50))
        
        # Get login history
        history = DeviceLoginHistoryRepository.get_user_login_history(user, limit=limit)
        
        # Serialize
        serializer = self.serializer_class(history, many=True)
        
        return Response({
            'status': 'success',
            'message': 'Login history retrieved successfully',
            'data': {
                'history': serializer.data,
                'total': len(serializer.data)
            }
        }, status=status.HTTP_200_OK)


class CurrentDeviceView(APIView):
    """
    GET: Get information about the current device
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Get device info from request
        device_info = get_device_info_from_request(request)
        fingerprint = device_info.get('device_fingerprint')
        
        # Find the device by fingerprint first
        device = UserDeviceRepository.get_user_devices(user).filter(
            device_fingerprint=fingerprint
        ).first()
        
        # If not found, try by is_current flag (for backwards compatibility)
        if not device:
            device = UserDeviceRepository.get_user_devices(user).filter(
                is_current=True, is_active=True
            ).first()
            
            # Update fingerprint if found
            if device:
                device.device_fingerprint = fingerprint
                device.save(update_fields=['device_fingerprint'])
        
        if not device:
            return Response({
                'status': 'error',
                'message': 'Current device not found. Please login again.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize
        serializer = UserDeviceSerializer(device, context={'request': request})
        
        return Response({
            'status': 'success',
            'message': 'Current device retrieved successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
