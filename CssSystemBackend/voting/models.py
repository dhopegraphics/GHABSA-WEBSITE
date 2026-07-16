"""
Advanced Voting/Election System for CSS Department
Supports: Course Rep Elections, Awards Voting, General Elections with categories
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import CustomUser
from uuid import uuid4
# CloudinaryField replaced with ImageField using DynamicStorage
# from cloudinary.models import CloudinaryField
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage


class VotingEvent(MediaUrlMixin, models.Model):
    """
    Main voting event - can be election, awards, poll, etc.
    """
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'banner_image': 'banner_image_url',
    }
    
    EVENT_TYPE_CHOICES = [
        ('election', 'Election'),  # Single winner (Course Rep, President, etc.)
        ('awards', 'Awards Voting'),  # Multiple categories with winners
        ('poll', 'Opinion Poll'),  # No winners, just results
        ('referendum', 'Referendum'),  # Yes/No vote
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('registration_open', 'Registration Open'),
        ('registration_closed', 'Registration Closed'),
        ('voting_open', 'Voting Open'),
        ('voting_closed', 'Voting Closed'),
        ('results_published', 'Results Published'),
        ('completed', 'Completed'),
    ]
    
    VISIBILITY_CHOICES = [
        ('public', 'Public - All students can see'),
        ('year', 'Year Specific - Only specific years'),
        ('program', 'Program Specific - Only specific programs'),
        ('private', 'Private - Invited users only'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=200, help_text="e.g., 'Year 2 Course Rep Elections 2024/2025'")
    slug = models.SlugField(unique=True, max_length=250)
    description = models.TextField(help_text="Full description of the voting event")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='election')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    
    # Banner/Poster
    banner_image = models.ImageField(storage=DynamicStorage(), upload_to="VotingBanners/", null=True, blank=True)
    banner_image_url = models.URLField(blank=True, null=True, help_text="Alternative: Provide image URL")
    
    # Manual Open/Close Controls (takes precedence over dates)
    registration_open = models.BooleanField(
        default=False,
        help_text="Master switch: Enable candidate registration. When OFF, registration is closed regardless of dates."
    )
    voting_open = models.BooleanField(
        default=False,
        help_text="Master switch: Enable voting. When OFF, voting is closed regardless of dates."
    )
    
    # Dates (only checked when master switch is ON)
    registration_start_date = models.DateTimeField(help_text="When candidates can register (only if registration_open is ON)")
    registration_end_date = models.DateTimeField(help_text="Last day for candidate registration")
    voting_start_date = models.DateTimeField(help_text="When voting opens (only if voting_open is ON)")
    voting_end_date = models.DateTimeField(help_text="When voting closes")
    
    # Eligibility
    eligible_years = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of years that can vote: [1, 2, 3, 4]"
    )
    eligible_programs = models.JSONField(
        default=list,
        blank=True,
        help_text="List of programs: ['CS', 'IT', 'Data Science']"
    )
    
    # Payment Configuration
    requires_payment = models.BooleanField(default=False, help_text="Does voting require payment?")
    voting_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text="Fee per vote (price per single vote)"
    )
    allow_multiple_vote_purchase = models.BooleanField(
        default=False,
        help_text="Allow users to buy multiple votes for a candidate?"
    )
    
    # Settings
    requires_authentication = models.BooleanField(
        default=True,
        help_text="Require users to login to vote? If False, anonymous voting is allowed for public events."
    )
    allow_multiple_votes = models.BooleanField(
        default=False, 
        help_text="Allow users to vote in multiple categories?"
    )
    allow_candidate_self_voting = models.BooleanField(
        default=False,
        help_text="Allow candidates to vote in this event (including for themselves)?"
    )
    show_live_results = models.BooleanField(
        default=False, 
        help_text="Show results while voting is ongoing?"
    )
    anonymous_voting = models.BooleanField(
        default=True, 
        help_text="Hide voter identities in results?"
    )
    max_votes_per_category = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Maximum votes per category (1 for single winner)"
    )
    
    # Statistics
    total_registered_candidates = models.IntegerField(default=0)
    total_eligible_voters = models.IntegerField(default=0)
    total_votes_cast = models.IntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_voting_events'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Voting Event"
        verbose_name_plural = "Voting Events"
        ordering = ['-voting_start_date']
    
    def __str__(self):
        return f"{self.title} ({self.get_event_type_display()})"
    
    def is_registration_open(self):
        """Check if registration is open. Boolean flag takes precedence over dates."""
        if not self.registration_open:
            return False
        now = timezone.now()
        return self.registration_start_date <= now <= self.registration_end_date
    
    def is_voting_open(self):
        """Check if voting is open. Boolean flag takes precedence over dates.
        Also checks that event status is not completed or results_published."""
        # Block voting if event is completed or results are published
        if self.status in ['completed', 'results_published', 'voting_closed']:
            return False
        if not self.voting_open:
            return False
        now = timezone.now()
        return self.voting_start_date <= now <= self.voting_end_date
    
    def can_user_participate(self, user):
        """Check if user is eligible to vote"""
        if not self.eligible_years and not self.eligible_programs:
            return True  # Public to all
        
        eligible = True
        if self.eligible_years:
            user_year = user.year if hasattr(user, 'year') else user.get_year()
            eligible = eligible and user_year in self.eligible_years
        if self.eligible_programs:
            eligible = eligible and user.program in self.eligible_programs
        
        return eligible
    
    def calculate_eligible_voters(self):
        """
        Calculate the number of eligible voters based on event restrictions.
        
        Logic:
        - If event has program restrictions: count users in those programs
        - If event has year restrictions: count users in those years
        - If both: count users matching both criteria
        - If no restrictions: count all active users
        
        For anonymous/public events, we estimate based on registered users.
        """
        from django.db.models import Q
        from django.utils import timezone
        
        # Start with all active users
        queryset = CustomUser.objects.filter(is_active=True)
        
        # Exclude superusers and staff (they typically don't vote)
        queryset = queryset.filter(is_superuser=False, is_staff=False)
        
        # Apply program filter if specified
        if self.eligible_programs and len(self.eligible_programs) > 0:
            queryset = queryset.filter(program__in=self.eligible_programs)
        
        # Apply year filter if specified
        if self.eligible_years and len(self.eligible_years) > 0:
            # Calculate graduation years from year levels
            # Year 1 = current_year + 3, Year 2 = current_year + 2, etc.
            current_year = timezone.now().year
            current_month = timezone.now().month
            
            # After November, students are "promoted" to next academic year
            if current_month >= 11:
                current_year += 1
            
            eligible_graduation_years = []
            for year_level in self.eligible_years:
                # Year level 1 graduates in 4 years, Year 2 in 3 years, etc.
                grad_year = current_year + (4 - year_level)
                eligible_graduation_years.append(grad_year)
            
            queryset = queryset.filter(graduation_year__in=eligible_graduation_years)
        
        return queryset.count()
    
    def update_eligible_voters_count(self):
        """Update the total_eligible_voters field with current count"""
        self.total_eligible_voters = self.calculate_eligible_voters()
        self.save(update_fields=['total_eligible_voters'])
        return self.total_eligible_voters
    
    def get_voter_turnout_percentage(self):
        """Calculate voter turnout percentage"""
        if self.total_eligible_voters and self.total_eligible_voters > 0:
            return round((self.total_votes_cast / self.total_eligible_voters) * 100, 1)
        return 0.0

    def generate_results(self, published_by=None):
        """
        Generate VotingResult records for all categories based on current votes.
        Called when status is set to 'results_published'.
        Handles:
        - Multi-category elections/awards
        - Single-category events (no explicit categories)
        - Poll/referendum events with poll options
        """
        from django.db.models import Count
        
        results_created = []
        
        # Handle poll/referendum events differently
        if self.event_type in ['poll', 'referendum']:
            results_created = self._generate_poll_results(published_by)
        else:
            results_created = self._generate_election_results(published_by)
        
        return results_created
    
    def _generate_poll_results(self, published_by=None):
        """Generate results for poll/referendum events"""
        from django.db.models import Count
        
        results_created = []
        
        # Check if poll has categories (multi-question poll)
        if self.categories.exists():
            for category in self.categories.all():
                # Get poll options with vote counts
                options = category.poll_options.annotate(
                    total_votes_received=Count('votes_received')
                ).order_by('-total_votes_received')
                
                # Build detailed results
                total_category_votes = sum(o.total_votes_received for o in options)
                detailed_results = []
                
                for option in options:
                    detailed_results.append({
                        'id': str(option.id),
                        'option_text': option.option_text,
                        'description': option.description,
                        'image': option.image.url if option.image else option.image_url,
                        'color': option.color,
                        'vote_count': option.total_votes_received,
                        'percentage': round(
                            (option.total_votes_received / total_category_votes * 100) 
                            if total_category_votes > 0 else 0, 
                            2
                        )
                    })
                
                # For polls, winner is the most voted option (if any)
                winning_option = options.first() if options.exists() else None
                
                result, created = VotingResult.objects.update_or_create(
                    event=self,
                    category=category,
                    defaults={
                        'winner': None,  # Polls don't have candidate winners
                        'total_votes_cast': total_category_votes,
                        'total_eligible_voters': self.total_eligible_voters or 0,
                        'voter_turnout_percentage': round(
                            (self.total_votes_cast / self.total_eligible_voters * 100)
                            if self.total_eligible_voters > 0 else 0,
                            2
                        ),
                        'is_published': True,
                        'published_date': timezone.now(),
                        'published_by': published_by,
                        'detailed_results': {
                            'type': 'poll',
                            'question': category.name,
                            'options': detailed_results,
                            'winning_option': detailed_results[0] if detailed_results else None
                        }
                    }
                )
                results_created.append(result)
        else:
            # Single-question poll (no categories)
            options = self.poll_options.annotate(
                total_votes_received=Count('votes_received')
            ).order_by('-total_votes_received')
            
            total_votes = sum(o.total_votes_received for o in options)
            detailed_results = []
            
            for option in options:
                detailed_results.append({
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
            
            result, created = VotingResult.objects.update_or_create(
                event=self,
                category=None,
                defaults={
                    'winner': None,
                    'total_votes_cast': total_votes,
                    'total_eligible_voters': self.total_eligible_voters or 0,
                    'voter_turnout_percentage': round(
                        (self.total_votes_cast / self.total_eligible_voters * 100)
                        if self.total_eligible_voters > 0 else 0,
                        2
                    ),
                    'is_published': True,
                    'published_date': timezone.now(),
                    'published_by': published_by,
                    'detailed_results': {
                        'type': 'poll',
                        'question': self.title,
                        'options': detailed_results,
                        'winning_option': detailed_results[0] if detailed_results else None
                    }
                }
            )
            results_created.append(result)
        
        return results_created
    
    def _generate_election_results(self, published_by=None):
        """Generate results for election/awards events"""
        from django.db.models import Count
        
        results_created = []
        
        # Check if event has categories
        if self.categories.exists():
            # Multi-category event
            for category in self.categories.all():
                # Get candidates with their vote counts
                candidates = category.candidates.filter(
                    status='approved'
                ).annotate(
                    total_votes_received=Count('votes_received')
                ).order_by('-total_votes_received')
                
                # Determine winner (candidate with most votes)
                winner = candidates.first() if candidates.exists() else None
                
                # Build detailed results
                detailed_results = []
                total_category_votes = sum(c.total_votes_received for c in candidates)
                for candidate in candidates:
                    detailed_results.append({
                        'id': str(candidate.id),
                        'candidate_name': candidate.candidate_name,
                        'candidate_id': candidate.candidate_id,  # Student ID
                        'profile_image': candidate.profile_image.url if candidate.profile_image else None,
                        'program': candidate.program,
                        'year': candidate.year,
                        'vote_count': candidate.total_votes_received,
                        'percentage': round(
                            (candidate.total_votes_received / total_category_votes * 100) 
                            if total_category_votes > 0 else 0, 
                            2
                        )
                    })
                
                # Create or update VotingResult
                result, created = VotingResult.objects.update_or_create(
                    event=self,
                    category=category,
                    defaults={
                        'winner': winner,
                        'total_votes_cast': total_category_votes,
                        'total_eligible_voters': self.total_eligible_voters or 0,
                        'voter_turnout_percentage': round(
                            (self.total_votes_cast / self.total_eligible_voters * 100)
                            if self.total_eligible_voters > 0 else 0,
                            2
                        ),
                        'is_published': True,
                        'published_date': timezone.now(),
                        'published_by': published_by,
                        'detailed_results': {
                            'type': 'election',
                            'candidates': detailed_results
                        }
                    }
                )
                results_created.append(result)
        else:
            # Single-category event (no explicit categories, all candidates under event)
            candidates = self.candidates.filter(
                status='approved'
            ).annotate(
                total_votes_received=Count('votes_received')
            ).order_by('-total_votes_received')
            
            if candidates.exists():
                winner = candidates.first()
                
                # Build detailed results
                total_votes = sum(c.total_votes_received for c in candidates)
                detailed_results = []
                for candidate in candidates:
                    detailed_results.append({
                        'id': str(candidate.id),
                        'candidate_name': candidate.candidate_name,
                        'candidate_id': candidate.candidate_id,  # Student ID
                        'profile_image': candidate.profile_image.url if candidate.profile_image else None,
                        'program': candidate.program,
                        'year': candidate.year,
                        'vote_count': candidate.total_votes_received,
                        'percentage': round(
                            (candidate.total_votes_received / total_votes * 100) 
                            if total_votes > 0 else 0, 
                            2
                        )
                    })
                
                # Create VotingResult without category
                result, created = VotingResult.objects.update_or_create(
                    event=self,
                    category=None,
                    defaults={
                        'winner': winner,
                        'total_votes_cast': total_votes,
                        'total_eligible_voters': self.total_eligible_voters or 0,
                        'voter_turnout_percentage': round(
                            (self.total_votes_cast / self.total_eligible_voters * 100)
                            if self.total_eligible_voters > 0 else 0,
                            2
                        ),
                        'is_published': True,
                        'published_date': timezone.now(),
                        'published_by': published_by,
                        'detailed_results': {
                            'type': 'election',
                            'candidates': detailed_results
                        }
                    }
                )
                results_created.append(result)
        
        return results_created
        
        return results_created


class VotingCategory(models.Model):
    """
    Categories within a voting event
    E.g., "Best Male Student", "Best Female Student", "Course Rep - CS", "Course Rep - IT"
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event = models.ForeignKey(VotingEvent, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=200, help_text="e.g., 'Best Male Student' or 'Course Rep - CS'")
    description = models.TextField(blank=True)
    display_order = models.IntegerField(default=0, help_text="Order to display categories")
    
    # Category-specific settings
    max_votes_allowed = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="How many candidates can a voter select in this category?"
    )
    
    # Eligibility for this specific category
    eligible_years = models.JSONField(
        default=list, 
        blank=True,
        help_text="Override event-level eligibility for this category: [1, 2, 3, 4]"
    )
    eligible_programs = models.JSONField(
        default=list,
        blank=True,
        help_text="Override event-level eligibility for this category"
    )
    
    # Statistics
    total_candidates = models.IntegerField(default=0)
    total_votes = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Voting Category"
        verbose_name_plural = "Voting Categories"
        ordering = ['event', 'display_order', 'name']
        unique_together = [['event', 'name']]
    
    def __str__(self):
        return f"{self.event.title} - {self.name}"


