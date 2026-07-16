"""
El Mercado API Serializers
==========================
Serializers for the multi-vendor marketplace platform.
"""

from rest_framework import serializers
from django.utils import timezone
from django.conf import settings

from .models import (
    SellerApplication, Seller, SellerWallet, WalletTransaction,
    PayoutRequest, SellerPayoutAccount, Category, Listing, ListingImage,
    ListingVariant, MarketplaceOrder, OrderItem, Review, Conversation,
    Message, Favorite, FollowedSeller, Dispute, MarketplaceSettings
)


# =============================================================================
# USER SERIALIZER (Local to avoid circular imports)
# =============================================================================

class BasicUserInfoSerializer(serializers.Serializer):
    """Lightweight serializer for basic user info"""
    id = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    profile_picture = serializers.ImageField(read_only=True)
    
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Add full name for convenience
        rep['full_name'] = f"{instance.first_name} {instance.last_name}".strip()
        return rep


# =============================================================================
# CATEGORY SERIALIZERS
# =============================================================================

class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    listing_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 
            'icon', 'image', 'is_active', 'display_order',
            'commission_rate', 'children', 'listing_count'
        ]
        read_only_fields = ['id', 'slug']
    
    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data
    
    def get_listing_count(self, obj):
        return obj.listings.filter(status='ACTIVE').count()


class CategoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for dropdowns/lists"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'parent']


# =============================================================================
# CUSTOM JSON FIELD FOR FORMDATA
# =============================================================================

class FormDataJSONField(serializers.JSONField):
    """
    Custom JSONField that handles JSON strings from FormData.
    FormData sends everything as strings, so we need to parse JSON strings
    before the field validation runs.
    """
    def to_internal_value(self, data):
        import json
        # If it's a string, try to parse it as JSON
        if isinstance(data, str):
            if not data or data.strip() == '':
                return self.default if hasattr(self, 'default') else []
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                # If it can't be parsed, return empty list for array fields
                return []
        # Now let the parent handle validation
        return super().to_internal_value(data)


# =============================================================================
# SELLER APPLICATION SERIALIZERS
# =============================================================================

class SellerApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating seller applications"""
    categories_of_interest = FormDataJSONField(required=False, default=list)
    
    class Meta:
        model = SellerApplication
        fields = [
            'seller_type', 'applicant_name', 'applicant_email', 'applicant_phone',
            'business_name', 'business_registration_number', 'business_type',
            'address_line_1', 'address_line_2', 'city', 'region', 'country',
            'id_document', 'id_document_type', 'business_document', 'proof_of_address',
            'description', 'categories_of_interest'
        ]
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)
    
    def validate(self, data):
        # Business sellers must provide business documents
        if data.get('seller_type') == 'BUSINESS':
            if not data.get('business_name'):
                raise serializers.ValidationError({
                    'business_name': 'Business name is required for business sellers.'
                })
            if not data.get('business_document'):
                raise serializers.ValidationError({
                    'business_document': 'Business registration document is required for business sellers.'
                })
        return data


class SellerApplicationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating seller applications - allows partial updates"""
    categories_of_interest = FormDataJSONField(required=False, default=list)
    
    class Meta:
        model = SellerApplication
        fields = [
            'seller_type', 'applicant_name', 'applicant_email', 'applicant_phone',
            'business_name', 'business_registration_number', 'business_type',
            'address_line_1', 'address_line_2', 'city', 'region', 'country',
            'id_document', 'id_document_type', 'business_document', 'proof_of_address',
            'description', 'categories_of_interest'
        ]
        extra_kwargs = {
            # Make all fields optional for partial updates
            'seller_type': {'required': False},
            'applicant_name': {'required': False},
            'applicant_email': {'required': False},
            'applicant_phone': {'required': False},
            'id_document': {'required': False},
            'id_document_type': {'required': False},
            'description': {'required': False},
        }
    
    def validate(self, data):
        # For updates, check business requirements only if changing to BUSINESS type
        # or if already BUSINESS and changing business fields
        instance = self.instance
        seller_type = data.get('seller_type', instance.seller_type if instance else None)
        
        if seller_type == 'BUSINESS':
            # Check business_name - use new value or existing
            business_name = data.get('business_name', instance.business_name if instance else None)
            if not business_name:
                raise serializers.ValidationError({
                    'business_name': 'Business name is required for business sellers.'
                })
            
            # For business_document, only require if instance doesn't have one AND not providing one
            has_existing_doc = instance and instance.business_document
            providing_new_doc = 'business_document' in data and data['business_document']
            
            if not has_existing_doc and not providing_new_doc:
                raise serializers.ValidationError({
                    'business_document': 'Business registration document is required for business sellers.'
                })
        
        return data


