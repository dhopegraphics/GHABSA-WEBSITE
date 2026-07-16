from rest_framework.serializers import ModelSerializer, CharField, UUIDField, Serializer
from phonenumber_field.serializerfields import PhoneNumberField
from products.models import Product, ProductColor, ProductSize
from rest_framework import serializers
from payments.serializers import TransactionSerializer
from utils.cloudinary_utils import get_card_image_url
import logging

logger = logging.getLogger(__name__)


class ProductColorSerializer(serializers.ModelSerializer):
    """Serializer for ProductColor"""
    class Meta:
        model = ProductColor
        fields = ['id', 'name', 'hex_code', 'display_order']


class ProductColorWithImageSerializer(serializers.Serializer):
    """
    Serializer for color with product-specific image
    Used when returning colors for a specific product
    """
    id = serializers.UUIDField()
    name = serializers.CharField()
    hex_code = serializers.CharField()
    display_order = serializers.IntegerField()
    image_url = serializers.CharField(allow_null=True, required=False)


class ProductSizeSerializer(serializers.ModelSerializer):
    """Serializer for ProductSize"""
    class Meta:
        model = ProductSize
        fields = ['id', 'name', 'code', 'display_order']


class ProductListSerializer(ModelSerializer):
    product_image = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    availability_message = serializers.SerializerMethodField()
    is_available_for_purchase = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    
    # Variant fields with product-specific color images
    available_colors = serializers.SerializerMethodField()
    available_sizes = ProductSizeSerializer(many=True, read_only=True)
    
    # Eligibility fields
    target_audience = serializers.CharField(read_only=True)
    target_audience_display = serializers.CharField(source='get_target_audience_display', read_only=True)
    restrict_by_programme = serializers.BooleanField(read_only=True)
    allowed_programmes = serializers.JSONField(read_only=True)
    restrict_by_year = serializers.BooleanField(read_only=True)
    allowed_years = serializers.JSONField(read_only=True)
    eligibility_info = serializers.SerializerMethodField()
    
    # Discount fields - added when discount applies
    original_price = serializers.SerializerMethodField()
    has_discount = serializers.SerializerMethodField()
    discount_info = serializers.SerializerMethodField()
    
    # Variant stock mapping - shows which sizes are available for each color (and vice versa)
    variant_stock_map = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "product_id",
            "product_image",
            "product_name",
            "description",
            "type_of_product",
            "price",
            "original_price",  # Only populated when discount applies
            "has_discount",
            "discount_info",  # Discount details when applicable
            "stock_quantity",
            "low_stock_threshold",
            "status",
            "status_display",
            "is_active",
            "sales_start_date",
            "sales_end_date",
            "availability_message",
            "is_available_for_purchase",
            "is_low_stock",
            "has_colors",
            "has_sizes",
            "available_colors",
            "available_sizes",
            "variant_stock_map",  # Maps color->sizes and size->colors with stock
            # Eligibility fields
            "target_audience",
            "target_audience_display",
            "restrict_by_programme",
            "allowed_programmes",
            "restrict_by_year",
            "allowed_years",
            "eligibility_info",
            "created_at",
            "last_updated",
        ]
        read_only_fields = [
            "product_id",
            "created_at",
            "last_updated",
        ]
    
    def _get_user_pricing(self, obj):
        """Helper to get user-specific pricing (cached per serializer instance)"""
        # Use instance cache to avoid recalculating for same object
        cache_key = f'_pricing_cache_{obj.product_id}'
        if not hasattr(self, cache_key):
            request = self.context.get('request')
            user = None
            if request and request.user and request.user.is_authenticated:
                user = request.user
            setattr(self, cache_key, obj.get_price_for_user(user))
        return getattr(self, cache_key)
    
    def to_representation(self, instance):
        """Override price with discounted price for the current user"""
        data = super().to_representation(instance)
        
        # Get user-specific pricing
        pricing = self._get_user_pricing(instance)
        
        # Replace price with final (potentially discounted) price
        data['price'] = str(pricing['final_price'])
        
        return data
    
    def get_original_price(self, obj):
        """Returns original price only if discount applies, otherwise None"""
        pricing = self._get_user_pricing(obj)
        if pricing['discount_applied']:
            return str(pricing['original_price'])
        return None
    
    def get_has_discount(self, obj):
        """Returns True if user has a discount on this product"""
        pricing = self._get_user_pricing(obj)
        return pricing['discount_applied']
    
    def get_discount_info(self, obj):
        """Returns discount details if applicable, otherwise None"""
        pricing = self._get_user_pricing(obj)
        if not pricing['discount_applied']:
            return None
        
        # Generate savings display
        if pricing['discount_type'] == 'percentage':
            savings_display = f"Save {pricing['discount_percentage']}%"
        else:
            savings_display = f"Save GH₵{pricing['discount_amount']}"
        
        return {
            'discount_name': pricing['discount_name'],
            'discount_type': pricing['discount_type'],
            'discount_percentage': str(pricing['discount_percentage']) if pricing['discount_percentage'] else None,
            'discount_amount': str(pricing['discount_amount']) if pricing['discount_amount'] else None,
            'savings_display': savings_display,
            'reason': pricing['discount_reason'],
        }

    def get_product_image(self, obj: Product):
        """Get optimized product image URL for faster loading"""
        image_url = None
        
        if obj.product_image_url:
            image_url = obj.product_image_url
        elif obj.product_image:
            # For Cloudinary images, get the URL
            try:
                image_url = obj.product_image.url
            except Exception as e:
                logger.error(f"Error getting image URL for product {obj.product_id}: {e}", exc_info=True)
                return None
        
        # Apply Cloudinary optimizations (auto format, auto quality, max width 400px for list view)
        return get_card_image_url(image_url, width=400)
    
    def get_availability_message(self, obj: Product):
        return obj.get_availability_message()
    
    def get_is_available_for_purchase(self, obj: Product):
        """Check both stock availability AND user eligibility"""
        # First check stock/status availability
        if not obj.is_available_for_purchase():
            return False
        
        # Then check user eligibility
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            is_eligible, _ = obj.check_user_eligibility(request.user)
            return is_eligible
        
        # For unauthenticated users, return base availability
        # They'll need to login to check their specific eligibility
        return True
    
    def get_is_low_stock(self, obj: Product):
        return obj.is_low_stock()
    
    def get_eligibility_info(self, obj: Product):
        """
        Get eligibility information based on the current user.
        Returns detailed info about whether user can purchase and why.
        """
        request = self.context.get('request')
        user = None
        if request and request.user and request.user.is_authenticated:
            user = request.user
        
        return obj.get_eligibility_info(user)
    
    def get_available_colors(self, obj: Product):
        """
        Get available colors with optimized product-specific images from ProductColorImage through table
        """
        from products.models import ProductColorImage
        
        colors_data = []
        for color in obj.available_colors.filter(is_active=True):
            color_data = {
                'id': str(color.id),
                'name': color.name,
                'hex_code': color.hex_code,
                'display_order': color.display_order,
                'image_url': None
            }
            
            # Get product-specific image for this color (optimized)
            try:
                color_image = ProductColorImage.objects.get(product=obj, color=color)
                color_data['image_url'] = color_image.get_image_url(optimized=True, width=400)
            except ProductColorImage.DoesNotExist:
                pass
            
            colors_data.append(color_data)
        
        return colors_data
    
    def get_variant_stock_map(self, obj: Product):
        """
        Get a map of available variants based on stock levels.
        
        This enables dynamic filtering on the frontend:
        - When user selects a color, show only sizes available for that color
        - When user selects a size, show only colors available for that size
        - Include stock quantities for real-time availability feedback
        
        Returns:
            {
                'sizes_by_color': {
                    color_id: [
                        {'id': size_id, 'name': 'Medium', 'code': 'M', 'stock': 10}
                    ]
                },
                'colors_by_size': {
                    size_id: [
                        {'id': color_id, 'name': 'Black', 'hex_code': '#000000', 'stock': 10}
                    ]
                },
                'stock_by_variant': {
                    'color_id:size_id': {'stock': 10, 'available': 8}
                }
            }
        """
        from products.models import ProductColorImage
        
        # If product has no variants, return empty map
        if not obj.has_colors and not obj.has_sizes:
            return None
        
        result = {
            'sizes_by_color': {},
            'colors_by_size': {},
            'stock_by_variant': {}
        }
        
        # Get all variant stocks with related color/size data
        variant_stocks = obj.variant_stocks.filter(
            stock_quantity__gt=0
        ).select_related('color', 'size')
        
        # Build mappings
        for stock in variant_stocks:
            color_id = str(stock.color.id) if stock.color else 'no_color'
            size_id = str(stock.size.id) if stock.size else 'no_size'
            
            # Stock by variant key (for direct lookup)
            variant_key = f"{color_id}:{size_id}"
            result['stock_by_variant'][variant_key] = {
                'stock': stock.stock_quantity,
                'available': stock.available_quantity,
                'is_low': stock.is_low_stock
            }
            
            # Sizes available for this color
            if stock.color and stock.size:
                if color_id not in result['sizes_by_color']:
                    result['sizes_by_color'][color_id] = []
                
                # Check if size already added for this color
                if not any(s['id'] == size_id for s in result['sizes_by_color'][color_id]):
                    result['sizes_by_color'][color_id].append({
                        'id': size_id,
                        'name': stock.size.name,
                        'code': stock.size.code,
                        'stock': stock.stock_quantity,
                        'display_order': stock.size.display_order
                    })
            
            # Colors available for this size
            if stock.size and stock.color:
                if size_id not in result['colors_by_size']:
                    result['colors_by_size'][size_id] = []
                
                # Check if color already added for this size
                if not any(c['id'] == color_id for c in result['colors_by_size'][size_id]):
                    # Get color image if available
                    image_url = None
                    try:
                        color_image = ProductColorImage.objects.get(product=obj, color=stock.color)
                        image_url = color_image.get_image_url(optimized=True, width=400)
                    except ProductColorImage.DoesNotExist:
                        pass
                    
                    result['colors_by_size'][size_id].append({
                        'id': color_id,
                        'name': stock.color.name,
                        'hex_code': stock.color.hex_code,
                        'stock': stock.stock_quantity,
                        'image_url': image_url,
                        'display_order': stock.color.display_order
                    })
        
        # Sort by display_order
        for color_id in result['sizes_by_color']:
            result['sizes_by_color'][color_id].sort(key=lambda x: x.get('display_order', 0))
        
        for size_id in result['colors_by_size']:
            result['colors_by_size'][size_id].sort(key=lambda x: x.get('display_order', 0))
        
        return result


