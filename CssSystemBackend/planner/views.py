from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from datetime import date, timedelta
from django.db.models import Q

from .models import (
    Task, SubTask, TaskAttachment, PomodoroSession, PomodoroSettings,
    Goal, AISuggestion, StudyStatistics, PlannerNotification
)
from .serializers import (
    TaskSerializer, TaskCreateSerializer, SubTaskSerializer,
    TaskAttachmentSerializer, PomodoroSessionSerializer,
    PomodoroSettingsSerializer, GoalSerializer,
    AISuggestionSerializer, StudyStatisticsSerializer,
    PlannerNotificationSerializer, PlannerDashboardSerializer
)
from .repository import (
    TaskRepository, PomodoroRepository,
    GoalRepository, AISuggestionRepository, StudyStatisticsRepository,
    PlannerNotificationRepository
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tasks"""
    
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        return TaskSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = TaskRepository.get_user_tasks(user)
        
        # Filter by query parameters
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = TaskRepository.filter_by_status(queryset, status_filter)
        
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = TaskRepository.filter_by_priority(queryset, priority)
        
        completed = self.request.query_params.get('completed', None)
        if completed is not None:
            queryset = queryset.filter(completed=completed.lower() == 'true')
        
        course_code = self.request.query_params.get('course_code', None)
        if course_code:
            queryset = queryset.filter(course_code__icontains=course_code)
        
        search = self.request.query_params.get('search', None)
        if search:
            queryset = TaskRepository.search_tasks(user, search)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's tasks"""
        tasks = TaskRepository.get_today_tasks(request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def week(self, request):
        """Get tasks for the current week"""
        from datetime import datetime
        
        # Optional start_date parameter to view different weeks
        start_date_str = request.query_params.get('start_date', None)
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        tasks = TaskRepository.get_week_tasks(request.user, start_date)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming tasks (next 7 days by default)"""
        days = int(request.query_params.get('days', 7))
        tasks = TaskRepository.get_upcoming_tasks(request.user, days)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue tasks"""
        tasks = TaskRepository.get_overdue_tasks(request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get completed tasks"""
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        tasks = TaskRepository.get_completed_tasks(request.user, start_date, end_date)
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_complete(self, request, pk=None):
        """Toggle task completion status"""
        task = self.get_object()
        task.completed = not task.completed
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def soft_delete(self, request, pk=None):
        """Soft delete a task"""
        task = self.get_object()
        task.is_deleted = True
        task.save()
        return Response({'status': 'task deleted'})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get task statistics"""
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        stats = TaskRepository.get_task_statistics(request.user, start_date, end_date)
        return Response(stats)


class SubTaskViewSet(viewsets.ModelViewSet):
    """ViewSet for managing subtasks"""
    
    serializer_class = SubTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        task_id = self.request.query_params.get('task_id', None)
        if task_id:
            return SubTask.objects.filter(task_id=task_id, task__user=self.request.user)
        return SubTask.objects.filter(task__user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_complete(self, request, pk=None):
        """Toggle subtask completion"""
        subtask = self.get_object()
        subtask.completed = not subtask.completed
        subtask.save()
        serializer = self.get_serializer(subtask)
        return Response(serializer.data)


class PomodoroSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing pomodoro sessions"""
    
    serializer_class = PomodoroSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        queryset = PomodoroRepository.get_user_sessions(user)
        
        task_id = self.request.query_params.get('task_id', None)
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        
        date_filter = self.request.query_params.get('date', None)
        if date_filter:
            queryset = queryset.filter(start_time__date=date_filter)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's pomodoro sessions"""
        sessions = PomodoroRepository.get_today_sessions(request.user)
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get pomodoro statistics"""
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        stats = PomodoroRepository.get_session_statistics(
            request.user, start_date, end_date
        )
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark session as completed"""
        session = self.get_object()
        session.completed = True
        session.end_time = timezone.now()
        session.save()
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def interrupt(self, request, pk=None):
        """Mark session as interrupted"""
        session = self.get_object()
        session.was_interrupted = True
        session.end_time = timezone.now()
        session.save()
        serializer = self.get_serializer(session)
        return Response(serializer.data)


class PomodoroSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing pomodoro settings"""
    
    serializer_class = PomodoroSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PomodoroSettings.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get', 'post', 'put'])
    def my_settings(self, request):
        """Get or update user's pomodoro settings"""
        settings = PomodoroRepository.get_or_create_settings(request.user)
        
        if request.method == 'GET':
            serializer = self.get_serializer(settings)
            return Response(serializer.data)
        
        elif request.method in ['POST', 'PUT']:
            serializer = self.get_serializer(settings, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class GoalViewSet(viewsets.ModelViewSet):
    """ViewSet for managing goals"""
    
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        queryset = GoalRepository.get_user_goals(user)
        
        goal_type = self.request.query_params.get('type', None)
        if goal_type:
            queryset = GoalRepository.get_goals_by_type(user, goal_type)
        
        category = self.request.query_params.get('category', None)
        if category:
            queryset = GoalRepository.get_goals_by_category(user, category)
        
        completed = self.request.query_params.get('completed', None)
        if completed is not None:
            queryset = queryset.filter(completed=completed.lower() == 'true')
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get currently active goals"""
        goals = GoalRepository.get_active_goals(request.user)
        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get goal statistics"""
        stats = GoalRepository.get_goal_statistics(request.user)
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update goal progress"""
        goal = self.get_object()
        current_value = request.data.get('current_value', None)
        
        if current_value is not None:
            goal.current_value = current_value
            
            # Auto-complete if target reached
            if goal.current_value >= goal.target_value:
                goal.completed = True
                goal.completed_at = timezone.now()
            
            goal.save()
            serializer = self.get_serializer(goal)
            return Response(serializer.data)
        
        return Response(
            {'error': 'current_value is required'},
            status=status.HTTP_400_BAD_REQUEST
        )


class AISuggestionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AI suggestions (read-only)"""
    
    serializer_class = AISuggestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = AISuggestionRepository.get_active_suggestions(user)
        
        suggestion_type = self.request.query_params.get('type', None)
        if suggestion_type:
            queryset = AISuggestionRepository.get_suggestions_by_type(
                user, suggestion_type
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Dismiss a suggestion"""
        suggestion = self.get_object()
        suggestion.is_dismissed = True
        suggestion.save()
        return Response({'status': 'suggestion dismissed'})
    
    @action(detail=True, methods=['post'])
    def act_upon(self, request, pk=None):
        """Mark suggestion as acted upon"""
        suggestion = self.get_object()
        suggestion.is_acted_upon = True
        suggestion.save()
        return Response({'status': 'suggestion acted upon'})


class StudyStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for study statistics (read-only)"""
    
    serializer_class = StudyStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        return StudyStatisticsRepository.get_user_statistics(
            user, start_date, end_date
        )
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's statistics"""
        stats = StudyStatisticsRepository.get_or_create_today_statistics(request.user)
        serializer = self.get_serializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def weekly(self, request):
        """Get weekly summary"""
        summary = StudyStatisticsRepository.get_weekly_summary(request.user)
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Get monthly summary"""
        year = request.query_params.get('year', None)
        month = request.query_params.get('month', None)
        summary = StudyStatisticsRepository.get_monthly_summary(
            request.user, year, month
        )
        return Response(summary)


class PlannerNotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for planner notifications"""
    
    serializer_class = PlannerNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        include_read = self.request.query_params.get('include_read', 'false')
        queryset = PlannerNotificationRepository.get_user_notifications(
            user, include_read.lower() == 'true'
        )
        
        notification_type = self.request.query_params.get('type', None)
        if notification_type:
            queryset = PlannerNotificationRepository.get_notifications_by_type(
                user, notification_type
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = PlannerNotificationRepository.get_unread_count(request.user)
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        count = PlannerNotificationRepository.mark_all_as_read(request.user)
        return Response({'marked_read': count})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark specific notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)


class PlannerDashboardViewSet(viewsets.ViewSet):
    """ViewSet for planner dashboard overview"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get complete dashboard overview"""
        user = request.user
        
        dashboard_data = {
            'today_tasks': TaskRepository.get_today_tasks(user)[:5],
            'upcoming_tasks': TaskRepository.get_upcoming_tasks(user, 3)[:5],
            'active_goals': GoalRepository.get_active_goals(user)[:3],
            'recent_sessions': PomodoroRepository.get_today_sessions(user)[:5],
            'ai_suggestions': AISuggestionRepository.get_active_suggestions(user)[:3],
            'statistics': StudyStatisticsRepository.get_or_create_today_statistics(user),
            'unread_notifications_count': PlannerNotificationRepository.get_unread_count(user)
        }
        
        serializer = PlannerDashboardSerializer(dashboard_data)
        return Response(serializer.data)
