from django.urls import path
from timetable_system.views import (
    GetExamSchedules,
    GetClassSchedules,
    GetCombinedTimetable,
    GetPastExamSchedules
)

urlpatterns = [
    path("schedules/", GetExamSchedules.as_view(), name="exam-schedules"),
    path("past-schedules/", GetPastExamSchedules.as_view(), name="past-exam-schedules"),
    path("class-schedules/", GetClassSchedules.as_view(), name="class-schedules"),
    path("timetable/", GetCombinedTimetable.as_view(), name="combined-timetable"),
]
