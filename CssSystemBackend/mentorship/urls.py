"""
Mentorship System - URL Configuration

API endpoints for the mentorship system.
"""

from django.urls import path
from mentorship.views import (
    # Area & Tag views
    MentorshipAreaListView,
    MentorshipAreaDetailView,
    AreaTagsListView,
    # Interviewer views
    InterviewerListView,
    InterviewerDetailView,
    # Mentor eligibility
    CheckMentorEligibilityView,
    # Mentor application views
    MentorApplicationCreateView,
    MentorApplicationDetailView,
    UserMentorApplicationsView,
    ScheduleInterviewView,
    # Interviewer action views
    InterviewerApplicationsView,
    InterviewerActionView,
    # Approved mentor views
    ApprovedMentorListView,
    ApprovedMentorDetailView,
    # Mentee application views
    CheckMenteeApplicationEligibilityView,
    MenteeApplicationCreateView,
    UserMenteeApplicationsView,
    MenteeApplicationDetailView,
    MenteeApplicationWithdrawView,
    # Mentor response views
    MentorPendingApplicationsView,
    MentorRespondToMenteeView,
    # Relationship views
    UserMentorshipsView,
    MentorshipRelationshipDetailView,
    # Session views
    CreateSessionView,
    SessionDetailView,
    CompleteSessionView,
    SessionReviewView,
    # Dashboard views
    MentorDashboardView,
    MenteeDashboardView,
    # Admin schedule management
    CreateInterviewerScheduleView,
    BulkCreateSchedulesView,
    # Donation views
    CheckMentorRelationshipView,
    DonateTOMentorView,
    MentorWalletInfoView,
    # Payment views
    InitiateMentorPaymentView,
    VerifyMentorPaymentView,
    MentorEarningsView,
    MenteePaymentHistoryView,
    MentorPaymentListView,
)

app_name = "mentorship"

