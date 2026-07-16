from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskViewSet, SubTaskViewSet, PomodoroSessionViewSet,
    PomodoroSettingsViewSet, GoalViewSet,
    AISuggestionViewSet, StudyStatisticsViewSet,
    PlannerNotificationViewSet, PlannerDashboardViewSet
)

app_name = 'planner'

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'subtasks', SubTaskViewSet, basename='subtask')
router.register(r'pomodoro-sessions', PomodoroSessionViewSet, basename='pomodoro-session')
router.register(r'pomodoro-settings', PomodoroSettingsViewSet, basename='pomodoro-settings')
router.register(r'goals', GoalViewSet, basename='goal')
router.register(r'ai-suggestions', AISuggestionViewSet, basename='ai-suggestion')
router.register(r'statistics', StudyStatisticsViewSet, basename='statistics')
router.register(r'notifications', PlannerNotificationViewSet, basename='notification')
router.register(r'dashboard', PlannerDashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
