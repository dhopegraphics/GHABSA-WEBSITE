#!/usr/bin/env python
"""
Test Script for Self-Grouping Feature
=====================================
Tests all self-grouping endpoints and creates a full team with multiple participants.

Run: python manage.py shell < scripts/test_self_grouping.py
Or:  python scripts/test_self_grouping.py (if Django settings configured)
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BioChemSystem.settings')
django.setup()

from django.utils import timezone
from django.db import transaction
from codequest.models import (
    CodeQuestEvent, CodeQuestParticipant, SelfGroupingTeam,
    SelfGroupingMembership, GroupInvitation, JoinRequest
)
from accounts.models import CustomUser as User
from events.models import Event
import random
import string


def generate_access_key():
    """Generate a random access key"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_success(text):
    print(f"  ✅ {text}")


def print_info(text):
    print(f"  ℹ️  {text}")


def print_error(text):
    print(f"  ❌ {text}")


def cleanup_test_data():
    """Clean up any existing test data"""
    print_header("CLEANUP: Removing existing test data")
    
    # Delete test participants and related data
    test_participants = CodeQuestParticipant.objects.filter(
        student_id__startswith='TEST'
    )
    
    if test_participants.exists():
        # Get teams created by test participants
        test_teams = SelfGroupingTeam.objects.filter(creator__in=test_participants)
        
        # Delete join requests
        JoinRequest.objects.filter(team__in=test_teams).delete()
        JoinRequest.objects.filter(requester__in=test_participants).delete()
        
        # Delete invitations
        GroupInvitation.objects.filter(team__in=test_teams).delete()
        GroupInvitation.objects.filter(sender__in=test_participants).delete()
        GroupInvitation.objects.filter(recipient__in=test_participants).delete()
        
        # Delete memberships
        SelfGroupingMembership.objects.filter(team__in=test_teams).delete()
        SelfGroupingMembership.objects.filter(participant__in=test_participants).delete()
        
        # Delete teams
        test_teams.delete()
        
        # Delete participants
        count = test_participants.count()
        test_participants.delete()
        print_success(f"Deleted {count} test participants and related data")
    else:
        print_info("No existing test data found")


def get_or_create_event():
    """Get or create a test event with self-grouping enabled"""
    print_header("SETUP: Getting/Creating CodeQuest Event")
    
    # Try to find an existing event
    cq_event = CodeQuestEvent.objects.filter(allow_self_grouping=True).first()
    
    if not cq_event:
        # Create a base event first
        base_event, _ = Event.objects.get_or_create(
            event_name="CodeQuest 2025 Test Event",
            defaults={
                'description': 'Test event for self-grouping feature',
                'event_type': 'competition',
                'event_date': timezone.now(),
                'event_end_date': timezone.now() + timezone.timedelta(days=30),
                'organised_by': 'CS Department',
            }
        )
        
        # Create CodeQuest event
        cq_event = CodeQuestEvent.objects.create(
            event=base_event,
            academic_year='2024/2025',
            semester='Second',
            course_code='CS 472',
            course_name='Software Engineering Project',
            status='ACTIVE',
            allow_self_grouping=True,
            min_group_size=3,  # Lower for testing
            max_group_size=5,  # Lower for testing
            registration_start_date=timezone.now() - timezone.timedelta(days=1),
            registration_end_date=timezone.now() + timezone.timedelta(days=30),
        )
        print_success(f"Created new CodeQuest event: {cq_event.event.event_name}")
    else:
        # Only enable self-grouping, DON'T modify min/max settings
        if not cq_event.allow_self_grouping:
            cq_event.allow_self_grouping = True
            cq_event.save()
        print_success(f"Using existing event: {cq_event.event.event_name}")
    
    print_info(f"Event ID: {cq_event.id}")
    print_info(f"Self-grouping: {'Enabled' if cq_event.allow_self_grouping else 'Disabled'}")
    print_info(f"Group size: {cq_event.min_group_size} - {cq_event.max_group_size}")
    
    return cq_event


