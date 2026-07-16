"""
Repository classes for Code Quest data access
Provides clean data access layer for views and business logic
"""
from django.db.models import Q, Count, Avg, Prefetch
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


class CodeQuestEventRepository:
    """Repository for CodeQuestEvent model"""
    
    @staticmethod
    def get_all_events():
        return CodeQuestEvent.objects.select_related('event').all()
    
    @staticmethod
    def get_active_events():
        """Get events that are not completed"""
        return CodeQuestEvent.objects.exclude(status='completed').select_related('event')
    
    @staticmethod
    def get_by_id(event_id):
        return CodeQuestEvent.objects.select_related('event').filter(id=event_id).first()
    
    @staticmethod
    def get_by_academic_year(academic_year):
        return CodeQuestEvent.objects.filter(academic_year=academic_year).select_related('event')
    
    @staticmethod
    def get_current_event():
        """Get the most recent active event"""
        from django.utils import timezone
        now = timezone.now()
        return CodeQuestEvent.objects.filter(
            registration_start_date__lte=now
        ).exclude(status='completed').order_by('-presentation_date').first()


class CodeQuestParticipantRepository:
    """Repository for CodeQuestParticipant model"""
    
    @staticmethod
    def get_all_participants(event_id=None):
        queryset = CodeQuestParticipant.objects.select_related('event', 'group')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        return queryset
    
    @staticmethod
    def get_by_id(participant_id):
        return CodeQuestParticipant.objects.select_related('event', 'group').filter(id=participant_id).first()
    
    @staticmethod
    def get_by_access_key(access_key):
        return CodeQuestParticipant.objects.select_related('event', 'group').filter(access_key=access_key).first()
    
    @staticmethod
    def get_by_student_id(student_id, event_id):
        return CodeQuestParticipant.objects.filter(student_id=student_id, event_id=event_id).first()
    
    @staticmethod
    def get_ungrouped_participants(event_id):
        """Get participants not assigned to any group"""
        return CodeQuestParticipant.objects.filter(event_id=event_id, group__isnull=True)
    
    @staticmethod
    def get_grouped_participants(event_id):
        """Get participants assigned to groups"""
        return CodeQuestParticipant.objects.filter(event_id=event_id, group__isnull=False).select_related('group')
    
    @staticmethod
    def get_deferred_participants(event_id):
        return CodeQuestParticipant.objects.filter(event_id=event_id, is_deferred=True)
    
    @staticmethod
    def get_regular_participants(event_id):
        return CodeQuestParticipant.objects.filter(event_id=event_id, is_deferred=False, year=2)


class CodeQuestGroupRepository:
    """Repository for CodeQuestGroup model"""
    
    @staticmethod
    def get_all_groups(event_id=None):
        queryset = CodeQuestGroup.objects.select_related('event', 'project_manager', 'consultant').prefetch_related('members')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        return queryset
    
    @staticmethod
    def get_by_id(group_id):
        return CodeQuestGroup.objects.select_related('event', 'project_manager', 'consultant').prefetch_related('members').filter(id=group_id).first()
    
    @staticmethod
    def get_groups_without_pm(event_id):
        """Get groups without project manager"""
        return CodeQuestGroup.objects.filter(event_id=event_id, project_manager__isnull=True)
    
    @staticmethod
    def get_groups_without_consultant(event_id):
        """Get groups without consultant"""
        return CodeQuestGroup.objects.filter(event_id=event_id, consultant__isnull=True)
    
    @staticmethod
    def get_groups_with_projects(event_id):
        """Get groups that have submitted projects"""
        return CodeQuestGroup.objects.filter(
            event_id=event_id
        ).exclude(project__isnull=True).select_related('project')


