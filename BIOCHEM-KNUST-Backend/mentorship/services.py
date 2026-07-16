"""
Mentorship System - Services Layer

Business logic for the mentorship system.
Handles complex operations, validations, and integrations.
"""

from rest_framework import status
from rest_framework.request import Request
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from typing import Tuple, Dict, Any, Optional
from uuid import UUID
import logging

from mentorship.repository import (
    MentorshipAreaRepository,
    SkillTagRepository,
    InterviewerRepository,
    InterviewerScheduleRepository,
    MentorApplicationRepository,
    ApprovedMentorRepository,
    MenteeApplicationRepository,
    MentorshipRelationshipRepository,
    MentorshipSessionRepository,
    MentorPaymentRepository,
)
from mentorship.models import (
    MentorApplication,
    ApprovedMentor,
    MenteeApplication,
    MentorshipRelationship,
    InterviewerSchedule,
    Interviewer,
)
from accounts.models import CustomUser

logger = logging.getLogger(__name__)


# ===========================
# Eligibility Services
# ===========================

def check_mentor_eligibility(user: CustomUser) -> Dict[str, Any]:
    """
    Check if a user is eligible to apply as a mentor.
    
    Rules:
    - Must not be a first-year student
    - Must not have a pending application
    - Must not already be an approved mentor
    """
    year = user.get_year()
    
    # Check year restriction
    if year == 1:
        return {
            'is_eligible': False,
            'current_year': year,
            'message': 'First-year students are not eligible to apply as mentors. '
                       'You can apply starting from your second year.',
            'has_pending_application': False,
            'is_approved_mentor': False,
        }
    
    # Check for pending application
    has_pending = MentorApplicationRepository.has_pending_application(user)
    if has_pending:
        return {
            'is_eligible': False,
            'current_year': year,
            'message': 'You already have a pending mentor application.',
            'has_pending_application': True,
            'is_approved_mentor': False,
        }
    
    # Check if already an approved mentor
    mentor = ApprovedMentorRepository.get_by_user(user)
    if mentor:
        return {
            'is_eligible': False,
            'current_year': year,
            'message': 'You are already an approved mentor.',
            'has_pending_application': False,
            'is_approved_mentor': True,
        }
    
    return {
        'is_eligible': True,
        'current_year': year,
        'message': 'You are eligible to apply as a mentor.',
        'has_pending_application': False,
        'is_approved_mentor': False,
    }


# ===========================
# Mentor Application Services
# ===========================

def create_mentor_application_service(
    request: Request,
    serializer_class
) -> Tuple[int, Dict[str, Any]]:
    """
    Service for creating a mentor application.
    """
    user = request.user
    
    # Check eligibility first
    eligibility = check_mentor_eligibility(user)
    if not eligibility['is_eligible']:
        return (
            status.HTTP_400_BAD_REQUEST,
            {
                'status': 'error',
                'message': eligibility['message'],
                'eligibility': eligibility
            }
        )
    
    # Validate and create application
    serializer = serializer_class(data=request.data, context={'request': request})
    if serializer.is_valid():
        try:
            application = serializer.save()
            return (
                status.HTTP_201_CREATED,
                {
                    'status': 'success',
                    'message': 'Mentor application submitted successfully.',
                    'application_id': str(application.id)
                }
            )
        except Exception as e:
            logger.error(f"Error creating mentor application: {str(e)}")
            return (
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {
                    'status': 'error',
                    'message': 'An error occurred while submitting your application.'
                }
            )
    
    return (
        status.HTTP_400_BAD_REQUEST,
        {
            'status': 'error',
            'message': 'Invalid application data.',
            'errors': serializer.errors
        }
    )


def get_mentor_application_service(
    request: Request,
    application_id: UUID
) -> Tuple[int, Dict[str, Any]]:
    """
    Get mentor application details.
    """
    application = MentorApplicationRepository.get_by_id(application_id)
    
    if not application:
        return (
            status.HTTP_404_NOT_FOUND,
            {'status': 'error', 'message': 'Application not found.'}
        )
    
    # Check permission (owner or staff)
    if application.applicant != request.user and not request.user.is_staff:
        return (
            status.HTTP_403_FORBIDDEN,
            {'status': 'error', 'message': 'You do not have permission to view this application.'}
        )
    
    from mentorship.serializers import MentorApplicationDetailSerializer
    serializer = MentorApplicationDetailSerializer(application)
    
    return (status.HTTP_200_OK, serializer.data)


