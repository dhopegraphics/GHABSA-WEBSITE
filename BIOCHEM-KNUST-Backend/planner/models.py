from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from uuid import uuid4
from accounts.models import CustomUser
from academics.models import Course
from django.utils import timezone
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage


class Task(models.Model):
    """User tasks and assignments"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='planner_tasks'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    course_code = models.CharField(max_length=100)  # e.g., "DCIT 308"
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='planner_tasks'
    )
    
    due_date = models.DateField()
    due_time = models.TimeField(null=True, blank=True)
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='medium',
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    completed = models.BooleanField(default=False, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    emoji = models.CharField(max_length=10, default='📝')
    color_gradient_start = models.CharField(max_length=7, default='#667eea')
    color_gradient_end = models.CharField(max_length=7, default='#764ba2')
    
    estimated_duration = models.IntegerField(
        help_text="Estimated duration in minutes",
        null=True,
        blank=True,
        validators=[MinValueValidator(1)]
    )
    actual_duration = models.IntegerField(
        help_text="Actual time spent in minutes",
        null=True,
        blank=True
    )
    
    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'planner_tasks'
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'completed', 'due_date']),
            models.Index(fields=['user', 'priority']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.first_name}"
    
    def save(self, *args, **kwargs):
        if self.completed and not self.completed_at:
            self.completed_at = timezone.now()
            self.status = 'completed'
        elif not self.completed and self.completed_at:
            self.completed_at = None
        super().save(*args, **kwargs)


class SubTask(models.Model):
    """Subtasks for breaking down larger tasks"""
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='subtasks'
    )
    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'planner_subtasks'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.task.title} - {self.title}"


class TaskAttachment(MediaUrlMixin, models.Model):
    """File attachments for tasks"""
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'file': 'file_url',
    }
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(storage=DynamicStorage(), upload_to='planner/attachments/%Y/%m/', blank=True, null=True)
    file_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide file URL (Google Drive, Dropbox, etc.) instead of uploading"
    )
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes", blank=True, null=True)
    file_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'planner_task_attachments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.task.title} - {self.filename}"


class PomodoroSession(models.Model):
    """Pomodoro focus sessions"""
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='pomodoro_sessions'
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pomodoro_sessions'
    )
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(help_text="Session duration in minutes")
    completed = models.BooleanField(default=False)
    was_interrupted = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'planner_pomodoro_sessions'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['user', 'start_time']),
        ]
    
    def __str__(self):
        return f"{self.user.first_name} - {self.start_time.date()}"


class PomodoroSettings(models.Model):
    """User-specific Pomodoro settings"""
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='pomodoro_settings'
    )
    focus_duration = models.IntegerField(
        default=25,
        validators=[MinValueValidator(5), MaxValueValidator(60)],
        help_text="Focus session duration in minutes"
    )
    short_break = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(15)],
        help_text="Short break duration in minutes"
    )
    long_break = models.IntegerField(
        default=15,
        validators=[MinValueValidator(5), MaxValueValidator(30)],
        help_text="Long break duration in minutes"
    )
    sessions_until_long_break = models.IntegerField(
        default=4,
        validators=[MinValueValidator(2), MaxValueValidator(10)]
    )
    auto_start_breaks = models.BooleanField(default=False)
    auto_start_pomodoros = models.BooleanField(default=False)
    sound_enabled = models.BooleanField(default=True)
    notifications_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'planner_pomodoro_settings'
        verbose_name = 'Pomodoro Settings'
        verbose_name_plural = 'Pomodoro Settings'
    
    def __str__(self):
        return f"{self.user.first_name}'s Pomodoro Settings"


class Goal(models.Model):
    """User goals (daily, weekly, monthly, semester)"""
    
    TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('semester', 'Semester'),
    ]
    
    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('personal', 'Personal'),
        ('health', 'Health'),
        ('career', 'Career'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='planner_goals'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    goal_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        db_index=True
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='academic'
    )
    
    target_value = models.FloatField(validators=[MinValueValidator(0)])
    current_value = models.FloatField(default=0, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=50, help_text="e.g., hours, tasks, pages")
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    icon = models.CharField(max_length=50, default='trophy')
    color = models.CharField(max_length=7, default='#10B981')
    
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'planner_goals'
        verbose_name = 'Goal'
        verbose_name_plural = 'Goals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'goal_type', 'completed']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.first_name}"
    
    @property
    def progress_percentage(self):
        if self.target_value == 0:
            return 0
        return min(100, (self.current_value / self.target_value) * 100)


class AISuggestion(models.Model):
    """AI-generated study suggestions"""
    
    TYPE_CHOICES = [
        ('study_time', 'Study Time Recommendation'),
        ('priority', 'Priority Suggestion'),
        ('productivity', 'Productivity Tip'),
        ('break', 'Break Reminder'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='ai_suggestions'
    )
    
    suggestion_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    icon = models.CharField(max_length=50, default='bulb')
    color = models.CharField(max_length=7, default='#F59E0B')
    
    priority = models.IntegerField(default=0)
    is_dismissed = models.BooleanField(default=False)
    is_acted_upon = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'planner_ai_suggestions'
        verbose_name = 'AI Suggestion'
        verbose_name_plural = 'AI Suggestions'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_dismissed', 'expires_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.first_name}"


class StudyStatistics(models.Model):
    """Daily aggregated study statistics"""
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='study_statistics'
    )
    date = models.DateField(db_index=True)
    
    # Task statistics
    tasks_completed = models.IntegerField(default=0)
    tasks_created = models.IntegerField(default=0)
    total_tasks = models.IntegerField(default=0)
    
    # Time statistics (in minutes)
    study_time = models.IntegerField(default=0)
    pomodoro_sessions = models.IntegerField(default=0)
    break_time = models.IntegerField(default=0)
    
    # Productivity metrics
    productivity_score = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    focus_score = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Streak tracking
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'planner_study_statistics'
        verbose_name = 'Study Statistics'
        verbose_name_plural = 'Study Statistics'
        unique_together = ['user', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
    
    def __str__(self):
        return f"{self.user.first_name} - {self.date}"


class PlannerNotification(models.Model):
    """Planner-specific notifications"""
    
    TYPE_CHOICES = [
        ('task_reminder', 'Task Reminder'),
        ('break_reminder', 'Break Reminder'),
        ('goal_progress', 'Goal Progress'),
        ('achievement', 'Achievement'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='planner_notifications'
    )
    
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    goal = models.ForeignKey(
        Goal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'planner_notifications'
        verbose_name = 'Planner Notification'
        verbose_name_plural = 'Planner Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.first_name}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
