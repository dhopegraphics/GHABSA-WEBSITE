"""
Utility functions for Code Quest system
Includes grouping algorithm, score calculation, and other helper functions
"""
import random
import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.conf import settings


logger = logging.getLogger(__name__)


def validate_group_membership(group, participant=None):
    """
    Validate if a group can accept more members based on event settings.
    
    Args:
        group: CodeQuestGroup instance
        participant: Optional CodeQuestParticipant to check if they can join
    
    Returns:
        Tuple (can_add: bool, message: str)
    """
    event = group.event
    min_size = event.min_group_size or 5
    max_size = event.max_group_size
    current_count = group.members.count()
    
    # Check if max size would be exceeded
    if max_size and current_count >= max_size:
        return (False, f"Group is full ({current_count}/{max_size} members)")
    
    # Check if participant is already in a group
    if participant and participant.group:
        if participant.group.id == group.id:
            return (False, "Participant is already in this group")
        return (False, f"Participant is already in {participant.group.group_number}")
    
    return (True, f"Group can accept members ({current_count}/{max_size or '∞'})")


def get_group_capacity_info(group):
    """
    Get detailed capacity information for a group.
    
    Args:
        group: CodeQuestGroup instance
    
    Returns:
        Dictionary with capacity details
    """
    event = group.event
    min_size = event.min_group_size or 5
    max_size = event.max_group_size
    current_count = group.members.count()
    
    return {
        'current_members': current_count,
        'min_size': min_size,
        'max_size': max_size,
        'is_minimum_met': current_count >= min_size,
        'is_full': max_size and current_count >= max_size,
        'spots_remaining': (max_size - current_count) if max_size else None,
        'members_needed': max(0, min_size - current_count),
    }


