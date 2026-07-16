"""
El Mercado API Views
====================
ViewSets and API views for the multi-vendor marketplace platform.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from django.utils import timezone
from django.db import models
from django.db.models import Q, Count, Avg, F, Sum, Case, When, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce, Now
from django.shortcuts import get_object_or_404
from django.conf import settings
from datetime import timedelta
from decimal import Decimal

from .models import (
    SellerApplication, Seller, SellerWallet, WalletTransaction,
    PayoutRequest, SellerPayoutAccount, Category, Listing, ListingImage,
    ListingVariant, MarketplaceOrder, OrderItem, Review, Conversation,
    Message, Favorite, FollowedSeller, Dispute, MarketplaceSettings
)
from .serializers import (
    SellerApplicationCreateSerializer, SellerApplicationUpdateSerializer, 
    SellerApplicationSerializer, SellerApplicationListSerializer,
    SellerApplicationStatusSerializer,
    SellerPublicSerializer, SellerDashboardSerializer, SellerListSerializer,
    SellerWalletSerializer, WalletTransactionSerializer,
    PayoutRequestCreateSerializer, PayoutRequestSerializer, SellerPayoutAccountSerializer,
    CategorySerializer, CategoryListSerializer,
    ListingCreateSerializer, ListingDetailSerializer, ListingListSerializer,
    ListingImageSerializer, ListingVariantSerializer,
    OrderCreateSerializer, OrderDetailSerializer, OrderListSerializer,
    ReviewCreateSerializer, ReviewSerializer, ReviewListSerializer,
    ConversationSerializer, ConversationListSerializer, MessageSerializer, MessageCreateSerializer,
    FavoriteSerializer, FollowedSellerSerializer,
    DisputeCreateSerializer, DisputeSerializer,
    MarketplaceSettingsSerializer
)
from .permissions import IsSeller, IsSellerOwner, IsBuyer, IsOrderParticipant


# =============================================================================
# PAGINATION & FILTERS
# =============================================================================

class StandardResultsPagination(PageNumberPagination):
    """Standard pagination for listings"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ListingFilter(django_filters.FilterSet):
    """
    Custom filter for Listings with support for:
    - Category (by ID or slug)
    - Price range (min_price, max_price)
    - Listing type
    - Condition
    - Seller
    - Search
    """
    category = django_filters.CharFilter(method='filter_category')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    listing_type = django_filters.CharFilter(field_name='listing_type')
    condition = django_filters.CharFilter(field_name='condition')
    seller = django_filters.CharFilter(method='filter_seller')
    search = django_filters.CharFilter(method='filter_search')
    is_in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    has_discount = django_filters.BooleanFilter(method='filter_has_discount')
    
    class Meta:
        model = Listing
        fields = ['category', 'listing_type', 'condition', 'seller', 'min_price', 'max_price']
    
    def filter_category(self, queryset, name, value):
        """Filter by category ID or slug, including child categories"""
        if not value:
            return queryset
        
        try:
            # Try to get category by ID first
            from uuid import UUID
            try:
                category = Category.objects.get(id=UUID(value))
            except (ValueError, Category.DoesNotExist):
                # Try by slug
                category = Category.objects.get(slug=value)
            
            # Get all descendant category IDs (including self)
            category_ids = [category.id]
            self._get_descendant_ids(category, category_ids)
            
            return queryset.filter(category_id__in=category_ids)
        except Category.DoesNotExist:
            return queryset.none()
    
    def _get_descendant_ids(self, category, ids_list):
        """Recursively get all descendant category IDs"""
        for child in category.children.filter(is_active=True):
            ids_list.append(child.id)
            self._get_descendant_ids(child, ids_list)
    
    def filter_seller(self, queryset, name, value):
        """Filter by seller ID or slug"""
        if not value:
            return queryset
        
        try:
            from uuid import UUID
            try:
                return queryset.filter(seller_id=UUID(value))
            except (ValueError, TypeError):
                return queryset.filter(seller__slug=value)
        except:
            return queryset
    
    def filter_search(self, queryset, name, value):
        """Full text search across title, description, tags"""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(tags__icontains=value) |
            Q(seller__display_name__icontains=value) |
            Q(category__name__icontains=value)
        ).distinct()
    
    def filter_in_stock(self, queryset, name, value):
        """Filter by stock availability"""
        if value is None:
            return queryset
        
        if value:
            return queryset.filter(
                Q(track_inventory=False) |
                Q(stock_quantity__gt=0) |
                Q(allow_backorder=True)
            )
        else:
            return queryset.filter(
                track_inventory=True,
                stock_quantity=0,
                allow_backorder=False
            )
    
    def filter_has_discount(self, queryset, name, value):
        """Filter listings with discounts"""
        if value is None:
            return queryset
        
        if value:
            return queryset.filter(
                compare_at_price__isnull=False,
                compare_at_price__gt=0
            ).exclude(compare_at_price__lte=F('price'))
        return queryset


# =============================================================================
# CATEGORY VIEWS
# =============================================================================

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for marketplace categories.
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'display_order']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    @action(detail=False, methods=['get'])
    def root(self, request):
        """Get only root categories (no parent)"""
        categories = self.queryset.filter(parent__isnull=True)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


# =============================================================================
# SELLER APPLICATION VIEWS
# =============================================================================

class SellerApplicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for seller applications.
    """
    queryset = SellerApplication.objects.all()
    serializer_class = SellerApplicationSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'seller_type']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        user = self.request.user
        # Admin actions that need access to all applications
        admin_actions = ['approve', 'reject', 'request_revision']
        
        # Allow staff to see all applications if they explicitly request it via query param
        # e.g., ?admin=true for admin dashboard views
        if user.is_staff and (self.action in admin_actions or self.request.query_params.get('admin') == 'true'):
            return SellerApplication.objects.all()
        
        # For regular users and staff checking their own applications (default behavior)
        return SellerApplication.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SellerApplicationCreateSerializer
        if self.action in ['update', 'partial_update']:
            return SellerApplicationUpdateSerializer
        if self.action == 'list':
            return SellerApplicationListSerializer
        return SellerApplicationSerializer
    
    def update(self, request, *args, **kwargs):
        """Override update to prevent editing approved/rejected applications"""
        application = self.get_object()
        
        # Only allow updates on PENDING or REVISION_REQUESTED applications
        if application.status not in ['PENDING', 'REVISION_REQUESTED']:
            return Response(
                {'error': 'Cannot edit an application that is under review, approved, or rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to prevent editing approved/rejected applications"""
        application = self.get_object()
        
        # Only allow updates on PENDING or REVISION_REQUESTED applications
        if application.status not in ['PENDING', 'REVISION_REQUESTED']:
            return Response(
                {'error': 'Cannot edit an application that is under review, approved, or rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().partial_update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """
        Approve a seller application (admin only).
        Creates seller profile and generates login credentials.
        Sends credentials via email/SMS to the seller.
        """
        application = self.get_object()
        
        if application.status != 'PENDING':
            return Response(
                {'error': 'Only pending applications can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        seller, temp_password = application.approve(request.user)
        
        # Send credentials to seller
        credentials_sent = self._send_seller_credentials(
            seller, 
            temp_password,
            application.applicant_email,
            str(application.applicant_phone)
        )
        
        return Response({
            'message': 'Application approved successfully',
            'seller_id': str(seller.id),
            'credentials_sent': credentials_sent,
            'seller_email': seller.email,
            # Only return temp password in response for debugging in dev
            # Remove in production
            'temp_password_for_testing': temp_password if settings.DEBUG else None
        })
    
    def _send_seller_credentials(self, seller, temp_password, email, phone):
        """
        Send login credentials to the newly approved seller.
        Uses modern HTML email template with plain text fallback.
        """
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from datetime import datetime
        
        login_url = getattr(
            settings, 
            'SELLER_PORTAL_LOGIN_URL', 
            f"{getattr(settings, 'BACKEND_URL', 'https://api.biochemknust.com')}/api/el-mercado/seller/login/"
        )

        from BioChemSystem.config.brand import get_brand_context
        # Context for the HTML template
        context = {
            **get_brand_context(),
            'seller_name': seller.display_name,
            'seller_email': email,
            'seller_phone': str(phone),
            'temp_password': temp_password,
            'login_url': login_url,
            'year': datetime.now().year,
        }
        
        sent_methods = []
        
        # Try sending email
        try:
            # Render HTML template
            html_content = render_to_string('el_mercado/emails/seller_credentials.html', context)
            text_content = strip_tags(html_content)  # Plain text fallback
            
            email_message = EmailMultiAlternatives(
                subject='🛍️ El Mercado - Your Seller Account is Ready!',
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            email_message.attach_alternative(html_content, "text/html")
            email_message.send(fail_silently=False)
            sent_methods.append('email')
        except Exception as e:
            print(f"Failed to send credentials email: {e}")
            # Fallback to plain text if template fails
            try:
                from django.core.mail import send_mail
                plain_message = (
                    f"Congratulations! Your seller application for '{seller.display_name}' has been approved!\n\n"
                    f"Login URL: {login_url}\n"
                    f"Email/Phone: {email}\n"
                    f"Temporary Password: {temp_password}\n\n"
                    f"Please change your password after your first login."
                )
                send_mail(
                    subject='El Mercado - Your Seller Account is Ready!',
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )
                sent_methods.append('email (plain)')
            except Exception as e2:
                print(f"Plain text email also failed: {e2}")
        
        # Try sending SMS (can integrate with SMS provider)
        try:
            # Example with a hypothetical SMS service
            # from notifications.utils import send_sms
            # sms_msg = f"El Mercado: Your seller account is ready! Password: {temp_password}. Login at {login_url}"
            # send_sms(phone, sms_msg)
            # sent_methods.append('sms')
            pass
        except Exception as e:
            print(f"Failed to send credentials SMS: {e}")
        
        return sent_methods

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """Reject a seller application (admin only)"""
        application = self.get_object()
        reason = request.data.get('reason', '')
        
        if application.status not in ['PENDING', 'UNDER_REVIEW']:
            return Response(
                {'error': 'Cannot reject this application'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.reject(request.user, reason)
        return Response({'message': 'Application rejected'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def request_revision(self, request, pk=None):
        """Request revision for a seller application (admin only)"""
        application = self.get_object()
        reason = request.data.get('reason', '')
        
        application.request_revision(request.user, reason)
        return Response({'message': 'Revision requested'})
    
    @action(detail=False, methods=['get', 'post'], permission_classes=[AllowAny], url_path='check-status')
    def check_status(self, request):
        """
        Check application status by tracking code (public endpoint).
        GET: ?tracking_code=ELM-XXXXXXXX
        POST: {"tracking_code": "ELM-XXXXXXXX"}
        """
        tracking_code = request.query_params.get('tracking_code') or request.data.get('tracking_code')
        
        if not tracking_code:
            return Response(
                {'error': 'Tracking code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            application = SellerApplication.objects.get(tracking_code=tracking_code.upper())
            serializer = SellerApplicationStatusSerializer(application)
            return Response(serializer.data)
        except SellerApplication.DoesNotExist:
            return Response(
                {'error': 'No application found with this tracking code'},
                status=status.HTTP_404_NOT_FOUND
            )


# =============================================================================
# SELLER VIEWS
# =============================================================================

class SellerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing sellers (public).
    """
    queryset = Seller.objects.filter(status='ACTIVE')
    serializer_class = SellerPublicSerializer
    authentication_classes = []  # No authentication needed for public seller profiles
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['display_name', 'description']
    filterset_fields = ['seller_type', 'is_verified']
    ordering_fields = ['average_rating', 'total_sales', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SellerListSerializer
        return SellerPublicSerializer
    
    @action(detail=True, methods=['get'])
    def listings(self, request, slug=None):
        """Get all active listings for a seller"""
        seller = self.get_object()
        listings = seller.listings.filter(status='ACTIVE')
        serializer = ListingListSerializer(listings, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, slug=None):
        """Get all reviews for a seller"""
        seller = self.get_object()
        reviews = seller.reviews.filter(is_approved=True)
        serializer = ReviewListSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], authentication_classes=[], permission_classes=[AllowAny])
    def follow(self, request, slug=None):
        """Follow a seller"""
        from rest_framework_simplejwt.authentication import JWTAuthentication
        # Manually authenticate for this action since viewset has auth disabled
        jwt_auth = JWTAuthentication()
        try:
            auth_result = jwt_auth.authenticate(request)
            if auth_result:
                request.user, request.auth = auth_result
        except Exception:
            pass
        
        if not request.user or not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        seller = self.get_object()
        follow, created = FollowedSeller.objects.get_or_create(
            user=request.user,
            seller=seller
        )
        
        if created:
            return Response({'message': 'Now following seller'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Already following'})
    
    @action(detail=True, methods=['delete'], authentication_classes=[], permission_classes=[AllowAny])
    def unfollow(self, request, slug=None):
        """Unfollow a seller"""
        from rest_framework_simplejwt.authentication import JWTAuthentication
        # Manually authenticate for this action since viewset has auth disabled
        jwt_auth = JWTAuthentication()
        try:
            auth_result = jwt_auth.authenticate(request)
            if auth_result:
                request.user, request.auth = auth_result
        except Exception:
            pass
        
        if not request.user or not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        seller = self.get_object()
        FollowedSeller.objects.filter(user=request.user, seller=seller).delete()
        return Response({'message': 'Unfollowed seller'})


class SellerDashboardViewSet(viewsets.ViewSet):
    """
    API endpoint for seller's own dashboard.
    """
    permission_classes = [IsAuthenticated, IsSeller]
    
    def get_seller(self, request):
        return request.user.seller_profile
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get seller's own profile"""
        seller = self.get_seller(request)
        serializer = SellerDashboardSerializer(seller)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update seller's own profile"""
        seller = self.get_seller(request)
        serializer = SellerDashboardSerializer(seller, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def wallet(self, request):
        """Get wallet details"""
        seller = self.get_seller(request)
        serializer = SellerWalletSerializer(seller.wallet)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Get wallet transactions"""
        seller = self.get_seller(request)
        transactions = seller.wallet.transactions.all()[:50]
        serializer = WalletTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def orders(self, request):
        """Get seller's orders"""
        seller = self.get_seller(request)
        status_filter = request.query_params.get('status')
        orders = seller.orders.all()
        
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        serializer = OrderListSerializer(orders[:50], many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get seller statistics"""
        seller = self.get_seller(request)
        
        return Response({
            'total_sales': seller.total_sales,
            'average_rating': str(seller.average_rating),
            'total_reviews': seller.total_reviews,
            'active_listings': seller.listings.filter(status='ACTIVE').count(),
            'pending_orders': seller.orders.filter(status__in=['PENDING', 'PAID', 'PROCESSING']).count(),
            'available_balance': str(seller.wallet.available_balance),
            'pending_balance': str(seller.wallet.pending_balance),
            'followers': seller.followers.count(),
        })


# =============================================================================
# LISTING VIEWS
# =============================================================================

class ListingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for marketplace listings.
    
    Supports filtering by:
    - category: Category ID or slug (includes child categories)
    - listing_type: PRODUCT, SERVICE, DIGITAL
    - condition: NEW, LIKE_NEW, GOOD, FAIR, FOR_PARTS
    - seller: Seller ID or slug
    - min_price: Minimum price (inclusive)
    - max_price: Maximum price (inclusive)
    - search: Full text search on title, description, tags
    - is_in_stock: Filter by stock availability
    - has_discount: Filter listings with discounts
    
    Supports ordering by:
    - price, -price
    - created_at, -created_at (default: -created_at)
    - average_rating, -average_rating
    - order_count, -order_count
    - view_count, -view_count
    """
    queryset = Listing.objects.filter(status='ACTIVE')
    serializer_class = ListingDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ListingFilter
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['price', 'created_at', 'average_rating', 'order_count', 'view_count']
    ordering = ['-created_at']  # Default ordering
    
    def get_queryset(self):
        queryset = Listing.objects.all()
        
        # For public views, only show active listings
        if not self.request.user.is_authenticated:
            return queryset.filter(status='ACTIVE')
        
        # Sellers can see their own listings
        if hasattr(self.request.user, 'seller_profile'):
            return queryset.filter(
                Q(status='ACTIVE') | Q(seller=self.request.user.seller_profile)
            )
        
        return queryset.filter(status='ACTIVE')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ListingListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ListingCreateSerializer
        return ListingDetailSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSeller()]
        return [AllowAny()]
    
    def retrieve(self, request, *args, **kwargs):
        """Increment view count on retrieve"""
        instance = self.get_object()
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSeller])
    def publish(self, request, slug=None):
        """Publish a listing"""
        listing = self.get_object()
        
        if listing.seller != request.user.seller_profile:
            return Response(
                {'error': 'You can only publish your own listings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        listing.publish()
        return Response({'message': 'Listing published successfully'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def favorite(self, request, slug=None):
        """Add listing to favorites"""
        listing = self.get_object()
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            listing=listing
        )
        
        if created:
            listing.favorite_count += 1
            listing.save(update_fields=['favorite_count'])
            return Response({'message': 'Added to favorites'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Already in favorites'})
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unfavorite(self, request, slug=None):
        """Remove listing from favorites"""
        listing = self.get_object()
        deleted, _ = Favorite.objects.filter(user=request.user, listing=listing).delete()
        
        if deleted:
            listing.favorite_count = max(0, listing.favorite_count - 1)
            listing.save(update_fields=['favorite_count'])
        
        return Response({'message': 'Removed from favorites'})
    
    @action(detail=True, methods=['get', 'post'], parser_classes=[JSONParser])
    def reviews(self, request, slug=None):
        """Get or create reviews for a listing"""
        listing = self.get_object()
        
        if request.method == 'GET':
            reviews = listing.reviews.filter(is_approved=True)
            serializer = ReviewListSerializer(reviews, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return Response(
                    {'error': 'Authentication required to submit a review'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Create review with listing context
            serializer = ReviewCreateSerializer(
                data={**request.data, 'listing': listing.id},
                context={'request': request, 'listing': listing}
            )
            
            if serializer.is_valid():
                review = serializer.save()
                return Response(
                    ReviewListSerializer(review).data,
                    status=status.HTTP_201_CREATED
                )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get Best Sellers - Products with highest sales performance.
        
        Algorithm combines multiple factors:
        1. Order count (40% weight) - Direct sales volume
        2. Revenue generated (25% weight) - Total sales value
        3. Conversion rate (15% weight) - Orders relative to views
        4. Review score (10% weight) - Customer satisfaction
        5. Recency bonus (10% weight) - Boost for recent activity
        
        Filters:
        - Only ACTIVE listings
        - Must have at least 1 order OR 10 views (excludes brand new listings)
        - Seller must be verified for trust
        - Must be in stock
        """
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        ninety_days_ago = now - timedelta(days=90)
        
        # Get base queryset of active listings with seller info
        queryset = Listing.objects.filter(
            status='ACTIVE',
        ).select_related('seller', 'category')
        
        # Annotate with calculated metrics
        queryset = queryset.annotate(
            # Count recent orders (last 30 days) for recency boost
            recent_order_count=Count(
                'order_items',
                filter=Q(
                    order_items__order__created_at__gte=thirty_days_ago,
                    order_items__order__status__in=['PAID', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
                )
            ),
            # Total revenue from completed orders
            total_revenue=Coalesce(
                Sum(
                    'order_items__total_price',
                    filter=Q(
                        order_items__order__status__in=['PAID', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
                    )
                ),
                Value(Decimal('0.00')),
                output_field=DecimalField()
            ),
            # Calculate conversion rate (orders / views), avoid division by zero
            conversion_rate=Case(
                When(view_count__gt=0, then=F('order_count') * 100.0 / F('view_count')),
                default=Value(0.0),
                output_field=DecimalField(max_digits=10, decimal_places=4)
            ),
            # Weighted score calculation
            # Normalize each factor and combine with weights
            bestseller_score=ExpressionWrapper(
                # Order count factor (40%) - cap at 100 orders for normalization
                (Case(
                    When(order_count__gte=100, then=Value(40.0)),
                    default=F('order_count') * 0.4,
                    output_field=DecimalField()
                )) +
                # Revenue factor (25%) - normalize by price (orders * avg value indicator)
                (Case(
                    When(total_revenue__gte=10000, then=Value(25.0)),
                    When(total_revenue__gt=0, then=F('total_revenue') / Value(Decimal('400.0'))),
                    default=Value(0.0),
                    output_field=DecimalField()
                )) +
                # Conversion rate (15%) - cap at 10% conversion
                (Case(
                    When(conversion_rate__gte=10, then=Value(15.0)),
                    default=F('conversion_rate') * 1.5,
                    output_field=DecimalField()
                )) +
                # Review score (10%) - based on average rating
                (F('average_rating') * 2) +  # Max 10 points (5 * 2)
                # Recency bonus (10%) - recent orders boost
                (Case(
                    When(recent_order_count__gte=10, then=Value(10.0)),
                    default=F('recent_order_count') * 1.0,
                    output_field=DecimalField()
                )),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
        
        # Filter to meaningful results
        queryset = queryset.filter(
            Q(order_count__gte=1) | Q(view_count__gte=10)  # Has some traction
        ).filter(
            Q(stock_quantity__gt=0) | Q(track_inventory=False)  # In stock
        )
        
        # Prefer verified sellers, but don't exclude unverified
        queryset = queryset.order_by(
            '-seller__is_verified',  # Verified sellers first
            '-bestseller_score',      # Then by score
            '-order_count',           # Tiebreaker: raw order count
            '-average_rating'         # Secondary tiebreaker: rating
        )[:12]
        
        serializer = ListingListSerializer(queryset, many=True, context={'request': request})
        
        # Add metadata about the calculation
        return Response({
            'results': serializer.data,
            'meta': {
                'algorithm': 'bestseller_v1',
                'factors': {
                    'order_count': '40%',
                    'revenue': '25%',
                    'conversion_rate': '15%',
                    'rating': '10%',
                    'recency': '10%'
                },
                'period': '30 days for recency, all-time for totals',
                'count': len(serializer.data)
            }
        })
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get New Arrivals - Recently added quality listings.
        
        Algorithm prioritizes:
        1. Recency (primary) - Published within last 30 days
        2. Quality signals (secondary) - Has images, description, proper pricing
        3. Seller reputation (tertiary) - Verified sellers get boost
        4. Early engagement (quaternary) - Views/favorites indicate interest
        
        Filters:
        - Only ACTIVE listings
        - Published within last 30 days (configurable)
        - Must have main image (quality indicator)
        - Must be in stock
        """
        now = timezone.now()
        days_param = request.query_params.get('days', 30)
        try:
            days = min(int(days_param), 90)  # Cap at 90 days
        except (ValueError, TypeError):
            days = 30
        
        cutoff_date = now - timedelta(days=days)
        
        # Get base queryset
        queryset = Listing.objects.filter(
            status='ACTIVE',
            created_at__gte=cutoff_date,
        ).select_related('seller', 'category')
        
        # Annotate with quality and engagement scores
        queryset = queryset.annotate(
            # Quality score based on listing completeness
            quality_score=ExpressionWrapper(
                # Has main image (essential) - 30 points
                Case(
                    When(Q(main_image__isnull=False) & ~Q(main_image=''), then=Value(30.0)),
                    default=Value(0.0),
                    output_field=DecimalField()
                ) +
                # Has description of meaningful length - 20 points
                Case(
                    When(description__regex=r'.{100,}', then=Value(20.0)),  # 100+ chars
                    When(description__regex=r'.{50,}', then=Value(10.0)),   # 50+ chars
                    default=Value(0.0),
                    output_field=DecimalField()
                ) +
                # Has compare_at_price (shows discount) - 10 points
                Case(
                    When(compare_at_price__isnull=False, then=Value(10.0)),
                    default=Value(0.0),
                    output_field=DecimalField()
                ) +
                # Seller is verified - 20 points
                Case(
                    When(seller__is_verified=True, then=Value(20.0)),
                    default=Value(0.0),
                    output_field=DecimalField()
                ) +
                # Has category assigned - 10 points
                Case(
                    When(category__isnull=False, then=Value(10.0)),
                    default=Value(0.0),
                    output_field=DecimalField()
                ) +
                # Has tags - 5 points
                Case(
                    When(~Q(tags=[]), then=Value(5.0)),
                    default=Value(0.0),
                    output_field=DecimalField()
                ) +
                # Reasonable price (not 0 or extremely high) - 5 points
                Case(
                    When(price__gt=0, price__lt=100000, then=Value(5.0)),
                    default=Value(0.0),
                    output_field=DecimalField()
                ),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            ),
            # Early engagement score
            engagement_score=ExpressionWrapper(
                # Views indicate interest (capped contribution)
                Case(
                    When(view_count__gte=100, then=Value(15.0)),
                    When(view_count__gte=50, then=Value(10.0)),
                    When(view_count__gte=10, then=Value(5.0)),
                    default=Value(0.0),
                    output_field=DecimalField()
                ) +
                # Favorites show strong interest
                Case(
                    When(favorite_count__gte=10, then=Value(15.0)),
                    When(favorite_count__gte=5, then=Value(10.0)),
                    When(favorite_count__gte=1, then=Value(5.0)),
                    default=Value(0.0),
                    output_field=DecimalField()
                ) +
                # Early orders are great signal
                Case(
                    When(order_count__gte=5, then=Value(20.0)),
                    When(order_count__gte=1, then=Value(10.0)),
                    default=Value(0.0),
                    output_field=DecimalField()
                ),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            ),
            # Combined score for new arrivals
            arrival_score=ExpressionWrapper(
                F('quality_score') + F('engagement_score'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
        
        # Filter for quality - must have image at minimum
        queryset = queryset.filter(
            Q(main_image__isnull=False) & ~Q(main_image='')
        ).filter(
            Q(stock_quantity__gt=0) | Q(track_inventory=False)  # In stock
        )
        
        # Order by recency first, then by quality/engagement score
        queryset = queryset.order_by(
            '-created_at',      # Newest first (primary)
        )
        
        # Take top results but re-sort by score within recent items
        recent_listings = list(queryset[:24])  # Get more, then sort
        recent_listings.sort(key=lambda x: (
            -getattr(x, 'arrival_score', 0),  # Higher score first
            -x.created_at.timestamp()          # Then newest
        ))
        
        serializer = ListingListSerializer(recent_listings[:12], many=True, context={'request': request})
        
        return Response({
            'results': serializer.data,
            'meta': {
                'algorithm': 'new_arrivals_v1',
                'factors': {
                    'quality_score': 'image, description, pricing, seller verification',
                    'engagement_score': 'views, favorites, early orders'
                },
                'period': f'{days} days',
                'count': len(serializer.data)
            }
        })
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """
        Get Trending Products - Items with recent surge in interest.
        
        Algorithm focuses on velocity of engagement:
        1. Recent views growth (last 7 days vs previous)
        2. Recent favorites growth
        3. Recent order velocity
        4. Social signals (shares, if tracked)
        """
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)
        
        queryset = Listing.objects.filter(
            status='ACTIVE',
        ).select_related('seller', 'category')
        
        # Annotate with recent activity metrics
        queryset = queryset.annotate(
            # Recent orders in last 7 days
            recent_orders=Count(
                'order_items',
                filter=Q(
                    order_items__order__created_at__gte=seven_days_ago,
                    order_items__order__status__in=['PAID', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
                )
            ),
            # Recent favorites (we'll use favorite_count as proxy since we don't track dates)
            # In production, you'd track favorite creation dates
            trending_score=ExpressionWrapper(
                # Recent orders heavily weighted
                F('recent_orders') * Value(Decimal('10.0')) +
                # Current favorites
                Case(
                    When(favorite_count__gte=20, then=Value(30.0)),
                    When(favorite_count__gte=10, then=Value(20.0)),
                    When(favorite_count__gte=5, then=Value(10.0)),
                    default=F('favorite_count') * Value(Decimal('2.0')),
                    output_field=DecimalField()
                ) +
                # High view velocity indicator
                Case(
                    When(view_count__gte=500, then=Value(20.0)),
                    When(view_count__gte=200, then=Value(15.0)),
                    When(view_count__gte=100, then=Value(10.0)),
                    When(view_count__gte=50, then=Value(5.0)),
                    default=Value(0.0),
                    output_field=DecimalField()
                ) +
                # Boost for good ratings
                F('average_rating') * Value(Decimal('3.0')),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
        
        # Filter for trending candidates
        queryset = queryset.filter(
            Q(view_count__gte=20) | Q(order_count__gte=1) | Q(favorite_count__gte=1)
        ).filter(
            Q(stock_quantity__gt=0) | Q(track_inventory=False)
        ).order_by('-trending_score', '-view_count')[:12]
        
        serializer = ListingListSerializer(queryset, many=True, context={'request': request})
        
        return Response({
            'results': serializer.data,
            'meta': {
                'algorithm': 'trending_v1',
                'period': '7 days',
                'count': len(serializer.data)
            }
        })


class SellerListingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for seller to manage their own listings.
    """
    serializer_class = ListingDetailSerializer
    permission_classes = [IsAuthenticated, IsSeller]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        return Listing.objects.filter(seller=self.request.user.seller_profile)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ListingListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ListingCreateSerializer
        return ListingDetailSerializer
    
    @action(detail=True, methods=['post'])
    def add_image(self, request, pk=None):
        """Add image to listing"""
        listing = self.get_object()
        serializer = ListingImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(listing=listing)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='remove_image/(?P<image_id>[^/.]+)')
    def remove_image(self, request, pk=None, image_id=None):
        """Remove image from listing"""
        listing = self.get_object()
        ListingImage.objects.filter(id=image_id, listing=listing).delete()
        return Response({'message': 'Image removed'})
    
    @action(detail=True, methods=['post'])
    def add_variant(self, request, pk=None):
        """Add variant to listing"""
        listing = self.get_object()
        serializer = ListingVariantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(listing=listing)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='remove_variant/(?P<variant_id>[^/.]+)')
    def remove_variant(self, request, pk=None, variant_id=None):
        """Remove variant from listing"""
        listing = self.get_object()
        ListingVariant.objects.filter(id=variant_id, listing=listing).delete()
        return Response({'message': 'Variant removed'})


# =============================================================================
# ORDER VIEWS
# =============================================================================

class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for marketplace orders.
    """
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_status']
    ordering_fields = ['created_at', 'total_amount']
    
    def get_queryset(self):
        user = self.request.user
        
        # Buyers see their orders
        buyer_orders = MarketplaceOrder.objects.filter(buyer=user)
        
        # Sellers see orders for their store
        if hasattr(user, 'seller_profile'):
            seller_orders = MarketplaceOrder.objects.filter(seller=user.seller_profile)
            return (buyer_orders | seller_orders).select_related('seller', 'buyer').prefetch_related('items').order_by('-created_at')
        
        return buyer_orders.select_related('seller', 'buyer').prefetch_related('items').order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderDetailSerializer
    
    @action(detail=False, methods=['get', 'post'], permission_classes=[AllowAny], url_path='verify')
    def verify(self, request):
        """
        Verify payment status for an El Mercado order.
        
        GET /api/orders/verify/?reference=ELM-XXXXXXXX
        POST /api/orders/verify/ with {"reference": "ELM-XXXXXXXX"}
        
        This endpoint is used by the payment callback page to check
        if the payment was successful.
        """
        from .services import ElMercadoService
        
        reference = request.query_params.get('reference') or request.data.get('reference')
        
        if not reference:
            return Response(
                {'error': 'Reference is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = ElMercadoService.verify_payment(reference)
        
        if result.success:
            return Response({
                'status': 'success',
                'message': result.message,
                'data': result.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'failed',
                'message': result.message,
                'error_code': result.error_code
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order (buyer only, before shipping)"""
        order = self.get_object()
        
        if order.buyer != request.user:
            return Response(
                {'error': 'Only the buyer can cancel this order'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if order.status not in ['PENDING', 'AWAITING_PAYMENT', 'PAID']:
            return Response(
                {'error': 'Cannot cancel order at this stage'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.update_status('CANCELLED', 'Cancelled by buyer')
        return Response({'message': 'Order cancelled'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSeller])
    def accept(self, request, pk=None):
        """Accept an order (seller only)"""
        order = self.get_object()
        
        if order.seller != request.user.seller_profile:
            return Response(
                {'error': 'Only the seller can accept this order'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if order.status != 'PAID':
            return Response(
                {'error': 'Can only accept paid orders'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.update_status('PROCESSING', 'Accepted by seller')
        
        # Add to seller's pending balance
        order.seller.wallet.add_pending(order.seller_earnings, f"Order {order.order_number}")
        
        return Response({'message': 'Order accepted'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSeller])
    def ship(self, request, pk=None):
        """Mark order as shipped (seller only)"""
        order = self.get_object()
        
        if order.seller != request.user.seller_profile:
            return Response(
                {'error': 'Only the seller can ship this order'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        tracking_number = request.data.get('tracking_number', '')
        tracking_url = request.data.get('tracking_url', '')
        
        order.tracking_number = tracking_number
        order.tracking_url = tracking_url
        order.shipped_at = timezone.now()
        order.save(update_fields=['tracking_number', 'tracking_url', 'shipped_at'])
        order.update_status('SHIPPED', 'Shipped by seller')
        
        return Response({'message': 'Order marked as shipped'})
    
    @action(detail=True, methods=['post', 'put'])
    def update_shipping(self, request, pk=None):
        """
        Update shipping address on an order (buyer only).
        Can only update before order is shipped.
        """
        order = self.get_object()
        
        if order.buyer != request.user:
            return Response(
                {'error': 'Only the buyer can update shipping address'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Can only update before shipping
        if order.status in ['SHIPPED', 'DELIVERED', 'COMPLETED', 'CANCELLED', 'REFUNDED']:
            return Response(
                {'error': 'Cannot update shipping address after order has been shipped'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update shipping fields
        data = request.data
        
        if data.get('shipping_address_id'):
            # If a shipping address ID is provided, fetch from saved addresses
            from accounts.models import ShippingAddress
            try:
                address = ShippingAddress.objects.get(
                    id=data['shipping_address_id'],
                    user=request.user
                )
                order.shipping_name = address.full_name
                order.shipping_phone = str(address.phone)
                order.shipping_email = address.email or request.user.email
                order.shipping_address_line_1 = address.address_line_1
                order.shipping_address_line_2 = address.address_line_2 or ''
                order.shipping_city = address.city
                order.shipping_region = address.region or ''
                order.shipping_country = address.country or 'Ghana'
                # Store reference to the address
                order.shipping_address = address
            except ShippingAddress.DoesNotExist:
                return Response(
                    {'error': 'Shipping address not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Direct fields update
            if data.get('name'):
                order.shipping_name = data['name']
            if data.get('phone'):
                order.shipping_phone = data['phone']
            if data.get('email'):
                order.shipping_email = data['email']
            if data.get('address_line_1'):
                order.shipping_address_line_1 = data['address_line_1']
            if data.get('address_line_2') is not None:
                order.shipping_address_line_2 = data['address_line_2']
            if data.get('city'):
                order.shipping_city = data['city']
            if data.get('region') is not None:
                order.shipping_region = data['region']
            if data.get('country'):
                order.shipping_country = data['country']
        
        order.save(update_fields=[
            'shipping_name', 'shipping_phone', 'shipping_email',
            'shipping_address_line_1', 'shipping_address_line_2',
            'shipping_city', 'shipping_region', 'shipping_country',
            'shipping_address'
        ])
        
        return Response({
            'message': 'Shipping address updated successfully',
            'shipping': {
                'name': order.shipping_name,
                'phone': str(order.shipping_phone) if order.shipping_phone else '',
                'address_line_1': order.shipping_address_line_1,
                'city': order.shipping_city,
            }
        })
    
    @action(detail=True, methods=['get'])
    def delivery_code(self, request, pk=None):
        """
        Get delivery verification code (buyer only).
        The buyer shows this code to the seller upon receiving the order
        to confirm delivery.
        """
        order = self.get_object()
        
        if order.buyer != request.user:
            return Response(
                {'error': 'Only the buyer can view the delivery code'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if order.status not in ['SHIPPED', 'DELIVERED', 'COMPLETED']:
            return Response(
                {'error': 'Delivery code is only available after order is shipped'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not order.delivery_code:
            return Response(
                {'error': 'No delivery code was generated for this order'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'delivery_code': order.delivery_code,
            'order_number': order.order_number,
            'message': 'Give this code to the seller when you receive your order to confirm delivery.',
            'is_verified': order.delivery_verified,
            'verified_at': order.delivery_verified_at.isoformat() if order.delivery_verified_at else None,
        })
    
    @action(detail=True, methods=['post'])
    def confirm_delivery(self, request, pk=None):
        """Confirm delivery (buyer only) - this completes the order and releases funds"""
        order = self.get_object()
        
        if order.buyer != request.user:
            return Response(
                {'error': 'Only the buyer can confirm delivery'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if order.status != 'SHIPPED':
            return Response(
                {'error': 'Can only confirm delivery for shipped orders'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.delivered_at = timezone.now()
        order.delivery_verified = True
        order.delivery_verified_at = timezone.now()
        order.save(update_fields=['delivered_at', 'delivery_verified', 'delivery_verified_at'])
        order.update_status('DELIVERED', 'Delivery confirmed by buyer')
        
        # Release funds immediately when buyer confirms
        funds_released = order.release_funds()
        if funds_released:
            order.update_status('COMPLETED', 'Order completed, funds released')
        
        return Response({
            'message': 'Delivery confirmed and order completed',
            'funds_released': funds_released
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete order and release funds"""
        order = self.get_object()
        
        if order.status != 'DELIVERED':
            return Response(
                {'error': 'Can only complete delivered orders'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.update_status('COMPLETED', 'Order completed')
        order.release_funds()
        
        return Response({'message': 'Order completed, funds released to seller'})


# =============================================================================
# REVIEW VIEWS
# =============================================================================

class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for reviews.
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['review_type', 'rating', 'is_verified_purchase']
    ordering_fields = ['created_at', 'rating', 'helpful_count']
    
    def get_queryset(self):
        return Review.objects.filter(
            Q(reviewer=self.request.user) | Q(is_approved=True)
        )
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ReviewListSerializer
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSeller])
    def respond(self, request, pk=None):
        """Seller responds to a review"""
        review = self.get_object()
        
        if review.seller != request.user.seller_profile:
            return Response(
                {'error': 'Can only respond to reviews for your store'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        response_text = request.data.get('response', '')
        review.seller_response = response_text
        review.seller_responded_at = timezone.now()
        review.save(update_fields=['seller_response', 'seller_responded_at'])
        
        return Response({'message': 'Response added'})
    
    @action(detail=True, methods=['post'])
    def helpful(self, request, pk=None):
        """Mark review as helpful"""
        review = self.get_object()
        review.helpful_count += 1
        review.save(update_fields=['helpful_count'])
        return Response({'message': 'Marked as helpful'})


# =============================================================================
# CONVERSATION VIEWS
# =============================================================================

class ConversationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for buyer-seller conversations.
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Buyers see their conversations
        buyer_convos = Conversation.objects.filter(buyer=user)
        
        # Sellers see their conversations
        if hasattr(user, 'seller_profile'):
            seller_convos = Conversation.objects.filter(seller=user.seller_profile)
            return (buyer_convos | seller_convos).distinct()
        
        return buyer_convos
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationSerializer
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get messages for a conversation"""
        conversation = self.get_object()
        messages = conversation.messages.all()
        
        # Mark as read
        if hasattr(request.user, 'seller_profile') and conversation.seller == request.user.seller_profile:
            conversation.seller_unread_count = 0
            conversation.save(update_fields=['seller_unread_count'])
            messages.filter(sender_type='BUYER', is_read=False).update(is_read=True, read_at=timezone.now())
        else:
            conversation.buyer_unread_count = 0
            conversation.save(update_fields=['buyer_unread_count'])
            messages.filter(sender_type='SELLER', is_read=False).update(is_read=True, read_at=timezone.now())
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message in a conversation"""
        conversation = self.get_object()
        serializer = MessageCreateSerializer(
            data=request.data,
            context={'request': request, 'conversation': conversation}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def start(self, request):
        """Start a new conversation"""
        seller_id = request.data.get('seller_id')
        listing_id = request.data.get('listing_id')
        initial_message = request.data.get('message', '')
        
        seller = get_object_or_404(Seller, id=seller_id)
        listing = None
        if listing_id:
            listing = get_object_or_404(Listing, id=listing_id, seller=seller)
        
        # Get or create conversation
        conversation, created = Conversation.objects.get_or_create(
            buyer=request.user,
            seller=seller,
            listing=listing
        )
        
        # Send initial message if provided
        if initial_message:
            Message.objects.create(
                conversation=conversation,
                sender_type='BUYER',
                sender_user=request.user,
                content=initial_message
            )
        
        serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


# =============================================================================
# PAYOUT VIEWS
# =============================================================================

class PayoutRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for seller payout requests.
    """
    serializer_class = PayoutRequestSerializer
    permission_classes = [IsAuthenticated, IsSeller]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'amount']
    
    def get_queryset(self):
        return PayoutRequest.objects.filter(wallet__seller=self.request.user.seller_profile)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PayoutRequestCreateSerializer
        return PayoutRequestSerializer
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a payout request"""
        payout = self.get_object()
        
        if payout.status != 'PENDING':
            return Response(
                {'error': 'Can only cancel pending payout requests'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payout.status = 'CANCELLED'
        payout.save(update_fields=['status'])
        return Response({'message': 'Payout request cancelled'})


class PayoutAccountViewSet(viewsets.ModelViewSet):
    """
    API endpoint for seller payout accounts.
    """
    serializer_class = SellerPayoutAccountSerializer
    permission_classes = [IsAuthenticated, IsSeller]
    
    def get_queryset(self):
        return SellerPayoutAccount.objects.filter(seller=self.request.user.seller_profile)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set account as default"""
        account = self.get_object()
        account.is_default = True
        account.save()
        return Response({'message': 'Account set as default'})


# =============================================================================
# FAVORITE & FOLLOW VIEWS
# =============================================================================

class FavoriteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user favorites.
    """
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        listing_id = request.data.get('listing_id')
        listing = get_object_or_404(Listing, id=listing_id)
        
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            listing=listing
        )
        
        if created:
            listing.favorite_count += 1
            listing.save(update_fields=['favorite_count'])
        
        serializer = self.get_serializer(favorite)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class FollowedSellerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for followed sellers.
    """
    serializer_class = FollowedSellerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FollowedSeller.objects.filter(user=self.request.user).select_related('seller')
    
    def create(self, request, *args, **kwargs):
        seller_id = request.data.get('seller_id')
        seller = get_object_or_404(Seller, id=seller_id)
        
        follow, created = FollowedSeller.objects.get_or_create(
            user=request.user,
            seller=seller
        )
        
        serializer = self.get_serializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def listings(self, request):
        """Get listings from all followed sellers"""
        followed_sellers = FollowedSeller.objects.filter(user=request.user).values_list('seller_id', flat=True)
        
        listings = Listing.objects.filter(
            seller_id__in=followed_sellers,
            status='ACTIVE'
        ).select_related('seller', 'category').prefetch_related('images').order_by('-created_at')
        
        # Apply optional filters
        category = request.query_params.get('category')
        if category:
            listings = listings.filter(category__slug=category)
        
        listing_type = request.query_params.get('listing_type')
        if listing_type:
            listings = listings.filter(listing_type=listing_type)
        
        search = request.query_params.get('search')
        if search:
            listings = listings.filter(title__icontains=search)
        
        ordering = request.query_params.get('ordering', '-created_at')
        listings = listings.order_by(ordering)
        
        # Paginate
        page = self.paginate_queryset(listings)
        if page is not None:
            serializer = ListingListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ListingListSerializer(listings[:50], many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def check(self, request):
        """Check if user follows a specific seller"""
        seller_slug = request.query_params.get('seller')
        if not seller_slug:
            return Response({'error': 'seller slug is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        is_following = FollowedSeller.objects.filter(
            user=request.user,
            seller__slug=seller_slug
        ).exists()
        
        return Response({'is_following': is_following})


# =============================================================================
# DISPUTE VIEWS
# =============================================================================

class DisputeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for order disputes.
    """
    serializer_class = DisputeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'reason']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        # Buyers see disputes they initiated
        buyer_disputes = Dispute.objects.filter(initiated_by=user)
        
        # Sellers see disputes for their orders
        if hasattr(user, 'seller_profile'):
            seller_disputes = Dispute.objects.filter(order__seller=user.seller_profile)
            return (buyer_disputes | seller_disputes).distinct()
        
        return buyer_disputes
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DisputeCreateSerializer
        return DisputeSerializer
    
    @action(detail=True, methods=['post'])
    def add_evidence(self, request, pk=None):
        """Add evidence to dispute"""
        dispute = self.get_object()
        evidence = request.data.get('evidence', {})
        
        dispute.evidence.append(evidence)
        dispute.save(update_fields=['evidence'])
        
        return Response({'message': 'Evidence added'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def resolve(self, request, pk=None):
        """Resolve a dispute (admin only)"""
        dispute = self.get_object()
        resolution_status = request.data.get('resolution_status')
        resolution_notes = request.data.get('resolution_notes', '')
        refund_amount = request.data.get('refund_amount')
        
        dispute.status = resolution_status
        dispute.resolution_notes = resolution_notes
        dispute.resolved_by = request.user
        dispute.resolved_at = timezone.now()
        
        if refund_amount:
            dispute.refund_amount = refund_amount
        
        dispute.save()
        
        return Response({'message': 'Dispute resolved'})


class MarketplaceSettingsViewSet(viewsets.ViewSet):
    """
    ViewSet for fetching marketplace settings and commission rates.
    Requires tracking code verification to access commission rates.
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def verify_tracking_code(self, request):
        """Verify seller application tracking code"""
        from .models import SellerApplication
        
        tracking_code = request.data.get('tracking_code', '').strip()
        
        if not tracking_code:
            return Response({
                'valid': False,
                'message': 'Tracking code is required'
            }, status=400)
        
        try:
            application = SellerApplication.objects.get(tracking_code=tracking_code)
            return Response({
                'valid': True,
                'message': 'Tracking code verified',
                'applicant_name': application.applicant_name,
                'application_status': application.status
            })
        except SellerApplication.DoesNotExist:
            return Response({
                'valid': False,
                'message': 'Invalid tracking code'
            }, status=404)
    
    @action(detail=False, methods=['post'])
    def commission_rates(self, request):
        """Get all commission rates - requires tracking code verification"""
        from .models import CommissionRate, MarketplaceSettings, SellerApplication
        
        tracking_code = request.data.get('tracking_code', '').strip()
        
        # Verify tracking code
        if not tracking_code:
            return Response({
                'error': 'Tracking code is required to access commission rates'
            }, status=403)
        
        try:
            SellerApplication.objects.get(tracking_code=tracking_code)
        except SellerApplication.DoesNotExist:
            return Response({
                'error': 'Invalid tracking code'
            }, status=403)
        
        settings = MarketplaceSettings.get_settings()
        commission_rates = CommissionRate.objects.filter(is_active=True)
        
        rates_data = []
        for rate in commission_rates:
            # Extract examples from description (format: "Description - Example1, Example2, ...")
            desc_parts = rate.description.split(' - ', 1)
            description = desc_parts[0] if desc_parts else rate.description
            examples = desc_parts[1].split(', ') if len(desc_parts) > 1 else []
            
            rates_data.append({
                'category_type': rate.category_type,
                'category_name': rate.get_category_type_display(),
                'rate': float(rate.rate),
                'description': description,
                'examples': examples,
            })
        
        return Response({
            'commission_rates': rates_data,
            'default_rate': float(settings.default_commission_rate),
            'fees': {
                'payment_processing_percentage': float(settings.payment_processing_fee_percentage),
                'payment_processing_fixed': float(settings.payment_processing_fee_fixed),
                'payout_transaction_fee': float(settings.payout_transaction_fee),
                'payout_processing_percentage': float(settings.payout_processing_fee_percentage),
            }
        })
    
    @action(detail=False, methods=['get'])
    def platform_fees(self, request):
        """Get platform fee structure"""
        from .models import MarketplaceSettings
        
        settings = MarketplaceSettings.get_settings()
        
        return Response({
            'payment_processing': {
                'percentage': float(settings.payment_processing_fee_percentage),
                'fixed': float(settings.payment_processing_fee_fixed),
                'description': 'Covers payment gateway costs (Paystack, MTN Mobile Money, Vodafone Cash)'
            },
            'payout_fee': {
                'per_transaction': float(settings.payout_transaction_fee),
                'processing_percentage': float(settings.payout_processing_fee_percentage),
                'description': 'Fee per withdrawal to bank or mobile money account'
            }
        })


# =============================================================================
# SELLER AUTHENTICATION API
# =============================================================================

from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken


class SellerAuthView(APIView):
    """
    API endpoint for seller authentication.
    Generates JWT tokens for sellers (separate from user authentication).
    
    POST /api/el-mercado/seller-auth/login/
    {
        "email_or_phone": "seller@example.com",
        "password": "password123"
    }
    
    Returns JWT tokens (access + refresh) that can be used for seller-specific APIs.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        email_or_phone = request.data.get('email_or_phone', '').strip()
        password = request.data.get('password', '')
        
        if not email_or_phone or not password:
            return Response(
                {'error': 'Email/phone and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate using seller's credentials
        seller, error = Seller.authenticate(email_or_phone, password)
        
        if not seller:
            return Response(
                {'error': error},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate tokens for the seller
        # We'll create a custom token that identifies this as a seller token
        refresh = RefreshToken()
        refresh['seller_id'] = str(seller.id)
        refresh['seller_email'] = seller.email
        refresh['token_type'] = 'seller'
        
        # Return token and seller info
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'seller': {
                'id': str(seller.id),
                'display_name': seller.display_name,
                'email': seller.email,
                'phone': str(seller.phone),
                'seller_type': seller.seller_type,
                'status': seller.status,
                'is_verified': seller.is_verified,
                'is_first_login': not seller.is_credentials_set,
            }
        })


class SellerChangePasswordAPIView(APIView):
    """
    API endpoint for sellers to change their password.
    Requires seller JWT token.
    """
    permission_classes = [AllowAny]  # We'll manually verify the seller token
    
    def post(self, request, *args, **kwargs):
        # Get seller from the custom token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            token = AccessToken(auth_header.split(' ')[1])
            
            # Verify this is a seller token
            if token.get('token_type') != 'seller':
                return Response(
                    {'error': 'Invalid seller token'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            seller_id = token.get('seller_id')
            seller = Seller.objects.get(id=seller_id)
        except Exception as e:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        current_password = request.data.get('current_password', '')
        new_password = request.data.get('new_password', '')
        confirm_password = request.data.get('confirm_password', '')
        
        # For first login, current password can be the temp password
        is_first_login = not seller.is_credentials_set
        
        if not is_first_login and not seller.check_password(current_password):
            return Response(
                {'error': 'Current password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(new_password) < 8:
            return Response(
                {'error': 'Password must be at least 8 characters long'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_password != confirm_password:
            return Response(
                {'error': 'Passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        seller.set_password(new_password)
        seller.save()
        
        return Response({
            'message': 'Password changed successfully',
            'is_credentials_set': seller.is_credentials_set
        })


class SellerPasswordResetRequestView(APIView):
    """
    API endpoint for requesting a seller password reset.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        email_or_phone = request.data.get('email_or_phone', '').strip()
        
        if not email_or_phone:
            return Response(
                {'error': 'Email or phone number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find seller (don't reveal if exists)
        try:
            seller = Seller.objects.get(
                Q(email__iexact=email_or_phone) | Q(phone=email_or_phone)
            )
            
            # Generate reset token
            token = seller.generate_password_reset_token()
            
            # Send email with HTML template
            reset_url = f"{settings.FRONTEND_URL}/seller/reset-password/{token}"
            
            try:
                from django.core.mail import EmailMultiAlternatives
                from django.template.loader import render_to_string
                from django.utils.html import strip_tags
                from datetime import datetime
                
                from BioChemSystem.config.brand import get_brand_context
                context = {
                    **get_brand_context(),
                    'seller_name': seller.display_name,
                    'reset_url': reset_url,
                    'expiry_hours': 24,
                    'year': datetime.now().year,
                }

                html_content = render_to_string('el_mercado/emails/seller_password_reset.html', context)
                text_content = strip_tags(html_content)
                
                email = EmailMultiAlternatives(
                    subject='🔐 El Mercado - Password Reset Request',
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[seller.email],
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=True)
            except Exception as e:
                print(f"Failed to send password reset email: {e}")
        except (Seller.DoesNotExist, Seller.MultipleObjectsReturned):
            pass  # Don't reveal if account exists
        
        # Always return success (security best practice)
        return Response({
            'message': 'If an account exists with that email/phone, you will receive a password reset link.'
        })


class SellerPasswordResetConfirmView(APIView):
    """
    API endpoint for confirming a seller password reset.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, token, *args, **kwargs):
        new_password = request.data.get('new_password', '')
        confirm_password = request.data.get('confirm_password', '')
        
        # Find seller with valid token
        seller = None
        for s in Seller.objects.filter(password_reset_token=token):
            if s.is_password_reset_token_valid(token):
                seller = s
                break
        
        if not seller:
            return Response(
                {'error': 'Invalid or expired reset link'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(new_password) < 8:
            return Response(
                {'error': 'Password must be at least 8 characters long'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_password != confirm_password:
            return Response(
                {'error': 'Passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        seller.set_password(new_password)
        seller.save()
        
        return Response({
            'message': 'Password reset successfully'
        })


# =============================================================================
# PAYOUT CONFIRMATION API VIEWS (For President to confirm payouts)
# =============================================================================

class PayoutConfirmationView(APIView):
    """
    API endpoint for President to view and confirm payout requests.
    Uses signed tokens for security - no authentication required.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        """
        Get payout details using a signed token.
        """
        from django.core import signing
        
        token = request.query_params.get('token')
        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Decode the signed token (valid for 7 days)
            data = signing.loads(token, max_age=60 * 60 * 24 * 7)
            payout_id = data.get('payout_id')
            
            payout = PayoutRequest.objects.select_related('wallet__seller').get(id=payout_id)
            seller = payout.wallet.seller
            
            # Format account details
            if payout.payout_method == 'MOBILE_MONEY':
                account_name = payout.account_name or ''
                account_number = str(payout.mobile_money_number) if payout.mobile_money_number else ''
                provider = payout.mobile_money_provider or ''
            else:
                account_name = payout.account_name or ''
                account_number = payout.account_number or ''
                provider = payout.bank_name or ''
            
            return Response({
                'reference': payout.reference,
                'seller_name': seller.display_name,
                'seller_phone': str(seller.phone) if seller.phone else '',
                'seller_email': seller.email or '',
                'amount': str(payout.amount),
                'platform_fee': str(payout.processing_fee),
                'net_amount': str(payout.net_amount),
                'payout_method': payout.get_payout_method_display(),
                'account_name': account_name,
                'account_number': account_number,
                'provider': provider,
                'status': payout.status,
                'status_display': payout.get_status_display(),
                'created_at': payout.created_at.isoformat(),
                'can_confirm': payout.status == 'PENDING',
            })
            
        except signing.BadSignature:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PayoutRequest.DoesNotExist:
            return Response(
                {'error': 'Payout request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request, *args, **kwargs):
        """
        Confirm that payout has been sent (mark as COMPLETED).
        """
        from django.core import signing
        
        token = request.data.get('token')
        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Decode the signed token
            data = signing.loads(token, max_age=60 * 60 * 24 * 7)
            payout_id = data.get('payout_id')
            
            payout = PayoutRequest.objects.get(id=payout_id)
            
            if payout.status != 'PENDING':
                return Response({
                    'error': f'Cannot confirm payout. Current status: {payout.get_status_display()}',
                    'status': payout.status,
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update payout status to COMPLETED
            payout.status = 'COMPLETED'
            payout.status_message = 'Confirmed as sent by President'
            payout.completed_at = timezone.now()
            payout.save(update_fields=['status', 'status_message', 'completed_at', 'updated_at'])
            
            return Response({
                'message': 'Payout marked as completed successfully',
                'reference': payout.reference,
                'status': 'COMPLETED',
            })
            
        except signing.BadSignature:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PayoutRequest.DoesNotExist:
            return Response(
                {'error': 'Payout request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