class SellerApplicationSerializer(serializers.ModelSerializer):
    """Full serializer for viewing application details"""
    user = BasicUserInfoSerializer(read_only=True)
    reviewed_by = BasicUserInfoSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    seller_type_display = serializers.CharField(source='get_seller_type_display', read_only=True)
    
    class Meta:
        model = SellerApplication
        fields = '__all__'
        read_only_fields = ['id', 'user', 'tracking_code', 'status', 'status_reason', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']


class SellerApplicationListSerializer(serializers.ModelSerializer):
    """Serializer for listing applications - includes all fields needed for display"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    seller_type_display = serializers.CharField(source='get_seller_type_display', read_only=True)
    
    class Meta:
        model = SellerApplication
        fields = [
            'id', 'user', 'tracking_code', 'seller_type', 'seller_type_display',
            'applicant_name', 'applicant_email', 'applicant_phone',
            'business_name', 'business_registration_number', 'business_type',
            'address_line_1', 'address_line_2', 'city', 'region', 'country',
            'id_document', 'id_document_type', 'business_document', 'proof_of_address',
            'description', 'categories_of_interest',
            'status', 'status_display', 'status_reason',
            'created_at', 'updated_at'
        ]


class SellerApplicationStatusSerializer(serializers.ModelSerializer):
    """Public serializer for checking application status by tracking code"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    seller_type_display = serializers.CharField(source='get_seller_type_display', read_only=True)
    seller_dashboard_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SellerApplication
        fields = [
            'tracking_code', 'applicant_name', 'applicant_email',
            'seller_type', 'seller_type_display', 'business_name',
            'status', 'status_display', 'status_reason',
            'seller_dashboard_url', 'created_at', 'updated_at'
        ]
    
    def get_seller_dashboard_url(self, obj):
        """Return seller dashboard URL only if approved"""
        if obj.status == 'APPROVED':
            return '/seller-dashboard/login/?next=/seller-dashboard/'
        return None


# =============================================================================
# SELLER SERIALIZERS
# =============================================================================

class SellerPublicSerializer(serializers.ModelSerializer):
    """Public seller profile - visible to all users"""
    seller_type_display = serializers.CharField(source='get_seller_type_display', read_only=True)
    follower_count = serializers.SerializerMethodField()
    listing_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    
    class Meta:
        model = Seller
        fields = [
            'id', 'display_name', 'slug', 'seller_type', 'seller_type_display',
            'logo', 'logo_url', 'banner', 'banner_url', 'description',
            'shipping_policy', 'return_policy',  # Policy fields
            'website', 'instagram', 'twitter', 'facebook',  # Social links
            'is_verified', 'verification_level', 'average_rating', 'total_reviews',
            'total_sales', 'vacation_mode', 'vacation_message',
            'follower_count', 'listing_count', 'is_following', 'created_at'
        ]
    
    def get_follower_count(self, obj):
        return obj.followers.count()
    
    def get_listing_count(self, obj):
        return obj.listings.filter(status='ACTIVE').count()
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.followers.filter(user=request.user).exists()
        return False


class SellerDashboardSerializer(serializers.ModelSerializer):
    """Full seller profile - for seller's own dashboard"""
    user = BasicUserInfoSerializer(read_only=True)
    wallet = serializers.SerializerMethodField()
    pending_orders_count = serializers.SerializerMethodField()
    active_listings_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Seller
        fields = '__all__'
        read_only_fields = ['id', 'slug', 'application', 'user', 'average_rating', 
                          'total_reviews', 'total_sales', 'created_at', 'updated_at']
    
    def get_wallet(self, obj):
        try:
            wallet = obj.wallet
            return {
                'available_balance': str(wallet.available_balance),
                'pending_balance': str(wallet.pending_balance),
                'currency': wallet.currency
            }
        except SellerWallet.DoesNotExist:
            return None
    
    def get_pending_orders_count(self, obj):
        return obj.orders.filter(status__in=['PENDING', 'PAID', 'PROCESSING']).count()
    
    def get_active_listings_count(self, obj):
        return obj.listings.filter(status='ACTIVE').count()


class SellerListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing sellers"""
    seller_type_display = serializers.CharField(source='get_seller_type_display', read_only=True)
    
    class Meta:
        model = Seller
        fields = [
            'id', 'display_name', 'slug', 'seller_type', 'seller_type_display',
            'logo_url', 'is_verified', 'average_rating', 'total_reviews'
        ]


class SellerWithPoliciesSerializer(serializers.ModelSerializer):
    """Seller serializer with policies - for product detail pages"""
    seller_type_display = serializers.CharField(source='get_seller_type_display', read_only=True)
    business_name = serializers.CharField(source='display_name', read_only=True)
    business_location = serializers.SerializerMethodField()
    total_products = serializers.SerializerMethodField()
    
    class Meta:
        model = Seller
        fields = [
            'id', 'display_name', 'business_name', 'slug', 'seller_type', 'seller_type_display',
            'logo_url', 'description', 'is_verified', 'average_rating', 'total_reviews',
            'total_sales', 'total_products', 'business_location',
            'shipping_policy', 'return_policy', 'created_at'
        ]
    
    def get_business_location(self, obj):
        """Get location from the seller's application"""
        if obj.application:
            parts = [obj.application.city, obj.application.region, obj.application.country]
            return ', '.join(filter(None, parts))
        return None
    
    def get_total_products(self, obj):
        return obj.listings.filter(status='ACTIVE').count()


# =============================================================================
# WALLET & PAYOUT SERIALIZERS
# =============================================================================

class SellerWalletSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.display_name', read_only=True)
    
    class Meta:
        model = SellerWallet
        fields = '__all__'
        read_only_fields = [
            'id', 'seller', 'available_balance', 'pending_balance',
            'total_earned', 'total_withdrawn', 'total_fees_paid',
            'created_at', 'updated_at'
        ]


class WalletTransactionSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'transaction_type', 'transaction_type_display',
            'amount', 'description', 'balance_after', 'created_at'
        ]