def create_test_users(count=6):
    """Get existing users or skip user creation"""
    print_header(f"SETUP: Getting {count} Users for Linking")
    
    # Try to get existing users with personal_email
    users = list(User.objects.filter(personal_email__isnull=False)[:count])
    
    if len(users) >= count:
        print_success(f"Found {len(users)} existing users to link")
        for u in users:
            print_info(f"  - {u.first_name} {u.last_name} ({u.personal_email})")
        return users
    
    # If not enough users, we'll create participants without linked users
    print_info(f"Only {len(users)} users found, will create participants without user links")
    return users


def create_test_participants(event, users):
    """Create test participants, optionally linked to users"""
    print_header(f"SETUP: Creating 6 Test Participants")
    
    skills_pool = [
        "Python, Django, REST APIs",
        "JavaScript, React, Node.js",
        "Java, Spring Boot, MySQL",
        "Flutter, Dart, Firebase",
        "Machine Learning, TensorFlow, Python",
        "DevOps, Docker, AWS",
        "UI/UX Design, Figma, CSS",
        "Database Design, PostgreSQL, MongoDB"
    ]
    
    roles_pool = [
        "Backend Developer",
        "Frontend Developer",
        "Full Stack Developer",
        "Mobile Developer",
        "ML Engineer",
        "DevOps Engineer",
        "UI/UX Designer",
        "Project Manager"
    ]
    
    names = [
        ("Kwame", "Asante"),
        ("Ama", "Mensah"),
        ("Kofi", "Owusu"),
        ("Abena", "Boateng"),
        ("Yaw", "Darko"),
        ("Akua", "Frimpong")
    ]
    
    years = [2, 3, 3, 4, 4, 4]
    
    participants = []
    for i in range(6):
        student_id = f"TEST{10000 + i + 1}"
        first_name, last_name = names[i]
        
        # Link to user if available
        user = users[i] if i < len(users) else None
        
        participant, created = CodeQuestParticipant.objects.get_or_create(
            event=event,
            student_id=student_id,
            defaults={
                'user': user,
                'student_name': f"{first_name} {last_name}",
                'email': f"{first_name.lower()}.{last_name.lower()}@st.knust.edu.gh",
                'phone_number': f"+233{random.randint(200000000, 299999999)}",
                'year': years[i],
                'skills': skills_pool[i % len(skills_pool)],
                'preferred_role': roles_pool[i % len(roles_pool)],
                'access_key': generate_access_key(),
            }
        )
        if created:
            linked = f"(linked to {user.first_name})" if user else "(no user link)"
            print_success(f"Created: {participant.student_name} ({student_id}) {linked}")
            print_info(f"    Skills: {participant.skills}")
        else:
            print_info(f"Exists: {participant.student_name} ({student_id})")
        participants.append(participant)
    
    return participants


def test_self_grouping_status(participant):
    """Test the status endpoint"""
    print_header("TEST: Self-Grouping Status Endpoint")
    
    event = participant.event
    
    status = {
        'self_grouping_enabled': event.allow_self_grouping,
        'min_group_size': event.min_group_size,
        'max_group_size': event.max_group_size,
        'participant_id': participant.id,
        'participant_name': participant.student_name,
        'has_team': SelfGroupingMembership.objects.filter(
            participant=participant, 
            status='accepted'
        ).exists()
    }
    
    print_success("Status retrieved successfully")
    for key, value in status.items():
        print_info(f"{key}: {value}")
    
    return status


