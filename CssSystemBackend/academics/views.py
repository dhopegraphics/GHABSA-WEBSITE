from django.shortcuts import render
from academics.serializers import (
    CourseSerializer,
    CourseResourceSerializer,
    OnlineTutorialTipsSerializer,
    PastQuestionsSerializer,
    SlidesSerializer,
    InternshipOpportunitiesSerializer,
)
from academics.repository import CourseRepository
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from academics.repository import (
    OnlineTutorialTipsRepository,
    SlidesRepository,
    PastQuestionsRepository,
    InternshipOpportunitiesRepository,
)
from rest_framework.response import Response

# Create your views here.


class GetAllCoursesView(ListAPIView):
    """
    Get courses - public access for browsing (with caching).
    
    Query Parameters:
        - program: Filter by program ('CS' for Computer Science, 'IT' for Information Technology)
                   If not provided, returns all courses.
    
    Examples:
        - /academics/courses/ - Returns all courses
        - /academics/courses/?program=CS - Returns only Computer Science courses
        - /academics/courses/?program=IT - Returns only Information Technology courses
    """
    permission_classes = [AllowAny]
    serializer_class = CourseSerializer
    
    def get_queryset(self):
        """Use repository method that includes caching and optimization"""
        program = self.request.query_params.get('program', None)
        
        if program and program.upper() in ['CS', 'IT']:
            return CourseRepository.get_by_program(program.upper())
        
        return CourseRepository.get_all()


class GetCourseResourcesView(RetrieveAPIView):
    """Get course resources - public access for educational content (with caching)"""
    permission_classes = [AllowAny]

    def get(self, request, course_id):
        # All repository methods now use caching
        # Get course details with lecturer information (cached)
        course = CourseRepository.get_by_id(course_id=course_id)
        
        if not course:
            return Response({"error": "Course not found"}, status=404)
        
        # Get course materials (all cached)
        online_tutorial_tips = OnlineTutorialTipsRepository.get_links(course_id=course_id)
        past_questions = PastQuestionsRepository.get_questions(course_id=course_id)
        slides = SlidesRepository.get_slides(course_id=course_id)

        data = {
            "course": CourseSerializer(course).data,
            "online_tutorial_tips": OnlineTutorialTipsSerializer(
                online_tutorial_tips, many=True
            ).data,
            "past_questions": PastQuestionsSerializer(past_questions, many=True).data,
            "slides": SlidesSerializer(slides, many=True).data,
        }
        return Response(data=data)


class InternshipOpportunitiesListView(ListAPIView):
    """Get all active internships - public access for career opportunities"""
    permission_classes = [AllowAny]
    serializer_class = InternshipOpportunitiesSerializer
    
    def get_queryset(self):
        """Use repository method for proper query execution per request"""
        return InternshipOpportunitiesRepository.get_active_internships()


class GetLecturerCoursesView(ListAPIView):
    """Get all courses taught by a specific lecturer - public access (with caching)"""
    permission_classes = [AllowAny]
    serializer_class = CourseSerializer
    
    def get(self, request, lecturer_id):
        # Uses cached repository method
        courses = CourseRepository.get_by_lecturer(lecturer_id=lecturer_id)
        data = self.serializer_class(courses, many=True).data
        return Response(data=data)
