"""
Unified Checkout Service
========================

Provides a unified checkout experience for both Merchandise (products)
and El Mercado (marketplace) purchases within a single transaction.

Features:
- Single cart checkout for items from multiple sources
- Splits items by source (merchandise vs el_mercado)
- Single payment gateway transaction
- Routes post-payment processing to appropriate services
- Generates validation codes for both systems
- Handles mixed cart scenarios

Usage:
    from payments.services.unified_checkout_service import UnifiedCheckoutService
    
    # Initialize unified checkout
    result = UnifiedCheckoutService.initialize_checkout(
        user=request.user,
        cart_items=[
            {
                'source': 'merchandise',
                'product_id': 'uuid-here',
                'quantity': 2,
                'variant_selections': [...],
                'is_gift_purchase': False,
            },
            {
                'source': 'el_mercado',
                'listing_id': 'listing-uuid',
                'seller_id': 'seller-uuid',
                'quantity': 1,
                'variant_id': 'optional-variant-id',
            }
        ],
        callback_url='https://...',
    )
"""

from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass
import logging
import secrets
import string

from django.db import transaction as db_transaction
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings

from payments.services.transaction_service import TransactionService
from payments.models import Transaction
from utils.utils import normalize_phone


logger = logging.getLogger(__name__)


class UnifiedCheckoutError(Exception):
    """Base exception for unified checkout errors"""
    pass


class CartValidationError(UnifiedCheckoutError):
    """Error when cart validation fails"""
    pass


class InsufficientStockError(UnifiedCheckoutError):
    """Error when stock is insufficient"""
    pass


class ProductNotFoundError(UnifiedCheckoutError):
    """Error when product/listing is not found"""
    pass


class PaymentInitializationError(UnifiedCheckoutError):
    """Error during payment initialization"""
    pass


@dataclass
class CheckoutItem:
    """Represents a validated checkout item"""
    source: str  # 'merchandise' or 'el_mercado'
    item_id: str  # product_id or listing_id
    name: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    original_metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source,
            'item_id': self.item_id,
            'name': self.name,
            'quantity': self.quantity,
            'unit_price': str(self.unit_price),
            'total_price': str(self.total_price),
            'metadata': self.original_metadata,
        }


@dataclass 
class CheckoutSummary:
    """Summary of checkout totals by source"""
    merchandise_items: List[CheckoutItem]
    el_mercado_items: List[CheckoutItem]
    merchandise_total: Decimal
    el_mercado_total: Decimal
    grand_total: Decimal
    currency: str = 'GHS'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'merchandise_items': [i.to_dict() for i in self.merchandise_items],
            'el_mercado_items': [i.to_dict() for i in self.el_mercado_items],
            'merchandise_total': str(self.merchandise_total),
            'el_mercado_total': str(self.el_mercado_total),
            'grand_total': str(self.grand_total),
            'currency': self.currency,
            'merchandise_count': len(self.merchandise_items),
            'el_mercado_count': len(self.el_mercado_items),
            'total_items': len(self.merchandise_items) + len(self.el_mercado_items),
        }


