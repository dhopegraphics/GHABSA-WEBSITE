from django.shortcuts import render, get_object_or_404
from django.http import Http404
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal

from events.repositories import EventRepo, EventRSVPRepo, EventRegistrationRepo, SyncMemoRepo
from events.serializers import (
    EventSerializer, EventRSVPSerializer, EventRSVPCreateSerializer,
    EventRegistrationSerializer, EventRegistrationCreateSerializer,
    SyncMemoAlbumSerializer, SyncMemoPhotoSerializer, SyncMemoPhotoUploadSerializer,
    SyncMemoCommentSerializer,
    # Payment serializers
    EventPaymentPackageSerializer, EventPaymentPackageListSerializer,
    EventPaymentTransactionSerializer, InitializeEventPaymentSerializer,
    VerifyEventPaymentSerializer, EventPaymentRefundSerializer,
    RequestEventRefundSerializer
)
from events.models import (
    Event, EventRSVP, EventRegistration,
    SyncMemoAlbum, SyncMemoPhoto, SyncMemoComment, SyncMemoLike, SyncMemoCommentLike,
    EventPaymentPackage, EventPaymentTransaction, EventPaymentRefund
)

# Initialize repositories
event_repo = EventRepo
rsvp_repo = EventRSVPRepo
registration_repo = EventRegistrationRepo
sync_memo_repo = SyncMemoRepo


# ========== PAGINATION ==========

class StandardResultsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100


# ========== EVENT VIEWS ==========

class EventListView(ListAPIView):
    """
    List all events with optional filtering
    GET /api/v1/events/
    
    Query Parameters:
    - filter: "upcoming" | "past" | "my_events"
    - type: event type filter
    - search: search query
    """
    serializer_class = EventSerializer
    pagination_class = StandardResultsPagination
    permission_classes = [AllowAny]  # Allow unauthenticated access for website

    def get_queryset(self):
        # Get base queryset with optimal sorting for frontend display
        queryset = event_repo.get_all_events_sorted()
        
        # Filter parameter
        filter_type = self.request.query_params.get('filter', None)
        if filter_type == 'upcoming':
            queryset = event_repo.get_upcoming_events()
        elif filter_type == 'past':
            queryset = event_repo.get_past_events()
        elif filter_type == 'my_events':
            # Get events user has RSVP'd or registered for
            if self.request.user.is_authenticated:
                rsvp_events = event_repo.get_user_rsvp_events(self.request.user)
                reg_events = event_repo.get_user_registered_events(self.request.user)
                queryset = (rsvp_events | reg_events).distinct()
            else:
                # Return empty queryset if user is not authenticated
                queryset = queryset.none()
        
        # Event type filter
        event_type = self.request.query_params.get('type', None)
        if event_type and event_type != 'all':
            queryset = queryset.filter(event_type=event_type)
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(event_name__icontains=search) |
                Q(description__icontains=search) |
                Q(organised_by__icontains=search)
            )
        
        return queryset

    def get_serializer_context(self):
        return {"request": self.request}