class PayoutRequestCreateSerializer(serializers.ModelSerializer):
    """For creating payout requests"""
    
    class Meta:
        model = PayoutRequest
        fields = [
            'amount', 'payout_method',
            'bank_name', 'bank_code', 'account_number', 'account_name',
            'mobile_money_provider', 'mobile_money_number'
        ]
    
    def validate_amount(self, value):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                wallet = request.user.seller_profile.wallet
                if value > wallet.available_balance:
                    raise serializers.ValidationError("Amount exceeds available balance")
                if value < wallet.minimum_payout_amount:
                    raise serializers.ValidationError(
                        f"Minimum payout amount is {wallet.currency} {wallet.minimum_payout_amount}"
                    )
            except (Seller.DoesNotExist, SellerWallet.DoesNotExist):
                raise serializers.ValidationError("Seller wallet not found")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        wallet = request.user.seller_profile.wallet
        validated_data['wallet'] = wallet
        validated_data['currency'] = wallet.currency
        return super().create(validated_data)


class PayoutRequestSerializer(serializers.ModelSerializer):
    """Full payout request details"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payout_method_display = serializers.CharField(source='get_payout_method_display', read_only=True)
    
    class Meta:
        model = PayoutRequest
        fields = '__all__'
        read_only_fields = [
            'id', 'reference', 'wallet', 'status', 'status_message',
            'gateway_reference', 'processed_by', 'processed_at', 'completed_at',
            'created_at', 'updated_at'
        ]


class SellerPayoutAccountSerializer(serializers.ModelSerializer):
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    
    class Meta:
        model = SellerPayoutAccount
        fields = '__all__'
        read_only_fields = ['id', 'seller', 'is_verified', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['seller'] = request.user.seller_profile
        return super().create(validated_data)


# =============================================================================
# LISTING SERIALIZERS
# =============================================================================

class ListingImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ListingImage
        fields = ['id', 'image', 'image_url', 'alt_text', 'display_order']
        read_only_fields = ['id', 'image_url']
    
    def get_image_url(self, obj):
        """Return the correct image URL, preferring the file URL over stored URL."""
        if obj.image:
            try:
                return obj.image.url
            except (ValueError, AttributeError):
                pass
        return obj.image_url or None


class ListingVariantSerializer(serializers.ModelSerializer):
    effective_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = ListingVariant
        fields = [
            'id', 'name', 'sku', 'attributes', 'price',
            'effective_price', 'stock_quantity', 'image', 'is_active'
        ]
        read_only_fields = ['id']


class ListingCreateSerializer(serializers.ModelSerializer):
    """For creating/editing listings"""
    images = ListingImageSerializer(many=True, required=False, read_only=True)
    variants = ListingVariantSerializer(many=True, required=False, read_only=True)
    
    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'listing_type', 'category', 'tags',
            'price', 'compare_at_price', 'currency',
            'stock_quantity', 'track_inventory', 'allow_backorder', 'low_stock_threshold',
            'condition', 'main_image',
            'requires_shipping', 'weight', 'shipping_info',
            'meta_title', 'meta_description',
            'images', 'variants'
        ]
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['seller'] = request.user.seller_profile
        return super().create(validated_data)


class ListingDetailSerializer(serializers.ModelSerializer):
    """Full listing details"""
    seller = SellerWithPoliciesSerializer(read_only=True)  # Full seller with policies
    category = CategoryListSerializer(read_only=True)
    images = ListingImageSerializer(many=True, read_only=True)
    variants = ListingVariantSerializer(many=True, read_only=True)
    listing_type_display = serializers.CharField(source='get_listing_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    can_review = serializers.SerializerMethodField()
    review_eligibility = serializers.SerializerMethodField()
    main_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = '__all__'
        read_only_fields = [
            'id', 'seller', 'slug', 'view_count', 'favorite_count', 'order_count',
            'average_rating', 'review_count', 'created_at', 'updated_at', 'published_at'
        ]
    
    def get_main_image_url(self, obj):
        """Return the correct main image URL, preferring the file URL over stored URL."""
        if obj.main_image:
            try:
                return obj.main_image.url
            except (ValueError, AttributeError):
                pass
        return obj.main_image_url or None
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites.filter(user=request.user).exists()
        return False
    
    def get_can_review(self, obj):
        """Check if the current user can review this listing"""
        eligibility = self.get_review_eligibility(obj)
        return eligibility['can_review']
    
    def get_review_eligibility(self, obj):
        """
        Get detailed review eligibility information.
        Returns dict with:
        - can_review: bool
        - reason: str (why they can't review)
        - status: str ('eligible', 'not_purchased', 'not_delivered', 'already_reviewed', 'not_authenticated')
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return {
                'can_review': False,
                'status': 'not_authenticated',
                'reason': 'You must be logged in to write a review.'
            }
        
        # Check if user has any order with this listing
        from el_mercado.models import MarketplaceOrder
        
        user_orders = MarketplaceOrder.objects.filter(
            buyer=request.user,
            items__listing=obj
        )
        
        if not user_orders.exists():
            return {
                'can_review': False,
                'status': 'not_purchased',
                'reason': 'You can only review products you have purchased.'
            }
        
        # Check if any order has been delivered or completed
        has_delivered_order = user_orders.filter(
            status__in=['DELIVERED', 'COMPLETED']
        ).exists()
        
        if not has_delivered_order:
            return {
                'can_review': False,
                'status': 'not_delivered',
                'reason': 'You can only review products after they have been delivered.'
            }
        
        # Check if already reviewed
        already_reviewed = obj.reviews.filter(reviewer=request.user).exists()
        
        if already_reviewed:
            return {
                'can_review': False,
                'status': 'already_reviewed',
                'reason': 'You have already reviewed this product. You can edit your existing review from the product page.'
            }
        
        return {
            'can_review': True,
            'status': 'eligible',
            'reason': None
        }


class ListingListSerializer(serializers.ModelSerializer):
    """Lightweight listing for grid/list views"""
    seller = SellerListSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    listing_type_display = serializers.CharField(source='get_listing_type_display', read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    main_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'slug', 'listing_type', 'listing_type_display',
            'price', 'compare_at_price', 'currency', 'discount_percentage',
            'main_image', 'main_image_url', 'condition', 'condition_display',
            'is_in_stock', 'stock_quantity', 'average_rating', 'review_count',
            'seller', 'category_name', 'created_at'
        ]
    
    def get_main_image_url(self, obj):
        """Return the correct main image URL, preferring the file URL over stored URL."""
        if obj.main_image:
            try:
                return obj.main_image.url
            except (ValueError, AttributeError):
                pass
        return obj.main_image_url or None


# =============================================================================
# ORDER SERIALIZERS
# =============================================================================

class OrderItemSerializer(serializers.ModelSerializer):
    listing_title = serializers.SerializerMethodField()
    listing_image_url = serializers.SerializerMethodField()
    listing_slug = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'listing', 'variant', 'listing_title', 'listing_image_url',
            'listing_slug', 'variant_name', 'unit_price', 'quantity', 'total_price'
        ]
        read_only_fields = ['id', 'variant_name', 'total_price']
    
    def get_listing_title(self, obj):
        """Return listing_title if set, otherwise get from listing"""
        if obj.listing_title:
            return obj.listing_title
        if obj.listing:
            return obj.listing.title
        return "Unknown Item"
    
    def get_listing_image_url(self, obj):
        """Return listing_image_url if set, otherwise get from listing"""
        if obj.listing_image_url:
            return obj.listing_image_url
        if obj.listing:
            return obj.listing.main_image_url or ''
        return ''
    
    def get_listing_slug(self, obj):
        """Return listing slug for review links"""
        if obj.listing:
            return obj.listing.slug
        return None