# Integrated payment system serializers

class VariantSelectionSerializer(serializers.Serializer):
    """Serializer for individual variant selection (color + size for a quantity)"""
    color_id = serializers.UUIDField(required=False, allow_null=True)
    size_id = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1)
    
    # Per-variant recipient fields
    is_gift_purchase = serializers.BooleanField(default=False, required=False)
    is_purchase_on_behalf = serializers.BooleanField(default=False, required=False)
    purchased_for_phone = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True)
    gift_message = serializers.CharField(max_length=500, required=False, allow_null=True, allow_blank=True)
    
    def validate_color_id(self, value):
        """Validate color exists and is active"""
        if value:
            try:
                ProductColor.objects.get(id=value, is_active=True)
            except ProductColor.DoesNotExist:
                raise serializers.ValidationError("Invalid color selection")
        return value
    
    def validate_size_id(self, value):
        """Validate size exists and is active"""
        if value:
            try:
                ProductSize.objects.get(id=value, is_active=True)
            except ProductSize.DoesNotExist:
                raise serializers.ValidationError("Invalid size selection")
        return value


class ProductPaymentInitializeSerializer(serializers.Serializer):
    """Serializer for initializing product payment"""
    
    product_id = serializers.UUIDField(required=True)
    quantity = serializers.IntegerField(default=1, min_value=1, max_value=100)
    gateway = serializers.CharField(default='paystack', max_length=50)
    callback_url = serializers.CharField(required=True, max_length=500)  # Changed from URLField to CharField to support custom schemes
    
    # Variant selections (list of {color_id, size_id, quantity})
    variant_selections = serializers.ListField(
        child=VariantSelectionSerializer(),
        required=False,
        allow_empty=True,
        help_text="List of variant selections with their quantities"
    )
    
    # Optional customer info (for guest checkout)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    
    # ========== Purchase Type Fields ==========
    is_gift_purchase = serializers.BooleanField(
        default=False,
        help_text="True if this is a gift with optional message"
    )
    is_purchase_on_behalf = serializers.BooleanField(
        default=False,
        help_text="True if buying on behalf of someone (they requested it)"
    )
    purchased_for_phone = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Phone number of the person this product is for"
    )
    gift_message = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Optional gift message (only for gift purchases)"
    )
    
    def validate_callback_url(self, value):
        """Validate callback URL - allow custom schemes for mobile apps"""
        if not value:
            raise serializers.ValidationError("Callback URL is required")
        
        # Allow custom schemes like cssknust://, myapp://, etc. as well as http/https
        if not (value.startswith('http://') or value.startswith('https://') or '://' in value):
            raise serializers.ValidationError("Invalid URL format")
        
        return value
    
    def validate_gateway(self, value):
        """Validate gateway exists and is active"""
        from payments.models import PaymentGateway
        try:
            PaymentGateway.objects.get(name=value, is_active=True, status='active')
        except PaymentGateway.DoesNotExist:
            raise serializers.ValidationError(f"Gateway '{value}' not available")
        return value
    
    def validate_product_id(self, value):
        """Validate product exists"""
        try:
            Product.objects.get(product_id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError(f"Product not found")
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        product_id = attrs.get('product_id')
        quantity = attrs.get('quantity')
        variant_selections = attrs.get('variant_selections', [])
        
        try:
            product = Product.objects.get(product_id=product_id)
            
            # If variant selections provided, validate them match product requirements
            if variant_selections:
                total_variant_quantity = sum(v['quantity'] for v in variant_selections)
                
                # Ensure total variant quantity matches order quantity
                if total_variant_quantity != quantity:
                    raise serializers.ValidationError({
                        'variant_selections': f'Total variant quantity ({total_variant_quantity}) must match order quantity ({quantity})'
                    })
                
                # Validate product has colors/sizes if they're being selected
                for selection in variant_selections:
                    if selection.get('color_id') and not product.has_colors:
                        raise serializers.ValidationError({
                            'variant_selections': 'This product does not have color options'
                        })
                    if selection.get('size_id') and not product.has_sizes:
                        raise serializers.ValidationError({
                            'variant_selections': 'This product does not have size options'
                        })
                    
                    # Validate selected color/size belongs to product
                    if selection.get('color_id'):
                        if not product.available_colors.filter(id=selection['color_id']).exists():
                            raise serializers.ValidationError({
                                'variant_selections': 'Selected color not available for this product'
                            })
                    
                    if selection.get('size_id'):
                        if not product.available_sizes.filter(id=selection['size_id']).exists():
                            raise serializers.ValidationError({
                                'variant_selections': 'Selected size not available for this product'
                            })
            
            # If product has variants but none provided, require them
            elif product.has_colors or product.has_sizes:
                raise serializers.ValidationError({
                    'variant_selections': 'This product requires color/size selections'
                })
                
        except Product.DoesNotExist:
            pass  # Already handled in validate_product_id
        
        # Validate purchase type fields
        is_gift = attrs.get('is_gift_purchase', False)
        is_on_behalf = attrs.get('is_purchase_on_behalf', False)
        purchased_for_phone = attrs.get('purchased_for_phone', '')
        gift_message = attrs.get('gift_message', '')
        
        # Cannot be both gift and on_behalf at the same time
        if is_gift and is_on_behalf:
            raise serializers.ValidationError({
                'is_gift_purchase': 'Cannot be both a gift and a purchase on behalf at the same time'
            })
        
        # If either gift or on_behalf, require phone number
        if (is_gift or is_on_behalf) and not purchased_for_phone:
            raise serializers.ValidationError({
                'purchased_for_phone': 'Recipient phone number is required for gift purchases or purchases on behalf'
            })
        
        # Gift message only allowed for gift purchases
        if gift_message and not is_gift:
            raise serializers.ValidationError({
                'gift_message': 'Gift message is only allowed for gift purchases'
            })
        
        return attrs


class ProductPaymentVerifySerializer(serializers.Serializer):
    """Serializer for verifying product payment"""
    
    reference = serializers.CharField(max_length=100, required=True)
    
    def validate_reference(self, value):
        """Validate reference exists"""
        from payments.models import Transaction
        try:
            Transaction.objects.get(reference=value, transaction_type='payment')
        except Transaction.DoesNotExist:
            raise serializers.ValidationError(f"Transaction not found")
        return value


class MerchandiseCollectionSerializer(serializers.Serializer):
    """Serializer for marking merchandise as collected"""
    
    validation_code = serializers.CharField(max_length=10, required=True)
    
    def validate_validation_code(self, value):
        """Validate validation code format"""
        if len(value) != 6:
            raise serializers.ValidationError("Validation code must be 6 characters")
        return value.upper()


class ProductTransactionSerializer(TransactionSerializer):
    """Extended transaction serializer with product-specific fields"""
    
    product_details = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    variant_selections = serializers.SerializerMethodField()
    
    class Meta(TransactionSerializer.Meta):
        fields = TransactionSerializer.Meta.fields + [
            'product_details',
            'quantity',
            'variant_selections',
        ]
    
    def get_product_details(self, obj):
        """Get product details from content object"""
        if obj.content_object and isinstance(obj.content_object, Product):
            product = obj.content_object
            return {
                'product_id': str(product.product_id),
                'product_name': product.product_name,
                'product_type': product.type_of_product,
                'product_image': product.product_image.url if product.product_image else product.product_image_url,
                'has_colors': product.has_colors,
                'has_sizes': product.has_sizes,
                'available_colors': ProductColorSerializer(product.available_colors.filter(is_active=True), many=True).data,
                'available_sizes': ProductSizeSerializer(product.available_sizes.filter(is_active=True), many=True).data,
            }
        return None
    
    def get_quantity(self, obj):
        """Get quantity from metadata"""
        return obj.metadata.get('quantity', 1)
    
    def get_variant_selections(self, obj):
        """
        Get variant selections with full color/size details
        
        NEW ARCHITECTURE: Read from ProductPayment.variant_selections (product-specific data)
        Priority:
        1. Check ProductPayment.variant_selections (new, proper location)
        2. Fall back to metadata['variant_selections'] (backward compatibility)
        """
        # Try ProductPayment first (new architecture - product data in product model)
        try:
            # Changed from OneToOne (product_payment) to ForeignKey (product_payments)
            if hasattr(obj, 'product_payments'):
                product_payment = obj.product_payments.first()
                if product_payment and product_payment.variant_selections:
                    from products.models import ProductColor, ProductSize
                    formatted = []
                    
                    for selection in product_payment.variant_selections:
                        item = {'quantity': selection.get('quantity', 1)}
                        
                        # Get color details
                        color_id = selection.get('color_id')
                        if color_id:
                            try:
                                color = ProductColor.objects.get(id=color_id)
                                item['color'] = {
                                    'id': str(color.id),
                                    'name': color.name,
                                    'hex_code': color.hex_code
                                }
                            except ProductColor.DoesNotExist:
                                pass
                        
                        # Get size details
                        size_id = selection.get('size_id')
                        if size_id:
                            try:
                                size = ProductSize.objects.get(id=size_id)
                                item['size'] = {
                                    'id': str(size.id),
                                    'name': size.name,
                                    'code': size.code
                                }
                            except ProductSize.DoesNotExist:
                                pass
                        
                        formatted.append(item)
                    
                    return formatted
        except Exception as e:
            # If ProductPayment doesn't exist or error, fall back
            logger.warning(f"Error reading from ProductPayment.variant_selections: {e}")
        
        # Fall back to metadata (for backward compatibility)
        return obj.metadata.get('variant_selections', [])


# Cart checkout serializers

class CartItemSerializer(serializers.Serializer):
    """Serializer for a single cart item"""
    
    product_id = serializers.UUIDField(required=True)
    quantity = serializers.IntegerField(min_value=1, max_value=100, default=1)
    variant_selections = serializers.ListField(
        child=VariantSelectionSerializer(),
        required=False,
        allow_empty=True,
        help_text="List of variant selections with their quantities and recipient info"
    )
    
    # Per-item recipient fields (fallback if no variant-level recipient)
    is_gift_purchase = serializers.BooleanField(default=False, required=False)
    is_purchase_on_behalf = serializers.BooleanField(default=False, required=False)
    purchased_for_phone = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True)
    gift_message = serializers.CharField(max_length=500, required=False, allow_null=True, allow_blank=True)
    
    def validate_product_id(self, value):
        """Validate product exists"""
        try:
            Product.objects.get(product_id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")
        return value
    
    def validate(self, attrs):
        """Validate cart item"""
        product_id = attrs.get('product_id')
        quantity = attrs.get('quantity')
        variant_selections = attrs.get('variant_selections', [])
        
        try:
            product = Product.objects.get(product_id=product_id)
            
            # Check product availability
            if not product.is_available_for_purchase():
                raise serializers.ValidationError({
                    'product_id': f"Product '{product.product_name}' is not available: {product.get_availability_message()}"
                })
            
            # Check stock
            if product.stock_quantity < quantity:
                raise serializers.ValidationError({
                    'quantity': f"Insufficient stock for '{product.product_name}'. Only {product.stock_quantity} available."
                })
            
            # Validate variants if provided
            if variant_selections:
                total_variant_quantity = sum(v['quantity'] for v in variant_selections)
                
                if total_variant_quantity != quantity:
                    raise serializers.ValidationError({
                        'variant_selections': f'Total variant quantity ({total_variant_quantity}) must match order quantity ({quantity})'
                    })
                
                for selection in variant_selections:
                    if selection.get('color_id') and not product.has_colors:
                        raise serializers.ValidationError({
                            'variant_selections': f'Product "{product.product_name}" does not have color options'
                        })
                    if selection.get('size_id') and not product.has_sizes:
                        raise serializers.ValidationError({
                            'variant_selections': f'Product "{product.product_name}" does not have size options'
                        })
                    
                    if selection.get('color_id'):
                        if not product.available_colors.filter(id=selection['color_id']).exists():
                            raise serializers.ValidationError({
                                'variant_selections': f'Selected color not available for "{product.product_name}"'
                            })
                    
                    if selection.get('size_id'):
                        if not product.available_sizes.filter(id=selection['size_id']).exists():
                            raise serializers.ValidationError({
                                'variant_selections': f'Selected size not available for "{product.product_name}"'
                            })
            
            elif product.has_colors or product.has_sizes:
                raise serializers.ValidationError({
                    'variant_selections': f'Product "{product.product_name}" requires color/size selections'
                })
            
        except Product.DoesNotExist:
            pass  # Already handled
        
        return attrs


class CartCheckoutSerializer(serializers.Serializer):
    """Serializer for cart checkout with multiple items"""
    
    cart_items = serializers.ListField(
        child=CartItemSerializer(),
        min_length=1,
        help_text="List of cart items to checkout"
    )
    gateway = serializers.CharField(default='paystack', max_length=50)
    callback_url = serializers.CharField(required=True, max_length=500)
    
    # Purchase type fields
    is_gift_purchase = serializers.BooleanField(default=False, required=False)
    is_purchase_on_behalf = serializers.BooleanField(default=False, required=False)
    purchased_for_phone = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True)
    gift_message = serializers.CharField(max_length=500, required=False, allow_null=True, allow_blank=True)
    
    def validate_gateway(self, value):
        """Validate gateway exists and is active"""
        from payments.models import PaymentGateway
        try:
            PaymentGateway.objects.get(name=value, is_active=True, status='active')
        except PaymentGateway.DoesNotExist:
            raise serializers.ValidationError(f"Gateway '{value}' not available")
        return value
    
    def validate_callback_url(self, value):
        """Validate callback URL"""
        if not value:
            raise serializers.ValidationError("Callback URL is required")
        
        if not (value.startswith('http://') or value.startswith('https://') or '://' in value):
            raise serializers.ValidationError("Invalid URL format")
        
        return value
    
    def validate(self, data):
        """Validate purchase type fields together"""
        is_gift = data.get('is_gift_purchase', False)
        is_on_behalf = data.get('is_purchase_on_behalf', False)
        purchased_for_phone = data.get('purchased_for_phone')
        
        # Can't be both gift and on_behalf
        if is_gift and is_on_behalf:
            raise serializers.ValidationError("Cannot be both gift purchase and on-behalf purchase")
        
        # If gift or on_behalf, phone is required
        if (is_gift or is_on_behalf) and not purchased_for_phone:
            raise serializers.ValidationError("Recipient phone number is required for gift or on-behalf purchases")
        
        return data


class ProductPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for ProductPayment records.
    Returns individual purchases with their own validation codes.
    Used in my_purchases endpoint to show each product purchased separately.
    """
    
    product_details = serializers.SerializerMethodField()
    formatted_variant_selections = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    can_change_preferences = serializers.SerializerMethodField()
    needs_preferences = serializers.SerializerMethodField()
    collection_summary = serializers.SerializerMethodField()
    formatted_collection_details = serializers.SerializerMethodField()
    discount_info = serializers.SerializerMethodField()
    buyer_info = serializers.SerializerMethodField()
    recipient_info = serializers.SerializerMethodField()
    
    class Meta:
        from products.models import ProductPayment
        model = ProductPayment
        fields = [
            'payment_id',
            'reference',
            'transaction_validation_code',
            'product',
            'product_details',
            'amount',
            'price_at_purchase',
            'original_price',
            'quantity',
            'variant_selections',
            'formatted_variant_selections',
            'payment_successful',
            'merchandise_taken',
            'merchandise_taken_at',
            'taken_by',
            'payed_at',
            'academic_year',
            'customer_name',
            'customer_email',
            'status',
            # Discount info
            'discount_applied',
            'discount_amount',
            'discount_type',
            'discount_percentage',
            'discount_reason',
            'discount_info',
            # Purchase type fields
            'is_gift_purchase',
            'is_purchase_on_behalf',
            'purchased_for_phone',
            'gift_message',
            'gift_linked_at',
            'buyer_info',
            'recipient_info',
            # Preference change tracking
            'preference_change_count',
            'preferences_last_updated_at',
            'preferences_locked',
            'can_change_preferences',
            'needs_preferences',
            # Collection tracking (per-variant)
            'collection_details',
            'collection_summary',
            'formatted_collection_details',
        ]
    
    def get_product_details(self, obj):
        """Get product details"""
        if obj.product:
            product = obj.product
            return {
                'product_id': str(product.product_id),
                'product_name': product.product_name,
                'product_type': product.type_of_product,
                'product_image': product.product_image.url if product.product_image else product.product_image_url,
                'has_colors': product.has_colors,
                'has_sizes': product.has_sizes,
                'available_colors': ProductColorSerializer(product.available_colors.filter(is_active=True), many=True).data,
                'available_sizes': ProductSizeSerializer(product.available_sizes.filter(is_active=True), many=True).data,
            }
        return None
    
    def get_formatted_variant_selections(self, obj):
        """Get variant selections with full color/size details"""
        if not obj.variant_selections:
            return []
        
        formatted = []
        for selection in obj.variant_selections:
            item = {'quantity': selection.get('quantity', 1)}
            
            # Get color details
            color_id = selection.get('color_id')
            if color_id:
                try:
                    color = ProductColor.objects.get(id=color_id)
                    item['color'] = {
                        'id': str(color.id),
                        'name': color.name,
                        'hex_code': color.hex_code
                    }
                except ProductColor.DoesNotExist:
                    item['color'] = {'id': color_id, 'name': 'Unknown', 'hex_code': ''}
            
            # Get size details
            size_id = selection.get('size_id')
            if size_id:
                try:
                    size = ProductSize.objects.get(id=size_id)
                    item['size'] = {
                        'id': str(size.id),
                        'name': size.name,
                        'code': size.code
                    }
                except ProductSize.DoesNotExist:
                    item['size'] = {'id': size_id, 'name': 'Unknown', 'code': ''}
            
            formatted.append(item)
        
        return formatted
    
    def get_status(self, obj):
        """Get purchase status including partial collection"""
        if not obj.payment_successful:
            return 'pending'
        if obj.merchandise_taken:
            return 'collected'
        # Check for partial collection
        if obj.collection_details:
            summary = obj.get_collection_summary()
            if summary['overall_status'] == 'partial':
                return 'partial'
        return 'success'
    
    def get_can_change_preferences(self, obj):
        """Check if preferences can be changed"""
        can_change, reason = obj.can_change_preferences()
        return {
            'allowed': can_change,
            'reason': reason if not can_change else '',
            'changes_remaining': max(0, 1 - obj.preference_change_count)
        }
    
    def get_needs_preferences(self, obj):
        """Check if preferences are missing"""
        needs, missing = obj.needs_preferences()
        return {
            'needs': needs,
            'missing': missing
        }
    
    def get_collection_summary(self, obj):
        """Get collection summary for the payment"""
        return obj.get_collection_summary()
    
    def get_formatted_collection_details(self, obj):
        """Get collection details with resolved color/size names"""
        return obj.get_formatted_collection_details()
    
    def get_discount_info(self, obj):
        """Get formatted discount information for this purchase"""
        if not obj.discount_applied:
            return None
        
        return {
            'discount_applied': True,
            'discount_name': obj.discount.name if obj.discount else None,
            'discount_type': obj.discount_type,
            'discount_percentage': str(obj.discount_percentage) if obj.discount_percentage else None,
            'discount_amount_per_unit': str(obj.discount_amount) if obj.discount_amount else None,
            'total_savings': str(obj.discount_amount * obj.quantity) if obj.discount_amount else None,
            'original_unit_price': str(obj.original_price) if obj.original_price else None,
            'paid_unit_price': str(obj.price_at_purchase) if obj.price_at_purchase else None,
            'discount_reason': obj.discount_reason,
            'savings_display': self._get_savings_display(obj),
        }
    
    def _get_savings_display(self, obj):
        """Generate a human-readable savings message"""
        if not obj.discount_applied or not obj.discount_amount:
            return None
        
        total_savings = obj.discount_amount * obj.quantity
        
        if obj.discount_type == 'percentage' and obj.discount_percentage:
            return f"Saved GHS {total_savings:.2f} ({obj.discount_percentage}% off)"
        else:
            return f"Saved GHS {total_savings:.2f}"
    
    def get_buyer_info(self, obj):
        """Get buyer information"""
        if obj.buyer:
            return {
                'id': str(obj.buyer.id),
                'name': obj.buyer.get_full_name(),
                'email': obj.buyer.email,
                'phone': str(obj.buyer.phone) if obj.buyer.phone else None,
            }
        return {
            'name': obj.customer_name,
            'email': obj.customer_email,
            'phone': str(obj.phone) if obj.phone else None,
        }
    
    def get_recipient_info(self, obj):
        """Get recipient information for gift purchases and purchases on behalf"""
        if not obj.is_gift_purchase and not obj.is_purchase_on_behalf:
            return None
        
        purchase_type = 'gift' if obj.is_gift_purchase else 'on_behalf'
        
        if obj.purchased_for_user:
            return {
                'id': str(obj.purchased_for_user.id),
                'name': obj.purchased_for_user.get_full_name(),
                'email': obj.purchased_for_user.email,
                'phone': str(obj.purchased_for_user.phone) if obj.purchased_for_user.phone else None,
                'linked': True,
                'linked_at': obj.gift_linked_at.isoformat() if obj.gift_linked_at else None,
                'purchase_type': purchase_type,
            }
        else:
            return {
                'phone': str(obj.purchased_for_phone) if obj.purchased_for_phone else None,
                'linked': False,
                'message': 'Waiting for recipient to register',
                'purchase_type': purchase_type,
            }