class EventDetailView(RetrieveAPIView):
    """
    Get event details
    GET /api/v1/events/{event_id}/
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [AllowAny]
    lookup_field = 'event_id'
    lookup_url_kwarg = 'event_id'

    def get_serializer_context(self):
        return {"request": self.request}


# ========== RSVP VIEWS ==========

class EventRSVPView(APIView):
    """
    Create or update RSVP for an event
    POST /api/v1/events/{event_id}/rsvp/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        event = get_object_or_404(Event, event_id=event_id)
        
        # Check if event is in the past
        if event.is_past:
            return Response(
                {"error": "Cannot RSVP to past events"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if RSVP allowed
        if not event.allows_rsvp:
            return Response(
                {"error": "RSVP is not allowed for this event"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create RSVP
        rsvp, created = EventRSVP.objects.get_or_create(
            event=event,
            user=request.user,
            defaults={'status': request.data.get('status', 'attending')}
        )
        
        if not created:
            # Update existing RSVP
            serializer = EventRSVPCreateSerializer(rsvp, data=request.data, partial=True)
        else:
            serializer = EventRSVPCreateSerializer(rsvp, data=request.data)
        
        if serializer.is_valid():
            serializer.save(user=request.user, event=event)
            return Response({
                "success": True,
                "message": f"RSVP updated to '{rsvp.status}'",
                "rsvp": EventRSVPSerializer(rsvp).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventAttendeesView(ListAPIView):
    """
    Get event attendees
    GET /api/v1/events/{event_id}/attendees/
    """
    serializer_class = EventRSVPSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        event_id = self.kwargs['event_id']
        event = get_object_or_404(Event, event_id=event_id)
        
        rsvp_status = self.request.query_params.get('status', None)
        return rsvp_repo.get_event_attendees(event, status=rsvp_status)


# ========== REGISTRATION VIEWS ==========

class EventRegistrationView(CreateAPIView):
    """
    Register for an event
    POST /api/v1/events/{event_id}/register/
    
    For paid events:
    - Include 'payment_package' (UUID) in request body
    - Registration will be created with 'pending_payment' status
    - Use /api/v1/events/payments/initialize/ to start payment
    """
    serializer_class = EventRegistrationCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        event = get_object_or_404(Event, event_id=event_id)
        
        # Validate registration is allowed
        if not event.requires_registration:
            return Response(
                {"error": "This event does not require registration"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not event.is_registration_open:
            return Response(
                {"error": "Registration is closed for this event"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if event.is_full:
            return Response(
                {"error": "This event is full"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already registered
        existing = registration_repo.get_user_registration(event, request.user)
        if existing:
            return Response(
                {"error": "You are already registered for this event",
                 "registration": EventRegistrationSerializer(existing).data},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add event to request data for validation
        data = request.data.copy()
        data['event'] = event.event_id
        
        # Create registration
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            registration = serializer.save(user=request.user)
            
            response_data = {
                "success": True,
                "message": "Registration created successfully",
                "registration": EventRegistrationSerializer(registration).data
            }
            
            # Include payment info for paid events
            if event.requires_payment and registration.payment_status == 'pending':
                response_data["payment_required"] = True
                response_data["payment_info"] = {
                    "amount_due": str(registration.amount_due),
                    "currency": "GHS",
                    "package": registration.payment_package.name if registration.payment_package else None,
                    "message": "Please proceed to payment to complete your registration."
                }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventRegistrationsListView(ListAPIView):
    """
    Get registrations for an event (admin only)
    GET /api/v1/events/{event_id}/registrations/
    """
    serializer_class = EventRegistrationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        event_id = self.kwargs['event_id']
        event = get_object_or_404(Event, event_id=event_id)
        
        reg_status = self.request.query_params.get('status', None)
        return registration_repo.get_event_registrations(event, status=reg_status)


class UserRegistrationView(RetrieveAPIView):
    """
    Get or cancel user's registration for an event
    GET /events/{event_id}/my-registration/ - Get registration
    DELETE /events/{event_id}/my-registration/ - Cancel registration
    """
    serializer_class = EventRegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        event_id = self.kwargs['event_id']
        event = get_object_or_404(Event, event_id=event_id)
        registration = registration_repo.get_user_registration(event, self.request.user)
        
        if not registration:
            raise Http404("No registration found for this event")
        
        return registration
    
    def delete(self, request, event_id):
        """Cancel user's registration"""
        event = get_object_or_404(Event, event_id=event_id)
        registration = registration_repo.get_user_registration(event, request.user)
        
        if not registration:
            return Response(
                {"error": "No registration found for this event"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only allow cancellation if status is pending or pending_payment
        if registration.status not in ['pending', 'pending_payment']:
            return Response(
                {"error": "Cannot cancel confirmed registrations. Please request a refund instead."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete the registration
        registration.delete()
        
        return Response({
            "success": True,
            "message": "Registration cancelled successfully"
        }, status=status.HTTP_200_OK)


# ========== SYNC MEMO (PHOTO GALLERY) VIEWS ==========

class SyncMemoGalleryView(ListAPIView):
    """
    Get all photo albums
    GET /api/v1/events/sync-memo/albums/
    """
    serializer_class = SyncMemoAlbumSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        event_id = self.request.query_params.get('event_id', None)
        if event_id:
            return SyncMemoAlbum.objects.filter(event__event_id=event_id)
        return sync_memo_repo.get_live_albums()

    def get_serializer_context(self):
        return {"request": self.request}


class EventAlbumPhotosView(ListAPIView):
    """
    Get photos for an event album
    GET /api/v1/events/{event_id}/sync-memo/photos/
    """
    serializer_class = SyncMemoPhotoSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        event_id = self.kwargs['event_id']
        event = get_object_or_404(Event, event_id=event_id)
        
        # Get or create album
        album = sync_memo_repo.get_or_create_album(event)
        
        # Sorting
        sort = self.request.query_params.get('sort', 'latest')
        queryset = sync_memo_repo.get_album_photos(album)
        
        if sort == 'most_liked':
            queryset = queryset.order_by('-likes__count', '-created_at')
        elif sort == 'oldest':
            queryset = queryset.order_by('created_at')
        
        return queryset

    def get_serializer_context(self):
        return {"request": self.request}


class SyncMemoUploadView(CreateAPIView):
    """
    Upload photo to event album
    POST /api/v1/events/{event_id}/sync-memo/upload/
    """
    serializer_class = SyncMemoPhotoUploadSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        event = get_object_or_404(Event, event_id=event_id)
        
        # Check if event is past
        if event.is_past:
            return Response(
                {"error": "Cannot upload photos to past events"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if uploads allowed
        if not event.sync_memo_enabled:
            return Response(
                {"error": "Photo uploads are not enabled for this event"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create album
        album = sync_memo_repo.get_or_create_album(event)
        
        if not album.allow_uploads:
            return Response(
                {"error": "Photo uploads are closed for this event"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create photo
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            photo = serializer.save(
                album=album,
                uploaded_by=request.user,
                is_approved=not album.require_approval
            )
            
            return Response({
                "success": True,
                "message": "Photo uploaded successfully",
                "photo": SyncMemoPhotoSerializer(photo, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PhotoDetailView(RetrieveAPIView):
    """
    Get photo details
    GET /api/v1/events/sync-memo/photos/{photo_id}/
    """
    queryset = SyncMemoPhoto.objects.all()
    serializer_class = SyncMemoPhotoSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    lookup_url_kwarg = 'photo_id'

    def get_serializer_context(self):
        return {"request": self.request}


class PhotoLikeView(APIView):
    """
    Like/unlike a photo
    POST /api/v1/events/sync-memo/photos/{photo_id}/like/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, photo_id):
        photo = get_object_or_404(SyncMemoPhoto, id=photo_id)
        action = request.data.get('action', 'like')
        
        if action == 'like':
            like, created = SyncMemoLike.objects.get_or_create(
                photo=photo,
                user=request.user
            )
            message = "Photo liked" if created else "Already liked"
        elif action == 'unlike':
            deleted = SyncMemoLike.objects.filter(
                photo=photo,
                user=request.user
            ).delete()
            message = "Photo unliked" if deleted[0] > 0 else "Not liked"
        else:
            return Response(
                {"error": "Invalid action. Use 'like' or 'unlike'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            "success": True,
            "message": message,
            "likes_count": photo.like_count,
            "user_has_liked": action == 'like'
        }, status=status.HTTP_200_OK)


class PhotoCommentsView(ListAPIView):
    """
    Get comments for a photo
    GET /api/v1/events/sync-memo/photos/{photo_id}/comments/
    """
    serializer_class = SyncMemoCommentSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        photo_id = self.kwargs['photo_id']
        photo = get_object_or_404(SyncMemoPhoto, id=photo_id)
        return sync_memo_repo.get_photo_comments(photo)

    def get_serializer_context(self):
        return {"request": self.request}


class PhotoCommentCreateView(CreateAPIView):
    """
    Add comment to a photo
    POST /api/v1/events/sync-memo/photos/{photo_id}/comments/
    """
    serializer_class = SyncMemoCommentSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, photo_id):
        photo = get_object_or_404(SyncMemoPhoto, id=photo_id)
        
        # Check if comments allowed
        if not photo.album.allow_comments:
            return Response(
                {"error": "Comments are not allowed for this album"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(
                photo=photo,
                user=request.user
            )
            
            return Response({
                "success": True,
                "message": "Comment added",
                "comment": SyncMemoCommentSerializer(comment, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentLikeView(APIView):
    """
    Like/unlike a comment
    POST /api/v1/events/sync-memo/comments/{comment_id}/like/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(SyncMemoComment, id=comment_id)
        action = request.data.get('action', 'like')
        
        if action == 'like':
            like, created = SyncMemoCommentLike.objects.get_or_create(
                comment=comment,
                user=request.user
            )
            message = "Comment liked" if created else "Already liked"
        elif action == 'unlike':
            deleted = SyncMemoCommentLike.objects.filter(
                comment=comment,
                user=request.user
            ).delete()
            message = "Comment unliked" if deleted[0] > 0 else "Not liked"
        else:
            return Response(
                {"error": "Invalid action. Use 'like' or 'unlike'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            "success": True,
            "message": message,
            "likes_count": comment.like_count,
            "user_has_liked": action == 'like'
        }, status=status.HTTP_200_OK)


class SyncMemoStatsView(APIView):
    """
    Get Sync Memo statistics
    GET /api/v1/events/sync-memo/stats/
    
    Returns:
    - total_photos: Total number of approved photos
    - events_covered: Number of events with photos
    - contributors: Number of unique photo uploaders
    - total_likes: Total likes across all photos
    - total_comments: Total comments across all photos
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        from django.db.models import Count, Sum
        
        # Total approved photos
        total_photos = SyncMemoPhoto.objects.filter(is_approved=True).count()
        
        # Events with at least one photo
        events_covered = SyncMemoAlbum.objects.filter(
            photos__is_approved=True
        ).distinct().count()
        
        # Unique contributors (users who uploaded photos)
        contributors = SyncMemoPhoto.objects.filter(
            is_approved=True
        ).values('uploaded_by').distinct().count()
        
        # Total likes and comments
        total_likes = SyncMemoLike.objects.count()
        total_comments = SyncMemoComment.objects.count()
        
        # Format large numbers (e.g., 1200 -> "1.2k+")
        def format_count(count):
            if count >= 1000:
                return f"{count / 1000:.1f}k+"
            return str(count)
        
        return Response({
            "success": True,
            "stats": {
                "total_photos": total_photos,
                "total_photos_formatted": format_count(total_photos),
                "events_covered": events_covered,
                "events_covered_formatted": str(events_covered),
                "contributors": contributors,
                "contributors_formatted": format_count(contributors),
                "total_likes": total_likes,
                "total_likes_formatted": format_count(total_likes),
                "total_comments": total_comments,
                "total_comments_formatted": format_count(total_comments),
            }
        }, status=status.HTTP_200_OK)


# ========== EVENT PAYMENT VIEWS ==========

class EventPaymentPackagesView(ListAPIView):
    """
    Get available payment packages for an event
    GET /api/v1/events/{event_id}/packages/
    """
    serializer_class = EventPaymentPackageListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        event_id = self.kwargs['event_id']
        event = get_object_or_404(Event, event_id=event_id)
        
        # Only return active and available packages
        return event.payment_packages.filter(
            is_active=True
        ).order_by('display_order', 'price')


class EventPaymentPackageDetailView(RetrieveAPIView):
    """
    Get details of a specific payment package
    GET /api/v1/events/packages/{package_id}/
    """
    queryset = EventPaymentPackage.objects.all()
    serializer_class = EventPaymentPackageSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    lookup_url_kwarg = 'package_id'


class InitializeEventPaymentView(APIView):
    """
    Initialize payment for an event registration
    POST /api/v1/events/payments/initialize/
    
    Request Body:
    {
        "registration_id": "uuid",
        "amount": "50.00",  // Optional, defaults to full balance
        "payment_gateway": "paystack",  // Optional, defaults to paystack
        "callback_url": "https://..."  // Optional, for web redirects
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InitializeEventPaymentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        registration = serializer.validated_data['registration']
        amount = serializer.validated_data['amount']
        gateway = serializer.validated_data.get('payment_gateway', 'paystack')
        callback_url = serializer.validated_data.get('callback_url', '')
        
        # Verify ownership
        if registration.user != request.user:
            return Response(
                {"error": "You can only pay for your own registration"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Determine transaction type
        if registration.amount_paid == 0:
            if amount < registration.amount_due:
                transaction_type = 'partial_payment'
            else:
                transaction_type = 'payment'
        else:
            transaction_type = 'balance_payment'
        
        # Create transaction record
        transaction = EventPaymentTransaction.objects.create(
            event=registration.event,
            registration=registration,
            user=request.user,
            package=registration.payment_package,
            transaction_type=transaction_type,
            amount=amount,
            currency='GHS',
            payment_gateway=gateway,
            customer_email=registration.email,
            customer_phone=registration.phone or '',
            customer_name=registration.full_name,
            ip_address=self._get_client_ip(request),
            expires_at=timezone.now() + timezone.timedelta(hours=24),
            metadata={
                'registration_number': registration.registration_number,
                'event_name': registration.event.event_name,
                'package_name': registration.payment_package.name if registration.payment_package else None,
                'callback_url': callback_url
            }
        )
        
        # Initialize with payment gateway
        if gateway == 'paystack':
            payment_response = self._initialize_paystack(transaction, callback_url)
        elif gateway == 'flutterwave':
            payment_response = self._initialize_flutterwave(transaction, callback_url)
        else:
            payment_response = {
                'success': False,
                'message': f'Unsupported gateway: {gateway}'
            }
        
        if not payment_response.get('success'):
            transaction.status = 'failed'
            transaction.status_message = payment_response.get('message', 'Gateway initialization failed')
            transaction.save()
            return Response(
                {"error": payment_response.get('message', 'Payment initialization failed')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update transaction with gateway details
        transaction.authorization_url = payment_response.get('authorization_url', '')
        transaction.access_code = payment_response.get('access_code', '')
        transaction.gateway_reference = payment_response.get('reference', transaction.reference)
        transaction.status = 'pending'
        transaction.save()
        
        return Response({
            "success": True,
            "message": "Payment initialized successfully",
            "transaction": EventPaymentTransactionSerializer(transaction).data,
            "authorization_url": transaction.authorization_url,
            "access_code": transaction.access_code,
            "reference": transaction.reference
        }, status=status.HTTP_200_OK)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
    
    def _initialize_paystack(self, transaction, callback_url):
        """Initialize payment with Paystack"""
        import requests
        from django.conf import settings
        
        try:
            paystack_secret = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
            if not paystack_secret:
                return {'success': False, 'message': 'Paystack not configured'}
            
            # Amount in kobo (smallest currency unit)
            amount_kobo = int(transaction.amount * 100)
            
            payload = {
                'email': transaction.customer_email,
                'amount': amount_kobo,
                'reference': transaction.reference,
                'currency': 'GHS',
                'metadata': {
                    'event_id': str(transaction.event.event_id),
                    'registration_id': str(transaction.registration.id),
                    'registration_number': transaction.registration.registration_number,
                    'transaction_type': 'event_payment'
                }
            }
            
            if callback_url:
                payload['callback_url'] = callback_url
            
            headers = {
                'Authorization': f'Bearer {paystack_secret}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                'https://api.paystack.co/transaction/initialize',
                json=payload,
                headers=headers,
                timeout=30
            )
            
            data = response.json()
            
            if data.get('status'):
                return {
                    'success': True,
                    'authorization_url': data['data']['authorization_url'],
                    'access_code': data['data']['access_code'],
                    'reference': data['data']['reference']
                }
            else:
                return {
                    'success': False,
                    'message': data.get('message', 'Paystack error')
                }
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _initialize_flutterwave(self, transaction, callback_url):
        """Initialize payment with Flutterwave"""
        import requests
        from django.conf import settings
        
        try:
            flutterwave_secret = getattr(settings, 'FLUTTERWAVE_SECRET_KEY', None)
            if not flutterwave_secret:
                return {'success': False, 'message': 'Flutterwave not configured'}
            
            payload = {
                'tx_ref': transaction.reference,
                'amount': str(transaction.amount),
                'currency': 'GHS',
                'redirect_url': callback_url or '',
                'payment_options': 'card,mobilemoney',
                'customer': {
                    'email': transaction.customer_email,
                    'name': transaction.customer_name,
                    'phonenumber': transaction.customer_phone
                },
                'customizations': {
                    'title': f'{transaction.event.event_name} Registration',
                    'description': f'Payment for {transaction.registration.registration_number}'
                },
                'meta': {
                    'event_id': str(transaction.event.event_id),
                    'registration_id': str(transaction.registration.id),
                    'transaction_type': 'event_payment'
                }
            }
            
            headers = {
                'Authorization': f'Bearer {flutterwave_secret}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                'https://api.flutterwave.com/v3/payments',
                json=payload,
                headers=headers,
                timeout=30
            )
            
            data = response.json()
            
            if data.get('status') == 'success':
                return {
                    'success': True,
                    'authorization_url': data['data']['link'],
                    'reference': transaction.reference
                }
            else:
                return {
                    'success': False,
                    'message': data.get('message', 'Flutterwave error')
                }
        except Exception as e:
            return {'success': False, 'message': str(e)}


class VerifyEventPaymentView(APIView):
    """
    Verify a payment transaction
    POST /api/v1/events/payments/verify/
    
    Request Body:
    {
        "reference": "EVTPAY-ABC123XYZ"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyEventPaymentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        reference = serializer.validated_data['reference']
        transaction = get_object_or_404(EventPaymentTransaction, reference=reference)
        
        # Check ownership (allow admins to verify any)
        if transaction.user != request.user and not request.user.is_staff:
            return Response(
                {"error": "You can only verify your own transactions"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Skip if already verified as success
        if transaction.status == 'success' and transaction.verified:
            return Response({
                "success": True,
                "message": "Transaction already verified",
                "transaction": EventPaymentTransactionSerializer(transaction).data,
                "registration": EventRegistrationSerializer(transaction.registration).data
            }, status=status.HTTP_200_OK)
        
        # Verify with gateway
        if transaction.payment_gateway == 'paystack':
            verify_response = self._verify_paystack(transaction)
        elif transaction.payment_gateway == 'flutterwave':
            verify_response = self._verify_flutterwave(transaction)
        else:
            verify_response = {'success': False, 'message': 'Unknown gateway'}
        
        if verify_response.get('success'):
            # Update transaction
            transaction.status = 'success'
            transaction.verified = True
            transaction.verified_at = timezone.now()
            transaction.completed_at = timezone.now()
            transaction.payment_method = verify_response.get('payment_method', '')
            transaction.gateway_response = verify_response.get('gateway_data', {})
            transaction.gateway_fee = Decimal(str(verify_response.get('fees', 0)))
            transaction.net_amount = transaction.amount - transaction.gateway_fee
            transaction.save()
            
            return Response({
                "success": True,
                "message": "Payment verified successfully",
                "transaction": EventPaymentTransactionSerializer(transaction).data,
                "registration": EventRegistrationSerializer(transaction.registration).data
            }, status=status.HTTP_200_OK)
        else:
            transaction.status = verify_response.get('status', 'failed')
            transaction.status_message = verify_response.get('message', '')
            transaction.verified = True
            transaction.verified_at = timezone.now()
            transaction.save()
            
            return Response({
                "success": False,
                "message": verify_response.get('message', 'Payment verification failed'),
                "transaction": EventPaymentTransactionSerializer(transaction).data
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _verify_paystack(self, transaction):
        """Verify transaction with Paystack"""
        import requests
        from django.conf import settings
        
        try:
            paystack_secret = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
            if not paystack_secret:
                return {'success': False, 'message': 'Paystack not configured'}
            
            headers = {
                'Authorization': f'Bearer {paystack_secret}',
            }
            
            response = requests.get(
                f'https://api.paystack.co/transaction/verify/{transaction.reference}',
                headers=headers,
                timeout=30
            )
            
            data = response.json()
            
            if data.get('status') and data.get('data', {}).get('status') == 'success':
                payment_data = data['data']
                return {
                    'success': True,
                    'payment_method': payment_data.get('channel', ''),
                    'fees': payment_data.get('fees', 0) / 100,  # Convert from kobo
                    'gateway_data': payment_data
                }
            else:
                status_value = data.get('data', {}).get('status', 'failed')
                return {
                    'success': False,
                    'status': status_value,
                    'message': data.get('message', f'Payment {status_value}')
                }
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _verify_flutterwave(self, transaction):
        """Verify transaction with Flutterwave"""
        import requests
        from django.conf import settings
        
        try:
            flutterwave_secret = getattr(settings, 'FLUTTERWAVE_SECRET_KEY', None)
            if not flutterwave_secret:
                return {'success': False, 'message': 'Flutterwave not configured'}
            
            headers = {
                'Authorization': f'Bearer {flutterwave_secret}',
            }
            
            # First get transaction ID
            response = requests.get(
                f'https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref={transaction.reference}',
                headers=headers,
                timeout=30
            )
            
            data = response.json()
            
            if data.get('status') == 'success' and data.get('data', {}).get('status') == 'successful':
                payment_data = data['data']
                return {
                    'success': True,
                    'payment_method': payment_data.get('payment_type', ''),
                    'fees': payment_data.get('app_fee', 0),
                    'gateway_data': payment_data
                }
            else:
                status_value = data.get('data', {}).get('status', 'failed')
                return {
                    'success': False,
                    'status': status_value,
                    'message': data.get('message', f'Payment {status_value}')
                }
        except Exception as e:
            return {'success': False, 'message': str(e)}


class EventPaymentWebhookView(APIView):
    """
    Webhook endpoint for payment gateway callbacks
    POST /api/v1/events/payments/webhook/{gateway}/
    """
    permission_classes = [AllowAny]

    def post(self, request, gateway):
        if gateway == 'paystack':
            return self._handle_paystack_webhook(request)
        elif gateway == 'flutterwave':
            return self._handle_flutterwave_webhook(request)
        
        return Response({"error": "Unknown gateway"}, status=status.HTTP_400_BAD_REQUEST)
    
    def _handle_paystack_webhook(self, request):
        """Handle Paystack webhook"""
        import hashlib
        import hmac
        from django.conf import settings
        
        # Verify signature
        paystack_secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        signature = request.headers.get('X-Paystack-Signature', '')
        
        expected = hmac.new(
            paystack_secret.encode('utf-8'),
            request.body,
            hashlib.sha512
        ).hexdigest()
        
        if signature != expected:
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
        
        event = request.data.get('event')
        data = request.data.get('data', {})
        
        if event == 'charge.success':
            reference = data.get('reference')
            
            try:
                transaction = EventPaymentTransaction.objects.get(reference=reference)
                
                if transaction.status != 'success':
                    transaction.status = 'success'
                    transaction.verified = True
                    transaction.verified_at = timezone.now()
                    transaction.completed_at = timezone.now()
                    transaction.payment_method = data.get('channel', '')
                    transaction.gateway_response = data
                    transaction.gateway_fee = Decimal(str(data.get('fees', 0))) / 100
                    transaction.net_amount = transaction.amount - transaction.gateway_fee
                    transaction.save()
            except EventPaymentTransaction.DoesNotExist:
                pass
        
        return Response({"success": True}, status=status.HTTP_200_OK)
    
    def _handle_flutterwave_webhook(self, request):
        """Handle Flutterwave webhook"""
        from django.conf import settings
        
        # Verify hash
        secret_hash = getattr(settings, 'FLUTTERWAVE_WEBHOOK_HASH', '')
        signature = request.headers.get('verif-hash', '')
        
        if signature != secret_hash:
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data
        
        if data.get('status') == 'successful':
            reference = data.get('tx_ref') or data.get('txRef')
            
            try:
                transaction = EventPaymentTransaction.objects.get(reference=reference)
                
                if transaction.status != 'success':
                    transaction.status = 'success'
                    transaction.verified = True
                    transaction.verified_at = timezone.now()
                    transaction.completed_at = timezone.now()
                    transaction.payment_method = data.get('payment_type', '')
                    transaction.gateway_response = data
                    transaction.gateway_fee = Decimal(str(data.get('app_fee', 0)))
                    transaction.net_amount = transaction.amount - transaction.gateway_fee
                    transaction.save()
            except EventPaymentTransaction.DoesNotExist:
                pass
        
        return Response({"success": True}, status=status.HTTP_200_OK)


class UserEventPaymentsView(ListAPIView):
    """
    Get user's event payment transactions
    GET /api/v1/events/payments/my-payments/
    """
    serializer_class = EventPaymentTransactionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        return EventPaymentTransaction.objects.filter(
            user=self.request.user
        ).select_related('event', 'registration', 'package').order_by('-initiated_at')


class RegistrationPaymentsView(ListAPIView):
    """
    Get payments for a specific registration
    GET /api/v1/events/registrations/{registration_id}/payments/
    """
    serializer_class = EventPaymentTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        registration_id = self.kwargs['registration_id']
        registration = get_object_or_404(EventRegistration, id=registration_id)
        
        # Only owner or admin can view
        if registration.user != self.request.user and not self.request.user.is_staff:
            return EventPaymentTransaction.objects.none()
        
        return registration.payment_transactions.all().order_by('-initiated_at')


class RequestEventRefundView(APIView):
    """
    Request a refund for an event registration
    POST /api/v1/events/payments/refund/
    
    Request Body:
    {
        "registration_id": "uuid",
        "amount": "50.00",  // Optional, defaults to full paid amount
        "reason": "user_request",
        "reason_details": "..."  // Optional
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RequestEventRefundSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        registration = serializer.validated_data['registration']
        amount = serializer.validated_data['amount']
        reason = serializer.validated_data['reason']
        reason_details = serializer.validated_data.get('reason_details', '')
        
        # Verify ownership (or admin)
        if registration.user != request.user and not request.user.is_staff:
            return Response(
                {"error": "You can only request refunds for your own registrations"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the original transaction to refund
        original_transaction = registration.payment_transactions.filter(
            status='success',
            transaction_type__in=['payment', 'partial_payment', 'balance_payment']
        ).first()
        
        if not original_transaction:
            return Response(
                {"error": "No successful payment found for this registration"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create refund record
        refund = EventPaymentRefund.objects.create(
            original_transaction=original_transaction,
            registration=registration,
            amount=amount,
            reason=reason,
            reason_details=reason_details,
            initiated_by=request.user,
            status='pending'
        )
        
        return Response({
            "success": True,
            "message": "Refund request submitted successfully. It will be processed by an admin.",
            "refund": EventPaymentRefundSerializer(refund).data
        }, status=status.HTTP_201_CREATED)


class UserRefundsView(ListAPIView):
    """
    Get user's refund requests
    GET /api/v1/events/payments/my-refunds/
    """
    serializer_class = EventPaymentRefundSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        return EventPaymentRefund.objects.filter(
            initiated_by=self.request.user
        ).select_related('original_transaction', 'registration').order_by('-created_at')
