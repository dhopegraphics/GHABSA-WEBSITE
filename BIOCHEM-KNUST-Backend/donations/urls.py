"""
Donation URLs
API routing for donation system
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PublicDonationView,
    DonationInitializeView,
    DonationVerifyView,
    DonationWebhookView,
    DonationViewSet,
    WithdrawalViewSet,
    TransactionViewSet,
    AdminDonationStatsView,
)

from .views_admin import (
    withdrawal_dashboard,
    create_withdrawal,
    approve_withdrawal,
    reject_withdrawal,
    process_gateway_transfer,
    verify_transfer,
    mark_manual_complete,
    bulk_process,
    withdrawal_detail,
    update_withdrawal,
    finalize_transfer_otp,
    sync_pending_transfers,
)

router = DefaultRouter()
router.register(r'donations', DonationViewSet, basename='donation')
router.register(r'withdrawals', WithdrawalViewSet, basename='withdrawal')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    # Public endpoints
    path('public/', PublicDonationView.as_view(), name='public-donations'),
    
    # Payment flow
    path('initialize/', DonationInitializeView.as_view(), name='donation-initialize'),
    path('verify/<str:reference>/', DonationVerifyView.as_view(), name='donation-verify'),
    
    # Webhook
    path('webhook/', DonationWebhookView.as_view(), name='donation-webhook'),
    
    # Admin stats
    path('admin/stats/', AdminDonationStatsView.as_view(), name='admin-donation-stats'),
    
    # Admin Dashboard (Standalone - NOT Django Admin)
    path('admin/dashboard/', withdrawal_dashboard, name='withdrawal-dashboard'),
    path('admin/create/', create_withdrawal, name='withdrawal-create'),
    path('admin/approve/<uuid:withdrawal_id>/', approve_withdrawal, name='withdrawal-approve'),
    path('admin/reject/<uuid:withdrawal_id>/', reject_withdrawal, name='withdrawal-reject'),
    path('admin/process/<uuid:withdrawal_id>/', process_gateway_transfer, name='withdrawal-process'),
    path('admin/verify/<uuid:withdrawal_id>/', verify_transfer, name='withdrawal-verify'),
    path('admin/complete/<uuid:withdrawal_id>/', mark_manual_complete, name='withdrawal-complete'),
    path('admin/bulk-process/', bulk_process, name='withdrawal-bulk-process'),
    path('admin/detail/<uuid:withdrawal_id>/', withdrawal_detail, name='withdrawal-detail'),
    path('admin/update/<uuid:withdrawal_id>/', update_withdrawal, name='withdrawal-update'),
    path('admin/finalize-otp/<uuid:withdrawal_id>/', finalize_transfer_otp, name='withdrawal-finalize-otp'),
    path('admin/sync-transfers/', sync_pending_transfers, name='withdrawal-sync-transfers'),
    
    # ViewSet routes
    path('', include(router.urls)),
]
