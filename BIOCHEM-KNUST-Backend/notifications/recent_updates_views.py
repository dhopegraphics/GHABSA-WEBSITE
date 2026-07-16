"""
Recent Updates Views
API endpoints for aggregated notifications without database storage
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import logging

from notifications.recent_updates_repository import RecentUpdatesRepository
from notifications.recent_updates_serializers import (
    RecentUpdatesResponseSerializer,
    RecentUpdateSerializer,
    NotificationStatsSerializer,
)

logger = logging.getLogger(__name__)


class RecentUpdatesView(APIView):
    """
    Get aggregated recent updates from multiple sources
    No database storage - aggregates from existing models
    
    GET /api/recent-updates/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get recent updates for the authenticated user"""
        try:
            # Get query parameters
            days = int(request.GET.get('days', 7))
            days = max(1, min(days, 30))  # Limit to 1-30 days
            
            types = request.GET.get('types', None)
            if types:
                types = [t.strip() for t in types.split(',')]
            
            priority = request.GET.get('priority', None)
            
            page = int(request.GET.get('page', 1))
            page = max(1, page)
            
            page_size = int(request.GET.get('page_size', 20))
            page_size = max(1, min(page_size, 100))  # Limit to 1-100 items
            
            # Get updates from repository
            result = RecentUpdatesRepository.get_recent_updates(
                user=request.user,
                days=days,
                types=types,
                priority=priority,
                page=page,
                page_size=page_size,
            )
            
            # Serialize the results list with context to include request
            serialized_results = RecentUpdateSerializer(
                result['results'], 
                many=True,
                context={'request': request}
            )
            result['results'] = serialized_results.data
            
            return Response(result, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"ValueError in RecentUpdatesView: {str(e)}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Exception in RecentUpdatesView: {str(e)}", exc_info=True)
            return Response(
                {'success': False, 'error': 'Failed to fetch updates'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecentUpdatesStatsView(APIView):
    """
    Get statistics about recent updates
    
    GET /api/recent-updates/stats/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get update statistics for the authenticated user"""
        try:
            days = int(request.GET.get('days', 7))
            days = max(1, min(days, 30))
            
            # Get updates
            result = RecentUpdatesRepository.get_recent_updates(
                user=request.user,
                days=days,
                limit=1000,  # Get all for stats
            )
            
            return Response(
                {
                    'success': True,
                    'stats': result['stats']
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'success': False, 'error': 'Failed to fetch statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecentUpdatesByTypeView(APIView):
    """
    Get updates filtered by specific type
    
    GET /api/recent-updates/type/<type>/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, update_type):
        """Get updates of a specific type"""
        try:
            # Validate type
            valid_types = ['task', 'event', 'helpdesk', 'payment', 'security', 'system']
            if update_type not in valid_types:
                return Response(
                    {
                        'success': False,
                        'error': f'Invalid type. Must be one of: {", ".join(valid_types)}'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            days = int(request.GET.get('days', 7))
            days = max(1, min(days, 30))
            
            page = int(request.GET.get('page', 1))
            page = max(1, page)
            
            page_size = int(request.GET.get('page_size', 20))
            page_size = max(1, min(page_size, 100))
            
            # Get updates
            result = RecentUpdatesRepository.get_recent_updates(
                user=request.user,
                days=days,
                types=[update_type],
                page=page,
                page_size=page_size,
            )
            
            # Serialize with context
            serialized_results = RecentUpdateSerializer(
                result['results'], 
                many=True,
                context={'request': request}
            )
            result['results'] = serialized_results.data
            
            return Response(result, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'success': False, 'error': 'Failed to fetch updates'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
