from django.urls import path
from notifications import views
from notifications.recent_updates_views import (
    RecentUpdatesView,
    RecentUpdatesStatsView,
    RecentUpdatesByTypeView,
)
from notifications.read_status_views import (
    MarkUpdateAsReadView,
    DeleteUpdateView,
    UnreadCountView,
)

app_name = 'notifications'

urlpatterns = [
    # Device management
    path('devices/register/', views.RegisterDeviceView.as_view(), name='register-device'),
    path('devices/check/', views.CheckDeviceView.as_view(), name='check-device'),
    path('devices/deactivate/', views.DeactivateCurrentDeviceView.as_view(), name='deactivate-device'),
    path('devices/', views.DeviceListView.as_view(), name='device-list'),
    path('devices/<uuid:pk>/', views.DeviceDetailView.as_view(), name='device-detail'),
    
    # VAPID public key for Web Push
    path('vapid-public-key/', views.get_vapid_public_key, name='vapid-public-key'),
    
    # Notifications
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('stats/', views.notification_stats, name='notification-stats'),
    
    # Recent Updates (Aggregated Notifications)
    path('recent-updates/', RecentUpdatesView.as_view(), name='recent-updates'),
    path('recent-updates/stats/', RecentUpdatesStatsView.as_view(), name='recent-updates-stats'),
    path('recent-updates/type/<str:update_type>/', RecentUpdatesByTypeView.as_view(), name='recent-updates-by-type'),
    
    # Recent Updates - Read Status Management
    path('recent-updates/mark-read/', MarkUpdateAsReadView.as_view(), name='mark-updates-read'),
    path('recent-updates/<str:update_id>/delete/', DeleteUpdateView.as_view(), name='delete-update'),
    path('recent-updates/unread-count/', UnreadCountView.as_view(), name='unread-count'),
    
    # Preferences
    path('preferences/', views.NotificationPreferenceView.as_view(), name='preferences'),
    
    # Testing
    path('test/', views.SendTestNotificationView.as_view(), name='test-notification'),
]
