"""
Mentorship System - Serializers

Comprehensive serializers for all mentorship models:
- MentorshipArea & SkillTag
- Interviewer & Schedule
- Mentor Application (with full details)
- Mentee Application
- Mentorship Relationships
"""

from rest_framework import serializers
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    Serializer,
    CharField,
    UUIDField,
    BooleanField,
    DecimalField,
    ListField,
    DateField,
    TimeField,
)
from django.utils import timezone
from mentorship.models import (
    MentorshipArea,
    SkillTag,
    Interviewer,
    InterviewerSchedule,
    MentorApplication,
    ApprovedMentor,
    MenteeApplication,
    MentorshipRelationship,
    MentorshipSession,
    MentorPayment,
)
from accounts.serializers import AccountProfileSerializer


# ===========================
# Mentorship Area Serializers
# ===========================

class SkillTagSerializer(ModelSerializer):
    """Serializer for skill tags"""
    area_name = SerializerMethodField()
    
    class Meta:
        model = SkillTag
        fields = ['id', 'name', 'description', 'area', 'area_name', 'is_active']
        read_only_fields = ['id']
    
    def get_area_name(self, obj):
        return obj.area.name


class SkillTagMinimalSerializer(ModelSerializer):
    """Minimal serializer for listing tags"""
    
    class Meta:
        model = SkillTag
        fields = ['id', 'name']


class MentorshipAreaSerializer(ModelSerializer):
    """Serializer for mentorship areas"""
    tags = SkillTagSerializer(many=True, read_only=True)
    mentor_count = SerializerMethodField()
    
    class Meta:
        model = MentorshipArea
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'color',
            'is_active', 'order', 'tags', 'mentor_count'
        ]
        read_only_fields = ['id', 'slug']
    
    def get_mentor_count(self, obj):
        return obj.approved_mentors.filter(is_active=True).count()


class MentorshipAreaListSerializer(ModelSerializer):
    """Lightweight serializer for listing areas"""
    tag_count = SerializerMethodField()
    mentor_count = SerializerMethodField()
    
    class Meta:
        model = MentorshipArea
        fields = ['id', 'name', 'slug', 'icon', 'color', 'tag_count', 'mentor_count']
    
    def get_tag_count(self, obj):
        return obj.tags.filter(is_active=True).count()
    
    def get_mentor_count(self, obj):
        return obj.approved_mentors.filter(is_active=True).count()


# ===========================
# Interviewer Serializers
# ===========================

class InterviewerScheduleSerializer(ModelSerializer):
    """Serializer for interviewer schedules"""
    is_available = SerializerMethodField()
    duration_minutes = SerializerMethodField()
    interview_type_display = SerializerMethodField()
    
    class Meta:
        model = InterviewerSchedule
        fields = [
            'id', 'date', 'start_time', 'end_time', 'interview_type',
            'interview_type_display', 'location', 'meeting_link',
            'is_booked', 'is_active', 'is_available', 'duration_minutes', 'notes'
        ]
        read_only_fields = ['id', 'is_booked']
    
    def get_is_available(self, obj):
        return obj.is_available
    
    def get_duration_minutes(self, obj):
        return obj.duration_minutes
    
    def get_interview_type_display(self, obj):
        return obj.get_interview_type_display()


class InterviewerSerializer(ModelSerializer):
    """Serializer for interviewers"""
    full_name = SerializerMethodField()
    phone = SerializerMethodField()
    email = SerializerMethodField()
    areas = MentorshipAreaListSerializer(many=True, read_only=True)
    schedules = SerializerMethodField()
    available_schedule_count = SerializerMethodField()
    
    class Meta:
        model = Interviewer
        fields = [
            'id', 'full_name', 'phone', 'email', 'bio', 'profile_image',
            'areas', 'max_daily_interviews', 'is_active',
            'schedules', 'available_schedule_count'
        ]
        read_only_fields = ['id']
    
    def get_full_name(self, obj):
        return obj.full_name
    
    def get_phone(self, obj):
        return str(obj.user.phone)
    
    def get_email(self, obj):
        return obj.user.personal_email or obj.user.student_email
    
    def get_schedules(self, obj):
        # Only return future, available schedules
        future_schedules = obj.schedules.filter(
            date__gte=timezone.now().date(),
            is_active=True,
            is_booked=False
        ).order_by('date', 'start_time')
        return InterviewerScheduleSerializer(future_schedules, many=True).data
    
    def get_available_schedule_count(self, obj):
        return obj.schedules.filter(
            date__gte=timezone.now().date(),
            is_active=True,
            is_booked=False
        ).count()


