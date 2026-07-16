from django.urls import path
from .views import (
    ProjectListView, 
    ProjectSubmissionView, 
    MyProjectsView, 
    ProjectDetailView,
    RequestUpdateView,
    CancelUpdateRequestView,
    CompleteUpdateView,
    get_available_years, 
    validate_image_url
)

urlpatterns = [
    path('', ProjectListView.as_view(), name='project-list'),
    path('submit/', ProjectSubmissionView.as_view(), name='project-submit'),
    path('my-projects/', MyProjectsView.as_view(), name='my-projects'),
    path('<uuid:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<uuid:pk>/request-update/', RequestUpdateView.as_view(), name='project-request-update'),
    path('<uuid:pk>/cancel-update/', CancelUpdateRequestView.as_view(), name='project-cancel-update'),
    path('<uuid:pk>/complete-update/', CompleteUpdateView.as_view(), name='project-complete-update'),
    path('years/', get_available_years, name='available-years'),
    path('validate-image/', validate_image_url, name='validate-image'),
]