class OrderCreateSerializer(serializers.ModelSerializer):
    """For creating orders"""
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    
    class Meta:
        model = MarketplaceOrder
        fields = [
            'seller', 'items',
            'shipping_name', 'shipping_phone', 'shipping_email',
            'shipping_address_line_1', 'shipping_address_line_2',
            'shipping_city', 'shipping_region', 'shipping_country',
            'buyer_notes'
        ]
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must have at least one item")
        return value
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')
        seller = validated_data['seller']
        
        # Calculate totals
        subtotal = 0
        order_items = []
        
        for item_data in items_data:
            listing_id = item_data.get('listing_id')
            variant_id = item_data.get('variant_id')
            quantity = item_data.get('quantity', 1)
            
            listing = Listing.objects.get(id=listing_id, seller=seller, status='ACTIVE')
            variant = None
            
            if variant_id:
                variant = ListingVariant.objects.get(id=variant_id, listing=listing)
                unit_price = variant.effective_price
            else:
                unit_price = listing.price
            
            order_items.append({
                'listing': listing,
                'variant': variant,
                'listing_title': listing.title,
                'listing_image_url': listing.main_image_url or '',
                'variant_name': variant.name if variant else '',
                'unit_price': unit_price,
                'quantity': quantity,
            })
            
            subtotal += unit_price * quantity
        
        # Create order
        validated_data['buyer'] = request.user
        validated_data['subtotal'] = subtotal
        validated_data['total_amount'] = subtotal + validated_data.get('shipping_cost', 0)
        validated_data['commission_rate'] = seller.commission_rate
        validated_data['seller_earnings'] = validated_data['total_amount'] * (1 - seller.commission_rate / 100)
        
        order = MarketplaceOrder.objects.create(**validated_data)
        
        # Create order items
        for item_data in order_items:
            OrderItem.objects.create(order=order, **item_data)
            # Reduce stock
            if item_data['variant']:
                item_data['variant'].stock_quantity -= item_data['quantity']
                item_data['variant'].save()
            else:
                item_data['listing'].reduce_stock(item_data['quantity'])
        
        return order