class InterviewerListSerializer(ModelSerializer):
    """Minimal serializer for listing interviewers"""
    full_name = SerializerMethodField()
    areas = SerializerMethodField()
    available_schedule_count = SerializerMethodField()
    
    class Meta:
        model = Interviewer
        fields = ['id', 'full_name', 'profile_image', 'areas', 'available_schedule_count', 'is_active']
    
    def get_full_name(self, obj):
        return obj.full_name
    
    def get_areas(self, obj):
        return [{'id': a.id, 'name': a.name} for a in obj.areas.all()[:3]]
    
    def get_available_schedule_count(self, obj):
        return obj.schedules.filter(
            date__gte=timezone.now().date(),
            is_active=True,
            is_booked=False
        ).count()


# ===========================
# Mentor Application Serializers
# ===========================

class MentorApplicationCreateSerializer(ModelSerializer):
    """Serializer for creating mentor applications"""
    areas = serializers.PrimaryKeyRelatedField(
        queryset=MentorshipArea.objects.filter(is_active=True),
        many=True
    )
    skills = serializers.PrimaryKeyRelatedField(
        queryset=SkillTag.objects.filter(is_active=True),
        many=True,
        required=False
    )
    available_days = ListField(
        child=CharField(),
        required=True
    )
    incentive_preferences = ListField(
        child=CharField(),
        required=True
    )
    # Interview schedule selection
    selected_schedule_id = UUIDField(required=False, allow_null=True)
    
    class Meta:
        model = MentorApplication
        fields = [
            'areas', 'skills', 'additional_skills', 'experience_description',
            'incentive_preferences', 'session_type', 'available_days',
            'sessions_per_semester', 'available_time_start', 'available_time_end',
            'mentee_capacity', 'needs_classroom', 'needs_data_support', 'other_resources',
            'selected_schedule_id'
        ]
    
    def validate(self, attrs):
        # Check if user is eligible (not first year)
        request = self.context.get('request')
        if request and request.user:
            if request.user.get_year() == 1:
                raise serializers.ValidationError({
                    'eligibility': 'First-year students are not eligible to apply as mentors. '
                                   'You can apply starting from your second year.'
                })
        return attrs
    
    def validate_available_days(self, value):
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in value:
            if day.lower() not in valid_days:
                raise serializers.ValidationError(f"Invalid day: {day}")
        return [d.lower() for d in value]
    
    def validate_incentive_preferences(self, value):
        valid_incentives = ['certification', 'publication', 'food_refreshments', 'monetary', 'recognition', 'none']
        for incentive in value:
            if incentive not in valid_incentives:
                raise serializers.ValidationError(f"Invalid incentive: {incentive}")
        return value
    
    def validate_selected_schedule_id(self, value):
        if value:
            try:
                schedule = InterviewerSchedule.objects.get(id=value)
                if not schedule.is_available:
                    raise serializers.ValidationError("This interview slot is no longer available.")
            except InterviewerSchedule.DoesNotExist:
                raise serializers.ValidationError("Invalid interview schedule selected.")
        return value
    
    def create(self, validated_data):
        areas = validated_data.pop('areas', [])
        skills = validated_data.pop('skills', [])
        schedule_id = validated_data.pop('selected_schedule_id', None)
        
        request = self.context.get('request')
        validated_data['applicant'] = request.user
        validated_data['status'] = 'submitted'
        validated_data['submitted_at'] = timezone.now()
        
        application = MentorApplication.objects.create(**validated_data)
        application.areas.set(areas)
        application.skills.set(skills)
        
        # Handle interview scheduling if schedule was selected
        if schedule_id:
            try:
                schedule = InterviewerSchedule.objects.get(id=schedule_id)
                if schedule.is_available:
                    application.schedule_interview(schedule)
            except InterviewerSchedule.DoesNotExist:
                pass  # Schedule not found, continue without scheduling
        
        return application