class Candidate(MediaUrlMixin, models.Model):
    """
    Person/option being voted for
    """
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'profile_image': 'profile_image_url',
    }
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disqualified', 'Disqualified'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event = models.ForeignKey(VotingEvent, on_delete=models.CASCADE, related_name='candidates')
    category = models.ForeignKey(
        VotingCategory, 
        on_delete=models.CASCADE, 
        related_name='candidates',
        null=True,
        blank=True,
        help_text="Leave blank for single-category elections"
    )
    
    # Candidate Info
    user_account = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidacies',
        help_text="Link to user account if candidate is a user"
    )
    candidate_name = models.CharField(max_length=200)
    candidate_id = models.CharField(max_length=50, blank=True, help_text="Student ID or unique identifier")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Profile
    bio = models.TextField(blank=True, help_text="Candidate biography/manifesto")
    profile_image = models.ImageField(storage=DynamicStorage(), upload_to="CandidateProfiles/", null=True, blank=True)
    profile_image_url = models.URLField(blank=True, null=True)
    
    # Program/Year Info
    program = models.CharField(max_length=50, blank=True, help_text="CS, IT, etc.")
    year = models.IntegerField(null=True, blank=True, help_text="Year 1, 2, 3, or 4")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, help_text="Internal notes about approval/rejection")
    
    # Voting Results
    vote_count = models.IntegerField(default=0)
    is_winner = models.BooleanField(default=False)
    position = models.IntegerField(null=True, blank=True, help_text="Final position/rank")
    
    # Metadata
    registration_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_candidates'
    )
    
    class Meta:
        verbose_name = "Candidate"
        verbose_name_plural = "Candidates"
        ordering = ['-vote_count', 'candidate_name']
        unique_together = [['event', 'candidate_id']]
    
    def __str__(self):
        category_name = f" - {self.category.name}" if self.category else ""
        return f"{self.candidate_name}{category_name}"


