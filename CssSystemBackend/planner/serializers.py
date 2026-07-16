from rest_framework import serializers
from django.utils import timezone
from datetime import date, timedelta
from .models import (
    Task, SubTask, TaskAttachment, PomodoroSession, PomodoroSettings,
    Goal, AISuggestion, StudyStatistics, PlannerNotification
)


class SubTaskSerializer(serializers.ModelSerializer):
    """Serializer for SubTask model"""
    
    class Meta:
        model = SubTask
        fields = [
            'id', 'title', 'completed', 'order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TaskAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for TaskAttachment model"""
    file = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskAttachment
        fields = [
            'id', 'file', 'filename', 'file_size', 'file_type', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_file(self, obj):
        # Prioritize URL over upload
        if obj.file_url:
            return obj.file_url
        if obj.file:
            return obj.file.url
        return None


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model"""
    
    subtasks = SubTaskSerializer(many=True, read_only=True)
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    pomodoro_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'user', 'user_name', 'title', 'description',
            'course_code', 'course', 'due_date', 'due_time',
            'priority', 'status', 'completed', 'completed_at',
            'emoji', 'color_gradient_start', 'color_gradient_end',
            'estimated_duration', 'actual_duration',
            'tags', 'notes', 'subtasks', 'attachments',
            'days_remaining', 'is_overdue', 'completion_percentage',
            'pomodoro_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'completed_at']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    
    def get_days_remaining(self, obj):
        if obj.completed:
            return 0
        delta = obj.due_date - date.today()
        return delta.days
    
    def get_is_overdue(self, obj):
        if obj.completed:
            return False
        return obj.due_date < date.today()
    
    def get_completion_percentage(self, obj):
        total_subtasks = obj.subtasks.count()
        if total_subtasks == 0:
            return 100 if obj.completed else 0
        completed_subtasks = obj.subtasks.filter(completed=True).count()
        return int((completed_subtasks / total_subtasks) * 100)
    
    def get_pomodoro_count(self, obj):
        return obj.pomodoro_sessions.filter(completed=True).count()


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks with nested subtasks"""
    
    subtasks = SubTaskSerializer(many=True, required=False)
    attachment_urls = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        write_only=True,
        help_text="List of attachment URLs (Google Drive, Dropbox, etc.)"
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'course_code', 'course',
            'due_date', 'due_time', 'priority', 'status',
            'emoji', 'color_gradient_start', 'color_gradient_end',
            'estimated_duration', 'tags', 'notes', 'subtasks', 'attachment_urls'
        ]
    
    def create(self, validated_data):
        subtasks_data = validated_data.pop('subtasks', [])
        attachment_urls = validated_data.pop('attachment_urls', [])
        task = Task.objects.create(**validated_data)
        
        for idx, subtask_data in enumerate(subtasks_data):
            SubTask.objects.create(task=task, order=idx, **subtask_data)
        
        # Create TaskAttachment records for each URL
        for url in attachment_urls:
            # Extract filename from URL or use a default
            filename = url.split('/')[-1] or 'Attachment'
            TaskAttachment.objects.create(
                task=task,
                file_url=url,
                filename=filename,
                file_type='url',
                file_size=0
            )
        
        return task


class PomodoroSessionSerializer(serializers.ModelSerializer):
    """Serializer for PomodoroSession model"""
    
    task_title = serializers.SerializerMethodField()
    actual_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = PomodoroSession
        fields = [
            'id', 'user', 'task', 'task_title', 'start_time',
            'end_time', 'duration', 'actual_duration', 'completed',
            'was_interrupted', 'notes'
        ]
        read_only_fields = ['id', 'user']
    
    def get_task_title(self, obj):
        return obj.task.title if obj.task else None
    
    def get_actual_duration(self, obj):
        """Calculate actual duration if session has ended"""
        if obj.end_time and obj.start_time:
            delta = obj.end_time - obj.start_time
            return int(delta.total_seconds() / 60)
        return None


class PomodoroSettingsSerializer(serializers.ModelSerializer):
    """Serializer for PomodoroSettings model"""
    
    class Meta:
        model = PomodoroSettings
        fields = [
            'user', 'focus_duration', 'short_break', 'long_break',
            'sessions_until_long_break', 'auto_start_breaks',
            'auto_start_pomodoros', 'sound_enabled',
            'notifications_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']


class GoalSerializer(serializers.ModelSerializer):
    """Serializer for Goal model"""
    
    progress_percentage = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Goal
        fields = [
            'id', 'user', 'title', 'description', 'goal_type',
            'category', 'target_value', 'current_value', 'unit',
            'progress_percentage', 'start_date', 'end_date',
            'days_remaining', 'is_active', 'icon', 'color',
            'completed', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'completed_at']
    
    def get_progress_percentage(self, obj):
        return obj.progress_percentage
    
    def get_days_remaining(self, obj):
        if obj.completed:
            return 0
        delta = obj.end_date - date.today()
        return max(0, delta.days)
    
    def get_is_active(self, obj):
        today = date.today()
        return (not obj.completed and 
                obj.start_date <= today <= obj.end_date)


class AISuggestionSerializer(serializers.ModelSerializer):
    """Serializer for AISuggestion model"""
    
    is_expired = serializers.SerializerMethodField()
    hours_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = AISuggestion
        fields = [
            'id', 'user', 'suggestion_type', 'title', 'content',
            'icon', 'color', 'priority', 'is_dismissed',
            'is_acted_upon', 'is_expired', 'hours_until_expiry',
            'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']
    
    def get_is_expired(self, obj):
        return obj.expires_at < timezone.now()
    
    def get_hours_until_expiry(self, obj):
        delta = obj.expires_at - timezone.now()
        return max(0, int(delta.total_seconds() / 3600))


class StudyStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for StudyStatistics model"""
    
    completion_rate = serializers.SerializerMethodField()
    avg_session_time = serializers.SerializerMethodField()
    
    class Meta:
        model = StudyStatistics
        fields = [
            'user', 'date', 'tasks_completed', 'tasks_created',
            'total_tasks', 'completion_rate', 'study_time',
            'pomodoro_sessions', 'break_time', 'avg_session_time',
            'productivity_score', 'focus_score', 'current_streak',
            'longest_streak', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_completion_rate(self, obj):
        if obj.total_tasks == 0:
            return 0
        return round((obj.tasks_completed / obj.total_tasks) * 100, 1)
    
    def get_avg_session_time(self, obj):
        if obj.pomodoro_sessions == 0:
            return 0
        return round(obj.study_time / obj.pomodoro_sessions, 1)


class PlannerNotificationSerializer(serializers.ModelSerializer):
    """Serializer for PlannerNotification model"""
    
    task_title = serializers.SerializerMethodField()
    class_info = serializers.SerializerMethodField()
    goal_title = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = PlannerNotification
        fields = [
            'id', 'user', 'notification_type', 'title', 'message',
            'task', 'task_title', 'goal', 'goal_title', 'is_read', 'time_ago',
            'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'read_at']
    
    def get_task_title(self, obj):
        return obj.task.title if obj.task else None
    
    def get_goal_title(self, obj):
        return obj.goal.title if obj.goal else None
    
    def get_time_ago(self, obj):
        """Calculate time ago in a human-readable format"""
        delta = timezone.now() - obj.created_at
        
        if delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds >= 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds >= 60:
            return f"{delta.seconds // 60}m ago"
        else:
            return "just now"


class PlannerDashboardSerializer(serializers.Serializer):
    """Serializer for planner dashboard overview"""
    
    today_tasks = TaskSerializer(many=True, read_only=True)
    upcoming_tasks = TaskSerializer(many=True, read_only=True)
    active_goals = GoalSerializer(many=True, read_only=True)
    recent_sessions = PomodoroSessionSerializer(many=True, read_only=True)
    ai_suggestions = AISuggestionSerializer(many=True, read_only=True)
    statistics = StudyStatisticsSerializer(read_only=True)
    unread_notifications_count = serializers.IntegerField()
