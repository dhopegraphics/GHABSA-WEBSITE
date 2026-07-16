from django.urls import path
from academics.views import (
    GetAllCoursesView,
    GetCourseResourcesView,
    GetLecturerCoursesView,
    InternshipOpportunitiesListView,
)

urlpatterns = [
    path(
        "courses/",
        GetAllCoursesView.as_view(),
        name="all_courses",
    ),
    path(
        "courses/<course_id>/",
        GetCourseResourcesView.as_view(),
        name="get-resources",
    ),
    path(
        "lecturers/<lecturer_id>/courses/",
        GetLecturerCoursesView.as_view(),
        name="lecturer-courses",
    ),
    path(
        "internships/",
        InternshipOpportunitiesListView.as_view(),
        name="internship_list",
    ),
]