def group_participants_automatically(event, participants, max_group_size=None, min_group_size=None):
    """
    Automatically group participants into balanced groups.
    Uses event settings for min/max group size if not explicitly provided.
    
    Args:
        event: CodeQuestEvent instance
        participants: QuerySet of CodeQuestParticipant instances
        max_group_size: Maximum number of members per group (defaults to event.max_group_size)
        min_group_size: Minimum number of members per group (defaults to event.min_group_size)
    
    Returns:
        List of created CodeQuestGroup instances
    """
    from codequest.models import CodeQuestGroup
    
    # Use event settings if not explicitly provided
    if min_group_size is None:
        min_group_size = event.min_group_size or 5
    if max_group_size is None:
        max_group_size = event.max_group_size or 10
    
    logger.info(
        f"Auto-grouping {participants.count()} participants for {event}: "
        f"min_size={min_group_size}, max_size={max_group_size}"
    )
    
    # Separate participants by category
    regular_students = list(participants.filter(year=2, is_deferred=False))
    deferred_students = list(participants.filter(is_deferred=True))
    
    # Shuffle for random distribution
    random.shuffle(regular_students)
    random.shuffle(deferred_students)
    
    groups_created = []
    group_number = 1
    
    def create_groups_from_list(students, category, start_num):
        """Helper function to create groups from a list of students"""
        local_groups = []
        current_num = start_num
        
        total_students = len(students)
        if total_students == 0:
            return local_groups, current_num
        
        # Calculate number of groups needed
        num_groups = max(1, (total_students + max_group_size - 1) // max_group_size)
        
        # Calculate target size per group
        target_size = total_students // num_groups
        remainder = total_students % num_groups
        
        start_idx = 0
        for i in range(num_groups):
            # Some groups get one extra member if there's a remainder
            group_size = target_size + (1 if i < remainder else 0)
            
            if group_size < min_group_size and i == num_groups - 1:
                # Last group too small, merge with previous
                if local_groups:
                    prev_group = local_groups[-1]
                    group_members = students[start_idx:]
                    # Add to previous group
                    for student in group_members:
                        student.group = prev_group
                        student.save()
                    break
            
            group_members = students[start_idx:start_idx + group_size]
            start_idx += group_size
            
            # Create group
            group = CodeQuestGroup.objects.create(
                event=event,
                group_number=f"Group {current_num}",
                category=category
            )
            
            # Assign members to group
            for student in group_members:
                student.group = group
                student.save()
            
            local_groups.append(group)
            current_num += 1
        
        return local_groups, current_num
    
    with transaction.atomic():
        # Create groups for regular students
        if regular_students:
            regular_groups, group_number = create_groups_from_list(
                regular_students, 
                'regular', 
                group_number
            )
            groups_created.extend(regular_groups)
        
        # Create groups for deferred students
        if deferred_students:
            deferred_groups, group_number = create_groups_from_list(
                deferred_students, 
                'deferred_only', 
                group_number
            )
            groups_created.extend(deferred_groups)
    
    return groups_created


def assign_consultants_randomly(event, consultants, groups):
    """
    Randomly assign consultants to groups
    
    Args:
        event: CodeQuestEvent instance
        consultants: QuerySet of CodeQuestConsultant instances
        groups: QuerySet of CodeQuestGroup instances
    
    Returns:
        List of ConsultantGroupAssignment instances
    """
    from codequest.models import ConsultantGroupAssignment
    
    consultant_list = list(consultants.filter(is_approved=True))
    group_list = list(groups.all())
    
    if not consultant_list or not group_list:
        return []
    
    random.shuffle(group_list)
    
    assignments = []
    consultant_idx = 0
    
    with transaction.atomic():
        for group in group_list:
            # Cycle through consultants
            consultant = consultant_list[consultant_idx % len(consultant_list)]
            
            # Create assignment
            assignment = ConsultantGroupAssignment.objects.create(
                consultant=consultant,
                group=group,
                is_active=True
            )
            
            # Update group's consultant field
            group.consultant = consultant
            group.save()
            
            assignments.append(assignment)
            consultant_idx += 1
    
    return assignments


def calculate_project_scores(project):
    """
    Calculate final score for a project based on all facilitator scores
    
    Args:
        project: CodeQuestProject instance
    
    Returns:
        FinalProjectScore instance
    """
    from codequest.models import FinalProjectScore, ProjectScore, ScoringCriteria
    from django.db.models import Avg, Sum
    
    event = project.group.event
    criteria_list = ScoringCriteria.objects.filter(event=event, is_active=True)
    
    if not criteria_list.exists():
        # No criteria defined
        return None
    
    total_weighted_score = Decimal('0.00')
    
    for criteria in criteria_list:
        # Get average score from all facilitators for this criteria
        avg_score = ProjectScore.objects.filter(
            project=project,
            criteria=criteria
        ).aggregate(avg=Avg('score'))['avg']
        
        if avg_score is not None:
            # Apply percentage weight
            weighted_score = (Decimal(str(avg_score)) / Decimal(str(criteria.max_points))) * criteria.percentage_weight
            total_weighted_score += weighted_score
    
    # Get or create final score record
    final_score, created = FinalProjectScore.objects.get_or_create(
        project=project,
        defaults={
            'total_score': total_weighted_score,
            'average_score': total_weighted_score,
        }
    )
    
    if not created:
        final_score.total_score = total_weighted_score
        final_score.average_score = total_weighted_score
        final_score.calculation_date = timezone.now()
        final_score.save()
    
    return final_score


def rank_all_projects(event):
    """
    Rank all projects in an event by total score
    
    Args:
        event: CodeQuestEvent instance
    
    Returns:
        List of FinalProjectScore instances (ordered by rank)
    """
    from codequest.models import FinalProjectScore, CodeQuestProject
    
    # Get all projects for this event
    projects = CodeQuestProject.objects.filter(
        group__event=event,
        is_approved=True
    )
    
    # Calculate scores for all projects
    for project in projects:
        calculate_project_scores(project)
    
    # Get all final scores and order by total score
    final_scores = FinalProjectScore.objects.filter(
        project__group__event=event
    ).order_by('-total_score', 'project__submission_date')
    
    # Assign ranks
    with transaction.atomic():
        for rank, final_score in enumerate(final_scores, start=1):
            final_score.rank = rank
            final_score.save()
    
    return list(final_scores)


def publish_results(event):
    """
    Publish results for all projects in an event
    
    Args:
        event: CodeQuestEvent instance
    
    Returns:
        Number of results published
    """
    from codequest.models import FinalProjectScore
    
    # First, rank all projects
    rank_all_projects(event)
    
    # Then publish all results
    final_scores = FinalProjectScore.objects.filter(
        project__group__event=event
    )
    
    count = 0
    with transaction.atomic():
        for final_score in final_scores:
            if not final_score.is_published:
                final_score.is_published = True
                final_score.published_date = timezone.now()
                final_score.save()
                count += 1
    
    return count


def end_pm_election(group):
    """
    End PM election for a group and declare winner
    
    Args:
        group: CodeQuestGroup instance
    
    Returns:
        ProjectManagerCandidate instance (winner) or None
    """
    from codequest.models import ProjectManagerCandidate
    
    candidates = ProjectManagerCandidate.objects.filter(
        group=group
    ).order_by('-vote_count', 'nomination_date')
    
    if not candidates.exists():
        return None
    
    winner = candidates.first()
    
    with transaction.atomic():
        # Mark winner
        winner.is_winner = True
        winner.save()
        
        # Mark others as not winner
        ProjectManagerCandidate.objects.filter(group=group).exclude(id=winner.id).update(is_winner=False)
        
        # Assign as project manager
        group.project_manager = winner.participant
        group.save()
    
    return winner


def get_group_statistics(group):
    """
    Get statistics for a group
    
    Args:
        group: CodeQuestGroup instance
    
    Returns:
        Dictionary with statistics
    """
    from codequest.models import GroupMemberRole, ProjectTask
    
    members = group.members.all()
    roles = GroupMemberRole.objects.filter(group=group)
    
    # Count roles
    role_distribution = {}
    for role in roles:
        role_type = role.role_type
        if role_type not in role_distribution:
            role_distribution[role_type] = 0
        role_distribution[role_type] += 1
    
    # Task statistics
    tasks = ProjectTask.objects.filter(project__group=group) if hasattr(group, 'project') else []
    task_stats = {
        'total': len(tasks),
        'completed': len([t for t in tasks if t.status == 'Completed']),
        'in_progress': len([t for t in tasks if t.status == 'In Progress']),
        'todo': len([t for t in tasks if t.status == 'Todo']),
    }
    
    return {
        'member_count': members.count(),
        'has_project_manager': group.project_manager is not None,
        'has_consultant': group.consultant is not None,
        'has_project': hasattr(group, 'project'),
        'role_distribution': role_distribution,
        'task_statistics': task_stats,
        'is_complete': group.is_complete,
    }


def validate_score_criteria_weights(event):
    """
    Validate that scoring criteria weights add up to 100%
    
    Args:
        event: CodeQuestEvent instance
    
    Returns:
        Tuple (is_valid: bool, total_weight: Decimal, message: str)
    """
    from codequest.models import ScoringCriteria
    from django.db.models import Sum
    
    total_weight = ScoringCriteria.objects.filter(
        event=event,
        is_active=True
    ).aggregate(total=Sum('percentage_weight'))['total'] or Decimal('0.00')
    
    is_valid = total_weight == Decimal('100.00')
    
    if is_valid:
        message = "✅ Scoring criteria weights are valid (100%)"
    else:
        message = f"⚠️ Warning: Total weight is {total_weight}% (should be 100%)"
    
    return is_valid, total_weight, message


# ============================================================
# EMAIL NOTIFICATION UTILITIES
# ============================================================

def send_group_formation_email(participant, group, send_async=True):
    """
    Send email notification to a participant when their group is formed
    
    Args:
        participant: CodeQuestParticipant instance
        group: CodeQuestGroup instance
        send_async: Whether to send asynchronously (default: True)
    
    Returns:
        Tuple (success: bool, message: str)
    """
    from utils.utils import send_email_notification, send_email_async
    
    if not participant.email:
        return (False, "Participant has no email address")
    
    event = group.event
    members = group.members.all()
    
    # Format dates
    def format_date(dt):
        if not dt:
            return None
        return dt.strftime('%B %d, %Y at %I:%M %p')
    
    # Build portal URL
    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://biochemknust.com')
    portal_url = f"{frontend_url}/code-quest-portal/login"
    
    context = {
        'participant_name': participant.student_name,
        'participant_student_id': participant.student_id,
        'access_key': participant.access_key,
        'group_name': group.group_name or group.group_number,
        'group_number': group.group_number,
        'member_count': members.count(),
        'members': list(members.values('student_name', 'student_id')),
        'academic_year': event.academic_year,
        'voting_start_date': format_date(event.voting_start_date),
        'voting_end_date': format_date(event.voting_end_date),
        'submission_deadline': format_date(event.project_submission_deadline),
        'presentation_date': format_date(event.presentation_date),
        'portal_url': portal_url,
    }
    
    subject = f"🚀 Code Quest {event.academic_year} - Your Group Has Been Formed!"
    template_name = 'codequest/group_formation_notification.html'
    
    try:
        if send_async:
            success, message = send_email_async(
                recipient_email=participant.email,
                subject=subject,
                template_name=template_name,
                context=context
            )
        else:
            success, message = send_email_notification(
                recipient_email=participant.email,
                subject=subject,
                template_name=template_name,
                context=context
            )
        
        if success:
            logger.info(f"Group formation email sent to {participant.email} for group {group.group_number}")
        else:
            logger.warning(f"Failed to send group formation email to {participant.email}: {message}")
        
        return (success, message)
    
    except Exception as e:
        logger.error(f"Error sending group formation email to {participant.email}: {str(e)}")
        return (False, str(e))


def notify_group_members_on_formation(group, send_async=True):
    """
    Send email notifications to all members of a group when it's fully formed
    
    Args:
        group: CodeQuestGroup instance
        send_async: Whether to send asynchronously (default: True)
    
    Returns:
        Dictionary with results: {'success': int, 'failed': int, 'errors': list}
    """
    members = group.members.all()
    results = {
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    for member in members:
        success, message = send_group_formation_email(member, group, send_async)
        if success:
            results['success'] += 1
        else:
            results['failed'] += 1
            results['errors'].append({
                'participant': member.student_name,
                'email': member.email,
                'error': message
            })
    
    logger.info(
        f"Group formation notifications sent for {group.group_number}: "
        f"{results['success']} success, {results['failed']} failed"
    )
    
    return results


def check_and_notify_group_completion(group):
    """
    Check if a group has met its minimum size requirement and notify members
    This is typically called after a participant is assigned to a group
    
    Uses the event's min_group_size and max_group_size settings to determine
    if the group is properly formed.
    
    Args:
        group: CodeQuestGroup instance
    
    Returns:
        Tuple (notified: bool, message: str)
    """
    event = group.event
    min_size = event.min_group_size or 5
    max_size = event.max_group_size  # Can be None (unlimited)
    member_count = group.members.count()
    
    logger.info(
        f"Checking group completion for {group.group_number}: "
        f"{member_count} members, min={min_size}, max={max_size or 'unlimited'}"
    )
    
    # Check if group has already been marked as complete (to avoid duplicate notifications)
    if group.is_complete:
        return (False, "Group was already marked as complete")
    
    # Check if minimum size is met
    if member_count < min_size:
        return (False, f"Group has {member_count} members, needs at least {min_size}")
    
    # Check if max size is exceeded (shouldn't happen but log warning)
    if max_size and member_count > max_size:
        logger.warning(
            f"Group {group.group_number} has {member_count} members, "
            f"exceeds max size of {max_size}"
        )
    
    # Mark group as complete and send notifications
    with transaction.atomic():
        group.is_complete = True
        group.save()
        
        # Send notifications to all members
        results = notify_group_members_on_formation(group)
        
        message = f"Notified {results['success']} members, {results['failed']} failed"
        return (True, message)


def send_pm_election_start_email(participant, group):
    """
    Send email notification when PM election starts
    
    Args:
        participant: CodeQuestParticipant instance
        group: CodeQuestGroup instance
    
    Returns:
        Tuple (success: bool, message: str)
    """
    from utils.utils import send_email_async
    
    if not participant.email:
        return (False, "Participant has no email address")
    
    event = group.event
    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://biochemknust.com')
    portal_url = f"{frontend_url}/code-quest-portal/login"
    
    # Build simple HTML email
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #2563eb, #7c3aed); color: white; padding: 20px; text-align: center;">
            <h1>🗳️ PM Election Has Started!</h1>
        </div>
        <div style="padding: 20px;">
            <p>Hello <strong>{participant.student_name}</strong>,</p>
            
            <p>The Project Manager election for your group (<strong>{group.group_name or group.group_number}</strong>) has officially started!</p>
            
            <h3>What to do:</h3>
            <ul>
                <li><strong>Nominate yourself</strong> if you want to lead the team</li>
                <li><strong>Vote</strong> for the candidate you think will lead best</li>
                <li>Election ends on <strong>{event.voting_end_date.strftime('%B %d, %Y at %I:%M %p') if event.voting_end_date else 'TBA'}</strong></li>
            </ul>
            
            <p style="text-align: center;">
                <a href="{portal_url}" style="background: #2563eb; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block;">
                    Go to Portal
                </a>
            </p>
            
            <p>Best of luck!<br><strong>Code Quest Team</strong></p>
        </div>
    </div>
    """
    
    subject = f"🗳️ PM Election Started - {group.group_name or group.group_number}"
    
    try:
        success, message = send_email_async(
            recipient_email=participant.email,
            subject=subject,
            html_message=html_content
        )
        return (success, message)
    except Exception as e:
        logger.error(f"Error sending PM election email to {participant.email}: {str(e)}")
        return (False, str(e))


def send_pm_election_result_email(participant, group, winner):
    """
    Send email notification with PM election results
    
    Args:
        participant: CodeQuestParticipant instance
        group: CodeQuestGroup instance
        winner: CodeQuestParticipant instance (the elected PM)
    
    Returns:
        Tuple (success: bool, message: str)
    """
    from utils.utils import send_email_async
    
    if not participant.email:
        return (False, "Participant has no email address")
    
    is_winner = participant.id == winner.id
    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://biochemknust.com')
    portal_url = f"{frontend_url}/code-quest-portal/login"
    
    if is_winner:
        subject = f"🎉 Congratulations! You're the Project Manager - {group.group_name or group.group_number}"
        message_intro = f"""
            <p>Hello <strong>{participant.student_name}</strong>,</p>
            <p>🎊 <strong>Congratulations!</strong> Your group members have elected you as their Project Manager!</p>
            <p>As PM, you'll be responsible for:</p>
            <ul>
                <li>Leading team meetings and coordination</li>
                <li>Assigning roles and tasks to team members</li>
                <li>Managing project timeline and deliverables</li>
                <li>Communicating with your consultant</li>
            </ul>
            <p>Your team is counting on you. Make them proud! 💪</p>
        """
    else:
        subject = f"📢 PM Election Results - {group.group_name or group.group_number}"
        message_intro = f"""
            <p>Hello <strong>{participant.student_name}</strong>,</p>
            <p>The PM election for your group has concluded!</p>
            <p>🎉 <strong>{winner.student_name}</strong> has been elected as your Project Manager.</p>
            <p>Work together with your new PM to build an amazing project!</p>
        """
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #2563eb, #7c3aed); color: white; padding: 20px; text-align: center;">
            <h1>{'🎉' if is_winner else '📢'} PM Election Results</h1>
            <p>{group.group_name or group.group_number}</p>
        </div>
        <div style="padding: 20px;">
            {message_intro}
            
            <p style="text-align: center;">
                <a href="{portal_url}" style="background: #2563eb; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block;">
                    Go to Portal
                </a>
            </p>
            
            <p>Best of luck with your project!<br><strong>Code Quest Team</strong></p>
        </div>
    </div>
    """
    
    try:
        success, message = send_email_async(
            recipient_email=participant.email,
            subject=subject,
            html_message=html_content
        )
        return (success, message)
    except Exception as e:
        logger.error(f"Error sending PM election result email to {participant.email}: {str(e)}")
        return (False, str(e))