class UnifiedCheckoutService:
    """
    Service for handling unified checkout across Merchandise and El Mercado.
    
    This service allows users to checkout items from both:
    - Merchandise (products from the products app)
    - El Mercado (marketplace listings from third-party sellers)
    
    In a single payment transaction.
    """
    
    DEFAULT_GATEWAY = 'paystack'
    
    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================
    
    @staticmethod
    def _normalize_phone_international(phone: str) -> str:
        """
        Normalize phone number to international format +233XXXXXXXXX
        
        Handles various input formats:
        - 0597959032 → +233597959032
        - 233597959032 → +233597959032
        - +233597959032 → +233597959032 (unchanged)
        - 597959032 → +233597959032
        """
        if not phone:
            return phone
        
        # Remove spaces and common separators
        cleaned = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Handle 0XXXXXXXXX format (10 digits starting with 0)
        if cleaned.startswith("0") and len(cleaned) == 10:
            return "+233" + cleaned[1:]
        
        # Handle 233XXXXXXXXX format without + (12 digits)
        elif cleaned.startswith("233") and len(cleaned) == 12 and not cleaned.startswith("+"):
            return "+" + cleaned
        
        # Handle already international format +233XXXXXXXXX
        elif cleaned.startswith("+233") and len(cleaned) == 13:
            return cleaned
        
        # Handle 9-digit local format (XXXXXXXXX)
        elif len(cleaned) == 9 and cleaned.isdigit():
            return "+233" + cleaned
        
        # Return as-is if unrecognized but log warning
        logger.warning(f"Unrecognized phone format, returning as-is: {phone}")
        return phone
    
    # ==========================================================================
    # CART VALIDATION & PROCESSING
    # ==========================================================================
    
    @classmethod
    def validate_and_process_cart(
        cls,
        user,
        cart_items: List[Dict[str, Any]],
    ) -> CheckoutSummary:
        """
        Validate all cart items and calculate totals.
        
        Args:
            user: User making the purchase
            cart_items: List of cart items with source field
        
        Returns:
            CheckoutSummary with validated items and totals
        
        Raises:
            CartValidationError: If validation fails
            ProductNotFoundError: If product/listing not found
            InsufficientStockError: If stock insufficient
        """
        if not cart_items:
            raise CartValidationError("Cart is empty")
        
        merchandise_items: List[CheckoutItem] = []
        el_mercado_items: List[CheckoutItem] = []
        
        merchandise_total = Decimal('0.00')
        el_mercado_total = Decimal('0.00')
        
        for item in cart_items:
            source = item.get('source', 'merchandise')
            
            if source == 'merchandise':
                validated_item = cls._validate_merchandise_item(user, item)
                merchandise_items.append(validated_item)
                merchandise_total += validated_item.total_price
                
            elif source == 'el_mercado':
                validated_item = cls._validate_el_mercado_item(user, item)
                el_mercado_items.append(validated_item)
                el_mercado_total += validated_item.total_price
                
            else:
                raise CartValidationError(f"Unknown item source: {source}")
        
        grand_total = merchandise_total + el_mercado_total
        
        return CheckoutSummary(
            merchandise_items=merchandise_items,
            el_mercado_items=el_mercado_items,
            merchandise_total=merchandise_total,
            el_mercado_total=el_mercado_total,
            grand_total=grand_total,
        )
    
    @classmethod
    def _validate_merchandise_item(cls, user, item: Dict[str, Any]) -> CheckoutItem:
        """Validate a merchandise item from the products app"""
        from products.models import Product, ProductColor, ProductSize
        
        product_id = item.get('product_id')
        quantity = item.get('quantity', 1)
        variant_selections = item.get('variant_selections', [])
        
        try:
            product = Product.objects.get(product_id=product_id)
        except Product.DoesNotExist:
            raise ProductNotFoundError(f"Product not found: {product_id}")
        
        # Check availability
        if not product.is_available_for_purchase():
            raise CartValidationError(
                f"Product '{product.product_name}' not available: {product.get_availability_message()}"
            )
        
        # Check user eligibility
        is_eligible, eligibility_message = product.check_user_eligibility(user)
        if not is_eligible:
            raise CartValidationError(
                f"Not eligible to purchase '{product.product_name}': {eligibility_message}"
            )
        
        # Check stock
        if product.stock_quantity < quantity:
            raise InsufficientStockError(
                f"Insufficient stock for '{product.product_name}'. "
                f"Available: {product.stock_quantity}, Requested: {quantity}"
            )
        
        # Validate variant selections if required
        if product.has_colors or product.has_sizes:
            if not variant_selections or len(variant_selections) == 0:
                missing = []
                if product.has_colors:
                    missing.append('color')
                if product.has_sizes:
                    missing.append('size')
                raise CartValidationError(
                    f"Product '{product.product_name}' requires {' and '.join(missing)} preferences."
                )
            
            for idx, selection in enumerate(variant_selections):
                if product.has_colors and not selection.get('color_id'):
                    raise CartValidationError(
                        f"Product '{product.product_name}': Color required for item {idx + 1}"
                    )
                if product.has_sizes and not selection.get('size_id'):
                    raise CartValidationError(
                        f"Product '{product.product_name}': Size required for item {idx + 1}"
                    )
        
        # Get user-specific pricing
        pricing_info = product.get_price_for_user(user)
        unit_price = pricing_info['final_price']
        total_price = unit_price * quantity
        
        # Format variant selections for storage
        formatted_selections = []
        if variant_selections:
            for selection in variant_selections:
                formatted = {'quantity': selection.get('quantity', 1)}
                if selection.get('color_id'):
                    formatted['color_id'] = str(selection['color_id'])
                if selection.get('size_id'):
                    formatted['size_id'] = str(selection['size_id'])
                # Include recipient data if present
                if selection.get('is_gift_purchase'):
                    formatted['is_gift_purchase'] = True
                if selection.get('is_purchase_on_behalf'):
                    formatted['is_purchase_on_behalf'] = True
                if selection.get('purchased_for_phone'):
                    # Normalize phone to +233XXXXXXXXX format
                    formatted['purchased_for_phone'] = cls._normalize_phone_international(selection['purchased_for_phone'])
                if selection.get('gift_message'):
                    formatted['gift_message'] = selection['gift_message']
                formatted_selections.append(formatted)
        
        # Normalize item-level phone number
        item_phone = item.get('purchased_for_phone')
        if item_phone:
            item_phone = cls._normalize_phone_international(item_phone)
        
        return CheckoutItem(
            source='merchandise',
            item_id=str(product.product_id),
            name=product.product_name,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            original_metadata={
                'product_id': str(product.product_id),
                'product_name': product.product_name,
                'product_type': product.type_of_product,
                'quantity': quantity,
                'unit_price': str(unit_price),
                'original_price': str(pricing_info['original_price']),
                'discount_applied': pricing_info['discount_applied'],
                'discount_name': pricing_info.get('discount_name'),
                'variant_selections': formatted_selections,
                # Item-level recipient data
                'is_gift_purchase': item.get('is_gift_purchase', False),
                'is_purchase_on_behalf': item.get('is_purchase_on_behalf', False),
                'purchased_for_phone': item_phone,
                'gift_message': item.get('gift_message'),
            }
        )
    
    @classmethod
    def _validate_el_mercado_item(cls, user, item: Dict[str, Any]) -> CheckoutItem:
        """Validate an El Mercado marketplace listing item"""
        from el_mercado.models import Listing, Seller
        
        listing_id = item.get('listing_id')
        seller_id = item.get('seller_id')
        quantity = item.get('quantity', 1)
        variant_id = item.get('variant_id')
        
        try:
            listing = Listing.objects.select_related('seller').get(pk=listing_id)
        except Listing.DoesNotExist:
            raise ProductNotFoundError(f"Listing not found: {listing_id}")
        
        # Check listing is active
        if listing.status != 'ACTIVE':
            raise CartValidationError(f"Listing '{listing.title}' is not available")
        
        # Check seller is verified and active
        seller = listing.seller
        if not seller.is_active:
            raise CartValidationError(
                f"Seller for '{listing.title}' is not currently active"
            )
        
        # Check stock if tracking inventory
        if listing.track_inventory and not listing.allow_backorder:
            if variant_id:
                variant = listing.variants.filter(pk=variant_id).first()
                if variant and variant.stock_quantity < quantity:
                    raise InsufficientStockError(
                        f"Insufficient stock for '{listing.title}' variant. "
                        f"Available: {variant.stock_quantity}, Requested: {quantity}"
                    )
            else:
                if listing.stock_quantity < quantity:
                    raise InsufficientStockError(
                        f"Insufficient stock for '{listing.title}'. "
                        f"Available: {listing.stock_quantity}, Requested: {quantity}"
                    )
        
        # Get price (variant price if applicable)
        if variant_id:
            variant = listing.variants.filter(pk=variant_id).first()
            if variant:
                unit_price = variant.price or listing.price
                variant_name = variant.name
            else:
                unit_price = listing.price
                variant_name = None
        else:
            unit_price = listing.price
            variant_name = None
        
        total_price = unit_price * quantity
        
        return CheckoutItem(
            source='el_mercado',
            item_id=str(listing.id),
            name=listing.title,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            original_metadata={
                'listing_id': str(listing.id),
                'listing_title': listing.title,
                'listing_slug': listing.slug,
                'seller_id': str(seller.id),
                'seller_name': seller.display_name,
                'quantity': quantity,
                'unit_price': str(unit_price),
                'variant_id': str(variant_id) if variant_id else None,
                'variant_name': variant_name,
                'listing_type': listing.listing_type,
                # Commission rate for later calculation
                'commission_rate': str(seller.commission_rate or Decimal('10.00')),
            }
        )
    
    # ==========================================================================
    # CHECKOUT INITIALIZATION
    # ==========================================================================
    
    @classmethod
    @db_transaction.atomic
    def initialize_checkout(
        cls,
        user,
        cart_items: List[Dict[str, Any]],
        callback_url: str,
        gateway_name: str = None,
        shipping_info: Dict[str, str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Initialize unified checkout for items from both sources.
        
        Args:
            user: User making the purchase
            cart_items: List of items with 'source' field ('merchandise' or 'el_mercado')
            callback_url: URL to redirect after payment
            gateway_name: Payment gateway to use (default: paystack)
            shipping_info: Shipping info for El Mercado items (if any)
            **kwargs: Additional parameters
        
        Returns:
            Dict containing:
                - transaction: Transaction instance
                - payment_url: URL to redirect user for payment
                - reference: Transaction reference
                - access_code: Gateway access code
                - summary: CheckoutSummary data
        
        Raises:
            UnifiedCheckoutError: If initialization fails
        """
        gateway_name = gateway_name or cls.DEFAULT_GATEWAY
        
        # Validate personal email
        personal_email = None
        if user and hasattr(user, 'personal_email'):
            personal_email = user.personal_email
        
        if not personal_email:
            raise UnifiedCheckoutError(
                "Personal email is required for payment. Please update your profile "
                "with a valid personal email address."
            )
        
        # Validate and process cart
        try:
            summary = cls.validate_and_process_cart(user, cart_items)
        except UnifiedCheckoutError:
            raise
        except Exception as e:
            logger.error(f"Cart validation failed: {str(e)}")
            raise CartValidationError(f"Failed to validate cart: {str(e)}")
        
        if summary.grand_total <= 0:
            raise CartValidationError("Cart total must be greater than zero")
        
        # Build description
        descriptions = []
        if summary.merchandise_items:
            merch_count = sum(i.quantity for i in summary.merchandise_items)
            descriptions.append(f"{merch_count} merchandise item(s)")
        if summary.el_mercado_items:
            em_count = sum(i.quantity for i in summary.el_mercado_items)
            descriptions.append(f"{em_count} marketplace item(s)")
        
        # Contextual description based on cart contents
        if summary.el_mercado_items and not summary.merchandise_items:
            description = f"El Mercado order: {em_count} marketplace item(s)"
        elif summary.merchandise_items and not summary.el_mercado_items:
            description = f"Merchandise purchase: {merch_count} item(s)"
        else:
            description = f"Unified checkout: {', '.join(descriptions)}"
        
        # Build metadata for transaction
        # Determine purchase type for metadata
        has_merchandise = len(summary.merchandise_items) > 0
        has_el_mercado = len(summary.el_mercado_items) > 0
        
        if has_el_mercado and not has_merchandise:
            purchase_type = 'el_mercado_only'
        elif has_merchandise and not has_el_mercado:
            purchase_type = 'merchandise_only'
        else:
            purchase_type = 'mixed'
        
        metadata = {
            'unified_checkout': True,
            'purchase_type': purchase_type,  # 'el_mercado_only', 'merchandise_only', or 'mixed'
            'has_merchandise': has_merchandise,
            'has_el_mercado': has_el_mercado,
            'summary': summary.to_dict(),
            'merchandise_items': [i.to_dict() for i in summary.merchandise_items],
            'el_mercado_items': [i.to_dict() for i in summary.el_mercado_items],
            'merchandise_total': str(summary.merchandise_total),
            'el_mercado_total': str(summary.el_mercado_total),
            'grand_total': str(summary.grand_total),
            # Shipping info for El Mercado
            'shipping_info': shipping_info or {},
        }
        
        # Prepare customer details
        customer_email = personal_email
        customer_phone = str(user.phone) if (user and hasattr(user, 'phone') and user.phone) else kwargs.get('phone', '')
        customer_name = user.get_full_name() if user else kwargs.get('name', '')
        if not customer_name and user:
            customer_name = f"{user.first_name} {user.last_name}".strip() or f"User {user.id}"
        
        # Determine reference prefix based on cart contents for better UX
        # This makes the transaction reference contextual:
        # - ELM-*: El Mercado only purchases
        # - TXN-*: Merchandise only purchases  
        # - UNIFIED-*: Mixed cart (both El Mercado and Merchandise)
        has_merchandise = len(summary.merchandise_items) > 0
        has_el_mercado = len(summary.el_mercado_items) > 0
        
        if has_el_mercado and not has_merchandise:
            # El Mercado only
            reference_prefix = 'ELM'
        elif has_merchandise and not has_el_mercado:
            # Merchandise only (but via cart checkout)
            reference_prefix = 'TXN'
        else:
            # Mixed cart
            reference_prefix = 'UNIFIED'
        
        unified_reference = TransactionService.generate_reference(prefix=reference_prefix)
        
        # Get content type - use a generic marker
        # We'll use the Transaction itself as content object is not needed
        try:
            # Create transaction with the unified reference
            transaction = TransactionService.create_transaction(
                user=user,
                amount=summary.grand_total,
                currency_code='GHS',
                description=description,
                transaction_type='payment',
                gateway_name=gateway_name,
                metadata=metadata,
                customer_email=customer_email,
                customer_phone=customer_phone,
                customer_name=customer_name,
                ip_address=kwargs.get('ip_address'),
                user_agent=kwargs.get('user_agent'),
                reference=unified_reference,  # Use our custom UNIFIED- reference
            )
            
            # Initialize payment with gateway
            gateway = TransactionService.get_gateway_instance(gateway_name)
            
            payment_result = gateway.initialize_payment(
                amount=summary.grand_total,
                email=customer_email,
                reference=transaction.reference,
                callback_url=callback_url,
                metadata={
                    'unified_checkout': True,
                    'transaction_id': str(transaction.id),
                },
                currency='GHS',
            )
            
            # Update transaction with gateway reference
            transaction.gateway_reference = payment_result.get('gateway_reference')
            transaction.gateway_metadata = payment_result
            transaction.status = 'pending'
            transaction.save()
            
            logger.info(
                f"Unified checkout initialized: {transaction.reference} "
                f"(Merchandise: {len(summary.merchandise_items)}, "
                f"El Mercado: {len(summary.el_mercado_items)})"
            )
            
            return {
                'transaction': transaction,
                'payment_url': payment_result.get('authorization_url'),
                'reference': transaction.reference,
                'access_code': payment_result.get('access_code'),
                'summary': summary.to_dict(),
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize unified checkout: {str(e)}")
            raise PaymentInitializationError(f"Payment initialization failed: {str(e)}")
    
    # ==========================================================================
    # PAYMENT COMPLETION
    # ==========================================================================
    
    @classmethod
    @db_transaction.atomic
    def complete_checkout(
        cls,
        transaction: Transaction,
        gateway_response: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Complete the unified checkout after successful payment.
        
        This method:
        1. Processes merchandise items → Creates ProductPayment records
        2. Processes El Mercado items → Creates MarketplaceOrder records
        3. Generates validation codes for all items
        4. Sends notifications
        
        Args:
            transaction: The completed Transaction
            gateway_response: Response from payment gateway
        
        Returns:
            Dict with results for both systems
        
        Raises:
            UnifiedCheckoutError: If completion fails
        """
        metadata = transaction.metadata or {}
        
        if not metadata.get('unified_checkout'):
            raise UnifiedCheckoutError("Transaction is not a unified checkout")
        
        # IDEMPOTENCY CHECK - If already completed, return existing results
        existing_results = metadata.get('completion_results')
        if existing_results and (existing_results.get('merchandise_results') or existing_results.get('el_mercado_results')):
            logger.info(f"Unified checkout {transaction.reference} already completed, returning cached results")
            return existing_results
        
        results = {
            'merchandise_results': [],
            'el_mercado_results': [],
            'validation_codes': [],
            'errors': [],
        }
        
        # Process merchandise items
        merchandise_items = metadata.get('merchandise_items', [])
        if merchandise_items:
            try:
                merch_results = cls._process_merchandise_items(
                    transaction=transaction,
                    items=merchandise_items,
                )
                results['merchandise_results'] = merch_results
            except Exception as e:
                logger.error(f"Failed to process merchandise items: {str(e)}")
                results['errors'].append({
                    'source': 'merchandise',
                    'error': str(e),
                })
        
        # Process El Mercado items  
        el_mercado_items = metadata.get('el_mercado_items', [])
        shipping_info = metadata.get('shipping_info', {})
        if el_mercado_items:
            try:
                em_results = cls._process_el_mercado_items(
                    transaction=transaction,
                    items=el_mercado_items,
                    shipping_info=shipping_info,
                )
                results['el_mercado_results'] = em_results
            except Exception as e:
                logger.error(f"Failed to process El Mercado items: {str(e)}")
                results['errors'].append({
                    'source': 'el_mercado',
                    'error': str(e),
                })
        
        # Collect all validation codes
        for result in results['merchandise_results']:
            if result.get('validation_code'):
                results['validation_codes'].append({
                    'source': 'merchandise',
                    'code': result['validation_code'],
                    'product_name': result.get('product_name'),
                    'quantity': result.get('quantity'),
                    'variant_selections': result.get('variant_selections', []),
                    'is_gift': result.get('is_gift'),
                    'is_on_behalf': result.get('is_on_behalf'),
                    'recipient_phone': result.get('recipient_phone'),
                    'recipient_name': result.get('recipient_name'),
                })
        
        for result in results['el_mercado_results']:
            if result.get('validation_code'):
                results['validation_codes'].append({
                    'source': 'el_mercado',
                    'code': result['validation_code'],
                    'order_number': result.get('order_number'),
                    'seller_name': result.get('seller_name'),
                })
        
        # Update transaction metadata with results
        transaction.metadata['completion_results'] = results
        transaction.save(update_fields=['metadata'])
        
        # Send notifications
        cls._send_completion_notifications(transaction, results)
        
        return results
    
    @classmethod
    def _process_merchandise_items(
        cls,
        transaction: Transaction,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Process merchandise items after payment success"""
        from products.payment_service import ProductPaymentService
        from products.models import Product, ProductPayment, ProductColor, ProductSize
        
        results = []
        user = transaction.user
        
        for item_data in items:
            metadata = item_data.get('metadata', {})
            product_id = metadata.get('product_id')
            quantity = metadata.get('quantity', 1)
            variant_selections = metadata.get('variant_selections', [])
            
            try:
                product = Product.objects.select_for_update().get(product_id=product_id)
                
                # Reduce stock
                product.stock_quantity -= quantity
                product.save(update_fields=['stock_quantity'])
                
                # Helper function to generate unique validation code
                def generate_unique_code():
                    while True:
                        code = ''.join(
                            secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6)
                        )
                        if not ProductPayment.objects.filter(transaction_validation_code=code).exists():
                            return code
                
                # Track all validation codes for this item
                validation_codes = []
                
                # Create ProductPayment record(s)
                if variant_selections:
                    # Group variants by recipient to determine if they share a validation code
                    # Key: (is_gift, is_on_behalf, recipient_phone) -> list of variant selections
                    from collections import defaultdict
                    recipient_groups = defaultdict(list)
                    
                    for selection in variant_selections:
                        # Determine recipient info for this variant
                        is_gift = selection.get('is_gift_purchase', metadata.get('is_gift_purchase', False))
                        is_on_behalf = selection.get('is_purchase_on_behalf', metadata.get('is_purchase_on_behalf', False))
                        raw_phone = selection.get('purchased_for_phone', metadata.get('purchased_for_phone'))
                        gift_message = selection.get('gift_message', metadata.get('gift_message'))
                        
                        # Normalize phone number to ensure consistent grouping
                        # e.g., "0597959032" and "+233597959032" should be same recipient
                        recipient_phone = cls._normalize_phone_international(raw_phone) if raw_phone else None
                        
                        # Create recipient key - variants with same recipient share validation code
                        recipient_key = (is_gift, is_on_behalf, recipient_phone or '')
                        recipient_groups[recipient_key].append({
                            'selection': selection,
                            'is_gift': is_gift,
                            'is_on_behalf': is_on_behalf,
                            'recipient_phone': recipient_phone,
                            'gift_message': gift_message,
                        })
                    
                    # Create ONE ProductPayment per recipient group
                    for recipient_key, group_items in recipient_groups.items():
                        is_gift, is_on_behalf, recipient_phone = recipient_key
                        gift_message = group_items[0]['gift_message']  # Use first gift message
                        
                        # Build all variant selections for this group
                        group_variant_selections = []
                        total_quantity = 0
                        
                        for item in group_items:
                            selection = item['selection']
                            sel_quantity = selection.get('quantity', 1)
                            total_quantity += sel_quantity
                            
                            color = None
                            size = None
                            if selection.get('color_id'):
                                color = ProductColor.objects.filter(id=selection['color_id']).first()
                            if selection.get('size_id'):
                                size = ProductSize.objects.filter(id=selection['size_id']).first()
                            
                            group_variant_selections.append({
                                'color_id': str(color.id) if color else None,
                                'color_name': color.name if color else None,
                                'size_id': str(size.id) if size else None,
                                'size_code': size.code if size else None,
                                'quantity': sel_quantity,
                            })
                        
                        # Try to link recipient user for gift/on-behalf purchases
                        purchased_for_user = None
                        if (is_gift or is_on_behalf) and recipient_phone:
                            from accounts.models import CustomUser
                            phone_str = str(recipient_phone).replace('+', '').replace(' ', '')
                            try:
                                purchased_for_user = CustomUser.objects.filter(
                                    phone__icontains=phone_str[-9:]
                                ).first()
                                if purchased_for_user:
                                    logger.info(f"Unified checkout: Recipient linked to user: {purchased_for_user.student_id or purchased_for_user.phone}")
                            except Exception as e:
                                logger.warning(f"Unified checkout: Failed to auto-link recipient: {e}")
                        
                        # Generate ONE validation code for this recipient group
                        validation_code = generate_unique_code()
                        validation_codes.append(validation_code)
                        
                        payment_record = ProductPayment.objects.create(
                            buyer=user,
                            product=product,
                            transaction_record=transaction,
                            quantity=total_quantity,
                            amount=Decimal(metadata.get('unit_price', '0')) * total_quantity,
                            price_at_purchase=Decimal(metadata.get('unit_price', '0')),
                            variant_selections=group_variant_selections,
                            transaction_validation_code=validation_code,
                            payment_successful=True,
                            is_gift_purchase=is_gift,
                            is_purchase_on_behalf=is_on_behalf,
                            purchased_for_phone=recipient_phone or None,
                            purchased_for_user=purchased_for_user if (is_gift or is_on_behalf) else None,
                            gift_message=gift_message,
                            gift_linked_at=timezone.now() if ((is_gift or is_on_behalf) and purchased_for_user) else None,
                        )
                        
                        # Add result for THIS specific recipient group
                        # Build user-friendly variant info with color names
                        readable_variants = []
                        for vs in group_variant_selections:
                            readable_variants.append({
                                'color': vs.get('color_name'),
                                'size': vs.get('size_code'),
                                'quantity': vs.get('quantity', 1),
                            })
                        
                        results.append({
                            'product_id': product_id,
                            'product_name': product.product_name,
                            'quantity': total_quantity,
                            'validation_code': validation_code,
                            'variant_selections': readable_variants,
                            'is_gift': is_gift,
                            'is_on_behalf': is_on_behalf,
                            'recipient_phone': recipient_phone,
                            'recipient_name': metadata.get('purchased_for_name'),
                            'status': 'success',
                        })
                else:
                    # Single item without variants
                    validation_code = generate_unique_code()
                    validation_codes.append(validation_code)
                    
                    # Normalize phone number for single item
                    single_item_phone = metadata.get('purchased_for_phone')
                    if single_item_phone:
                        single_item_phone = cls._normalize_phone_international(single_item_phone)
                    
                    # Get gift/on-behalf flags
                    single_is_gift = metadata.get('is_gift_purchase', False)
                    single_is_on_behalf = metadata.get('is_purchase_on_behalf', False)
                    
                    # Try to link recipient user for gift/on-behalf purchases
                    single_purchased_for_user = None
                    if (single_is_gift or single_is_on_behalf) and single_item_phone:
                        from accounts.models import CustomUser
                        phone_str = str(single_item_phone).replace('+', '').replace(' ', '')
                        try:
                            single_purchased_for_user = CustomUser.objects.filter(
                                phone__icontains=phone_str[-9:]
                            ).first()
                            if single_purchased_for_user:
                                logger.info(f"Unified checkout: Single item recipient linked to user: {single_purchased_for_user.student_id or single_purchased_for_user.phone}")
                        except Exception as e:
                            logger.warning(f"Unified checkout: Failed to auto-link single item recipient: {e}")
                    
                    payment_record = ProductPayment.objects.create(
                        buyer=user,
                        product=product,
                        transaction_record=transaction,
                        quantity=quantity,
                        amount=Decimal(metadata.get('unit_price', '0')) * quantity,
                        price_at_purchase=Decimal(metadata.get('unit_price', '0')),
                        transaction_validation_code=validation_code,
                        payment_successful=True,
                        is_gift_purchase=single_is_gift,
                        is_purchase_on_behalf=single_is_on_behalf,
                        purchased_for_phone=single_item_phone,
                        purchased_for_user=single_purchased_for_user if (single_is_gift or single_is_on_behalf) else None,
                        gift_message=metadata.get('gift_message'),
                        gift_linked_at=timezone.now() if ((single_is_gift or single_is_on_behalf) and single_purchased_for_user) else None,
                    )
                    
                    results.append({
                        'product_id': product_id,
                        'product_name': product.product_name,
                        'quantity': quantity,
                        'validation_code': validation_code,
                        'variant_selections': [],
                        'is_gift': single_is_gift,
                        'is_on_behalf': single_is_on_behalf,
                        'recipient_phone': single_item_phone,
                        'recipient_name': metadata.get('purchased_for_name'),
                        'status': 'success',
                    })
                
            except Exception as e:
                logger.error(f"Failed to process merchandise item {product_id}: {str(e)}")
                results.append({
                    'product_id': product_id,
                    'error': str(e),
                    'status': 'failed',
                })
        
        return results
    
    @classmethod
    def _process_el_mercado_items(
        cls,
        transaction: Transaction,
        items: List[Dict[str, Any]],
        shipping_info: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Process El Mercado marketplace items after payment success"""
        from el_mercado.models import Listing, Seller, MarketplaceOrder, OrderItem
        
        results = []
        user = transaction.user
        
        # Group items by seller
        items_by_seller: Dict[str, List[Dict]] = {}
        for item_data in items:
            metadata = item_data.get('metadata', {})
            seller_id = metadata.get('seller_id')
            if seller_id not in items_by_seller:
                items_by_seller[seller_id] = []
            items_by_seller[seller_id].append(item_data)
        
        # Create order for each seller
        for seller_id, seller_items in items_by_seller.items():
            try:
                seller = Seller.objects.get(id=seller_id)
                
                # Calculate totals for this seller's items
                subtotal = Decimal('0.00')
                order_items_data = []
                
                for item_data in seller_items:
                    metadata = item_data.get('metadata', {})
                    listing_id = metadata.get('listing_id')
                    quantity = metadata.get('quantity', 1)
                    unit_price = Decimal(metadata.get('unit_price', '0'))
                    variant_id = metadata.get('variant_id')
                    
                    listing = Listing.objects.get(pk=listing_id)
                    
                    # Reduce stock if tracking
                    if listing.track_inventory:
                        if variant_id:
                            variant = listing.variants.filter(pk=variant_id).first()
                            if variant:
                                variant.stock_quantity -= quantity
                                variant.save(update_fields=['stock_quantity'])
                        else:
                            listing.stock_quantity -= quantity
                            listing.save(update_fields=['stock_quantity'])
                    
                    item_total = unit_price * quantity
                    subtotal += item_total
                    
                    order_items_data.append({
                        'listing': listing,
                        'variant_id': variant_id,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'total_price': item_total,
                    })
                
                # Calculate commission
                commission_rate = seller.commission_rate or Decimal('10.00')
                platform_commission = subtotal * (commission_rate / 100)
                seller_earnings = subtotal - platform_commission
                
                # Note: El Mercado uses delivery_code which is generated when seller ships
                # No validation code is generated at purchase time
                
                # Resolve shipping address if ID provided
                shipping_address_instance = None
                if shipping_info.get('shipping_address_id'):
                    from accounts.models import ShippingAddress
                    try:
                        shipping_address_instance = ShippingAddress.objects.get(
                            id=shipping_info['shipping_address_id'],
                            user=user
                        )
                    except ShippingAddress.DoesNotExist:
                        pass
                
                # Create the order
                order = MarketplaceOrder.objects.create(
                    buyer=user,
                    seller=seller,
                    subtotal=subtotal,
                    shipping_cost=Decimal('0.00'),
                    discount_amount=Decimal('0.00'),
                    total_amount=subtotal,
                    commission_rate=commission_rate,
                    platform_commission=platform_commission,
                    seller_earnings=seller_earnings,
                    currency='GHS',
                    status='PAID',
                    payment_status='PAID',
                    payment_reference=transaction.reference,
                    paid_at=timezone.now(),
                    # Shipping info
                    shipping_name=shipping_info.get('name', user.get_full_name()),
                    shipping_phone=shipping_info.get('phone', getattr(user, 'phone', '')),
                    shipping_email=shipping_info.get('email', user.email),
                    shipping_address_line_1=shipping_info.get('address', shipping_info.get('address_line_1', '')),
                    shipping_address_line_2=shipping_info.get('address_line_2', ''),
                    shipping_city=shipping_info.get('city', ''),
                    shipping_region=shipping_info.get('region', ''),
                    shipping_country=shipping_info.get('country', 'Ghana'),
                    shipping_digital_address=shipping_info.get('digital_address', ''),
                    shipping_landmark=shipping_info.get('landmark', ''),
                    delivery_instructions=shipping_info.get('delivery_instructions', ''),
                    shipping_address=shipping_address_instance,
                )
                
                # Create order items
                for item_data in order_items_data:
                    variant = None
                    if item_data.get('variant_id'):
                        variant = item_data['listing'].variants.filter(
                            pk=item_data['variant_id']
                        ).first()
                    
                    OrderItem.objects.create(
                        order=order,
                        listing=item_data['listing'],
                        variant=variant,
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        total_price=item_data['total_price'],
                    )
                
                # Build items detail list for display
                items_detail = []
                for item_data in order_items_data:
                    listing = item_data['listing']
                    variant = None
                    if item_data.get('variant_id'):
                        variant = listing.variants.filter(pk=item_data['variant_id']).first()
                    
                    # Get first image from related images
                    first_image = listing.images.first()
                    image_url = None
                    if first_image:
                        # Use image_url if set (CDN), otherwise use local image path
                        image_url = first_image.image_url or (first_image.image.url if first_image.image else None)
                    
                    items_detail.append({
                        'listing_id': str(listing.id),
                        'name': listing.title,
                        'description': listing.description[:150] + '...' if listing.description and len(listing.description) > 150 else listing.description,
                        'quantity': item_data['quantity'],
                        'unit_price': str(item_data['unit_price']),
                        'total_price': str(item_data['total_price']),
                        'variant_name': variant.name if variant else None,
                        'image': image_url,
                    })
                
                results.append({
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                    'seller_id': seller_id,
                    'seller_name': seller.display_name,
                    'items_count': len(seller_items),
                    'items': items_detail,  # Item details for display
                    'total_amount': str(subtotal),
                    'order_status': order.status,  # Should be 'PAID'
                    'status': 'success',
                    # Note: delivery_code is NOT available at purchase time
                    # It's only generated when seller ships the order
                })
                
                logger.info(f"Created El Mercado order {order.order_number} for seller {seller.display_name}")
                
            except Exception as e:
                logger.error(f"Failed to process El Mercado items for seller {seller_id}: {str(e)}")
                results.append({
                    'seller_id': seller_id,
                    'error': str(e),
                    'status': 'failed',
                })
        
        return results
    
    @classmethod
    def _send_completion_notifications(
        cls,
        transaction: Transaction,
        results: Dict[str, Any],
    ) -> None:
        """Send notifications after checkout completion"""
        from utils.utils import send_sms_message
        from notifications.services import PushNotificationService
        from payments.services.unified_checkout_notifications import UnifiedCheckoutNotificationService
        
        user = transaction.user
        validation_codes = results.get('validation_codes', [])
        
        if not validation_codes:
            return
        
        # CRITICAL: Check if email already sent BEFORE attempting to send
        # This prevents duplicate emails when complete_checkout is called multiple times
        transaction.refresh_from_db()
        if transaction.metadata.get('email_notification_sent'):
            logger.info(f"Email already sent for {transaction.reference}, skipping notification")
            return
        
        # Send Email Notification (NEW - comprehensive email with all details)
        try:
            email_sent = UnifiedCheckoutNotificationService.send_purchase_confirmation_email(
                transaction=transaction,
                merchandise_results=results.get('merchandise_results', []),
                el_mercado_results=results.get('el_mercado_results', []),
            )
            
            # Mark email as sent to prevent duplicate sends by other systems (e.g., signals)
            if email_sent:
                Transaction.objects.filter(id=transaction.id).update(
                    metadata={
                        **(transaction.metadata or {}),
                        'email_notification_sent': True,
                        'email_sent_at': timezone.now().isoformat(),
                        'email_sent_by': 'unified_checkout_service',
                    }
                )
        except Exception as e:
            logger.error(f"Failed to send unified checkout email: {str(e)}")
        
        # Build SMS message
        message_parts = [f"Thank you for your purchase!"]
        
        merch_codes = [vc for vc in validation_codes if vc['source'] == 'merchandise']
        em_codes = [vc for vc in validation_codes if vc['source'] == 'el_mercado']
        
        if merch_codes:
            message_parts.append("\nMerchandise codes:")
            for vc in merch_codes:
                message_parts.append(f"- {vc['product_name']}: {vc['code']}")
        
        if em_codes:
            message_parts.append("\nMarketplace orders:")
            for vc in em_codes:
                message_parts.append(f"- {vc['seller_name']} ({vc['order_number']}): {vc['code']}")
        
        message_parts.append("\nCheck your email for full order details.")
        message = "\n".join(message_parts)
        
        # Send SMS
        if hasattr(user, 'phone') and user.phone:
            try:
                send_sms_message(str(user.phone), message)
            except Exception as e:
                logger.error(f"Failed to send SMS notification: {str(e)}")
        
        # Send in-app / push notification
        try:
            PushNotificationService.send_to_user(
                user=user,
                title="🎉 Purchase Complete!",
                body=f"Your order has been confirmed. Check your email for details.",
                data={
                    'type': 'unified_purchase',
                    'transaction_reference': transaction.reference,
                    'validation_codes': validation_codes,
                    'screen': 'purchases',
                },
                priority='high',
                category='merchandise',
            )
        except Exception as e:
            logger.error(f"Failed to send push notification: {str(e)}")
    
    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================
    
    @classmethod
    def get_checkout_status(cls, reference: str) -> Dict[str, Any]:
        """Get the status of a unified checkout by reference"""
        try:
            transaction = Transaction.objects.get(reference=reference)
            
            metadata = transaction.metadata or {}
            
            return {
                'reference': reference,
                'status': transaction.status,
                'amount': str(transaction.amount),
                'is_unified_checkout': metadata.get('unified_checkout', False),
                'summary': metadata.get('summary'),
                'completion_results': metadata.get('completion_results'),
            }
        except Transaction.DoesNotExist:
            raise UnifiedCheckoutError(f"Transaction not found: {reference}")
