from django.shortcuts import render
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView, Response
from rest_framework.permissions import IsAuthenticated

from timetable_system.serializers import ExaminationScheduleSerializer, ClassScheduleSerializer
from timetable_system.services import (
    get_exam_schedules_service,
    get_class_schedules_service,
    get_combined_timetable_service,
    get_past_exam_schedules_service
)


class GetExamSchedules(ListAPIView):
    """
    Get personalized exam schedules for the authenticated user.
    Automatically filters by user's year and shows upcoming + recent exams.
    """
    serializer_class = ExaminationScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = get_exam_schedules_service
        status, context = service(request, {"exams": self.serializer_class})
        return Response(status=status, data=context)


class GetClassSchedules(ListAPIView):
    """
    Get personalized class schedules for the authenticated user.
    Automatically filters by:
    - Academic year
    - Program (CS/IT)
    - Year (1-4)
    - Group (G1/G2)
    - Current semester
    """
    serializer_class = ClassScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = get_class_schedules_service
        status, context = service(request, {"class_schedules": self.serializer_class})
        return Response(status=status, data=context)


class GetPastExamSchedules(ListAPIView):
    """
    Get past exam schedules for the authenticated user.
    Shows only exams that have already occurred (past dates).
    """
    serializer_class = ExaminationScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = get_past_exam_schedules_service
        status, context = service(request, {"exams": self.serializer_class})
        return Response(status=status, data=context)


class GetCombinedTimetable(APIView):
    """
    Get combined timetable with both class schedules and exam schedules.
    This is the main endpoint for the comprehensive Timetable page.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = get_combined_timetable_service
        status, context = service(
            request, 
            {
                "class_schedules": ClassScheduleSerializer,
                "exams": ExaminationScheduleSerializer
            }
        )
        return Response(status=status, data=context)
