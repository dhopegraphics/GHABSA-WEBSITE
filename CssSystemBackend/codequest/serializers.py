"""
Django REST Framework serializers for Code Quest models
"""
from rest_framework import serializers
from django.utils import timezone
from codequest.models import (
    CodeQuestEvent,
    CodeQuestParticipant,
    CodeQuestGroup,
    ProjectManagerCandidate,
    ProjectManagerVote,
    GroupMemberRole,
    CodeQuestProject,
    CodeQuestConsultant,
    ConsultantGroupAssignment,
    ScoringCriteria,
    CodeQuestFacilitator,
    ProjectScore,
    FinalProjectScore,
    ProjectTask,
)
from events.serializers import EventSerializer


# ========== PUBLIC EVENT SERIALIZER ==========

class ActiveCodeQuestEventSerializer(serializers.ModelSerializer):
    """
    Public serializer for active CodeQuest event
    Used on the frontend CodeQuest page to display event info
    """
    # Event details from the linked Event model
    event_name = serializers.CharField(source='event.event_name', read_only=True)
    event_description = serializers.CharField(source='event.description', read_only=True)
    event_image_1 = serializers.SerializerMethodField()
    event_image_2 = serializers.SerializerMethodField()
    venue = serializers.CharField(source='event.venue', read_only=True)
    building = serializers.CharField(source='event.building', read_only=True)
    organised_by = serializers.CharField(source='event.organised_by', read_only=True)
    
    # CodeQuest specific details
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    participant_count = serializers.SerializerMethodField()
    consultant_count = serializers.SerializerMethodField()
    
    # Computed fields
    is_registration_open = serializers.SerializerMethodField()
    registration_status = serializers.SerializerMethodField()
    days_until_presentation = serializers.SerializerMethodField()
    current_phase = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeQuestEvent
        fields = [
            'id', 'event_name', 'event_description', 'event_image_1', 'event_image_2',
            'venue', 'building', 'organised_by',
            'academic_year', 'semester', 'course_code', 'course_name',
            'registration_start_date', 'registration_end_date',
            'grouping_date', 'voting_start_date', 'voting_end_date',
            'project_submission_deadline', 'presentation_date',
            'venue_details', 'status', 'status_display',
            'participant_count', 'consultant_count',
            'is_registration_open', 'registration_status',
            'days_until_presentation', 'current_phase',
        ]
    
    def get_event_image_1(self, obj):
        if obj.event.event_image_1:
            return obj.event.event_image_1.url if hasattr(obj.event.event_image_1, 'url') else str(obj.event.event_image_1)
        return obj.event.event_image_1_url
    
    def get_event_image_2(self, obj):
        if obj.event.event_image_2:
            return obj.event.event_image_2.url if hasattr(obj.event.event_image_2, 'url') else str(obj.event.event_image_2)
        return obj.event.event_image_2_url
    
    def get_participant_count(self, obj):
        return obj.participants.count()
    
    def get_consultant_count(self, obj):
        return obj.consultants.filter(is_approved=True).count()
    
    def get_is_registration_open(self, obj):
        now = timezone.now()
        return (
            obj.status == 'registration_open' and
            obj.registration_start_date <= now <= obj.registration_end_date
        )
    
    def get_registration_status(self, obj):
        now = timezone.now()
        if obj.status == 'completed':
            return 'completed'
        if obj.status == 'draft':
            return 'coming_soon'
        if now < obj.registration_start_date:
            return 'not_started'
        if obj.registration_start_date <= now <= obj.registration_end_date:
            return 'open'
        return 'closed'
    
    def get_days_until_presentation(self, obj):
        now = timezone.now()
        if obj.presentation_date > now:
            delta = obj.presentation_date - now
            return delta.days
        return 0
    
    def get_current_phase(self, obj):
        """Return current phase based on dates and status"""
        now = timezone.now()
        
        if obj.status == 'completed':
            return {'phase': 'completed', 'label': 'Event Completed'}
        
        if obj.status == 'draft':
            return {'phase': 'upcoming', 'label': 'Coming Soon'}
        
        if now < obj.registration_start_date:
            return {'phase': 'pre_registration', 'label': 'Registration Opens Soon'}
        
        if obj.registration_start_date <= now <= obj.registration_end_date:
            return {'phase': 'registration', 'label': 'Registration Open'}
        
        if obj.registration_end_date < now < obj.grouping_date:
            return {'phase': 'pre_grouping', 'label': 'Registration Closed'}
        
        if obj.grouping_date <= now < obj.voting_start_date:
            return {'phase': 'grouping', 'label': 'Group Formation'}
        
        if obj.voting_start_date <= now <= obj.voting_end_date:
            return {'phase': 'voting', 'label': 'PM Election'}
        
        if obj.voting_end_date < now < obj.project_submission_deadline:
            return {'phase': 'development', 'label': 'Development Phase'}
        
        if obj.project_submission_deadline <= now < obj.presentation_date:
            return {'phase': 'submission', 'label': 'Final Submissions'}
        
        if now >= obj.presentation_date:
            return {'phase': 'presentation', 'label': 'Presentation Day'}
        
        return {'phase': 'unknown', 'label': obj.get_status_display()}


