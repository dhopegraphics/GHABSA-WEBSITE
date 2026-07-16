"""
El Mercado Seller Dashboard
===========================
A separate Django Admin site for sellers to manage their store.
Accessible at /seller-dashboard/

Supports TWO authentication methods:
1. Seller's own credentials (email/phone + password) - PRIMARY method
2. Django user authentication (legacy, for sellers with user accounts)
"""

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.db.models import Sum, Count, Q
from django.urls import reverse, path
from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect

from .models import (
    Seller, Listing, ListingImage, ListingVariant,
    MarketplaceOrder, OrderItem, Review, Conversation,
    Message, SellerWallet, WalletTransaction, PayoutRequest,
    SellerPayoutAccount
)
from . import seller_views
from .seller_views import get_current_seller, SELLER_SESSION_KEY


class SellerAdminSite(AdminSite):
    """
    Custom admin site for sellers.
    Supports both seller-specific auth and Django user auth.
    """
    site_header = "El Mercado - Seller Portal"
    site_title = "El Mercado Seller Portal"
    index_title = "Welcome to your Seller Dashboard"
    site_url = None  # Disable "View Site" link
    login_template = 'seller_admin/seller_login.html'
    index_template = 'seller_admin/seller_index.html'
    
    def has_permission(self, request):
        """
        Check if the user has permission to access the seller dashboard.
        Supports two auth methods:
        1. Seller session auth (seller's own credentials)
        2. Django user auth (for sellers with user accounts)
        """
        # Method 1: Check seller session auth (PRIMARY)
        seller = get_current_seller(request)
        if seller and seller.status == 'ACTIVE':
            # Attach seller to request for use in views
            request.seller = seller
            return True
        
        # Method 2: Check Django user auth (LEGACY/FALLBACK)
        if request.user.is_authenticated:
            if hasattr(request.user, 'seller_profile') and \
               request.user.seller_profile.status == 'ACTIVE':
                request.seller = request.user.seller_profile
                return True
        
        return False
    
    def login(self, request, extra_context=None):
        """
        Redirect to our custom seller login page instead of Django admin login.
        """
        # If already authenticated, redirect to index
        if self.has_permission(request):
            return redirect('seller_admin:index')
        
        # Redirect to our custom seller login
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        next_url = request.GET.get('next', '')
        login_url = reverse('el_mercado:seller_login')
        if next_url:
            login_url += f'?next={next_url}'
        return HttpResponseRedirect(login_url)
    
    def logout(self, request, extra_context=None):
        """
        Handle logout for both auth methods.
        """
        from django.contrib.auth import logout as django_logout
        
        # Clear seller session
        seller_views.seller_logout(request)
        
        # Also logout Django user (if any)
        django_logout(request)
        
        # Redirect to seller login
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(reverse('el_mercado:seller_login'))
    
    def _get_seller_from_request(self, request):
        """
        Get the seller from the request (from either auth method).
        """
        if hasattr(request, 'seller'):
            return request.seller
        
        # Try seller session auth
        seller = get_current_seller(request)
        if seller:
            return seller
        
        # Try Django user auth
        if request.user.is_authenticated and hasattr(request.user, 'seller_profile'):
            return request.user.seller_profile
        
        return None
    
    def each_context(self, request):
        """Add extra context for templates"""
        context = super().each_context(request)
        context['site_header'] = self.site_header
        context['FRONTEND_URL'] = getattr(settings, 'FRONTEND_URL', 'https://biochemknust.com')
        # Add seller to context
        seller = self._get_seller_from_request(request)
        if seller:
            context['seller'] = seller
        return context
    
    def index(self, request, extra_context=None):
        """Custom index view with dashboard stats"""
        extra_context = extra_context or {}
        
        # Get seller from either auth method
        seller = self._get_seller_from_request(request)
        
        if seller:
            # Active Listings count
            active_listings = Listing.objects.filter(
                seller=seller,
                status='ACTIVE'
            ).count()
            
            # Pending Orders count
            pending_orders = MarketplaceOrder.objects.filter(
                seller=seller,
                status__in=['PENDING', 'CONFIRMED', 'PROCESSING']
            ).count()
            
            # Wallet Balance
            try:
                wallet_balance = seller.wallet.available_balance
            except:
                wallet_balance = 0
            
            # Total Reviews count
            total_reviews = Review.objects.filter(
                listing__seller=seller
            ).count()
            
            # Average rating
            from django.db.models import Avg
            avg_rating = Review.objects.filter(
                listing__seller=seller
            ).aggregate(avg=Avg('rating'))['avg'] or 0
            
            # Recent orders
            recent_orders = MarketplaceOrder.objects.filter(
                seller=seller
            ).order_by('-created_at')[:5]
            
            # Unread messages
            unread_messages = Conversation.objects.filter(
                seller=seller
            ).aggregate(total=Sum('seller_unread_count'))['total'] or 0
            
            extra_context.update({
                'active_listings': active_listings,
                'pending_orders': pending_orders,
                'wallet_balance': wallet_balance,
                'total_reviews': total_reviews,
                'avg_rating': round(avg_rating, 1),
                'recent_orders': recent_orders,
                'unread_messages': unread_messages,
                'seller': seller,
            })
        
        return super().index(request, extra_context)
    
    def get_urls(self):
        """Add custom URLs for seller dashboard views"""
        urls = super().get_urls()
        custom_urls = [
            path('actions/add-payout-account/', 
                 self.admin_view(seller_views.add_payout_account),
                 name='add_payout_account'),
            path('actions/request-payout/', 
                 self.admin_view(seller_views.request_payout),
                 name='request_payout'),
            path('actions/pause-store/', 
                 self.admin_view(seller_views.pause_store),
                 name='pause_store'),
            path('actions/delete-store/', 
                 self.admin_view(seller_views.delete_store_request),
                 name='delete_store'),
            path('actions/toggle-auto-accept/',
                 self.admin_view(seller_views.toggle_auto_accept),
                 name='toggle_auto_accept'),
            # Conversation messages
            path('el_mercado/conversation/<uuid:conversation_id>/send-message/',
                 self.admin_view(seller_views.send_message),
                 name='send_message'),
            path('el_mercado/conversation/<uuid:conversation_id>/messages/',
                 self.admin_view(seller_views.get_conversation_messages),
                 name='get_conversation_messages'),
            # Start/find conversation from order
            path('el_mercado/order/<uuid:order_id>/message-customer/',
                 self.admin_view(seller_views.start_conversation_with_customer),
                 name='start_conversation_with_customer'),
            # Order status update actions
            path('el_mercado/order/<uuid:order_id>/accept/',
                 self.admin_view(seller_views.accept_order),
                 name='accept_order'),
            path('el_mercado/order/<uuid:order_id>/decline/',
                 self.admin_view(seller_views.decline_order),
                 name='decline_order'),
            path('el_mercado/order/<uuid:order_id>/ship/',
                 self.admin_view(seller_views.ship_order),
                 name='ship_order'),
            path('el_mercado/order/<uuid:order_id>/verify-delivery/',
                 self.admin_view(seller_views.verify_delivery),
                 name='verify_delivery'),
            path('el_mercado/order/<uuid:order_id>/mark-delivered/',
                 self.admin_view(seller_views.mark_delivered),
                 name='mark_delivered'),
            path('el_mercado/order/<uuid:order_id>/complete/',
                 self.admin_view(seller_views.complete_order),
                 name='complete_order'),
            path('el_mercado/order/<uuid:order_id>/save-notes/',
                 self.admin_view(seller_views.save_order_notes),
                 name='save_order_notes'),
            # Transaction history and payout settings
            path('wallet/transactions/',
                 self.admin_view(seller_views.transaction_history),
                 name='wallet_transactions'),
            path('wallet/payout-settings/',
                 self.admin_view(seller_views.payout_settings),
                 name='payout_settings'),
            # Earnings chart data API
            path('api/earnings-data/',
                 self.admin_view(seller_views.earnings_chart_data),
                 name='earnings_chart_data'),
            # Review reply
            path('el_mercado/review/<uuid:review_id>/reply/',
                 self.admin_view(seller_views.reply_to_review),
                 name='reply_to_review'),
            # Payout account actions
            path('el_mercado/payout-account/<uuid:account_id>/set-primary/',
                 self.admin_view(seller_views.set_primary_payout_account),
                 name='set_primary_payout_account'),
            # Payout request actions
            path('el_mercado/payout-request/<uuid:payout_id>/cancel/',
                 self.admin_view(seller_views.cancel_payout_request),
                 name='cancel_payout_request'),
        ]
        return custom_urls + urls


