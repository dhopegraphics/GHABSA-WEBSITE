from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import UserRateThrottle
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    HelpDeskCategory, HelpDeskRequest, HelpDeskResponse,
    ResponseVote, ResponseReply, RequestBookmark, HelpDeskNotification,
    ContentReport
)
from .serializers import (
    HelpDeskCategorySerializer, HelpDeskRequestListSerializer,
    HelpDeskRequestDetailSerializer, HelpDeskRequestCreateSerializer,
    HelpDeskRequestUpdateSerializer, HelpDeskResponseListSerializer,
    HelpDeskResponseCreateSerializer, ResponseVoteSerializer,
    ResponseReplySerializer, ResponseReplyCreateSerializer,
    RequestBookmarkSerializer, HelpDeskNotificationSerializer,
    ContentReportSerializer, MyRequestSerializer, HelpingRequestSerializer
)
from .repository import (
    HelpDeskRepository, ResponseRepository, NotificationRepository
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CreateRequestThrottle(UserRateThrottle):
    rate = '5/hour'


class CreateResponseThrottle(UserRateThrottle):
    rate = '20/hour'


class HelpDeskCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for HelpDesk categories
    List and retrieve only
    """
    queryset = HelpDeskCategory.objects.filter(is_active=True)
    serializer_class = HelpDeskCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return self.queryset.order_by('display_order', 'name')


class HelpDeskRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Help Requests
    CRUD operations + custom actions
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        from django.db.models import Case, When, IntegerField
        
        user = self.request.user
        queryset = HelpDeskRepository.get_active_requests()
        
        # Apply filters from query params
        category = self.request.query_params.get('category')
        priority = self.request.query_params.get('priority')
        search = self.request.query_params.get('search')
        has_responses = self.request.query_params.get('has_responses')
        ordering = self.request.query_params.get('ordering', '-created_at')
        
        filters = {}
        if category:
            filters['category'] = category
        if priority:
            filters['priority'] = priority
        if search:
            filters['search'] = search
        if has_responses:
            filters['has_responses'] = has_responses
        
        # Handle priority ordering BEFORE passing to repository (urgent > high > normal)
        if 'priority_order' in ordering:
            # Get queryset with filters but no ordering yet (pass empty string to skip default ordering)
            queryset = HelpDeskRepository.get_active_requests(filters, '')
            queryset = queryset.annotate(
                priority_rank=Case(
                    When(priority='urgent', then=1),
                    When(priority='high', then=2),
                    When(priority='normal', then=3),
                    output_field=IntegerField(),
                )
            )
            # Replace priority_order with priority_rank in ordering
            ordering = ordering.replace('priority_order', 'priority_rank')
            # Clear any existing ordering and apply our custom one
            queryset = queryset.order_by()  # Clear existing ordering
            queryset = queryset.order_by(*ordering.split(','))
        else:
            # Normal ordering - pass to repository
            queryset = HelpDeskRepository.get_active_requests(filters, ordering)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return HelpDeskRequestListSerializer
        elif self.action == 'create':
            return HelpDeskRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return HelpDeskRequestUpdateSerializer
        return HelpDeskRequestDetailSerializer
    
    def get_throttles(self):
        if self.action == 'create':
            return [CreateRequestThrottle()]
        return super().get_throttles()
    
    def retrieve(self, request, *args, **kwargs):
        """Get request details and track view"""
        # Get fresh instance without annotations from list queryset
        pk = kwargs.get('pk')
        instance = HelpDeskRequest.objects.select_related('category').prefetch_related(
            'code_snippets', 'images'
        ).get(pk=pk)
        
        # Track view
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        HelpDeskRepository.track_request_view(
            instance, request.user, ip_address, user_agent
        )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """Create new request"""
        serializer.save(author=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Update request - only if no responses"""
        instance = self.get_object()
        
        # Check ownership
        if instance.author != request.user:
            return Response(
                {'error': 'You can only edit your own requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if has responses
        if instance.response_count > 0:
            return Response(
                {'error': 'Cannot edit request that has responses'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete request"""
        instance = self.get_object()
        
        # Check ownership
        if instance.author != request.user:
            return Response(
                {'error': 'You can only delete your own requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if has responses
        if instance.response_count > 0:
            return Response(
                {'error': 'Cannot delete request that has responses'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Soft delete
        instance.is_deleted = True
        instance.status = 'deleted'
        instance.save(update_fields=['is_deleted', 'status'])
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Get current user's requests"""
        status_filter = request.query_params.get('status')
        queryset = HelpDeskRepository.get_my_requests(request.user, status_filter)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MyRequestSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = MyRequestSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def helping(self, request):
        """Get requests where user has posted responses"""
        queryset = HelpDeskRepository.get_helping_requests(request.user)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = HelpingRequestSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = HelpingRequestSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark request as resolved (author only)"""
        instance = self.get_object()
        
        if instance.author != request.user:
            return Response(
                {'error': 'Only request author can mark as resolved'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance.is_resolved = True
        instance.resolved_at = timezone.now()
        instance.status = 'resolved'
        instance.save(update_fields=['is_resolved', 'resolved_at', 'status'])
        
        # Create notifications
        NotificationRepository.create_resolved_notification(instance)
        
        return Response({
            'id': str(instance.id),
            'is_resolved': True,
            'resolved_at': instance.resolved_at
        })
    
    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """Reopen a resolved request (author only)"""
        instance = self.get_object()
        
        if instance.author != request.user:
            return Response(
                {'error': 'Only request author can reopen'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance.is_resolved = False
        instance.resolved_at = None
        instance.status = 'active'
        instance.save(update_fields=['is_resolved', 'resolved_at', 'status'])
        
        return Response({
            'id': str(instance.id),
            'is_resolved': False,
            'status': 'active'
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search requests"""
        query = request.query_params.get('q', '')
        filters = {
            'category': request.query_params.get('category'),
            'priority': request.query_params.get('priority'),
            'tags': request.query_params.get('tags'),
        }
        
        queryset = HelpDeskRepository.search_requests(query, filters)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = HelpDeskRequestListSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = HelpDeskRequestListSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)


class HelpDeskResponseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Responses
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = HelpDeskResponseListSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        request_id = self.request.query_params.get('request_id')
        if request_id:
            sort = self.request.query_params.get('sort', '-created_at')
            return HelpDeskRepository.get_request_responses(request_id, sort)

        # For detail actions (retrieve, update, vote, etc.) the router
        # calls `get_object()` which looks up the instance from this
        # queryset. Returning `none()` here prevents lookups by pk and
        # causes 404s for detail actions when `request_id` isn't passed.
        #
        # Return a safe default queryset of non-deleted responses so
        # detail actions can find a response by its pk.
        return HelpDeskResponse.objects.filter(is_deleted=False)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return HelpDeskResponseCreateSerializer
        return HelpDeskResponseListSerializer
    
    def get_throttles(self):
        if self.action == 'create':
            return [CreateResponseThrottle()]
        return super().get_throttles()
    
    def perform_create(self, serializer):
        """Create new response"""
        response = serializer.save(author=self.request.user)
        
        # Create notification
        NotificationRepository.create_new_response_notification(response)
    
    def update(self, request, *args, **kwargs):
        """Update response - only within 15 minutes"""
        instance = self.get_object()
        
        # Check ownership
        if instance.author != request.user:
            return Response(
                {'error': 'You can only edit your own responses'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check time limit (15 minutes)
        time_diff = timezone.now() - instance.created_at
        if time_diff.total_seconds() > 900:  # 15 minutes
            return Response(
                {'error': 'Can only edit responses within 15 minutes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if marked helpful
        if instance.is_marked_helpful:
            return Response(
                {'error': 'Cannot edit response marked as helpful'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete response"""
        instance = self.get_object()
        
        if instance.author != request.user:
            return Response(
                {'error': 'You can only delete your own responses'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if instance.is_marked_helpful:
            return Response(
                {'error': 'Cannot delete response marked as helpful'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Soft delete
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])
        
        # Update request response count
        instance.request.response_count -= 1
        instance.request.save(update_fields=['response_count'])
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post', 'delete'])
    def vote(self, request, pk=None):
        """Vote on response (POST) or remove vote (DELETE)"""
        instance = self.get_object()
        
        if request.method == 'POST':
            # Cannot vote on own response
            if instance.author == request.user:
                return Response(
                    {'error': 'Cannot vote on your own response'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            vote_type = request.data.get('vote_type')
            if vote_type not in ['upvote', 'downvote']:
                return Response(
                    {'error': 'Invalid vote type'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            vote, created = ResponseRepository.vote_response(
                instance, request.user, vote_type
            )
            
            # Refresh instance to get updated counts
            instance.refresh_from_db()
            
            # Check for upvote notification threshold
            if vote_type == 'upvote':
                NotificationRepository.create_upvote_notification(instance)
            
            return Response({
                'response_id': str(instance.id),
                'vote_type': vote_type,
                'upvotes': instance.upvotes,
                'downvotes': instance.downvotes
            })
        
        elif request.method == 'DELETE':
            # Remove vote
            success = ResponseRepository.remove_vote(instance, request.user)
            
            if success:
                instance.refresh_from_db()
                return Response({
                    'response_id': str(instance.id),
                    'upvotes': instance.upvotes,
                    'downvotes': instance.downvotes
                })
            
            return Response(
                {'error': 'No vote found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """Mark response as helpful (request author only)"""
        instance = self.get_object()
        
        # Only request author can mark as helpful
        if instance.request.author != request.user:
            return Response(
                {'error': 'Only request author can mark responses as helpful'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        success = ResponseRepository.mark_response_helpful(instance, request.user)
        
        if success:
            # Create notification
            NotificationRepository.create_helpful_notification(instance)
            
            return Response({
                'response_id': str(instance.id),
                'is_marked_helpful': True,
                'marked_helpful_at': instance.marked_helpful_at
            })
        
        return Response(
            {'error': 'Response already marked as helpful'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ResponseReplyViewSet(viewsets.ModelViewSet):
    """ViewSet for response replies/follow-ups"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ResponseReplySerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        response_id = self.request.query_params.get('response_id')
        if response_id:
            # Return top-level replies only (parent_reply is null)
            # Nested replies are included via serializer
            return ResponseReply.objects.filter(
                response_id=response_id,
                parent_reply__isnull=True,
                is_deleted=False
            ).order_by('created_at')
        
        # For detail actions (retrieve, update, delete)
        return ResponseReply.objects.filter(is_deleted=False)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ResponseReplyCreateSerializer
        return ResponseReplySerializer
    
    def perform_create(self, serializer):
        """Create new reply"""
        serializer.save(author=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Update reply - only within 15 minutes"""
        instance = self.get_object()
        
        # Check ownership
        if instance.author != request.user:
            return Response(
                {'error': 'You can only edit your own replies'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check time limit (15 minutes)
        time_diff = timezone.now() - instance.created_at
        if time_diff.total_seconds() > 900:  # 15 minutes
            return Response(
                {'error': 'Can only edit replies within 15 minutes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete reply"""
        instance = self.get_object()
        
        if instance.author != request.user:
            return Response(
                {'error': 'You can only delete your own replies'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])
        
        # Update response follow_up_count
        instance.response.follow_up_count -= 1
        instance.response.save(update_fields=['follow_up_count'])
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class BookmarkViewSet(viewsets.ModelViewSet):
    """ViewSet for bookmarks"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RequestBookmarkSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return HelpDeskRepository.get_bookmarked_requests(self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """Remove bookmark by request_id"""
        request_id = kwargs.get('pk')
        bookmark = get_object_or_404(
            RequestBookmark,
            request_id=request_id,
            user=request.user
        )
        bookmark.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for notifications"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = HelpDeskNotificationSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        unread_only = self.request.query_params.get('unread') == 'true'
        return HelpDeskRepository.get_user_notifications(
            self.request.user, unread_only
        )
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        HelpDeskRepository.mark_notifications_read(request.user)
        return Response({'message': 'All notifications marked as read'})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark single notification as read"""
        instance = self.get_object()
        instance.is_read = True
        instance.read_at = timezone.now()
        instance.save(update_fields=['is_read', 'read_at'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """Mark single notification as read (alternative method via PATCH)"""
        instance = self.get_object()
        instance.is_read = True
        instance.read_at = timezone.now()
        instance.save(update_fields=['is_read', 'read_at'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet for content reports"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ContentReportSerializer
    http_method_names = ['post']  # Only allow creating reports
    
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)


class StatsView(viewsets.ViewSet):
    """ViewSet for statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user stats"""
        stats = HelpDeskRepository.get_user_stats(request.user)
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def global_stats(self, request):
        """Get global system stats"""
        stats = HelpDeskRepository.get_global_stats()
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def trending_tags(self, request):
        """Get trending tags based on recent usage"""
        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 10))
        
        trending = HelpDeskRepository.get_trending_tags(days=days, limit=limit)
        return Response(trending)