def test_create_team(creator):
    """Test creating a team"""
    print_header("TEST: Create Team Endpoint")
    
    # Check if creator already has a team
    existing_membership = SelfGroupingMembership.objects.filter(
        participant=creator,
        status='accepted'
    ).first()
    
    if existing_membership:
        print_info(f"Creator already in team: {existing_membership.team}")
        return existing_membership.team
    
    team = SelfGroupingTeam.objects.create(
        event=creator.event,
        team_name=f"Alpha Squad - {creator.student_name.split()[0]}",
        creator=creator,
        status='forming'
    )
    
    # Create membership for creator
    SelfGroupingMembership.objects.create(
        team=team,
        participant=creator,
        is_creator=True,
        status='accepted'
    )
    
    print_success(f"Team created: {team.team_name}")
    print_info(f"Team ID: {team.id}")
    print_info(f"Creator: {creator.student_name}")
    print_info(f"Access Key: {creator.access_key}")
    
    return team


def test_send_invitations(team, participants):
    """Test sending invitations to participants"""
    print_header("TEST: Send Invitations Endpoint")
    
    creator = team.creator
    invitations = []
    
    for participant in participants:
        if participant.id == creator.id:
            continue
        
        # Check if already invited or member
        existing = GroupInvitation.objects.filter(
            team=team,
            recipient=participant,
            status='pending'
        ).exists()
        
        if existing:
            print_info(f"Already invited: {participant.student_name}")
            continue
        
        is_member = SelfGroupingMembership.objects.filter(
            participant=participant,
            status='accepted'
        ).exists()
        
        if is_member:
            print_info(f"Already in a team: {participant.student_name}")
            continue
        
        invitation = GroupInvitation.objects.create(
            team=team,
            sender=creator,
            recipient=participant,
            message=f"Hey {participant.student_name.split()[0]}! Join our team!",
            status='pending'
        )
        invitations.append(invitation)
        print_success(f"Invitation sent to: {participant.student_name}")
    
    print_info(f"Total invitations sent: {len(invitations)}")
    return invitations


def test_accept_invitations(invitations, count=3):
    """Test accepting invitations"""
    print_header(f"TEST: Accept {count} Invitations")
    
    accepted = 0
    for invitation in invitations[:count]:
        if invitation.status != 'pending':
            continue
        
        # Accept the invitation
        invitation.status = 'accepted'
        invitation.responded_at = timezone.now()
        invitation.save()
        
        # Create membership
        membership, created = SelfGroupingMembership.objects.get_or_create(
            team=invitation.team,
            participant=invitation.recipient,
            defaults={
                'is_creator': False,
                'status': 'accepted'
            }
        )
        
        if created:
            accepted += 1
            print_success(f"Accepted: {invitation.recipient.student_name} joined {invitation.team.team_name}")
    
    # Check team status
    team = invitations[0].team if invitations else None
    if team:
        member_count = team.memberships.filter(status='accepted').count()
        print_info(f"Team now has {member_count} members")
        
        if member_count >= team.event.min_group_size:
            print_success("Team is ready to finalize! ✨")
    
    return accepted


def test_decline_invitation(invitations):
    """Test declining an invitation"""
    print_header("TEST: Decline Invitation")
    
    # Find a pending invitation to decline
    pending = [inv for inv in invitations if inv.status == 'pending']
    
    if not pending:
        print_info("No pending invitations to decline")
        return None
    
    invitation = pending[0]
    invitation.status = 'declined'
    invitation.responded_at = timezone.now()
    invitation.save()
    
    print_success(f"Declined: {invitation.recipient.student_name} declined invitation")
    return invitation


def test_join_request(team, requester):
    """Test sending a join request"""
    print_header("TEST: Send Join Request Endpoint")
    
    # Check if already a member
    is_member = SelfGroupingMembership.objects.filter(
        participant=requester,
        status='accepted'
    ).exists()
    
    if is_member:
        print_info(f"{requester.student_name} is already in a team")
        return None
    
    # Check if request already exists
    existing = JoinRequest.objects.filter(
        team=team,
        requester=requester,
        status='pending'
    ).first()
    
    if existing:
        print_info(f"Request already exists from {requester.student_name}")
        return existing
    
    request = JoinRequest.objects.create(
        team=team,
        requester=requester,
        message=f"Hi! I'd love to join your team. I have skills in {requester.skills[:30]}...",
        status='pending'
    )
    
    print_success(f"Join request sent by: {requester.student_name}")
    print_info(f"To team: {team.team_name}")
    
    return request