def get_user_mentor_applications_service(request: Request) -> Tuple[int, Dict[str, Any]]:
    """
    Get all mentor applications for the current user.
    """
    applications = MentorApplicationRepository.get_by_user(request.user)
    
    from mentorship.serializers import MentorApplicationListSerializer
    serializer = MentorApplicationListSerializer(applications, many=True)
    
    return (status.HTTP_200_OK, {'applications': serializer.data})


def schedule_interview_service(
    request: Request,
    application_id: UUID,
    schedule_id: UUID
) -> Tuple[int, Dict[str, Any]]:
    """
    Schedule an interview for a mentor application.
    """
    application = MentorApplicationRepository.get_by_id(application_id)
    
    if not application:
        return (
            status.HTTP_404_NOT_FOUND,
            {'status': 'error', 'message': 'Application not found.'}
        )
    
    # Check permission
    if application.applicant != request.user:
        return (
            status.HTTP_403_FORBIDDEN,
            {'status': 'error', 'message': 'You can only schedule interviews for your own applications.'}
        )
    
    # Check application status
    if application.status not in ['submitted', 'draft']:
        return (
            status.HTTP_400_BAD_REQUEST,
            {'status': 'error', 'message': f'Cannot schedule interview. Application status is {application.status}.'}
        )
    
    # Get and validate schedule
    schedule = InterviewerScheduleRepository.get_by_id(schedule_id)
    
    if not schedule:
        return (
            status.HTTP_404_NOT_FOUND,
            {'status': 'error', 'message': 'Schedule not found.'}
        )
    
    if not schedule.is_available:
        return (
            status.HTTP_400_BAD_REQUEST,
            {'status': 'error', 'message': 'This interview slot is no longer available.'}
        )
    
    try:
        with transaction.atomic():
            application.schedule_interview(schedule)
            
            # TODO: Send notification to applicant and interviewer
            # This would integrate with your notifications system
            
            return (
                status.HTTP_200_OK,
                {
                    'status': 'success',
                    'message': 'Interview scheduled successfully.',
                    'interview_date': str(schedule.date),
                    'interview_time': f"{schedule.start_time} - {schedule.end_time}",
                    'interviewer': schedule.interviewer.full_name
                }
            )
    except ValidationError as e:
        return (
            status.HTTP_400_BAD_REQUEST,
            {'status': 'error', 'message': str(e)}
        )
    except Exception as e:
        logger.error(f"Error scheduling interview: {str(e)}")
        return (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            {'status': 'error', 'message': 'An error occurred while scheduling the interview.'}
        )


# ===========================
# Interviewer Services
# ===========================

def get_interviewers_list_service(
    area_id: Optional[UUID] = None
) -> Tuple[int, Dict[str, Any]]:
    """
    Get list of interviewers with available schedules.
    """
    if area_id:
        interviewers = InterviewerRepository.get_with_available_schedules(area_id)
    else:
        interviewers = InterviewerRepository.get_with_available_schedules()
    
    from mentorship.serializers import InterviewerSerializer
    serializer = InterviewerSerializer(interviewers, many=True)
    
    return (status.HTTP_200_OK, {'interviewers': serializer.data})


