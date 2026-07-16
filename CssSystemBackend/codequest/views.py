"""
Django REST Framework views for Code Quest API
Provides all endpoints for authentication, registration, voting, scoring, etc.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.utils import timezone
from django.db import transaction, models
from django.db.models import Count, Avg, Q
import logging

from codequest.models import *
from codequest.serializers import *
from codequest.repositories import *
from codequest import utils as codequest_utils
from utils.utils import notify_user_email

logger = logging.getLogger(__name__)


# ===============================
# Public Event Info View
# ===============================

class ActiveCodeQuestEventView(APIView):
    """
    Get the active/current CodeQuest event
    This is the first endpoint the frontend should call to check if CodeQuest is available
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        now = timezone.now()
        
        # Find active CodeQuest event (not completed, linked to competition event)
        # Priority: registration_open > other active statuses > draft (upcoming)
        active_event = CodeQuestEvent.objects.filter(
            event__event_type='competition',
            presentation_date__gte=now  # Event hasn't passed
        ).exclude(
            status='completed'
        ).select_related('event').order_by(
            # Prioritize events with open registration
            '-status',
            'presentation_date'
        ).first()
        
        # If no upcoming event, try to find the most recent completed one
        if not active_event:
            active_event = CodeQuestEvent.objects.filter(
                event__event_type='competition',
                status='completed'
            ).select_related('event').order_by('-presentation_date').first()
            
            if active_event:
                serializer = ActiveCodeQuestEventSerializer(active_event)
                return Response({
                    'available': False,
                    'reason': 'completed',
                    'message': 'Code Quest has ended. Stay tuned for the next edition!',
                    'last_event': serializer.data
                })
        
        if not active_event:
            return Response({
                'available': False,
                'reason': 'no_event',
                'message': 'No Code Quest event is currently scheduled. Check back later!'
            })
        
        serializer = ActiveCodeQuestEventSerializer(active_event)
        
        # Determine availability based on status
        is_available = active_event.status != 'draft'
        
        return Response({
            'available': is_available,
            'reason': 'active' if is_available else 'coming_soon',
            'message': 'Code Quest is live!' if is_available else 'Code Quest is coming soon!',
            'event': serializer.data
        })