class CodeQuestEventSerializer(serializers.ModelSerializer):
    """Serializer for CodeQuestEvent model"""
    event = EventSerializer(read_only=True)
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('events.models', fromlist=['Event']).Event.objects.all(),
        source='event',
        write_only=True
    )
    participant_count = serializers.SerializerMethodField()
    group_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeQuestEvent
        fields = '__all__'
    
    def get_participant_count(self, obj):
        return obj.participants.count()
    
    def get_group_count(self, obj):
        return obj.groups.count()


class CodeQuestEventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for event listing"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CodeQuestEvent
        fields = ['id', 'academic_year', 'semester', 'course_name', 'status', 'status_display', 
                  'presentation_date', 'registration_start_date', 'registration_end_date']


class CodeQuestParticipantSerializer(serializers.ModelSerializer):
    """Serializer for CodeQuestParticipant model"""
    year_display = serializers.CharField(source='get_year_display', read_only=True)
    preferred_role_display = serializers.CharField(source='get_preferred_role_display', read_only=True)
    group_name = serializers.CharField(source='group.group_number', read_only=True)
    is_project_manager = serializers.SerializerMethodField()
    # User account info (read-only display fields)
    user_full_name = serializers.SerializerMethodField()
    user_student_id = serializers.CharField(source='user.student_id', read_only=True)
    
    class Meta:
        model = CodeQuestParticipant
        fields = '__all__'
        extra_kwargs = {
            'access_key': {'read_only': True},
            'group': {'read_only': True},
            'user': {'read_only': True},  # Auto-assigned from authenticated user
        }
    
    def get_is_project_manager(self, obj):
        return obj.managed_groups.exists()
    
    def get_user_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return None
    
    def validate(self, attrs):
        """
        Validate that:
        1. User hasn't already registered as participant for this event
        2. User hasn't registered as consultant for this event
        3. Student ID isn't already registered for this event
        """
        event = attrs.get('event')
        student_id = attrs.get('student_id')
        request = self.context.get('request')
        user = request.user if request else None
        
        if event and user:
            # Check if user already registered as participant
            existing_participant = CodeQuestParticipant.objects.filter(
                event=event, user=user
            ).first()
            if existing_participant:
                raise serializers.ValidationError({
                    'user': f'You have already registered as a participant for this event. Your access key is: {existing_participant.access_key}'
                })
            
            # Check if user already registered as consultant
            existing_consultant = CodeQuestConsultant.objects.filter(
                event=event, user=user
            ).first()
            if existing_consultant:
                raise serializers.ValidationError({
                    'user': 'You have already registered as a consultant for this event. You cannot register as both.'
                })
        
        if event and student_id:
            # Check if student_id already registered for this event (regardless of user)
            existing_by_student_id = CodeQuestParticipant.objects.filter(
                event=event, student_id=student_id
            ).first()
            if existing_by_student_id:
                raise serializers.ValidationError({
                    'student_id': f'This Student ID is already registered for this event.'
                })
            
            # Also check if student_id is registered as consultant
            existing_consultant_by_id = CodeQuestConsultant.objects.filter(
                event=event, student_id=student_id
            ).first()
            if existing_consultant_by_id:
                raise serializers.ValidationError({
                    'student_id': 'This Student ID is already registered as a consultant for this event.'
                })
        
        return attrs