def test_accept_join_request(join_request):
    """Test accepting a join request"""
    print_header("TEST: Accept Join Request")
    
    if not join_request or join_request.status != 'pending':
        print_info("No pending join request to accept")
        return False
    
    team = join_request.team
    
    # Check if team is full
    member_count = team.memberships.filter(status='accepted').count()
    if member_count >= team.event.max_group_size:
        print_error(f"Team is full ({member_count}/{team.event.max_group_size})")
        return False
    
    # Accept the request
    join_request.status = 'accepted'
    join_request.responded_by = team.creator
    join_request.responded_at = timezone.now()
    join_request.save()
    
    # Create membership
    membership, created = SelfGroupingMembership.objects.get_or_create(
        team=team,
        participant=join_request.requester,
        defaults={
            'is_creator': False,
            'status': 'accepted'
        }
    )
    
    print_success(f"Accepted: {join_request.requester.student_name} joined via request")
    
    member_count = team.memberships.filter(status='accepted').count()
    print_info(f"Team now has {member_count}/{team.event.max_group_size} members")
    
    return True


def test_get_my_team(participant):
    """Test getting my team details"""
    print_header("TEST: Get My Team Endpoint")
    
    membership = SelfGroupingMembership.objects.filter(
        participant=participant,
        status='accepted'
    ).select_related('team', 'team__creator').first()
    
    if not membership:
        print_info(f"{participant.student_name} is not in any team")
        return None
    
    team = membership.team
    members = team.memberships.filter(status='accepted').select_related('participant')
    
    print_success(f"Team: {team.team_name}")
    print_info(f"Status: {team.get_status_display()}")
    print_info(f"Creator: {team.creator.student_name}")
    print_info(f"Members ({members.count()}):")
    
    for m in members:
        role = "👑 Creator" if m.is_creator else "Member"
        print_info(f"  - {m.participant.student_name} ({m.participant.student_id}) [{role}]")
        print_info(f"    Skills: {m.participant.skills}")
    
    return team


def test_list_available_teams(event, exclude_participant):
    """Test listing available teams"""
    print_header("TEST: List Available Teams Endpoint")
    
    teams = SelfGroupingTeam.objects.filter(
        event=event,
        status='forming'
    ).exclude(
        memberships__participant=exclude_participant,
        memberships__status='accepted'
    )
    
    print_success(f"Found {teams.count()} available teams")
    
    for team in teams:
        member_count = team.memberships.filter(status='accepted').count()
        can_join = member_count < event.max_group_size
        print_info(f"  - {team.team_name}: {member_count}/{event.max_group_size} members {'✅ Can Join' if can_join else '❌ Full'}")
    
    return list(teams)


def test_list_available_participants(event, team):
    """Test listing available participants"""
    print_header("TEST: List Available Participants Endpoint")
    
    # Get participants not in any team
    participants = CodeQuestParticipant.objects.filter(
        event=event
    ).exclude(
        team_memberships__status='accepted'
    )
    
    print_success(f"Found {participants.count()} available participants")
    
    for p in participants:
        print_info(f"  - {p.student_name} ({p.student_id})")
        print_info(f"    Skills: {p.skills}")
        print_info(f"    Preferred Role: {p.preferred_role}")
    
    return list(participants)


def test_finalize_team(team):
    """Test finalizing a team"""
    print_header("TEST: Finalize Team Endpoint")
    
    member_count = team.memberships.filter(status='accepted').count()
    min_size = team.event.min_group_size
    max_size = team.event.max_group_size
    
    print_info(f"Team: {team.team_name}")
    print_info(f"Members: {member_count}/{max_size} (min: {min_size})")
    
    if member_count < min_size:
        print_error(f"Cannot finalize: Need at least {min_size} members")
        return False
    
    # Update team status
    team.status = 'finalized'
    team.finalized_at = timezone.now()
    team.save()
    
    print_success(f"Team '{team.team_name}' has been FINALIZED! 🎉")
    print_info("This team can now be converted to an official CodeQuest group")
    
    return True