urlpatterns = [
    # ===========================
    # Mentorship Areas & Tags
    # ===========================
    path(
        "areas/",
        MentorshipAreaListView.as_view(),
        name="area-list",
    ),
    path(
        "areas/<uuid:area_id>/",
        MentorshipAreaDetailView.as_view(),
        name="area-detail",
    ),
    path(
        "areas/<uuid:area_id>/tags/",
        AreaTagsListView.as_view(),
        name="area-tags",
    ),
    
    # ===========================
    # Interviewers (for mentor applicants)
    # ===========================
    path(
        "interviewers/",
        InterviewerListView.as_view(),
        name="interviewer-list",
    ),
    path(
        "interviewers/<uuid:interviewer_id>/",
        InterviewerDetailView.as_view(),
        name="interviewer-detail",
    ),
    
    # ===========================
    # Mentor Eligibility
    # ===========================
    path(
        "mentor/eligibility/",
        CheckMentorEligibilityView.as_view(),
        name="mentor-eligibility",
    ),
    
    # ===========================
    # Mentor Applications
    # ===========================
    path(
        "mentor/apply/",
        MentorApplicationCreateView.as_view(),
        name="mentor-apply",
    ),
    path(
        "mentor/applications/",
        UserMentorApplicationsView.as_view(),
        name="mentor-applications",
    ),
    path(
        "mentor/applications/<uuid:application_id>/",
        MentorApplicationDetailView.as_view(),
        name="mentor-application-detail",
    ),
    path(
        "mentor/applications/<uuid:application_id>/schedule-interview/",
        ScheduleInterviewView.as_view(),
        name="schedule-interview",
    ),
    
    # ===========================
    # Interviewer Actions (Admin/Staff)
    # ===========================
    path(
        "interviewer/applications/",
        InterviewerApplicationsView.as_view(),
        name="interviewer-applications",
    ),
    path(
        "interviewer/applications/<uuid:application_id>/action/",
        InterviewerActionView.as_view(),
        name="interviewer-action",
    ),
    
    # ===========================
    # Approved Mentors (Discovery)
    # ===========================
    path(
        "mentors/",
        ApprovedMentorListView.as_view(),
        name="mentor-list",
    ),
    path(
        "mentors/<uuid:mentor_id>/",
        ApprovedMentorDetailView.as_view(),
        name="mentor-detail",
    ),
    path(
        "mentors/<uuid:mentor_id>/relationship/",
        CheckMentorRelationshipView.as_view(),
        name="mentor-relationship-check",
    ),
    path(
        "mentors/<uuid:mentor_id>/donate/",
        DonateTOMentorView.as_view(),
        name="mentor-donate",
    ),
    
    # ===========================
    # Mentee Applications
    # ===========================
    path(
        "mentee/eligibility/<uuid:mentor_id>/",
        CheckMenteeApplicationEligibilityView.as_view(),
        name="mentee-eligibility-check",
    ),
    path(
        "mentee/apply/",
        MenteeApplicationCreateView.as_view(),
        name="mentee-apply",
    ),
    path(
        "mentee/applications/",
        UserMenteeApplicationsView.as_view(),
        name="mentee-applications",
    ),
    path(
        "mentee/applications/<uuid:application_id>/",
        MenteeApplicationDetailView.as_view(),
        name="mentee-application-detail",
    ),
    path(
        "mentee/applications/<uuid:application_id>/withdraw/",
        MenteeApplicationWithdrawView.as_view(),
        name="mentee-application-withdraw",
    ),
    
    # ===========================
    # Mentor Response to Mentee Applications
    # ===========================
    path(
        "mentor/pending-mentees/",
        MentorPendingApplicationsView.as_view(),
        name="mentor-pending-mentees",
    ),
    path(
        "mentor/mentee-applications/<uuid:application_id>/respond/",
        MentorRespondToMenteeView.as_view(),
        name="mentor-respond-to-mentee",
    ),
    
    # ===========================
    # Mentorship Relationships
    # ===========================
    path(
        "relationships/",
        UserMentorshipsView.as_view(),
        name="user-mentorships",
    ),
    path(
        "relationships/<uuid:relationship_id>/",
        MentorshipRelationshipDetailView.as_view(),
        name="relationship-detail",
    ),
    
    # ===========================
    # Sessions
    # ===========================
    path(
        "sessions/create/",
        CreateSessionView.as_view(),
        name="create-session",
    ),
    path(
        "sessions/<uuid:session_id>/",
        SessionDetailView.as_view(),
        name="session-detail",
    ),
    path(
        "sessions/<uuid:session_id>/complete/",
        CompleteSessionView.as_view(),
        name="complete-session",
    ),
    path(
        "sessions/<uuid:session_id>/review/",
        SessionReviewView.as_view(),
        name="session-review",
    ),
    
    # ===========================
    # Dashboards
    # ===========================
    path(
        "dashboard/mentor/",
        MentorDashboardView.as_view(),
        name="mentor-dashboard",
    ),
    path(
        "dashboard/mentee/",
        MenteeDashboardView.as_view(),
        name="mentee-dashboard",
    ),
    
    # ===========================
    # Admin Schedule Management
    # ===========================
    path(
        "admin/schedules/create/",
        CreateInterviewerScheduleView.as_view(),
        name="admin-create-schedule",
    ),
    path(
        "admin/schedules/bulk-create/",
        BulkCreateSchedulesView.as_view(),
        name="admin-bulk-create-schedules",
    ),
    
    # ===========================
    # Wallet & Donations
    # ===========================
    path(
        "wallet/info/",
        MentorWalletInfoView.as_view(),
        name="wallet-info",
    ),
    
    # ===========================
    # Payments (Integrated with payment system)
    # ===========================
    path(
        "payments/initiate/",
        InitiateMentorPaymentView.as_view(),
        name="payment-initiate",
    ),
    path(
        "payments/verify/",
        VerifyMentorPaymentView.as_view(),
        name="payment-verify",
    ),
    path(
        "payments/earnings/",
        MentorEarningsView.as_view(),
        name="payment-earnings",
    ),
    path(
        "payments/history/",
        MenteePaymentHistoryView.as_view(),
        name="payment-history",
    ),
    path(
        "payments/mentor/",
        MentorPaymentListView.as_view(),
        name="payment-mentor-list",
    ),
]