class OrderDetailSerializer(serializers.ModelSerializer):
    """Full order details"""
    buyer = BasicUserInfoSerializer(read_only=True)
    seller = SellerListSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    delivery_code = serializers.SerializerMethodField()
    
    class Meta:
        model = MarketplaceOrder
        fields = '__all__'
        read_only_fields = [
            'id', 'order_number', 'buyer', 'platform_commission', 'seller_earnings',
            'status_history', 'created_at', 'updated_at'
        ]
    
    def get_delivery_code(self, obj):
        """
        Only show delivery code to the buyer, not to the seller.
        The seller should only receive the code from the buyer in person.
        """
        request = self.context.get('request')
        if request and request.user == obj.buyer:
            # Only show code if order has been shipped
            if obj.status in ['SHIPPED', 'DELIVERED', 'COMPLETED']:
                return obj.delivery_code
        return None


class OrderListSerializer(serializers.ModelSerializer):
    """Order listing with details for buyer view"""
    seller_name = serializers.CharField(source='seller.display_name', read_only=True)
    seller = serializers.SerializerMethodField()
    buyer_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    item_count = serializers.SerializerMethodField()
    shipping_phone = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = MarketplaceOrder
        fields = [
            'id', 'order_number', 'seller', 'seller_name', 'buyer_name',
            'subtotal', 'shipping_cost', 'discount_amount',
            'total_amount', 'currency', 'status', 'status_display',
            'payment_status', 'item_count', 'items', 'created_at',
            # Shipping fields for buyer display
            'shipping_name', 'shipping_phone', 'shipping_email',
            'shipping_address_line_1', 'shipping_address_line_2',
            'shipping_city', 'shipping_region', 'shipping_digital_address',
            'delivery_code', 'tracking_number', 'tracking_url'
        ]
    
    def get_seller(self, obj):
        """Return seller details including contact info"""
        seller = obj.seller
        if seller:
            return {
                'id': str(seller.id),
                'display_name': seller.display_name,
                'email': seller.email,
                'phone': str(seller.phone) if seller.phone else None,
                'logo_url': seller.logo_url,
            }
        return None
    
    def get_buyer_name(self, obj):
        return obj.buyer.get_full_name() or obj.buyer.email
    
    def get_item_count(self, obj):
        return obj.items.count()
    
    def get_shipping_phone(self, obj):
        """Convert PhoneNumber to string for JSON serialization"""
        return str(obj.shipping_phone) if obj.shipping_phone else None