class PollOption(MediaUrlMixin, models.Model):
    """
    Options/choices for poll/referendum type voting events.
    Unlike candidates, poll options are predefined choices users vote on.
    
    For polls: Options can be text statements, choices, etc.
    For referendums: Typically "Yes" and "No" options
    """
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'image': 'image_url',
    }
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event = models.ForeignKey(
        VotingEvent, 
        on_delete=models.CASCADE, 
        related_name='poll_options',
        help_text="The poll/referendum event this option belongs to"
    )
    category = models.ForeignKey(
        VotingCategory, 
        on_delete=models.CASCADE, 
        related_name='poll_options',
        null=True,
        blank=True,
        help_text="For multi-question polls, link to the question category"
    )
    
    # Option Content
    option_text = models.CharField(
        max_length=500, 
        help_text="The option/choice text (e.g., 'Yes', 'No', 'Strongly Agree', etc.)"
    )
    description = models.TextField(
        blank=True, 
        help_text="Optional detailed description or explanation of this option"
    )
    
    # Optional Image (for visual polls)
    image = models.ImageField(storage=DynamicStorage(), upload_to="PollOptions/", null=True, blank=True)
    image_url = models.URLField(blank=True, null=True, help_text="Alternative: Provide image URL")
    
    # Display Settings
    display_order = models.IntegerField(
        default=0, 
        help_text="Order to display options (lower = first)"
    )
    color = models.CharField(
        max_length=7, 
        blank=True, 
        help_text="Hex color for result visualization (e.g., '#4CAF50')"
    )
    
    # Statistics
    vote_count = models.IntegerField(default=0, help_text="Total votes for this option")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Poll Option"
        verbose_name_plural = "Poll Options"
        ordering = ['event', 'category', 'display_order', 'option_text']
        unique_together = [['event', 'category', 'option_text']]
        indexes = [
            models.Index(fields=['event', 'vote_count']),
        ]
    
    def __str__(self):
        category_info = f" ({self.category.name})" if self.category else ""
        return f"{self.option_text}{category_info} - {self.event.title}"
    
    @property
    def percentage(self):
        """Calculate vote percentage for this option"""
        total = self.event.total_votes_cast
        if total == 0:
            return 0
        return round((self.vote_count / total) * 100, 2)


