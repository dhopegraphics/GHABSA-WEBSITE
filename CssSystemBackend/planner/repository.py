from django.db.models import Q, Count, Sum, Avg, Prefetch
from django.utils import timezone
from datetime import timedelta, date
from .models import (
    Task, SubTask, TaskAttachment, PomodoroSession, PomodoroSettings,
    Goal, AISuggestion, StudyStatistics, PlannerNotification
)


class TaskRepository:
    """Repository for Task operations with optimized queries"""
    
    @staticmethod
    def get_user_tasks(user, include_deleted=False):
        """Get all tasks for a user with related data"""
        queryset = Task.objects.filter(user=user).select_related(
            'user', 'course'
        ).prefetch_related(
            'subtasks',
            'attachments',
            'pomodoro_sessions'
        )
        
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        return queryset
    
    @staticmethod
    def get_task_by_id(task_id, user=None):
        """Get a specific task with all related data"""
        queryset = Task.objects.select_related(
            'user', 'course'
        ).prefetch_related(
            'subtasks',
            'attachments',
            'pomodoro_sessions'
        )
        
        if user:
            queryset = queryset.filter(user=user)
        
        return queryset.filter(id=task_id, is_deleted=False).first()
    
    @staticmethod
    def get_today_tasks(user):
        """Get tasks due today"""
        today = date.today()
        return TaskRepository.get_user_tasks(user).filter(
            due_date=today,
            completed=False
        ).order_by('priority', 'due_time')
    
    @staticmethod
    def get_week_tasks(user, start_date=None):
        """Get tasks for the current week grouped by day"""
        from datetime import timedelta
        
        if start_date is None:
            # Get current week (Sunday to Saturday)
            today = date.today()
            start_date = today - timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0)
        
        end_date = start_date + timedelta(days=6)
        
        return TaskRepository.get_user_tasks(user).filter(
            due_date__range=[start_date, end_date]
        ).order_by('due_date', 'priority', 'due_time')
    
    @staticmethod
    def get_upcoming_tasks(user, days=7):
        """Get tasks due in the next N days"""
        today = date.today()
        end_date = today + timedelta(days=days)
        return TaskRepository.get_user_tasks(user).filter(
            due_date__range=[today, end_date],
            completed=False
        ).order_by('due_date', 'priority')
    
    @staticmethod
    def get_overdue_tasks(user):
        """Get overdue incomplete tasks"""
        today = date.today()
        return TaskRepository.get_user_tasks(user).filter(
            due_date__lt=today,
            completed=False
        ).order_by('due_date')
    
    @staticmethod
    def get_completed_tasks(user, start_date=None, end_date=None):
        """Get completed tasks within a date range"""
        queryset = TaskRepository.get_user_tasks(user).filter(completed=True)
        
        if start_date:
            queryset = queryset.filter(completed_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(completed_at__lte=end_date)
        
        return queryset.order_by('-completed_at')
    
    @staticmethod
    def filter_by_priority(queryset, priority):
        """Filter tasks by priority"""
        return queryset.filter(priority=priority)
    
    @staticmethod
    def filter_by_status(queryset, status):
        """Filter tasks by status"""
        return queryset.filter(status=status)
    
    @staticmethod
    def search_tasks(user, query):
        """Search tasks by title, description, or course code"""
        return TaskRepository.get_user_tasks(user).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(course_code__icontains=query)
        )
    
    @staticmethod
    def get_task_statistics(user, start_date=None, end_date=None):
        """Get task completion statistics"""
        queryset = Task.objects.filter(user=user, is_deleted=False)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset.aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(completed=True)),
            pending=Count('id', filter=Q(status='pending')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            high_priority=Count('id', filter=Q(priority='high')),
        )


class PomodoroRepository:
    """Repository for Pomodoro operations"""
    
    @staticmethod
    def get_user_sessions(user):
        """Get all pomodoro sessions for a user"""
        return PomodoroSession.objects.filter(user=user).select_related(
            'user', 'task'
        ).order_by('-start_time')
    
    @staticmethod
    def get_today_sessions(user):
        """Get today's pomodoro sessions"""
        today = timezone.now().date()
        return PomodoroRepository.get_user_sessions(user).filter(
            start_time__date=today
        )
    
    @staticmethod
    def get_sessions_by_date_range(user, start_date, end_date):
        """Get sessions within a date range"""
        return PomodoroRepository.get_user_sessions(user).filter(
            start_time__date__range=[start_date, end_date]
        )
    
    @staticmethod
    def get_session_statistics(user, start_date=None, end_date=None):
        """Get pomodoro session statistics"""
        queryset = PomodoroSession.objects.filter(user=user)
        
        if start_date:
            queryset = queryset.filter(start_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_time__date__lte=end_date)
        
        return queryset.aggregate(
            total_sessions=Count('id'),
            completed_sessions=Count('id', filter=Q(completed=True)),
            interrupted_sessions=Count('id', filter=Q(was_interrupted=True)),
            total_minutes=Sum('duration'),
            avg_duration=Avg('duration')
        )
    
    @staticmethod
    def get_or_create_settings(user):
        """Get or create pomodoro settings for user"""
        settings, created = PomodoroSettings.objects.get_or_create(user=user)
        return settings


