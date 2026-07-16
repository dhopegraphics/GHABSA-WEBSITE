"""
Mentorship System - Views

API views for the mentorship system.
Provides endpoints for:
- Mentorship areas and tags
- Mentor applications and interviews
- Mentee applications
- Mentor discovery
- Mentorship relationships
- Sessions and dashboards
"""

from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    CreateAPIView,
    RetrieveAPIView,
)
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.request import Request

from mentorship.serializers import (
    # Area & Tag serializers
    MentorshipAreaSerializer,
    MentorshipAreaListSerializer,
    SkillTagSerializer,
    # Interviewer serializers
    InterviewerSerializer,
    InterviewerListSerializer,
    InterviewerScheduleSerializer,
    # Mentor application serializers
    MentorApplicationCreateSerializer,
    MentorApplicationDetailSerializer,
    MentorApplicationListSerializer,
    ScheduleInterviewSerializer,
    InterviewApprovalSerializer,
    # Approved mentor serializers
    ApprovedMentorDetailSerializer,
    ApprovedMentorListSerializer,
    # Mentee application serializers
    MenteeApplicationCreateSerializer,
    MenteeApplicationDetailSerializer,
    MenteeApplicationListSerializer,
    MenteeApplicationResponseSerializer,
    # Relationship serializers
    MentorshipRelationshipDetailSerializer,
    MentorshipRelationshipListSerializer,
    # Session serializers
    MentorshipSessionSerializer,
    CreateSessionSerializer,
    CompleteSessionSerializer,
    # Dashboard serializers
    EligibilityCheckSerializer,
)
from mentorship.services import (
    # Eligibility
    check_mentor_eligibility,
    # Mentor applications
    create_mentor_application_service,
    get_mentor_application_service,
    get_user_mentor_applications_service,
    schedule_interview_service,
    # Interviewer services
    get_interviewers_list_service,
    interviewer_action_service,
    get_interviewer_applications_service,
    # Mentee applications
    create_mentee_application_service,
    get_mentee_applications_service,
    mentor_respond_to_mentee_service,
    get_mentor_pending_applications_service,
    # Mentor discovery
    list_approved_mentors_service,
    get_mentor_detail_service,
    # Relationships
    get_user_mentorships_service,
    # Sessions
    create_session_service,
    complete_session_service,
    # Dashboards
    get_mentor_dashboard_service,
    get_mentee_dashboard_service,
    # Areas & Tags
    list_mentorship_areas_service,
    get_area_tags_service,
)


# ===========================
# Mentorship Area Views
# ===========================

class MentorshipAreaListView(APIView):
    """
    List all active mentorship areas.
    No authentication required.
    """
    
    def get(self, request):
        status_code, data = list_mentorship_areas_service()
        return Response(data, status=status_code)