def interviewer_action_service(
    request: Request,
    application_id: UUID,
    action: str,
    notes: str = "",
    interview_link: str = ""
) -> Tuple[int, Dict[str, Any]]:
    """
    Interviewer actions: approve, reject, complete_interview, send_link
    """
    # Get interviewer profile
    interviewer = InterviewerRepository.get_by_user(request.user)
    
    if not interviewer:
        return (
            status.HTTP_403_FORBIDDEN,
            {'status': 'error', 'message': 'You are not registered as an interviewer.'}
        )
    
    application = MentorApplicationRepository.get_by_id(application_id)
    
    if not application:
        return (
            status.HTTP_404_NOT_FOUND,
            {'status': 'error', 'message': 'Application not found.'}
        )
    
    # Check if this interviewer is assigned to this application
    if application.assigned_interviewer != interviewer:
        return (
            status.HTTP_403_FORBIDDEN,
            {'status': 'error', 'message': 'You are not the assigned interviewer for this application.'}
        )
    
    try:
        with transaction.atomic():
            if action == 'send_link':
                application.interview_link = interview_link
                application.save()
                # TODO: Send notification to applicant
                return (
                    status.HTTP_200_OK,
                    {'status': 'success', 'message': 'Interview link sent successfully.'}
                )
            
            elif action == 'complete_interview':
                application.complete_interview(notes)
                return (
                    status.HTTP_200_OK,
                    {'status': 'success', 'message': 'Interview marked as completed.'}
                )
            
            elif action == 'approve':
                if application.status != 'interview_completed':
                    return (
                        status.HTTP_400_BAD_REQUEST,
                        {'status': 'error', 'message': 'Interview must be completed before approval.'}
                    )
                
                application.approve(interviewer, notes)
                
                # Create approved mentor profile
                mentor = ApprovedMentorRepository.create_from_application(application)
                
                # TODO: Send notification to applicant
                
                return (
                    status.HTTP_200_OK,
                    {
                        'status': 'success',
                        'message': 'Mentor application approved successfully.',
                        'mentor_id': str(mentor.id)
                    }
                )
            
            elif action == 'reject':
                application.reject(interviewer, notes)
                # TODO: Send notification to applicant
                return (
                    status.HTTP_200_OK,
                    {'status': 'success', 'message': 'Mentor application rejected.'}
                )
            
            else:
                return (
                    status.HTTP_400_BAD_REQUEST,
                    {'status': 'error', 'message': f'Invalid action: {action}'}
                )
    
    except ValidationError as e:
        return (
            status.HTTP_400_BAD_REQUEST,
            {'status': 'error', 'message': str(e)}
        )
    except Exception as e:
        logger.error(f"Error in interviewer action: {str(e)}")
        return (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            {'status': 'error', 'message': 'An error occurred while processing the action.'}
        )


def get_interviewer_applications_service(request: Request) -> Tuple[int, Dict[str, Any]]:
    """
    Get applications assigned to an interviewer.
    """
    interviewer = InterviewerRepository.get_by_user(request.user)
    
    if not interviewer:
        return (
            status.HTTP_403_FORBIDDEN,
            {'status': 'error', 'message': 'You are not registered as an interviewer.'}
        )
    
    applications = MentorApplicationRepository.get_by_interviewer(interviewer)
    
    from mentorship.serializers import MentorApplicationListSerializer
    serializer = MentorApplicationListSerializer(applications, many=True)
    
    return (status.HTTP_200_OK, {'applications': serializer.data})


# ===========================
# Mentee Application Services
# ===========================

