from executives.views import (
    ExecutiveListView, 
    PastExecutiveListView, 
    ExecutiveByYearView,
    AvailableYearsView,
    CommitteeListView,
    CommitteeDetailView,
    CurrentAdministrationView,
    AppointeeListView,
    AppointeeByCommitteeView,
    AppointeeDetailView,
    AppointeeSocialLinksView,
    AppointeeSocialLinkDetailView,
)
from executives.permission_views_v2 import (
    list_all_permissions,
    get_available_permissions,
    grant_permissions,
    revoke_permissions,
    list_member_permissions,
    my_permissions,
    permission_audit_log,
)
from django.urls import path, re_path

urlpatterns = [
    # Executive routes
    path("", ExecutiveListView.as_view(), name="executives"),
    path("past/", PastExecutiveListView.as_view(), name="past-executives"),
    path("years/", AvailableYearsView.as_view(), name="available-years"),
    re_path(r"^year/(?P<year>[\w\-/]+)/$", ExecutiveByYearView.as_view(), name="executives-by-year"),
    
    # Current Administration route (executives + committees)
    path("current-administration/", CurrentAdministrationView.as_view(), name="current-administration"),
    
    # Committee routes
    path("committees/", CommitteeListView.as_view(), name="committees"),
    path("committees/<uuid:committee_id>/", CommitteeDetailView.as_view(), name="committee-detail"),
    
    # Appointee routes
    path("appointees/", AppointeeListView.as_view(), name="appointees"),
    path("appointees/committee/<uuid:committee_id>/", AppointeeByCommitteeView.as_view(), name="appointees-by-committee"),
    path("appointees/<uuid:appointee_id>/", AppointeeDetailView.as_view(), name="appointee-detail"),
    path("appointees/<uuid:appointee_id>/social-links/", AppointeeSocialLinksView.as_view(), name="appointee-social-links"),
    path("appointees/<uuid:appointee_id>/social-links/<int:link_id>/", AppointeeSocialLinkDetailView.as_view(), name="appointee-social-link-detail"),
    
    # Permission Management routes
    path("permissions/all/", list_all_permissions, name="list-all-permissions"),
    path("committees/<uuid:committee_id>/permissions/available/", get_available_permissions, name="available-permissions"),
    path("committees/<uuid:committee_id>/permissions/grant/", grant_permissions, name="grant-permissions"),
    path("committees/<uuid:committee_id>/permissions/revoke/", revoke_permissions, name="revoke-permissions"),
    path("committees/<uuid:committee_id>/permissions/member/<int:member_id>/", list_member_permissions, name="member-permissions"),
    path("committees/<uuid:committee_id>/permissions/my/", my_permissions, name="my-permissions"),
    path("committees/<uuid:committee_id>/permissions/audit/", permission_audit_log, name="permission-audit"),
]
