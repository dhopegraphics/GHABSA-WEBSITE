from events import views
from django.urls import path

urlpatterns = [
    # Event endpoints
    path("", views.EventListView.as_view(), name="events-list"),
    path("<uuid:event_id>/", views.EventDetailView.as_view(), name="event-detail"),
    
    # RSVP endpoints
    path("<uuid:event_id>/rsvp/", views.EventRSVPView.as_view(), name="event-rsvp"),
    path("<uuid:event_id>/attendees/", views.EventAttendeesView.as_view(), name="event-attendees"),
    
    # Registration endpoints
    path("<uuid:event_id>/register/", views.EventRegistrationView.as_view(), name="event-register"),
    path("<uuid:event_id>/registrations/", views.EventRegistrationsListView.as_view(), name="event-registrations-list"),
    path("<uuid:event_id>/my-registration/", views.UserRegistrationView.as_view(), name="user-registration"),
    
    # Payment Package endpoints
    path("<uuid:event_id>/packages/", views.EventPaymentPackagesView.as_view(), name="event-packages"),
    path("packages/<uuid:package_id>/", views.EventPaymentPackageDetailView.as_view(), name="package-detail"),
    
    # Payment endpoints
    path("payments/initialize/", views.InitializeEventPaymentView.as_view(), name="event-payment-initialize"),
    path("payments/verify/", views.VerifyEventPaymentView.as_view(), name="event-payment-verify"),
    path("payments/webhook/<str:gateway>/", views.EventPaymentWebhookView.as_view(), name="event-payment-webhook"),
    path("payments/my-payments/", views.UserEventPaymentsView.as_view(), name="user-event-payments"),
    path("payments/refund/", views.RequestEventRefundView.as_view(), name="event-refund-request"),
    path("payments/my-refunds/", views.UserRefundsView.as_view(), name="user-event-refunds"),
    path("registrations/<uuid:registration_id>/payments/", views.RegistrationPaymentsView.as_view(), name="registration-payments"),
    
    # Sync Memo (Photo Gallery) endpoints
    path("sync-memo/stats/", views.SyncMemoStatsView.as_view(), name="sync-memo-stats"),
    path("sync-memo/albums/", views.SyncMemoGalleryView.as_view(), name="sync-memo-albums"),
    path("<uuid:event_id>/sync-memo/photos/", views.EventAlbumPhotosView.as_view(), name="event-album-photos"),
    path("<uuid:event_id>/sync-memo/upload/", views.SyncMemoUploadView.as_view(), name="sync-memo-upload"),
    path("sync-memo/photos/<uuid:photo_id>/", views.PhotoDetailView.as_view(), name="photo-detail"),
    path("sync-memo/photos/<uuid:photo_id>/like/", views.PhotoLikeView.as_view(), name="photo-like"),
    path("sync-memo/photos/<uuid:photo_id>/comments/", views.PhotoCommentsView.as_view(), name="photo-comments"),
    path("sync-memo/photos/<uuid:photo_id>/comments/create/", views.PhotoCommentCreateView.as_view(), name="photo-comment-create"),
    path("sync-memo/comments/<uuid:comment_id>/like/", views.CommentLikeView.as_view(), name="comment-like"),
]
