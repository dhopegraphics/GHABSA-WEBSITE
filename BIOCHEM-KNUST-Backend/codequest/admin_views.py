"""
Admin views for Code Quest management
Requires admin authentication
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction

from codequest.models import *
from codequest.serializers import *
from codequest.repositories import *
from codequest import utils as codequest_utils


class CodeQuestEventViewSet(viewsets.ModelViewSet):
    """CRUD operations for Code Quest events"""
    queryset = CodeQuestEvent.objects.all()
    serializer_class = CodeQuestEventSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CodeQuestEventListSerializer
        return CodeQuestEventSerializer


class GroupStudentsView(APIView):
    """Trigger automatic grouping algorithm"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        event_id = request.data.get('event_id')
        max_group_size = request.data.get('max_group_size')
        min_group_size = request.data.get('min_group_size', 5)
        
        if not event_id:
            return Response(
                {'error': 'event_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event = CodeQuestEventRepository.get_by_id(event_id)
        
        if not event:
            return Response(
                {'error': 'Event not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get ungrouped participants
        participants = CodeQuestParticipantRepository.get_ungrouped_participants(event_id)
        
        if not participants.exists():
            return Response(
                {'message': 'No ungrouped participants found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Run grouping algorithm
        groups = codequest_utils.group_participants_automatically(
            event, 
            participants, 
            max_group_size=max_group_size or event.max_group_size,
            min_group_size=min_group_size
        )
        
        serializer = CodeQuestGroupListSerializer(groups, many=True)
        
        return Response({
            'message': f'Successfully created {len(groups)} groups',
            'total_groups': len(groups),
            'groups': serializer.data
        })


class AssignConsultantsView(APIView):
    """Assign consultants to groups"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        event_id = request.data.get('event_id')
        method = request.data.get('method', 'random')  # random or manual
        
        if not event_id:
            return Response(
                {'error': 'event_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event = CodeQuestEventRepository.get_by_id(event_id)
        
        if not event:
            return Response(
                {'error': 'Event not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if method == 'random':
            consultants = CodeQuestConsultantRepository.get_approved_consultants(event_id)
            groups = CodeQuestGroupRepository.get_groups_without_consultant(event_id)
            
            if not consultants.exists():
                return Response(
                    {'error': 'No approved consultants found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not groups.exists():
                return Response(
                    {'message': 'All groups already have consultants'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            assignments = codequest_utils.assign_consultants_randomly(event, consultants, groups)
            
            serializer = ConsultantGroupAssignmentSerializer(assignments, many=True)
            
            return Response({
                'message': f'Successfully assigned consultants to {len(assignments)} groups',
                'total_assignments': len(assignments),
                'assignments': serializer.data
            })
        
        elif method == 'manual':
            # Manual assignment requires consultant_id and group_id
            consultant_id = request.data.get('consultant_id')
            group_id = request.data.get('group_id')
            
            if not all([consultant_id, group_id]):
                return Response(
                    {'error': 'consultant_id and group_id are required for manual assignment'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            consultant = CodeQuestConsultantRepository.get_by_id(consultant_id)
            group = CodeQuestGroupRepository.get_by_id(group_id)
            
            if not consultant or not group:
                return Response(
                    {'error': 'Consultant or group not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create assignment
            assignment = ConsultantGroupAssignment.objects.create(
                consultant=consultant,
                group=group,
                assigned_by=request.user,
                is_active=True
            )
            
            group.consultant = consultant
            group.save()
            
            serializer = ConsultantGroupAssignmentSerializer(assignment)
            
            return Response({
                'message': 'Consultant assigned successfully',
                'assignment': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(
            {'error': 'Invalid method. Use "random" or "manual"'},
            status=status.HTTP_400_BAD_REQUEST
        )


class AddFacilitatorView(APIView):
    """Add facilitator with access code"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        serializer = CodeQuestFacilitatorSerializer(data=request.data)
        
        if serializer.is_valid():
            facilitator = serializer.save()
            
            response_serializer = CodeQuestFacilitatorSerializer(facilitator)
            return Response({
                'message': 'Facilitator added successfully',
                'facilitator': response_serializer.data,
                'access_code': facilitator.access_code
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApproveProjectView(APIView):
    """Approve or reject project submission"""
    permission_classes = [permissions.IsAdminUser]
    
    def patch(self, request, project_id):
        project = CodeQuestProjectRepository.get_by_id(project_id)
        
        if not project:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        is_approved = request.data.get('is_approved')
        admin_feedback = request.data.get('admin_feedback', '')
        
        if is_approved is None:
            return Response(
                {'error': 'is_approved is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        project.is_approved = is_approved
        project.admin_feedback = admin_feedback
        project.save()
        
        serializer = CodeQuestProjectSerializer(project)
        
        return Response({
            'message': 'Project approval status updated',
            'project': serializer.data
        })


class CalculateScoresView(APIView):
    """Calculate final scores for all projects"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        event_id = request.data.get('event_id')
        
        if not event_id:
            return Response(
                {'error': 'event_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event = CodeQuestEventRepository.get_by_id(event_id)
        
        if not event:
            return Response(
                {'error': 'Event not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate scoring criteria
        is_valid, total_weight, message = codequest_utils.validate_score_criteria_weights(event)
        
        if not is_valid:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Rank all projects
        final_scores = codequest_utils.rank_all_projects(event)
        
        serializer = FinalProjectScoreSerializer(final_scores, many=True)
        
        return Response({
            'message': f'Calculated scores for {len(final_scores)} projects',
            'total_projects': len(final_scores),
            'scores': serializer.data
        })


class PublishResultsView(APIView):
    """Publish results to participants"""
    permission_classes = [permissions.IsAdminUser]
    
    def patch(self, request):
        event_id = request.data.get('event_id')
        
        if not event_id:
            return Response(
                {'error': 'event_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event = CodeQuestEventRepository.get_by_id(event_id)
        
        if not event:
            return Response(
                {'error': 'Event not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        count = codequest_utils.publish_results(event)
        
        return Response({
            'message': f'Published results for {count} projects',
            'total_published': count
        })


class EndPMElectionView(APIView):
    """End PM election for a group"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        group_id = request.data.get('group_id')
        
        if not group_id:
            return Response(
                {'error': 'group_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        group = CodeQuestGroupRepository.get_by_id(group_id)
        
        if not group:
            return Response(
                {'error': 'Group not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        winner = codequest_utils.end_pm_election(group)
        
        if not winner:
            return Response(
                {'error': 'No candidates found for this group'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ProjectManagerCandidateSerializer(winner)
        
        return Response({
            'message': f'{winner.participant.student_name} is now the Project Manager',
            'winner': serializer.data
        })


class EventAnalyticsView(APIView):
    """Get analytics for an event"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        event_id = request.query_params.get('event_id')
        
        if not event_id:
            return Response(
                {'error': 'event_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event = CodeQuestEventRepository.get_by_id(event_id)
        
        if not event:
            return Response(
                {'error': 'Event not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Gather statistics
        total_participants = CodeQuestParticipantRepository.get_all_participants(event_id).count()
        grouped_participants = CodeQuestParticipantRepository.get_grouped_participants(event_id).count()
        ungrouped_participants = CodeQuestParticipantRepository.get_ungrouped_participants(event_id).count()
        deferred_participants = CodeQuestParticipantRepository.get_deferred_participants(event_id).count()
        
        total_groups = CodeQuestGroupRepository.get_all_groups(event_id).count()
        groups_without_pm = CodeQuestGroupRepository.get_groups_without_pm(event_id).count()
        groups_without_consultant = CodeQuestGroupRepository.get_groups_without_consultant(event_id).count()
        groups_with_projects = CodeQuestGroupRepository.get_groups_with_projects(event_id).count()
        
        total_consultants = CodeQuestConsultantRepository.get_all_consultants(event_id).count()
        approved_consultants = CodeQuestConsultantRepository.get_approved_consultants(event_id).count()
        pending_consultants = CodeQuestConsultantRepository.get_pending_approval(event_id).count()
        
        total_projects = CodeQuestProjectRepository.get_all_projects(event_id).count()
        approved_projects = CodeQuestProjectRepository.get_approved_projects(event_id).count()
        pending_projects = CodeQuestProjectRepository.get_pending_approval(event_id).count()
        
        total_facilitators = CodeQuestFacilitatorRepository.get_all_facilitators(event_id).count()
        total_criteria = ScoringCriteriaRepository.get_criteria_by_event(event_id).count()
        
        scored_projects = FinalProjectScore.objects.filter(
            project__group__event_id=event_id
        ).count()
        published_scores = FinalProjectScore.objects.filter(
            project__group__event_id=event_id,
            is_published=True
        ).count()
        
        return Response({
            'event': CodeQuestEventSerializer(event).data,
            'participants': {
                'total': total_participants,
                'grouped': grouped_participants,
                'ungrouped': ungrouped_participants,
                'deferred': deferred_participants,
            },
            'groups': {
                'total': total_groups,
                'without_pm': groups_without_pm,
                'without_consultant': groups_without_consultant,
                'with_projects': groups_with_projects,
            },
            'consultants': {
                'total': total_consultants,
                'approved': approved_consultants,
                'pending': pending_consultants,
            },
            'projects': {
                'total': total_projects,
                'approved': approved_projects,
                'pending': pending_projects,
            },
            'scoring': {
                'facilitators': total_facilitators,
                'criteria': total_criteria,
                'scored_projects': scored_projects,
                'published_scores': published_scores,
            }
        })
