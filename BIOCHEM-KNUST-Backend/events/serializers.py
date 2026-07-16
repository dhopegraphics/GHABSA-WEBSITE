from rest_framework.serializers import Serializer, ModelSerializer
from events.models import (
    Event, EventRSVP, EventRegistration, TeamMember,
    SyncMemoAlbum, SyncMemoPhoto, SyncMemoComment, SyncMemoLike, SyncMemoCommentLike,
    EventPaymentPackage, EventPaymentTransaction, EventPaymentRefund
)
from timeline.serializers import TimelineSerializer
from rest_framework import serializers
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from utils.cloudinary_utils import get_card_image_url, get_avatar_url, get_detail_image_url


# ========== NESTED SERIALIZERS FOR MOBILE APP ==========

class EventLocationSerializer(serializers.Serializer):
    """Nested serializer for event location info"""
    type = serializers.CharField(source='location_type')
    venue = serializers.CharField(allow_null=True)
    building = serializers.CharField(allow_null=True)
    virtual_link = serializers.URLField(allow_null=True)


class EventRegistrationInfoSerializer(serializers.Serializer):
    """Nested serializer for registration information"""
    required = serializers.BooleanField(source='requires_registration')
    deadline = serializers.DateTimeField(source='registration_deadline', allow_null=True)
    max_attendees = serializers.IntegerField(allow_null=True)
    is_open = serializers.BooleanField(source='is_registration_open', read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    allows_teams = serializers.BooleanField(source='allows_team_registration')
    min_team_size = serializers.IntegerField()
    max_team_size = serializers.IntegerField()


class EventPaymentInfoSerializer(serializers.Serializer):
    """Nested serializer for payment information"""
    required = serializers.BooleanField(source='requires_payment')
    description = serializers.CharField(source='payment_description', allow_null=True)
    early_bird_deadline = serializers.DateTimeField(allow_null=True)
    payment_deadline = serializers.DateTimeField(allow_null=True)
    is_early_bird_active = serializers.BooleanField(read_only=True)
    is_payment_deadline_passed = serializers.BooleanField(read_only=True)
    allow_partial_payment = serializers.BooleanField()
    minimum_deposit_percentage = serializers.IntegerField()
    lowest_price = serializers.DecimalField(
        source='lowest_package_price', max_digits=10, decimal_places=2,
        allow_null=True, read_only=True
    )
    has_packages = serializers.BooleanField(source='has_available_packages', read_only=True)


class EventAttendanceSerializer(serializers.Serializer):
    """Nested serializer for attendance information"""
    total_attending = serializers.IntegerField(source='attendee_count', read_only=True)
    capacity = serializers.IntegerField(source='max_attendees', allow_null=True)
    user_rsvp_status = serializers.SerializerMethodField()
    user_is_registered = serializers.SerializerMethodField()
    
    def get_user_rsvp_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            rsvp = obj.rsvps.filter(user=request.user).first()
            return rsvp.status if rsvp else None
        return None
    
    def get_user_is_registered(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.registrations.filter(
                user=request.user,
                status__in=['confirmed', 'pending']
            ).exists()
        return False


class SyncMemoInfoSerializer(serializers.Serializer):
    """Nested serializer for Sync Memo (photo gallery) info"""
    enabled = serializers.BooleanField(source='sync_memo_enabled')
    album_id = serializers.SerializerMethodField()
    photo_count = serializers.SerializerMethodField()
    contributor_count = serializers.SerializerMethodField()
    is_live = serializers.SerializerMethodField()
    
    def get_album_id(self, obj):
        try:
            return str(obj.sync_memo_album.id) if hasattr(obj, 'sync_memo_album') else None
        except:
            return None
    
    def get_photo_count(self, obj):
        try:
            return obj.sync_memo_album.photo_count if hasattr(obj, 'sync_memo_album') else 0
        except:
            return 0
    
    def get_contributor_count(self, obj):
        try:
            return obj.sync_memo_album.contributor_count if hasattr(obj, 'sync_memo_album') else 0
        except:
            return 0
    
    def get_is_live(self, obj):
        try:
            return obj.sync_memo_album.status == 'live' if hasattr(obj, 'sync_memo_album') else False
        except:
            return False


# ========== MAIN EVENT SERIALIZER (BACKWARD COMPATIBLE) ==========

class EventSerializer(ModelSerializer):
    """
    Main event serializer - MAINTAINS BACKWARD COMPATIBILITY
    All original fields preserved + new fields for mobile app
    """
    # Original fields (preserved for website frontend)
    timeline = TimelineSerializer(many=True)
    event_image_1 = serializers.SerializerMethodField()
    event_image_2 = serializers.SerializerMethodField()
    event_status = serializers.SerializerMethodField()
    
    # New fields for mobile app (added as nested objects to avoid breaking changes)
    location = EventLocationSerializer(source='*', read_only=True)
    registration = EventRegistrationInfoSerializer(source='*', read_only=True)
    attendance = EventAttendanceSerializer(source='*', read_only=True)
    sync_memo = SyncMemoInfoSerializer(source='*', read_only=True)
    payment = EventPaymentInfoSerializer(source='*', read_only=True)
    
    # Additional mobile app fields
    category = serializers.CharField(source='event_type', read_only=True)
    is_past = serializers.BooleanField(read_only=True)

    class Meta:
        model = Event
        fields = "__all__"

    def get_event_image_1(self, obj: Event):
        # Prioritize URL over upload, apply optimization
        url = obj.event_image_1_url if obj.event_image_1_url else (obj.event_image_1.url if obj.event_image_1 else None)
        return get_card_image_url(url, width=600)

    def get_event_image_2(self, obj: Event):
        # Prioritize URL over upload, apply optimization
        url = obj.event_image_2_url if obj.event_image_2_url else (obj.event_image_2.url if obj.event_image_2 else None)
        return get_card_image_url(url, width=600)

    def get_event_status(self, obj: Event):
        """
        Determine event status based on current time and event dates
        - 'ongoing': Event has started and hasn't ended yet
        - 'upcoming': Event hasn't started yet (event_date is in the future)
        - 'past': Event has ended
        """
        now = timezone.now()
        
        if not obj.event_date:
            return 'unknown'
        
        # If event has an end date, use it to determine status
        if obj.event_end_date:
            if now < obj.event_date:
                return 'upcoming'
            elif obj.event_date <= now <= obj.event_end_date:
                return 'ongoing'
            else:
                return 'past'
        else:
            # Single-day event logic
            # Event is upcoming if it hasn't started yet
            if now < obj.event_date:
                return 'upcoming'
            
            # Event is ongoing if it started today and the day hasn't ended
            event_day_start = obj.event_date.replace(hour=0, minute=0, second=0, microsecond=0)
            event_day_end = obj.event_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            if event_day_start <= now <= event_day_end and obj.event_date <= now:
                return 'ongoing'
            else:
                return 'past'


# ========== RSVP SERIALIZERS ==========

class RSVPUserSerializer(serializers.Serializer):
    """Minimal user info for RSVP display"""
    id = serializers.IntegerField(source='user.id')
    username = serializers.CharField(source='user.username')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    avatar = serializers.SerializerMethodField()
    
    def get_avatar(self, obj):
        # Assuming user has profile with avatar
        try:
            if hasattr(obj.user, 'profile') and obj.user.profile.avatar:
                return get_avatar_url(obj.user.profile.avatar.url, size=100)
        except:
            pass
        return None


class EventRSVPSerializer(ModelSerializer):
    """RSVP serializer for mobile app"""
    user_info = RSVPUserSerializer(source='*', read_only=True)
    event_name = serializers.CharField(source='event.event_name', read_only=True)
    
    class Meta:
        model = EventRSVP
        fields = ['id', 'event', 'user', 'status', 'reminder', 'notes', 
                  'created_at', 'updated_at', 'user_info', 'event_name']
        read_only_fields = ['id', 'created_at', 'updated_at']


class EventRSVPCreateSerializer(ModelSerializer):
    """Serializer for creating/updating RSVP"""
    class Meta:
        model = EventRSVP
        fields = ['status', 'reminder', 'notes']  # Removed 'event' as it's handled in the view


# ========== REGISTRATION SERIALIZERS ==========

class TeamMemberSerializer(ModelSerializer):
    """Team member serializer"""
    class Meta:
        model = TeamMember
        fields = ['id', 'full_name', 'email', 'phone', 'student_id', 
                  'year_group', 'program', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']


class EventRegistrationSerializer(ModelSerializer):
    """Event registration serializer"""
    team_members = TeamMemberSerializer(many=True, read_only=True)
    event_name = serializers.CharField(source='event.event_name', read_only=True)
    user_info = serializers.SerializerMethodField()
    payment_info = serializers.SerializerMethodField()
    
    class Meta:
        model = EventRegistration
        fields = [
            'id', 'registration_number', 'event', 'user', 'status', 
            'payment_status', 'payment_package', 'amount_due', 'amount_paid',
            'payment_completed_at', 'full_name', 'email', 'phone',
            'student_id', 'year_group', 'program', 'is_team_leader', 'team_name',
            'dietary_restrictions', 'special_requirements', 'notes',
            'checked_in', 'checked_in_at', 'created_at', 'updated_at',
            'team_members', 'event_name', 'user_info', 'payment_info'
        ]
        read_only_fields = ['id', 'registration_number', 'created_at', 'updated_at', 
                           'checked_in_at', 'payment_completed_at', 'amount_paid']
    
    def get_user_info(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
        }
    
    def get_payment_info(self, obj):
        """Get payment summary for registration"""
        return {
            'status': obj.payment_status,
            'amount_due': str(obj.amount_due),
            'amount_paid': str(obj.amount_paid),
            'balance_due': str(obj.balance_due),
            'is_fully_paid': obj.is_fully_paid,
            'payment_percentage': obj.payment_percentage,
            'package_name': obj.payment_package.name if obj.payment_package else None,
        }


class EventRegistrationCreateSerializer(ModelSerializer):
    """Serializer for creating event registration"""
    team_members = TeamMemberSerializer(many=True, required=False)
    
    class Meta:
        model = EventRegistration
        fields = [
            'event', 'payment_package', 'full_name', 'email', 'phone', 'student_id',
            'year_group', 'program', 'is_team_leader', 'team_name',
            'dietary_restrictions', 'special_requirements', 'notes', 'team_members'
        ]
    
    def validate(self, attrs):
        event = attrs.get('event')
        payment_package = attrs.get('payment_package')
        
        # Check if event requires payment but no package selected
        if event.requires_payment:
            if not payment_package:
                # Check if event has packages
                if event.payment_packages.filter(is_active=True).exists():
                    raise serializers.ValidationError({
                        'payment_package': 'This event requires payment. Please select a package.'
                    })
            else:
                # Validate that package belongs to the event
                if payment_package.event != event:
                    raise serializers.ValidationError({
                        'payment_package': 'Invalid package for this event.'
                    })
                
                # Check if package is available
                if not payment_package.is_available:
                    raise serializers.ValidationError({
                        'payment_package': 'This package is not available.'
                    })
        
        return attrs
    
    def create(self, validated_data):
        team_members_data = validated_data.pop('team_members', [])
        event = validated_data.get('event')
        payment_package = validated_data.get('payment_package')
        
        # Set initial status based on payment requirement
        if event.requires_payment:
            validated_data['status'] = 'pending_payment'
            validated_data['payment_status'] = 'pending'
            
            # Calculate amount due from package
            if payment_package:
                validated_data['amount_due'] = payment_package.current_price
        else:
            validated_data['status'] = 'pending'
            validated_data['payment_status'] = 'not_required'
        
        registration = EventRegistration.objects.create(**validated_data)
        
        # Create team members if provided
        for member_data in team_members_data:
            TeamMember.objects.create(registration=registration, **member_data)
        
        return registration


# ========== SYNC MEMO SERIALIZERS ==========

class SyncMemoPhotoUploadSerializer(ModelSerializer):
    """Serializer for uploading photos"""
    class Meta:
        model = SyncMemoPhoto
        fields = ['album', 'photo', 'caption', 'share_to_feed']


class SyncMemoCommentSerializer(ModelSerializer):
    """Serializer for photo comments"""
    user_info = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = SyncMemoComment
        fields = ['id', 'photo', 'user', 'comment', 'like_count', 
                  'created_at', 'updated_at', 'user_info', 'user_has_liked']
        read_only_fields = ['id', 'created_at', 'updated_at', 'like_count']
    
    def get_user_info(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
        }
    
    def get_user_has_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.comment_likes.filter(user=request.user).exists()
        return False


class SyncMemoPhotoSerializer(ModelSerializer):
    """Serializer for viewing photos"""
    uploaded_by_info = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    comments_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = SyncMemoPhoto
        fields = ['id', 'album', 'uploaded_by', 'photo_url', 'caption',
                  'like_count', 'comment_count', 'created_at', 'updated_at',
                  'uploaded_by_info', 'user_has_liked', 'comments_preview']
        read_only_fields = ['id', 'created_at', 'updated_at', 'like_count', 'comment_count']
    
    def get_photo_url(self, obj):
        # Prioritize URL over upload, apply optimization
        url = obj.photo_url if obj.photo_url else (obj.photo.url if obj.photo else None)
        return get_detail_image_url(url, width=800)
    
    def get_uploaded_by_info(self, obj):
        return {
            'id': obj.uploaded_by.id,
            'username': obj.uploaded_by.username,
            'first_name': obj.uploaded_by.first_name,
            'last_name': obj.uploaded_by.last_name,
        }
    
    def get_user_has_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_comments_preview(self, obj):
        # Return first 3 comments
        comments = obj.comments.all()[:3]
        return SyncMemoCommentSerializer(comments, many=True, context=self.context).data


class SyncMemoAlbumSerializer(ModelSerializer):
    """Serializer for photo albums"""
    event_info = serializers.SerializerMethodField()
    cover_photo_url = serializers.SerializerMethodField()
    recent_photos = serializers.SerializerMethodField()
    
    class Meta:
        model = SyncMemoAlbum
        fields = ['id', 'event', 'title', 'description', 'status',
                  'cover_photo_url', 'photo_count', 'contributor_count',
                  'allow_uploads', 'allow_comments', 'created_at', 'updated_at',
                  'event_info', 'recent_photos']
        read_only_fields = ['id', 'created_at', 'updated_at', 'photo_count', 'contributor_count']
    
    def get_cover_photo_url(self, obj):
        # Prioritize URL over upload, apply optimization
        url = None
        if obj.cover_photo_url:
            url = obj.cover_photo_url
        elif obj.cover_photo:
            url = obj.cover_photo.url
        else:
            # Use first photo as cover if no cover set
            first_photo = obj.photos.filter(is_approved=True).first()
            url = first_photo.photo.url if first_photo and first_photo.photo else None
        return get_card_image_url(url, width=400)
    
    def get_event_info(self, obj):
        return {
            'id': str(obj.event.event_id),
            'name': obj.event.event_name,
            'date': obj.event.event_date,
            'emoji': obj.event.emoji,
        }
    
    def get_recent_photos(self, obj):
        # Return 5 most recent photos
        photos = obj.photos.filter(is_approved=True).order_by('-created_at')[:5]
        return SyncMemoPhotoSerializer(photos, many=True, context=self.context).data


# ========== PAYMENT SERIALIZERS ==========

class EventPaymentPackageSerializer(ModelSerializer):
    """Serializer for event payment packages"""
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    slots_available = serializers.IntegerField(read_only=True, allow_null=True)
    is_sold_out = serializers.BooleanField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    savings_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = EventPaymentPackage
        fields = [
            'id', 'event', 'name', 'package_type', 'description',
            'price', 'early_bird_price', 'current_price', 'savings_amount',
            'max_slots', 'slots_available', 'is_sold_out', 'is_available',
            'benefits', 'available_from', 'available_until',
            'is_active', 'display_order', 'is_featured', 'badge_text',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EventPaymentPackageListSerializer(ModelSerializer):
    """Lighter serializer for package listing"""
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    slots_available = serializers.IntegerField(read_only=True, allow_null=True)
    is_sold_out = serializers.BooleanField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = EventPaymentPackage
        fields = [
            'id', 'name', 'package_type', 'description',
            'price', 'early_bird_price', 'current_price',
            'slots_available', 'is_sold_out', 'is_available',
            'benefits', 'is_featured', 'badge_text'
        ]


class EventPaymentTransactionSerializer(ModelSerializer):
    """Serializer for event payment transactions"""
    event_name = serializers.CharField(source='event.event_name', read_only=True)
    package_name = serializers.CharField(source='package.name', read_only=True, allow_null=True)
    registration_number = serializers.CharField(
        source='registration.registration_number', read_only=True
    )
    is_successful = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = EventPaymentTransaction
        fields = [
            'id', 'reference', 'event', 'event_name', 'registration',
            'registration_number', 'package', 'package_name',
            'transaction_type', 'amount', 'currency',
            'payment_method', 'payment_gateway', 'status', 'status_message',
            'gateway_reference', 'authorization_url', 'access_code',
            'customer_email', 'customer_phone', 'customer_name',
            'gateway_fee', 'net_amount', 'refund_amount',
            'initiated_at', 'completed_at', 'expires_at',
            'is_successful', 'is_pending', 'is_expired', 'verified'
        ]
        read_only_fields = [
            'id', 'reference', 'initiated_at', 'completed_at',
            'gateway_fee', 'net_amount', 'verified'
        ]


class InitializeEventPaymentSerializer(serializers.Serializer):
    """Serializer for initializing event payment"""
    registration_id = serializers.UUIDField(
        help_text="ID of the registration to pay for"
    )
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        help_text="Amount to pay. If not provided, full amount due will be used."
    )
    payment_gateway = serializers.ChoiceField(
        choices=['paystack', 'flutterwave', 'momo'],
        default='paystack',
        help_text="Payment gateway to use"
    )
    callback_url = serializers.URLField(
        required=False,
        help_text="URL to redirect to after payment (for web)"
    )
    
    def validate(self, attrs):
        registration_id = attrs.get('registration_id')
        amount = attrs.get('amount')
        
        try:
            registration = EventRegistration.objects.get(id=registration_id)
        except EventRegistration.DoesNotExist:
            raise serializers.ValidationError({
                'registration_id': 'Registration not found.'
            })
        
        # Check if registration requires payment
        if registration.payment_status == 'not_required':
            raise serializers.ValidationError({
                'registration_id': 'This registration does not require payment.'
            })
        
        # Check if already fully paid
        if registration.is_fully_paid:
            raise serializers.ValidationError({
                'registration_id': 'This registration is already fully paid.'
            })
        
        # Validate amount
        balance = registration.balance_due
        if amount:
            if amount > balance:
                raise serializers.ValidationError({
                    'amount': f'Amount cannot exceed balance due (GHS {balance}).'
                })
            
            # Check minimum deposit if partial payment
            event = registration.event
            if event.allow_partial_payment and amount < balance:
                min_deposit = (registration.amount_due * event.minimum_deposit_percentage) / 100
                if registration.amount_paid < min_deposit and amount < min_deposit:
                    raise serializers.ValidationError({
                        'amount': f'Minimum deposit is GHS {min_deposit} ({event.minimum_deposit_percentage}%).'
                    })
            elif not event.allow_partial_payment and amount < balance:
                raise serializers.ValidationError({
                    'amount': 'Partial payment is not allowed for this event. Please pay the full amount.'
                })
        else:
            attrs['amount'] = balance
        
        attrs['registration'] = registration
        return attrs


class VerifyEventPaymentSerializer(serializers.Serializer):
    """Serializer for verifying event payment"""
    reference = serializers.CharField(
        help_text="Transaction reference to verify"
    )
    
    def validate_reference(self, value):
        try:
            transaction = EventPaymentTransaction.objects.get(reference=value)
        except EventPaymentTransaction.DoesNotExist:
            raise serializers.ValidationError('Transaction not found.')
        
        return value


class EventPaymentRefundSerializer(ModelSerializer):
    """Serializer for refund records"""
    original_transaction_reference = serializers.CharField(
        source='original_transaction.reference', read_only=True
    )
    registration_number = serializers.CharField(
        source='registration.registration_number', read_only=True
    )
    is_successful = serializers.BooleanField(read_only=True)
    is_partial = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = EventPaymentRefund
        fields = [
            'id', 'reference', 'original_transaction', 'original_transaction_reference',
            'registration', 'registration_number', 'amount', 'reason', 'reason_details',
            'status', 'status_message', 'gateway_reference',
            'initiated_by', 'approved_by', 'approved_at',
            'created_at', 'processed_at', 'completed_at',
            'is_successful', 'is_partial'
        ]
        read_only_fields = [
            'id', 'reference', 'created_at', 'processed_at', 'completed_at',
            'approved_at', 'gateway_reference'
        ]


class RequestEventRefundSerializer(serializers.Serializer):
    """Serializer for requesting a refund"""
    registration_id = serializers.UUIDField(
        help_text="ID of the registration to refund"
    )
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        help_text="Amount to refund. If not provided, full paid amount will be refunded."
    )
    reason = serializers.ChoiceField(
        choices=[
            'event_cancelled', 'user_request', 'duplicate_payment',
            'event_rescheduled', 'dissatisfaction', 'other'
        ]
    )
    reason_details = serializers.CharField(
        required=False, allow_blank=True,
        help_text="Additional details about refund reason"
    )
    
    def validate(self, attrs):
        registration_id = attrs.get('registration_id')
        amount = attrs.get('amount')
        
        try:
            registration = EventRegistration.objects.get(id=registration_id)
        except EventRegistration.DoesNotExist:
            raise serializers.ValidationError({
                'registration_id': 'Registration not found.'
            })
        
        # Check if there's anything to refund
        if registration.amount_paid <= 0:
            raise serializers.ValidationError({
                'registration_id': 'This registration has no payments to refund.'
            })
        
        # Get refundable amount (paid amount minus already refunded)
        total_refunded = registration.refunds.filter(
            status='success'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        refundable = registration.amount_paid - total_refunded
        
        if refundable <= 0:
            raise serializers.ValidationError({
                'registration_id': 'This registration has already been fully refunded.'
            })
        
        if amount:
            if amount > refundable:
                raise serializers.ValidationError({
                    'amount': f'Amount cannot exceed refundable balance (GHS {refundable}).'
                })
        else:
            attrs['amount'] = refundable
        
        attrs['registration'] = registration
        return attrs
