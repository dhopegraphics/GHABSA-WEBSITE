from django.urls import path
from faculty.views import StaffListView

urlpatterns = [
    path('staff/', StaffListView.as_view(), name='staff-list'),
]