# Create the seller admin site instance
seller_admin_site = SellerAdminSite(name='seller_admin')


# =============================================================================
# BASE SELLER MODEL ADMIN
# =============================================================================

class SellerBaseModelAdmin(admin.ModelAdmin):
    """
    Base ModelAdmin for seller dashboard.
    Overrides permission methods to work with seller session auth.
    Since SellerAdminSite.has_permission() already handles authentication,
    we grant all permissions to authenticated sellers here.
    """
    
    def has_module_permission(self, request):
        """Allow access to the module if seller is authenticated"""
        return hasattr(request, 'seller') and request.seller is not None
    
    def has_view_permission(self, request, obj=None):
        """Allow viewing if seller is authenticated"""
        return hasattr(request, 'seller') and request.seller is not None
    
    def has_change_permission(self, request, obj=None):
        """Allow changing if seller is authenticated"""
        return hasattr(request, 'seller') and request.seller is not None
    
    def has_add_permission(self, request):
        """Allow adding if seller is authenticated"""
        return hasattr(request, 'seller') and request.seller is not None
    
    def has_delete_permission(self, request, obj=None):
        """Allow deleting if seller is authenticated"""
        return hasattr(request, 'seller') and request.seller is not None
    
    def _get_seller(self, request):
        """Helper to get the seller from the request"""
        if hasattr(request, 'seller'):
            return request.seller
        # Fallback: try to get from user
        if request.user.is_authenticated and hasattr(request.user, 'seller_profile'):
            return request.user.seller_profile
        return None
    
    def log_addition(self, request, obj, message):
        """
        Override to skip admin logging when seller has no Django user.
        Django's admin log requires a user_id which may not exist for
        sellers using the separate authentication system.
        """
        if request.user.is_authenticated and request.user.pk:
            return super().log_addition(request, obj, message)
        # Skip logging for sellers without Django user accounts
        return None
    
    def log_change(self, request, obj, message):
        """
        Override to skip admin logging when seller has no Django user.
        """
        if request.user.is_authenticated and request.user.pk:
            return super().log_change(request, obj, message)
        # Skip logging for sellers without Django user accounts
        return None
    
    def log_deletion(self, request, obj, object_repr):
        """
        Override to skip admin logging when seller has no Django user.
        """
        if request.user.is_authenticated and request.user.pk:
            return super().log_deletion(request, obj, object_repr)
        # Skip logging for sellers without Django user accounts
        return None