class GoalRepository:
    """Repository for Goal operations"""
    
    @staticmethod
    def get_user_goals(user, include_completed=True):
        """Get all goals for a user"""
        queryset = Goal.objects.filter(user=user).select_related('user')
        
        if not include_completed:
            queryset = queryset.filter(completed=False)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def get_goals_by_type(user, goal_type):
        """Get goals by type (daily, weekly, monthly, semester)"""
        return GoalRepository.get_user_goals(user).filter(goal_type=goal_type)
    
    @staticmethod
    def get_active_goals(user):
        """Get currently active goals"""
        today = date.today()
        return GoalRepository.get_user_goals(user, include_completed=False).filter(
            start_date__lte=today,
            end_date__gte=today
        )
    
    @staticmethod
    def get_goals_by_category(user, category):
        """Get goals by category"""
        return GoalRepository.get_user_goals(user).filter(category=category)
    
    @staticmethod
    def get_goal_statistics(user):
        """Get goal completion statistics"""
        goals = Goal.objects.filter(user=user)
        
        return {
            'total': goals.count(),
            'completed': goals.filter(completed=True).count(),
            'active': goals.filter(
                completed=False,
                start_date__lte=date.today(),
                end_date__gte=date.today()
            ).count(),
            'by_type': {
                'daily': goals.filter(goal_type='daily').count(),
                'weekly': goals.filter(goal_type='weekly').count(),
                'monthly': goals.filter(goal_type='monthly').count(),
                'semester': goals.filter(goal_type='semester').count(),
            }
        }


class AISuggestionRepository:
    """Repository for AI Suggestion operations"""
    
    @staticmethod
    def get_active_suggestions(user):
        """Get active (not dismissed, not expired) suggestions"""
        now = timezone.now()
        return AISuggestion.objects.filter(
            user=user,
            is_dismissed=False,
            expires_at__gte=now
        ).select_related('user').order_by('-priority', '-created_at')
    
    @staticmethod
    def get_suggestions_by_type(user, suggestion_type):
        """Get suggestions by type"""
        return AISuggestionRepository.get_active_suggestions(user).filter(
            suggestion_type=suggestion_type
        )
    
    @staticmethod
    def dismiss_expired_suggestions():
        """Mark expired suggestions as dismissed"""
        now = timezone.now()
        return AISuggestion.objects.filter(
            expires_at__lt=now,
            is_dismissed=False
        ).update(is_dismissed=True)


class StudyStatisticsRepository:
    """Repository for Study Statistics operations"""
    
    @staticmethod
    def get_user_statistics(user, start_date=None, end_date=None):
        """Get study statistics for a user"""
        queryset = StudyStatistics.objects.filter(user=user).select_related('user')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('-date')
    
    @staticmethod
    def get_statistics_by_date(user, target_date):
        """Get statistics for a specific date"""
        return StudyStatistics.objects.filter(
            user=user,
            date=target_date
        ).select_related('user').first()
    
    @staticmethod
    def get_or_create_today_statistics(user):
        """Get or create today's statistics"""
        today = date.today()
        stats, created = StudyStatistics.objects.get_or_create(
            user=user,
            date=today
        )
        return stats
    
    @staticmethod
    def get_weekly_summary(user):
        """Get summary for the current week"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        stats = StudyStatisticsRepository.get_user_statistics(
            user, week_start, week_end
        )
        
        return stats.aggregate(
            total_study_time=Sum('study_time'),
            total_tasks_completed=Sum('tasks_completed'),
            total_pomodoro_sessions=Sum('pomodoro_sessions'),
            avg_productivity=Avg('productivity_score'),
            avg_focus=Avg('focus_score')
        )
    
    @staticmethod
    def get_monthly_summary(user, year=None, month=None):
        """Get summary for a specific month"""
        if not year or not month:
            today = date.today()
            year = today.year
            month = today.month
        
        stats = StudyStatistics.objects.filter(
            user=user,
            date__year=year,
            date__month=month
        )
        
        return stats.aggregate(
            total_study_time=Sum('study_time'),
            total_tasks_completed=Sum('tasks_completed'),
            total_pomodoro_sessions=Sum('pomodoro_sessions'),
            avg_productivity=Avg('productivity_score'),
            avg_focus=Avg('focus_score'),
            days_active=Count('id')
        )


class PlannerNotificationRepository:
    """Repository for Planner Notification operations"""
    
    @staticmethod
    def get_user_notifications(user, include_read=False):
        """Get all notifications for a user"""
        queryset = PlannerNotification.objects.filter(user=user).select_related(
            'user', 'task', 'goal'
        )
        
        if not include_read:
            queryset = queryset.filter(is_read=False)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def get_notifications_by_type(user, notification_type):
        """Get notifications by type"""
        return PlannerNotificationRepository.get_user_notifications(user).filter(
            notification_type=notification_type
        )
    
    @staticmethod
    def get_unread_count(user):
        """Get count of unread notifications"""
        return PlannerNotification.objects.filter(
            user=user,
            is_read=False
        ).count()
    
    @staticmethod
    def mark_all_as_read(user):
        """Mark all notifications as read for a user"""
        now = timezone.now()
        return PlannerNotification.objects.filter(
            user=user,
            is_read=False
        ).update(is_read=True, read_at=now)