# =============================================================================
# REVIEW SERIALIZERS
# =============================================================================

class ReviewCreateSerializer(serializers.ModelSerializer):
    """For creating reviews - only buyers who have received orders can review"""
    review_type = serializers.CharField(required=False, default='LISTING')
    listing = serializers.PrimaryKeyRelatedField(queryset=Listing.objects.all(), required=False)
    seller = serializers.PrimaryKeyRelatedField(queryset=Seller.objects.all(), required=False)
    order = serializers.PrimaryKeyRelatedField(queryset=MarketplaceOrder.objects.all(), required=False)
    
    class Meta:
        model = Review
        fields = ['review_type', 'listing', 'seller', 'order', 'rating', 'title', 'content']
    
    def validate(self, data):
        request = self.context.get('request')
        user = request.user
        
        # Get listing from context if provided (from the view)
        listing_from_context = self.context.get('listing')
        if listing_from_context and not data.get('listing'):
            data['listing'] = listing_from_context
        
        review_type = data.get('review_type', 'LISTING')
        listing = data.get('listing')
        seller = data.get('seller')
        order = data.get('order')
        
        # Auto-determine review type
        if listing and not seller:
            data['review_type'] = 'LISTING'
        elif seller and not listing:
            data['review_type'] = 'SELLER'
        
        review_type = data.get('review_type')
        
        if review_type == 'LISTING' and not listing:
            raise serializers.ValidationError({'listing': 'Listing is required for listing reviews'})
        
        if review_type == 'SELLER' and not seller:
            raise serializers.ValidationError({'seller': 'Seller is required for seller reviews'})
        
        # =========================================================================
        # CORE CONSTRAINT: User must have PURCHASED AND RECEIVED the product
        # =========================================================================
        
        if review_type == 'LISTING' and listing:
            # Check if user has a DELIVERED or COMPLETED order containing this listing
            from el_mercado.models import MarketplaceOrder, OrderItem
            
            eligible_orders = MarketplaceOrder.objects.filter(
                buyer=user,
                status__in=['DELIVERED', 'COMPLETED'],
                items__listing=listing
            ).distinct()
            
            if not eligible_orders.exists():
                raise serializers.ValidationError({
                    'listing': 'You can only review products you have purchased and received. '
                               'Please wait until your order is delivered.'
                })
            
            # Check if already reviewed this listing
            existing_review = Review.objects.filter(
                reviewer=user,
                listing=listing
            ).exists()
            
            if existing_review:
                raise serializers.ValidationError({
                    'listing': 'You have already reviewed this product.'
                })
            
            # Auto-set the order if not provided
            if not order:
                data['order'] = eligible_orders.first()
        
        if review_type == 'SELLER' and seller:
            # Check if user has any DELIVERED or COMPLETED order from this seller
            from el_mercado.models import MarketplaceOrder
            
            eligible_orders = MarketplaceOrder.objects.filter(
                buyer=user,
                seller=seller,
                status__in=['DELIVERED', 'COMPLETED']
            )
            
            if not eligible_orders.exists():
                raise serializers.ValidationError({
                    'seller': 'You can only review sellers you have purchased from and received orders. '
                              'Please wait until your order is delivered.'
                })
            
            # Check if already reviewed this seller
            existing_review = Review.objects.filter(
                reviewer=user,
                seller=seller
            ).exists()
            
            if existing_review:
                raise serializers.ValidationError({
                    'seller': 'You have already reviewed this seller.'
                })
            
            # Auto-set the order if not provided
            if not order:
                data['order'] = eligible_orders.first()
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['reviewer'] = request.user
        
        # Mark as verified purchase since we validated they have a delivered order
        validated_data['is_verified_purchase'] = True
        
        # Auto-populate seller field from listing if not already set
        # This ensures reviews show up in the seller's dashboard
        listing = validated_data.get('listing')
        if listing and not validated_data.get('seller'):
            validated_data['seller'] = listing.seller
        
        return super().create(validated_data)


