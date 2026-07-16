from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework import serializers
from django.utils import timezone
from academics.models import (
    Course,
    Lecturer,
    AcademicSlides,
    OnlineTutorialTips,
    PastQuestions,
    InternshipOpportunities,
)
from utils.cloudinary_utils import get_avatar_url, get_card_image_url


class LecturerSerializer(ModelSerializer):
    """Serializer for Lecturer model"""

    profile_image = serializers.SerializerMethodField()
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Lecturer
        fields = [
            "lecturer_id",
            "title",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "office_location",
            "specialization",
            "bio",
            "profile_image",
            "is_active",
            "created_at",
            "last_updated",
        ]
        read_only_fields = ["lecturer_id", "created_at", "last_updated"]

    def get_profile_image(self, obj: Lecturer):
        # Prioritize URL over upload, apply optimization
        url = obj.profile_image_url if obj.profile_image_url else (obj.profile_image.url if obj.profile_image else None)
        return get_avatar_url(url, size=200)


class CourseSerializer(ModelSerializer):
    """Serializer for Course model with lecturer details"""

    lecturer = LecturerSerializer(read_only=True)
    lecturer_id = serializers.PrimaryKeyRelatedField(
        queryset=Lecturer.objects.all(),
        source="lecturer",
        write_only=True,
        required=False,
        allow_null=True,
    )
    semester_display = serializers.CharField(source="get_semester_display", read_only=True)
    program_display = serializers.CharField(source="get_program_display", read_only=True)
    lecturer_name = serializers.CharField(read_only=True)
    prerequisites = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Course.objects.all(), required=False
    )
    
    # Add resource counts
    slides_count = serializers.SerializerMethodField()
    past_questions_count = serializers.SerializerMethodField()
    online_tutorial_tips_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "course_id",
            "course_code",
            "course_name",
            "year",
            "semester",
            "semester_display",
            "program",
            "program_display",
            "credit_hours",
            "description",
            "lecturer",
            "lecturer_id",
            "lecturer_name",
            "prerequisites",
            "slides_count",
            "past_questions_count",
            "online_tutorial_tips_count",
            "created_at",
            "last_updated",
        ]
        read_only_fields = ["course_id", "created_at", "last_updated"]
    
    def get_slides_count(self, obj):
        """Get the count of slides for this course - uses annotated value if available"""
        # Use annotated count from repository to avoid N+1 query
        if hasattr(obj, '_slides_count'):
            return obj._slides_count
        return obj.slides.filter(approved=True).count()
    
    def get_past_questions_count(self, obj):
        """Get the count of past questions for this course - uses annotated value if available"""
        if hasattr(obj, '_past_questions_count'):
            return obj._past_questions_count
        return obj.past_questions.filter(approved=True).count()
    
    def get_online_tutorial_tips_count(self, obj):
        """Get the count of online tutorial tips for this course - uses annotated value if available"""
        if hasattr(obj, '_online_tips_count'):
            return obj._online_tips_count
        return obj.online_tips.filter(approved=True).count()


class SlidesSerializer(ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = AcademicSlides
        fields = "__all__"

    def get_file(self, obj: OnlineTutorialTips):
        # Prioritize URL over upload
        if obj.file_url:
            return obj.file_url
        if obj.file:
            return obj.file.url
        return None


class InternshipOpportunitiesSerializer(ModelSerializer):
    image = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = InternshipOpportunities
        fields = [
            "internship_id",
            "campany_name",
            "image",
            "description",
            "registration_link",
            "application_deadline",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_image(self, obj: InternshipOpportunities):
        # Prioritize URL over upload, apply optimization
        url = obj.image_url if obj.image_url else (obj.image.url if obj.image else None)
        return get_card_image_url(url, width=400)

    def get_is_active(self, obj: InternshipOpportunities):
        """
        Determine if internship is still accepting applications
        - True: Deadline hasn't passed yet (or no deadline set)
        - False: Deadline has passed
        """
        if not obj.application_deadline:
            return True  # No deadline means it's still active
        
        return timezone.now() < obj.application_deadline


class OnlineTutorialTipsSerializer(ModelSerializer):
    class Meta:
        model = OnlineTutorialTips
        fields = "__all__"


class PastQuestionsSerializer(ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = PastQuestions
        fields = "__all__"

    def get_file(self, obj):
        # Prioritize URL over upload
        if obj.file_url:
            return obj.file_url
        if obj.file:
            return obj.file.url
        return None


class CourseResourceSerializer(Serializer):
    # slides = SlidesSerializer()
    online_tutorila_tips = OnlineTutorialTips()
    past_questions = PastQuestionsSerializer()
