"""
Data Access Layer for HelpDesk
Optimized database queries with proper indexing and prefetching
"""
from django.db.models import Q, F, Count, Prefetch
from django.utils import timezone
from datetime import timedelta
from .models import (
    HelpDeskCategory, HelpDeskRequest, HelpDeskResponse,
    ResponseVote, RequestBookmark, RequestView, HelpDeskNotification
)


class HelpDeskRepository:
    """Repository for HelpDesk data access"""
    
    @staticmethod
    def get_active_requests(filters=None, order_by='-created_at'):
        """
        Get all active help requests with optimized queries
        """
        queryset = HelpDeskRequest.objects.filter(
            status='active',
            is_deleted=False
        ).select_related('category')
        
        # Apply filters
        if filters:
            if 'category' in filters:
                queryset = queryset.filter(category_id=filters['category'])
            if 'priority' in filters:
                queryset = queryset.filter(priority=filters['priority'])
            if 'search' in filters:
                search_term = filters['search']
                # Remove # prefix if searching for a tag
                tag_search = search_term.lstrip('#')
                
                # Use Q objects for complex OR queries
                # For tag search, we need to check if any tag in the array matches
                q_filter = Q(title__icontains=search_term) | Q(description__icontains=search_term)
                
                # For tag matching, get all requests and filter in Python (SQLite-compatible)
                # This is less efficient but works across all databases
                matching_ids = []
                if tag_search:
                    all_with_tags = HelpDeskRequest.objects.filter(
                        status='active',
                        is_deleted=False,
                        tags__isnull=False
                    ).exclude(tags=[]).values_list('id', 'tags')
                    
                    for req_id, tags in all_with_tags:
                        if tags and any(tag_search.lower() in tag.lower() for tag in tags):
                            matching_ids.append(req_id)
                
                if matching_ids:
                    q_filter |= Q(id__in=matching_ids)
                
                queryset = queryset.filter(q_filter)
            # Filter by answered/unanswered status
            if 'has_responses' in filters:
                if filters['has_responses'] == 'true':
                    queryset = queryset.filter(response_count__gt=0)
                elif filters['has_responses'] == 'false':
                    queryset = queryset.filter(response_count=0)
        
        # Apply ordering (skip if empty string is passed)
        if order_by:
            # Handle comma-separated ordering fields (e.g., "priority_rank,-created_at")
            ordering_fields = [field.strip() for field in order_by.split(',')]
            queryset = queryset.order_by(*ordering_fields)
        
        return queryset
    
    @staticmethod
    def get_request_detail(request_id, user=None):
        """
        Get request details with all related data
        """
        queryset = HelpDeskRequest.objects.select_related(
            'category'
        ).prefetch_related(
            'code_snippets',
            'images'
        )
        
        return queryset.get(id=request_id, is_deleted=False)
    
    @staticmethod
    def get_my_requests(user, status_filter=None):
        """
        Get user's own requests
        """
        queryset = HelpDeskRequest.objects.filter(
            author=user,
            is_deleted=False
        ).select_related('category')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def get_helping_requests(user):
        """
        Get requests where user has posted responses (excluding their own requests)
        """
        return HelpDeskRequest.objects.filter(
            responses__author=user,
            responses__is_deleted=False,
            is_deleted=False
        ).exclude(
            author=user  # Exclude requests created by the same user
        ).select_related('category').distinct().order_by('-created_at')
    
    @staticmethod
    def get_request_responses(request_id, order_by='-created_at'):
        """
        Get all responses for a request
        """
        return HelpDeskResponse.objects.filter(
            request_id=request_id,
            is_deleted=False
        ).prefetch_related(
            'code_snippets',
            'links'
        ).order_by(order_by)
    
    @staticmethod
    def get_bookmarked_requests(user):
        """
        Get user's bookmarked requests
        """
        return RequestBookmark.objects.filter(
            user=user
        ).select_related(
            'request',
            'request__category'
        ).order_by('-created_at')
    
    @staticmethod
    def track_request_view(request_obj, user, ip_address=None, user_agent=None):
        """
        Track request view (avoid duplicate views within 24 hours)
        """
        # Check if user already viewed in last 24 hours
        if user and user.is_authenticated:
            recent_view = RequestView.objects.filter(
                request=request_obj,
                user=user,
                viewed_at__gte=timezone.now() - timedelta(hours=24)
            ).exists()
            
            if not recent_view:
                # Create new view
                RequestView.objects.create(
                    request=request_obj,
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                # Increment view count using update() to avoid F() expression staying in memory
                HelpDeskRequest.objects.filter(pk=request_obj.pk).update(
                    view_count=F('view_count') + 1
                )
    
    @staticmethod
    def search_requests(query, filters=None):
        """
        Search requests by query string
        """
        queryset = HelpDeskRequest.objects.filter(
            status='active',
            is_deleted=False
        )
        
        # Search in title, description, tags, course
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__contains=[query]) |
                Q(course__icontains=query)
            )
        
        # Apply additional filters
        if filters:
            if 'category' in filters:
                queryset = queryset.filter(category_id=filters['category'])
            if 'priority' in filters:
                queryset = queryset.filter(priority=filters['priority'])
            if 'tags' in filters:
                tags = filters['tags'].split(',')
                for tag in tags:
                    queryset = queryset.filter(tags__contains=[tag.strip()])
        
        return queryset.select_related('category').order_by('-created_at')
    
    @staticmethod
    def get_trending_requests(days=7, limit=10):
        """
        Get trending requests based on views and responses
        """
        since_date = timezone.now() - timedelta(days=days)
        
        return HelpDeskRequest.objects.filter(
            status='active',
            is_deleted=False,
            created_at__gte=since_date
        ).select_related('category').order_by(
            '-view_count',
            '-response_count',
            '-created_at'
        )[:limit]
    
    @staticmethod
    def get_user_notifications(user, unread_only=False):
        """
        Get user's helpdesk notifications
        """
        queryset = HelpDeskNotification.objects.filter(
            user=user
        ).select_related('request', 'response')
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def mark_notifications_read(user, notification_ids=None):
        """
        Mark notifications as read
        """
        queryset = HelpDeskNotification.objects.filter(user=user, is_read=False)
        
        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)
        
        queryset.update(is_read=True, read_at=timezone.now())
    
    @staticmethod
    def get_user_stats(user):
        """
        Get user statistics
        """
        stats = {
            'requests_created': HelpDeskRequest.objects.filter(
                author=user,
                is_deleted=False
            ).count(),
            'requests_resolved': HelpDeskRequest.objects.filter(
                author=user,
                is_resolved=True,
                is_deleted=False
            ).count(),
            'responses_posted': HelpDeskResponse.objects.filter(
                author=user,
                is_deleted=False
            ).count(),
            'helpful_responses': HelpDeskResponse.objects.filter(
                author=user,
                is_marked_helpful=True,
                is_deleted=False
            ).count(),
            'total_upvotes': ResponseVote.objects.filter(
                response__author=user,
                vote_type='upvote'
            ).count(),
            'total_downvotes': ResponseVote.objects.filter(
                response__author=user,
                vote_type='downvote'
            ).count(),
            'bookmarks_count': RequestBookmark.objects.filter(user=user).count(),
        }
        
        return stats
    
    @staticmethod
    def get_global_stats():
        """
        Get global system statistics
        """
        today = timezone.now().date()
        
        stats = {
            'total_requests': HelpDeskRequest.objects.filter(
                is_deleted=False
            ).count(),
            'active_requests': HelpDeskRequest.objects.filter(
                status='active',
                is_deleted=False
            ).count(),
            'resolved_requests': HelpDeskRequest.objects.filter(
                is_resolved=True,
                is_deleted=False
            ).count(),
            'total_responses': HelpDeskResponse.objects.filter(
                is_deleted=False
            ).count(),
            'active_users_today': HelpDeskRequest.objects.filter(
                created_at__date=today
            ).values('author').distinct().count(),
        }
        
        return stats
    
    @staticmethod
    def get_trending_tags(days=30, limit=10):
        """
        Get trending tags based on usage in recent requests
        Returns list of tag strings sorted by frequency
        """
        from collections import Counter
        
        since_date = timezone.now() - timedelta(days=days)
        
        # Get all tags from recent requests
        requests = HelpDeskRequest.objects.filter(
            created_at__gte=since_date,
            is_deleted=False,
            tags__isnull=False
        ).exclude(tags=[]).values_list('tags', flat=True)
        
        # Flatten and count tags
        tag_counter = Counter()
        for tag_list in requests:
            if tag_list and isinstance(tag_list, list):
                # Normalize tags to lowercase for counting
                normalized_tags = [tag.strip() for tag in tag_list if tag and tag.strip()]
                tag_counter.update(normalized_tags)
        
        # Get top tags (most_common returns list sorted by frequency descending)
        top_tags = tag_counter.most_common(limit)
        
        # Only return tags that have at least 1 occurrence
        result = [{'tag': tag, 'count': count} for tag, count in top_tags if count > 0]
        
        return result


