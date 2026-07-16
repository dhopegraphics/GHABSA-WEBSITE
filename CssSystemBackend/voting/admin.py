"""
Admin interface for Voting System
Executives can manage voting events, candidates, and payments
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    VotingEvent, VotingCategory, Candidate, Vote,
    VoterEligibility, VotingPayment, VotingResult, PollOption
)
from utils.media_mixins import make_media_admin_mixin

# Create media admin mixins for models with file fields
VotingEventMediaAdminMixin = make_media_admin_mixin(['banner_image'])
CandidateMediaAdminMixin = make_media_admin_mixin(['profile_image'])
PollOptionMediaAdminMixin = make_media_admin_mixin(['image'])


@admin.register(VotingEvent)
class VotingEventAdmin(VotingEventMediaAdminMixin, admin.ModelAdmin):
    list_display = [
        'title', 'event_type', 'status', 'registration_open', 'voting_open',
        'voting_start_date', 'voting_end_date', 'total_votes_cast', 'requires_payment'
    ]
    list_filter = ['event_type', 'status', 'visibility', 'registration_open', 'voting_open', 'requires_payment', 'created_at']
    list_editable = ['registration_open', 'voting_open']  # Quick toggle from list view
    search_fields = ['title', 'description', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = [
        'id', 'total_registered_candidates', 'total_eligible_voters',
        'total_votes_cast', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id', 'title', 'slug', 'description', 'event_type',
                'status', 'visibility'
            )
        }),
        ('Banner/Visual', {
            'fields': ('banner_image', 'banner_image_url'),
            'classes': ('collapse',)
        }),
        ('🔘 Open/Close Controls', {
            'fields': ('registration_open', 'voting_open'),
            'description': 'Master switches: Toggle these to open/close registration or voting instantly. When OFF, dates are ignored.'
        }),
        ('Schedule (Only applies when switches are ON)', {
            'fields': (
                'registration_start_date', 'registration_end_date',
                'voting_start_date', 'voting_end_date'
            )
        }),
        ('Eligibility', {
            'fields': ('eligible_years', 'eligible_programs'),
            'description': 'Leave empty for public access to all students. Use [1, 2, 3, 4] for years.'
        }),
        ('Payment Configuration', {
            'fields': ('requires_payment', 'voting_fee', 'allow_multiple_vote_purchase'),
            'classes': ('collapse',)
        }),
        ('Voting Settings', {
            'fields': (
                'requires_authentication', 'allow_multiple_votes', 'allow_candidate_self_voting',
                'show_live_results', 'anonymous_voting', 'max_votes_per_category'
            ),
            'description': 'requires_authentication: If unchecked, anonymous users can vote (with device fingerprint tracking).'
        }),
        ('Statistics', {
            'fields': (
                'total_registered_candidates', 'total_eligible_voters',
                'total_votes_cast'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['generate_results', 'publish_results', 'recalculate_eligible_voters']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new event
            obj.created_by = request.user
        
        # Auto-calculate eligible voters when event is saved
        # Calculate before checking status change so results have accurate turnout
        obj.total_eligible_voters = obj.calculate_eligible_voters()
        
        # Check if status changed to 'results_published'
        if change and 'status' in form.changed_data:
            if obj.status == 'results_published':
                # Auto-generate results when publishing
                obj.generate_results(published_by=request.user)
        
        super().save_model(request, obj, form, change)
    
    @admin.action(description='Recalculate Eligible Voters for selected events')
    def recalculate_eligible_voters(self, request, queryset):
        total_updated = 0
        for event in queryset:
            event.update_eligible_voters_count()
            total_updated += 1
        self.message_user(
            request,
            f"Recalculated eligible voters for {total_updated} event(s)."
        )
    
    @admin.action(description='Generate/Update Results for selected events')
    def generate_results(self, request, queryset):
        total_results = 0
        for event in queryset:
            results = event.generate_results(published_by=request.user)
            total_results += len(results)
        self.message_user(
            request,
            f"Generated {total_results} result(s) for {queryset.count()} event(s)."
        )
    
    @admin.action(description='Publish Results (generate + set status)')
    def publish_results(self, request, queryset):
        total_results = 0
        for event in queryset:
            results = event.generate_results(published_by=request.user)
            event.status = 'results_published'
            event.voting_open = False  # Close voting
            event.save()
            total_results += len(results)
        self.message_user(
            request,
            f"Published {total_results} result(s) for {queryset.count()} event(s). Status set to 'Results Published'."
        )


@admin.register(VotingCategory)
class VotingCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'event', 'event_type_display', 'display_order', 'total_candidates',
        'total_votes', 'max_votes_allowed'
    ]
    list_filter = ['event', 'event__event_type']
    search_fields = ['name', 'description', 'event__title']
    readonly_fields = ['id', 'total_candidates', 'total_votes', 'created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'event', 'name', 'description', 'display_order')
        }),
        ('Voting Settings', {
            'fields': ('max_votes_allowed',)
        }),
        ('Category-Specific Eligibility', {
            'fields': ('eligible_years', 'eligible_programs'),
            'description': 'Override event-level eligibility for this category. Use [1, 2, 3, 4] for years.',
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('total_candidates', 'total_votes'),
            'classes': ('collapse',)
        }),
    )
    
    def event_type_display(self, obj):
        return obj.event.get_event_type_display()
    event_type_display.short_description = 'Event Type'


class PollOptionInline(admin.TabularInline):
    """Inline admin for managing poll options within a category"""
    model = PollOption
    extra = 0
    fields = ['option_text', 'description', 'display_order', 'color', 'vote_count']
    readonly_fields = ['vote_count']


@admin.register(PollOption)
class PollOptionAdmin(PollOptionMediaAdminMixin, admin.ModelAdmin):
    """Admin for poll/referendum options"""
    list_display = [
        'option_text', 'event', 'category', 'display_order',
        'vote_count', 'percentage_display', 'color_preview'
    ]
    list_filter = ['event', 'event__event_type', 'category', 'created_at']
    search_fields = ['option_text', 'description', 'event__title', 'category__name']
    readonly_fields = ['id', 'vote_count', 'created_at', 'updated_at']
    list_editable = ['display_order']
    ordering = ['event', 'category', 'display_order']
    
    fieldsets = (
        ('Event & Category', {
            'fields': ('id', 'event', 'category'),
            'description': 'For single-question polls, leave category empty. For multi-question polls, select the question category.'
        }),
        ('Option Content', {
            'fields': ('option_text', 'description')
        }),
        ('Visual', {
            'fields': ('image', 'image_url', 'color'),
            'description': 'Optional: Add an image or color for visual polls/charts.',
            'classes': ('collapse',)
        }),
        ('Display & Order', {
            'fields': ('display_order',)
        }),
        ('Statistics', {
            'fields': ('vote_count',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def percentage_display(self, obj):
        return f"{obj.percentage}%"
    percentage_display.short_description = 'Vote %'
    
    def color_preview(self, obj):
        if obj.color:
            return format_html(
                '<span style="background-color: {}; padding: 2px 10px; border-radius: 3px;">&nbsp;</span>',
                obj.color
            )
        return '-'
    color_preview.short_description = 'Color'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('event', 'category')


@admin.register(Candidate)
class CandidateAdmin(CandidateMediaAdminMixin, admin.ModelAdmin):
    list_display = [
        'candidate_name', 'event', 'category', 'program', 'year',
        'status', 'vote_count', 'is_winner'
    ]
    list_filter = [
        'status', 'event', 'category', 'program', 'year',
        'is_winner', 'registration_date'
    ]
    search_fields = [
        'candidate_name', 'candidate_id', 'email', 'phone', 'bio'
    ]
    readonly_fields = [
        'id', 'registration_date', 'vote_count', 'approved_date',
        'approved_by', 'is_winner', 'position'
    ]
    
    fieldsets = (
        ('Event Information', {
            'fields': ('id', 'event', 'category')
        }),
        ('Candidate Details', {
            'fields': (
                'user_account', 'candidate_name', 'candidate_id',
                'email', 'phone', 'program', 'year'
            )
        }),
        ('Profile', {
            'fields': ('bio', 'profile_image', 'profile_image_url')
        }),
        ('Approval Status', {
            'fields': (
                'status', 'admin_notes', 'approved_date', 'approved_by'
            )
        }),
        ('Results', {
            'fields': ('vote_count', 'is_winner', 'position'),
            'classes': ('collapse',),
            'description': '⚠️ Vote counts and winners are automatically calculated. Cannot be manually edited.'
        }),
    )
    
    actions = ['approve_candidates', 'reject_candidates']
    
    def save_model(self, request, obj, form, change):
        if obj.status == 'approved' and not obj.approved_date:
            obj.approved_date = timezone.now()
            obj.approved_by = request.user
        super().save_model(request, obj, form, change)
    
    def approve_candidates(self, request, queryset):
        updated = queryset.update(
            status='approved',
            approved_date=timezone.now()
        )
        # Set approved_by for each
        for candidate in queryset:
            candidate.approved_by = request.user
            candidate.save()
        self.message_user(request, f'{updated} candidate(s) approved.')
    approve_candidates.short_description = "Approve selected candidates"
    
    def reject_candidates(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} candidate(s) rejected.')
    reject_candidates.short_description = "Reject selected candidates"


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = [
        'voter_name', 'event', 'category', 'vote_target',
        'vote_quantity', 'vote_date', 'payment_verified'
    ]
    list_filter = [
        'event', 'category', 'payment_verified', 'vote_date',
        'event__event_type'
    ]
    search_fields = [
        'voter__phone', 'voter__first_name', 'voter__last_name',
        'candidate__candidate_name', 'poll_option__option_text',
        'payment_reference', 'device_fingerprint'
    ]
    readonly_fields = [
        'id', 'event', 'category', 'candidate', 'poll_option', 'voter',
        'vote_quantity', 'vote_date', 'ip_address', 'user_agent',
        'device_fingerprint', 'session_id', 'payment_verified',
        'payment_reference', 'payment_amount'
    ]
    
    fieldsets = (
        ('Vote Information', {
            'fields': ('id', 'event', 'category', 'candidate', 'poll_option', 'voter', 'vote_quantity')
        }),
        ('Payment', {
            'fields': ('payment_verified', 'payment_reference', 'payment_amount'),
            'description': '⚠️ Payment verification is handled by the universal payment system.'
        }),
        ('Metadata', {
            'fields': ('vote_date', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def voter_name(self, obj):
        if obj.voter:
            return obj.voter.get_full_name() or obj.voter.email
        return f"Anonymous ({obj.ip_address or 'Unknown'})"
    voter_name.short_description = 'Voter'
    
    def vote_target(self, obj):
        """Display what was voted for - candidate or poll option"""
        if obj.candidate:
            return f"🗳️ {obj.candidate.candidate_name}"
        elif obj.poll_option:
            return f"📊 {obj.poll_option.option_text}"
        return "-"
    vote_target.short_description = 'Voted For'
    
    def has_add_permission(self, request):
        """Votes can only be cast through the API, not manually created."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """
        Votes cannot be individually deleted to maintain audit trail.
        However, superusers can delete (needed for cascade deletes when deleting events).
        """
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Votes are readonly - cannot be modified after casting."""
        return False