class MentorApplicationDetailSerializer(ModelSerializer):
    """Detailed serializer for viewing mentor applications"""
    applicant = AccountProfileSerializer(read_only=True)
    areas = MentorshipAreaListSerializer(many=True, read_only=True)
    skills = SkillTagMinimalSerializer(many=True, read_only=True)
    assigned_interviewer = InterviewerListSerializer(read_only=True)
    interview_schedule_details = SerializerMethodField()
    status_display = SerializerMethodField()
    session_type_display = SerializerMethodField()
    mentee_capacity_display = SerializerMethodField()
    is_eligible = SerializerMethodField()
    
    class Meta:
        model = MentorApplication
        fields = [
            'id', 'applicant', 'status', 'status_display',
            'areas', 'skills', 'additional_skills', 'experience_description',
            'incentive_preferences', 'session_type', 'session_type_display',
            'available_days', 'sessions_per_semester', 'available_time_start', 'available_time_end',
            'mentee_capacity', 'mentee_capacity_display',
            'needs_classroom', 'needs_data_support', 'other_resources',
            'assigned_interviewer', 'interview_schedule_details', 'interview_link',
            'interview_notes', 'interview_completed_at',
            'approval_notes', 'approved_at', 'rejection_reason', 'rejected_at',
            'is_eligible', 'submitted_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'applicant', 'status', 'created_at', 'updated_at']
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_session_type_display(self, obj):
        return obj.get_session_type_display()
    
    def get_mentee_capacity_display(self, obj):
        return obj.get_mentee_capacity_display()
    
    def get_interview_schedule_details(self, obj):
        if obj.interview_schedule:
            return InterviewerScheduleSerializer(obj.interview_schedule).data
        return None
    
    def get_is_eligible(self, obj):
        return obj.is_eligible


class MentorApplicationListSerializer(ModelSerializer):
    """Minimal serializer for listing applications"""
    applicant_name = SerializerMethodField()
    areas = SerializerMethodField()
    status_display = SerializerMethodField()
    interview_date = SerializerMethodField()
    interview_details = SerializerMethodField()
    assigned_interviewer_name = SerializerMethodField()
    
    class Meta:
        model = MentorApplication
        fields = [
            'id', 'applicant_name', 'areas', 'status', 'status_display',
            'interview_date', 'interview_details', 'assigned_interviewer_name',
            'interview_link', 'experience_description', 'rejection_reason',
            'created_at'
        ]
    
    def get_applicant_name(self, obj):
        return f"{obj.applicant.first_name} {obj.applicant.last_name}"
    
    def get_areas(self, obj):
        return [{'id': str(a.id), 'name': a.name} for a in obj.areas.all()[:3]]
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_interview_date(self, obj):
        if obj.interview_schedule:
            return str(obj.interview_schedule.date)
        return None
    
    def get_interview_details(self, obj):
        """Return full interview schedule details"""
        if obj.interview_schedule:
            schedule = obj.interview_schedule
            return {
                'id': str(schedule.id),
                'date': str(schedule.date),
                'start_time': str(schedule.start_time)[:5] if schedule.start_time else None,
                'end_time': str(schedule.end_time)[:5] if schedule.end_time else None,
                'interview_type': schedule.interview_type,
                'interview_type_display': schedule.get_interview_type_display(),
                'location': schedule.location,
                'meeting_link': schedule.meeting_link,
                'notes': schedule.notes,
            }
        return None
    
    def get_assigned_interviewer_name(self, obj):
        if obj.assigned_interviewer:
            return obj.assigned_interviewer.full_name
        return None


class ScheduleInterviewSerializer(Serializer):
    """Serializer for scheduling an interview"""
    schedule_id = UUIDField()
    
    def validate_schedule_id(self, value):
        try:
            schedule = InterviewerSchedule.objects.get(id=value)
            if not schedule.is_available:
                raise serializers.ValidationError("This interview slot is not available.")
            return value
        except InterviewerSchedule.DoesNotExist:
            raise serializers.ValidationError("Schedule not found.")


class InterviewApprovalSerializer(Serializer):
    """Serializer for approving/rejecting mentor applications"""
    action = CharField()  # 'approve' or 'reject'
    notes = CharField(required=False, allow_blank=True)
    interview_link = CharField(required=False, allow_blank=True)
    
    def validate_action(self, value):
        if value not in ['approve', 'reject', 'complete_interview', 'send_link']:
            raise serializers.ValidationError("Invalid action. Must be 'approve', 'reject', 'complete_interview', or 'send_link'.")
        return value


# ===========================
# Approved Mentor Serializers
# ===========================

class ApprovedMentorDetailSerializer(ModelSerializer):
    """Detailed serializer for approved mentors (for mentees to view)"""
    user = AccountProfileSerializer(read_only=True)
    areas = MentorshipAreaListSerializer(many=True, read_only=True)
    skills = SkillTagMinimalSerializer(many=True, read_only=True)
    session_type = SerializerMethodField()
    session_type_display = SerializerMethodField()
    available_days = SerializerMethodField()
    available_time_start = SerializerMethodField()
    available_time_end = SerializerMethodField()
    mentee_capacity = SerializerMethodField()
    available_slots = SerializerMethodField()
    has_available_slots = SerializerMethodField()
    incentive_preferences = SerializerMethodField()
    needs_classroom = SerializerMethodField()
    needs_data_support = SerializerMethodField()
    
    class Meta:
        model = ApprovedMentor
        fields = [
            'id', 'user', 'areas', 'skills', 'is_active', 'is_accepting_mentees',
            'session_type', 'session_type_display', 'available_days',
            'available_time_start', 'available_time_end', 'mentee_capacity',
            'available_slots', 'has_available_slots', 'incentive_preferences',
            'needs_classroom', 'needs_data_support',
            'total_mentees', 'current_mentees', 'completed_sessions',
            'average_rating', 'total_ratings', 'created_at'
        ]
    
    def get_session_type(self, obj):
        return obj.application.session_type
    
    def get_session_type_display(self, obj):
        return obj.application.get_session_type_display()
    
    def get_available_days(self, obj):
        return obj.application.available_days
    
    def get_available_time_start(self, obj):
        return obj.application.available_time_start
    
    def get_available_time_end(self, obj):
        return obj.application.available_time_end
    
    def get_mentee_capacity(self, obj):
        return obj.application.mentee_capacity
    
    def get_available_slots(self, obj):
        return obj.available_slots
    
    def get_has_available_slots(self, obj):
        return obj.has_available_slots
    
    def get_incentive_preferences(self, obj):
        return obj.application.incentive_preferences
    
    def get_needs_classroom(self, obj):
        return obj.application.needs_classroom
    
    def get_needs_data_support(self, obj):
        return obj.application.needs_data_support


class ApprovedMentorListSerializer(ModelSerializer):
    """List serializer for mentors"""
    user = AccountProfileSerializer(read_only=True)
    full_name = SerializerMethodField()
    profile_image = SerializerMethodField()
    areas = SerializerMethodField()
    skills = SerializerMethodField()
    session_type = SerializerMethodField()
    available_slots = SerializerMethodField()
    has_available_slots = SerializerMethodField()
    year = SerializerMethodField()  # Changed from level to year
    programme = SerializerMethodField()
    bio = SerializerMethodField()
    
    class Meta:
        model = ApprovedMentor
        fields = [
            'id', 'user', 'full_name', 'profile_image', 'areas', 'skills',
            'session_type', 'available_slots', 'has_available_slots',
            'average_rating', 'total_ratings', 'is_accepting_mentees',
            'year', 'programme', 'bio'  # Changed from level to year
        ]
    
    def get_full_name(self, obj):
        return obj.full_name
    
    def get_profile_image(self, obj):
        # Return user profile image if exists
        return None  # Can be extended if profile images are added
    
    def get_areas(self, obj):
        return [{'id': a.id, 'name': a.name, 'color': a.color} for a in obj.areas.all()[:3]]
    
    def get_skills(self, obj):
        return [{'id': s.id, 'name': s.name} for s in obj.skills.all()[:5]]
    
    def get_session_type(self, obj):
        return obj.application.session_type
    
    def get_available_slots(self, obj):
        return obj.available_slots
    
    def get_has_available_slots(self, obj):
        return obj.has_available_slots
    
    def get_year(self, obj):
        """Return the mentor's current year (1-4). KNUST uses Year not Level."""
        return obj.user.get_year() if hasattr(obj.user, 'get_year') else None
    
    def get_programme(self, obj):
        return obj.user.programme if hasattr(obj.user, 'programme') else None
    
    def get_bio(self, obj):
        return obj.application.experience_description if obj.application else None


# ===========================
# Mentee Application Serializers
# ===========================

class MenteeApplicationCreateSerializer(ModelSerializer):
    """Serializer for creating mentee applications"""
    mentor = serializers.PrimaryKeyRelatedField(
        queryset=ApprovedMentor.objects.filter(is_active=True, is_accepting_mentees=True)
    )
    area = serializers.PrimaryKeyRelatedField(
        queryset=MentorshipArea.objects.filter(is_active=True)
    )
    current_skills = serializers.PrimaryKeyRelatedField(
        queryset=SkillTag.objects.filter(is_active=True),
        many=True,
        required=False
    )
    skills_to_learn = serializers.PrimaryKeyRelatedField(
        queryset=SkillTag.objects.filter(is_active=True),
        many=True,
        required=False
    )
    
    class Meta:
        model = MenteeApplication
        fields = [
            'mentor', 'area', 'current_skills', 'skills_description',
            'skills_to_learn', 'learning_goals',
            'offering_type', 'offering_description', 'offering_amount',
            'message'
        ]
    
    def validate(self, attrs):
        from mentorship.models import MentorshipRelationship
        
        mentor = attrs.get('mentor')
        area = attrs.get('area')
        request = self.context.get('request')
        
        if not request or not request.user:
            raise serializers.ValidationError({
                'non_field_errors': 'Authentication required.'
            })
        
        user = request.user
        
        # Check if mentor is accepting mentees
        if not mentor.has_available_slots:
            raise serializers.ValidationError({
                'mentor': 'This mentor has no available slots.'
            })
        
        # Check if area is in mentor's areas
        if area not in mentor.areas.all():
            raise serializers.ValidationError({
                'area': 'This mentor does not mentor in this area.'
            })
        
        # RULE 1: Check if mentee has an ACTIVE relationship with ANY mentor
        active_relationship = MentorshipRelationship.objects.filter(
            mentee=user,
            status='active'
        ).first()
        
        if active_relationship:
            raise serializers.ValidationError({
                'non_field_errors': f'You already have an active mentorship with {active_relationship.mentor.full_name}. '
                                   f'You can only have one active mentorship at a time. '
                                   f'Complete or end your current mentorship before applying to another mentor.'
            })
        
        # RULE 2: Check if mentee has already applied to this mentor for this area (pending/accepted)
        existing_application = MenteeApplication.objects.filter(
            applicant=user,
            mentor=mentor,
            area=area,
            status__in=['pending', 'accepted']
        ).exists()
        
        if existing_application:
            raise serializers.ValidationError({
                'area': 'You have already applied to this mentor for this area and your application is pending or accepted.'
            })
        
        # RULE 3: Check if mentee has EVER had a relationship with this mentor for this area
        past_relationship = MentorshipRelationship.objects.filter(
            mentee=user,
            mentor=mentor,
            area=area
        ).exists()
        
        if past_relationship:
            raise serializers.ValidationError({
                'area': f'You have already been mentored by {mentor.full_name} in {area.name}. '
                       f'You cannot apply to the same mentor for the same area again. '
                       f'Try applying for a different area if available.'
            })
        
        return attrs
    
    def create(self, validated_data):
        current_skills = validated_data.pop('current_skills', [])
        skills_to_learn = validated_data.pop('skills_to_learn', [])
        
        request = self.context.get('request')
        validated_data['applicant'] = request.user
        
        application = MenteeApplication.objects.create(**validated_data)
        application.current_skills.set(current_skills)
        application.skills_to_learn.set(skills_to_learn)
        
        return application


class MenteeApplicationDetailSerializer(ModelSerializer):
    """Detailed serializer for mentee applications"""
    applicant = AccountProfileSerializer(read_only=True)
    mentor = ApprovedMentorListSerializer(read_only=True)
    area = MentorshipAreaListSerializer(read_only=True)
    current_skills = SkillTagMinimalSerializer(many=True, read_only=True)
    skills_to_learn = SkillTagMinimalSerializer(many=True, read_only=True)
    status_display = SerializerMethodField()
    offering_type_display = SerializerMethodField()
    
    class Meta:
        model = MenteeApplication
        fields = [
            'id', 'applicant', 'mentor', 'area', 'status', 'status_display',
            'current_skills', 'skills_description', 'skills_to_learn', 'learning_goals',
            'offering_type', 'offering_type_display', 'offering_description', 'offering_amount',
            'message', 'mentor_response', 'responded_at', 'created_at', 'updated_at'
        ]
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_offering_type_display(self, obj):
        return obj.get_offering_type_display()


class MenteeApplicationListSerializer(ModelSerializer):
    """Minimal serializer for listing mentee applications"""
    applicant_name = SerializerMethodField()
    mentor = SerializerMethodField()
    area = SerializerMethodField()
    status_display = SerializerMethodField()
    
    class Meta:
        model = MenteeApplication
        fields = [
            'id', 'applicant_name', 'mentor', 'area',
            'message', 'learning_goals', 'skills_description',
            'offering_type', 'offering_description', 'offering_amount',
            'status', 'status_display', 'created_at'
        ]
    
    def get_applicant_name(self, obj):
        return f"{obj.applicant.first_name} {obj.applicant.last_name}"
    
    def get_mentor(self, obj):
        mentor = obj.mentor
        return {
            'id': str(mentor.id),
            'first_name': mentor.user.first_name,
            'last_name': mentor.user.last_name,
            'full_name': mentor.full_name,
            'areas': [{'id': str(a.id), 'name': a.name} for a in mentor.areas.all()],
            'session_type': mentor.application.session_type if mentor.application else None,
        }
    
    def get_area(self, obj):
        return {
            'id': str(obj.area.id),
            'name': obj.area.name,
            'color': obj.area.color if hasattr(obj.area, 'color') else '#3B82F6'
        }
    
    def get_status_display(self, obj):
        return obj.get_status_display()


class MenteeApplicationResponseSerializer(Serializer):
    """Serializer for mentor responding to mentee applications"""
    action = CharField()  # 'accept' or 'reject'
    response_message = CharField(required=False, allow_blank=True)
    
    def validate_action(self, value):
        if value not in ['accept', 'reject']:
            raise serializers.ValidationError("Invalid action. Must be 'accept' or 'reject'.")
        return value


# ===========================
# Mentorship Relationship Serializers
# ===========================

class MentorshipRelationshipDetailSerializer(ModelSerializer):
    """Detailed serializer for mentorship relationships"""
    mentor = ApprovedMentorListSerializer(read_only=True)
    mentee = AccountProfileSerializer(read_only=True)
    area = MentorshipAreaListSerializer(read_only=True)
    status_display = SerializerMethodField()
    
    class Meta:
        model = MentorshipRelationship
        fields = [
            'id', 'mentor', 'mentee', 'area', 'status', 'status_display',
            'sessions_completed', 'last_session_date', 'next_session_date',
            'started_at', 'completed_at', 'updated_at'
        ]
    
    def get_status_display(self, obj):
        return obj.get_status_display()


class MentorshipRelationshipListSerializer(ModelSerializer):
    """Minimal serializer for listing relationships"""
    mentor_name = SerializerMethodField()
    mentee_name = SerializerMethodField()
    mentee = SerializerMethodField()
    area_name = SerializerMethodField()
    status_display = SerializerMethodField()
    
    class Meta:
        model = MentorshipRelationship
        fields = [
            'id', 'mentor_name', 'mentee_name', 'mentee', 'area_name',
            'status', 'status_display', 'sessions_completed', 'started_at'
        ]
    
    def get_mentor_name(self, obj):
        return obj.mentor.full_name
    
    def get_mentee_name(self, obj):
        return f"{obj.mentee.first_name} {obj.mentee.last_name}"
    
    def get_mentee(self, obj):
        """Return mentee details for display"""
        mentee = obj.mentee
        return {
            'id': str(mentee.id),
            'first_name': mentee.first_name,
            'last_name': mentee.last_name,
            'year': mentee.get_year() if hasattr(mentee, 'get_year') else None,
            'programme': mentee.get_program_display_name() if hasattr(mentee, 'get_program_display_name') else None,
            'personal_email': mentee.personal_email,
            'student_email': mentee.student_email,
        }
    
    def get_area_name(self, obj):
        return obj.area.name
    
    def get_status_display(self, obj):
        return obj.get_status_display()


# ===========================
# Mentorship Session Serializers
# ===========================

class MentorshipSessionSerializer(ModelSerializer):
    """Serializer for mentorship sessions"""
    session_type_display = SerializerMethodField()
    status_display = SerializerMethodField()
    mentor = SerializerMethodField()
    mentee = SerializerMethodField()
    scheduled_date = SerializerMethodField()
    scheduled_time = SerializerMethodField()
    title = SerializerMethodField()
    
    class Meta:
        model = MentorshipSession
        fields = [
            'id', 'relationship', 'date', 'start_time', 'end_time',
            'session_type', 'session_type_display', 'location', 'meeting_link',
            'status', 'status_display', 'agenda', 'mentor_notes',
            'mentee_feedback', 'rating', 'created_at',
            'mentor', 'mentee', 'scheduled_date', 'scheduled_time', 'title'
        ]
    
    def get_session_type_display(self, obj):
        return obj.get_session_type_display()
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_mentor(self, obj):
        mentor = obj.relationship.mentor
        return {
            'id': str(mentor.id),
            'first_name': mentor.user.first_name,
            'last_name': mentor.user.last_name,
            'full_name': mentor.full_name
        }
    
    def get_mentee(self, obj):
        mentee = obj.relationship.mentee
        return {
            'id': str(mentee.id),
            'first_name': mentee.first_name,
            'last_name': mentee.last_name,
            'full_name': f"{mentee.first_name} {mentee.last_name}"
        }
    
    def get_scheduled_date(self, obj):
        """Format date as a readable string"""
        if obj.date:
            return obj.date.strftime('%b %d, %Y')
        return None
    
    def get_scheduled_time(self, obj):
        """Format time as a readable string"""
        if obj.start_time:
            return obj.start_time.strftime('%I:%M %p')
        return None
    
    def get_title(self, obj):
        """Generate a title for the session"""
        area_name = obj.relationship.area.name if obj.relationship.area else 'General'
        return f"{area_name} Session"


class CreateSessionSerializer(ModelSerializer):
    """Serializer for creating sessions"""
    
    class Meta:
        model = MentorshipSession
        fields = [
            'relationship', 'date', 'start_time', 'end_time',
            'session_type', 'location', 'meeting_link', 'agenda'
        ]


class CompleteSessionSerializer(Serializer):
    """Serializer for completing a session (mentor only)"""
    mentor_notes = CharField(required=False, allow_blank=True)


class SessionReviewSerializer(Serializer):
    """Serializer for mentee's session review"""
    feedback = CharField(required=False, allow_blank=True)
    rating = serializers.IntegerField(required=True, min_value=1, max_value=5)


# ===========================
# Payment Serializers
# ===========================

class MentorPaymentSerializer(ModelSerializer):
    """Serializer for mentor payments"""
    mentor_name = SerializerMethodField()
    mentee_name = SerializerMethodField()
    payment_type_display = SerializerMethodField()
    status_display = SerializerMethodField()
    transaction_status = SerializerMethodField()
    is_paid = SerializerMethodField()
    
    class Meta:
        model = MentorPayment
        fields = [
            'id', 'mentor', 'mentor_name', 'mentee', 'mentee_name',
            'relationship', 'amount', 'payment_type', 'payment_type_display',
            'status', 'status_display', 'transaction', 'transaction_reference',
            'transaction_status', 'description', 'is_paid',
            'created_at', 'completed_at', 'updated_at'
        ]
        read_only_fields = ['id', 'transaction', 'transaction_reference', 'created_at', 'completed_at']
    
    def get_mentor_name(self, obj):
        return obj.mentor.full_name
    
    def get_mentee_name(self, obj):
        if obj.mentee:
            return f"{obj.mentee.first_name} {obj.mentee.last_name}"
        return None
    
    def get_payment_type_display(self, obj):
        return obj.get_payment_type_display()
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_transaction_status(self, obj):
        """Get the linked transaction status"""
        if obj.transaction:
            return obj.transaction.status
        return None
    
    def get_is_paid(self, obj):
        """Check if payment is completed"""
        return obj.is_paid


# ===========================
# Dashboard Serializers
# ===========================

class MentorDashboardSerializer(Serializer):
    """Serializer for mentor dashboard data"""
    application = MentorApplicationDetailSerializer()
    mentor_profile = ApprovedMentorDetailSerializer()
    pending_mentee_applications = MenteeApplicationListSerializer(many=True)
    active_mentees = MentorshipRelationshipListSerializer(many=True)
    upcoming_sessions = MentorshipSessionSerializer(many=True)
    total_earnings = DecimalField(max_digits=10, decimal_places=2)


class MenteeDashboardSerializer(Serializer):
    """Serializer for mentee dashboard data"""
    applications = MenteeApplicationListSerializer(many=True)
    active_mentorships = MentorshipRelationshipListSerializer(many=True)
    upcoming_sessions = MentorshipSessionSerializer(many=True)


class EligibilityCheckSerializer(Serializer):
    """Serializer for checking mentor eligibility"""
    is_eligible = BooleanField()
    current_year = serializers.IntegerField()
    message = CharField()
    has_pending_application = BooleanField()
    is_approved_mentor = BooleanField()