class MentorshipAreaDetailView(APIView):
    """
    Get details of a specific mentorship area including its tags.
    """
    
    def get(self, request, area_id):
        from mentorship.repository import MentorshipAreaRepository
        area = MentorshipAreaRepository.get_by_id(area_id)
        
        if not area:
            return Response(
                {'status': 'error', 'message': 'Area not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = MentorshipAreaSerializer(area)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AreaTagsListView(APIView):
    """
    Get all skill tags for a specific area.
    """
    
    def get(self, request, area_id):
        status_code, data = get_area_tags_service(area_id)
        return Response(data, status=status_code)


# ===========================
# Interviewer Views
# ===========================

class InterviewerListView(APIView):
    """
    List all active interviewers with their available schedules.
    Used by mentor applicants to select an interviewer.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        area_id = request.query_params.get('area_id', None)
        status_code, data = get_interviewers_list_service(area_id)
        return Response(data, status=status_code)


class InterviewerDetailView(APIView):
    """
    Get detailed information about an interviewer.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, interviewer_id):
        from mentorship.repository import InterviewerRepository
        interviewer = InterviewerRepository.get_by_id(interviewer_id)
        
        if not interviewer:
            return Response(
                {'status': 'error', 'message': 'Interviewer not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = InterviewerSerializer(interviewer)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ===========================
# Mentor Eligibility View
# ===========================

class CheckMentorEligibilityView(APIView):
    """
    Check if the current user is eligible to apply as a mentor.
    Returns eligibility status and reason.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        eligibility = check_mentor_eligibility(request.user)
        serializer = EligibilityCheckSerializer(eligibility)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ===========================
# Mentor Application Views
# ===========================

class MentorApplicationCreateView(CreateAPIView):
    """
    Submit a new mentor application.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MentorApplicationCreateSerializer
    
    def post(self, request):
        status_code, data = create_mentor_application_service(
            request, MentorApplicationCreateSerializer
        )
        return Response(data, status=status_code)


class MentorApplicationDetailView(APIView):
    """
    Get details of a specific mentor application.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, application_id):
        status_code, data = get_mentor_application_service(request, application_id)
        return Response(data, status=status_code)


class UserMentorApplicationsView(APIView):
    """
    Get all mentor applications for the current user.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        status_code, data = get_user_mentor_applications_service(request)
        return Response(data, status=status_code)


class ScheduleInterviewView(APIView):
    """
    Schedule an interview for a mentor application.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ScheduleInterviewSerializer
    
    def post(self, request, application_id):
        serializer = ScheduleInterviewSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        schedule_id = serializer.validated_data['schedule_id']
        status_code, data = schedule_interview_service(request, application_id, schedule_id)
        return Response(data, status=status_code)


# ===========================
# Interviewer Action Views (Admin Dashboard)
# ===========================

class InterviewerApplicationsView(APIView):
    """
    Get all applications assigned to the current interviewer.
    Staff/Interviewer only.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        status_code, data = get_interviewer_applications_service(request)
        return Response(data, status=status_code)


class InterviewerActionView(APIView):
    """
    Interviewer actions: approve, reject, complete_interview, send_link
    """
    permission_classes = [IsAuthenticated]
    serializer_class = InterviewApprovalSerializer
    
    def post(self, request, application_id):
        serializer = InterviewApprovalSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')
        interview_link = serializer.validated_data.get('interview_link', '')
        
        status_code, data = interviewer_action_service(
            request, application_id, action, notes, interview_link
        )
        return Response(data, status=status_code)


# ===========================
# Approved Mentor Views (Discovery)
# ===========================

class ApprovedMentorListView(APIView):
    """
    List approved mentors for mentees to discover.
    Supports filtering by area and search.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        area_id = request.query_params.get('area_id', None)
        search_query = request.query_params.get('search', None)
        
        status_code, data = list_approved_mentors_service(area_id, search_query)
        return Response(data, status=status_code)


class ApprovedMentorDetailView(APIView):
    """
    Get detailed information about an approved mentor.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, mentor_id):
        status_code, data = get_mentor_detail_service(mentor_id)
        return Response(data, status=status_code)


# ===========================
# Mentee Application Views
# ===========================

class CheckMenteeApplicationEligibilityView(APIView):
    """
    Check if the current user can apply to a specific mentor.
    Returns eligibility status for each of the mentor's areas.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, mentor_id):
        from mentorship.models import MentorshipRelationship, MenteeApplication
        from mentorship.repository import ApprovedMentorRepository
        
        user = request.user
        mentor = ApprovedMentorRepository.get_by_id(mentor_id)
        
        if not mentor:
            return Response(
                {'status': 'error', 'message': 'Mentor not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user has an active relationship with ANY mentor
        active_relationship = MentorshipRelationship.objects.filter(
            mentee=user,
            status='active'
        ).select_related('mentor', 'area').first()
        
        if active_relationship:
            return Response({
                'can_apply': False,
                'reason': 'active_mentorship',
                'message': f'You already have an active mentorship with {active_relationship.mentor.full_name} in {active_relationship.area.name}. '
                          f'You can only have one active mentorship at a time.',
                'active_mentor': {
                    'id': str(active_relationship.mentor.id),
                    'name': active_relationship.mentor.full_name,
                    'area': active_relationship.area.name
                },
                'areas': []
            }, status=status.HTTP_200_OK)
        
        # Check each of the mentor's areas for eligibility
        areas_eligibility = []
        
        for area in mentor.areas.all():
            area_status = {
                'id': str(area.id),
                'name': area.name,
                'color': area.color,
                'can_apply': True,
                'reason': None
            }
            
            # Check for pending/accepted application for this area
            pending_application = MenteeApplication.objects.filter(
                applicant=user,
                mentor=mentor,
                area=area,
                status__in=['pending', 'accepted']
            ).first()
            
            if pending_application:
                area_status['can_apply'] = False
                area_status['reason'] = 'pending_application'
                area_status['message'] = f'You already have a {"pending" if pending_application.status == "pending" else "accepted"} application for this area.'
            else:
                # Check for past relationship with this mentor+area
                past_relationship = MentorshipRelationship.objects.filter(
                    mentee=user,
                    mentor=mentor,
                    area=area
                ).first()
                
                if past_relationship:
                    area_status['can_apply'] = False
                    area_status['reason'] = 'past_mentorship'
                    area_status['message'] = f'You were already mentored by {mentor.full_name} in {area.name}.'
            
            areas_eligibility.append(area_status)
        
        # Check if there's at least one area the user can apply to
        can_apply_to_any = any(a['can_apply'] for a in areas_eligibility)
        
        return Response({
            'can_apply': can_apply_to_any,
            'reason': None if can_apply_to_any else 'no_available_areas',
            'message': None if can_apply_to_any else 'You cannot apply to this mentor for any area.',
            'mentor_has_slots': mentor.has_available_slots,
            'areas': areas_eligibility
        }, status=status.HTTP_200_OK)


class MenteeApplicationCreateView(CreateAPIView):
    """
    Submit a new mentee application to a mentor.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MenteeApplicationCreateSerializer
    
    def post(self, request):
        status_code, data = create_mentee_application_service(
            request, MenteeApplicationCreateSerializer
        )
        return Response(data, status=status_code)


class UserMenteeApplicationsView(APIView):
    """
    Get all mentee applications for the current user.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        status_code, data = get_mentee_applications_service(request)
        return Response(data, status=status_code)


class MenteeApplicationDetailView(APIView):
    """
    Get details of a specific mentee application.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, application_id):
        from mentorship.repository import MenteeApplicationRepository
        application = MenteeApplicationRepository.get_by_id(application_id)
        
        if not application:
            return Response(
                {'status': 'error', 'message': 'Application not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission (applicant, mentor, or staff)
        if (application.applicant != request.user and 
            application.mentor.user != request.user and 
            not request.user.is_staff):
            return Response(
                {'status': 'error', 'message': 'You do not have permission to view this application.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MenteeApplicationDetailSerializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MenteeApplicationWithdrawView(APIView):
    """
    Withdraw a pending mentee application.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, application_id):
        from mentorship.repository import MenteeApplicationRepository
        application = MenteeApplicationRepository.get_by_id(application_id)
        
        if not application:
            return Response(
                {'status': 'error', 'message': 'Application not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if application.applicant != request.user:
            return Response(
                {'status': 'error', 'message': 'You can only withdraw your own applications.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if application.status != 'pending':
            return Response(
                {'status': 'error', 'message': f'Cannot withdraw. Application is already {application.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.withdraw()
        
        return Response(
            {'status': 'success', 'message': 'Application withdrawn successfully.'},
            status=status.HTTP_200_OK
        )


# ===========================
# Mentor Response to Mentee Views
# ===========================

class MentorPendingApplicationsView(APIView):
    """
    Get pending mentee applications for the current mentor.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        status_code, data = get_mentor_pending_applications_service(request)
        return Response(data, status=status_code)


class MentorRespondToMenteeView(APIView):
    """
    Mentor accepts or rejects a mentee application.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MenteeApplicationResponseSerializer
    
    def post(self, request, application_id):
        serializer = MenteeApplicationResponseSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action = serializer.validated_data['action']
        response_message = serializer.validated_data.get('response_message', '')
        
        status_code, data = mentor_respond_to_mentee_service(
            request, application_id, action, response_message
        )
        return Response(data, status=status_code)


# ===========================
# Mentorship Relationship Views
# ===========================

class UserMentorshipsView(APIView):
    """
    Get all mentorship relationships for the current user.
    Returns relationships as both mentor and mentee.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        status_code, data = get_user_mentorships_service(request)
        return Response(data, status=status_code)


class MentorshipRelationshipDetailView(APIView):
    """
    Get details of a specific mentorship relationship.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, relationship_id):
        from mentorship.repository import MentorshipRelationshipRepository
        relationship = MentorshipRelationshipRepository.get_by_id(relationship_id)
        
        if not relationship:
            return Response(
                {'status': 'error', 'message': 'Relationship not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission
        if (relationship.mentor.user != request.user and 
            relationship.mentee != request.user and 
            not request.user.is_staff):
            return Response(
                {'status': 'error', 'message': 'You do not have permission to view this relationship.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MentorshipRelationshipDetailSerializer(relationship)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ===========================
# Session Views
# ===========================

class CreateSessionView(CreateAPIView):
    """
    Schedule a new mentorship session.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CreateSessionSerializer
    
    def post(self, request):
        status_code, data = create_session_service(request, CreateSessionSerializer)
        return Response(data, status=status_code)


class SessionDetailView(APIView):
    """
    Get details of a specific session.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, session_id):
        from mentorship.repository import MentorshipSessionRepository
        session = MentorshipSessionRepository.get_by_id(session_id)
        
        if not session:
            return Response(
                {'status': 'error', 'message': 'Session not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission
        if (session.relationship.mentor.user != request.user and 
            session.relationship.mentee != request.user and 
            not request.user.is_staff):
            return Response(
                {'status': 'error', 'message': 'You do not have permission to view this session.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MentorshipSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompleteSessionView(APIView):
    """
    Mark a session as completed (mentor only).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CompleteSessionSerializer
    
    def post(self, request, session_id):
        serializer = CompleteSessionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        mentor_notes = serializer.validated_data.get('mentor_notes', '')
        
        status_code, data = complete_session_service(
            request, session_id, mentor_notes
        )
        return Response(data, status=status_code)


class SessionReviewView(APIView):
    """
    Add mentee's feedback and rating to a completed session (mentee only).
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        from mentorship.serializers import SessionReviewSerializer
        from mentorship.services import add_session_review_service
        
        serializer = SessionReviewSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        feedback = serializer.validated_data.get('feedback', '')
        rating = serializer.validated_data.get('rating')
        
        status_code, data = add_session_review_service(
            request, session_id, feedback, rating
        )
        return Response(data, status=status_code)


# ===========================
# Dashboard Views
# ===========================

class MentorDashboardView(APIView):
    """
    Get mentor dashboard data.
    Shows application status, pending mentee applications, active mentees, etc.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        status_code, data = get_mentor_dashboard_service(request)
        return Response(data, status=status_code)


class MenteeDashboardView(APIView):
    """
    Get mentee dashboard data.
    Shows applications, active mentorships, upcoming sessions.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        status_code, data = get_mentee_dashboard_service(request)
        return Response(data, status=status_code)


# ===========================
# Admin Schedule Management Views
# ===========================

class CreateInterviewerScheduleView(CreateAPIView):
    """
    Create interviewer schedules.
    Staff/Admin only.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = InterviewerScheduleSerializer
    
    def post(self, request):
        serializer = InterviewerScheduleSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'status': 'success', 'message': 'Schedule created successfully.', 'data': serializer.data},
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            {'status': 'error', 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class BulkCreateSchedulesView(APIView):
    """
    Create multiple interviewer schedules at once.
    Staff/Admin only.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request):
        schedules_data = request.data.get('schedules', [])
        
        if not schedules_data:
            return Response(
                {'status': 'error', 'message': 'No schedules provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created = []
        errors = []
        
        for schedule_data in schedules_data:
            serializer = InterviewerScheduleSerializer(data=schedule_data)
            if serializer.is_valid():
                serializer.save()
                created.append(serializer.data)
            else:
                errors.append({
                    'data': schedule_data,
                    'errors': serializer.errors
                })
        
        return Response({
            'status': 'success' if not errors else 'partial',
            'created_count': len(created),
            'error_count': len(errors),
            'created': created,
            'errors': errors
        }, status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST)


# ===========================
# Donation Views
# ===========================

class CheckMentorRelationshipView(APIView):
    """
    Check if current user has a relationship with a mentor.
    Also returns mentor's wallet info for donation eligibility.
    
    GET /mentorship/mentors/<mentor_id>/relationship/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, mentor_id):
        from mentorship.payment_services import MentorWalletService
        from mentorship.models import ApprovedMentor
        
        try:
            mentor = ApprovedMentor.objects.get(id=mentor_id, is_active=True)
        except ApprovedMentor.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Mentor not found or not active'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check relationship
        relationship_info = MentorWalletService.check_mentee_mentor_relationship(
            mentee=request.user,
            mentor=mentor
        )
        
        return Response({
            'status': 'success',
            'data': {
                'mentor_id': str(mentor.id),
                'mentor_name': mentor.full_name,
                **relationship_info
            }
        }, status=status.HTTP_200_OK)


class DonateTOMentorView(APIView):
    """
    Create a donation to a mentor.
    
    POST /mentorship/mentors/<mentor_id>/donate/
    
    Request body:
    {
        "amount": "50.00",
        "message": "Thank you for your guidance!",
        "callback_url": "https://example.com/payment/callback"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, mentor_id):
        from mentorship.payment_services import MentorDonationService
        from mentorship.models import ApprovedMentor
        from decimal import Decimal
        
        try:
            mentor = ApprovedMentor.objects.get(id=mentor_id, is_active=True)
        except ApprovedMentor.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Mentor not found or not active'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prevent donating to self
        if mentor.user == request.user:
            return Response(
                {'status': 'error', 'message': 'You cannot donate to yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        amount = request.data.get('amount')
        message = request.data.get('message', '')
        callback_url = request.data.get('callback_url', '')
        
        if not amount:
            return Response(
                {'status': 'error', 'message': 'amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, TypeError) as e:
            return Response(
                {'status': 'error', 'message': f'Invalid amount: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = MentorDonationService.create_donation(
                donor=request.user,
                mentor=mentor,
                amount=amount,
                message=message,
                callback_url=callback_url,
            )
            
            return Response({
                'status': 'success',
                'message': 'Donation initiated successfully',
                'data': {
                    'payment_id': str(result['mentor_payment'].id),
                    'reference': result['reference'],
                    'authorization_url': result['authorization_url'],
                    'access_code': result.get('access_code'),
                    'amount': str(amount),
                    'mentor_name': mentor.full_name,
                }
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class MentorWalletInfoView(APIView):
    """
    Get mentor's wallet information (for mentor themselves).
    
    GET /mentorship/wallet/info/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from mentorship.payment_services import MentorWalletService, MentorDonationService
        from mentorship.models import ApprovedMentor
        
        try:
            mentor = ApprovedMentor.objects.get(user=request.user)
        except ApprovedMentor.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'You are not an approved mentor'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        wallet_info = MentorWalletService.get_mentor_wallet_info(mentor)
        donation_stats = MentorDonationService.get_mentor_donation_stats(mentor)
        
        return Response({
            'status': 'success',
            'data': {
                **wallet_info,
                **donation_stats,
            }
        }, status=status.HTTP_200_OK)


# ===========================
# Payment Views
# ===========================

class InitiateMentorPaymentView(APIView):
    """
    Initiate a payment to a mentor.
    
    POST /mentorship/payments/initiate/
    
    Request body:
    {
        "mentor_id": "uuid",
        "amount": "100.00",
        "description": "Mentorship support",
        "callback_url": "https://example.com/callback",
        "relationship_id": "uuid" (optional)
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from mentorship.payment_services import MentorshipPaymentService
        from mentorship.models import ApprovedMentor, MentorshipRelationship
        from decimal import Decimal
        
        mentor_id = request.data.get('mentor_id')
        amount = request.data.get('amount')
        description = request.data.get('description', '')
        callback_url = request.data.get('callback_url', '')
        relationship_id = request.data.get('relationship_id')
        
        # Validate required fields
        if not mentor_id:
            return Response(
                {'status': 'error', 'message': 'mentor_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not amount:
            return Response(
                {'status': 'error', 'message': 'amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, TypeError) as e:
            return Response(
                {'status': 'error', 'message': f'Invalid amount: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get mentor
        try:
            mentor = ApprovedMentor.objects.get(id=mentor_id, is_active=True)
        except ApprovedMentor.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Mentor not found or not active'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get relationship if provided
        relationship = None
        if relationship_id:
            try:
                relationship = MentorshipRelationship.objects.get(
                    id=relationship_id,
                    mentee=request.user,
                    mentor=mentor
                )
            except MentorshipRelationship.DoesNotExist:
                pass
        
        try:
            result = MentorshipPaymentService.create_mentor_offering_payment(
                mentee=request.user,
                mentor=mentor,
                amount=amount,
                description=description,
                callback_url=callback_url,
                relationship=relationship,
            )
            
            return Response({
                'status': 'success',
                'message': 'Payment initiated successfully',
                'data': {
                    'payment_id': str(result['mentor_payment'].id),
                    'reference': result['reference'],
                    'authorization_url': result['authorization_url'],
                    'access_code': result.get('access_code'),
                }
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class VerifyMentorPaymentView(APIView):
    """
    Verify a mentor payment status.
    
    POST /mentorship/payments/verify/
    
    Request body:
    {
        "reference": "TXN-..."
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from mentorship.payment_services import MentorshipPaymentService
        from mentorship.serializers import MentorPaymentSerializer
        
        reference = request.data.get('reference')
        
        if not reference:
            return Response(
                {'status': 'error', 'message': 'reference is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            mentor_payment = MentorshipPaymentService.verify_and_sync_payment(reference)
            
            # Check ownership
            if mentor_payment.mentee != request.user:
                return Response(
                    {'status': 'error', 'message': 'Payment not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response({
                'status': 'success',
                'data': MentorPaymentSerializer(mentor_payment).data
            }, status=status.HTTP_200_OK)
        
        except ValueError as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class MentorEarningsView(APIView):
    """
    Get current user's mentor earnings.
    
    GET /mentorship/payments/earnings/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from mentorship.payment_services import MentorshipPaymentService
        from mentorship.models import ApprovedMentor
        
        try:
            mentor = ApprovedMentor.objects.get(user=request.user)
        except ApprovedMentor.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'You are not an approved mentor'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        earnings = MentorshipPaymentService.get_mentor_earnings(mentor)
        
        return Response({
            'status': 'success',
            'data': {
                'total_earnings': str(earnings['total_earnings']),
                'offerings_total': str(earnings['offerings_total']),
                'incentives_total': str(earnings['incentives_total']),
                'pending_amount': str(earnings['pending_amount']),
                'completed_count': earnings['completed_count'],
                'pending_count': earnings['pending_count'],
            }
        }, status=status.HTTP_200_OK)


class MenteePaymentHistoryView(APIView):
    """
    Get current user's payment history as a mentee.
    
    GET /mentorship/payments/history/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from mentorship.payment_services import MentorshipPaymentService
        from mentorship.serializers import MentorPaymentSerializer
        
        payment_data = MentorshipPaymentService.get_mentee_payments(request.user)
        
        return Response({
            'status': 'success',
            'data': {
                'total_paid': str(payment_data['total_paid']),
                'payment_count': payment_data['payment_count'],
                'payments': MentorPaymentSerializer(
                    payment_data['payments'], 
                    many=True
                ).data
            }
        }, status=status.HTTP_200_OK)


class MentorPaymentListView(APIView):
    """
    Get all payments for a mentor (mentor's view).
    
    GET /mentorship/payments/mentor/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from mentorship.models import ApprovedMentor, MentorPayment
        from mentorship.serializers import MentorPaymentSerializer
        
        try:
            mentor = ApprovedMentor.objects.get(user=request.user)
        except ApprovedMentor.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'You are not an approved mentor'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        payments = MentorPayment.objects.filter(
            mentor=mentor
        ).select_related('mentee', 'transaction', 'relationship').order_by('-created_at')
        
        # Filter by status if provided
        payment_status = request.query_params.get('status')
        if payment_status:
            payments = payments.filter(status=payment_status)
        
        return Response({
            'status': 'success',
            'data': MentorPaymentSerializer(payments, many=True).data
        }, status=status.HTTP_200_OK)

