"""
URL configuration for Code Quest application
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from codequest import views, admin_views

# Router for ViewSets
router = DefaultRouter()
router.register(r'events', admin_views.CodeQuestEventViewSet, basename='codequest-event')

app_name = 'codequest'

urlpatterns = [
    # Router URLs (admin)
    path('', include(router.urls)),
    
    # ===============================
    # Public Event Info (FIRST ENDPOINT TO CALL)
    # ===============================
    path('active-event/', views.ActiveCodeQuestEventView.as_view(), name='active-event'),
    
    # ===============================
    # User Details (for pre-filling registration forms)
    # ===============================
    path('user/details/', views.CurrentUserDetailsView.as_view(), name='user-details'),
    
    # ===============================
    # Authentication Endpoints
    # ===============================
    path('portal/login/', views.PortalLoginView.as_view(), name='portal-login'),
    path('auth/student-login/', views.StudentLoginView.as_view(), name='student-login'),
    path('auth/consultant-login/', views.ConsultantLoginView.as_view(), name='consultant-login'),
    path('auth/facilitator-login/', views.FacilitatorLoginView.as_view(), name='facilitator-login'),
    
    # ===============================
    # Registration Endpoints
    # ===============================
    path('register/student/', views.StudentRegistrationView.as_view(), name='student-register'),
    path('register/consultant/', views.ConsultantRegistrationView.as_view(), name='consultant-register'),
    
    # ===============================
    # Student Portal Endpoints
    # ===============================
    path('participant/dashboard/', views.ParticipantDashboardView.as_view(), name='participant-dashboard'),
    path('student/my-group/', views.MyGroupView.as_view(), name='my-group'),
    path('student/my-project/', views.MyProjectView.as_view(), name='my-project'),
    
    # ===============================
    # PM Election Endpoints
    # ===============================
    path('pm-election/candidates/', views.PMCandidatesView.as_view(), name='pm-candidates'),
    path('pm-election/nominate/', views.NominatePMView.as_view(), name='pm-nominate'),
    path('pm-election/vote/', views.VotePMView.as_view(), name='pm-vote'),
    
    # ===============================
    # PM Actions Endpoints
    # ===============================
    path('pm/assign-role/', views.AssignRoleView.as_view(), name='assign-role'),
    path('pm/create-task/', views.CreateTaskView.as_view(), name='create-task'),
    path('pm/update-task/<int:task_id>/', views.UpdateTaskView.as_view(), name='update-task'),
    
    # ===============================
    # Project Management Endpoints
    # ===============================
    path('project/submit/', views.SubmitProjectView.as_view(), name='project-submit'),
    path('project/update/<int:project_id>/', views.UpdateProjectView.as_view(), name='project-update'),
    
    # ===============================
    # Consultant Portal Endpoints
    # ===============================
    path('consultant/my-groups/', views.ConsultantMyGroupsView.as_view(), name='consultant-my-groups'),
    path('consultant/group/<int:group_id>/', views.ConsultantGroupDetailView.as_view(), name='consultant-group-detail'),
    
    # ===============================
    # Scoring Endpoints (Facilitators)
    # ===============================
    path('scoring/projects/', views.ScoringProjectsListView.as_view(), name='scoring-projects'),
    path('scoring/criteria/', views.ScoringCriteriaView.as_view(), name='scoring-criteria'),
    path('scoring/submit/', views.SubmitScoreView.as_view(), name='scoring-submit'),
    path('scoring/my-scores/', views.FacilitatorMyScoresView.as_view(), name='facilitator-my-scores'),
    
    # ===============================
    # Results Endpoints
    # ===============================
    path('results/leaderboard/', views.LeaderboardView.as_view(), name='results-leaderboard'),
    path('results/my-score/', views.MyScoreView.as_view(), name='results-my-score'),
    path('results/breakdown/<int:project_id>/', views.ScoreBreakdownView.as_view(), name='results-breakdown'),
    
    # ===============================
    # Admin Management Endpoints
    # ===============================
    path('admin/group-students/', admin_views.GroupStudentsView.as_view(), name='admin-group-students'),
    path('admin/assign-consultants/', admin_views.AssignConsultantsView.as_view(), name='admin-assign-consultants'),
    path('admin/add-facilitator/', admin_views.AddFacilitatorView.as_view(), name='admin-add-facilitator'),
    path('admin/approve-project/<int:project_id>/', admin_views.ApproveProjectView.as_view(), name='admin-approve-project'),
    path('admin/calculate-scores/', admin_views.CalculateScoresView.as_view(), name='admin-calculate-scores'),
    path('admin/publish-results/', admin_views.PublishResultsView.as_view(), name='admin-publish-results'),
    path('admin/end-pm-election/', admin_views.EndPMElectionView.as_view(), name='admin-end-pm-election'),
    path('admin/analytics/', admin_views.EventAnalyticsView.as_view(), name='admin-analytics'),
    
    # ===============================
    # Self-Grouping Endpoints
    # ===============================
    path('self-grouping/status/', views.SelfGroupingStatusView.as_view(), name='self-grouping-status'),
    path('self-grouping/participants/', views.AvailableParticipantsView.as_view(), name='available-participants'),
    path('self-grouping/teams/', views.AvailableTeamsView.as_view(), name='available-teams'),
    path('self-grouping/create-team/', views.CreateTeamView.as_view(), name='create-team'),
    path('self-grouping/my-team/', views.MyTeamView.as_view(), name='my-team'),
    path('self-grouping/leave-team/', views.LeaveTeamView.as_view(), name='leave-team'),
    path('self-grouping/finalize/', views.FinalizeTeamView.as_view(), name='finalize-team'),
    
    # Invitations
    path('self-grouping/invitations/', views.MyInvitationsView.as_view(), name='my-invitations'),
    path('self-grouping/invite/', views.SendInvitationView.as_view(), name='send-invitation'),
    path('self-grouping/invite/<int:invitation_id>/cancel/', views.CancelInvitationView.as_view(), name='cancel-invitation'),
    path('self-grouping/invite/<int:invitation_id>/respond/', views.RespondToInvitationView.as_view(), name='respond-invitation'),
    
    # Join Requests
    path('self-grouping/join-requests/', views.MyJoinRequestsView.as_view(), name='my-join-requests'),
    path('self-grouping/request-join/', views.SendJoinRequestView.as_view(), name='send-join-request'),
    path('self-grouping/request/<int:request_id>/cancel/', views.CancelJoinRequestView.as_view(), name='cancel-join-request'),
    path('self-grouping/request/<int:request_id>/respond/', views.RespondToJoinRequestView.as_view(), name='respond-join-request'),
]