class Vote(models.Model):
    """
    Individual vote cast by a user (supports both authenticated and anonymous voters)
    Supports voting for either candidates (elections/awards) or poll options (polls/referendums)
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event = models.ForeignKey(VotingEvent, on_delete=models.CASCADE, related_name='votes')
    category = models.ForeignKey(
        VotingCategory,
        on_delete=models.CASCADE,
        related_name='votes',
        null=True,
        blank=True
    )
    
    # For elections/awards - vote for a candidate
    candidate = models.ForeignKey(
        Candidate, 
        on_delete=models.CASCADE, 
        related_name='votes_received',
        null=True,
        blank=True,
        help_text="The candidate voted for (for election/awards events)"
    )
    
    # For polls/referendums - vote for a poll option
    poll_option = models.ForeignKey(
        PollOption,
        on_delete=models.CASCADE,
        related_name='votes_received',
        null=True,
        blank=True,
        help_text="The poll option voted for (for poll/referendum events)"
    )
    
    voter = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='votes_cast',
        null=True,  # Allow null for anonymous voters
        blank=True,
        help_text="User who cast the vote (null for anonymous/guest voters)"
    )
    
    # Vote quantity (for vote purchasing)
    vote_quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of votes purchased (default: 1)"
    )
    
    # Payment tracking
    payment_verified = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, blank=True)
    payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Total amount paid for these votes"
    )
    
    # Metadata & Device Fingerprinting
    vote_date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    device_fingerprint = models.CharField(
        max_length=64, 
        blank=True,
        db_index=True,
        help_text="SHA-256 hash of device fingerprint for anonymous vote tracking"
    )
    session_id = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="Session ID for tracking anonymous voters"
    )
    
    class Meta:
        verbose_name = "Vote"
        verbose_name_plural = "Votes"
        ordering = ['-vote_date']
        # NOTE: No unique_together constraint to allow multiple vote purchases
        indexes = [
            models.Index(fields=['event', 'candidate']),
            models.Index(fields=['event', 'poll_option']),
            models.Index(fields=['voter', 'event']),
            models.Index(fields=['payment_reference']),
            models.Index(fields=['event', 'device_fingerprint']),
        ]
    
    def __str__(self):
        voter_name = self.voter.get_full_name() if self.voter else f"Anonymous ({self.ip_address})"
        if self.candidate:
            return f"{voter_name} voted for {self.candidate.candidate_name}"
        elif self.poll_option:
            return f"{voter_name} voted for '{self.poll_option.option_text}'"
        return f"{voter_name} - vote in {self.event.title}"
    
    def clean(self):
        """Validate that either candidate OR poll_option is set, not both"""
        from django.core.exceptions import ValidationError
        
        if self.candidate and self.poll_option:
            raise ValidationError("A vote cannot be for both a candidate and a poll option. Choose one.")
        
        if not self.candidate and not self.poll_option:
            raise ValidationError("A vote must be for either a candidate or a poll option.")
        
        # Validate vote type matches event type
        if self.event.event_type in ['poll', 'referendum']:
            if self.candidate:
                raise ValidationError("Poll/referendum events require voting for poll options, not candidates.")
        else:
            if self.poll_option:
                raise ValidationError("Election/awards events require voting for candidates, not poll options.")


class VoterEligibility(models.Model):
    """
    Track which users are eligible to vote in an event
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event = models.ForeignKey(VotingEvent, on_delete=models.CASCADE, related_name='eligible_voters')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='voting_eligibility')
    
    # Eligibility status
    is_eligible = models.BooleanField(default=True)
    eligibility_reason = models.TextField(blank=True, help_text="Why eligible or not eligible")
    
    # Voting status
    has_voted = models.BooleanField(default=False)
    vote_date = models.DateTimeField(null=True, blank=True)
    
    # Payment status
    payment_required = models.BooleanField(default=False)
    payment_verified = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Voter Eligibility"
        verbose_name_plural = "Voter Eligibilities"
        unique_together = [['event', 'user']]
        indexes = [
            models.Index(fields=['event', 'is_eligible']),
            models.Index(fields=['event', 'has_voted']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.event.title}"


class VotingPayment(models.Model):
    """
    DEPRECATED: This model is deprecated and will be removed in a future version.
    Use the universal payment system (payments.models.Transaction) instead.
    
    Track payments for voting (if event requires payment).
    Integrated with Paystack for online payments (cards, mobile money, bank transfers).
    
    Migration Notes:
    - New payments are handled by payments.models.Transaction with GenericForeignKey
    - This model is kept for backward compatibility with existing data only
    - All new payment operations should use TransactionService from payments app
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('abandoned', 'Abandoned'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('paystack_card', 'Paystack - Card'),
        ('paystack_mobile_money', 'Paystack - Mobile Money'),
        ('paystack_bank', 'Paystack - Bank'),
        ('paystack_ussd', 'Paystack - USSD'),
        ('paystack_bank_transfer', 'Paystack - Bank Transfer'),
        ('paystack_qr', 'Paystack - QR Code'),
        ('manual_cash', 'Manual - Cash'),
        ('manual_transfer', 'Manual - Bank Transfer'),
        ('other', 'Other'),
    ]
    
    CURRENCY_CHOICES = [
        ('GHS', 'Ghana Cedis (GHS)'),
        ('USD', 'US Dollars (USD)'),
        ('NGN', 'Nigerian Naira (NGN)'),
        ('ZAR', 'South African Rand (ZAR)'),
        ('KES', 'Kenyan Shilling (KES)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event = models.ForeignKey(VotingEvent, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='voting_payments')
    
    # Payment details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount in main currency unit (e.g., GHS)"
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='GHS',
        help_text="Currency code"
    )
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES)
    payment_reference = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique payment reference (Paystack or custom)"
    )
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, help_text="Email used for payment")
    
    # Paystack specific fields
    paystack_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Paystack transaction reference"
    )
    paystack_access_code = models.CharField(
        max_length=100,
        blank=True,
        help_text="Paystack access code"
    )
    authorization_url = models.URLField(
        blank=True,
        help_text="Paystack payment URL"
    )
    authorization_code = models.CharField(
        max_length=100,
        blank=True,
        help_text="For recurring payments"
    )
    channel = models.CharField(
        max_length=50,
        blank=True,
        help_text="Payment channel used (card, mobile_money, etc.)"
    )
    card_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Card type if paid with card (Visa, Mastercard, Verve)"
    )
    bank = models.CharField(
        max_length=100,
        blank=True,
        help_text="Bank used for payment"
    )
    gateway_response = models.CharField(
        max_length=255,
        blank=True,
        help_text="Response from payment gateway"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    verified_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_payments'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    payment_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When payment was actually completed"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional payment metadata from Paystack"
    )
    notes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of payment initiator"
    )
    
    class Meta:
        verbose_name = "Voting Payment"
        verbose_name_plural = "Voting Payments"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_reference']),
            models.Index(fields=['paystack_reference']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.currency} {self.amount} ({self.status})"
    
    @property
    def is_successful(self):
        """Check if payment was successful"""
        return self.status in ['success', 'verified']
    
    @property
    def is_pending(self):
        """Check if payment is still pending"""
        return self.status in ['pending', 'processing']
    
    @property
    def formatted_amount(self):
        """Get formatted amount with currency"""
        return f"{self.currency} {self.amount:.2f}"


class VotingResult(models.Model):
    """
    Final results for an event/category
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event = models.ForeignKey(VotingEvent, on_delete=models.CASCADE, related_name='results')
    category = models.ForeignKey(
        VotingCategory,
        on_delete=models.CASCADE,
        related_name='results',
        null=True,
        blank=True
    )
    
    # Winner(s)
    winner = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='won_results',
        null=True,
        blank=True
    )
    
    # Results data
    total_votes_cast = models.IntegerField(default=0)
    total_eligible_voters = models.IntegerField(default=0)
    voter_turnout_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Percentage of eligible voters who voted"
    )
    
    # Publication
    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='published_results'
    )
    
    # Detailed results (JSON)
    detailed_results = models.JSONField(
        default=dict,
        help_text="Full breakdown of votes per candidate"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Voting Result"
        verbose_name_plural = "Voting Results"
        unique_together = [['event', 'category']]
    
    def __str__(self):
        category_name = f" - {self.category.name}" if self.category else ""
        return f"Results: {self.event.title}{category_name}"
