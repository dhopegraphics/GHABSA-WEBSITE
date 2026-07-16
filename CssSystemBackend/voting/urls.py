"""
URL Configuration for Voting System
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VotingEventViewSet, VotingCategoryViewSet, CandidateViewSet,
    VoteViewSet, VotingPaymentViewSet, VotingResultViewSet
)
from .payment_views import PaymentViewSet
from .currency_views import get_currencies, convert_currency

app_name = 'voting'

# Create router
router = DefaultRouter()
router.register(r'events', VotingEventViewSet, basename='voting-event')
router.register(r'categories', VotingCategoryViewSet, basename='voting-category')
router.register(r'candidates', CandidateViewSet, basename='candidate')
router.register(r'votes', VoteViewSet, basename='vote')
router.register(r'payments-old', VotingPaymentViewSet, basename='voting-payment-old')  # Deprecated - for backward compatibility only
router.register(r'payments', PaymentViewSet, basename='payment')  # New universal payment system
router.register(r'results', VotingResultViewSet, basename='voting-result')

# Webhooks are now handled by the universal payment system at /api/payments/webhooks/
urlpatterns = [
    path('', include(router.urls)),
    path('currencies/', get_currencies, name='currencies'),
    path('currency/convert/', convert_currency, name='currency-convert'),
]
