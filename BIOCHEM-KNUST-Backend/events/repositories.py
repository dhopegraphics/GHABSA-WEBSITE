from events.models import (
    Event, EventRSVP, EventRegistration, TeamMember,
    SyncMemoAlbum, SyncMemoPhoto, SyncMemoComment
)
from django.utils import timezone
from django.db.models import Q, Count, Prefetch, Case, When
from django.db import models


class EventRepo:
    """Repository for Event model queries"""
    model = Event.objects

    @classmethod
    def get_all_events(cls):
        """Get all events with related data prefetched"""
        return cls.model.select_related().prefetch_related(
            'timeline',
            'rsvps',
            'registrations',
            'sync_memo_album'
        ).all()
    
    @classmethod
    def get_all_events_sorted(cls):
        """Get all events sorted for optimal frontend display
        Order: upcoming (nearest first) -> ongoing -> past (most recent first)
        """
        from django.utils import timezone
        
        now = timezone.now()
        
        # Get each category separately with proper sorting
        upcoming_events = cls.get_upcoming_events()  # Already sorted ascending
        ongoing_events = cls.get_ongoing_events()    # Already sorted ascending  
        past_events = cls.get_past_events()          # Already sorted descending
        
        # Combine them in the right order
        # Convert to lists to avoid multiple database hits
        upcoming_list = list(upcoming_events)
        ongoing_list = list(ongoing_events)
        past_list = list(past_events)
        
        # Create a combined queryset-like result
        # Since Django doesn't easily let us combine different orderings,
        # we'll return the concatenated list
        combined = upcoming_list + ongoing_list + past_list
        
        # Convert back to a QuerySet for consistency with other methods
        # Get all IDs in the correct order
        if combined:
            ordered_ids = [event.event_id for event in combined]
            preserved_order = Case(
                *[When(event_id=pk, then=pos) for pos, pk in enumerate(ordered_ids)]
            )
            return cls.model.filter(event_id__in=ordered_ids).annotate(
                preserved=preserved_order
            ).order_by('preserved').select_related().prefetch_related(
                'timeline', 'rsvps', 'registrations', 'sync_memo_album'
            )
        else:
            return cls.model.none()

    @classmethod
    def get_ongoing_events(cls):
        """Get events that are currently ongoing"""
        now = timezone.now()
        
        # Events with end_date: current time is between start and end
        ongoing_with_end = Q(
            event_date__lte=now,
            event_end_date__gte=now
        )
        
        # Events without end_date: event has started (event_date <= now) and still on the same day
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        ongoing_single_day = Q(
            event_date__lte=now,  # Event must have started
            event_date__gte=today_start,  # Event started today
            event_end_date__isnull=True
        )
        
        return cls.model.filter(ongoing_with_end | ongoing_single_day).order_by('event_date')

    @classmethod
    def get_upcoming_events(cls):
        """Get events that haven't started yet"""
        now = timezone.now()
        return cls.model.filter(event_date__gt=now).order_by('event_date')

    @classmethod
    def get_past_events(cls):
        """Get events that have ended"""
        now = timezone.now()
        
        # Events with end_date: end_date has passed
        past_with_end = Q(event_end_date__lt=now)
        
        # Events without end_date: event_date day has passed
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        past_single_day = Q(
            event_date__lt=today_start,
            event_end_date__isnull=True
        )
        
        return cls.model.filter(past_with_end | past_single_day).order_by('-event_date')
    
    @classmethod
    def get_featured_events(cls):
        """Get featured events"""
        return cls.model.filter(featured=True).order_by('-event_date')
    
    @classmethod
    def get_events_by_type(cls, event_type):
        """Get events filtered by type"""
        return cls.model.filter(event_type=event_type).order_by('-event_date')
    
    @classmethod
    def get_user_rsvp_events(cls, user):
        """Get events user has RSVP'd to"""
        return cls.model.filter(
            rsvps__user=user,
            rsvps__status='attending'
        ).distinct().order_by('-event_date')
    
    @classmethod
    def get_user_registered_events(cls, user):
        """Get events user is registered for"""
        return cls.model.filter(
            registrations__user=user,
            registrations__status__in=['confirmed', 'pending']
        ).distinct().order_by('-event_date')
    
    @classmethod
    def search_events(cls, query):
        """Search events by name, description, or organizer"""
        return cls.model.filter(
            Q(event_name__icontains=query) |
            Q(description__icontains=query) |
            Q(organised_by__icontains=query)
        ).order_by('-event_date')


class EventRSVPRepo:
    """Repository for EventRSVP model queries"""
    model = EventRSVP.objects
    
    @classmethod
    def get_user_rsvp(cls, event, user):
        """Get user's RSVP for an event"""
        return cls.model.filter(event=event, user=user).first()
    
    @classmethod
    def get_event_attendees(cls, event, status=None):
        """Get attendees for an event, optionally filtered by status"""
        queryset = cls.model.filter(event=event).select_related('user')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')
    
    @classmethod
    def get_attending_count(cls, event):
        """Get count of users attending an event"""
        return cls.model.filter(event=event, status='attending').count()


class EventRegistrationRepo:
    """Repository for EventRegistration model queries"""
    model = EventRegistration.objects
    
    @classmethod
    def get_user_registration(cls, event, user):
        """Get user's registration for an event"""
        return cls.model.filter(event=event, user=user).first()
    
    @classmethod
    def get_event_registrations(cls, event, status=None):
        """Get registrations for an event"""
        queryset = cls.model.filter(event=event).select_related('user').prefetch_related('team_members')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')
    
    @classmethod
    def get_confirmed_count(cls, event):
        """Get count of confirmed registrations"""
        return cls.model.filter(event=event, status='confirmed').count()
    
    @classmethod
    def get_team_registrations(cls, event):
        """Get team registrations for an event"""
        return cls.model.filter(
            event=event,
            is_team_leader=True
        ).prefetch_related('team_members')


class SyncMemoRepo:
    """Repository for Sync Memo (photo gallery) queries"""
    
    @classmethod
    def get_or_create_album(cls, event):
        """Get or create album for an event"""
        album, created = SyncMemoAlbum.objects.get_or_create(
            event=event,
            defaults={
                'title': f"{event.event_name} Photos",
                'description': f"Photo gallery for {event.event_name}",
            }
        )
        return album
    
    @classmethod
    def get_live_albums(cls):
        """Get all live photo albums"""
        return SyncMemoAlbum.objects.filter(
            status='live'
        ).select_related('event').prefetch_related(
            'photos'
        ).order_by('-created_at')
    
    @classmethod
    def get_album_photos(cls, album, approved_only=True):
        """Get photos for an album"""
        queryset = SyncMemoPhoto.objects.filter(album=album).select_related(
            'uploaded_by'
        ).prefetch_related('likes', 'comments')
        
        if approved_only:
            queryset = queryset.filter(is_approved=True)
        
        return queryset.order_by('-created_at')
    
    @classmethod
    def get_photo_comments(cls, photo):
        """Get comments for a photo"""
        return SyncMemoComment.objects.filter(
            photo=photo
        ).select_related('user').prefetch_related('comment_likes').order_by('created_at')
