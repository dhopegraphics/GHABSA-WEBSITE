"""
Serializers for Voting System API
"""
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import hashlib
from .models import (
    VotingEvent, VotingCategory, Candidate, Vote,
    VoterEligibility, VotingPayment, VotingResult, PollOption
)
from utils.cloudinary_utils import get_avatar_url, get_banner_image_url


def generate_server_fingerprint(request):
    """
    Generate a reliable fingerprint server-side from request headers.
    This is more reliable than client-side fingerprinting on mobile devices.
    """
    if not request:
        return ''
    
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


class PollOptionSerializer(serializers.ModelSerializer):
    """Serializer for poll options"""
    image_url_display = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = PollOption
        fields = [
            'id', 'event', 'category', 'option_text', 'description',
            'image', 'image_url', 'image_url_display', 'display_order',
            'color', 'vote_count', 'percentage', 'created_at'
        ]
        read_only_fields = ['id', 'vote_count', 'percentage', 'created_at']
    
    def get_image_url_display(self, obj):
        """Get image URL from Cloudinary or URL field"""
        if obj.image:
            return obj.image.url
        return obj.image_url
    
    def get_percentage(self, obj):
        """Calculate vote percentage"""
        return obj.percentage


class PollOptionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for poll option lists"""
    image_url_display = serializers.SerializerMethodField()
    percentage = serializers.ReadOnlyField()
    category_id = serializers.UUIDField(source='category.id', read_only=True, allow_null=True)
    
    class Meta:
        model = PollOption
        fields = [
            'id', 'category', 'category_id', 'option_text', 'description', 'image_url_display',
            'color', 'vote_count', 'percentage', 'display_order'
        ]
    
    def get_image_url_display(self, obj):
        if obj.image:
            return obj.image.url
        return obj.image_url


class VotingCategorySerializer(serializers.ModelSerializer):
    """Serializer for voting categories - includes poll options for poll events"""
    poll_options = PollOptionListSerializer(many=True, read_only=True)
    
    class Meta:
        model = VotingCategory
        fields = [
            'id', 'name', 'description', 'display_order',
            'max_votes_allowed', 'eligible_years', 'eligible_programs',
            'total_candidates', 'total_votes', 'poll_options', 'created_at'
        ]
        read_only_fields = ['id', 'total_candidates', 'total_votes', 'created_at']


class CandidateSerializer(serializers.ModelSerializer):
    """Serializer for candidates"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    profile_picture = serializers.SerializerMethodField()
    
    class Meta:
        model = Candidate
        fields = [
            'id', 'event', 'category', 'category_name',
            'user_account', 'candidate_name', 'candidate_id',
            'email', 'phone', 'bio', 'profile_image', 'profile_image_url',
            'profile_picture', 'program', 'year', 'status',
            'vote_count', 'is_winner', 'position', 'registration_date'
        ]
        read_only_fields = [
            'id', 'vote_count', 'is_winner', 'position',
            'registration_date', 'status'
        ]
    
    def get_profile_picture(self, obj):
        """Get profile picture URL (Cloudinary or URL field), optimized"""
        if obj.profile_image:
            url = obj.profile_image.url
        elif obj.profile_image_url:
            url = obj.profile_image_url
        else:
            return None
        return get_avatar_url(url, size=300)


class CandidateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for candidate lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    profile_picture = serializers.SerializerMethodField()
    
    class Meta:
        model = Candidate
        fields = [
            'id', 'candidate_name', 'candidate_id', 'profile_picture',
            'program', 'year', 'category', 'category_name', 'vote_count',
            'is_winner', 'position', 'status', 'bio'
        ]
    
    def get_profile_picture(self, obj):
        if obj.profile_image:
            url = obj.profile_image.url
        elif obj.profile_image_url:
            url = obj.profile_image_url
        else:
            return None
        return get_avatar_url(url, size=150)


class VotingEventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for event lists"""
    banner = serializers.SerializerMethodField()
    is_registration_open = serializers.SerializerMethodField()
    is_voting_open = serializers.SerializerMethodField()
    total_registered_candidates = serializers.SerializerMethodField()
    
    class Meta:
        model = VotingEvent
        fields = [
            'id', 'title', 'slug', 'event_type', 'status', 'visibility',
            'banner', 'voting_start_date', 'voting_end_date',
            'registration_open', 'voting_open',  # Boolean master switches
            'requires_authentication',  # Whether login is required to vote
            'is_registration_open', 'is_voting_open',  # Computed values
            'requires_payment', 'voting_fee', 'total_votes_cast',
            'total_registered_candidates',
            'eligible_years', 'eligible_programs',  # For frontend visibility filtering
        ]
    
    def get_banner(self, obj):
        url = obj.banner_image.url if obj.banner_image else obj.banner_image_url
        return get_banner_image_url(url, width=800)
    
    def get_is_registration_open(self, obj):
        return obj.is_registration_open()
    
    def get_is_voting_open(self, obj):
        return obj.is_voting_open()
    
    def get_total_registered_candidates(self, obj):
        """Return count of approved candidates"""
        return Candidate.objects.filter(event=obj, status='approved').count()


class VotingEventDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single event view"""
    categories = VotingCategorySerializer(many=True, read_only=True)
    poll_options = PollOptionListSerializer(many=True, read_only=True)  # For single-question polls
    banner = serializers.SerializerMethodField()
    is_registration_open = serializers.SerializerMethodField()
    is_voting_open = serializers.SerializerMethodField()
    user_has_voted = serializers.SerializerMethodField()
    user_is_eligible = serializers.SerializerMethodField()
    user_payment_status = serializers.SerializerMethodField()
    total_registered_candidates = serializers.SerializerMethodField()
    total_poll_options = serializers.SerializerMethodField()
    is_poll_event = serializers.SerializerMethodField()
    
    class Meta:
        model = VotingEvent
        fields = [
            'id', 'title', 'slug', 'description', 'event_type',
            'status', 'visibility', 'banner',
            'registration_open', 'voting_open',  # Boolean master switches
            'requires_authentication',  # Whether login is required to vote
            'registration_start_date', 'registration_end_date',
            'voting_start_date', 'voting_end_date',
            'eligible_years', 'eligible_programs',
            'requires_payment', 'voting_fee', 'allow_multiple_vote_purchase',
            'allow_multiple_votes', 'allow_candidate_self_voting',
            'show_live_results', 'anonymous_voting', 'max_votes_per_category',
            'total_registered_candidates', 'total_eligible_voters',
            'total_votes_cast', 'categories', 'poll_options',
            'total_poll_options', 'is_poll_event',
            'is_registration_open', 'is_voting_open',  # Computed values
            'user_has_voted', 'user_is_eligible', 'user_payment_status',
            'created_at', 'updated_at'
        ]
    
    def get_banner(self, obj):
        url = obj.banner_image.url if obj.banner_image else obj.banner_image_url
        return get_banner_image_url(url, width=1200)
    
    def get_is_registration_open(self, obj):
        return obj.is_registration_open()
    
    def get_is_voting_open(self, obj):
        return obj.is_voting_open()
    
    def get_total_registered_candidates(self, obj):
        """Return count of approved candidates"""
        return Candidate.objects.filter(event=obj, status='approved').count()
    
    def get_total_poll_options(self, obj):
        """Return total poll options count"""
        return obj.poll_options.count()
    
    def get_is_poll_event(self, obj):
        """Check if this is a poll/referendum event"""
        return obj.event_type in ['poll', 'referendum']
    
    def get_user_has_voted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Vote.objects.filter(event=obj, voter=request.user).exists()
        return False
    
    def get_user_is_eligible(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            eligibility = VoterEligibility.objects.filter(
                event=obj, user=request.user
            ).first()
            return eligibility.is_eligible if eligibility else obj.can_user_participate(request.user)
        return False
    
    def get_user_payment_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj.requires_payment:
            payment = VotingPayment.objects.filter(
                event=obj, user=request.user, status='verified'
            ).first()
            return {
                'required': True,
                'verified': payment is not None,
                'amount': str(obj.voting_fee)
            }
        return {'required': False, 'verified': True}


class VoteSerializer(serializers.ModelSerializer):
    """Serializer for casting votes with vote purchasing support and anonymous user support
    Supports voting for either candidates (elections/awards) or poll options (polls/referendums)
    """
    
    # Read-only nested details
    poll_option_details = PollOptionListSerializer(source='poll_option', read_only=True)
    candidate_details = serializers.SerializerMethodField()
    event_title = serializers.CharField(source='event.title', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    
    # Optional fields for anonymous/guest voters
    guest_email = serializers.EmailField(required=False, write_only=True, help_text="Email for anonymous voters")
    guest_phone = serializers.CharField(required=False, write_only=True, max_length=20, help_text="Phone for anonymous voters")
    guest_name = serializers.CharField(required=False, write_only=True, max_length=255, help_text="Name for anonymous voters")
    device_fingerprint = serializers.CharField(required=False, write_only=True, max_length=64, help_text="Device fingerprint for duplicate detection")
    session_id = serializers.CharField(required=False, write_only=True, max_length=64, help_text="Session ID for vote tracking")
    
    class Meta:
        model = Vote
        fields = [
            'id', 'event', 'event_title', 'category', 'category_name',
            'candidate', 'candidate_details', 'poll_option', 'poll_option_details',
            'vote_quantity', 'payment_verified', 'payment_reference', 'payment_amount',
            'vote_date', 'guest_email', 'guest_phone', 'guest_name',
            'device_fingerprint', 'session_id'
        ]
        read_only_fields = ['id', 'vote_date', 'payment_verified', 'event_title', 'category_name', 'poll_option_details', 'candidate_details']
    
    def get_candidate_details(self, obj):
        """Get candidate details if vote is for a candidate"""
        if obj.candidate:
            return {
                'id': str(obj.candidate.id),
                'candidate_name': obj.candidate.candidate_name,
                'profile_image': obj.candidate.profile_image.url if obj.candidate.profile_image else None,
            }
        return None
    
    def _get_detection_reason(self, existing_vote, user, device_fingerprint, server_fingerprint, session_id, ip_address):
        """
        Determine how the duplicate vote was detected and return a user-friendly message.
        This helps users understand why they cannot vote again.
        """
        reasons = []
        
        # Check what matched
        if user and existing_vote.voter and existing_vote.voter == user:
            return "Your account was used to vote previously."
        
        if existing_vote.ip_address and ip_address and existing_vote.ip_address == ip_address:
            reasons.append("same network/IP address")
        
        if device_fingerprint and existing_vote.device_fingerprint:
            if existing_vote.device_fingerprint == device_fingerprint:
                reasons.append("device fingerprint")
            elif server_fingerprint and existing_vote.device_fingerprint.startswith(server_fingerprint):
                reasons.append("browser/device signature")
        
        if session_id and existing_vote.session_id == session_id:
            reasons.append("browser session")
        
        if reasons:
            reason_text = ", ".join(reasons)
            return f"Detected via {reason_text}. Each person can only vote once."
        
        return "Duplicate voting is not allowed."
    
    def validate(self, data):
        """Validate vote submission for both authenticated and anonymous users"""
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        is_anonymous = not user
        
        event = data.get('event')
        category = data.get('category')
        candidate = data.get('candidate')
        poll_option = data.get('poll_option')
        client_fingerprint = data.get('device_fingerprint', '')
        session_id = data.get('session_id', '')
        
        # Generate server-side fingerprint for more reliable tracking
        server_fingerprint = generate_server_fingerprint(request)
        
        # Combine client and server fingerprints for best results
        # Server fingerprint is always generated, client may be empty on some mobile browsers
        if client_fingerprint:
            # Use combined fingerprint for strongest identification
            combined_fingerprint = f"{server_fingerprint}_{client_fingerprint[:16]}"
        else:
            # Fallback to server fingerprint only
            combined_fingerprint = server_fingerprint
        
        # Store the combined fingerprint for later use
        data['_combined_fingerprint'] = combined_fingerprint
        data['_server_fingerprint'] = server_fingerprint
        
        # Use combined fingerprint for duplicate detection
        device_fingerprint = combined_fingerprint
        
        # Check if event status allows voting
        if event.status in ['completed', 'results_published', 'voting_closed']:
            raise serializers.ValidationError(
                "This voting event has ended. Results may have been published or the event is completed."
            )
        
        # Check if voting is open
        if not event.is_voting_open():
            raise serializers.ValidationError("Voting is not currently open for this event.")
        
        # Validate vote target based on event type
        is_poll_event = event.event_type in ['poll', 'referendum']
        
        if is_poll_event:
            # Poll/referendum events require poll_option, not candidate
            if candidate:
                raise serializers.ValidationError(
                    "This is a poll/referendum event. Vote for a poll option, not a candidate."
                )
            if not poll_option:
                raise serializers.ValidationError(
                    "Poll option is required for poll/referendum events."
                )
            # Validate poll option belongs to event
            if poll_option.event != event:
                raise serializers.ValidationError("Poll option does not belong to this event.")
            if category and poll_option.category != category:
                raise serializers.ValidationError("Poll option does not belong to this category/question.")
        else:
            # Election/awards events require candidate, not poll_option
            if poll_option:
                raise serializers.ValidationError(
                    "This is an election/awards event. Vote for a candidate, not a poll option."
                )
            if not candidate:
                raise serializers.ValidationError(
                    "Candidate is required for election/awards events."
                )
        
        # Get IP address for cross-referencing
        ip_address = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
        
        # Store IP for later use
        data['_ip_address'] = ip_address
        
        # Determine the category to check - use poll_option's category if available
        vote_category = category
        if not vote_category and poll_option and poll_option.category:
            vote_category = poll_option.category
        
        # ========================================
        # ROBUST DUPLICATE DETECTION
        # ========================================
        # Check for duplicate votes regardless of login status
        # This prevents: 
        # 1. Anonymous vote then login and vote again
        # 2. Login vote then clear session and vote anonymously
        # 3. Vote on phone then vote on PC (if same IP)
        # 4. Clear history and vote again (fingerprint/IP still tracked)
        
        if not event.allow_multiple_vote_purchase:
            from django.db.models import Q
            
            # Build comprehensive identifier filter for ALL votes (not just anonymous)
            all_votes_query = Vote.objects.filter(event=event)
            
            identifier_filter = Q()
            
            # Check by device fingerprint (combined client+server fingerprint)
            if device_fingerprint:
                identifier_filter |= Q(device_fingerprint=device_fingerprint)
            
            # Check by server fingerprint prefix (catches same device even with different client fp)
            if server_fingerprint:
                identifier_filter |= Q(device_fingerprint__startswith=server_fingerprint)
            
            # Check by session ID
            if session_id:
                identifier_filter |= Q(session_id=session_id)
            
            # Check by IP address - important for catching phone->PC switches on same network
            if ip_address:
                identifier_filter |= Q(ip_address=ip_address)
            
            # Check by authenticated user (if logged in, also check their previous votes)
            if user:
                identifier_filter |= Q(voter=user)
            
            # Apply identifier filter
            if identifier_filter:
                existing_votes = all_votes_query.filter(identifier_filter)
                
                # Check if already voted in this category (or event if no categories)
                if vote_category:
                    category_votes = existing_votes.filter(category=vote_category)
                    if category_votes.exists():
                        # Get details for better error message
                        existing = category_votes.first()
                        
                        # Determine how we detected the duplicate
                        detection_reason = self._get_detection_reason(
                            existing, user, device_fingerprint, server_fingerprint, session_id, ip_address
                        )
                        
                        if existing.voter:
                            raise serializers.ValidationError(
                                f"You have already voted in the '{vote_category.name}' category. {detection_reason}"
                            )
                        else:
                            raise serializers.ValidationError(
                                f"This device has already voted in the '{vote_category.name}' category. {detection_reason}"
                            )
                else:
                    # No category - check if voted in event at all
                    if existing_votes.exists():
                        existing = existing_votes.first()
                        
                        # Determine how we detected the duplicate
                        detection_reason = self._get_detection_reason(
                            existing, user, device_fingerprint, server_fingerprint, session_id, ip_address
                        )
                        
                        if existing.voter:
                            raise serializers.ValidationError(
                                f"You have already voted in this event. {detection_reason}"
                            )
                        else:
                            raise serializers.ValidationError(
                                f"This device has already voted in this event. {detection_reason}"
                            )
        
        # For anonymous users, check event settings
        if is_anonymous:
            # Check if event requires authentication
            if event.requires_authentication:
                raise serializers.ValidationError(
                    "This event requires you to login to vote. Please create an account or login."
                )
            
            # If requires_authentication is False, allow anonymous voting
            # regardless of visibility or eligibility settings
            # (these restrictions are meant for filtering authenticated users, not blocking anonymous votes
            # when the event explicitly allows anonymous voting)
            
            # However, if the event is NOT public and has eligibility restrictions,
            # we should still require auth so we can verify eligibility
            if event.visibility != 'public' and (event.eligible_years or event.eligible_programs):
                raise serializers.ValidationError(
                    "This event has eligibility restrictions. Please log in to verify your eligibility."
                )
        else:
            # Check if authenticated user is eligible
            if not event.can_user_participate(user):
                raise serializers.ValidationError("You are not eligible to vote in this event.")
            
            # Check if user is trying to vote for THEMSELVES (self-voting check)
            # Only applies to election events with candidates
            if not is_poll_event and not event.allow_candidate_self_voting and candidate:
                # Check if the candidate being voted for is the current user
                if candidate.user_account and candidate.user_account == user:
                    raise serializers.ValidationError(
                        "You cannot vote for yourself in this event. Please vote for another candidate."
                    )
        
        # For election events, validate candidate
        if candidate:
            if candidate.event != event:
                raise serializers.ValidationError("Candidate does not belong to this event.")
            
            if category and candidate.category != category:
                raise serializers.ValidationError("Candidate does not belong to this category.")
        
        # Validate vote quantity
        vote_quantity = data.get('vote_quantity', 1)
        if vote_quantity < 1:
            raise serializers.ValidationError("Vote quantity must be at least 1.")
        
        # Check if multiple vote purchase is allowed
        if vote_quantity > 1 and not event.allow_multiple_vote_purchase:
            raise serializers.ValidationError(
                "This event does not allow purchasing multiple votes."
            )
        
        # Calculate payment amount
        if event.requires_payment:
            payment_amount = event.voting_fee * vote_quantity
            data['payment_amount'] = payment_amount
            # Payment will be verified after payment gateway callback
            data['payment_verified'] = False
        else:
            data['payment_amount'] = 0
            data['payment_verified'] = True  # No payment needed
        
        return data
    
    def create(self, validated_data):
        """Create vote with support for both authenticated and anonymous users.
        Uses atomic transaction to ensure data consistency.
        """
        request = self.context.get('request')
        
        # Remove guest fields from validated_data (they're not model fields)
        guest_email = validated_data.pop('guest_email', None)
        guest_phone = validated_data.pop('guest_phone', None)
        guest_name = validated_data.pop('guest_name', None)
        client_fingerprint = validated_data.pop('device_fingerprint', '')
        session_id = validated_data.pop('session_id', '')
        
        # Get the combined fingerprint from validation step
        combined_fingerprint = validated_data.pop('_combined_fingerprint', '')
        server_fingerprint = validated_data.pop('_server_fingerprint', '')
        
        # Use combined fingerprint for storage (more reliable)
        device_fingerprint = combined_fingerprint or client_fingerprint or server_fingerprint
        
        # Set voter to authenticated user or None for anonymous
        if request and request.user.is_authenticated:
            validated_data['voter'] = request.user
        else:
            validated_data['voter'] = None
        
        # For poll options, ensure category is set from poll_option if not provided
        poll_option = validated_data.get('poll_option')
        if poll_option and not validated_data.get('category') and poll_option.category:
            validated_data['category'] = poll_option.category
        
        # Get IP and user agent
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                validated_data['ip_address'] = x_forwarded_for.split(',')[0]
            else:
                validated_data['ip_address'] = request.META.get('REMOTE_ADDR')
            
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]
            validated_data['device_fingerprint'] = device_fingerprint
            validated_data['session_id'] = session_id
        
        # Store guest information in user_agent field if anonymous
        if not request.user.is_authenticated and (guest_email or guest_phone or guest_name):
            guest_info = f"Guest: {guest_name or 'Anonymous'} | Email: {guest_email or 'N/A'} | Phone: {guest_phone or 'N/A'}"
            validated_data['user_agent'] = guest_info[:500]
        
        # Use atomic transaction to ensure vote and count updates are consistent
        with transaction.atomic():
            vote = Vote.objects.create(**validated_data)
            
            # Only update counts if payment is verified (no payment required or already verified)
            if vote.payment_verified:
                self._update_vote_counts(vote)
        
        return vote
    
    def _update_vote_counts(self, vote):
        """Update candidate/poll_option and event vote counts"""
        # Update candidate or poll option vote count
        if vote.candidate:
            candidate = vote.candidate
            candidate.vote_count += vote.vote_quantity
            candidate.save()
        elif vote.poll_option:
            poll_option = vote.poll_option
            poll_option.vote_count += vote.vote_quantity
            poll_option.save()
        
        # Update category total votes
        if vote.category:
            category = vote.category
            category.total_votes += vote.vote_quantity
            category.save()
        
        # Update event total votes
        event = vote.event
        event.total_votes_cast += vote.vote_quantity
        event.save()
        
        # Update voter eligibility only for authenticated users
        if vote.voter:
            eligibility, created = VoterEligibility.objects.get_or_create(
                event=event,
                user=vote.voter,
                defaults={'is_eligible': True}
            )
            eligibility.has_voted = True
            eligibility.vote_date = timezone.now()
            eligibility.save()


class VotingPaymentSerializer(serializers.ModelSerializer):
    """Serializer for voting payments"""
    
    class Meta:
        model = VotingPayment
        fields = [
            'id', 'event', 'amount', 'payment_method',
            'payment_reference', 'phone_number', 'status',
            'payment_date', 'notes'
        ]
        read_only_fields = ['id', 'status', 'payment_date']
    
    def create(self, validated_data):
        """Create payment record"""
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class VotingResultSerializer(serializers.ModelSerializer):
    """Serializer for voting results"""
    event_title = serializers.CharField(source='event.title', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    winner_details = CandidateListSerializer(source='winner', read_only=True)
    total_eligible_voters = serializers.SerializerMethodField()
    voter_turnout_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = VotingResult
        fields = [
            'id', 'event', 'event_title', 'category', 'category_name',
            'winner', 'winner_details', 'total_votes_cast',
            'total_eligible_voters', 'voter_turnout_percentage',
            'is_published', 'published_date', 'detailed_results',
            'created_at'
        ]
    
    def get_total_eligible_voters(self, obj):
        """Get eligible voters from result or calculate from event"""
        if obj.total_eligible_voters and obj.total_eligible_voters > 0:
            return obj.total_eligible_voters
        
        # Calculate from event
        event = obj.event
        if event.total_eligible_voters and event.total_eligible_voters > 0:
            return event.total_eligible_voters
        
        # Calculate dynamically
        return event.calculate_eligible_voters()
    
    def get_voter_turnout_percentage(self, obj):
        """Calculate voter turnout dynamically"""
        eligible = self.get_total_eligible_voters(obj)
        if eligible > 0:
            turnout = (obj.total_votes_cast / eligible) * 100
            return round(turnout, 2)
        return 0.0


class VoterEligibilitySerializer(serializers.ModelSerializer):
    """Serializer for voter eligibility"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    
    class Meta:
        model = VoterEligibility
        fields = [
            'id', 'event', 'event_title', 'user', 'user_name',
            'is_eligible', 'eligibility_reason', 'has_voted',
            'vote_date', 'payment_required', 'payment_verified',
            'payment_reference', 'payment_date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CandidateRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for candidate self-registration"""
    
    class Meta:
        model = Candidate
        fields = [
            'event', 'category', 'candidate_name', 'candidate_id',
            'email', 'phone', 'bio', 'profile_image', 'profile_image_url',
            'program', 'year'
        ]
        extra_kwargs = {
            'category': {'required': False, 'allow_null': True},
            'candidate_id': {'required': False, 'allow_blank': True},
            'email': {'required': False, 'allow_blank': True},
            'phone': {'required': False, 'allow_blank': True},
            'bio': {'required': False, 'allow_blank': True},
            'program': {'required': False, 'allow_blank': True},
            'year': {'required': False, 'allow_null': True},
            'profile_image_url': {'required': False, 'allow_blank': True},
        }
    
    def validate(self, data):
        """Validate candidate registration"""
        event = data.get('event')
        request = self.context.get('request')
        user = request.user if request else None
        
        # Check if registration is open
        if not event.is_registration_open():
            raise serializers.ValidationError(
                "Candidate registration is not currently open for this event."
            )
        
        # Check if user already registered for this event
        if user:
            existing = Candidate.objects.filter(
                event=event,
                user_account=user
            ).exclude(status='rejected').first()
            
            if existing:
                status_display = existing.get_status_display()
                raise serializers.ValidationError(
                    f"You have already registered for this event. Status: {status_display}"
                )
        
        # Check if event requires a category but none provided
        if event.categories.exists() and not data.get('category'):
            raise serializers.ValidationError({
                'category': "This event has categories. Please select a category to contest in."
            })
        
        # Validate program eligibility if event has program restrictions
        if event.eligible_programs and len(event.eligible_programs) > 0:
            program = data.get('program')
            if not program:
                raise serializers.ValidationError({
                    'program': f"This event is restricted to specific programs. Please select one of: {', '.join(event.eligible_programs)}"
                })
            if program not in event.eligible_programs:
                raise serializers.ValidationError({
                    'program': f"This event is only for {', '.join(event.eligible_programs)} students."
                })
        
        # Validate year eligibility if event has year restrictions
        if event.eligible_years and len(event.eligible_years) > 0:
            year = data.get('year')
            if not year:
                raise serializers.ValidationError({
                    'year': f"This event is restricted to specific years. Please select one of: Year {', '.join(map(str, event.eligible_years))}"
                })
            if year not in event.eligible_years:
                raise serializers.ValidationError({
                    'year': f"This event is only for Year {', '.join(map(str, event.eligible_years))} students."
                })
        
        return data
    
    def create(self, validated_data):
        """Create candidate with pending status"""
        request = self.context.get('request')
        validated_data['user_account'] = request.user
        validated_data['status'] = 'pending'
        
        # Create the candidate
        candidate = super().create(validated_data)
        
        # Update the event's registered candidates count
        event = validated_data.get('event')
        event.total_registered_candidates = Candidate.objects.filter(
            event=event
        ).exclude(status='rejected').count()
        event.save(update_fields=['total_registered_candidates'])
        
        return candidate


class PaymentInitializationSerializer(serializers.Serializer):
    """Serializer for payment initialization request using Universal Payment System"""
    event_slug = serializers.SlugField(
        required=True,
        help_text="Slug of the voting event"
    )
    currency = serializers.ChoiceField(
        choices=['GHS', 'USD', 'NGN', 'ZAR', 'KES'],
        default='GHS',
        required=False,
        help_text="Currency code (defaults to GHS)"
    )
    gateway = serializers.ChoiceField(
        choices=['paystack', 'flutterwave', 'stripe', 'mtn_momo'],
        default='paystack',
        required=False,
        help_text="Payment gateway to use (defaults to paystack)"
    )
    callback_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="URL to redirect after payment"
    )
    customer_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text="Customer email for payment receipt"
    )
    customer_phone = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=20,
        help_text="Customer phone number with country code"
    )
    customer_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        help_text="Customer full name"
    )


class PaymentVerificationSerializer(serializers.Serializer):
    """Serializer for payment verification request"""
    reference = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Payment reference to verify"
    )


class VotingPaymentDetailSerializer(serializers.ModelSerializer):
    """Detailed payment serializer with all fields"""
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_slug = serializers.CharField(source='event.slug', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    payment_method_display = serializers.CharField(
        source='get_payment_method_display',
        read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    formatted_amount = serializers.CharField(read_only=True)
    is_successful = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = VotingPayment
        fields = [
            'id', 'event', 'event_title', 'event_slug',
            'user', 'user_name', 'user_phone',
            'amount', 'currency', 'formatted_amount',
            'payment_method', 'payment_method_display',
            'payment_reference', 'paystack_reference',
            'authorization_url', 'channel', 'card_type', 'bank',
            'status', 'status_display', 'is_successful', 'is_pending',
            'gateway_response', 'email', 'phone_number',
            'created_at', 'payment_date', 'verified_at',
            'verified_by', 'notes', 'metadata'
        ]
        read_only_fields = [
            'id', 'created_at', 'payment_date', 'verified_at',
            'verified_by', 'paystack_reference', 'authorization_url',
            'channel', 'card_type', 'bank', 'gateway_response'
        ]