@admin.register(VoterEligibility)
class VoterEligibilityAdmin(admin.ModelAdmin):
    list_display = [
        'user_name', 'event', 'is_eligible', 'has_voted',
        'payment_required', 'payment_verified'
    ]
    list_filter = [
        'event', 'is_eligible', 'has_voted', 'payment_required',
        'payment_verified', 'created_at'
    ]
    search_fields = [
        'user__phone', 'user__first_name', 'user__last_name',
        'event__title', 'payment_reference'
    ]
    readonly_fields = [
        'id', 'created_at', 'vote_date', 'has_voted',
        'payment_verified', 'payment_reference', 'payment_date'
    ]
    
    fieldsets = (
        ('Event & User', {
            'fields': ('id', 'event', 'user')
        }),
        ('Eligibility', {
            'fields': ('is_eligible', 'eligibility_reason')
        }),
        ('Voting Status', {
            'fields': ('has_voted', 'vote_date'),
            'description': '⚠️ Voting status is automatically updated when votes are cast.'
        }),
        ('Payment Status', {
            'fields': (
                'payment_required', 'payment_verified',
                'payment_reference', 'payment_date'
            ),
            'description': '⚠️ Payment verification is handled by the universal payment system.'
        }),
    )
    
    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = 'User'
    
    actions = ['mark_as_eligible']
    
    def mark_as_eligible(self, request, queryset):
        updated = queryset.update(is_eligible=True)
        self.message_user(request, f'{updated} voter(s) marked as eligible.')
    mark_as_eligible.short_description = "Mark as eligible"