class CurrentUserDetailsView(APIView):
    """
    Get current authenticated user's details for pre-filling registration forms.
    Also checks if the user has already registered for the current CodeQuest event.
    Returns detailed registration status including group assignment, PM status, etc.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        event_id = request.query_params.get('event_id')
        
        # Check for existing registrations
        existing_participant = None
        existing_consultant = None
        participant_details = None
        consultant_details = None
        
        if event_id:
            existing_participant = CodeQuestParticipant.objects.filter(
                user=user, event_id=event_id
            ).select_related('group', 'group__project_manager').first()
            
            existing_consultant = CodeQuestConsultant.objects.filter(
                user=user, event_id=event_id
            ).first()
            
            # Build detailed participant info
            if existing_participant:
                participant_details = {
                    'id': existing_participant.id,
                    'access_key': existing_participant.access_key,
                    'student_name': existing_participant.student_name,
                    'student_id': existing_participant.student_id,
                    'year': existing_participant.year,
                    'preferred_role': existing_participant.preferred_role,
                    'registration_date': existing_participant.registration_date.isoformat(),
                    'group': None,
                    'is_project_manager': False,
                }
                
                if existing_participant.group:
                    participant_details['group'] = {
                        'id': existing_participant.group.id,
                        'group_number': existing_participant.group.group_number,
                        'group_name': existing_participant.group.group_name,
                        'member_count': existing_participant.group.members.count(),
                        'has_project_manager': existing_participant.group.project_manager is not None,
                    }
                    participant_details['is_project_manager'] = (
                        existing_participant.group.project_manager == existing_participant
                    )
            
            # Build detailed consultant info
            if existing_consultant:
                consultant_details = {
                    'id': existing_consultant.id,
                    'access_key': existing_consultant.access_key,
                    'student_name': existing_consultant.student_name,
                    'student_id': existing_consultant.student_id,
                    'year': existing_consultant.year,
                    'is_approved': existing_consultant.is_approved,
                    'expertise_areas': existing_consultant.expertise_areas,
                    'registration_date': existing_consultant.registration_date.isoformat(),
                    'assigned_groups_count': existing_consultant.group_assignments.filter(is_active=True).count(),
                }
        
        # Calculate user year from graduation_year
        from datetime import datetime
        current_year = datetime.now().year
        current_month = datetime.now().month
        # After October, students are in next academic year
        academic_year = current_year if current_month < 11 else current_year + 1
        user_year = user.graduation_year - academic_year + 4  # Year 1-4
        user_year = max(1, min(4, user_year))  # Clamp between 1-4
        
        return Response({
            'user': {
                'id': str(user.id),
                'student_id': user.student_id or user.index_number or '',
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.personal_email or '',  # Use personal email for CodeQuest communications
                'student_email': user.student_email or '',
                'phone': str(user.phone) if user.phone else '',
                'year': user_year,
                'program': user.program,
            },
            'registration_status': {
                'is_registered': existing_participant is not None or existing_consultant is not None,
                'registered_as': 'participant' if existing_participant else ('consultant' if existing_consultant else None),
                'can_register_as_participant': existing_participant is None and existing_consultant is None,
                'can_register_as_consultant': existing_participant is None and existing_consultant is None,
            },
            'participant': participant_details,
            'consultant': consultant_details,
        })


# Authentication Views
class PortalLoginView(APIView):
    """
    Combined portal login for participants and consultants.
    Checks access_key against both tables and returns user_type.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        access_key = request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'message': 'Access key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # First, check if it's a participant
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        if participant:
            serializer = CodeQuestParticipantSerializer(participant)
            return Response({
                'message': 'Login successful',
                'user_type': 'participant',
                'user_data': serializer.data
            })
        
        # Then, check if it's a consultant
        consultant = CodeQuestConsultantRepository.get_by_access_key(access_key)
        if consultant:
            if not consultant.is_approved:
                return Response(
                    {'message': 'Your consultant account is pending approval. Please wait for admin approval.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = CodeQuestConsultantSerializer(consultant)
            return Response({
                'message': 'Login successful',
                'user_type': 'consultant',
                'user_data': serializer.data
            })
        
        # No match found
        return Response(
            {'message': 'Invalid access key. Please check and try again.'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class StudentLoginView(APIView):
    """Login for students using access_key"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        access_key = request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = CodeQuestParticipantSerializer(participant)
        return Response({
            'message': 'Login successful',
            'participant': serializer.data
        })


class ConsultantLoginView(APIView):
    """Login for consultants using access_key"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        access_key = request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultant = CodeQuestConsultantRepository.get_by_access_key(access_key)
        
        if not consultant or not consultant.is_approved:
            return Response(
                {'error': 'Invalid access key or account not approved'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = CodeQuestConsultantSerializer(consultant)
        return Response({
            'message': 'Login successful',
            'consultant': serializer.data
        })


class FacilitatorLoginView(APIView):
    """Login for facilitators using access_code"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        access_code = request.data.get('access_code')
        
        if not access_code:
            return Response(
                {'error': 'access_code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        facilitator = CodeQuestFacilitatorRepository.get_by_access_code(access_code)
        
        if not facilitator:
            return Response(
                {'error': 'Invalid access code'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = CodeQuestFacilitatorSerializer(facilitator)
        return Response({
            'message': 'Login successful',
            'facilitator': serializer.data
        })


# Student Registration & Management
class StudentRegistrationView(APIView):
    """Register new student participant - requires authentication to link user account"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Pass request context for validation (checking existing registrations)
        serializer = CodeQuestParticipantSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Link the authenticated user to the participant registration
            participant = serializer.save(user=request.user)
            
            # Send confirmation email with access key
            self._send_registration_email(participant)
            
            # Return with access_key
            response_serializer = CodeQuestParticipantSerializer(participant)
            return Response({
                'message': 'Registration successful',
                'participant': response_serializer.data,
                'access_key': participant.access_key
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _send_registration_email(self, participant):
        """Send registration confirmation email to participant"""
        try:
            event = participant.event
            subject = f"Code Quest {event.academic_year} - Registration Confirmed"
            
            message = f"""Dear {participant.student_name},

Welcome to Code Quest {event.academic_year}! 🎉

Your registration has been successfully completed. Here are your details:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 REGISTRATION DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Student ID: {participant.student_id}
Name: {participant.student_name}
Year: Year {participant.year}
Preferred Role: {participant.preferred_role or 'Not specified'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔑 YOUR ACCESS KEY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{participant.access_key}

⚠️ IMPORTANT: Save this access key! You'll need it to:
• Login to the participant portal
• View your group assignment
• Vote for Project Manager
• Track your progress

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 WHAT'S NEXT?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Wait for group formation - you'll be notified via email
2. Once assigned, you can view your group members
3. Vote for your group's Project Manager during the election period
4. Start building your amazing app!

Key Dates:
• Registration Closes: {event.registration_end_date.strftime('%B %d, %Y')}
• Group Formation: {event.grouping_date.strftime('%B %d, %Y')}
• PM Election: {event.voting_start_date.strftime('%B %d, %Y')} - {event.voting_end_date.strftime('%B %d, %Y')}
• Presentation Day: {event.presentation_date.strftime('%B %d, %Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If you have any questions, contact us at {settings.EMAIL_ADMIN}

Good luck! 🚀

Best regards,
{settings.BRAND_SITE_LABEL} Code Quest Team
"""
            
            success, error_msg = notify_user_email(
                email=participant.email,
                message=message,
                subject=subject
            )
            
            if success:
                logger.info(f"Registration email sent to {participant.email}")
            else:
                logger.error(f"Failed to send registration email to {participant.email}: {error_msg}")
                
        except Exception as e:
            logger.error(f"Exception sending registration email: {str(e)}", exc_info=True)


class MyGroupView(APIView):
    """Get participant's group details"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_key = request.query_params.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not participant.group:
            return Response({
                'message': 'Not assigned to any group yet',
                'group': None
            })
        
        serializer = GroupDetailSerializer(participant.group)
        return Response(serializer.data)


class ParticipantDashboardView(APIView):
    """
    Comprehensive dashboard endpoint for participant portal.
    Returns all data needed for the participant dashboard including:
    - Participant info
    - Group info (if assigned)
    - Project info (if exists)
    - Consultant info (if assigned)
    - Event timeline and phases
    - Tasks (if any)
    - PM election status
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_key = request.query_params.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        event = participant.event
        now = timezone.now()
        
        # Serialize participant data
        participant_data = CodeQuestParticipantSerializer(participant).data
        
        # Get group data
        group_data = None
        project_data = None
        consultant_data = None
        tasks_data = []
        pm_candidates = []
        has_voted = False
        is_pm_candidate = False
        is_project_manager = False
        
        if participant.group:
            group_data = GroupDetailSerializer(participant.group).data
            
            # Check if participant is project manager
            is_project_manager = participant.group.project_manager == participant
            
            # Get project if exists
            project = CodeQuestProjectRepository.get_by_group(participant.group.id)
            if project:
                project_data = CodeQuestProjectSerializer(project).data
                
                # Get tasks assigned to this participant
                tasks = ProjectTaskRepository.get_tasks_by_participant(participant.id)
                tasks_data = ProjectTaskSerializer(tasks, many=True).data
            
            # Get consultant if assigned
            consultant_assignments = ConsultantGroupAssignmentRepository.get_assignments_by_group(participant.group.id)
            if consultant_assignments.exists():
                consultant = consultant_assignments.first().consultant
                consultant_data = CodeQuestConsultantPublicSerializer(consultant).data
            
            # Get PM election data
            candidates = ProjectManagerCandidateRepository.get_candidates_by_group(participant.group.id)
            pm_candidates = ProjectManagerCandidateSerializer(candidates, many=True).data
            
            # Check if this participant is a candidate
            is_pm_candidate = candidates.filter(participant=participant).exists()
            
            # Check if participant has voted
            has_voted = ProjectManagerVoteRepository.has_voted(participant.id, participant.group.id)
        
        # Determine current phase
        phase = self._determine_phase(event, participant, now)
        
        # Get pending tasks count
        pending_tasks = len([t for t in tasks_data if t.get('status') in ['Todo', 'In Progress']])
        
        # Build event timeline
        timeline = {
            'registration_start': event.registration_start_date.isoformat(),
            'registration_end': event.registration_end_date.isoformat(),
            'grouping_date': event.grouping_date.isoformat(),
            'voting_start': event.voting_start_date.isoformat(),
            'voting_end': event.voting_end_date.isoformat(),
            'submission_deadline': event.project_submission_deadline.isoformat(),
            'presentation_date': event.presentation_date.isoformat(),
        }
        
        return Response({
            'participant': {
                **participant_data,
                'pending_tasks': pending_tasks,
                'is_project_manager': is_project_manager,
            },
            'group': group_data,
            'project': project_data,
            'consultant': consultant_data,
            'tasks': tasks_data,
            'event': {
                'id': event.id,
                'academic_year': event.academic_year,
                'semester': event.semester,
                'course_code': event.course_code,
                'course_name': event.course_name,
                'status': event.status,
                'timeline': timeline,
                'allow_self_grouping': event.allow_self_grouping,
                'min_group_size': event.min_group_size,
                'max_group_size': event.max_group_size,
            },
            'phase': phase,
            'pm_election': {
                'nomination_open': event.voting_start_date <= now <= event.voting_end_date and not participant.group.project_manager if participant.group else False,
                'voting_open': event.voting_start_date <= now <= event.voting_end_date,
                'candidates': pm_candidates,
                'has_voted': has_voted,
                'is_candidate': is_pm_candidate,
                'winner': participant.group.project_manager.student_name if participant.group and participant.group.project_manager else None,
            } if participant.group else None,
        })
    
    def _determine_phase(self, event, participant, now):
        """Determine current dashboard phase"""
        if not participant.group:
            return {
                'name': 'waiting',
                'label': 'Waiting for Group Formation',
                'description': 'Your group is being formed. Check back soon!'
            }
        
        # Check if PM election is in progress
        if event.voting_start_date <= now <= event.voting_end_date:
            if not participant.group.project_manager:
                return {
                    'name': 'voting',
                    'label': 'PM Election in Progress',
                    'description': 'Vote for your group\'s Project Manager'
                }
        
        # Check if PM has been elected
        if participant.group.project_manager:
            # Check if project submission is open
            if now <= event.project_submission_deadline:
                return {
                    'name': 'development',
                    'label': 'Development Phase',
                    'description': 'Build your amazing app!'
                }
            
            # After submission deadline
            if now <= event.presentation_date:
                return {
                    'name': 'presentation',
                    'label': 'Presentation Preparation',
                    'description': 'Prepare for your presentation'
                }
            
            return {
                'name': 'completed',
                'label': 'Event Completed',
                'description': 'Code Quest has ended. Check your results!'
            }
        
        return {
            'name': 'active',
            'label': 'Group Formed',
            'description': 'Your group has been formed'
        }


class MyProjectView(APIView):
    """Get participant's project details"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_key = request.query_params.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant or not participant.group:
            return Response({
                'message': 'No group/project found',
                'project': None
            })
        
        project = CodeQuestProjectRepository.get_by_group(participant.group.id)
        
        if not project:
            return Response({
                'message': 'Project not yet created',
                'project': None
            })
        
        serializer = ProjectDetailSerializer(project)
        return Response(serializer.data)


# Consultant Views
class ConsultantRegistrationView(APIView):
    """Register new consultant - requires authentication to link user account"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Pass request context for validation (checking existing registrations)
        serializer = CodeQuestConsultantSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Link the authenticated user to the consultant registration
            consultant = serializer.save(user=request.user)
            
            # Send confirmation email with access key
            self._send_registration_email(consultant)
            
            response_serializer = CodeQuestConsultantSerializer(consultant)
            return Response({
                'message': 'Registration successful. Awaiting admin approval.',
                'consultant': response_serializer.data,
                'access_key': consultant.access_key
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _send_registration_email(self, consultant):
        """Send registration confirmation email to consultant"""
        try:
            event = consultant.event
            subject = f"Code Quest {event.academic_year} - Consultant Application Received"
            
            message = f"""Dear {consultant.student_name},

Thank you for applying to be a Consultant for Code Quest {event.academic_year}! 🎓

Your application has been received and is pending admin approval.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 APPLICATION DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Student ID: {consultant.student_id}
Name: {consultant.student_name}
Year: {consultant.get_year_display()}
Expertise Areas: {', '.join(consultant.expertise_areas) if consultant.expertise_areas else 'Not specified'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔑 YOUR ACCESS KEY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{consultant.access_key}

⚠️ IMPORTANT: Save this access key! Once approved, you'll need it to:
• Login to the consultant portal
• View your assigned groups
• Monitor group progress
• Provide guidance to teams

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏳ WHAT'S NEXT?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ⏳ Wait for admin approval (you'll be notified via email)
2. 👥 Once approved, groups will be assigned to you
3. 🎯 Guide your assigned groups through their project

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If you have any questions, contact us at {settings.EMAIL_ADMIN}

Thank you for offering to mentor! 🙏

Best regards,
{settings.BRAND_SITE_LABEL} Code Quest Team
"""
            
            success, error_msg = notify_user_email(
                email=consultant.email,
                message=message,
                subject=subject
            )
            
            if success:
                logger.info(f"Consultant registration email sent to {consultant.email}")
            else:
                logger.error(f"Failed to send consultant registration email to {consultant.email}: {error_msg}")
                
        except Exception as e:
            logger.error(f"Exception sending consultant registration email: {str(e)}", exc_info=True)


class ConsultantMyGroupsView(APIView):
    """Get consultant's assigned groups"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_key = request.query_params.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultant = CodeQuestConsultantRepository.get_by_access_key(access_key)
        
        if not consultant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        assignments = ConsultantGroupAssignmentRepository.get_assignments_by_consultant(consultant.id)
        groups = [assignment.group for assignment in assignments]
        
        serializer = GroupDetailSerializer(groups, many=True)
        return Response({
            'total_groups': len(groups),
            'groups': serializer.data
        })


class ConsultantGroupDetailView(APIView):
    """Get specific group details for consultant"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, group_id):
        access_key = request.query_params.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultant = CodeQuestConsultantRepository.get_by_access_key(access_key)
        
        if not consultant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        group = CodeQuestGroupRepository.get_by_id(group_id)
        
        if not group or group.consultant_id != consultant.id:
            return Response(
                {'error': 'Group not found or not assigned to you'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = GroupDetailSerializer(group)
        return Response(serializer.data)


# Scoring Views (Facilitators)
class ScoringProjectsListView(APIView):
    """List all projects for scoring"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_code = request.query_params.get('access_code')
        
        if not access_code:
            return Response(
                {'error': 'access_code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        facilitator = CodeQuestFacilitatorRepository.get_by_access_code(access_code)
        
        if not facilitator:
            return Response(
                {'error': 'Invalid access code'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        projects = CodeQuestProjectRepository.get_approved_projects(facilitator.event_id)
        serializer = CodeQuestProjectListSerializer(projects, many=True)
        
        return Response({
            'total_projects': projects.count(),
            'projects': serializer.data
        })


class ScoringCriteriaView(APIView):
    """Get scoring criteria for event"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_code = request.query_params.get('access_code')
        
        if not access_code:
            return Response(
                {'error': 'access_code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        facilitator = CodeQuestFacilitatorRepository.get_by_access_code(access_code)
        
        if not facilitator:
            return Response(
                {'error': 'Invalid access code'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        criteria = ScoringCriteriaRepository.get_criteria_by_event(facilitator.event_id)
        serializer = ScoringCriteriaSerializer(criteria, many=True)
        
        return Response({
            'total_criteria': criteria.count(),
            'criteria': serializer.data
        })


class SubmitScoreView(APIView):
    """Submit score for project"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        access_code = request.data.get('access_code')
        
        if not access_code:
            return Response(
                {'error': 'access_code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        facilitator = CodeQuestFacilitatorRepository.get_by_access_code(access_code)
        
        if not facilitator:
            return Response(
                {'error': 'Invalid access code'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = ProjectScoreSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check if already scored this criteria
            project_id = serializer.validated_data['project'].id
            criteria_id = serializer.validated_data['criteria'].id
            
            if ProjectScoreRepository.has_scored(facilitator.id, project_id, criteria_id):
                return Response(
                    {'error': 'Already scored this criteria for this project'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            score = serializer.save(facilitator=facilitator)
            
            response_serializer = ProjectScoreSerializer(score)
            return Response({
                'message': 'Score submitted successfully',
                'score': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FacilitatorMyScoresView(APIView):
    """View facilitator's submitted scores"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_code = request.query_params.get('access_code')
        
        if not access_code:
            return Response(
                {'error': 'access_code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        facilitator = CodeQuestFacilitatorRepository.get_by_access_code(access_code)
        
        if not facilitator:
            return Response(
                {'error': 'Invalid access code'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        scores = ProjectScoreRepository.get_scores_by_facilitator(facilitator.id)
        serializer = ProjectScoreSerializer(scores, many=True)
        
        return Response({
            'total_scores': scores.count(),
            'scores': serializer.data
        })


# Results & Leaderboard
class LeaderboardView(APIView):
    """Get published leaderboard"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        event_id = request.query_params.get('event_id')
        
        if not event_id:
            return Response(
                {'error': 'event_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        scores = FinalProjectScoreRepository.get_published_scores(event_id)
        serializer = FinalProjectScoreSerializer(scores, many=True)
        
        return Response({
            'total_projects': scores.count(),
            'leaderboard': serializer.data
        })


class MyScoreView(APIView):
    """Get participant's group score"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_key = request.query_params.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant or not participant.group:
            return Response(
                {'error': 'No group found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        project = CodeQuestProjectRepository.get_by_group(participant.group.id)
        
        if not project:
            return Response(
                {'message': 'No project found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        final_score = FinalProjectScoreRepository.get_by_project(project.id)
        
        if not final_score or not final_score.is_published:
            return Response({
                'message': 'Scores not yet published'
            })
        
        serializer = FinalProjectScoreSerializer(final_score)
        return Response(serializer.data)


class ScoreBreakdownView(APIView):
    """Get detailed score breakdown for a project"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, project_id):
        project = CodeQuestProjectRepository.get_by_id(project_id)
        
        if not project:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        final_score = FinalProjectScoreRepository.get_by_project(project_id)
        
        if not final_score or not final_score.is_published:
            return Response({
                'message': 'Scores not yet published'
            })
        
        scores = ProjectScoreRepository.get_scores_by_project(project_id)
        
        serializer = ProjectScoreSerializer(scores, many=True)
        final_serializer = FinalProjectScoreSerializer(final_score)
        
        return Response({
            'final_score': final_serializer.data,
            'detailed_scores': serializer.data
        })


# PM Election Views
class PMCandidatesView(APIView):
    """Get PM candidates for a group"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_key = request.query_params.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant or not participant.group:
            return Response(
                {'error': 'Invalid access key or no group assigned'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        candidates = ProjectManagerCandidateRepository.get_candidates_by_group(participant.group.id)
        serializer = ProjectManagerCandidateSerializer(candidates, many=True)
        
        return Response({
            'candidates': serializer.data,
            'total_candidates': candidates.count()
        })


class NominatePMView(APIView):
    """Self-nominate as PM candidate"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        access_key = request.data.get('access_key')
        nomination_statement = request.data.get('nomination_statement')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant or not participant.group:
            return Response(
                {'error': 'Invalid access key or no group assigned'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if already nominated
        existing = ProjectManagerCandidateRepository.get_by_participant_and_group(
            participant.id, participant.group.id
        )
        
        if existing:
            return Response(
                {'error': 'Already nominated'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        candidate = ProjectManagerCandidate.objects.create(
            participant=participant,
            group=participant.group,
            nomination_statement=nomination_statement or ''
        )
        
        serializer = ProjectManagerCandidateSerializer(candidate)
        return Response({
            'message': 'Nomination successful',
            'candidate': serializer.data
        }, status=status.HTTP_201_CREATED)


class VotePMView(APIView):
    """Vote for PM candidate"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        access_key = request.data.get('access_key')
        candidate_id = request.data.get('candidate_id')
        
        if not all([access_key, candidate_id]):
            return Response(
                {'error': 'access_key and candidate_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant or not participant.group:
            return Response(
                {'error': 'Invalid access key or no group assigned'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        candidate = ProjectManagerCandidateRepository.get_by_id(candidate_id)
        
        if not candidate or candidate.group != participant.group:
            return Response(
                {'error': 'Invalid candidate or not in same group'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already voted
        has_voted = ProjectManagerVoteRepository.has_voted(participant.id, participant.group.id)
        
        if has_voted:
            return Response(
                {'error': 'Already voted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Record vote atomically
        with transaction.atomic():
            vote = ProjectManagerVote.objects.create(
                voter=participant,
                candidate=candidate,
                group=participant.group
            )
            
            candidate.vote_count += 1
            candidate.save()
        
        return Response({
            'message': 'Vote recorded successfully',
            'candidate': ProjectManagerCandidateSerializer(candidate).data
        }, status=status.HTTP_201_CREATED)


# PM Actions
class AssignRoleView(APIView):
    """PM assigns role to group member"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        access_key = request.data.get('access_key')
        member_id = request.data.get('member_id')
        role_type = request.data.get('role_type')
        is_lead = request.data.get('is_lead', False)
        
        if not all([access_key, member_id, role_type]):
            return Response(
                {'error': 'access_key, member_id, and role_type are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pm = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not pm or not pm.group:
            return Response(
                {'error': 'Invalid access key or no group assigned'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if pm.group.project_manager != pm:
            return Response(
                {'error': 'Only PM can assign roles'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        member = CodeQuestParticipantRepository.get_by_id(member_id)
        
        if not member or member.group != pm.group:
            return Response(
                {'error': 'Member not found or not in same group'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update or create role
        role, created = GroupMemberRole.objects.update_or_create(
            member=member,
            group=pm.group,
            defaults={
                'role_type': role_type,
                'is_lead': is_lead,
                'assigned_by': pm
            }
        )
        
        serializer = GroupMemberRoleSerializer(role)
        return Response({
            'message': 'Role assigned successfully',
            'role': serializer.data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class CreateTaskView(APIView):
    """PM creates task for group"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        access_key = request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pm = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not pm or not pm.group:
            return Response(
                {'error': 'Invalid access key or no group assigned'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if pm.group.project_manager != pm:
            return Response(
                {'error': 'Only PM can create tasks'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProjectTaskSerializer(data=request.data)
        
        if serializer.is_valid():
            task = serializer.save(
                group=pm.group,
                created_by=pm
            )
            
            response_serializer = ProjectTaskSerializer(task)
            return Response({
                'message': 'Task created successfully',
                'task': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateTaskView(APIView):
    """Update task status"""
    permission_classes = [permissions.AllowAny]
    
    def patch(self, request, task_id):
        access_key = request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        task = ProjectTaskRepository.get_by_id(task_id)
        
        if not task:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only PM or assigned member can update
        is_pm = task.group.project_manager == participant
        is_assigned = task.assigned_to == participant
        
        if not (is_pm or is_assigned):
            return Response(
                {'error': 'Not authorized to update this task'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProjectTaskSerializer(task, data=request.data, partial=True)
        
        if serializer.is_valid():
            # Auto-set completed_date if status changed to COMPLETED
            if serializer.validated_data.get('status') == 'COMPLETED':
                serializer.validated_data['completed_date'] = timezone.now().date()
            
            task = serializer.save()
            
            response_serializer = ProjectTaskSerializer(task)
            return Response({
                'message': 'Task updated successfully',
                'task': response_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Project Management
class SubmitProjectView(APIView):
    """Submit project for group"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        access_key = request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant or not participant.group:
            return Response(
                {'error': 'Invalid access key or no group assigned'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if project already exists
        existing_project = CodeQuestProjectRepository.get_by_group(participant.group.id)
        
        if existing_project:
            return Response(
                {'error': 'Project already submitted. Use update endpoint instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CodeQuestProjectSerializer(data=request.data)
        
        if serializer.is_valid():
            project = serializer.save(group=participant.group)
            
            response_serializer = CodeQuestProjectSerializer(project)
            return Response({
                'message': 'Project submitted successfully',
                'project': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateProjectView(APIView):
    """Update project details"""
    permission_classes = [permissions.AllowAny]
    
    def patch(self, request, project_id):
        access_key = request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        project = CodeQuestProjectRepository.get_by_id(project_id)
        
        if not project:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if project.group != participant.group:
            return Response(
                {'error': 'Not authorized to update this project'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CodeQuestProjectSerializer(project, data=request.data, partial=True)
        
        if serializer.is_valid():
            project = serializer.save()
            
            response_serializer = CodeQuestProjectSerializer(project)
            return Response({
                'message': 'Project updated successfully',
                'project': response_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# SELF-GROUPING VIEWS
# ============================================================

class SelfGroupingStatusView(APIView):
    """
    Check if self-grouping is enabled and get participant's current status
    - Includes date range checks (start_date, end_date/lockdown)
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_key = request.query_params.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        event = participant.event
        
        # Check if self-grouping is enabled
        if not event.allow_self_grouping:
            return Response({
                'self_grouping_enabled': False,
                'self_grouping_active': False,
                'message': 'Self-grouping is not enabled for this event'
            })
        
        # Get detailed self-grouping status
        sg_status = event.get_self_grouping_status()
        is_active = event.is_self_grouping_active()
        is_locked = event.is_self_grouping_locked()
        
        # Base response with status info
        response_data = {
            'self_grouping_enabled': True,
            'self_grouping_active': is_active,
            'self_grouping_status': sg_status['status'],
            'self_grouping_message': sg_status['message'],
            'is_locked': is_locked,
            'start_date': event.self_grouping_start_date.isoformat() if event.self_grouping_start_date else None,
            'end_date': event.self_grouping_end_date.isoformat() if event.self_grouping_end_date else None,
            'min_group_size': event.min_group_size,
            'max_group_size': event.max_group_size,
        }
        
        # Check if participant is already in an official group
        if participant.group:
            response_data.update({
                'participant_status': 'in_official_group',
                'group_id': participant.group.id,
                'group_name': participant.group.group_name or participant.group.group_number,
                'message': 'You are already assigned to an official group'
            })
            return Response(response_data)
        
        # Check if participant is in a self-grouping team
        active_membership = SelfGroupingMembership.objects.filter(
            participant=participant,
            status='accepted',
            team__status__in=['forming', 'ready']
        ).select_related('team').first()
        
        if active_membership:
            team_serializer = SelfGroupingTeamSerializer(active_membership.team)
            response_data.update({
                'participant_status': 'in_team',
                'is_creator': active_membership.is_creator,
                'team': team_serializer.data,
                'message': 'You are in a self-grouping team'
            })
            return Response(response_data)
        
        # Participant is available for grouping
        pending_invitations = GroupInvitation.objects.filter(
            recipient=participant,
            status='pending'
        ).count()
        
        response_data.update({
            'participant_status': 'available',
            'pending_invitations': pending_invitations,
            'message': 'You can create or join a team' if is_active else sg_status['message']
        })
        
        return Response(response_data)


class AvailableParticipantsView(APIView):
    """
    List participants available for self-grouping (not in any group or team)
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_key = request.query_params.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        event = participant.event
        
        if not event.allow_self_grouping:
            return Response(
                {'error': 'Self-grouping is not enabled for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get participants who:
        # 1. Are in the same event
        # 2. Are not in an official group
        # 3. Are not in an active self-grouping team
        
        # Get IDs of participants in active teams
        in_team_ids = SelfGroupingMembership.objects.filter(
            team__event=event,
            status='accepted',
            team__status__in=['forming', 'ready']
        ).values_list('participant_id', flat=True)
        
        available_participants = CodeQuestParticipant.objects.filter(
            event=event,
            group__isnull=True  # Not in official group
        ).exclude(
            id__in=in_team_ids  # Not in active team
        ).exclude(
            id=participant.id  # Exclude self
        ).order_by('student_name')
        
        # Optional filtering
        role_filter = request.query_params.get('role')
        if role_filter:
            available_participants = available_participants.filter(preferred_role=role_filter)
        
        search = request.query_params.get('search')
        if search:
            available_participants = available_participants.filter(
                models.Q(student_name__icontains=search) |
                models.Q(student_id__icontains=search) |
                models.Q(skills__icontains=search)
            )
        
        serializer = ParticipantBriefSerializer(available_participants, many=True)
        
        return Response({
            'count': available_participants.count(),
            'participants': serializer.data
        })


class AvailableTeamsView(APIView):
    """
    List teams that are still accepting members (for join requests)
    Excludes teams the participant is already a member of
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_key = request.query_params.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        event = participant.event
        
        if not event.allow_self_grouping:
            return Response(
                {'error': 'Self-grouping is not enabled for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get IDs of teams the participant is already a member of
        my_team_ids = SelfGroupingMembership.objects.filter(
            participant=participant,
            status='accepted'
        ).values_list('team_id', flat=True)
        
        # Get teams that are still forming, can accept members, and exclude participant's teams
        available_teams = SelfGroupingTeam.objects.filter(
            event=event,
            status='forming'
        ).exclude(
            id__in=my_team_ids
        ).select_related('creator').prefetch_related('memberships')
        
        # Filter out full teams
        teams_with_space = []
        for team in available_teams:
            if team.can_add_members():
                teams_with_space.append(team)
        
        serializer = SelfGroupingTeamListSerializer(teams_with_space, many=True)
        
        return Response({
            'count': len(teams_with_space),
            'teams': serializer.data
        })


class CreateTeamView(APIView):
    """
    Create a new self-grouping team
    - Cannot create during lockdown period
    - Cannot create before self-grouping start date
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        access_key = request.query_params.get('access_key') or request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        event = participant.event
        
        if not event.allow_self_grouping:
            return Response(
                {'error': 'Self-grouping is not enabled for this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if self-grouping is active (within date range)
        if not event.is_self_grouping_active():
            sg_status = event.get_self_grouping_status()
            return Response(
                {'error': sg_status['message'], 'status': sg_status['status']},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already in official group
        if participant.group:
            return Response(
                {'error': 'You are already assigned to an official group'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already in a team
        existing_membership = SelfGroupingMembership.objects.filter(
            participant=participant,
            status='accepted',
            team__status__in=['forming', 'ready']
        ).exists()
        
        if existing_membership:
            return Response(
                {'error': 'You are already in a team. Leave your current team first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CreateTeamSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Create team
            team = SelfGroupingTeam.objects.create(
                event=event,
                team_name=serializer.validated_data.get('team_name', ''),
                creator=participant,
                status='forming'
            )
            
            # Add creator as first member
            SelfGroupingMembership.objects.create(
                team=team,
                participant=participant,
                status='accepted',
                is_creator=True
            )
        
        team_serializer = SelfGroupingTeamSerializer(team)
        
        return Response({
            'message': 'Team created successfully',
            'team': team_serializer.data
        }, status=status.HTTP_201_CREATED)


class MyTeamView(APIView):
    """
    Get details of participant's current team
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_key = request.query_params.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Find active membership
        membership = SelfGroupingMembership.objects.filter(
            participant=participant,
            status='accepted',
            team__status__in=['forming', 'ready']
        ).select_related('team').first()
        
        if not membership:
            return Response(
                {'error': 'You are not in any team'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        team_serializer = SelfGroupingTeamSerializer(membership.team)
        
        # Get pending invitations sent by this team
        pending_invitations = GroupInvitation.objects.filter(
            team=membership.team,
            status='pending'
        )
        invitations_serializer = GroupInvitationSerializer(pending_invitations, many=True)
        
        # Get pending join requests to this team
        pending_requests = JoinRequest.objects.filter(
            team=membership.team,
            status='pending'
        )
        requests_serializer = JoinRequestSerializer(pending_requests, many=True)
        
        return Response({
            'team': team_serializer.data,
            'is_creator': membership.is_creator,
            'pending_invitations_sent': invitations_serializer.data,
            'pending_join_requests': requests_serializer.data
        })


class LeaveTeamView(APIView):
    """
    Leave current self-grouping team
    - If creator leaves, transfer to next member (first to join)
    - If last member leaves, auto-delete the team
    - Cannot leave during lockdown period
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        access_key = request.query_params.get('access_key') or request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        event = participant.event
        
        # Check if self-grouping is locked
        if event.is_self_grouping_locked():
            return Response(
                {'error': 'Self-grouping period has ended. You cannot leave your team.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Find active membership
        membership = SelfGroupingMembership.objects.filter(
            participant=participant,
            status='accepted',
            team__status__in=['forming', 'ready']
        ).select_related('team').first()
        
        if not membership:
            return Response(
                {'error': 'You are not in any team'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        team = membership.team
        
        with transaction.atomic():
            # Mark current membership as left
            membership.status = 'left'
            membership.save()
            
            # Get remaining active members (excluding the one who just left)
            remaining_members = SelfGroupingMembership.objects.filter(
                team=team,
                status='accepted'
            ).exclude(id=membership.id).order_by('joined_at')
            
            if not remaining_members.exists():
                # No members left - disband the team
                team.status = 'disbanded'
                team.save()
                
                # Cancel all pending invitations
                GroupInvitation.objects.filter(team=team, status='pending').update(
                    status='cancelled',
                    responded_at=timezone.now()
                )
                
                # Cancel all pending join requests
                JoinRequest.objects.filter(team=team, status='pending').update(
                    status='cancelled',
                    responded_at=timezone.now()
                )
                
                return Response({
                    'message': 'Team disbanded because all members left',
                    'team_disbanded': True
                })
            
            elif membership.is_creator:
                # Creator is leaving but there are other members
                # Transfer creator role to the first member who joined
                new_creator = remaining_members.first()
                new_creator.is_creator = True
                new_creator.save()
                
                # Update the team's creator field
                team.creator = new_creator.participant
                team.save()
                
                # Update team status if needed
                if team.member_count() < (team.event.min_group_size or 5):
                    team.status = 'forming'
                    team.save()
                
                return Response({
                    'message': f'You have left the team. {new_creator.participant.student_name} is now the team creator.',
                    'team_disbanded': False,
                    'new_creator': new_creator.participant.student_name
                })
            
            else:
                # Regular member leaves
                # Update team status if needed
                if team.member_count() < (team.event.min_group_size or 5):
                    team.status = 'forming'
                    team.save()
                
                return Response({
                    'message': 'You have left the team',
                    'team_disbanded': False
                })


class SendInvitationView(APIView):
    """
    Send invitation to another participant to join your team
    - Cannot send during lockdown period
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        access_key = request.query_params.get('access_key') or request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        event = participant.event
        
        # Check if self-grouping is active
        if not event.is_self_grouping_active():
            sg_status = event.get_self_grouping_status()
            return Response(
                {'error': sg_status['message'], 'status': sg_status['status']},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Find participant's team
        membership = SelfGroupingMembership.objects.filter(
            participant=participant,
            status='accepted',
            team__status='forming'
        ).select_related('team').first()
        
        if not membership:
            return Response(
                {'error': 'You need to be in a forming team to send invitations'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        team = membership.team
        
        # Check if team can add more members
        if not team.can_add_members():
            return Response(
                {'error': 'Team is full'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = SendInvitationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        recipient_id = serializer.validated_data['recipient_id']
        message = serializer.validated_data.get('message', '')
        
        # Get recipient
        try:
            recipient = CodeQuestParticipant.objects.get(id=recipient_id, event=participant.event)
        except CodeQuestParticipant.DoesNotExist:
            return Response(
                {'error': 'Participant not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if recipient is already in a group
        if recipient.group:
            return Response(
                {'error': 'This participant is already in an official group'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if recipient is in another team
        recipient_in_team = SelfGroupingMembership.objects.filter(
            participant=recipient,
            status='accepted',
            team__status__in=['forming', 'ready']
        ).exists()
        
        if recipient_in_team:
            return Response(
                {'error': 'This participant is already in a team'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for existing pending invitation
        existing_invitation = GroupInvitation.objects.filter(
            team=team,
            recipient=recipient,
            status='pending'
        ).exists()
        
        if existing_invitation:
            return Response(
                {'error': 'You already have a pending invitation to this participant'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create invitation
        invitation = GroupInvitation.objects.create(
            team=team,
            sender=participant,
            recipient=recipient,
            message=message,
            status='pending'
        )
        
        # TODO: Send notification email to recipient
        
        invitation_serializer = GroupInvitationSerializer(invitation)
        
        return Response({
            'message': f'Invitation sent to {recipient.student_name}',
            'invitation': invitation_serializer.data
        }, status=status.HTTP_201_CREATED)


class CancelInvitationView(APIView):
    """
    Cancel a pending invitation
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, invitation_id):
        access_key = request.query_params.get('access_key') or request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            invitation = GroupInvitation.objects.get(id=invitation_id, status='pending')
        except GroupInvitation.DoesNotExist:
            return Response(
                {'error': 'Invitation not found or already processed'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if participant is in the team
        is_team_member = SelfGroupingMembership.objects.filter(
            team=invitation.team,
            participant=participant,
            status='accepted'
        ).exists()
        
        if not is_team_member:
            return Response(
                {'error': 'You are not authorized to cancel this invitation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        invitation.status = 'cancelled'
        invitation.responded_at = timezone.now()
        invitation.save()
        
        return Response({
            'message': 'Invitation cancelled'
        })


class MyInvitationsView(APIView):
    """
    Get invitations sent and received by the participant
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_key = request.query_params.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get received invitations (all statuses for display)
        received = GroupInvitation.objects.filter(
            recipient=participant
        ).select_related('team', 'sender').order_by('-created_at')
        
        # Get sent invitations (only if participant is in a team)
        sent = GroupInvitation.objects.filter(
            sender=participant
        ).select_related('team', 'recipient').order_by('-created_at')
        
        received_serializer = GroupInvitationSerializer(received, many=True)
        sent_serializer = GroupInvitationSerializer(sent, many=True)
        
        return Response({
            'received': received_serializer.data,
            'sent': sent_serializer.data
        })


class RespondToInvitationView(APIView):
    """
    Accept or decline an invitation
    - If user accepts while in another team, they leave the old team and join the new one
    - Cannot accept during lockdown period
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, invitation_id):
        access_key = request.query_params.get('access_key') or request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        event = participant.event
        
        # Check if self-grouping is locked
        if event.is_self_grouping_locked():
            return Response(
                {'error': 'Self-grouping period has ended. You cannot change teams.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            invitation = GroupInvitation.objects.get(
                id=invitation_id,
                recipient=participant,
                status='pending'
            )
        except GroupInvitation.DoesNotExist:
            return Response(
                {'error': 'Invitation not found or already processed'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = RespondInvitationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        action = serializer.validated_data['action']
        
        # Check if invitation expired
        if invitation.is_expired():
            invitation.status = 'expired'
            invitation.save()
            return Response(
                {'error': 'This invitation has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            if action == 'accept':
                # Check if already in a group
                if participant.group:
                    return Response(
                        {'error': 'You are already in an official group'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                team = invitation.team
                
                # Check if team can still add members
                if not team.can_add_members():
                    invitation.status = 'declined'
                    invitation.responded_at = timezone.now()
                    invitation.save()
                    return Response(
                        {'error': 'Team is now full'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Check if already in another team - if so, leave it first
                existing_membership = SelfGroupingMembership.objects.filter(
                    participant=participant,
                    status='accepted',
                    team__status__in=['forming', 'ready']
                ).select_related('team').first()
                
                left_previous_team = False
                previous_team_name = None
                
                if existing_membership:
                    old_team = existing_membership.team
                    previous_team_name = old_team.team_name or f"Team by {old_team.creator.student_name}"
                    
                    # Leave the old team
                    existing_membership.status = 'left'
                    existing_membership.save()
                    
                    # Check if old team needs creator transfer or disbanding
                    remaining_members = SelfGroupingMembership.objects.filter(
                        team=old_team,
                        status='accepted'
                    ).order_by('joined_at')
                    
                    if not remaining_members.exists():
                        # No members left - disband
                        old_team.status = 'disbanded'
                        old_team.save()
                        GroupInvitation.objects.filter(team=old_team, status='pending').update(
                            status='cancelled', responded_at=timezone.now()
                        )
                        JoinRequest.objects.filter(team=old_team, status='pending').update(
                            status='cancelled', responded_at=timezone.now()
                        )
                    elif existing_membership.is_creator:
                        # Transfer creator to next member
                        new_creator = remaining_members.first()
                        new_creator.is_creator = True
                        new_creator.save()
                        old_team.creator = new_creator.participant
                        old_team.save()
                    
                    # Update old team status if needed
                    if old_team.status != 'disbanded':
                        if old_team.member_count() < (old_team.event.min_group_size or 5):
                            old_team.status = 'forming'
                            old_team.save()
                    
                    left_previous_team = True
                
                # Add to new team
                SelfGroupingMembership.objects.create(
                    team=team,
                    participant=participant,
                    status='accepted',
                    is_creator=False
                )
                
                # Update invitation
                invitation.status = 'accepted'
                invitation.responded_at = timezone.now()
                invitation.save()
                
                # Cancel other pending invitations
                GroupInvitation.objects.filter(
                    recipient=participant,
                    status='pending'
                ).exclude(id=invitation.id).update(
                    status='cancelled',
                    responded_at=timezone.now()
                )
                
                # Cancel pending join requests from this participant
                JoinRequest.objects.filter(
                    requester=participant,
                    status='pending'
                ).update(
                    status='cancelled',
                    responded_at=timezone.now()
                )
                
                # Update team status if ready
                if team.is_ready_to_finalize():
                    team.status = 'ready'
                    team.save()
                
                team_serializer = SelfGroupingTeamSerializer(team)
                
                message = f'You have joined {team.team_name or "the team"}!'
                if left_previous_team:
                    message = f'You left "{previous_team_name}" and joined {team.team_name or "the team"}!'
                
                return Response({
                    'message': message,
                    'team': team_serializer.data,
                    'left_previous_team': left_previous_team
                })
            
            else:  # decline
                invitation.status = 'declined'
                invitation.responded_at = timezone.now()
                invitation.save()
                
                return Response({
                    'message': 'Invitation declined'
                })


class SendJoinRequestView(APIView):
    """
    Request to join an existing team
    - Cannot request during lockdown period
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        access_key = request.query_params.get('access_key') or request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        event = participant.event
        
        # Check if self-grouping is active
        if not event.is_self_grouping_active():
            sg_status = event.get_self_grouping_status()
            return Response(
                {'error': sg_status['message'], 'status': sg_status['status']},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already in a group
        if participant.group:
            return Response(
                {'error': 'You are already in an official group'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already in a team - allow but warn (they'd leave if request accepted)
        existing_membership = SelfGroupingMembership.objects.filter(
            participant=participant,
            status='accepted',
            team__status__in=['forming', 'ready']
        ).exists()
        
        # Note: We now allow users in a team to request to join another
        # If accepted, they will leave their current team
        
        serializer = SendJoinRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        team_id = serializer.validated_data['team_id']
        message = serializer.validated_data.get('message', '')
        
        try:
            team = SelfGroupingTeam.objects.get(
                id=team_id,
                event=participant.event,
                status='forming'
            )
        except SelfGroupingTeam.DoesNotExist:
            return Response(
                {'error': 'Team not found or not accepting requests'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if team can add members
        if not team.can_add_members():
            return Response(
                {'error': 'Team is full'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for existing pending request
        existing_request = JoinRequest.objects.filter(
            team=team,
            requester=participant,
            status='pending'
        ).exists()
        
        if existing_request:
            return Response(
                {'error': 'You already have a pending request to this team'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create join request
        join_request = JoinRequest.objects.create(
            team=team,
            requester=participant,
            message=message,
            status='pending'
        )
        
        request_serializer = JoinRequestSerializer(join_request)
        
        return Response({
            'message': f'Join request sent to {team.team_name or "the team"}',
            'request': request_serializer.data
        }, status=status.HTTP_201_CREATED)


class MyJoinRequestsView(APIView):
    """
    Get join requests sent by the participant
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        access_key = request.query_params.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get pending requests
        pending = JoinRequest.objects.filter(
            requester=participant,
            status='pending'
        ).select_related('team')
        
        # Get recent requests
        from datetime import timedelta
        recent_date = timezone.now() - timedelta(days=30)
        
        recent = JoinRequest.objects.filter(
            requester=participant,
            created_at__gte=recent_date
        ).exclude(
            status='pending'
        ).select_related('team').order_by('-responded_at')[:10]
        
        pending_serializer = JoinRequestSerializer(pending, many=True)
        recent_serializer = JoinRequestSerializer(recent, many=True)
        
        return Response({
            'pending_count': pending.count(),
            'pending': pending_serializer.data,
            'recent': recent_serializer.data
        })


class CancelJoinRequestView(APIView):
    """
    Cancel a pending join request
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, request_id):
        access_key = request.query_params.get('access_key') or request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            join_request = JoinRequest.objects.get(
                id=request_id,
                requester=participant,
                status='pending'
            )
        except JoinRequest.DoesNotExist:
            return Response(
                {'error': 'Request not found or already processed'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        join_request.status = 'cancelled'
        join_request.responded_at = timezone.now()
        join_request.save()
        
        return Response({
            'message': 'Join request cancelled'
        })


class RespondToJoinRequestView(APIView):
    """
    Accept or decline a join request (team creator/members)
    - If requester is in another team, they will leave it when accepted
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, request_id):
        access_key = request.query_params.get('access_key') or request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        event = participant.event
        
        # Check if self-grouping is locked
        if event.is_self_grouping_locked():
            return Response(
                {'error': 'Self-grouping period has ended. You cannot accept new members.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            join_request = JoinRequest.objects.get(id=request_id, status='pending')
        except JoinRequest.DoesNotExist:
            return Response(
                {'error': 'Request not found or already processed'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if participant is in the team (and is creator)
        membership = SelfGroupingMembership.objects.filter(
            team=join_request.team,
            participant=participant,
            status='accepted',
            is_creator=True  # Only creator can accept/decline requests
        ).first()
        
        if not membership:
            return Response(
                {'error': 'Only the team creator can respond to join requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RespondJoinRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        action = serializer.validated_data['action']
        team = join_request.team
        requester = join_request.requester
        
        with transaction.atomic():
            if action == 'accept':
                # Check if requester is now in a group
                if requester.group:
                    join_request.status = 'declined'
                    join_request.responded_by = participant
                    join_request.responded_at = timezone.now()
                    join_request.save()
                    return Response(
                        {'error': 'Requester is now in an official group'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Check if team can still add members
                if not team.can_add_members():
                    return Response(
                        {'error': 'Team is now full'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Check if requester is in another team - if so, leave it first
                existing_membership = SelfGroupingMembership.objects.filter(
                    participant=requester,
                    status='accepted',
                    team__status__in=['forming', 'ready']
                ).select_related('team').first()
                
                if existing_membership:
                    old_team = existing_membership.team
                    
                    # Leave the old team
                    existing_membership.status = 'left'
                    existing_membership.save()
                    
                    # Check if old team needs creator transfer or disbanding
                    remaining_members = SelfGroupingMembership.objects.filter(
                        team=old_team,
                        status='accepted'
                    ).order_by('joined_at')
                    
                    if not remaining_members.exists():
                        # No members left - disband
                        old_team.status = 'disbanded'
                        old_team.save()
                        GroupInvitation.objects.filter(team=old_team, status='pending').update(
                            status='cancelled', responded_at=timezone.now()
                        )
                        JoinRequest.objects.filter(team=old_team, status='pending').update(
                            status='cancelled', responded_at=timezone.now()
                        )
                    elif existing_membership.is_creator:
                        # Transfer creator to next member
                        new_creator = remaining_members.first()
                        new_creator.is_creator = True
                        new_creator.save()
                        old_team.creator = new_creator.participant
                        old_team.save()
                    
                    # Update old team status if needed
                    if old_team.status != 'disbanded':
                        if old_team.member_count() < (old_team.event.min_group_size or 5):
                            old_team.status = 'forming'
                            old_team.save()
                
                # Add to team
                SelfGroupingMembership.objects.create(
                    team=team,
                    participant=requester,
                    status='accepted',
                    is_creator=False
                )
                
                # Update request
                join_request.status = 'accepted'
                join_request.responded_by = participant
                join_request.responded_at = timezone.now()
                join_request.save()
                
                # Cancel requester's other pending requests
                JoinRequest.objects.filter(
                    requester=requester,
                    status='pending'
                ).exclude(id=join_request.id).update(
                    status='cancelled',
                    responded_at=timezone.now()
                )
                
                # Decline pending invitations to requester
                GroupInvitation.objects.filter(
                    recipient=requester,
                    status='pending'
                ).update(
                    status='cancelled',
                    responded_at=timezone.now()
                )
                
                # Update team status
                if team.is_ready_to_finalize():
                    team.status = 'ready'
                    team.save()
                
                return Response({
                    'message': f'{requester.student_name} has joined the team!',
                    'new_member_count': team.member_count()
                })
            
            else:  # decline
                join_request.status = 'declined'
                join_request.responded_by = participant
                join_request.responded_at = timezone.now()
                join_request.save()
                
                return Response({
                    'message': 'Request declined'
                })


class FinalizeTeamView(APIView):
    """
    Finalize a team and create an official CodeQuestGroup
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        access_key = request.query_params.get('access_key') or request.data.get('access_key')
        
        if not access_key:
            return Response(
                {'error': 'access_key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = CodeQuestParticipantRepository.get_by_access_key(access_key)
        
        if not participant:
            return Response(
                {'error': 'Invalid access key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Find participant's team (must be creator)
        membership = SelfGroupingMembership.objects.filter(
            participant=participant,
            status='accepted',
            is_creator=True,
            team__status__in=['forming', 'ready']
        ).select_related('team').first()
        
        if not membership:
            return Response(
                {'error': 'You must be the team creator to finalize'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        team = membership.team
        
        # Check if team is ready
        if not team.is_ready_to_finalize():
            min_size = team.event.min_group_size or 5
            return Response({
                'error': f'Team needs at least {min_size} members to finalize',
                'current_members': team.member_count(),
                'required': min_size
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Get next group number
            existing_groups = CodeQuestGroup.objects.filter(event=team.event).count()
            group_number = f"Group {existing_groups + 1}"
            
            # Create official group
            official_group = CodeQuestGroup.objects.create(
                event=team.event,
                group_number=group_number,
                group_name=team.team_name,
                category='regular',  # Can be updated by admin
                is_complete=True
            )
            
            # Move all members to official group
            for team_membership in team.memberships.filter(status='accepted'):
                team_membership.participant.group = official_group
                team_membership.participant.save()
            
            # Update team status
            team.status = 'finalized'
            team.finalized_group = official_group
            team.finalized_at = timezone.now()
            team.save()
            
            # Cancel all pending invitations and requests
            GroupInvitation.objects.filter(team=team, status='pending').update(
                status='cancelled',
                responded_at=timezone.now()
            )
            JoinRequest.objects.filter(team=team, status='pending').update(
                status='cancelled',
                responded_at=timezone.now()
            )
            
            # Send notification emails to all members
            from codequest.utils import notify_group_members_on_formation
            notify_group_members_on_formation(official_group)
        
        return Response({
            'message': 'Team finalized! You are now officially grouped.',
            'group_id': official_group.id,
            'group_number': official_group.group_number,
            'group_name': official_group.group_name
        })