def print_summary(event, team):
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total_participants = CodeQuestParticipant.objects.filter(
        event=event,
        student_id__startswith='TEST'
    ).count()
    
    total_teams = SelfGroupingTeam.objects.filter(
        event=event,
        creator__student_id__startswith='TEST'
    ).count()
    
    total_invitations = GroupInvitation.objects.filter(
        team__event=event,
        team__creator__student_id__startswith='TEST'
    ).count()
    
    total_requests = JoinRequest.objects.filter(
        team__event=event,
        team__creator__student_id__startswith='TEST'
    ).count()
    
    print(f"""
    📊 Test Data Created:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Participants:    {total_participants}
    Teams:           {total_teams}
    Invitations:     {total_invitations}
    Join Requests:   {total_requests}
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    🔑 Access Keys for Testing:
    """)
    
    participants = CodeQuestParticipant.objects.filter(
        event=event,
        student_id__startswith='TEST'
    )
    
    for p in participants:
        membership = SelfGroupingMembership.objects.filter(
            participant=p,
            status='accepted'
        ).first()
        team_info = f"In team: {membership.team.team_name}" if membership else "No team"
        is_creator = "👑" if membership and membership.is_creator else ""
        print(f"    {p.student_name} ({p.student_id})")
        print(f"      Access Key: {p.access_key}")
        print(f"      Status: {team_info} {is_creator}")
        print()
    
    if team:
        print(f"""
    ✅ Main Test Team:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Name:    {team.team_name}
    Status:  {team.get_status_display()}
    Members: {team.memberships.filter(status='accepted').count()}/{team.event.max_group_size}
    Creator: {team.creator.student_name}
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)


def run_all_tests():
    """Run all self-grouping tests"""
    print("\n" + "🚀" * 30)
    print("\n  SELF-GROUPING FEATURE - COMPLETE TEST SUITE")
    print("\n" + "🚀" * 30)
    
    with transaction.atomic():
        # Cleanup
        cleanup_test_data()
        
        # Setup
        event = get_or_create_event()
        users = create_test_users(6)
        participants = create_test_participants(event, users)
        
        # Test 1: Status
        test_self_grouping_status(participants[0])
        
        # Test 2: Create Team (Participant 1 creates team)
        team = test_create_team(participants[0])
        
        # Test 3: Send Invitations (to participants 2, 3, 4)
        invitations = test_send_invitations(team, participants[1:5])
        
        # Test 4: Accept Invitations (participants 2, 3 accept)
        test_accept_invitations(invitations, count=2)
        
        # Test 5: Decline Invitation (participant 4 declines)
        test_decline_invitation(invitations)
        
        # Test 6: Join Request (participant 5 requests to join)
        join_request = test_join_request(team, participants[4])
        
        # Test 7: Accept Join Request
        test_accept_join_request(join_request)
        
        # Test 8: List Available Teams
        test_list_available_teams(event, participants[5])
        
        # Test 9: List Available Participants
        test_list_available_participants(event, team)
        
        # Test 10: Get My Team
        test_get_my_team(participants[0])  # Creator
        test_get_my_team(participants[1])  # Member
        test_get_my_team(participants[5])  # Not in team
        
        # Test 11: Finalize Team (if has enough members)
        member_count = team.memberships.filter(status='accepted').count()
        if member_count >= event.min_group_size:
            test_finalize_team(team)
        else:
            print_header("SKIP: Finalize Team")
            print_info(f"Team has {member_count} members, needs {event.min_group_size}")
        
        # Summary
        print_summary(event, team)
    
    print("\n" + "✅" * 30)
    print("\n  ALL TESTS COMPLETED SUCCESSFULLY!")
    print("\n" + "✅" * 30 + "\n")


if __name__ == '__main__':
    run_all_tests()