@admin.register(VotingPayment)
class VotingPaymentAdmin(admin.ModelAdmin):
    """
    ⚠️ DEPRECATED: This model is kept for historical data only.
    All new payments are handled by the universal payment system (payments app).
    Admin can view but not create/edit/delete.
    """
    list_display = [
        'user_name', 'event', 'amount', 'payment_method',
        'status', 'payment_date', 'verified_by'
    ]
    list_filter = [
        'status', 'payment_method', 'event', 'payment_date'
    ]
    search_fields = [
        'user__phone', 'user__first_name', 'user__last_name',
        'payment_reference', 'phone_number'
    ]
    readonly_fields = [
        'id', 'event', 'user', 'amount', 'payment_method',
        'payment_reference', 'phone_number', 'status',
        'verified_by', 'payment_date', 'verified_at', 'notes'
    ]
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'id', 'event', 'user', 'amount', 'payment_method',
                'payment_reference', 'phone_number'
            )
        }),
        ('Verification', {
            'fields': ('status', 'verified_by', 'verified_at', 'notes')
        }),
    )
    
    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = 'User'
    
    def has_add_permission(self, request):
        """Deprecated model - no new records should be created."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Historical payment records must be preserved."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Deprecated model - use universal payment system instead."""
        return False


@admin.register(VotingResult)
class VotingResultAdmin(admin.ModelAdmin):
    list_display = [
        'event', 'category', 'winner', 'total_votes_cast',
        'voter_turnout_percentage', 'is_published'
    ]
    list_filter = ['event', 'is_published', 'published_date']
    search_fields = ['event__title', 'category__name', 'winner__candidate_name']
    readonly_fields = [
        'id', 'created_at', 'published_date', 'published_by',
        'event', 'category', 'winner', 'total_votes_cast',
        'total_eligible_voters', 'voter_turnout_percentage',
        'detailed_results'
    ]
    
    fieldsets = (
        ('Result Information', {
            'fields': ('id', 'event', 'category', 'winner'),
            'description': '⚠️ Results are automatically calculated based on vote counts.'
        }),
        ('Statistics', {
            'fields': (
                'total_votes_cast', 'total_eligible_voters',
                'voter_turnout_percentage', 'detailed_results'
            )
        }),
        ('Publication', {
            'fields': ('is_published', 'published_date', 'published_by'),
            'description': 'Admins can only publish/unpublish results, not modify them.'
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if obj.is_published and not obj.published_date:
            obj.published_date = timezone.now()
            obj.published_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_add_permission(self, request):
        """Results are automatically generated, not manually created."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete result records."""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Can only publish/unpublish results, not modify the data."""
        if obj is None:
            return True
        # Allow changing only the is_published field
        return True
    
    def get_readonly_fields(self, request, obj=None):
        """Make all fields readonly except is_published."""
        if obj:  # Editing existing result
            return self.readonly_fields
        return self.readonly_fields
    
    actions = ['publish_results', 'unpublish_results']
    
    def publish_results(self, request, queryset):
        for result in queryset:
            result.is_published = True
            result.published_date = timezone.now()
            result.published_by = request.user
            result.save()
        self.message_user(request, f'{queryset.count()} result(s) published.')
    publish_results.short_description = "Publish selected results"
    
    def unpublish_results(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} result(s) unpublished.')
    unpublish_results.short_description = "Unpublish selected results"
