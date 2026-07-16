"""
Django signals for Code Quest system
Handles automatic notifications when group-related changes occur
"""
import logging
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.db import transaction


logger = logging.getLogger(__name__)


@receiver(post_save, sender='codequest.CodeQuestParticipant')
def on_participant_group_assigned(sender, instance, **kwargs):
    """
    When a participant is assigned to a group, check if the group
    is now complete and send notifications to all members.
    """
    from codequest.utils import check_and_notify_group_completion
    
    # Skip if no group assigned
    if not instance.group:
        return
    
    # Skip if this is a new participant (group assignment usually happens in a separate save)
    if kwargs.get('created', False):
        return
    
    # Check if group field was updated
    if hasattr(instance, '_loaded_values'):
        old_group_id = instance._loaded_values.get('group_id')
        if old_group_id == instance.group_id:
            return  # Group hasn't changed
    
    # Use transaction.on_commit to ensure DB is in consistent state
    transaction.on_commit(lambda: _check_group_completion(instance.group_id))


def _check_group_completion(group_id):
    """
    Helper function to check and notify group completion.
    Called after transaction commits.
    """
    from codequest.models import CodeQuestGroup
    from codequest.utils import check_and_notify_group_completion
    
    try:
        group = CodeQuestGroup.objects.get(id=group_id)
        notified, message = check_and_notify_group_completion(group)
        
        if notified:
            logger.info(f"Group {group.group_number} formation complete: {message}")
        
    except CodeQuestGroup.DoesNotExist:
        logger.warning(f"Group {group_id} not found for completion check")
    except Exception as e:
        logger.error(f"Error checking group completion for group {group_id}: {str(e)}")


@receiver(post_save, sender='codequest.ProjectManagerCandidate')
def on_pm_winner_declared(sender, instance, **kwargs):
    """
    When a PM candidate is marked as winner, send notifications to all group members
    """
    from codequest.utils import send_pm_election_result_email
    
    # Only proceed if this candidate was marked as winner
    if not instance.is_winner:
        return
    
    # Skip if this is not an update (created=False for updates)
    if kwargs.get('created', False):
        return
    
    group = instance.group
    winner = instance.participant
    
    # Send notifications to all group members
    transaction.on_commit(lambda: _notify_pm_election_results(group.id, winner.id))


def _notify_pm_election_results(group_id, winner_id):
    """
    Helper function to send PM election result notifications.
    Called after transaction commits.
    """
    from codequest.models import CodeQuestGroup, CodeQuestParticipant
    from codequest.utils import send_pm_election_result_email
    
    try:
        group = CodeQuestGroup.objects.get(id=group_id)
        winner = CodeQuestParticipant.objects.get(id=winner_id)
        members = group.members.all()
        
        success_count = 0
        for member in members:
            success, message = send_pm_election_result_email(member, group, winner)
            if success:
                success_count += 1
        
        logger.info(
            f"PM election result notifications sent for {group.group_number}: "
            f"{success_count}/{members.count()} successful"
        )
        
    except Exception as e:
        logger.error(f"Error sending PM election result notifications: {str(e)}")


@receiver(post_save, sender='codequest.CodeQuestEvent')
def on_event_status_change(sender, instance, **kwargs):
    """
    When event status changes to 'voting', notify all participants
    """
    from codequest.utils import send_pm_election_start_email
    
    # Skip if this is a new event
    if kwargs.get('created', False):
        return
    
    # Check if status changed to voting
    if instance.status != 'voting':
        return
    
    # Check if this was actually a status change
    if hasattr(instance, '_loaded_values'):
        old_status = instance._loaded_values.get('status')
        if old_status == 'voting':
            return  # Status hasn't changed
    
    # Notify all participants in groups
    transaction.on_commit(lambda: _notify_voting_started(instance.id))


def _notify_voting_started(event_id):
    """
    Helper function to send voting started notifications.
    Called after transaction commits.
    """
    from codequest.models import CodeQuestEvent, CodeQuestParticipant
    from codequest.utils import send_pm_election_start_email
    
    try:
        event = CodeQuestEvent.objects.get(id=event_id)
        
        # Get all participants who are assigned to groups
        participants = CodeQuestParticipant.objects.filter(
            event=event,
            group__isnull=False
        ).select_related('group')
        
        success_count = 0
        for participant in participants:
            success, message = send_pm_election_start_email(participant, participant.group)
            if success:
                success_count += 1
        
        logger.info(
            f"PM election start notifications sent for event {event_id}: "
            f"{success_count}/{participants.count()} successful"
        )
        
    except Exception as e:
        logger.error(f"Error sending voting started notifications: {str(e)}")


# =============================================================================
# Model tracking for detecting field changes
# =============================================================================

def track_model_fields(*fields):
    """
    Decorator to track specific fields for change detection in signals.
    Call this on post_init to store original values.
    """
    def decorator(func):
        def wrapper(sender, instance, **kwargs):
            instance._loaded_values = {}
            for field in fields:
                if hasattr(instance, field):
                    value = getattr(instance, field)
                    # Handle foreign keys
                    if hasattr(value, 'id'):
                        instance._loaded_values[f'{field}_id'] = value.id
                    else:
                        instance._loaded_values[field] = value
            return func(sender, instance, **kwargs)
        return wrapper
    return decorator


# Connect post_init signals to track field changes
from django.db.models.signals import post_init

@receiver(post_init, sender='codequest.CodeQuestParticipant')
def track_participant_fields(sender, instance, **kwargs):
    """Track group_id field for change detection"""
    instance._loaded_values = {
        'group_id': instance.group_id if instance.pk else None
    }


@receiver(post_init, sender='codequest.CodeQuestEvent')
def track_event_fields(sender, instance, **kwargs):
    """Track status field for change detection"""
    instance._loaded_values = {
        'status': instance.status if instance.pk else None
    }


@receiver(post_init, sender='codequest.ProjectManagerCandidate')
def track_pm_candidate_fields(sender, instance, **kwargs):
    """Track is_winner field for change detection"""
    instance._loaded_values = {
        'is_winner': instance.is_winner if instance.pk else None
    }