class CodeQuestParticipantPublicSerializer(serializers.ModelSerializer):
    """Public serializer (hides sensitive data)"""
    year_display = serializers.CharField(source='get_year_display', read_only=True)
    preferred_role_display = serializers.CharField(source='get_preferred_role_display', read_only=True)
    
    class Meta:
        model = CodeQuestParticipant
        fields = ['id', 'student_id', 'student_name', 'year', 'year_display', 
                  'preferred_role', 'preferred_role_display', 'skills']


class CodeQuestGroupSerializer(serializers.ModelSerializer):
    """Serializer for CodeQuestGroup model"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    project_manager_name = serializers.CharField(source='project_manager.student_name', read_only=True)
    consultant_name = serializers.CharField(source='consultant.name', read_only=True)
    member_count = serializers.SerializerMethodField()
    members = CodeQuestParticipantPublicSerializer(many=True, read_only=True)
    
    class Meta:
        model = CodeQuestGroup
        fields = '__all__'
    
    def get_member_count(self, obj):
        return obj.members.count()


class CodeQuestGroupListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for group listing"""
    member_count = serializers.SerializerMethodField()
    project_manager_name = serializers.CharField(source='project_manager.student_name', read_only=True)
    has_project = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeQuestGroup
        fields = ['id', 'group_number', 'group_name', 'category', 'member_count', 
                  'project_manager_name', 'has_project', 'is_complete']
    
    def get_member_count(self, obj):
        return obj.members.count()
    
    def get_has_project(self, obj):
        return hasattr(obj, 'project')


class ProjectManagerCandidateSerializer(serializers.ModelSerializer):
    """Serializer for ProjectManagerCandidate model"""
    participant_name = serializers.CharField(source='participant.student_name', read_only=True)
    participant_id_number = serializers.CharField(source='participant.student_id', read_only=True)
    group_number = serializers.CharField(source='group.group_number', read_only=True)
    
    class Meta:
        model = ProjectManagerCandidate
        fields = '__all__'
        extra_kwargs = {
            'vote_count': {'read_only': True},
            'is_winner': {'read_only': True},
        }


class ProjectManagerVoteSerializer(serializers.ModelSerializer):
    """Serializer for ProjectManagerVote model"""
    voter_name = serializers.CharField(source='voter.student_name', read_only=True)
    candidate_name = serializers.CharField(source='candidate.participant.student_name', read_only=True)
    
    class Meta:
        model = ProjectManagerVote
        fields = '__all__'
        extra_kwargs = {
            'vote_date': {'read_only': True},
        }