class ReviewSerializer(serializers.ModelSerializer):
    """Full review details"""
    reviewer = BasicUserInfoSerializer(read_only=True)
    review_type_display = serializers.CharField(source='get_review_type_display', read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = [
            'id', 'reviewer', 'is_approved', 'is_verified_purchase',
            'helpful_count', 'unhelpful_count', 'created_at', 'updated_at'
        ]


class ReviewListSerializer(serializers.ModelSerializer):
    """Lightweight review listing"""
    reviewer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'review_type', 'rating', 'title', 'content',
            'reviewer_name', 'is_verified_purchase', 'seller_response',
            'seller_responded_at', 'helpful_count', 'created_at'
        ]
    
    def get_reviewer_name(self, obj):
        return obj.reviewer.get_full_name() or obj.reviewer.email


# =============================================================================
# CONVERSATION & MESSAGE SERIALIZERS
# =============================================================================

class MessageSerializer(serializers.ModelSerializer):
    sender_type_display = serializers.CharField(source='get_sender_type_display', read_only=True)
    sender_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender_type', 'sender_type_display', 'sender_name',
            'content', 'attachment', 'attachment_name',
            'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'sender_type', 'sender_user', 'is_read', 'read_at', 'created_at']
    
    def get_sender_name(self, obj):
        if obj.sender_user:
            return obj.sender_user.get_full_name() or obj.sender_user.email
        return "System"