class ResponseRepository:
    """Repository for response-related queries"""
    
    @staticmethod
    def vote_response(response, user, vote_type):
        """
        Vote on a response (upvote or downvote)
        Returns: (vote_obj, created)
        """
        # Check if already voted
        vote, created = ResponseVote.objects.get_or_create(
            response=response,
            user=user,
            defaults={'vote_type': vote_type}
        )
        
        if not created and vote.vote_type != vote_type:
            # User is changing their vote
            old_vote = vote.vote_type
            vote.vote_type = vote_type
            vote.save()
            
            # Update response vote counts using update() to avoid F() expression staying in memory
            if old_vote == 'upvote':
                HelpDeskResponse.objects.filter(pk=response.pk).update(
                    upvotes=F('upvotes') - 1,
                    downvotes=F('downvotes') + 1
                )
            else:
                HelpDeskResponse.objects.filter(pk=response.pk).update(
                    upvotes=F('upvotes') + 1,
                    downvotes=F('downvotes') - 1
                )
            # Refresh to get updated values
            response.refresh_from_db(fields=['upvotes', 'downvotes'])
        
        elif created:
            # New vote - use update() to avoid F() expression staying in memory
            if vote_type == 'upvote':
                HelpDeskResponse.objects.filter(pk=response.pk).update(
                    upvotes=F('upvotes') + 1
                )
            else:
                HelpDeskResponse.objects.filter(pk=response.pk).update(
                    downvotes=F('downvotes') + 1
                )
            # Refresh to get updated values
            response.refresh_from_db(fields=['upvotes', 'downvotes'])
        
        return vote, created
    
    @staticmethod
    def remove_vote(response, user):
        """
        Remove a vote from a response
        """
        try:
            vote = ResponseVote.objects.get(response=response, user=user)
            
            # Update response vote counts using update() to avoid F() expression staying in memory
            if vote.vote_type == 'upvote':
                HelpDeskResponse.objects.filter(pk=response.pk).update(
                    upvotes=F('upvotes') - 1
                )
            else:
                HelpDeskResponse.objects.filter(pk=response.pk).update(
                    downvotes=F('downvotes') - 1
                )
            # Refresh to get updated values
            response.refresh_from_db(fields=['upvotes', 'downvotes'])
            
            vote.delete()
            return True
        except ResponseVote.DoesNotExist:
            return False
    
    @staticmethod
    def mark_response_helpful(response, request_author):
        """
        Mark a response as helpful (only by request author)
        """
        if response.request.author != request_author:
            return False
        
        if not response.is_marked_helpful:
            response.is_marked_helpful = True
            response.marked_helpful_at = timezone.now()
            response.save(update_fields=['is_marked_helpful', 'marked_helpful_at'])
            
            # Update request helpful count using update() to avoid F() expression staying in memory
            HelpDeskRequest.objects.filter(pk=response.request.pk).update(
                helpful_response_count=F('helpful_response_count') + 1
            )
            # Refresh the request object to get the updated value
            response.request.refresh_from_db(fields=['helpful_response_count'])
            
            return True
        
        return False


