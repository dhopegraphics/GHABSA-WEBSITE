"""
Views for Voting System API
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, BasePermission
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
import hashlib


def generate_server_fingerprint(request):
    """
    Generate a reliable fingerprint server-side from request headers.
    This is more reliable than client-side fingerprinting on mobile devices.
    
    Combines:
    - User-Agent (browser/device info)
    - Accept-Language (user's language preferences)
    - Accept-Encoding (browser capabilities)
    - IP Address (network identifier)
    
    Returns a 32-character hex string.
    """
    components = [
        request.META.get('HTTP_USER_AGENT', 'unknown'),
        request.META.get('HTTP_ACCEPT_LANGUAGE', 'unknown'),
        request.META.get('HTTP_ACCEPT_ENCODING', 'unknown'),
    ]
    
    # Get client IP (handle proxies)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0].strip()
    else:
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    components.append(ip_address)
    
    # Create deterministic hash
    fingerprint_str = '|'.join(str(c) for c in components)
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]


def get_client_ip(request):
    """Extract client IP address from request, handling proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class IsAuthenticatedOrPublicEvent(BasePermission):
    """
    Custom permission: Allow access if user is authenticated OR event is public.
    For voting and payment endpoints, check if the event allows public participation.
    """
    def has_permission(self, request, view):
        # Always allow authenticated users
        if request.user and request.user.is_authenticated:
            return True
        
        # For anonymous users, check if it's a safe method (GET, HEAD, OPTIONS)
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # For POST requests (voting/payment), check event accessibility
        # This will be further validated in the serializer/view
        return True  # Allow the request, validation happens in serializer
    
    def has_object_permission(self, request, view, obj):
        # Authenticated users always have access
        if request.user and request.user.is_authenticated:
            return True
        
        # For anonymous users, check if object (event) is public
        if hasattr(obj, 'visibility'):
            return obj.visibility == 'public'
        
        return False

from .models import (
    VotingEvent, VotingCategory, Candidate, Vote,
    VoterEligibility, VotingPayment, VotingResult, PollOption
)
from .serializers import (
    VotingEventListSerializer, VotingEventDetailSerializer,
    VotingCategorySerializer, CandidateSerializer, CandidateListSerializer,
    VoteSerializer, VotingPaymentSerializer, VotingResultSerializer,
    VoterEligibilitySerializer, CandidateRegistrationSerializer,
    PollOptionSerializer, PollOptionListSerializer
)


class VotingEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing voting events
    
    list: Get all voting events
    retrieve: Get a specific voting event with categories and candidates
    """
    queryset = VotingEvent.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'status', 'visibility', 'requires_payment']
    search_fields = ['title', 'description']
    ordering_fields = ['voting_start_date', 'voting_end_date', 'created_at']
    ordering = ['-voting_start_date']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VotingEventDetailSerializer
        return VotingEventListSerializer
    
    def get_queryset(self):
        """
        Filter events based on user eligibility.
        
        For listing (list action): Show all events so users can see what's available
        and know they need to log in to participate in restricted events.
        
        For detail view (retrieve action): Show all events (not draft) and let
        retrieve() handle permission checks with proper error messages.
        """
        queryset = super().get_queryset()
        
        # Show all events in the list view so users can see what's available
        # The frontend will display login requirements based on requires_authentication
        # and visibility fields. Actions like voting/registering are protected separately.
        if self.action == 'list':
            # Filter out draft events - show all others
            return queryset.exclude(status='draft')
        
        # For detail view and other actions, show all non-draft events
        # Permission checks will handle access control with proper error messages
        return queryset.exclude(status='draft')
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single voting event with proper permission handling.
        Returns 403 with helpful message for visibility-restricted events.
        """
        instance = self.get_object()
        
        # Check visibility permissions
        visibility_error = self._check_event_visibility(request, instance)
        if visibility_error:
            return visibility_error
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def _check_event_visibility(self, request, event):
        """
        Helper to check if user has access to the event based on visibility.
        Returns a Response with error if access denied, or None if access granted.
        """
        user = request.user
        
        if not user.is_authenticated:
            if event.visibility != 'public':
                return Response({
                    'detail': 'Authentication required to access this event.',
                    'visibility': event.visibility,
                    'requires_login': True
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            # For year-specific events
            if event.visibility == 'year' and event.eligible_years:
                user_year = getattr(user, 'year', None) or getattr(user, 'level', None)
                if user_year and int(user_year) not in [int(y) for y in event.eligible_years]:
                    return Response({
                        'detail': f'This event is restricted to Year {", ".join(map(str, event.eligible_years))} students.',
                        'visibility': event.visibility,
                        'eligible_years': event.eligible_years,
                        'your_year': user_year
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # For program-specific events
            if event.visibility == 'program' and event.eligible_programs:
                user_program = getattr(user, 'program', None) or getattr(user, 'department', None)
                if user_program and user_program.lower() not in [p.lower() for p in event.eligible_programs]:
                    return Response({
                        'detail': 'This event is restricted to specific programs.',
                        'visibility': event.visibility,
                        'eligible_programs': event.eligible_programs,
                        'your_program': user_program
                    }, status=status.HTTP_403_FORBIDDEN)
        
        return None  # Access granted
    
    @action(detail=True, methods=['get'])
    def candidates(self, request, slug=None):
        """Get all approved candidates for an event (elections/awards only)"""
        event = self.get_object()
        
        # Check visibility permissions
        visibility_error = self._check_event_visibility(request, event)
        if visibility_error:
            return visibility_error
        
        # For poll events, return empty or redirect to poll_options
        if event.event_type in ['poll', 'referendum']:
            return Response({
                'message': 'This is a poll/referendum event. Use poll_options endpoint instead.',
                'poll_options_url': f'/api/voting/events/{event.slug}/poll_options/'
            })
        
        candidates = Candidate.objects.filter(
            event=event,
            status='approved'
        ).select_related('category', 'user_account')
        
        # Group by category if event has categories
        if event.categories.exists():
            serializer = CandidateListSerializer(candidates, many=True)
            # Group results by category
            grouped = {}
            for candidate_data in serializer.data:
                cat_name = candidate_data.get('category_name', 'Uncategorized')
                if cat_name not in grouped:
                    grouped[cat_name] = []
                grouped[cat_name].append(candidate_data)
            
            return Response(grouped)
        else:
            serializer = CandidateListSerializer(candidates, many=True)
            return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def poll_options(self, request, slug=None):
        """Get all poll options for a poll/referendum event"""
        event = self.get_object()
        
        # Check visibility permissions
        visibility_error = self._check_event_visibility(request, event)
        if visibility_error:
            return visibility_error
        
        # Validate event type
        if event.event_type not in ['poll', 'referendum']:
            return Response({
                'message': 'This is not a poll/referendum event. Use candidates endpoint instead.',
                'candidates_url': f'/api/voting/events/{event.slug}/candidates/'
            })
        
        # Get poll options
        options = PollOption.objects.filter(event=event).select_related('category')
        
        # Group by category if event has categories (multi-question poll)
        if event.categories.exists():
            grouped = {}
            for category in event.categories.all():
                category_options = options.filter(category=category)
                serializer = PollOptionListSerializer(category_options, many=True)
                grouped[category.name] = {
                    'category_id': str(category.id),
                    'question': category.name,
                    'description': category.description,
                    'options': serializer.data
                }
            return Response(grouped)
        else:
            # Single-question poll
            serializer = PollOptionListSerializer(options, many=True)
            return Response({
                'question': event.title,
                'description': event.description,
                'options': serializer.data
            })
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def my_eligibility(self, request, slug=None):
        """Check user's eligibility for an event"""
        event = self.get_object()
        user = request.user
        
        eligibility, created = VoterEligibility.objects.get_or_create(
            event=event,
            user=user,
            defaults={
                'is_eligible': event.can_user_participate(user),
                'payment_required': event.requires_payment
            }
        )
        
        serializer = VoterEligibilitySerializer(eligibility)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def results(self, request, slug=None):
        """Get results for an event (supports both elections and polls)"""
        event = self.get_object()
        
        # First, check if there are any published VotingResult records
        published_results = VotingResult.objects.filter(
            event=event,
            is_published=True
        ).select_related('category', 'winner')
        
        # If there are published results, return them
        if published_results.exists():
            serializer = VotingResultSerializer(published_results, many=True)
            return Response(serializer.data)
        
        # Check if there are unpublished VotingResult records
        # If results exist but are unpublished, don't show anything
        unpublished_results = VotingResult.objects.filter(
            event=event,
            is_published=False
        ).exists()
        
        if unpublished_results:
            return Response(
                {'detail': 'Results have been unpublished and are not available.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # No VotingResult records exist at all
        # Only show live calculated results if show_live_results is explicitly enabled
        # This allows admins to show live vote counts during an ongoing election
        if not event.show_live_results:
            return Response(
                {'detail': 'Results are not yet available. Results have not been published for this event.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Fallback: Calculate results on-the-fly from votes
        # This only happens if show_live_results is True AND no VotingResult records exist
        from django.db.models import Count
        
        live_results = []
        
        # Handle poll/referendum events differently
        if event.event_type in ['poll', 'referendum']:
            live_results = self._calculate_poll_results_live(event)
        else:
            live_results = self._calculate_election_results_live(event)
        
        return Response(live_results)
    
    def _calculate_poll_results_live(self, event):
        """Calculate live poll results"""
        from django.db.models import Count
        
        live_results = []
        
        # Calculate eligible voters if not set
        eligible_voters = event.total_eligible_voters
        if not eligible_voters or eligible_voters == 0:
            eligible_voters = event.calculate_eligible_voters()
            # Update the event for future requests
            event.total_eligible_voters = eligible_voters
            event.save(update_fields=['total_eligible_voters'])
        
        if event.categories.exists():
            # Multi-question poll
            for category in event.categories.all():
                options = category.poll_options.annotate(
                    total_votes_received=Count('votes_received')
                ).order_by('-total_votes_received')
                
                total_votes = sum(o.total_votes_received for o in options)
                
                option_results = []
                for option in options:
                    option_results.append({
                        'id': str(option.id),
                        'option_text': option.option_text,
                        'description': option.description,
                        'image': option.image.url if option.image else option.image_url,
                        'color': option.color,
                        'vote_count': option.total_votes_received,
                        'percentage': round(
                            (option.total_votes_received / total_votes * 100)
                            if total_votes > 0 else 0,
                            2
                        )
                    })
                
                winning_option = options.first() if options.exists() else None
                
                live_results.append({
                    'id': str(category.id),
                    'event': str(event.id),
                    'event_title': event.title,
                    'category': str(category.id),
                    'category_name': category.name,
                    'winner': None,  # Polls don't have candidate winners
                    'winner_details': None,
                    'total_votes_cast': total_votes,
                    'total_eligible_voters': eligible_voters,
                    'voter_turnout_percentage': round(
                        (total_votes / eligible_voters * 100)
                        if eligible_voters > 0 else 0,
                        2
                    ),
                    'detailed_results': {
                        'type': 'poll',
                        'question': category.name,
                        'options': option_results,
                        'winning_option': option_results[0] if option_results else None
                    },
                    'is_published': event.status == 'results_published',
                    'published_date': None
                })
        else:
            # Single-question poll
            options = event.poll_options.annotate(
                total_votes_received=Count('votes_received')
            ).order_by('-total_votes_received')
            
            total_votes = sum(o.total_votes_received for o in options)
            
            option_results = []
            for option in options:
                option_results.append({
                    'id': str(option.id),
                    'option_text': option.option_text,
                    'description': option.description,
                    'image': option.image.url if option.image else option.image_url,
                    'color': option.color,
                    'vote_count': option.total_votes_received,
                    'percentage': round(
                        (option.total_votes_received / total_votes * 100)
                        if total_votes > 0 else 0,
                        2
                    )
                })
            
            live_results.append({
                'id': str(event.id),
                'event': str(event.id),
                'event_title': event.title,
                'category': None,
                'category_name': event.title,
                'winner': None,
                'winner_details': None,
                'total_votes_cast': total_votes,
                'total_eligible_voters': eligible_voters,
                'voter_turnout_percentage': round(
                    (total_votes / eligible_voters * 100)
                    if eligible_voters > 0 else 0,
                    2
                ),
                'detailed_results': {
                    'type': 'poll',
                    'question': event.title,
                    'options': option_results,
                    'winning_option': option_results[0] if option_results else None
                },
                'is_published': event.status == 'results_published',
                'published_date': None
            })
        
        return live_results
    
    def _calculate_election_results_live(self, event):
        """Calculate live election/awards results"""
        from django.db.models import Count
        
        live_results = []
        
        # Calculate eligible voters if not set
        eligible_voters = event.total_eligible_voters
        if not eligible_voters or eligible_voters == 0:
            eligible_voters = event.calculate_eligible_voters()
            # Update the event for future requests
            event.total_eligible_voters = eligible_voters
            event.save(update_fields=['total_eligible_voters'])
        
        # Check if event has categories
        if event.categories.exists():
            for category in event.categories.all():
                candidates = category.candidates.filter(
                    status='approved'
                ).annotate(
                    total_votes_received=Count('votes_received')
                ).order_by('-total_votes_received')
                
                winner = candidates.first() if candidates.exists() else None
                total_votes = sum(c.total_votes_received for c in candidates)
                
                candidate_results = []
                for candidate in candidates:
                    candidate_results.append({
                        'candidate_id': str(candidate.id),
                        'id': str(candidate.id),
                        'candidate_name': candidate.candidate_name,
                        'name': candidate.candidate_name,
                        'photo': candidate.profile_image.url if candidate.profile_image else None,
                        'profile_image': candidate.profile_image.url if candidate.profile_image else None,
                        'vote_count': candidate.total_votes_received,
                        'votes': candidate.total_votes_received,
                        'percentage': round(
                            (candidate.total_votes_received / total_votes * 100)
                            if total_votes > 0 else 0,
                            2
                        )
                    })
                
                live_results.append({
                    'id': str(category.id),
                    'event': str(event.id),
                    'event_title': event.title,
                    'category': str(category.id),
                    'category_name': category.name,
                    'winner': str(winner.id) if winner else None,
                    'winner_details': {
                        'id': str(winner.id),
                        'candidate_name': winner.candidate_name,
                        'display_name': winner.candidate_name,
                        'photo': winner.profile_image.url if winner.profile_image else None,
                        'profile_image': winner.profile_image.url if winner.profile_image else None,
                        'vote_count': winner.total_votes_received if winner else 0
                    } if winner else None,
                    'total_votes_cast': total_votes,
                    'total_eligible_voters': eligible_voters,
                    'voter_turnout_percentage': round(
                        (total_votes / eligible_voters * 100)
                        if eligible_voters > 0 else 0,
                        2
                    ),
                    'detailed_results': {
                        'type': 'election',
                        'candidates': candidate_results
                    },
                    'is_published': event.status == 'results_published',
                    'published_date': None
                })
        else:
            # Single-category event (no explicit categories)
            candidates = event.candidates.filter(
                status='approved'
            ).annotate(
                total_votes_received=Count('votes_received')
            ).order_by('-total_votes_received')
            
            if candidates.exists():
                winner = candidates.first()
                total_votes = sum(c.total_votes_received for c in candidates)
                
                candidate_results = []
                for candidate in candidates:
                    candidate_results.append({
                        'candidate_id': str(candidate.id),
                        'id': str(candidate.id),
                        'candidate_name': candidate.candidate_name,
                        'name': candidate.candidate_name,
                        'photo': candidate.profile_image.url if candidate.profile_image else None,
                        'profile_image': candidate.profile_image.url if candidate.profile_image else None,
                        'vote_count': candidate.total_votes_received,
                        'votes': candidate.total_votes_received,
                        'percentage': round(
                            (candidate.total_votes_received / total_votes * 100)
                            if total_votes > 0 else 0,
                            2
                        )
                    })
                
                live_results.append({
                    'id': str(event.id),
                    'event': str(event.id),
                    'event_title': event.title,
                    'category': None,
                    'category_name': event.title,  # Use event title as category name
                    'winner': str(winner.id) if winner else None,
                    'winner_details': {
                        'id': str(winner.id),
                        'candidate_name': winner.candidate_name,
                        'display_name': winner.candidate_name,
                        'photo': winner.profile_image.url if winner.profile_image else None,
                        'profile_image': winner.profile_image.url if winner.profile_image else None,
                        'vote_count': winner.total_votes_received if winner else 0
                    } if winner else None,
                    'total_votes_cast': total_votes,
                    'total_eligible_voters': eligible_voters,
                    'voter_turnout_percentage': round(
                        (total_votes / eligible_voters * 100)
                        if eligible_voters > 0 else 0,
                        2
                    ),
                    'detailed_results': {
                        'type': 'election',
                        'candidates': candidate_results
                    },
                    'is_published': event.status == 'results_published',
                    'published_date': None
                })
        
        return live_results
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, slug=None):
        """Get event statistics"""
        event = self.get_object()
        
        # Calculate eligible voters if not set
        eligible_voters = event.total_eligible_voters
        if not eligible_voters or eligible_voters == 0:
            eligible_voters = event.calculate_eligible_voters()
            # Update the event for future requests
            event.total_eligible_voters = eligible_voters
            event.save(update_fields=['total_eligible_voters'])
        
        stats = {
            'event': event.title,
            'total_eligible_voters': eligible_voters,
            'total_votes_cast': event.total_votes_cast,
            'total_registered_candidates': event.total_registered_candidates,
            'voter_turnout': round(
                (event.total_votes_cast / eligible_voters * 100)
                if eligible_voters > 0 else 0,
                2
            ),
            'by_category': []
        }
        
        # Stats by category
        categories = event.categories.all()
        for category in categories:
            stats['by_category'].append({
                'category': category.name,
                'total_candidates': category.total_candidates,
                'total_votes': category.total_votes
            })
        
        return Response(stats)


class CandidateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing candidates
    
    list: Get all candidates
    retrieve: Get a specific candidate
    register: Self-register as a candidate
    """
    queryset = Candidate.objects.filter(status='approved')
    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event', 'category', 'program', 'year', 'status']
    search_fields = ['candidate_name', 'bio', 'candidate_id']
    ordering_fields = ['vote_count', 'candidate_name', 'registration_date']
    ordering = ['-vote_count']
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def register(self, request):
        """Self-register as a candidate"""
        serializer = CandidateRegistrationSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {
                'detail': 'Registration submitted successfully. Awaiting approval.',
                'candidate': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_candidacies(self, request):
        """Get all candidacies for the current user"""
        candidacies = Candidate.objects.filter(user_account=request.user)
        serializer = CandidateSerializer(candidacies, many=True)
        return Response(serializer.data)


class VoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for voting
    
    create: Cast a vote (supports both authenticated and anonymous users for public events)
    list: Get user's voting history (requires authentication)
    """
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = [IsAuthenticatedOrPublicEvent]
    http_method_names = ['get', 'post', 'head', 'options']
    
    def get_queryset(self):
        """Users can only see their own votes. Anonymous users see nothing."""
        if self.request.user and self.request.user.is_authenticated:
            return Vote.objects.filter(voter=self.request.user)
        return Vote.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Cast a vote"""
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {
                'detail': 'Vote cast successfully!',
                'vote': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def my_votes(self, request):
        """Get all votes cast by current user"""
        votes = self.get_queryset().select_related('event', 'category', 'candidate', 'poll_option')
        serializer = self.get_serializer(votes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_vote(self, request):
        """Cast multiple votes at once (for events with multiple categories)"""
        votes_data = request.data.get('votes', [])
        
        if not votes_data:
            return Response(
                {'detail': 'No votes provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_votes = []
        errors = []
        
        for vote_data in votes_data:
            serializer = self.get_serializer(
                data=vote_data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                created_votes.append(serializer.data)
            else:
                errors.append({
                    'vote_data': vote_data,
                    'errors': serializer.errors
                })
        
        return Response(
            {
                'detail': f'{len(created_votes)} vote(s) cast successfully.',
                'votes': created_votes,
                'errors': errors
            },
            status=status.HTTP_201_CREATED if created_votes else status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def check_anonymous_vote(self, request):
        """
        Check if a user (anonymous or authenticated) has already voted in an event.
        Uses comprehensive cross-referencing of fingerprints, IP, session, and user account.
        
        This is a ROBUST check that catches:
        - Anonymous vote then login attempt
        - Login vote then anonymous attempt  
        - Vote on phone then PC (same IP/network)
        - Clear history and vote again
        
        Request body:
        - event_slug: The event slug to check
        - device_fingerprint: The client device fingerprint
        - session_id: Optional session ID
        """
        event_slug = request.data.get('event_slug')
        client_fingerprint = request.data.get('device_fingerprint', '')
        session_id = request.data.get('session_id', '')
        
        if not event_slug:
            return Response(
                {'detail': 'Event slug is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the event
        try:
            event = VotingEvent.objects.get(slug=event_slug)
        except VotingEvent.DoesNotExist:
            return Response(
                {'detail': 'Event not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate server-side fingerprint for more reliable checking
        server_fingerprint = generate_server_fingerprint(request)
        ip_address = get_client_ip(request)
        
        # Combine client and server fingerprints (same logic as vote creation)
        if client_fingerprint:
            combined_fingerprint = f"{server_fingerprint}_{client_fingerprint[:16]}"
        else:
            combined_fingerprint = server_fingerprint
        
        # ========================================
        # COMPREHENSIVE VOTE CHECK
        # ========================================
        # Check ALL votes (not just anonymous) to prevent:
        # 1. Anonymous vote then login to vote again
        # 2. Login vote then logout to vote anonymously
        
        from django.db.models import Q
        
        # Start with ALL votes for this event
        all_votes = Vote.objects.filter(event=event)
        
        has_voted = False
        voted_categories = []
        matched_by = None
        vote_type = None  # 'anonymous' or 'authenticated'
        
        # Build comprehensive identifier filter
        identifier_filter = Q()
        
        # Check by combined fingerprint
        if combined_fingerprint:
            identifier_filter |= Q(device_fingerprint=combined_fingerprint)
        
        # Check by server fingerprint prefix
        if server_fingerprint:
            identifier_filter |= Q(device_fingerprint__startswith=server_fingerprint)
        
        # Check by client fingerprint suffix
        if client_fingerprint:
            identifier_filter |= Q(device_fingerprint__endswith=client_fingerprint[:16])
        
        # Check by session_id
        if session_id:
            identifier_filter |= Q(session_id=session_id)
        
        # Check by IP address
        if ip_address:
            identifier_filter |= Q(ip_address=ip_address)
        
        # Check by authenticated user (if logged in)
        if request.user.is_authenticated:
            identifier_filter |= Q(voter=request.user)
        
        # Apply filter and check for existing votes
        if identifier_filter:
            matching_votes = all_votes.filter(identifier_filter)
            
            if matching_votes.exists():
                has_voted = True
                voted_categories = list(matching_votes.values_list('category__name', flat=True))
                
                # Determine what matched
                first_match = matching_votes.first()
                vote_type = 'authenticated' if first_match.voter else 'anonymous'
                
                # Determine match reason for debugging
                if first_match.voter and request.user.is_authenticated and first_match.voter == request.user:
                    matched_by = 'user_account'
                elif first_match.device_fingerprint == combined_fingerprint:
                    matched_by = 'combined_fingerprint'
                elif server_fingerprint and first_match.device_fingerprint.startswith(server_fingerprint):
                    matched_by = 'server_fingerprint'
                elif first_match.session_id == session_id:
                    matched_by = 'session_id'
                elif first_match.ip_address == ip_address:
                    matched_by = 'ip_address'
                else:
                    matched_by = 'identifier_match'
        
        # Filter out None values from categories (for events without categories)
        voted_categories = [c for c in voted_categories if c is not None]
        
        # Generate user-friendly reason message
        reason_message = None
        if has_voted:
            if matched_by == 'user_account':
                reason_message = "Your account has already voted in this event."
            elif matched_by == 'ip_address':
                reason_message = "A vote has already been cast from this network. Each network can only vote once."
            elif matched_by in ['combined_fingerprint', 'server_fingerprint']:
                reason_message = "This device has already been used to vote in this event."
            elif matched_by == 'session_id':
                reason_message = "This browser session has already been used to vote."
            else:
                reason_message = "A vote has already been detected from this device/network."
        
        return Response({
            'has_voted': has_voted,
            'voted_categories': list(set(voted_categories)),  # Remove duplicates
            'event_slug': event_slug,
            'matched_by': matched_by,
            'vote_type': vote_type,
            'reason': reason_message,
            'checked_by': {
                'fingerprint': bool(client_fingerprint),
                'server_fingerprint': bool(server_fingerprint),
                'session': bool(session_id),
                'ip': bool(ip_address),
                'user': request.user.is_authenticated
            }
        })

    @action(detail=False, methods=['post'], permission_classes=[])
    def batch_check_vote_status(self, request):
        """
        Check vote status for multiple events at once.
        This is called when VotingPage loads to pre-check all events.
        
        Request body:
        - event_slugs: List of event slugs to check (optional - if empty, checks all active events)
        - device_fingerprint: The client device fingerprint
        - session_id: Optional session ID
        
        Returns:
        {
            'voted_events': {
                'event-slug-1': {
                    'has_voted': True,
                    'reason': 'Your account has already voted...',
                    'voted_categories': ['President', 'VP']
                },
                ...
            }
        }
        """
        event_slugs = request.data.get('event_slugs', [])
        client_fingerprint = request.data.get('device_fingerprint', '')
        session_id = request.data.get('session_id', '')
        
        # Generate server-side fingerprint
        server_fingerprint = generate_server_fingerprint(request)
        ip_address = get_client_ip(request)
        
        # Combine client and server fingerprints
        if client_fingerprint:
            combined_fingerprint = f"{server_fingerprint}_{client_fingerprint[:16]}"
        else:
            combined_fingerprint = server_fingerprint
        
        # Get events to check - if no slugs provided, get all active/open events
        if event_slugs:
            events = VotingEvent.objects.filter(slug__in=event_slugs)
        else:
            # Get events that are currently active (voting open or recently closed)
            events = VotingEvent.objects.filter(
                status__in=['active', 'voting_open', 'voting_closed', 'results_published']
            )
        
        # Build identifier filter for finding matching votes
        identifier_filter = Q()
        
        if combined_fingerprint:
            identifier_filter |= Q(device_fingerprint=combined_fingerprint)
        
        if server_fingerprint:
            identifier_filter |= Q(device_fingerprint__startswith=server_fingerprint)
        
        if client_fingerprint:
            identifier_filter |= Q(device_fingerprint__endswith=client_fingerprint[:16])
        
        if session_id:
            identifier_filter |= Q(session_id=session_id)
        
        if ip_address:
            identifier_filter |= Q(ip_address=ip_address)
        
        if request.user.is_authenticated:
            identifier_filter |= Q(voter=request.user)
        
        # Query all matching votes in one go (efficient batch query)
        if identifier_filter:
            matching_votes = Vote.objects.filter(identifier_filter).filter(
                event__in=events
            ).select_related('event', 'category').values(
                'event__slug', 'category__name', 'voter', 'ip_address', 
                'device_fingerprint', 'session_id'
            )
        else:
            matching_votes = Vote.objects.none()
        
        # Group votes by event
        voted_events = {}
        for vote in matching_votes:
            event_slug = vote['event__slug']
            
            if event_slug not in voted_events:
                # Determine reason
                reason = None
                if vote['voter'] and request.user.is_authenticated:
                    reason = "Your account has already voted in this event."
                elif vote['ip_address'] == ip_address:
                    reason = "A vote has already been cast from this network."
                elif vote['device_fingerprint'] and (
                    vote['device_fingerprint'] == combined_fingerprint or
                    (server_fingerprint and vote['device_fingerprint'].startswith(server_fingerprint))
                ):
                    reason = "This device has already been used to vote."
                else:
                    reason = "A vote has already been detected from this device/network."
                
                voted_events[event_slug] = {
                    'has_voted': True,
                    'reason': reason,
                    'voted_categories': []
                }
            
            # Add category to list
            if vote['category__name']:
                if vote['category__name'] not in voted_events[event_slug]['voted_categories']:
                    voted_events[event_slug]['voted_categories'].append(vote['category__name'])
        
        return Response({
            'voted_events': voted_events,
            'checked_count': events.count(),
            'voted_count': len(voted_events)
        })


class VotingPaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for voting payments
    
    create: Submit payment information
    list: Get user's payment history
    """
    queryset = VotingPayment.objects.all()
    serializer_class = VotingPaymentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']
    
    def get_queryset(self):
        """Users can only see their own payments"""
        return VotingPayment.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Submit payment information"""
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {
                'detail': 'Payment submitted successfully. Awaiting verification.',
                'payment': serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class VotingCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing voting categories
    """
    queryset = VotingCategory.objects.all()
    serializer_class = VotingCategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event']
    ordering_fields = ['display_order', 'name']
    ordering = ['display_order']
    
    @action(detail=True, methods=['get'])
    def candidates(self, request, pk=None):
        """Get all approved candidates in a category"""
        category = self.get_object()
        candidates = Candidate.objects.filter(
            category=category,
            status='approved'
        ).order_by('-vote_count')
        
        serializer = CandidateListSerializer(candidates, many=True)
        return Response(serializer.data)


class VotingResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing published voting results
    """
    queryset = VotingResult.objects.filter(is_published=True)
    serializer_class = VotingResultSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event', 'category']
    ordering = ['-published_date']