class MessageCreateSerializer(serializers.ModelSerializer):
    """For sending messages"""
    
    class Meta:
        model = Message
        fields = ['content', 'attachment', 'attachment_name']
    
    def create(self, validated_data):
        conversation = self.context.get('conversation')
        request = self.context.get('request')
        
        validated_data['conversation'] = conversation
        validated_data['sender_user'] = request.user
        
        # Determine sender type
        if hasattr(request.user, 'seller_profile') and conversation.seller == request.user.seller_profile:
            validated_data['sender_type'] = 'SELLER'
        else:
            validated_data['sender_type'] = 'BUYER'
        
        return super().create(validated_data)


class ConversationSerializer(serializers.ModelSerializer):
    """Full conversation details"""
    buyer = BasicUserInfoSerializer(read_only=True)
    seller = SellerListSerializer(read_only=True)
    listing = ListingListSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'buyer', 'seller', 'listing', 'order',
            'buyer_unread_count', 'seller_unread_count',
            'last_message', 'unread_count', 'last_message_at', 'created_at'
        ]
    
    def get_last_message(self, obj):
        message = obj.messages.last()
        if message:
            return MessageSerializer(message).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(request.user, 'seller_profile') and obj.seller == request.user.seller_profile:
                return obj.seller_unread_count
            return obj.buyer_unread_count
        return 0


class ConversationListSerializer(serializers.ModelSerializer):
    """Lightweight conversation listing"""
    other_party = serializers.SerializerMethodField()
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    last_message_preview = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'other_party', 'listing_title', 'order',
            'last_message_preview', 'unread_count', 'last_message_at'
        ]
    
    def get_other_party(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(request.user, 'seller_profile') and obj.seller == request.user.seller_profile:
                return {
                    'type': 'buyer',
                    'name': obj.buyer.get_full_name() or obj.buyer.email
                }
            return {
                'type': 'seller',
                'name': obj.seller.display_name,
                'logo_url': obj.seller.logo_url
            }
        return None
    
    def get_last_message_preview(self, obj):
        message = obj.messages.last()
        if message:
            content = message.content[:50]
            return f"{content}..." if len(message.content) > 50 else content
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(request.user, 'seller_profile') and obj.seller == request.user.seller_profile:
                return obj.seller_unread_count
            return obj.buyer_unread_count
        return 0


# =============================================================================
# FAVORITE & FOLLOW SERIALIZERS
# =============================================================================

class FavoriteSerializer(serializers.ModelSerializer):
    listing = ListingListSerializer(read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'listing', 'created_at']
        read_only_fields = ['id', 'created_at']


class FollowedSellerSerializer(serializers.ModelSerializer):
    seller = SellerListSerializer(read_only=True)
    
    class Meta:
        model = FollowedSeller
        fields = ['id', 'seller', 'notify_new_listings', 'notify_sales', 'created_at']
        read_only_fields = ['id', 'created_at']


# =============================================================================
# DISPUTE SERIALIZERS
# =============================================================================

class DisputeCreateSerializer(serializers.ModelSerializer):
    """For creating disputes"""
    
    class Meta:
        model = Dispute
        fields = ['order', 'reason', 'description', 'evidence']
    
    def validate_order(self, value):
        request = self.context.get('request')
        if value.buyer != request.user:
            raise serializers.ValidationError("You can only dispute your own orders")
        if value.status not in ['DELIVERED', 'COMPLETED']:
            raise serializers.ValidationError("Can only dispute delivered or completed orders")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['initiated_by'] = request.user
        
        # Update order status
        order = validated_data['order']
        order.update_status('DISPUTED', 'Dispute opened by buyer')
        
        return super().create(validated_data)


class DisputeSerializer(serializers.ModelSerializer):
    """Full dispute details"""
    order = OrderListSerializer(read_only=True)
    initiated_by = BasicUserInfoSerializer(read_only=True)
    resolved_by = BasicUserInfoSerializer(read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Dispute
        fields = '__all__'
        read_only_fields = [
            'id', 'reference', 'initiated_by', 'status', 'resolution_notes',
            'resolved_by', 'resolved_at', 'refund_amount', 'created_at', 'updated_at'
        ]


# =============================================================================
# MARKETPLACE SETTINGS SERIALIZER
# =============================================================================

class MarketplaceSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketplaceSettings
        fields = '__all__'