def create_mentee_application_service(
    request: Request,
    serializer_class
) -> Tuple[int, Dict[str, Any]]:
    """
    Service for creating a mentee application.
    """
    serializer = serializer_class(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        try:
            application = serializer.save()
            
            # TODO: Send notification to mentor
            
            return (
                status.HTTP_201_CREATED,
                {
                    'status': 'success',
                    'message': 'Mentee application submitted successfully. Waiting for mentor approval.',
                    'application_id': str(application.id)
                }
            )
        except Exception as e:
            logger.error(f"Error creating mentee application: {str(e)}")
            return (
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {
                    'status': 'error',
                    'message': 'An error occurred while submitting your application.'
                }
            )
    
    return (
        status.HTTP_400_BAD_REQUEST,
        {
            'status': 'error',
            'message': 'Invalid application data.',
            'errors': serializer.errors
        }
    )


def get_mentee_applications_service(request: Request) -> Tuple[int, Dict[str, Any]]:
    """
    Get all mentee applications for the current user.
    """
    applications = MenteeApplicationRepository.get_by_applicant(request.user)
    
    from mentorship.serializers import MenteeApplicationListSerializer
    serializer = MenteeApplicationListSerializer(applications, many=True)
    
    return (status.HTTP_200_OK, {'applications': serializer.data})


def mentor_respond_to_mentee_service(
    request: Request,
    application_id: UUID,
    action: str,
    response_message: str = ""
) -> Tuple[int, Dict[str, Any]]:
    """
    Mentor accepts or rejects a mentee application.
    """
    # Get mentor profile
    mentor = ApprovedMentorRepository.get_by_user(request.user)
    
    if not mentor:
        return (
            status.HTTP_403_FORBIDDEN,
            {'status': 'error', 'message': 'You are not an approved mentor.'}
        )
    
    application = MenteeApplicationRepository.get_by_id(application_id)
    
    if not application:
        return (
            status.HTTP_404_NOT_FOUND,
            {'status': 'error', 'message': 'Application not found.'}
        )
    
    # Check if this is the mentor's application to respond to
    if application.mentor != mentor:
        return (
            status.HTTP_403_FORBIDDEN,
            {'status': 'error', 'message': 'This application was not sent to you.'}
        )
    
    if application.status != 'pending':
        return (
            status.HTTP_400_BAD_REQUEST,
            {'status': 'error', 'message': f'Application is already {application.status}.'}
        )
    
    try:
        with transaction.atomic():
            if action == 'accept':
                if not mentor.has_available_slots:
                    return (
                        status.HTTP_400_BAD_REQUEST,
                        {'status': 'error', 'message': 'You have no available mentee slots.'}
                    )
                
                application.accept(response_message)
                
                # TODO: Send notification to mentee
                
                return (
                    status.HTTP_200_OK,
                    {
                        'status': 'success',
                        'message': 'Mentee application accepted. A new mentorship relationship has been created.',
                    }
                )
            
            elif action == 'reject':
                application.reject(response_message)
                
                # TODO: Send notification to mentee
                
                return (
                    status.HTTP_200_OK,
                    {'status': 'success', 'message': 'Mentee application rejected.'}
                )
            
            else:
                return (
                    status.HTTP_400_BAD_REQUEST,
                    {'status': 'error', 'message': f'Invalid action: {action}'}
                )
    
    except ValidationError as e:
        return (
            status.HTTP_400_BAD_REQUEST,
            {'status': 'error', 'message': str(e)}
        )
    except Exception as e:
        logger.error(f"Error responding to mentee application: {str(e)}")
        return (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            {'status': 'error', 'message': 'An error occurred while processing the response.'}
        )


def get_mentor_pending_applications_service(request: Request) -> Tuple[int, Dict[str, Any]]:
    """
    Get pending mentee applications for a mentor.
    """
    mentor = ApprovedMentorRepository.get_by_user(request.user)
    
    if not mentor:
        return (
            status.HTTP_403_FORBIDDEN,
            {'status': 'error', 'message': 'You are not an approved mentor.'}
        )
    
    applications = MenteeApplicationRepository.get_pending_by_mentor(mentor)
    
    from mentorship.serializers import MenteeApplicationDetailSerializer
    serializer = MenteeApplicationDetailSerializer(applications, many=True)
    
    return (status.HTTP_200_OK, {'applications': serializer.data})


# ===========================
# Mentor Discovery Services
# ===========================

def list_approved_mentors_service(
    area_id: Optional[UUID] = None,
    search_query: Optional[str] = None
) -> Tuple[int, Dict[str, Any]]:
    """
    List approved mentors for mentees to discover.
    """
    if search_query:
        mentors = ApprovedMentorRepository.search(search_query, area_id)
    elif area_id:
        mentors = ApprovedMentorRepository.get_by_area(area_id)
    else:
        mentors = ApprovedMentorRepository.get_accepting_mentees()
    
    from mentorship.serializers import ApprovedMentorListSerializer
    serializer = ApprovedMentorListSerializer(mentors, many=True)
    
    return (status.HTTP_200_OK, {'mentors': serializer.data})


def get_mentor_detail_service(mentor_id: UUID) -> Tuple[int, Dict[str, Any]]:
    """
    Get detailed information about a mentor.
    """
    mentor = ApprovedMentorRepository.get_by_id(mentor_id)
    
    if not mentor:
        return (
            status.HTTP_404_NOT_FOUND,
            {'status': 'error', 'message': 'Mentor not found.'}
        )
    
    from mentorship.serializers import ApprovedMentorDetailSerializer
    serializer = ApprovedMentorDetailSerializer(mentor)
    
    return (status.HTTP_200_OK, serializer.data)


# ===========================
# Mentorship Relationship Services
# ===========================

def get_user_mentorships_service(request: Request) -> Tuple[int, Dict[str, Any]]:
    """
    Get all mentorship relationships for the current user.
    """
    user = request.user
    
    # Check if user is a mentor
    mentor = ApprovedMentorRepository.get_by_user(user)
    
    as_mentor = []
    as_mentee = []
    
    if mentor:
        mentor_relationships = MentorshipRelationshipRepository.get_by_mentor(mentor)
        from mentorship.serializers import MentorshipRelationshipListSerializer
        as_mentor = MentorshipRelationshipListSerializer(mentor_relationships, many=True).data
    
    mentee_relationships = MentorshipRelationshipRepository.get_by_mentee(user)
    from mentorship.serializers import MentorshipRelationshipListSerializer
    as_mentee = MentorshipRelationshipListSerializer(mentee_relationships, many=True).data
    
    return (
        status.HTTP_200_OK,
        {
            'as_mentor': as_mentor,
            'as_mentee': as_mentee
        }
    )


# ===========================
# Session Services
# ===========================

def create_session_service(
    request: Request,
    serializer_class
) -> Tuple[int, Dict[str, Any]]:
    """
    Create a new mentorship session.
    """
    serializer = serializer_class(data=request.data)
    
    if serializer.is_valid():
        try:
            session = serializer.save()
            
            # TODO: Send notifications to both parties
            
            return (
                status.HTTP_201_CREATED,
                {
                    'status': 'success',
                    'message': 'Session scheduled successfully.',
                    'session_id': str(session.id)
                }
            )
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return (
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {
                    'status': 'error',
                    'message': 'An error occurred while scheduling the session.'
                }
            )
    
    return (
        status.HTTP_400_BAD_REQUEST,
        {
            'status': 'error',
            'message': 'Invalid session data.',
            'errors': serializer.errors
        }
    )


def complete_session_service(
    request: Request,
    session_id: UUID,
    mentor_notes: str = ""
) -> Tuple[int, Dict[str, Any]]:
    """
    Mark a session as completed (mentor only).
    """
    session = MentorshipSessionRepository.get_by_id(session_id)
    
    if not session:
        return (
            status.HTTP_404_NOT_FOUND,
            {'status': 'error', 'message': 'Session not found.'}
        )
    
    # Check permission - only mentor can complete
    user = request.user
    is_mentor = session.relationship.mentor.user == user
    
    if not is_mentor:
        return (
            status.HTTP_403_FORBIDDEN,
            {'status': 'error', 'message': 'Only the mentor can complete this session.'}
        )
    
    if session.status == 'completed':
        return (
            status.HTTP_400_BAD_REQUEST,
            {'status': 'error', 'message': 'Session is already completed.'}
        )
    
    try:
        session.complete(mentor_notes)
        
        return (
            status.HTTP_200_OK,
            {'status': 'success', 'message': 'Session marked as completed.'}
        )
    except Exception as e:
        logger.error(f"Error completing session: {str(e)}")
        return (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            {'status': 'error', 'message': 'An error occurred while completing the session.'}
        )


def add_session_review_service(
    request: Request,
    session_id: UUID,
    feedback: str = "",
    rating: Optional[int] = None
) -> Tuple[int, Dict[str, Any]]:
    """
    Add mentee's feedback and rating to a completed session (mentee only).
    """
    session = MentorshipSessionRepository.get_by_id(session_id)
    
    if not session:
        return (
            status.HTTP_404_NOT_FOUND,
            {'status': 'error', 'message': 'Session not found.'}
        )
    
    # Check permission - only mentee can review
    user = request.user
    is_mentee = session.relationship.mentee == user
    
    if not is_mentee:
        return (
            status.HTTP_403_FORBIDDEN,
            {'status': 'error', 'message': 'Only the mentee can review this session.'}
        )
    
    if session.status != 'completed':
        return (
            status.HTTP_400_BAD_REQUEST,
            {'status': 'error', 'message': 'Can only review completed sessions.'}
        )
    
    if session.rating:
        return (
            status.HTTP_400_BAD_REQUEST,
            {'status': 'error', 'message': 'You have already reviewed this session.'}
        )
    
    try:
        session.add_mentee_review(feedback, rating)
        
        return (
            status.HTTP_200_OK,
            {'status': 'success', 'message': 'Review submitted successfully.'}
        )
    except Exception as e:
        logger.error(f"Error adding session review: {str(e)}")
        return (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            {'status': 'error', 'message': 'An error occurred while submitting your review.'}
        )


# ===========================
# Dashboard Services
# ===========================

def get_mentor_dashboard_service(request: Request) -> Tuple[int, Dict[str, Any]]:
    """
    Get dashboard data for a mentor.
    """
    user = request.user
    mentor = ApprovedMentorRepository.get_by_user(user)
    
    if not mentor:
        # Check if user has an application
        application = MentorApplicationRepository.get_latest_by_user(user)
        
        if application:
            from mentorship.serializers import MentorApplicationDetailSerializer
            return (
                status.HTTP_200_OK,
                {
                    'is_approved': False,
                    'application': MentorApplicationDetailSerializer(application).data
                }
            )
        
        return (
            status.HTTP_200_OK,
            {
                'is_approved': False,
                'application': None,
                'eligibility': check_mentor_eligibility(user)
            }
        )
    
    # Get mentor's data
    from mentorship.serializers import (
        ApprovedMentorDetailSerializer,
        MenteeApplicationDetailSerializer,
        MentorshipRelationshipListSerializer,
        MentorshipSessionSerializer
    )
    
    pending_applications = MenteeApplicationRepository.get_pending_by_mentor(mentor)
    active_mentees = MentorshipRelationshipRepository.get_active_by_mentor(mentor)
    all_sessions = MentorshipSessionRepository.get_by_mentor(mentor)
    upcoming_sessions = MentorshipSessionRepository.get_upcoming(user, as_mentor=True)
    total_earnings = MentorPaymentRepository.get_total_earnings(mentor)
    
    # Debug logging
    logger = logging.getLogger(__name__)
    logger.info(f"[MentorDashboard] User: {user.id} ({user.first_name})")
    logger.info(f"[MentorDashboard] ApprovedMentor: {mentor.id}")
    logger.info(f"[MentorDashboard] Active Mentees: {len(active_mentees)}")
    logger.info(f"[MentorDashboard] All Sessions: {len(all_sessions)}")
    logger.info(f"[MentorDashboard] Upcoming Sessions: {len(upcoming_sessions)}")
    
    # Check raw session count in database
    from mentorship.models import MentorshipSession
    all_sessions_in_db = MentorshipSession.objects.count()
    logger.info(f"[MentorDashboard] Total sessions in DB: {all_sessions_in_db}")
    
    # Check relationships for this mentor
    mentor_relationships = mentor.mentorship_relationships.all()
    logger.info(f"[MentorDashboard] Mentor relationships: {len(mentor_relationships)}")
    for rel in mentor_relationships:
        sessions_for_rel = rel.sessions.all()
        logger.info(f"[MentorDashboard] Relationship {rel.id}: {len(sessions_for_rel)} sessions")
    
    # Calculate stats
    completed_sessions = [s for s in all_sessions if s.status == 'completed']
    
    # Get donation stats and wallet info
    from mentorship.payment_services import MentorDonationService, MentorWalletService
    donation_stats = MentorDonationService.get_mentor_donation_stats(mentor)
    
    # Get recent donations received
    from mentorship.models import MentorPayment
    recent_donations = MentorPayment.objects.filter(
        mentor=mentor,
        payment_type='offering',
        status='completed'
    ).select_related('mentee').order_by('-created_at')[:10]
    
    donation_history = [
        {
            'id': str(donation.id),
            'donor_name': f"{donation.mentee.first_name} {donation.mentee.last_name}",
            'amount': float(donation.amount),
            'message': donation.offering_description or '',
            'date': donation.created_at.strftime('%Y-%m-%d %H:%M'),
        }
        for donation in recent_donations
    ]
    
    return (
        status.HTTP_200_OK,
        {
            'is_approved': True,
            'mentor_profile': ApprovedMentorDetailSerializer(mentor).data,
            'pending_applications': MenteeApplicationDetailSerializer(pending_applications, many=True).data,
            'active_mentees': MentorshipRelationshipListSerializer(active_mentees, many=True).data,
            'all_sessions': MentorshipSessionSerializer(all_sessions, many=True).data,
            'upcoming_sessions': MentorshipSessionSerializer(upcoming_sessions, many=True).data,
            'total_sessions': len(all_sessions),
            'sessions_conducted': len(completed_sessions),
            'active_mentees_count': len(active_mentees),
            'total_earnings': float(total_earnings),
            'pending_earnings': 0.0,  # TODO: Calculate pending earnings
            'paid_sessions': 0,  # TODO: Calculate paid sessions
            # Donation & Wallet Info
            'wallet_balance': float(donation_stats['wallet_balance']),
            'has_wallet': donation_stats['has_wallet'],
            'total_donations_received': float(donation_stats['total_donations_received']),
            'total_donors': donation_stats['total_donors'],
            'total_donations_count': donation_stats['total_donations_count'],
            'donation_history': donation_history,
        }
    )


def get_mentee_dashboard_service(request: Request) -> Tuple[int, Dict[str, Any]]:
    """
    Get dashboard data for a mentee.
    """
    user = request.user
    
    from mentorship.serializers import (
        MenteeApplicationListSerializer,
        MentorshipRelationshipDetailSerializer,
        MentorshipSessionSerializer
    )
    
    # Get all applications
    all_applications = MenteeApplicationRepository.get_by_applicant(user)
    
    # Separate pending applications
    pending_applications = [app for app in all_applications if app.status == 'pending']
    
    # Get active mentorship relationships
    active_mentorships = MentorshipRelationshipRepository.get_active_by_mentee(user)
    
    # Get all sessions and upcoming sessions
    all_sessions = MentorshipSessionRepository.get_by_mentee(user)
    upcoming_sessions = MentorshipSessionRepository.get_upcoming(user, as_mentor=False)
    
    # Debug logging
    logger = logging.getLogger(__name__)
    logger.info(f"[MenteeDashboard] User: {user.id} ({user.first_name})")
    logger.info(f"[MenteeDashboard] Active Mentorships: {len(active_mentorships)}")
    logger.info(f"[MenteeDashboard] All Sessions: {len(all_sessions)}")
    logger.info(f"[MenteeDashboard] Upcoming Sessions: {len(upcoming_sessions)}")
    
    # Check relationships for this mentee
    for rel in active_mentorships:
        sessions_for_rel = rel.sessions.all()
        logger.info(f"[MenteeDashboard] Relationship {rel.id} with {rel.mentor.full_name}: {len(sessions_for_rel)} sessions")
    
    # Calculate stats
    completed_sessions = [s for s in all_sessions if s.status == 'completed']
    
    # Build active mentors list with detailed info
    active_mentors = []
    for relationship in active_mentorships:
        mentor = relationship.mentor
        active_mentors.append({
            'id': str(mentor.id),
            'relationship_id': str(relationship.id),
            'first_name': mentor.user.first_name,
            'last_name': mentor.user.last_name,
            'full_name': mentor.full_name,
            'bio': mentor.application.experience_description if mentor.application else None,
            'areas': [{'id': str(a.id), 'name': a.name} for a in mentor.areas.all()],
            'session_type': mentor.application.session_type if mentor.application else None,
            'sessions_completed': relationship.sessions_completed,
            'last_session_date': relationship.last_session_date,
            'next_session_date': relationship.next_session_date,
            'started_at': relationship.started_at,
            'area': {
                'id': str(relationship.area.id),
                'name': relationship.area.name
            }
        })
    
    return (
        status.HTTP_200_OK,
        {
            # Stats
            'active_mentors_count': len(active_mentors),
            'total_sessions': len(all_sessions),
            'sessions_attended': len(completed_sessions),
            'goals_achieved': 0,  # TODO: Implement goals tracking
            
            # Lists
            'active_mentors': active_mentors,
            'pending_applications': MenteeApplicationListSerializer(pending_applications, many=True).data,
            'all_applications': MenteeApplicationListSerializer(all_applications, many=True).data,
            'all_sessions': MentorshipSessionSerializer(all_sessions, many=True).data,
            'upcoming_sessions': MentorshipSessionSerializer(upcoming_sessions, many=True).data,
            
            # Legacy field for backwards compatibility
            'active_mentorships': MentorshipRelationshipDetailSerializer(active_mentorships, many=True).data,
        }
    )


# ===========================
# Area and Tag Services
# ===========================

def list_mentorship_areas_service() -> Tuple[int, Dict[str, Any]]:
    """
    List all active mentorship areas.
    """
    areas = MentorshipAreaRepository.get_with_mentor_count()
    
    from mentorship.serializers import MentorshipAreaSerializer
    serializer = MentorshipAreaSerializer(areas, many=True)
    
    return (status.HTTP_200_OK, {'areas': serializer.data})


def get_area_tags_service(area_id: UUID) -> Tuple[int, Dict[str, Any]]:
    """
    Get all tags for a specific area.
    """
    tags = SkillTagRepository.get_by_area(area_id)
    
    from mentorship.serializers import SkillTagSerializer
    serializer = SkillTagSerializer(tags, many=True)
    
    return (status.HTTP_200_OK, {'tags': serializer.data})
