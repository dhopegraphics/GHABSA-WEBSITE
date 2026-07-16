from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HelpDeskCategoryViewSet, HelpDeskRequestViewSet,
    HelpDeskResponseViewSet, ResponseReplyViewSet, BookmarkViewSet,
    NotificationViewSet, ReportViewSet, StatsView
)

# Create router
router = DefaultRouter()
router.register(r'categories', HelpDeskCategoryViewSet, basename='category')
router.register(r'requests', HelpDeskRequestViewSet, basename='request')
router.register(r'responses', HelpDeskResponseViewSet, basename='response')
router.register(r'replies', ResponseReplyViewSet, basename='reply')
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'stats', StatsView, basename='stats')

urlpatterns = [
    path('', include(router.urls)),
]
