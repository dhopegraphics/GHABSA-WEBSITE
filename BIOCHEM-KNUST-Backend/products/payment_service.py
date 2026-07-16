"""
Product Payment Service
Integrates product purchases with the main payment system
"""
from typing import Dict, Any, Optional, List
from decimal import Decimal
from django.conf import settings
from django.db import transaction as db_transaction
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import logging

from payments.services.transaction_service import TransactionService
from payments.models import Transaction
from products.models import Product
from utils.utils import send_sms_message, notify_user
from utils.logging_config import get_logger, log_payment_event

logger = get_logger(__name__, 'products')
payment_logger = get_logger('payments', 'payments')


class ProductPaymentService:
    """
    Service for handling product payments using the main payment infrastructure
    
    Features:
    - Initialize product payments
    - Verify payments via webhooks
    - Handle stock reduction
    - Generate validation codes
    - Send SMS notifications
    """
    
    @classmethod
    @db_transaction.atomic
    def initialize_product_payment(
        cls,
        user,
        product_id: str,
        gateway_name: str = 'paystack',
        callback_url: str = '',
        quantity: int = 1,
        variant_selections: list = None,
        # Purchase type parameters
        is_gift_purchase: bool = False,
        is_purchase_on_behalf: bool = False,
        purchased_for_phone: str = None,
        gift_message: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Initialize a payment for a product purchase
        
        Args:
            user: User making the purchase
            product_id: UUID of the product
            gateway_name: Payment gateway to use (default: paystack)
            callback_url: URL to redirect after payment
            quantity: Number of items to purchase (default: 1)
            variant_selections: List of dicts with color_id, size_id, quantity for each variant
            is_gift_purchase: If True, this is a gift with optional message
            is_purchase_on_behalf: If True, buying on behalf of someone (they requested it)
            purchased_for_phone: Phone number of recipient
            gift_message: Optional message (only for gifts)
            **kwargs: Additional parameters
        
        Returns:
            Dict containing:
                - transaction: Transaction instance
                - payment_url: URL to redirect user for payment
                - reference: Transaction reference
                - access_code: Gateway access code
        
        Raises:
            ValueError: If product not available or invalid
        """
        # Get product
        try:
            product = Product.objects.select_for_update().get(product_id=product_id)
        except Product.DoesNotExist:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # Validate product availability
        if not product.is_available_for_purchase():
            raise ValueError(
                f"Product not available: {product.get_availability_message()}"
            )
        
        # Validate user eligibility
        is_eligible, eligibility_message = product.check_user_eligibility(user)
        if not is_eligible:
            raise ValueError(f"Not eligible to purchase: {eligibility_message}")
        
        # Check stock quantity
        if product.stock_quantity < quantity:
            raise ValueError(
                f"Insufficient stock. Only {product.stock_quantity} items available"
            )
        
        # CRITICAL: Validate variant selections if product requires them
        if product.has_colors or product.has_sizes:
            if not variant_selections or len(variant_selections) == 0:
                missing = []
                if product.has_colors:
                    missing.append('color')
                if product.has_sizes:
                    missing.append('size')
                raise ValueError(
                    f"This product requires {' and '.join(missing)} preferences. "
                    f"Please select your preferences before purchasing."
                )
            
            # Validate each selection has required fields
            for idx, selection in enumerate(variant_selections):
                if product.has_colors and not selection.get('color_id'):
                    raise ValueError(
                        f"Color preference is required for item {idx + 1}. "
                        f"Please select a color before purchasing."
                    )
                if product.has_sizes and not selection.get('size_id'):
                    raise ValueError(
                        f"Size preference is required for item {idx + 1}. "
                        f"Please select a size before purchasing."
                    )
        
        # Get user-specific pricing (considering discounts)
        pricing_info = product.get_price_for_user(user)
        unit_price = pricing_info['final_price']
        original_unit_price = pricing_info['original_price']
        discount_applied = pricing_info['discount_applied']
        
        # Calculate total amount using the (possibly discounted) price
        total_amount = unit_price * quantity
        
        # Get product content type
        content_type = ContentType.objects.get_for_model(Product)
        
        # Prepare transaction description
        description = f"Purchase of {quantity}x {product.product_name}"
        if discount_applied:
            description += f" (with {pricing_info['discount_name']})"
        
        # Prepare metadata with variant selections and pricing info
        metadata = {
            'product_id': str(product.product_id),
            'product_name': product.product_name,
            'quantity': quantity,
            'unit_price': str(unit_price),
            'original_unit_price': str(original_unit_price),
            'product_type': product.type_of_product,
            # Discount information
            'discount_applied': discount_applied,
            'discount_name': pricing_info['discount_name'],
            'discount_type': pricing_info['discount_type'],
            'discount_amount': str(pricing_info['discount_amount']) if pricing_info['discount_amount'] else None,
            'discount_percentage': str(pricing_info['discount_percentage']) if pricing_info['discount_percentage'] else None,
            'discount_reason': pricing_info['discount_reason'],
            'total_savings': str(pricing_info['discount_amount'] * quantity) if discount_applied else None,
        }
        
        # Format variant selections with full details
        formatted_selections = []
        raw_selections = []  # Store raw IDs for the variant_selections field
        
        if variant_selections:
            from products.models import ProductColor, ProductSize
            
            for selection in variant_selections:
                # Store raw selection for variant_selections field
                # Convert UUIDs to strings for JSON serialization
                raw_selection = {
                    'quantity': selection['quantity']
                }
                if selection.get('color_id'):
                    raw_selection['color_id'] = str(selection['color_id'])
                if selection.get('size_id'):
                    raw_selection['size_id'] = str(selection['size_id'])
                
                raw_selections.append(raw_selection)
                
                # Format with names for metadata (backward compatibility)
                formatted = {'quantity': selection['quantity']}
                
                if selection.get('color_id'):
                    try:
                        color = ProductColor.objects.get(id=selection['color_id'])
                        formatted['color'] = {
                            'id': str(color.id),
                            'name': color.name,
                            'hex_code': color.hex_code
                        }
                    except ProductColor.DoesNotExist:
                        pass
                
                if selection.get('size_id'):
                    try:
                        size = ProductSize.objects.get(id=selection['size_id'])
                        formatted['size'] = {
                            'id': str(size.id),
                            'name': size.name,
                            'code': size.code
                        }
                    except ProductSize.DoesNotExist:
                        pass
                
                formatted_selections.append(formatted)
            
            # Add to metadata - both formats for compatibility
            metadata['variant_selections'] = formatted_selections  # For human-readable display
            metadata['raw_variant_selections'] = raw_selections    # For ProductPayment storage
        
        # Add purchase type information to metadata
        if is_gift_purchase or is_purchase_on_behalf:
            metadata['is_gift_purchase'] = is_gift_purchase
            metadata['is_purchase_on_behalf'] = is_purchase_on_behalf
            metadata['purchased_for_phone'] = purchased_for_phone
            if is_gift_purchase and gift_message:
                metadata['gift_message'] = gift_message
        
        metadata.update(kwargs.get('metadata', {}))
        
        # Validate that user has a personal email
        personal_email = None
        if user and hasattr(user, 'personal_email'):
            personal_email = user.personal_email
        
        if not personal_email:
            raise ValueError(
                "Personal email is required for payment. Please update your profile with a valid personal email address to complete your purchase."
            )
        
        # Prepare customer details
        customer_email = personal_email
        customer_phone = str(user.phone) if (user and hasattr(user, 'phone') and user.phone) else kwargs.get('phone', '')
        customer_name = user.get_full_name() if user else kwargs.get('name', '')
        if not customer_name and user:
            customer_name = f"{user.first_name} {user.last_name}".strip() or f"User {user.id}"
        
        # Create transaction using TransactionService
        transaction = TransactionService.create_transaction(
            user=user,
            amount=total_amount,
            currency_code='GHS',
            description=description,
            transaction_type='payment',
            gateway_name=gateway_name,
            content_object=product,
            metadata=metadata,
            customer_email=customer_email,
            customer_phone=customer_phone,
            customer_name=customer_name,
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent'),
        )
        
        # NOTE: Variant selections stored in metadata and will be moved to ProductPayment later
        # No need to store in Transaction model directly anymore
        
        # Initialize payment with gateway
        gateway = TransactionService.get_gateway_instance(gateway_name)
        
        payment_result = gateway.initialize_payment(
            amount=total_amount,
            email=transaction.customer_email or settings.EMAIL_INFO,
            reference=transaction.reference,
            callback_url=callback_url,
            metadata=metadata,
            currency='GHS',
        )
        
        # Update transaction with gateway reference
        transaction.gateway_reference = payment_result.get('gateway_reference')
        transaction.gateway_metadata = payment_result
        transaction.status = 'pending'
        transaction.save()
        
        return {
            'transaction': transaction,
            'payment_url': payment_result.get('authorization_url'),
            'reference': transaction.reference,
            'access_code': payment_result.get('access_code'),
        }
    
    @classmethod
    @db_transaction.atomic
    def initialize_cart_payment(
        cls,
        user,
        cart_items: list,
        gateway_name: str = 'paystack',
        callback_url: str = '',
        # Purchase type parameters
        is_gift_purchase: bool = False,
        is_purchase_on_behalf: bool = False,
        purchased_for_phone: str = None,
        gift_message: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Initialize a payment for multiple cart items
        
        Args:
            user: User making the purchase
            cart_items: List of cart items with product_id, quantity, variant_selections
            gateway_name: Payment gateway to use (default: paystack)
            callback_url: URL to redirect after payment
            is_gift_purchase: If True, this is a gift purchase with optional message
            is_purchase_on_behalf: If True, buying on behalf of someone (they requested it)
            purchased_for_phone: Phone number of recipient (required for gift/on_behalf)
            gift_message: Optional message for gift purchases
            **kwargs: Additional parameters
        
        Returns:
            Dict containing:
                - transaction: Transaction instance
                - payment_url: URL to redirect user for payment
                - reference: Transaction reference
                - access_code: Gateway access code
                - items_data: List of processed item data
        
        Raises:
            ValueError: If products not available or invalid
        """
        if not cart_items:
            raise ValueError("Cart is empty")
        
        # Validate personal email
        personal_email = None
        if user and hasattr(user, 'personal_email'):
            personal_email = user.personal_email
        
        if not personal_email:
            raise ValueError(
                "Personal email is required for payment. Please update your profile with a valid personal email address to complete your purchase."
            )
        
        # Process all cart items
        total_amount = Decimal('0.00')
        items_data = []
        product_names = []
        
        for item in cart_items:
            product_id = item['product_id']
            quantity = item.get('quantity', 1)
            variant_selections = item.get('variant_selections', [])
            
            # Get and validate product
            try:
                product = Product.objects.select_for_update().get(product_id=product_id)
            except Product.DoesNotExist:
                raise ValueError(f"Product with ID {product_id} not found")
            
            if not product.is_available_for_purchase():
                raise ValueError(
                    f"Product '{product.product_name}' not available: {product.get_availability_message()}"
                )
            
            # Validate user eligibility for this product
            is_eligible, eligibility_message = product.check_user_eligibility(user)
            if not is_eligible:
                raise ValueError(
                    f"Not eligible to purchase '{product.product_name}': {eligibility_message}"
                )
            
            if product.stock_quantity < quantity:
                raise ValueError(
                    f"Insufficient stock for '{product.product_name}'. Only {product.stock_quantity} items available"
                )
            
            # CRITICAL: Validate variant selections if product requires them
            if product.has_colors or product.has_sizes:
                if not variant_selections or len(variant_selections) == 0:
                    missing = []
                    if product.has_colors:
                        missing.append('color')
                    if product.has_sizes:
                        missing.append('size')
                    raise ValueError(
                        f"Product '{product.product_name}' requires {' and '.join(missing)} preferences. "
                        f"Please select your preferences before checkout."
                    )
                
                # Validate each selection has required fields
                for idx, selection in enumerate(variant_selections):
                    if product.has_colors and not selection.get('color_id'):
                        raise ValueError(
                            f"Product '{product.product_name}': Color preference is required for item {idx + 1}"
                        )
                    if product.has_sizes and not selection.get('size_id'):
                        raise ValueError(
                            f"Product '{product.product_name}': Size preference is required for item {idx + 1}"
                        )
            
            # Get user-specific pricing (considering discounts)
            pricing_info = product.get_price_for_user(user)
            unit_price = pricing_info['final_price']
            original_unit_price = pricing_info['original_price']
            discount_applied = pricing_info['discount_applied']
            
            # Calculate item total using the (possibly discounted) price
            item_total = unit_price * quantity
            total_amount += item_total
            
            # Format variant selections
            formatted_selections = []
            raw_selections = []
            
            if variant_selections:
                from products.models import ProductColor, ProductSize
                
                for selection in variant_selections:
                    raw_selection = {'quantity': selection.get('quantity', 1)}
                    if selection.get('color_id'):
                        raw_selection['color_id'] = str(selection['color_id'])
                    if selection.get('size_id'):
                        raw_selection['size_id'] = str(selection['size_id'])
                    # Include per-variant recipient data (NEW)
                    if selection.get('is_gift_purchase'):
                        raw_selection['is_gift_purchase'] = True
                    if selection.get('is_purchase_on_behalf'):
                        raw_selection['is_purchase_on_behalf'] = True
                    if selection.get('purchased_for_phone'):
                        raw_selection['purchased_for_phone'] = selection['purchased_for_phone']
                    if selection.get('gift_message'):
                        raw_selection['gift_message'] = selection['gift_message']
                    raw_selections.append(raw_selection)
                    
                    formatted = {'quantity': selection['quantity']}
                    if selection.get('color_id'):
                        try:
                            color = ProductColor.objects.get(id=selection['color_id'])
                            formatted['color'] = {
                                'id': str(color.id),
                                'name': color.name,
                                'hex_code': color.hex_code
                            }
                        except ProductColor.DoesNotExist:
                            pass
                    
                    if selection.get('size_id'):
                        try:
                            size = ProductSize.objects.get(id=selection['size_id'])
                            formatted['size'] = {
                                'id': str(size.id),
                                'name': size.name,
                                'code': size.code
                            }
                        except ProductSize.DoesNotExist:
                            pass
                    
                    formatted_selections.append(formatted)
            
            items_data.append({
                'product_id': str(product.product_id),
                'product_name': product.product_name,
                'product_type': product.type_of_product,
                'quantity': quantity,
                'unit_price': str(unit_price),
                'original_unit_price': str(original_unit_price),
                'item_total': str(item_total),
                'variant_selections': formatted_selections,
                'raw_variant_selections': raw_selections,
                # Discount information
                'discount_applied': discount_applied,
                'discount_name': pricing_info['discount_name'],
                'discount_type': pricing_info['discount_type'],
                'discount_amount': str(pricing_info['discount_amount']) if pricing_info['discount_amount'] else None,
                'discount_percentage': str(pricing_info['discount_percentage']) if pricing_info['discount_percentage'] else None,
                'discount_reason': pricing_info['discount_reason'],
                'item_savings': str(pricing_info['discount_amount'] * quantity) if discount_applied else None,
                # Per-item recipient information (NEW)
                'is_gift_purchase': item.get('is_gift_purchase', False),
                'is_purchase_on_behalf': item.get('is_purchase_on_behalf', False),
                'purchased_for_phone': item.get('purchased_for_phone'),
                'gift_message': item.get('gift_message'),
            })
            product_names.append(product.product_name)
        
        # Get content type for first product (main reference)
        first_product = Product.objects.get(product_id=cart_items[0]['product_id'])
        content_type = ContentType.objects.get_for_model(Product)
        
        # Prepare description
        if len(product_names) == 1:
            description = f"Purchase of {cart_items[0].get('quantity', 1)}x {product_names[0]}"
        else:
            description = f"Cart purchase: {', '.join(product_names[:3])}" + (
                f" and {len(product_names) - 3} more" if len(product_names) > 3 else ""
            )
        
        # Prepare metadata
        metadata = {
            'cart_checkout': True,
            'items_count': len(cart_items),
            'items': items_data,
            'total_amount': str(total_amount),
        }
        
        # Add purchase type information to metadata
        if is_gift_purchase or is_purchase_on_behalf:
            metadata['is_gift_purchase'] = is_gift_purchase
            metadata['is_purchase_on_behalf'] = is_purchase_on_behalf
            metadata['purchased_for_phone'] = purchased_for_phone
            if is_gift_purchase and gift_message:
                metadata['gift_message'] = gift_message
        
        metadata.update(kwargs.get('metadata', {}))
        
        # Prepare customer details
        customer_email = personal_email
        customer_phone = str(user.phone) if (user and hasattr(user, 'phone') and user.phone) else kwargs.get('phone', '')
        customer_name = user.get_full_name() if user else kwargs.get('name', '')
        if not customer_name and user:
            customer_name = f"{user.first_name} {user.last_name}".strip() or f"User {user.id}"
        
        # Create main transaction
        transaction = TransactionService.create_transaction(
            user=user,
            amount=total_amount,
            currency_code='GHS',
            description=description,
            transaction_type='payment',
            gateway_name=gateway_name,
            content_object=first_product,  # Reference first product
            metadata=metadata,
            customer_email=customer_email,
            customer_phone=customer_phone,
            customer_name=customer_name,
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent'),
        )
        
        # Store cart items in transaction metadata for processing after payment
        # IMPORTANT: Include per-item recipient data for multi-recipient purchases
        transaction.metadata['cart_items'] = [
            {
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'variant_selections': item.get('raw_variant_selections', []),
                # Per-item recipient data
                'is_gift_purchase': item.get('is_gift_purchase', False),
                'is_purchase_on_behalf': item.get('is_purchase_on_behalf', False),
                'purchased_for_phone': item.get('purchased_for_phone'),
                'gift_message': item.get('gift_message'),
            }
            for item in items_data
        ]
        transaction.save(update_fields=['metadata'])
        
        # Initialize payment with gateway
        gateway = TransactionService.get_gateway_instance(gateway_name)
        
        payment_result = gateway.initialize_payment(
            amount=total_amount,
            email=transaction.customer_email or settings.EMAIL_INFO,
            reference=transaction.reference,
            callback_url=callback_url,
            metadata=metadata,
            currency='GHS',
        )
        
        # Update transaction with gateway reference
        transaction.gateway_reference = payment_result.get('gateway_reference')
        transaction.gateway_metadata = payment_result
        transaction.status = 'pending'
        transaction.save()
        
        logger.info(f"Cart payment initialized: {transaction.reference} with {len(cart_items)} items, total: {total_amount} GHS")
        
        return {
            'transaction': transaction,
            'payment_url': payment_result.get('authorization_url'),
            'reference': transaction.reference,
            'access_code': payment_result.get('access_code'),
            'items_data': items_data,
            'total_amount': str(total_amount),
        }
    
    @classmethod
    @db_transaction.atomic
    def complete_product_payment(
        cls,
        transaction: Transaction,
        reduce_stock: bool = True,
        send_notification: bool = True,
    ) -> Dict[str, Any]:
        """
        Complete a product payment after successful verification
        
        This should be called from webhook handler after payment verification
        Creates ProductPayment records for EACH item in the cart (or single item)
        Each ProductPayment gets its own unique validation code
        
        Args:
            transaction: Transaction instance
            reduce_stock: Whether to reduce product stock (default: True)
            send_notification: Whether to send SMS notification (default: True)
        
        Returns:
            Dict with completion status and details including all product payments
        
        Raises:
            ValueError: If transaction invalid or product not found
        """
        from products.models import ProductPayment
        
        logger.info(f"Starting complete_product_payment for transaction: {transaction.reference}")
        
        # Refresh transaction from database to ensure we have latest metadata
        transaction.refresh_from_db()
        
        # IDEMPOTENCY CHECK: If already completed, return existing result
        # This prevents duplicate notifications when called from multiple sources (webhook, verify API, retry tasks)
        if transaction.metadata and transaction.metadata.get('product_payment_completed'):
            logger.info(f"Transaction {transaction.reference} already completed, skipping duplicate processing")
            
            # Return existing result from metadata
            existing_result = transaction.metadata.get('completion_result', {})
            if existing_result:
                logger.info(f"Returning cached completion result for {transaction.reference}")
                return existing_result
            
            # If no cached result, build one from ProductPayment records
            from products.models import ProductPayment
            product_payments = list(ProductPayment.objects.filter(
                transaction_record=transaction
            ).select_related('product'))
            
            if product_payments:
                is_cart = len(product_payments) > 1 or transaction.metadata.get('cart_checkout', False)
                validation_codes = [{
                    'code': pp.transaction_validation_code,
                    'product_name': pp.product.product_name if pp.product else 'Unknown',
                    'quantity': pp.quantity,
                    'product_id': str(pp.product.product_id) if pp.product else None,
                } for pp in product_payments]
                
                return {
                    'success': True,
                    'transaction_id': str(transaction.id),
                    'reference': transaction.reference,
                    'is_cart_checkout': is_cart,
                    'validation_codes': validation_codes,
                    'already_completed': True,
                }
        
        # Debug logging
        logger.info(f"Transaction metadata keys: {list(transaction.metadata.keys()) if transaction.metadata else 'None'}")
        logger.info(f"Transaction metadata: {transaction.metadata}")
        
        # Validate transaction
        if transaction.status != 'success':
            raise ValueError(f"Transaction status is {transaction.status}, not success")
        
        if transaction.transaction_type != 'payment':
            raise ValueError(f"Transaction type is {transaction.transaction_type}, not payment")
        
        # Check if this is a cart checkout (multiple items) or single item
        is_cart_checkout = transaction.metadata.get('cart_checkout', False)
        cart_items = transaction.metadata.get('cart_items', [])
        
        logger.info(f"is_cart_checkout: {is_cart_checkout}, cart_items count: {len(cart_items)}")
        
        product_payments = []
        validation_codes = []
        
        if is_cart_checkout and cart_items:
            # CART CHECKOUT: Create ProductPayment for EACH cart item or variant
            logger.info(f"Processing cart checkout with {len(cart_items)} items")
            
            for idx, item_data in enumerate(cart_items):
                product_id = item_data.get('product_id')
                quantity = item_data.get('quantity', 1)
                variant_selections = item_data.get('variant_selections', [])
                
                # Get the product
                try:
                    product = Product.objects.select_for_update().get(product_id=product_id)
                except Product.DoesNotExist:
                    logger.error(f"Product {product_id} not found for cart item {idx}")
                    continue
                
                # Get item price and discount info from metadata (items list has full details)
                items_metadata = transaction.metadata.get('items', [])
                item_meta = next((i for i in items_metadata if i.get('product_id') == product_id), {})
                item_unit_price = Decimal(item_meta.get('unit_price', str(product.price)))
                
                # Extract discount info for this item
                item_discount_applied = item_meta.get('discount_applied', False)
                item_discount_name = item_meta.get('discount_name')
                item_discount_type = item_meta.get('discount_type')
                item_discount_amount = Decimal(item_meta.get('discount_amount', '0')) if item_meta.get('discount_amount') else None
                item_discount_percentage = Decimal(item_meta.get('discount_percentage', '0')) if item_meta.get('discount_percentage') else None
                item_discount_reason = item_meta.get('discount_reason')
                item_original_unit_price = Decimal(item_meta.get('original_unit_price', str(product.price)))
                
                # Item-level recipient info (fallback if variant doesn't have recipient)
                item_is_gift = item_data.get('is_gift_purchase', transaction.metadata.get('is_gift_purchase', False))
                item_is_on_behalf = item_data.get('is_purchase_on_behalf', transaction.metadata.get('is_purchase_on_behalf', False))
                item_purchased_for_phone = item_data.get('purchased_for_phone', transaction.metadata.get('purchased_for_phone'))
                item_gift_message = item_data.get('gift_message', transaction.metadata.get('gift_message'))
                
                # Check if product has variants and we should create per-variant payments
                has_per_variant_recipients = any(
                    (sel.get('is_gift_purchase') or sel.get('is_purchase_on_behalf'))
                    for sel in variant_selections
                )
                
                if variant_selections and has_per_variant_recipients:
                    # CREATE SEPARATE PRODUCTPAYMENT FOR EACH VARIANT (with recipient)
                    logger.info(f"Creating per-variant payments for {product.product_name}")
                    
                    for v_idx, variant in enumerate(variant_selections):
                        # Get variant-specific recipient info or fall back to item-level
                        v_is_gift = variant.get('is_gift_purchase', item_is_gift)
                        v_is_on_behalf = variant.get('is_purchase_on_behalf', item_is_on_behalf)
                        v_purchased_for_phone = variant.get('purchased_for_phone', item_purchased_for_phone)
                        v_gift_message = variant.get('gift_message', item_gift_message)
                        v_quantity = variant.get('quantity', 1)
                        
                        # Calculate amount for this variant
                        variant_amount = item_unit_price * v_quantity
                        
                        # Try to link recipient user
                        purchased_for_user = None
                        if (v_is_gift or v_is_on_behalf) and v_purchased_for_phone:
                            from accounts.models import CustomUser
                            phone_str = str(v_purchased_for_phone).replace('+', '').replace(' ', '')
                            try:
                                purchased_for_user = CustomUser.objects.filter(
                                    phone__icontains=phone_str[-9:]
                                ).first()
                                if purchased_for_user:
                                    logger.info(f"Variant recipient linked to user: {purchased_for_user.student_id or purchased_for_user.phone}")
                            except Exception as e:
                                logger.warning(f"Failed to auto-link variant recipient: {e}")
                        
                        # Generate unique validation code
                        temp_payment = ProductPayment()
                        unique_validation_code = temp_payment.generate_unique_validation_code()
                        
                        # Create ProductPayment for this specific variant
                        product_payment, created = ProductPayment.objects.get_or_create(
                            reference=f"{transaction.reference}-{idx}-v{v_idx}",  # Unique per variant
                            defaults={
                                'transaction_record': transaction,
                                'transaction': str(transaction.id),
                                'buyer': transaction.user,
                                'product': product,
                                'phone': transaction.customer_phone,
                                'customer_name': transaction.customer_name,
                                'customer_email': transaction.customer_email,
                                'amount': variant_amount,
                                'price_at_purchase': item_unit_price,
                                'quantity': v_quantity,
                                'payment_successful': True,
                                'transaction_validation_code': unique_validation_code,
                                'variant_selections': [variant],  # Single variant
                                # Discount fields
                                'discount_applied': item_discount_applied,
                                'original_price': item_original_unit_price,
                                'discount_amount': item_discount_amount * v_quantity if item_discount_amount else None,
                                'discount_type': item_discount_type,
                                'discount_percentage': item_discount_percentage,
                                'discount_reason': item_discount_reason,
                                # Purchase type fields
                                'is_gift_purchase': v_is_gift,
                                'is_purchase_on_behalf': v_is_on_behalf,
                                'purchased_for_phone': v_purchased_for_phone if (v_is_gift or v_is_on_behalf) else None,
                                'purchased_for_user': purchased_for_user if (v_is_gift or v_is_on_behalf) else None,
                                'gift_message': v_gift_message if v_is_gift else None,
                                'gift_linked_at': timezone.now() if ((v_is_gift or v_is_on_behalf) and purchased_for_user) else None,
                            }
                        )
                        
                        if created:
                            product_payments.append(product_payment)
                            validation_codes.append({
                                'code': unique_validation_code,
                                'product_name': product.product_name,
                                'quantity': v_quantity,
                                'is_gift': v_is_gift,
                                'is_on_behalf': v_is_on_behalf,
                                'recipient_phone': v_purchased_for_phone if (v_is_gift or v_is_on_behalf) else None,
                                'variant_selections': cls._format_variant_selections([variant]),
                            })
                            
                            # Record discount usage
                            if item_discount_applied and item_discount_name:
                                try:
                                    from products.models import ProductDiscount
                                    discount_obj = ProductDiscount.objects.filter(
                                        product=product,
                                        name=item_discount_name,
                                        is_active=True
                                    ).first()
                                    if discount_obj:
                                        discount_obj.record_usage(transaction.user, transaction)
                                        product_payment.discount = discount_obj
                                        product_payment.save(update_fields=['discount'])
                                except Exception as e:
                                    logger.warning(f"Failed to record discount usage: {e}")
                        else:
                            # IMPORTANT: Use the existing validation code from DB, not the newly generated one
                            product_payments.append(product_payment)
                            validation_codes.append({
                                'code': product_payment.transaction_validation_code,  # Use DB value!
                                'product_name': product.product_name,
                                'quantity': v_quantity,
                                'is_gift': v_is_gift,
                                'is_on_behalf': v_is_on_behalf,
                                'recipient_phone': v_purchased_for_phone if (v_is_gift or v_is_on_behalf) else None,
                                'variant_selections': cls._format_variant_selections(product_payment.variant_selections),
                            })
                            logger.info(f"Per-variant ProductPayment already exists, using existing validation code: {product_payment.transaction_validation_code}")
                
                else:
                    # SINGLE PRODUCTPAYMENT FOR THIS ITEM (no per-variant recipients)
                    item_total = item_unit_price * quantity
                    
                    # Try to link to recipient user if gift or on-behalf purchase
                    item_purchased_for_user = None
                    if (item_is_gift or item_is_on_behalf) and item_purchased_for_phone:
                        from accounts.models import CustomUser
                        phone_str = str(item_purchased_for_phone).replace('+', '').replace(' ', '')
                        try:
                            item_purchased_for_user = CustomUser.objects.filter(
                                phone__icontains=phone_str[-9:]
                            ).first()
                            if item_purchased_for_user:
                                purchase_type = "gift" if item_is_gift else "on-behalf"
                                logger.info(f"{purchase_type.capitalize()} purchase linked to user: {item_purchased_for_user.student_id or item_purchased_for_user.phone}")
                        except Exception as e:
                            logger.warning(f"Failed to auto-link purchase: {e}")
                    
                    # Generate unique validation code for this product payment
                    temp_payment = ProductPayment()
                    unique_validation_code = temp_payment.generate_unique_validation_code()
                    
                    # Create ProductPayment for this item
                    product_payment, created = ProductPayment.objects.get_or_create(
                        reference=f"{transaction.reference}-{idx}",  # Unique reference per item
                        defaults={
                            'transaction_record': transaction,
                            'transaction': str(transaction.id),
                            'buyer': transaction.user,  # Who paid
                            'product': product,
                            'phone': transaction.customer_phone,
                            'customer_name': transaction.customer_name,
                            'customer_email': transaction.customer_email,
                            'amount': item_total,
                            'price_at_purchase': item_unit_price,
                            'quantity': quantity,
                            'payment_successful': True,
                            'transaction_validation_code': unique_validation_code,
                            'variant_selections': variant_selections,
                            # Discount fields
                            'discount_applied': item_discount_applied,
                            'original_price': item_original_unit_price,
                            'discount_amount': item_discount_amount,
                            'discount_type': item_discount_type,
                            'discount_percentage': item_discount_percentage,
                            'discount_reason': item_discount_reason,
                            # Purchase type fields (use ITEM-LEVEL variables)
                            'is_gift_purchase': item_is_gift,
                            'is_purchase_on_behalf': item_is_on_behalf,
                            'purchased_for_phone': item_purchased_for_phone if (item_is_gift or item_is_on_behalf) else None,
                            'purchased_for_user': item_purchased_for_user if (item_is_gift or item_is_on_behalf) else None,
                            'gift_message': item_gift_message if item_is_gift else None,
                            'gift_linked_at': timezone.now() if ((item_is_gift or item_is_on_behalf) and item_purchased_for_user) else None,
                        }
                    )
                    
                    # Add to tracking lists
                    product_payments.append(product_payment)
                    
                    # IMPORTANT: Use the existing validation code from DB if record already exists
                    actual_validation_code = unique_validation_code if created else product_payment.transaction_validation_code
                    validation_codes.append({
                        'code': actual_validation_code,
                        'product_name': product.product_name,
                        'quantity': quantity,
                        'is_gift': item_is_gift,
                        'is_on_behalf': item_is_on_behalf,
                        'recipient_phone': item_purchased_for_phone if (item_is_gift or item_is_on_behalf) else None,
                        'variant_selections': cls._format_variant_selections(product_payment.variant_selections),
                    })
                    
                    if not created:
                        logger.info(f"Cart item ProductPayment already exists, using existing validation code: {product_payment.transaction_validation_code}")
                    
                    # Record discount usage if applied (only for newly created records)
                    if created and item_discount_applied and item_discount_name:
                        try:
                            from products.models import ProductDiscount
                            discount_obj = ProductDiscount.objects.filter(
                                product=product,
                                name=item_discount_name,
                                is_active=True
                            ).first()
                            if discount_obj:
                                discount_obj.record_usage(transaction.user, transaction)
                                product_payment.discount = discount_obj
                                product_payment.save(update_fields=['discount'])
                                logger.info(f"Discount usage recorded for cart item {idx}: {item_discount_name}")
                        except Exception as e:
                            logger.warning(f"Failed to record discount usage for cart item {idx}: {e}")
                
                # Reduce stock for this product (for both per-variant and single payment cases)
                if reduce_stock:
                    if variant_selections and (product.has_colors or product.has_sizes):
                        # For products with variants, reduce stock per variant
                        for variant in variant_selections:
                            v_color_id = variant.get('color_id')
                            v_size_id = variant.get('size_id')
                            v_qty = variant.get('quantity', 1)
                            
                            success = product.reduce_stock(
                                quantity=v_qty,
                                color=v_color_id,
                                size=v_size_id
                            )
                            if success:
                                logger.info(f"Variant stock reduced for {product.product_name} "
                                           f"(color={v_color_id}, size={v_size_id}): -{v_qty}")
                            else:
                                logger.warning(f"Failed to reduce variant stock for {product.product_name} "
                                              f"(color={v_color_id}, size={v_size_id})")
                    elif product.stock_quantity >= quantity:
                        # For simple products without variants
                        old_stock = product.stock_quantity
                        product.reduce_stock(quantity)
                        logger.info(f"Stock reduced for {product.product_name}: {old_stock} -> {product.stock_quantity}")
            
            # Store all validation codes in transaction metadata
            transaction.metadata['validation_codes'] = validation_codes
            
            # Send notification with all validation codes (only if not already sent)
            notification_already_sent = transaction.metadata.get('notification_sent', {}).get('push_sent', False)
            if send_notification and validation_codes and not notification_already_sent:
                try:
                    notification_results = cls._send_cart_purchase_notification(
                        transaction, 
                        validation_codes,
                        product_payments
                    )
                    
                    # Mark notification as sent in transaction metadata (for signal idempotency)
                    if not transaction.metadata:
                        transaction.metadata = {}
                    transaction.metadata['notification_sent'] = {
                        'push_sent': notification_results.get('push_sent', False),
                        'sms_sent': notification_results.get('sms_sent', False),
                        'sent_at': timezone.now().isoformat(),
                        'sent_by': 'complete_product_payment',
                    }
                    transaction.save(update_fields=['metadata'])
                    
                    # Update notification status for all product payments
                    for pp in product_payments:
                        pp.notification_sent = notification_results.get('push_sent', False) or notification_results.get('sms_sent', False)
                        pp.sms_sent = notification_results.get('sms_sent', False)
                        pp.push_sent = notification_results.get('push_sent', False)
                        pp.notification_sent_at = timezone.now()
                        pp.save()
                        
                except Exception as e:
                    logger.error(f"Failed to send cart notifications: {str(e)}", exc_info=True)
            else:
                logger.info(f"Skipping notification for {transaction.reference} - already sent or send_notification=False")
            
            result = {
                'success': True,
                'transaction_id': str(transaction.id),
                'reference': transaction.reference,
                'is_cart_checkout': True,
                'items_count': len(product_payments),
                'validation_codes': validation_codes,
                'amount_paid': str(transaction.amount),
                'product_payments': [str(pp.payment_id) for pp in product_payments],
            }
            
            # Mark as completed and cache result for idempotency
            transaction.metadata['product_payment_completed'] = True
            transaction.metadata['completion_result'] = result
            transaction.metadata['completed_at'] = timezone.now().isoformat()
            transaction.save(update_fields=['metadata'])
            
        else:
            # SINGLE ITEM CHECKOUT: Original behavior
            if not transaction.content_object or not isinstance(transaction.content_object, Product):
                raise ValueError("Transaction is not linked to a product")
            
            product = transaction.content_object
            quantity = transaction.metadata.get('quantity', 1)
            
            logger.info(f"Product: {product.product_name}, Quantity: {quantity}")
            
            # Extract variant selections from Transaction metadata
            # Use raw_variant_selections (with IDs) instead of formatted variant_selections (with full objects)
            variant_selections = transaction.metadata.get('raw_variant_selections', [])
            if not variant_selections:
                # Fallback: try to extract from formatted variant_selections
                formatted = transaction.metadata.get('variant_selections', [])
                if formatted:
                    variant_selections = []
                    for sel in formatted:
                        raw_sel = {'quantity': sel.get('quantity', 1)}
                        if sel.get('color'):
                            raw_sel['color_id'] = sel['color'].get('id')
                        if sel.get('size'):
                            raw_sel['size_id'] = sel['size'].get('id')
                        variant_selections.append(raw_sel)
            
            logger.info(f"Variant selections for ProductPayment: {variant_selections}")
            
            # Generate unique validation code for ProductPayment
            from products.models import ProductPayment
            temp_payment = ProductPayment()
            validation_code = temp_payment.generate_unique_validation_code()
            
            # Extract discount information from transaction metadata
            discount_applied = transaction.metadata.get('discount_applied', False)
            discount_name = transaction.metadata.get('discount_name')
            discount_type = transaction.metadata.get('discount_type')
            discount_amount = Decimal(transaction.metadata.get('discount_amount', '0')) if transaction.metadata.get('discount_amount') else None
            discount_percentage = Decimal(transaction.metadata.get('discount_percentage', '0')) if transaction.metadata.get('discount_percentage') else None
            discount_reason = transaction.metadata.get('discount_reason')
            original_unit_price = Decimal(transaction.metadata.get('original_unit_price', str(product.price)))
            
            # Extract purchase type information from transaction metadata
            is_gift = transaction.metadata.get('is_gift_purchase', False)
            is_on_behalf = transaction.metadata.get('is_purchase_on_behalf', False)
            purchased_for_phone = transaction.metadata.get('purchased_for_phone')
            gift_message = transaction.metadata.get('gift_message')
            purchased_for_user = None
            
            # If this is a gift or on-behalf purchase, try to find the recipient user by phone
            if (is_gift or is_on_behalf) and purchased_for_phone:
                try:
                    from accounts.models import CustomUser
                    # Normalize phone numbers for comparison (last 9 digits)
                    purchased_for_phone_digits = ''.join(filter(str.isdigit, str(purchased_for_phone)))[-9:]
                    
                    recipient = CustomUser.objects.filter(
                        phone__icontains=purchased_for_phone_digits
                    ).first()
                    
                    if recipient:
                        purchased_for_user = recipient
                        purchase_type = "gift" if is_gift else "on-behalf"
                        logger.info(f"{purchase_type.capitalize()} purchase: Found recipient user {recipient.student_id or recipient.phone} for phone {purchased_for_phone}")
                    else:
                        purchase_type = "gift" if is_gift else "on-behalf"
                        logger.info(f"{purchase_type.capitalize()} purchase: No user found for phone {purchased_for_phone}, will auto-link on registration")
                except Exception as e:
                    logger.error(f"Error finding recipient user: {e}")
            
            # Create ProductPayment record
            product_payment, created = ProductPayment.objects.get_or_create(
                reference=transaction.reference,
                defaults={
                    'transaction_record': transaction,
                    'transaction': str(transaction.id),
                    'buyer': transaction.user,  # Who paid
                    'product': product,
                    'phone': transaction.customer_phone,
                    'customer_name': transaction.customer_name,
                    'customer_email': transaction.customer_email,
                    'amount': transaction.amount,
                    'quantity': quantity,
                    'payment_successful': True,
                    'transaction_validation_code': validation_code,
                    'variant_selections': variant_selections,
                    # Discount fields
                    'discount_applied': discount_applied,
                    'original_price': original_unit_price,
                    'price_at_purchase': original_unit_price if not discount_applied else (transaction.amount / quantity),
                    'discount_amount': discount_amount,
                    'discount_type': discount_type,
                    'discount_percentage': discount_percentage,
                    'discount_reason': discount_reason,
                    # Purchase type fields
                    'is_gift_purchase': is_gift,
                    'is_purchase_on_behalf': is_on_behalf,
                    'purchased_for_phone': purchased_for_phone if (is_gift or is_on_behalf) else None,
                    'purchased_for_user': purchased_for_user if (is_gift or is_on_behalf) else None,
                    'gift_message': gift_message if is_gift else None,
                    'gift_linked_at': timezone.now() if ((is_gift or is_on_behalf) and purchased_for_user) else None,
                }
            )
            
            # Record discount usage if a discount was applied
            if created and discount_applied and discount_name:
                try:
                    from products.models import ProductDiscount
                    # Find the discount by name and product
                    discount_obj = ProductDiscount.objects.filter(
                        product=product, 
                        name=discount_name, 
                        is_active=True
                    ).first()
                    if discount_obj:
                        discount_obj.record_usage(transaction.user, transaction)
                        product_payment.discount = discount_obj
                        product_payment.save(update_fields=['discount'])
                        logger.info(f"Discount usage recorded for {discount_name}")
                except Exception as e:
                    logger.warning(f"Failed to record discount usage: {e}")
            
            if created:
                logger.info(f"ProductPayment created: {product_payment.payment_id}")
            else:
                # IMPORTANT: Use the existing validation code from DB, not the newly generated one
                validation_code = product_payment.transaction_validation_code
                
                product_payment.payment_successful = True
                product_payment.customer_name = transaction.customer_name
                product_payment.customer_email = transaction.customer_email
                product_payment.transaction_record = transaction
                product_payment.variant_selections = variant_selections
                product_payment.save()
                logger.info(f"ProductPayment updated: {product_payment.payment_id}, using existing validation code: {validation_code}")
            
            product_payments.append(product_payment)
            validation_codes.append({
                'code': validation_code,
                'product_name': product.product_name,
                'quantity': quantity,
                'product_id': str(product.product_id),
                'variant_selections': cls._format_variant_selections(product_payment.variant_selections),
            })
            
            # Reduce stock (with variant support)
            if reduce_stock:
                if variant_selections and (product.has_colors or product.has_sizes):
                    # For products with variants, reduce stock per variant
                    for variant in variant_selections:
                        v_color_id = variant.get('color_id')
                        v_size_id = variant.get('size_id')
                        v_qty = variant.get('quantity', 1)
                        
                        success = product.reduce_stock(
                            quantity=v_qty,
                            color=v_color_id,
                            size=v_size_id
                        )
                        if success:
                            logger.info(f"Variant stock reduced for {product.product_name} "
                                       f"(color={v_color_id}, size={v_size_id}): -{v_qty}")
                        else:
                            logger.warning(f"Failed to reduce variant stock for {product.product_name} "
                                          f"(color={v_color_id}, size={v_size_id})")
                elif product.stock_quantity >= quantity:
                    # For simple products without variants
                    old_stock = product.stock_quantity
                    product.reduce_stock(quantity)
                    logger.info(f"Stock reduced: {old_stock} -> {product.stock_quantity}")
            
            # Send notification (only if not already sent)
            notification_already_sent = transaction.metadata.get('notification_sent', {}).get('push_sent', False)
            if send_notification and validation_code and not notification_already_sent:
                try:
                    notification_results = cls._send_purchase_notification(transaction, product)
                    
                    if not transaction.metadata:
                        transaction.metadata = {}
                    transaction.metadata['notification_sent'] = {
                        'push_sent': notification_results.get('push_sent', False),
                        'sms_sent': notification_results.get('sms_sent', False),
                        'sent_at': timezone.now().isoformat(),
                        'sent_by': 'complete_product_payment',
                    }
                    transaction.save(update_fields=['metadata'])
                    
                    product_payment.notification_sent = notification_results.get('push_sent', False) or notification_results.get('sms_sent', False)
                    product_payment.sms_sent = notification_results.get('sms_sent', False)
                    product_payment.push_sent = notification_results.get('push_sent', False)
                    product_payment.notification_sent_at = timezone.now()
                    product_payment.save()
                    
                except Exception as e:
                    logger.error(f"Failed to send notifications: {str(e)}", exc_info=True)
            else:
                logger.info(f"Skipping notification for {transaction.reference} - already sent or send_notification=False")
            
            result = {
                'success': True,
                'transaction_id': str(transaction.id),
                'reference': transaction.reference,
                'is_cart_checkout': False,
                'validation_codes': validation_codes,
                'validation_code': validation_code,  # Keep for backward compatibility
                'product_name': product.product_name,
                'amount_paid': str(transaction.amount),
                'product_payment_id': str(product_payment.payment_id),
            }
            
            # Mark as completed and cache result for idempotency
            transaction.metadata['product_payment_completed'] = True
            transaction.metadata['completion_result'] = result
            transaction.metadata['completed_at'] = timezone.now().isoformat()
            transaction.save(update_fields=['metadata'])
        
        logger.info(f"Product payment completed successfully: {result}")
        return result
    
    @classmethod
    def _format_variant_selections(cls, variant_selections):
        """
        Format variant selections with color/size names for API response.
        
        Args:
            variant_selections: List of variant selection dicts with color_id/size_id
        
        Returns:
            List of formatted dicts with color/size names
        """
        if not variant_selections:
            return []
        
        from products.models import ProductColor, ProductSize
        
        formatted = []
        for selection in variant_selections:
            item = {'quantity': selection.get('quantity', 1)}
            
            # Get color name
            color_id = selection.get('color_id')
            if color_id:
                try:
                    color = ProductColor.objects.get(id=color_id)
                    item['color'] = color.name
                    item['color_hex'] = color.hex_code
                except ProductColor.DoesNotExist:
                    pass
            
            # Get size name
            size_id = selection.get('size_id')
            if size_id:
                try:
                    size = ProductSize.objects.get(id=size_id)
                    item['size'] = size.name
                except ProductSize.DoesNotExist:
                    pass
            
            formatted.append(item)
        
        return formatted
    
    @classmethod
    def _send_cart_purchase_notification(cls, transaction: Transaction, validation_codes: list, product_payments: list):
        """
        Send notification for cart purchase with multiple validation codes
        
        Args:
            transaction: Transaction instance
            validation_codes: List of dicts with code, product_name, quantity
            product_payments: List of ProductPayment instances
        """
        user = transaction.user
        
        notification_results = {
            'push_sent': False,
            'sms_sent': False,
            'push_error': None,
            'sms_error': None,
        }
        
        # Build message with all validation codes
        codes_text = "\n".join([
            f"• {vc['product_name']} (x{vc['quantity']}): {vc['code']}"
            for vc in validation_codes
        ])
        
        # Try Push Notification
        if user:
            try:
                from notifications.services import PushNotificationService
                from notifications.models import PushNotificationDevice
                
                has_push_devices = PushNotificationDevice.objects.filter(
                    user=user,
                    is_active=True
                ).exists()
                
                if has_push_devices:
                    push_result = PushNotificationService.send_to_user(
                        user=user,
                        title="🎉 Cart Purchase Successful!",
                        body=f"Your purchase of {len(validation_codes)} item(s) is confirmed. Check your purchases for validation codes.",
                        data={
                            'type': 'cart_purchase',
                            'validation_codes': validation_codes,
                            'transaction_id': str(transaction.id),
                            'reference': transaction.reference,
                            'amount': str(transaction.amount),
                            'items_count': len(validation_codes),
                            'screen': 'purchases',
                        },
                        priority='high',
                        badge=len(validation_codes),
                        category='merchandise',
                    )
                    
                    if push_result.get('success'):
                        notification_results['push_sent'] = True
                        logger.info(f"Push notification sent for cart purchase to {user.username}")
                    else:
                        notification_results['push_error'] = push_result.get('error', 'Unknown error')
                        
            except Exception as e:
                notification_results['push_error'] = str(e)
                logger.error(f"Push notification exception: {str(e)}", exc_info=True)
        
        # SMS sending disabled - uncomment when needed
        # phone = transaction.customer_phone
        # if phone:
        #     try:
        #         phone_str = str(phone).replace('+233', '0').replace('+', '')
        #         
        #         # Build SMS message manually since it has multiple codes
        #         sms_message = f"{settings.BRAND_SITE_LABEL} Purchase Confirmed!\n\nYour validation codes:\n{codes_text}\n\nTotal: GHS {transaction.amount}\n\nPresent these codes to collect your items."
        #         
        #         success, message, campaign_id = notify_user(phone_str, sms_message)
        #         
        #         if success:
        #             notification_results['sms_sent'] = True
        #             logger.info(f"SMS sent for cart purchase to {phone_str}")
        #         else:
        #             notification_results['sms_error'] = message
        #             
        #     except Exception as e:
        #         notification_results['sms_error'] = str(e)
        #         logger.error(f"SMS exception: {str(e)}", exc_info=True)
        
        return notification_results
    
    @classmethod
    def _send_purchase_notification(cls, transaction: Transaction, product: Product):
        """
        Send notification to customer via SMS and/or Push Notification with validation code
        
        Priority:
        1. Push Notification (if user has active devices)
        2. SMS (always sent as backup)
        
        Args:
            transaction: Transaction instance
            product: Product instance
        """
        from products.models import ProductPayment
        user = transaction.user
        # Get validation code from ProductPayment record
        product_payment = ProductPayment.objects.filter(reference=transaction.reference).first()
        validation_code = product_payment.transaction_validation_code if product_payment else 'N/A'
        
        notification_results = {
            'push_sent': False,
            'sms_sent': False,
            'push_error': None,
            'sms_error': None,
        }
        
        # Try Push Notification first (prioritized)
        if user:
            try:
                from notifications.services import PushNotificationService
                from notifications.models import PushNotificationDevice
                
                # Check if user has active push devices
                has_push_devices = PushNotificationDevice.objects.filter(
                    user=user,
                    is_active=True
                ).exists()
                
                if has_push_devices:
                    push_result = PushNotificationService.send_to_user(
                        user=user,
                        title="🎉 Purchase Successful!",
                        body=f"Your {product.product_name} purchase is confirmed. Validation Code: {validation_code}",
                        data={
                            'type': 'product_purchase',
                            'validation_code': validation_code,
                            'product_id': str(product.product_id),
                            'product_name': product.product_name,
                            'transaction_id': str(transaction.id),
                            'reference': transaction.reference,
                            'amount': str(transaction.amount),
                            'screen': 'purchases',  # Navigate to purchases screen
                        },
                        priority='high',
                        badge=1,
                        category='merchandise',
                    )
                    
                    if push_result.get('success'):
                        notification_results['push_sent'] = True
                        device_count = push_result.get('devices_count', 1)
                        logger.info(f"Push notification sent to {device_count} device(s) for user {user.username}")
                    else:
                        notification_results['push_error'] = push_result.get('error', 'Unknown error')
                        logger.warning(f"Push notification failed for {user.username}: {notification_results['push_error']}")
                else:
                    logger.info(f"No active push devices for user {user.username}")
                    
            except Exception as e:
                notification_results['push_error'] = str(e)
                logger.error(f"Push notification exception for {user.username}: {str(e)}", exc_info=True)
        
        # SMS sending disabled - uncomment when needed
        # phone = transaction.customer_phone
        # if phone:
        #     try:
        #         # Format phone number (remove country code if present)
        #         phone_str = str(phone).replace('+233', '0').replace('+', '')
        #         
        #         success, message, campaign_id = send_sms_message(
        #             phone_str,
        #             "product_purchase.txt",
        #             {
        #                 "purchase_code": validation_code,
        #                 "product_name": product.product_name,
        #             },
        #         )
        #         
        #         if success:
        #             notification_results['sms_sent'] = True
        #             logger.info(f"SMS sent to {phone_str} (Campaign: {campaign_id})")
        #         else:
        #             notification_results['sms_error'] = message
        #             logger.error(f"SMS failed for {phone_str}: {message}")
        #             
        #     except Exception as e:
        #         notification_results['sms_error'] = str(e)
        #         logger.error(f"SMS exception for {phone_str}: {str(e)}", exc_info=True)
        
        # Log notification summary
        if notification_results['push_sent'] or notification_results['sms_sent']:
            channels = []
            if notification_results['push_sent']:
                channels.append('Push')
            if notification_results['sms_sent']:
                channels.append('SMS')
            logger.info(f"Validation code sent via: {', '.join(channels)}")
        else:
            logger.error(f"WARNING: Failed to send validation code via any channel")
            if notification_results.get('push_error'):
                logger.error(f"   Push Error: {notification_results['push_error']}")
            if notification_results.get('sms_error'):
                logger.error(f"   SMS Error: {notification_results['sms_error']}")
        
        return notification_results
    
    @classmethod
    def _send_collection_notification(
        cls,
        product_payment,
        summary: Dict[str, Any],
        product_name: str
    ) -> Dict[str, Any]:
        """
        Send push notification to user when their merchandise is collected.
        
        Args:
            product_payment: ProductPayment instance
            summary: Collection summary dict
            product_name: Name of the product
        
        Returns:
            Dict with notification status
        """
        from notifications.services import PushNotificationService
        from accounts.models import CustomUser
        
        notification_result = {
            'push_sent': False,
            'push_error': None
        }
        
        try:
            # Find user by phone number
            if not product_payment.phone:
                logger.warning("No phone number for collection notification")
                return notification_result
            
            phone_str = str(product_payment.phone)
            
            try:
                user = CustomUser.objects.get(phone=phone_str)
            except CustomUser.DoesNotExist:
                # Try without + prefix if it has one
                if phone_str.startswith('+'):
                    try:
                        user = CustomUser.objects.get(phone=phone_str[1:])
                    except CustomUser.DoesNotExist:
                        logger.warning(f"No user found for phone {phone_str}")
                        return notification_result
                else:
                    logger.warning(f"No user found for phone {phone_str}")
                    return notification_result
            
            # Build notification message based on collection status
            total_collected = summary.get('total_collected', 0)
            total_ordered = summary.get('total_ordered', 0)
            overall_status = summary.get('overall_status', 'pending')
            
            if overall_status == 'collected':
                # All items collected
                title = "✅ Merchandise Collected!"
                body = f"Your {product_name} order has been fully collected. ({total_collected}/{total_ordered} items)"
            elif overall_status == 'partial':
                # Partial collection
                title = "📦 Partial Collection"
                body = f"You've collected {total_collected} of {total_ordered} items from your {product_name} order. Come back for the rest!"
            else:
                # First collection
                title = "📦 Collection Started"
                body = f"Your {product_name} collection has started. ({total_collected}/{total_ordered} items collected)"
            
            # Send push notification to all user devices (mobile + web)
            result = PushNotificationService.send_to_user(
                user=user,
                title=title,
                body=body,
                data={
                    'type': 'merchandise_collected',
                    'product_name': product_name,
                    'validation_code': product_payment.transaction_validation_code,
                    'collected': total_collected,
                    'total': total_ordered,
                    'status': overall_status,
                    'screen': 'purchases',  # Navigate to purchases screen
                },
                priority='high',
                category='merchandise'
            )
            
            if result.get('success'):
                notification_result['push_sent'] = True
                logger.info(f"Collection notification sent to {phone_str}")
            else:
                notification_result['push_error'] = result.get('error', 'Unknown error')
                logger.warning(f"Collection notification failed for {phone_str}: {result.get('error')}")
                
        except Exception as e:
            notification_result['push_error'] = str(e)
            logger.error(f"Collection notification exception: {str(e)}", exc_info=True)
        
        return notification_result
    
    @classmethod
    @db_transaction.atomic
    def mark_merchandise_collected(
        cls,
        validation_code: str,
        collected_by: Optional[Any] = None,
        variant_collections: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Mark merchandise as collected using validation code.
        Supports partial collection with per-variant tracking.
        
        Args:
            validation_code: 6-character validation code
            collected_by: User/staff who verified the collection
            variant_collections: Optional list of specific variant collections:
                [{
                    'variant_index': 0,
                    'quantity': 1,
                    'substituted': False,
                    'substitution_notes': ''
                }]
                If None, marks ALL variants as fully collected.
        
        Returns:
            Dict with collection status and details
        
        Raises:
            ValueError: If validation code invalid or payment not successful
        """
        from products.models import ProductPayment
        
        collector_name = str(collected_by) if collected_by else 'Admin'
        
        # First try ProductPayment (new architecture - cart checkout items)
        try:
            product_payment = ProductPayment.objects.select_for_update().get(
                transaction_validation_code=validation_code.upper()
            )
            
            if not product_payment.payment_successful:
                raise ValueError("Payment not successful")
            
            # Initialize collection details if not already done
            product_payment.initialize_collection_details()
            
            # Get current collection summary
            summary_before = product_payment.get_collection_summary()
            
            if variant_collections:
                # Partial collection - collect specific variants
                collected_variants = []
                for vc in variant_collections:
                    variant_idx = vc.get('variant_index', 0)
                    qty = vc.get('quantity', 1)
                    substituted = vc.get('substituted', False)
                    notes = vc.get('substitution_notes', '')
                    
                    detail = product_payment.collect_variant(
                        variant_index=variant_idx,
                        quantity=qty,
                        collected_by=collector_name,
                        substituted=substituted,
                        substitution_notes=notes
                    )
                    collected_variants.append(detail)
            else:
                # Full collection - mark all variants as fully collected
                if summary_before['overall_status'] == 'collected':
                    raise ValueError(
                        f"All merchandise already collected on "
                        f"{product_payment.merchandise_taken_at.strftime('%Y-%m-%d %H:%M') if product_payment.merchandise_taken_at else 'unknown date'}"
                    )
                
                collected_variants = []
                for idx, detail in enumerate(product_payment.collection_details):
                    if detail.get('status') != 'collected':
                        remaining = detail.get('ordered_quantity', 1) - detail.get('collected_quantity', 0)
                        if remaining > 0:
                            updated_detail = product_payment.collect_variant(
                                variant_index=idx,
                                quantity=remaining,
                                collected_by=collector_name
                            )
                            collected_variants.append(updated_detail)
            
            # Get updated summary
            summary_after = product_payment.get_collection_summary()
            product = product_payment.product
            
            # Send push notification to user about collection
            cls._send_collection_notification(
                product_payment=product_payment,
                summary=summary_after,
                product_name=product.product_name if product else 'Unknown'
            )
            
            return {
                'success': True,
                'product_payment_id': str(product_payment.payment_id),
                'validation_code': product_payment.transaction_validation_code,
                'reference': product_payment.reference,
                'product_name': product.product_name if product else 'Unknown',
                'quantity': product_payment.quantity,
                'customer_name': product_payment.customer_name,
                'customer_phone': str(product_payment.phone) if product_payment.phone else None,
                'customer_email': product_payment.customer_email,
                'amount_paid': str(product_payment.amount),
                'collection_summary': summary_after,
                'collected_variants': collected_variants,
                'formatted_collection_details': product_payment.get_formatted_collection_details(),
                'fully_collected': summary_after['overall_status'] == 'collected',
                'collected_at': product_payment.merchandise_taken_at,
            }
            
        except ProductPayment.DoesNotExist:
            raise ValueError("Invalid validation code - no product payment found")
    
    @classmethod
    @db_transaction.atomic
    def mark_variant_unavailable(
        cls,
        validation_code: str,
        variant_index: int,
        reason: str = '',
        marked_by: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Mark a specific variant as unavailable (out of stock, etc.)
        
        Args:
            validation_code: 6-character validation code
            variant_index: Index of the variant to mark
            reason: Reason for unavailability
            marked_by: Staff who marked it
        
        Returns:
            Dict with updated collection details
        """
        from products.models import ProductPayment
        
        marker_name = str(marked_by) if marked_by else 'Admin'
        
        try:
            product_payment = ProductPayment.objects.select_for_update().get(
                transaction_validation_code=validation_code.upper()
            )
        except ProductPayment.DoesNotExist:
            raise ValueError("Invalid validation code")
        
        if not product_payment.payment_successful:
            raise ValueError("Payment not successful")
        
        product_payment.initialize_collection_details()
        detail = product_payment.mark_variant_unavailable(
            variant_index=variant_index,
            reason=reason,
            marked_by=marker_name
        )
        
        return {
            'success': True,
            'variant_index': variant_index,
            'updated_detail': detail,
            'collection_summary': product_payment.get_collection_summary(),
            'formatted_collection_details': product_payment.get_formatted_collection_details(),
        }
    
    @classmethod
    def get_collection_status(cls, validation_code: str) -> Dict[str, Any]:
        """
        Get current collection status for a validation code.
        
        Args:
            validation_code: 6-character validation code
        
        Returns:
            Dict with full collection details
        """
        from products.models import ProductPayment
        
        # Try ProductPayment first
        try:
            product_payment = ProductPayment.objects.select_related('product').get(
                transaction_validation_code=validation_code.upper()
            )
            
            product_payment.initialize_collection_details()
            product = product_payment.product
            
            return {
                'success': True,
                'source': 'product_payment',
                'product_payment_id': str(product_payment.payment_id),
                'validation_code': product_payment.transaction_validation_code,
                'reference': product_payment.reference,
                'product_name': product.product_name if product else 'Unknown',
                'product_image': product.get_image_url() if product and hasattr(product, 'get_image_url') else None,
                'quantity': product_payment.quantity,
                'customer_name': product_payment.customer_name,
                'customer_phone': str(product_payment.phone) if product_payment.phone else None,
                'customer_email': product_payment.customer_email,
                'amount_paid': str(product_payment.amount) if product_payment.amount else '0',
                'payment_successful': product_payment.payment_successful,
                'paid_at': product_payment.payed_at,
                'academic_year': product_payment.academic_year,
                'collection_summary': product_payment.get_collection_summary(),
                'collection_details': product_payment.collection_details,
                'formatted_collection_details': product_payment.get_formatted_collection_details(),
                'merchandise_taken': product_payment.merchandise_taken,
                'merchandise_taken_at': product_payment.merchandise_taken_at,
                'taken_by': product_payment.taken_by,
            }
            
        except ProductPayment.DoesNotExist:
            raise ValueError("Invalid validation code - no product payment found")
    
    @classmethod
    def get_product_transaction(cls, reference: str) -> Optional[Transaction]:
        """
        Get a product transaction by reference
        
        Args:
            reference: Transaction reference
        
        Returns:
            Transaction instance or None
        """
        try:
            return Transaction.objects.select_related(
                'user', 'currency', 'gateway'
            ).get(reference=reference, transaction_type='payment')
        except Transaction.DoesNotExist:
            return None
    
    @classmethod
    def get_user_product_purchases(cls, user, status: Optional[str] = None):
        """
        Get all product purchases for a user
        
        Args:
            user: User instance
            status: Filter by status (optional)
        
        Returns:
            QuerySet of Transaction instances
        """
        from django.db.models import Q
        
        product_content_type = ContentType.objects.get_for_model(Product)
        
        queryset = Transaction.objects.filter(
            user=user,
            transaction_type='payment',
            content_type=product_content_type
        ).select_related('currency', 'gateway').order_by('-initiated_at')
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