# =============================================================================
# INLINE ADMINS
# =============================================================================

class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1
    fields = ['image', 'alt_text', 'display_order']


class ListingVariantInline(admin.TabularInline):
    model = ListingVariant
    extra = 0
    fields = ['name', 'sku', 'price', 'stock_quantity', 'is_active']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['listing', 'variant', 'quantity', 'unit_price', 'total_price']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


# =============================================================================
# SELLER LISTING ADMIN
# =============================================================================

class SellerListingAdmin(SellerBaseModelAdmin):
    """
    Listing management for sellers - they can only see/edit their own listings.
    """
    change_list_template = 'seller_admin/el_mercado/listing/change_list.html'
    change_form_template = 'seller_admin/el_mercado/listing/change_form.html'
    delete_confirmation_template = 'seller_admin/el_mercado/listing/delete_confirmation.html'
    delete_selected_confirmation_template = 'seller_admin/el_mercado/listing/delete_selected_confirmation.html'
    
    list_display = [
        'title', 'listing_type', 'status_badge', 'price', 
        'stock_quantity', 'order_count', 'average_rating', 'created_at'
    ]
    list_filter = ['status', 'listing_type', 'category', 'condition']
    search_fields = ['title', 'description']
    readonly_fields = [
        'id', 'slug', 'seller', 'view_count', 'favorite_count', 'order_count',
        'average_rating', 'review_count', 'created_at', 'updated_at', 'published_at'
    ]
    inlines = [ListingImageInline, ListingVariantInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'slug', 'description', 'listing_type')
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_at_price', 'currency')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'track_inventory', 'allow_backorder', 'low_stock_threshold')
        }),
        ('Condition & Shipping', {
            'fields': ('condition', 'requires_shipping', 'weight', 'shipping_info')
        }),
        ('Images', {
            'fields': ('main_image',)
        }),
        ('Status', {
            'fields': ('status', 'rejection_reason', 'published_at')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('view_count', 'favorite_count', 'order_count', 'average_rating', 'review_count'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Only show listings belonging to the current seller"""
        qs = super().get_queryset(request)
        seller = self._get_seller(request)
        if seller:
            return qs.filter(seller=seller)
        return qs.none()
    
    def changelist_view(self, request, extra_context=None):
        """Add listing stats to the changelist context"""
        extra_context = extra_context or {}
        
        seller = self._get_seller(request)
        if seller:
            
            # Active listings count
            active_listings = Listing.objects.filter(
                seller=seller,
                status='ACTIVE'
            ).count()
            
            # Pending review count
            pending_review = Listing.objects.filter(
                seller=seller,
                status='PENDING_REVIEW'
            ).count()
            
            # Total views across all listings
            total_views = Listing.objects.filter(
                seller=seller
            ).aggregate(total=Sum('view_count'))['total'] or 0
            
            extra_context['active_listings'] = active_listings
            extra_context['pending_review'] = pending_review
            extra_context['total_views'] = total_views
        
        return super().changelist_view(request, extra_context)
    
    def save_model(self, request, obj, form, change):
        """Automatically set the seller to the current seller profile"""
        if not change:  # Creating new listing
            obj.seller = self._get_seller(request)
        super().save_model(request, obj, form, change)
    
    def status_badge(self, obj):
        colors = {
            'DRAFT': '#95a5a6',
            'PENDING_REVIEW': '#f39c12',
            'ACTIVE': '#27ae60',
            'REJECTED': '#e74c3c',
            'SOLD_OUT': '#e67e22',
            'ARCHIVED': '#7f8c8d',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# =============================================================================
# SELLER ORDER ADMIN
# =============================================================================

class SellerOrderAdmin(SellerBaseModelAdmin):
    """
    Order management for sellers - they can only see orders for their store.
    """
    change_list_template = 'seller_admin/el_mercado/marketplaceorder/change_list.html'
    change_form_template = 'seller_admin/el_mercado/marketplaceorder/change_form.html'
    
    list_display = [
        'order_number', 'buyer_name', 'status_badge', 'payment_status_badge',
        'total_amount', 'seller_earnings', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'buyer__first_name', 'buyer__last_name']
    readonly_fields = [
        'id', 'order_number', 'seller', 'buyer', 'subtotal', 'platform_commission',
        'seller_earnings', 'total_amount', 'payment_status', 'payment_reference',
        'paid_at', 'created_at', 'updated_at', 'shipped_at', 'delivered_at',
        'funds_released', 'funds_released_at', 'status_history'
    ]
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'buyer', 'status')
        }),
        ('Financials', {
            'fields': ('subtotal', 'platform_commission', 'seller_earnings', 'total_amount', 'currency')
        }),
        ('Payment', {
            'fields': ('payment_status', 'payment_reference', 'paid_at')
        }),
        ('Shipping', {
            'fields': ('shipping_name', 'shipping_phone', 'shipping_address_line_1', 
                      'shipping_city', 'shipping_region', 'tracking_number', 'tracking_url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'shipped_at', 'delivered_at', 'funds_released_at'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('seller_notes', 'buyer_notes'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Only show orders for the current seller"""
        qs = super().get_queryset(request)
        seller = self._get_seller(request)
        if seller:
            return qs.filter(seller=seller)
        return qs.none()
    
    def changelist_view(self, request, extra_context=None):
        """Add order stats to the changelist context"""
        extra_context = extra_context or {}
        
        seller = self._get_seller(request)
        if seller:
            
            # Pending orders count
            pending_count = MarketplaceOrder.objects.filter(
                seller=seller,
                status='PENDING'
            ).count()
            
            # Processing orders count
            processing_count = MarketplaceOrder.objects.filter(
                seller=seller,
                status='PROCESSING'
            ).count()
            
            # Shipped orders count
            shipped_count = MarketplaceOrder.objects.filter(
                seller=seller,
                status='SHIPPED'
            ).count()
            
            # Completed orders count
            completed_count = MarketplaceOrder.objects.filter(
                seller=seller,
                status='COMPLETED'
            ).count()
            
            extra_context['pending_count'] = pending_count
            extra_context['processing_count'] = processing_count
            extra_context['shipped_count'] = shipped_count
            extra_context['completed_count'] = completed_count
        
        return super().changelist_view(request, extra_context)
    
    def buyer_name(self, obj):
        return f"{obj.buyer.first_name} {obj.buyer.last_name}"
    buyer_name.short_description = 'Buyer'
    
    def status_badge(self, obj):
        colors = {
            'PENDING': '#f39c12',
            'AWAITING_PAYMENT': '#3498db',
            'PAID': '#27ae60',
            'PROCESSING': '#9b59b6',
            'SHIPPED': '#1abc9c',
            'DELIVERED': '#2ecc71',
            'COMPLETED': '#27ae60',
            'CANCELLED': '#e74c3c',
            'REFUNDED': '#95a5a6',
            'DISPUTED': '#e74c3c',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def payment_status_badge(self, obj):
        colors = {
            'PENDING': '#f39c12',
            'PAID': '#27ae60',
            'FAILED': '#e74c3c',
            'REFUNDED': '#95a5a6',
            'PARTIALLY_REFUNDED': '#e67e22',
        }
        color = colors.get(obj.payment_status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Payment'
    
    def has_add_permission(self, request):
        """Sellers cannot create orders manually"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Sellers cannot delete orders"""
        return False


# =============================================================================
# SELLER REVIEW ADMIN (Read-only)
# =============================================================================

class SellerReviewAdmin(SellerBaseModelAdmin):
    """
    Reviews for the seller - read only, but seller can respond.
    """
    change_list_template = 'seller_admin/el_mercado/review/change_list.html'
    change_form_template = 'seller_admin/el_mercado/review/change_form.html'
    
    list_display = ['reviewer_name', 'review_type', 'rating_stars', 'title', 'is_approved', 'created_at']
    list_filter = ['review_type', 'rating', 'is_approved', 'created_at']
    search_fields = ['title', 'content', 'reviewer__first_name']
    readonly_fields = [
        'id', 'reviewer', 'seller', 'listing', 'order', 'review_type',
        'rating', 'title', 'content', 'is_verified_purchase', 'is_approved',
        'helpful_count', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Review Info', {
            'fields': ('reviewer', 'review_type', 'listing', 'order', 'rating', 'title', 'content')
        }),
        ('Status', {
            'fields': ('is_verified_purchase', 'is_approved', 'helpful_count')
        }),
        ('Your Response', {
            'fields': ('seller_response', 'seller_responded_at')
        }),
    )
    
    def get_queryset(self, request):
        """Only show reviews for the current seller (either direct seller reviews or listing reviews)"""
        qs = super().get_queryset(request)
        seller = self._get_seller(request)
        if seller:
            # Include reviews where seller is directly set OR reviews for listings owned by this seller
            return qs.filter(
                Q(seller=seller) | Q(listing__seller=seller)
            ).distinct()
        return qs.none()
    
    def changelist_view(self, request, extra_context=None):
        """Add review statistics to context"""
        extra_context = extra_context or {}
        seller = self._get_seller(request)
        if seller:
            # Include all reviews (direct seller or listing-based) for this seller
            reviews = Review.objects.filter(
                Q(seller=seller) | Q(listing__seller=seller),
                is_approved=True
            ).distinct()
            
            # Calculate statistics
            from django.db.models import Avg
            total_reviews = reviews.count()
            avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
            
            # Rating breakdown
            rating_counts = {i: reviews.filter(rating=i).count() for i in range(1, 6)}
            
            # Calculate percentages
            if total_reviews > 0:
                rating_percentages = {k: (v / total_reviews * 100) for k, v in rating_counts.items()}
            else:
                rating_percentages = {i: 0 for i in range(1, 6)}
            
            # Replies count
            replied = reviews.exclude(seller_response='').exclude(seller_response__isnull=True).count()
            awaiting_reply = total_reviews - replied
            
            extra_context.update({
                'review_stats': {
                    'average_rating': round(avg_rating, 1),
                    'total_reviews': total_reviews,
                    'rating_counts': rating_counts,
                    'rating_percentages': rating_percentages,
                    'replied_count': replied,
                    'awaiting_reply': awaiting_reply,
                }
            })
        return super().changelist_view(request, extra_context)
    
    def reviewer_name(self, obj):
        return f"{obj.reviewer.first_name} {obj.reviewer.last_name}"
    reviewer_name.short_description = 'Reviewer'
    
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: #f1c40f; font-size: 14px;">{}</span>', stars)
    rating_stars.short_description = 'Rating'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# =============================================================================
# SELLER WALLET ADMIN (Read-only)
# =============================================================================

class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = ['transaction_type', 'amount', 'balance_after', 'description', 'reference_id', 'created_at']
    can_delete = False
    max_num = 20
    ordering = ['-created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


class SellerWalletAdmin(SellerBaseModelAdmin):
    """
    Wallet view for sellers - read only.
    """
    change_list_template = 'seller_admin/el_mercado/sellerwallet/change_list.html'
    
    list_display = ['seller', 'available_balance', 'pending_balance', 'total_earned', 'currency']
    readonly_fields = [
        'id', 'seller', 'available_balance', 'pending_balance', 'total_earned',
        'total_withdrawn', 'total_fees_paid', 'currency', 'created_at', 'updated_at'
    ]
    inlines = [WalletTransactionInline]
    
    fieldsets = (
        ('Balances', {
            'fields': ('available_balance', 'pending_balance', 'currency')
        }),
        ('Lifetime Stats', {
            'fields': ('total_earned', 'total_withdrawn', 'total_fees_paid')
        }),
        ('Payout Settings', {
            'fields': ('minimum_payout_amount', 'auto_payout_enabled', 'auto_payout_threshold')
        }),
    )
    
    def get_queryset(self, request):
        """Only show the current seller's wallet"""
        qs = super().get_queryset(request)
        seller = self._get_seller(request)
        if seller:
            return qs.filter(seller=seller)
        return qs.none()
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# =============================================================================
# PAYOUT REQUEST ADMIN
# =============================================================================

class SellerPayoutRequestAdmin(SellerBaseModelAdmin):
    """
    Payout requests for sellers.
    """
    change_list_template = 'seller_admin/el_mercado/payoutrequest/change_list.html'
    change_form_template = 'seller_admin/el_mercado/payoutrequest/change_form.html'
    
    list_display = ['id_short', 'amount', 'status_badge', 'payout_method', 'created_at']
    list_filter = ['status', 'created_at']
    readonly_fields = [
        'id', 'wallet', 'amount', 'currency', 'status',
        'processed_at', 'completed_at', 'gateway_reference', 'status_message',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Request Info', {
            'fields': ('amount', 'currency', 'payout_method')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'bank_code', 'account_number', 'account_name'),
            'classes': ('collapse',)
        }),
        ('Mobile Money', {
            'fields': ('mobile_money_provider', 'mobile_money_number'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'status_message', 'processed_at', 'completed_at', 'gateway_reference')
        }),
    )
    
    def get_queryset(self, request):
        """Only show the current seller's payout requests"""
        qs = super().get_queryset(request)
        seller = self._get_seller(request)
        if seller:
            return qs.filter(wallet__seller=seller)
        return qs.none()
    
    def changelist_view(self, request, extra_context=None):
        """Add payout statistics to context"""
        extra_context = extra_context or {}
        
        seller = self._get_seller(request)
        if seller:
            
            try:
                wallet = seller.wallet
                extra_context['available_balance'] = wallet.available_balance
                extra_context['pending_balance'] = wallet.pending_balance
                extra_context['total_earned'] = wallet.total_earned
                extra_context['total_withdrawn'] = wallet.total_withdrawn
                extra_context['currency'] = wallet.currency
            except SellerWallet.DoesNotExist:
                extra_context['available_balance'] = 0
                extra_context['pending_balance'] = 0
                extra_context['total_earned'] = 0
                extra_context['total_withdrawn'] = 0
                extra_context['currency'] = 'GHS'
            
            # Payout stats
            payouts = PayoutRequest.objects.filter(wallet__seller=seller)
            extra_context['pending_payouts'] = payouts.filter(status='PENDING').count()
            extra_context['processing_payouts'] = payouts.filter(status='PROCESSING').count()
            extra_context['completed_payouts'] = payouts.filter(status='COMPLETED').count()
            extra_context['failed_payouts'] = payouts.filter(status='FAILED').count()
        
        return super().changelist_view(request, extra_context)
    
    def add_view(self, request, form_url='', extra_context=None):
        """Add extra context for the add form"""
        extra_context = extra_context or {}
        seller = self._get_seller(request)
        if seller:
            # Get marketplace settings for dynamic fees
            from .models import MarketplaceSettings
            settings = MarketplaceSettings.get_settings()
            extra_context['processing_fee_percentage'] = float(settings.payout_processing_fee_percentage)
            extra_context['min_payout'] = float(settings.minimum_payout_amount)
            
            # Get seller's payout accounts
            extra_context['payout_accounts'] = SellerPayoutAccount.objects.filter(
                seller=seller
            ).order_by('-is_default', '-created_at')
            # Get wallet balance
            try:
                wallet = seller.wallet
                extra_context['wallet'] = wallet
                extra_context['available_balance'] = wallet.available_balance
                extra_context['pending_balance'] = wallet.pending_balance
            except SellerWallet.DoesNotExist:
                extra_context['available_balance'] = 0
                extra_context['pending_balance'] = 0
        return super().add_view(request, form_url, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Add extra context for viewing/editing payout details"""
        extra_context = extra_context or {}
        seller = self._get_seller(request)
        
        try:
            payout = PayoutRequest.objects.get(pk=object_id)
            extra_context['payout'] = payout
            extra_context['can_cancel'] = payout.status == 'PENDING'
            
            # Get marketplace settings for fee info
            from .models import MarketplaceSettings
            settings = MarketplaceSettings.get_settings()
            extra_context['processing_fee_percentage'] = float(settings.payout_processing_fee_percentage)
            
            # Get wallet balance
            if seller:
                try:
                    wallet = seller.wallet
                    extra_context['available_balance'] = wallet.available_balance
                except SellerWallet.DoesNotExist:
                    extra_context['available_balance'] = 0
        except PayoutRequest.DoesNotExist:
            pass
        
        return super().change_view(request, object_id, form_url, extra_context)
    
    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def status_badge(self, obj):
        colors = {
            'PENDING': '#f39c12',
            'PROCESSING': '#3498db',
            'COMPLETED': '#27ae60',
            'FAILED': '#e74c3c',
            'CANCELLED': '#95a5a6',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        """Set wallet on new payout request"""
        if not change:
            seller = self._get_seller(request)
            if seller:
                obj.wallet = seller.wallet
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        """Can only delete pending requests"""
        if obj and obj.status != 'PENDING':
            return False
        return True


# =============================================================================
# PAYOUT ACCOUNT ADMIN
# =============================================================================

class SellerPayoutAccountAdmin(SellerBaseModelAdmin):
    """
    Payout accounts for sellers.
    """
    change_list_template = 'seller_admin/el_mercado/sellerpayoutaccount/change_list.html'
    change_form_template = 'seller_admin/el_mercado/sellerpayoutaccount/change_form.html'
    delete_confirmation_template = 'seller_admin/el_mercado/sellerpayoutaccount/delete_confirmation.html'
    
    list_display = ['account_name', 'account_type', 'bank_name', 'is_default', 'is_verified']
    list_filter = ['account_type', 'is_verified']
    readonly_fields = ['id', 'seller', 'is_verified', 'created_at']
    
    fieldsets = (
        ('Account Info', {
            'fields': ('account_type', 'is_default')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'bank_code', 'account_number', 'account_name'),
            'classes': ('collapse',)
        }),
        ('Mobile Money', {
            'fields': ('mobile_money_provider', 'mobile_money_number', 'mobile_money_name'),
            'classes': ('collapse',)
        }),
        ('Verification', {
            'fields': ('is_verified',)
        }),
    )
    
    def get_queryset(self, request):
        """Only show the current seller's payout accounts"""
        qs = super().get_queryset(request)
        seller = self._get_seller(request)
        if seller:
            return qs.filter(seller=seller)
        return qs.none()
    
    def add_view(self, request, form_url='', extra_context=None):
        """Handle custom form submission for adding payout account"""
        from django.contrib import messages
        
        if request.method == 'POST':
            seller = self._get_seller(request)
            if not seller:
                messages.error(request, "Seller not found.")
                return redirect('seller_admin:el_mercado_sellerpayoutaccount_changelist')
            
            account_type = request.POST.get('account_type', 'BANK')
            is_default = request.POST.get('is_default') == 'on'
            
            try:
                if account_type == 'BANK':
                    bank_name = request.POST.get('bank_name', '').strip()
                    account_number = request.POST.get('account_number', '').strip()
                    account_name = request.POST.get('account_name', '').strip()
                    bank_code = request.POST.get('bank_code', '').strip()
                    
                    if not bank_name or not account_number or not account_name:
                        messages.error(request, "Please fill in all required bank details.")
                        return super().add_view(request, form_url, extra_context)
                    
                    account = SellerPayoutAccount.objects.create(
                        seller=seller,
                        account_type='BANK',
                        bank_name=bank_name,
                        bank_code=bank_code,
                        account_number=account_number,
                        account_name=account_name,
                        is_default=is_default,
                    )
                    
                else:  # MOBILE_MONEY
                    provider = request.POST.get('mobile_money_provider', '').strip()
                    momo_number = request.POST.get('mobile_money_number', '').strip()
                    momo_name = request.POST.get('mobile_money_name', '').strip()
                    
                    if not provider or not momo_number or not momo_name:
                        messages.error(request, "Please fill in all required mobile money details.")
                        return super().add_view(request, form_url, extra_context)
                    
                    account = SellerPayoutAccount.objects.create(
                        seller=seller,
                        account_type='MOBILE_MONEY',
                        mobile_money_provider=provider,
                        mobile_money_number=momo_number,
                        mobile_money_name=momo_name,
                        is_default=is_default,
                    )
                
                # If is_default, unset other defaults
                if is_default:
                    SellerPayoutAccount.objects.filter(
                        seller=seller
                    ).exclude(pk=account.pk).update(is_default=False)
                
                messages.success(request, "Payout account added successfully!")
                return redirect('seller_admin:el_mercado_sellerpayoutaccount_changelist')
                
            except Exception as e:
                messages.error(request, f"Error adding account: {str(e)}")
                return super().add_view(request, form_url, extra_context)
        
        # GET request - render the form
        extra_context = extra_context or {}
        extra_context['add'] = True
        return super().add_view(request, form_url, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Handle custom form submission for editing payout account"""
        from django.contrib import messages
        
        seller = self._get_seller(request)
        
        # Get the object
        try:
            obj = SellerPayoutAccount.objects.get(pk=object_id, seller=seller)
        except SellerPayoutAccount.DoesNotExist:
            messages.error(request, "Account not found.")
            return redirect('seller_admin:el_mercado_sellerpayoutaccount_changelist')
        
        if request.method == 'POST':
            account_type = request.POST.get('account_type', 'BANK')
            is_default = request.POST.get('is_default') == 'on'
            
            try:
                obj.account_type = account_type
                obj.is_default = is_default
                
                if account_type == 'BANK':
                    obj.bank_name = request.POST.get('bank_name', '').strip()
                    obj.account_number = request.POST.get('account_number', '').strip()
                    obj.account_name = request.POST.get('account_name', '').strip()
                    obj.bank_code = request.POST.get('bank_code', '').strip()
                    # Clear mobile money fields
                    obj.mobile_money_provider = ''
                    obj.mobile_money_number = ''
                    obj.mobile_money_name = ''
                    
                    if not obj.bank_name or not obj.account_number or not obj.account_name:
                        messages.error(request, "Please fill in all required bank details.")
                        extra_context = extra_context or {}
                        extra_context['original'] = obj
                        return super().change_view(request, object_id, form_url, extra_context)
                    
                else:  # MOBILE_MONEY
                    obj.mobile_money_provider = request.POST.get('mobile_money_provider', '').strip()
                    obj.mobile_money_number = request.POST.get('mobile_money_number', '').strip()
                    obj.mobile_money_name = request.POST.get('mobile_money_name', '').strip()
                    # Clear bank fields
                    obj.bank_name = ''
                    obj.bank_code = ''
                    obj.account_number = ''
                    obj.account_name = ''
                    
                    if not obj.mobile_money_provider or not obj.mobile_money_number or not obj.mobile_money_name:
                        messages.error(request, "Please fill in all required mobile money details.")
                        extra_context = extra_context or {}
                        extra_context['original'] = obj
                        return super().change_view(request, object_id, form_url, extra_context)
                
                obj.save()
                
                # If is_default, unset other defaults
                if is_default:
                    SellerPayoutAccount.objects.filter(
                        seller=seller
                    ).exclude(pk=obj.pk).update(is_default=False)
                
                messages.success(request, "Payout account updated successfully!")
                return redirect('seller_admin:el_mercado_sellerpayoutaccount_changelist')
                
            except Exception as e:
                messages.error(request, f"Error updating account: {str(e)}")
        
        # GET request - render the form with existing data
        extra_context = extra_context or {}
        extra_context['original'] = obj
        extra_context['add'] = False
        return super().change_view(request, object_id, form_url, extra_context)
    
    def delete_view(self, request, object_id, extra_context=None):
        """Custom delete view with proper template context"""
        from django.contrib import messages
        
        seller = self._get_seller(request)
        
        # Get the object
        try:
            obj = SellerPayoutAccount.objects.get(pk=object_id, seller=seller)
        except SellerPayoutAccount.DoesNotExist:
            messages.error(request, "Account not found.")
            return redirect('seller_admin:el_mercado_sellerpayoutaccount_changelist')
        
        if request.method == 'POST':
            try:
                account_name = obj.account_name or obj.mobile_money_name or "Account"
                obj.delete()
                messages.success(request, f"Payout account '{account_name}' deleted successfully!")
                return redirect('seller_admin:el_mercado_sellerpayoutaccount_changelist')
            except Exception as e:
                messages.error(request, f"Error deleting account: {str(e)}")
                return redirect('seller_admin:el_mercado_sellerpayoutaccount_changelist')
        
        # GET request - show confirmation
        extra_context = extra_context or {}
        extra_context['object'] = obj
        return super().delete_view(request, object_id, extra_context)
    
    def save_model(self, request, obj, form, change):
        """Set seller on new payout account"""
        if not change:
            obj.seller = self._get_seller(request)
        super().save_model(request, obj, form, change)


# =============================================================================
# CONVERSATION ADMIN
# =============================================================================

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['sender_type', 'sender_user', 'content', 'is_read', 'created_at']
    can_delete = False
    ordering = ['created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


class SellerConversationAdmin(SellerBaseModelAdmin):
    """
    Conversations with buyers.
    """
    change_list_template = 'seller_admin/el_mercado/conversation/change_list.html'
    change_form_template = 'seller_admin/el_mercado/conversation/change_form.html'
    
    list_display = ['buyer_name', 'listing_title', 'seller_unread_count', 'last_message_at']
    list_filter = ['created_at']
    search_fields = ['buyer__first_name', 'buyer__last_name', 'listing__title']
    readonly_fields = ['id', 'buyer', 'seller', 'listing', 'order', 'created_at', 'last_message_at']
    inlines = [MessageInline]
    
    def get_queryset(self, request):
        """Only show the current seller's conversations"""
        qs = super().get_queryset(request)
        seller = self._get_seller(request)
        if seller:
            return qs.filter(seller=seller)
        return qs.none()
    
    def changelist_view(self, request, extra_context=None):
        """Add stats to the changelist context"""
        extra_context = extra_context or {}
        
        seller = self._get_seller(request)
        if seller:
            today = timezone.now().date()
            today_start = timezone.make_aware(
                timezone.datetime.combine(today, timezone.datetime.min.time())
            )
            
            # Total unread messages for seller
            total_unread = Conversation.objects.filter(
                seller=seller
            ).aggregate(total=Sum('seller_unread_count'))['total'] or 0
            
            # Conversations responded to today (seller sent a message today)
            responded_today = Message.objects.filter(
                conversation__seller=seller,
                sender_type='SELLER',
                created_at__gte=today_start
            ).values('conversation').distinct().count()
            
            # Average response time calculation
            # Get conversations where buyer sent first and seller replied
            from django.db.models import F, ExpressionWrapper, DurationField
            
            # Simplified: count conversations with recent seller responses
            avg_response = "< 1hr"  # Default placeholder
            
            extra_context['total_unread'] = total_unread
            extra_context['responded_today'] = responded_today
            extra_context['avg_response_time'] = avg_response
        
        return super().changelist_view(request, extra_context)
    
    def buyer_name(self, obj):
        return f"{obj.buyer.first_name} {obj.buyer.last_name}"
    buyer_name.short_description = 'Buyer'
    
    def listing_title(self, obj):
        return obj.listing.title if obj.listing else '-'
    listing_title.short_description = 'Listing'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# =============================================================================
# SELLER PROFILE ADMIN (Own Profile)
# =============================================================================

class SellerProfileAdmin(SellerBaseModelAdmin):
    """
    Seller's own profile management.
    """
    change_form_template = 'seller_admin/el_mercado/seller/change_form.html'
    change_list_template = 'seller_admin/el_mercado/seller/change_list.html'
    
    list_display = ['display_name', 'seller_type', 'status', 'average_rating', 'total_sales']
    readonly_fields = [
        'id', 'slug', 'application', 'user', 'seller_type', 'status', 'status_reason',
        'average_rating', 'total_reviews', 'total_sales', 'commission_rate',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Profile', {
            'fields': ('display_name', 'slug', 'seller_type', 'status')
        }),
        ('Contact', {
            'fields': ('email', 'phone')
        }),
        ('Branding', {
            'fields': ('logo', 'banner', 'description')
        }),
        ('Social Links', {
            'fields': ('website', 'instagram', 'twitter', 'facebook')
        }),
        ('Store Policies', {
            'fields': ('shipping_policy', 'return_policy')
        }),
        ('Statistics', {
            'fields': ('average_rating', 'total_reviews', 'total_sales', 'commission_rate'),
            'classes': ('collapse',)
        }),
        ('Store Settings', {
            'fields': ('auto_accept_orders', 'vacation_mode', 'vacation_message')
        }),
        ('Notifications', {
            'fields': ('notify_new_orders', 'notify_messages', 'notify_reviews', 
                      'notify_low_stock', 'notify_payouts'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Only show the current seller's profile"""
        qs = super().get_queryset(request)
        seller = self._get_seller(request)
        if seller:
            return qs.filter(id=seller.id)
        return qs.none()
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Handle multiple form submissions for different settings sections"""
        from django.contrib import messages
        
        if request.method == 'POST':
            seller = self._get_seller(request)
            form_type = request.POST.get('form_type')
            
            if form_type == 'store_info':
                # Handle store information update
                seller.display_name = request.POST.get('display_name', seller.display_name)
                seller.description = request.POST.get('description', seller.description)
                seller.email = request.POST.get('email', seller.email)
                seller.phone = request.POST.get('phone', seller.phone)
                
                # Handle file uploads
                if 'logo' in request.FILES:
                    seller.logo = request.FILES['logo']
                if 'banner' in request.FILES:
                    seller.banner = request.FILES['banner']
                
                seller.save(update_fields=[
                    'display_name', 'description', 'email', 'phone', 
                    'logo', 'banner', 'updated_at'
                ])
                messages.success(request, 'Store information updated successfully!')
                
            elif form_type == 'policies':
                # Handle store policies update
                seller.shipping_policy = request.POST.get('shipping_policy', seller.shipping_policy)
                seller.return_policy = request.POST.get('return_policy', seller.return_policy)
                seller.save(update_fields=['shipping_policy', 'return_policy', 'updated_at'])
                messages.success(request, 'Store policies saved successfully!')
                
            elif form_type == 'social_links':
                # Handle social links update
                seller.instagram = request.POST.get('instagram', '').strip()
                seller.twitter = request.POST.get('twitter', '').strip()
                seller.facebook = request.POST.get('facebook', '').strip()
                seller.website = request.POST.get('website', '').strip() or None
                seller.save(update_fields=['instagram', 'twitter', 'facebook', 'website', 'updated_at'])
                messages.success(request, 'Social links saved successfully!')
                
            elif form_type == 'order_settings':
                # Handle order settings update
                seller.auto_accept_orders = 'auto_accept_orders' in request.POST
                seller.save(update_fields=['auto_accept_orders', 'updated_at'])
                messages.success(request, 'Order settings saved successfully!')
                
            elif form_type == 'notifications':
                # Handle notification preferences update
                seller.notify_new_orders = 'notify_new_orders' in request.POST
                seller.notify_messages = 'notify_messages' in request.POST
                seller.notify_reviews = 'notify_reviews' in request.POST
                seller.notify_low_stock = 'notify_low_stock' in request.POST
                seller.notify_payouts = 'notify_payouts' in request.POST
                seller.save(update_fields=[
                    'notify_new_orders', 'notify_messages', 'notify_reviews',
                    'notify_low_stock', 'notify_payouts', 'updated_at'
                ])
                messages.success(request, 'Notification settings saved successfully!')
        
        return super().change_view(request, object_id, form_url, extra_context)
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# =============================================================================
# REGISTER MODELS TO SELLER ADMIN
# =============================================================================

seller_admin_site.register(Seller, SellerProfileAdmin)
seller_admin_site.register(Listing, SellerListingAdmin)
seller_admin_site.register(MarketplaceOrder, SellerOrderAdmin)
seller_admin_site.register(Review, SellerReviewAdmin)
seller_admin_site.register(SellerWallet, SellerWalletAdmin)
seller_admin_site.register(PayoutRequest, SellerPayoutRequestAdmin)
seller_admin_site.register(SellerPayoutAccount, SellerPayoutAccountAdmin)
seller_admin_site.register(Conversation, SellerConversationAdmin)
