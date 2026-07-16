"""
Views for managing notification read/unread status
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import logging

from notifications.recent_updates_repository import RecentUpdatesRepository

logger = logging.getLogger(__name__)


class MarkUpdateAsReadView(APIView):
    """
    Mark one or multiple updates as read
    
    POST /api/notifications/recent-updates/mark-read/
    Body: {"update_ids": ["event-123", "task-456"]}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Mark updates as read"""
        try:
            update_ids = request.data.get('update_ids', [])
            if not update_ids:
                return Response(
                    {'success': False, 'error': 'update_ids is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not isinstance(update_ids, list):
                update_ids = [update_ids]
            
            from notifications.models import RecentUpdateReadStatus
            
            # Mark as read (or undelete if previously deleted)
            marked_count = 0
            for update_id in update_ids:
                # Extract update type from update_id (e.g., "event-123" -> "event")
                update_type = update_id.split('-')[0] if '-' in update_id else 'unknown'
                
                # Get or create, and reset is_deleted flag
                read_status, created = RecentUpdateReadStatus.objects.update_or_create(
                    user=request.user,
                    update_id=update_id,
                    defaults={
                        'is_deleted': False,
                        'deleted_at': None,
                        'update_type': update_type
                    }
                )
                marked_count += 1
            
            return Response({
                'success': True,
                'marked_count': marked_count,
                'message': f'Marked {marked_count} update(s) as read'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error marking updates as read: {str(e)}", exc_info=True)
            return Response(
                {'success': False, 'error': 'Failed to mark updates as read'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DeleteUpdateView(APIView):
    """
    Delete/hide an update from the user's notifications
    
    DELETE /api/notifications/recent-updates/<update_id>/delete/
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, update_id):
        """Delete/hide an update"""
        try:
            from notifications.models import RecentUpdateReadStatus
            
            # Extract update type from update_id
            update_type = update_id.split('-')[0] if '-' in update_id else 'unknown'
            
            # Mark as deleted (and also as read)
            read_status, created = RecentUpdateReadStatus.objects.update_or_create(
                user=request.user,
                update_id=update_id,
                defaults={
                    'is_deleted': True,
                    'deleted_at': timezone.now(),
                    'update_type': update_type
                }
            )
            
            return Response({
                'success': True,
                'message': 'Update deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error deleting update: {str(e)}", exc_info=True)
            return Response(
                {'success': False, 'error': 'Failed to delete update'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UnreadCountView(APIView):
    """
    Get count of unread notifications
    
    GET /api/notifications/recent-updates/unread-count/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get unread notification count"""
        try:
            days = int(request.GET.get('days', 7))
            days = max(1, min(days, 30))
            
            # Get all updates (without pagination for counting)
            result = RecentUpdatesRepository.get_recent_updates(
                user=request.user,
                days=days,
                limit=1000,  # Get all for counting
            )
            
            from notifications.models import RecentUpdateReadStatus
            
            # Get read/deleted update IDs
            read_or_deleted_ids = set(
                RecentUpdateReadStatus.objects.filter(
                    user=request.user
                ).values_list('update_id', flat=True)
            )
            
            # Count unread (not read and not deleted)
            all_update_ids = [update['id'] for update in result['results']]
            unread_ids = [uid for uid in all_update_ids if uid not in read_or_deleted_ids]
            
            # Count by category
            from collections import defaultdict
            unread_by_category = defaultdict(int)
            for update in result['results']:
                if update['id'] in unread_ids:
                    unread_by_category[update['category']] += 1
            
            return Response({
                'success': True,
                'unread_count': len(unread_ids),
                'total_count': len(all_update_ids),
                'unread_by_category': dict(unread_by_category)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}", exc_info=True)
            return Response(
                {'success': False, 'error': 'Failed to get unread count'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
