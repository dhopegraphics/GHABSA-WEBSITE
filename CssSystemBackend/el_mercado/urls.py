"""
El Mercado URL Configuration
============================
URL routing for the multi-vendor marketplace API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    SellerApplicationViewSet,
    SellerViewSet,
    SellerDashboardViewSet,
    ListingViewSet,
    SellerListingViewSet,
    OrderViewSet,
    ReviewViewSet,
    ConversationViewSet,
    PayoutRequestViewSet,
    PayoutAccountViewSet,
    FavoriteViewSet,
    FollowedSellerViewSet,
    DisputeViewSet,
    MarketplaceSettingsViewSet,
    # Seller Auth API Views
    SellerAuthView,
    SellerChangePasswordAPIView,
    SellerPasswordResetRequestView,
    SellerPasswordResetConfirmView,
    # Payout Confirmation API View
    PayoutConfirmationView,
)

from .seller_views import (
    seller_login_view,
    seller_logout_view,
    seller_change_password_view,
    seller_forgot_password_view,
    seller_reset_password_view,
)

app_name = 'el_mercado'

# Create router
router = DefaultRouter()

# Public routes
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'sellers', SellerViewSet, basename='seller')
router.register(r'listings', ListingViewSet, basename='listing')

# Seller application routes
router.register(r'seller-applications', SellerApplicationViewSet, basename='seller-application')

# Seller dashboard routes
router.register(r'seller/dashboard', SellerDashboardViewSet, basename='seller-dashboard')
router.register(r'seller/listings', SellerListingViewSet, basename='seller-listing')
router.register(r'seller/payouts', PayoutRequestViewSet, basename='seller-payout')
router.register(r'seller/payout-accounts', PayoutAccountViewSet, basename='seller-payout-account')

# Order routes
router.register(r'orders', OrderViewSet, basename='order')

# Review routes
router.register(r'reviews', ReviewViewSet, basename='review')

# Communication routes
router.register(r'conversations', ConversationViewSet, basename='conversation')

# User favorites and follows
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'follows', FollowedSellerViewSet, basename='follow')

# Dispute routes
router.register(r'disputes', DisputeViewSet, basename='dispute')

# Platform settings (public)
router.register(r'settings', MarketplaceSettingsViewSet, basename='marketplace-settings')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # ==========================================================================
    # SELLER AUTHENTICATION URLS (Template-based views for browser)
    # ==========================================================================
    path('seller/login/', seller_login_view, name='seller_login'),
    path('seller/logout/', seller_logout_view, name='seller_logout'),
    path('seller/change-password/', seller_change_password_view, name='seller_change_password'),
    path('seller/forgot-password/', seller_forgot_password_view, name='seller_forgot_password'),
    path('seller/reset-password/<str:token>/', seller_reset_password_view, name='seller_reset_password'),
    
    # ==========================================================================
    # SELLER AUTHENTICATION API URLS (For frontend apps - returns JWT tokens)
    # ==========================================================================
    path('seller-auth/login/', SellerAuthView.as_view(), name='seller_auth_login'),
    path('seller-auth/change-password/', SellerChangePasswordAPIView.as_view(), name='seller_auth_change_password'),
    path('seller-auth/forgot-password/', SellerPasswordResetRequestView.as_view(), name='seller_auth_forgot_password'),
    path('seller-auth/reset-password/<str:token>/', SellerPasswordResetConfirmView.as_view(), name='seller_auth_reset_password'),
    
    # ==========================================================================
    # PAYOUT CONFIRMATION API (For President to confirm payouts via email link)
    # ==========================================================================
    path('payout/confirm/', PayoutConfirmationView.as_view(), name='payout_confirm'),
]