class NotificationRepository:
    """Repository for creating notifications"""
    
    @staticmethod
    def create_new_response_notification(response):
        """
        Create notification when someone responds to a request
        """
        # Don't notify if response author is same as request author
        if response.author != response.request.author:
            HelpDeskNotification.objects.create(
                user=response.request.author,
                notification_type='new_response',
                title='New response to your request',
                message=f"Someone responded to '{response.request.title}'",
                request=response.request,
                response=response
            )
    
    @staticmethod
    def create_helpful_notification(response):
        """
        Create notification when response is marked helpful
        """
        HelpDeskNotification.objects.create(
            user=response.author,
            notification_type='response_marked_helpful',
            title='Your response was marked helpful!',
            message=f"The request author found your response helpful",
            request=response.request,
            response=response
        )
    
    @staticmethod
    def create_upvote_notification(response, threshold=5):
        """
        Create notification when response reaches upvote threshold
        """
        if response.upvotes >= threshold and response.upvotes % threshold == 0:
            HelpDeskNotification.objects.create(
                user=response.author,
                notification_type='response_upvoted',
                title=f'Your response received {response.upvotes} upvotes',
                message=f"Your response is being well-received by the community",
                request=response.request,
                response=response
            )
    
    @staticmethod
    def create_resolved_notification(request):
        """
        Create notification when request is resolved
        """
        # Notify all responders
        responders = HelpDeskResponse.objects.filter(
            request=request,
            is_deleted=False
        ).values_list('author', flat=True).distinct()
        
        for responder_id in responders:
            if responder_id != request.author_id:
                HelpDeskNotification.objects.create(
                    user_id=responder_id,
                    notification_type='request_resolved',
                    title='Request you helped with was resolved',
                    message=f"'{request.title}' has been marked as resolved",
                    request=request
                )