class ProjectManagerCandidateRepository:
    """Repository for ProjectManagerCandidate model"""
    
    @staticmethod
    def get_candidates_by_group(group_id):
        return ProjectManagerCandidate.objects.filter(group_id=group_id).select_related('participant').order_by('-vote_count')
    
    @staticmethod
    def get_by_id(candidate_id):
        return ProjectManagerCandidate.objects.select_related('participant', 'group').filter(id=candidate_id).first()
    
    @staticmethod
    def get_winner(group_id):
        return ProjectManagerCandidate.objects.filter(group_id=group_id, is_winner=True).first()


class ProjectManagerVoteRepository:
    """Repository for ProjectManagerVote model"""
    
    @staticmethod
    def get_votes_by_group(group_id):
        return ProjectManagerVote.objects.filter(group_id=group_id).select_related('voter', 'candidate')
    
    @staticmethod
    def has_voted(voter_id, group_id):
        return ProjectManagerVote.objects.filter(voter_id=voter_id, group_id=group_id).exists()
    
    @staticmethod
    def get_vote_by_voter(voter_id, group_id):
        return ProjectManagerVote.objects.filter(voter_id=voter_id, group_id=group_id).first()


class GroupMemberRoleRepository:
    """Repository for GroupMemberRole model"""
    
    @staticmethod
    def get_roles_by_group(group_id):
        return GroupMemberRole.objects.filter(group_id=group_id).select_related('participant')
    
    @staticmethod
    def get_roles_by_participant(participant_id):
        return GroupMemberRole.objects.filter(participant_id=participant_id).select_related('group')
    
    @staticmethod
    def get_role_distribution(group_id):
        """Get count of members per role type"""
        return GroupMemberRole.objects.filter(group_id=group_id).values('role_type').annotate(count=Count('id'))


class CodeQuestProjectRepository:
    """Repository for CodeQuestProject model"""
    
    @staticmethod
    def get_all_projects(event_id=None):
        queryset = CodeQuestProject.objects.select_related('group', 'group__event')
        if event_id:
            queryset = queryset.filter(group__event_id=event_id)
        return queryset
    
    @staticmethod
    def get_by_id(project_id):
        return CodeQuestProject.objects.select_related('group').filter(id=project_id).first()
    
    @staticmethod
    def get_by_group(group_id):
        return CodeQuestProject.objects.filter(group_id=group_id).first()
    
    @staticmethod
    def get_approved_projects(event_id):
        return CodeQuestProject.objects.filter(group__event_id=event_id, is_approved=True).select_related('group')
    
    @staticmethod
    def get_pending_approval(event_id):
        return CodeQuestProject.objects.filter(
            group__event_id=event_id, 
            is_approved=False,
            submission_date__isnull=False
        ).select_related('group')


class CodeQuestConsultantRepository:
    """Repository for CodeQuestConsultant model"""
    
    @staticmethod
    def get_all_consultants(event_id=None):
        queryset = CodeQuestConsultant.objects.all()
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        return queryset
    
    @staticmethod
    def get_by_id(consultant_id):
        return CodeQuestConsultant.objects.filter(id=consultant_id).first()
    
    @staticmethod
    def get_by_access_key(access_key):
        return CodeQuestConsultant.objects.filter(access_key=access_key).first()
    
    @staticmethod
    def get_approved_consultants(event_id):
        return CodeQuestConsultant.objects.filter(event_id=event_id, is_approved=True)
    
    @staticmethod
    def get_pending_approval(event_id):
        return CodeQuestConsultant.objects.filter(event_id=event_id, is_approved=False)


class ConsultantGroupAssignmentRepository:
    """Repository for ConsultantGroupAssignment model"""
    
    @staticmethod
    def get_assignments_by_consultant(consultant_id):
        return ConsultantGroupAssignment.objects.filter(
            consultant_id=consultant_id, 
            is_active=True
        ).select_related('group')
    
    @staticmethod
    def get_assignments_by_group(group_id):
        return ConsultantGroupAssignment.objects.filter(
            group_id=group_id, 
            is_active=True
        ).select_related('consultant')
    
    @staticmethod
    def get_active_assignments(event_id):
        return ConsultantGroupAssignment.objects.filter(
            group__event_id=event_id,
            is_active=True
        ).select_related('consultant', 'group')