class GroupMemberRoleSerializer(serializers.ModelSerializer):
    """Serializer for GroupMemberRole model"""
    participant_name = serializers.CharField(source='participant.student_name', read_only=True)
    role_display = serializers.CharField(source='get_role_type_display', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.student_name', read_only=True)
    
    class Meta:
        model = GroupMemberRole
        fields = '__all__'
        extra_kwargs = {
            'assigned_date': {'read_only': True},
        }


class CodeQuestProjectSerializer(serializers.ModelSerializer):
    """Serializer for CodeQuestProject model"""
    group_number = serializers.CharField(source='group.group_number', read_only=True)
    group_details = CodeQuestGroupListSerializer(source='group', read_only=True)
    app_logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeQuestProject
        fields = '__all__'
        extra_kwargs = {
            'is_approved': {'read_only': True},
            'admin_feedback': {'read_only': True},
        }
    
    def get_app_logo_url(self, obj):
        # Prioritize URL over upload
        if obj.app_logo_url:
            return obj.app_logo_url
        if obj.app_logo:
            return obj.app_logo.url
        return None


class CodeQuestProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for project listing"""
    group_number = serializers.CharField(source='group.group_number', read_only=True)
    
    class Meta:
        model = CodeQuestProject
        fields = ['id', 'app_name', 'group_number', 'is_approved', 'submission_date']


class CodeQuestConsultantSerializer(serializers.ModelSerializer):
    """Serializer for CodeQuestConsultant model"""
    assigned_group_count = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()
    # User account info (read-only display fields)
    user_full_name = serializers.SerializerMethodField()
    user_student_id = serializers.CharField(source='user.student_id', read_only=True)
    
    class Meta:
        model = CodeQuestConsultant
        fields = '__all__'
        extra_kwargs = {
            'access_key': {'read_only': True},
            'is_approved': {'read_only': True},
            'user': {'read_only': True},  # Auto-assigned from authenticated user
        }
    
    def get_assigned_group_count(self, obj):
        return obj.group_assignments.filter(is_active=True).count()
    
    def get_user_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return None
    
    def get_profile_image_url(self, obj):
        # Prioritize URL over upload
        if obj.profile_image_url:
            return obj.profile_image_url
        if obj.profile_image:
            return obj.profile_image.url
        return None
    
    def validate(self, attrs):
        """
        Validate that:
        1. User hasn't already registered as consultant for this event
        2. User hasn't registered as participant for this event
        3. Student ID isn't already registered for this event
        """
        event = attrs.get('event')
        student_id = attrs.get('student_id')
        request = self.context.get('request')
        user = request.user if request else None
        
        if event and user:
            # Check if user already registered as consultant
            existing_consultant = CodeQuestConsultant.objects.filter(
                event=event, user=user
            ).first()
            if existing_consultant:
                raise serializers.ValidationError({
                    'user': f'You have already applied as a consultant for this event. Your access key is: {existing_consultant.access_key}'
                })
            
            # Check if user already registered as participant
            existing_participant = CodeQuestParticipant.objects.filter(
                event=event, user=user
            ).first()
            if existing_participant:
                raise serializers.ValidationError({
                    'user': 'You have already registered as a participant for this event. You cannot register as both.'
                })
        
        if event and student_id:
            # Check if student_id already registered as consultant for this event
            existing_by_student_id = CodeQuestConsultant.objects.filter(
                event=event, student_id=student_id
            ).first()
            if existing_by_student_id:
                raise serializers.ValidationError({
                    'student_id': f'This Student ID is already registered as a consultant for this event.'
                })
            
            # Also check if student_id is registered as participant
            existing_participant_by_id = CodeQuestParticipant.objects.filter(
                event=event, student_id=student_id
            ).first()
            if existing_participant_by_id:
                raise serializers.ValidationError({
                    'student_id': 'This Student ID is already registered as a participant for this event.'
                })
        
        return attrs


class CodeQuestConsultantPublicSerializer(serializers.ModelSerializer):
    """Public serializer for consultants (hides access key)"""
    profile_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeQuestConsultant
        fields = ['id', 'name', 'expertise_areas', 'years_experience', 
                  'company_organization', 'bio', 'profile_image_url']
    
    def get_profile_image_url(self, obj):
        # Prioritize URL over upload
        if obj.profile_image_url:
            return obj.profile_image_url
        if obj.profile_image:
            return obj.profile_image.url
        return None


class ConsultantGroupAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for ConsultantGroupAssignment model"""
    consultant_name = serializers.CharField(source='consultant.name', read_only=True)
    group_number = serializers.CharField(source='group.group_number', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)
    
    class Meta:
        model = ConsultantGroupAssignment
        fields = '__all__'
        extra_kwargs = {
            'assigned_date': {'read_only': True},
        }


class ScoringCriteriaSerializer(serializers.ModelSerializer):
    """Serializer for ScoringCriteria model"""
    
    class Meta:
        model = ScoringCriteria
        fields = '__all__'


class CodeQuestFacilitatorSerializer(serializers.ModelSerializer):
    """Serializer for CodeQuestFacilitator model"""
    scores_submitted = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeQuestFacilitator
        fields = '__all__'
        extra_kwargs = {
            'access_code': {'read_only': True},
        }
    
    def get_scores_submitted(self, obj):
        return obj.scores_given.count()


class ProjectScoreSerializer(serializers.ModelSerializer):
    """Serializer for ProjectScore model"""
    facilitator_name = serializers.CharField(source='facilitator.name', read_only=True)
    criteria_name = serializers.CharField(source='criteria.criteria_name', read_only=True)
    project_name = serializers.CharField(source='project.app_name', read_only=True)
    max_points = serializers.IntegerField(source='criteria.max_points', read_only=True)
    
    class Meta:
        model = ProjectScore
        fields = '__all__'
        extra_kwargs = {
            'scored_date': {'read_only': True},
        }
    
    def validate(self, data):
        """Validate that score doesn't exceed max_points"""
        if 'score' in data and 'criteria' in data:
            if data['score'] > data['criteria'].max_points:
                raise serializers.ValidationError(
                    f"Score cannot exceed {data['criteria'].max_points} for this criteria"
                )
        return data


class FinalProjectScoreSerializer(serializers.ModelSerializer):
    """Serializer for FinalProjectScore model"""
    project_name = serializers.CharField(source='project.app_name', read_only=True)
    group_number = serializers.CharField(source='project.group.group_number', read_only=True)
    project_details = CodeQuestProjectListSerializer(source='project', read_only=True)
    
    class Meta:
        model = FinalProjectScore
        fields = '__all__'
        extra_kwargs = {
            'total_score': {'read_only': True},
            'average_score': {'read_only': True},
            'rank': {'read_only': True},
            'calculation_date': {'read_only': True},
        }


class ProjectTaskSerializer(serializers.ModelSerializer):
    """Serializer for ProjectTask model"""
    assigned_to_name = serializers.CharField(source='assigned_to.student_name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.student_name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectTask
        fields = '__all__'
        extra_kwargs = {
            'created_date': {'read_only': True},
            'assigned_by': {'read_only': True},
        }
    
    def get_is_overdue(self, obj):
        if obj.due_date and obj.status not in ['Completed']:
            from django.utils import timezone
            return obj.due_date < timezone.now()
        return False


# Nested serializers for detailed views
class GroupDetailSerializer(serializers.ModelSerializer):
    """Detailed group serializer with all related data"""
    members = CodeQuestParticipantPublicSerializer(many=True, read_only=True)
    project = CodeQuestProjectSerializer(read_only=True)
    consultant = CodeQuestConsultantPublicSerializer(read_only=True)
    member_roles = GroupMemberRoleSerializer(many=True, read_only=True)
    pm_candidates = ProjectManagerCandidateSerializer(many=True, read_only=True)
    
    class Meta:
        model = CodeQuestGroup
        fields = '__all__'


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Detailed project serializer with group and scores"""
    group_details = CodeQuestGroupListSerializer(source='group', read_only=True)
    scores = ProjectScoreSerializer(many=True, read_only=True)
    final_score = FinalProjectScoreSerializer(read_only=True)
    tasks = ProjectTaskSerializer(many=True, read_only=True)
    
    class Meta:
        model = CodeQuestProject
        fields = '__all__'


# ============================================================
# SELF-GROUPING SERIALIZERS
# ============================================================

from codequest.models import (
    SelfGroupingTeam,
    SelfGroupingMembership,
    GroupInvitation,
    JoinRequest,
)


class ParticipantBriefSerializer(serializers.ModelSerializer):
    """Brief participant info for self-grouping views"""
    year_display = serializers.CharField(source='get_year_display', read_only=True)
    preferred_role_display = serializers.CharField(source='get_preferred_role_display', read_only=True)
    has_team = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeQuestParticipant
        fields = [
            'id', 'student_id', 'student_name', 'year', 'year_display',
            'preferred_role', 'preferred_role_display', 'skills',
            'is_deferred', 'has_team'
        ]
    
    def get_has_team(self, obj):
        """Check if participant is in an active self-grouping team"""
        return obj.team_memberships.filter(
            status='accepted',
            team__status__in=['forming', 'ready']
        ).exists()


class SelfGroupingMembershipSerializer(serializers.ModelSerializer):
    """Serializer for team membership"""
    participant_name = serializers.CharField(source='participant.student_name', read_only=True)
    participant_id_number = serializers.CharField(source='participant.student_id', read_only=True)
    participant_role = serializers.CharField(source='participant.preferred_role', read_only=True)
    participant_skills = serializers.CharField(source='participant.skills', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SelfGroupingMembership
        fields = [
            'id', 'participant', 'participant_name', 'participant_id_number',
            'participant_role', 'participant_skills', 'status', 'status_display',
            'is_creator', 'joined_at'
        ]


class SelfGroupingTeamSerializer(serializers.ModelSerializer):
    """Serializer for self-grouping team"""
    creator_name = serializers.CharField(source='creator.student_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    member_count = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    can_add_members = serializers.SerializerMethodField()
    is_ready_to_finalize = serializers.SerializerMethodField()
    min_size = serializers.IntegerField(source='event.min_group_size', read_only=True)
    max_size = serializers.IntegerField(source='event.max_group_size', read_only=True)
    pending_invitations_count = serializers.SerializerMethodField()
    pending_requests_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SelfGroupingTeam
        fields = [
            'id', 'team_name', 'creator', 'creator_name', 'status', 'status_display',
            'member_count', 'members', 'can_add_members', 'is_ready_to_finalize',
            'min_size', 'max_size', 'pending_invitations_count', 'pending_requests_count',
            'created_at', 'updated_at'
        ]
    
    def get_member_count(self, obj):
        return obj.memberships.filter(status='accepted').count()
    
    def get_members(self, obj):
        """Return members with consistent field names matching frontend expectations"""
        memberships = obj.memberships.filter(status='accepted').select_related('participant')
        return [
            {
                'id': m.participant.id,
                'student_name': m.participant.student_name,
                'student_id': m.participant.student_id,
                'skills': m.participant.skills,
                'preferred_role': m.participant.preferred_role,
                'is_creator': m.is_creator,
                'joined_at': m.joined_at.isoformat() if m.joined_at else None
            }
            for m in memberships
        ]
    
    def get_can_add_members(self, obj):
        return obj.can_add_members()
    
    def get_is_ready_to_finalize(self, obj):
        return obj.is_ready_to_finalize()
    
    def get_pending_invitations_count(self, obj):
        return obj.invitations.filter(status='pending').count()
    
    def get_pending_requests_count(self, obj):
        return obj.join_requests.filter(status='pending').count()


class SelfGroupingTeamListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for team listing"""
    creator_name = serializers.CharField(source='creator.student_name', read_only=True)
    creator_id = serializers.CharField(source='creator.student_id', read_only=True)
    creator_skills = serializers.CharField(source='creator.skills', read_only=True)
    member_count = serializers.SerializerMethodField()
    max_size = serializers.IntegerField(source='event.max_group_size', read_only=True)
    min_size = serializers.IntegerField(source='event.min_group_size', read_only=True)
    can_join = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    
    class Meta:
        model = SelfGroupingTeam
        fields = [
            'id', 'team_name', 'creator', 'creator_name', 'creator_id', 'creator_skills',
            'status', 'member_count', 'max_size', 'min_size', 'can_join', 'members', 'created_at'
        ]
    
    def get_member_count(self, obj):
        return obj.memberships.filter(status='accepted').count()
    
    def get_can_join(self, obj):
        return obj.can_add_members() and obj.status == 'forming'
    
    def get_members(self, obj):
        """Return members with their skills for team preview"""
        memberships = obj.memberships.filter(status='accepted').select_related('participant')
        return [
            {
                'id': m.participant.id,
                'student_name': m.participant.student_name,
                'student_id': m.participant.student_id,
                'skills': m.participant.skills,
                'preferred_role': m.participant.preferred_role,
                'is_creator': m.is_creator
            }
            for m in memberships
        ]


class GroupInvitationSerializer(serializers.ModelSerializer):
    """Serializer for group invitations"""
    sender_name = serializers.CharField(source='sender.student_name', read_only=True)
    sender_id_number = serializers.CharField(source='sender.student_id', read_only=True)
    recipient_id = serializers.IntegerField(source='recipient.id', read_only=True)
    recipient_name = serializers.CharField(source='recipient.student_name', read_only=True)
    recipient_id_number = serializers.CharField(source='recipient.student_id', read_only=True)
    team_name = serializers.SerializerMethodField()
    team_member_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupInvitation
        fields = [
            'id', 'team', 'team_name', 'team_member_count',
            'sender', 'sender_name', 'sender_id_number',
            'recipient', 'recipient_id', 'recipient_name', 'recipient_id_number',
            'message', 'status', 'status_display', 'is_expired',
            'created_at', 'responded_at'
        ]
    
    def get_team_name(self, obj):
        return obj.team.team_name or f"Team by {obj.team.creator.student_name}"
    
    def get_team_member_count(self, obj):
        return obj.team.member_count()
    
    def get_is_expired(self, obj):
        return obj.is_expired()


class JoinRequestSerializer(serializers.ModelSerializer):
    """Serializer for join requests"""
    requester_name = serializers.CharField(source='requester.student_name', read_only=True)
    requester_id_number = serializers.CharField(source='requester.student_id', read_only=True)
    requester_role = serializers.CharField(source='requester.preferred_role', read_only=True)
    requester_skills = serializers.CharField(source='requester.skills', read_only=True)
    team_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    responded_by_name = serializers.CharField(source='responded_by.student_name', read_only=True)
    
    class Meta:
        model = JoinRequest
        fields = [
            'id', 'team', 'team_name',
            'requester', 'requester_name', 'requester_id_number',
            'requester_role', 'requester_skills',
            'message', 'status', 'status_display',
            'responded_by', 'responded_by_name',
            'created_at', 'responded_at'
        ]
    
    def get_team_name(self, obj):
        return obj.team.team_name or f"Team by {obj.team.creator.student_name}"


class CreateTeamSerializer(serializers.Serializer):
    """Serializer for creating a new team"""
    team_name = serializers.CharField(max_length=200, required=False, allow_blank=True)


class SendInvitationSerializer(serializers.Serializer):
    """Serializer for sending invitation"""
    recipient_id = serializers.IntegerField()
    message = serializers.CharField(max_length=500, required=False, allow_blank=True)


class RespondInvitationSerializer(serializers.Serializer):
    """Serializer for responding to invitation"""
    action = serializers.ChoiceField(choices=['accept', 'decline'])


class SendJoinRequestSerializer(serializers.Serializer):
    """Serializer for sending join request"""
    team_id = serializers.IntegerField()
    message = serializers.CharField(max_length=500, required=False, allow_blank=True)


class RespondJoinRequestSerializer(serializers.Serializer):
    """Serializer for responding to join request"""
    action = serializers.ChoiceField(choices=['accept', 'decline'])