class ScoringCriteriaRepository:
    """Repository for ScoringCriteria model"""
    
    @staticmethod
    def get_criteria_by_event(event_id):
        return ScoringCriteria.objects.filter(event_id=event_id, is_active=True).order_by('order', 'criteria_name')
    
    @staticmethod
    def get_by_id(criteria_id):
        return ScoringCriteria.objects.filter(id=criteria_id).first()


class CodeQuestFacilitatorRepository:
    """Repository for CodeQuestFacilitator model"""
    
    @staticmethod
    def get_all_facilitators(event_id=None):
        queryset = CodeQuestFacilitator.objects.filter(is_active=True)
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        return queryset
    
    @staticmethod
    def get_by_id(facilitator_id):
        return CodeQuestFacilitator.objects.filter(id=facilitator_id).first()
    
    @staticmethod
    def get_by_access_code(access_code):
        return CodeQuestFacilitator.objects.filter(access_code=access_code, is_active=True).first()


class ProjectScoreRepository:
    """Repository for ProjectScore model"""
    
    @staticmethod
    def get_scores_by_project(project_id):
        return ProjectScore.objects.filter(project_id=project_id).select_related('facilitator', 'criteria')
    
    @staticmethod
    def get_scores_by_facilitator(facilitator_id):
        return ProjectScore.objects.filter(facilitator_id=facilitator_id).select_related('project', 'criteria')
    
    @staticmethod
    def get_score(project_id, facilitator_id, criteria_id):
        return ProjectScore.objects.filter(
            project_id=project_id,
            facilitator_id=facilitator_id,
            criteria_id=criteria_id
        ).first()
    
    @staticmethod
    def has_scored(facilitator_id, project_id, criteria_id):
        return ProjectScore.objects.filter(
            facilitator_id=facilitator_id,
            project_id=project_id,
            criteria_id=criteria_id
        ).exists()


class FinalProjectScoreRepository:
    """Repository for FinalProjectScore model"""
    
    @staticmethod
    def get_all_scores(event_id):
        return FinalProjectScore.objects.filter(
            project__group__event_id=event_id
        ).select_related('project', 'project__group').order_by('-total_score')
    
    @staticmethod
    def get_published_scores(event_id):
        return FinalProjectScore.objects.filter(
            project__group__event_id=event_id,
            is_published=True
        ).select_related('project', 'project__group').order_by('rank')
    
    @staticmethod
    def get_by_project(project_id):
        return FinalProjectScore.objects.filter(project_id=project_id).first()
    
    @staticmethod
    def get_leaderboard(event_id, limit=10):
        """Get top N projects"""
        return FinalProjectScore.objects.filter(
            project__group__event_id=event_id,
            is_published=True
        ).select_related('project', 'project__group').order_by('rank')[:limit]


class ProjectTaskRepository:
    """Repository for ProjectTask model"""
    
    @staticmethod
    def get_tasks_by_project(project_id):
        return ProjectTask.objects.filter(project_id=project_id).select_related('assigned_to', 'assigned_by')
    
    @staticmethod
    def get_tasks_by_participant(participant_id):
        return ProjectTask.objects.filter(assigned_to_id=participant_id).select_related('project')
    
    @staticmethod
    def get_by_id(task_id):
        return ProjectTask.objects.select_related('project', 'assigned_to', 'assigned_by').filter(id=task_id).first()
    
    @staticmethod
    def get_overdue_tasks(project_id):
        from django.utils import timezone
        return ProjectTask.objects.filter(
            project_id=project_id,
            due_date__lt=timezone.now(),
            status__in=['Todo', 'In Progress']
        )
    
    @staticmethod
    def get_tasks_by_status(project_id, status):
        return ProjectTask.objects.filter(project_id=project_id, status=status).select_related('assigned_to')
