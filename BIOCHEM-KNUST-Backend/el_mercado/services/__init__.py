"""
El Mercado Services Package
===========================

Provides all service functions for El Mercado marketplace.

Services:
- ElMercadoPaymentService: Order payments, verification, refunds
- PayoutService: Seller payouts and bank management

Usage:
    from el_mercado.services import ElMercadoPaymentService, PayoutService
    
    # Create order and initialize payment
    order, summary = ElMercadoPaymentService.create_order(...)
    result = ElMercadoPaymentService.initialize_payment(order, callback_url)
    
    # Process seller payout
    result = PayoutService.request_payout(seller, amount)
"""

# =============================================================================
# PAYMENT SERVICE
# =============================================================================

"""
El Mercado Payment Service
==========================

Handles all payment operations for the marketplace by integrating with
the main payment system while providing marketplace-specific logic.

Features:
- Order payment initialization
- Payment verification and processing
- Seller wallet management
- Commission calculation
- Escrow handling
- Refund processing
- Transaction history
"""

from decimal import Decimal
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import logging

from django.db import transaction as db_transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from payments.models import Transaction, Currency, PaymentGateway
from payments.services.transaction_service import TransactionService
from payments.services.refund_service import RefundService

from el_mercado.models import (
    MarketplaceOrder,
    OrderItem,
    Seller,
    SellerWallet,
    WalletTransaction,
    Listing,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class PaymentError(Exception):
    """Base exception for payment errors"""
    pass


class PaymentInitializationError(PaymentError):
    """Error during payment initialization"""
    pass


class PaymentVerificationError(PaymentError):
    """Error during payment verification"""
    pass


class InsufficientStockError(PaymentError):
    """Error when stock is insufficient"""
    pass


class OrderNotFoundError(PaymentError):
    """Error when order is not found"""
    pass


class InvalidOrderStateError(PaymentError):
    """Error when order is in invalid state for operation"""
    pass


class RefundError(PaymentError):
    """Error during refund processing"""
    pass


class WalletError(PaymentError):
    """Error during wallet operations"""
    pass


@dataclass
class PaymentResult:
    """Result of a payment operation"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'message': self.message,
            'data': self.data,
            'error_code': self.error_code,
        }


@dataclass
class OrderSummary:
    """Summary of order for payment"""
    order_id: str
    order_number: str
    subtotal: Decimal
    shipping_cost: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    commission_rate: Decimal
    platform_commission: Decimal
    seller_earnings: Decimal
    currency: str
    items: List[Dict[str, Any]]


# =============================================================================
# MAIN PAYMENT SERVICE
# =============================================================================

class ElMercadoPaymentService:
    """
    Main payment service for El Mercado marketplace.
    
    Handles:
    - Order creation and payment initialization
    - Payment verification and order status updates
    - Seller wallet credit after successful payments
    - Commission calculation and deduction
    - Refund processing
    - Escrow management
    """
    
    # Default gateway for marketplace payments
    DEFAULT_GATEWAY = 'paystack'
    
    # Commission rate for platform (can be overridden per seller/category)
    DEFAULT_COMMISSION_RATE = Decimal('10.00')  # 10%
    
    # Escrow hold period in days
    ESCROW_HOLD_DAYS = 7
    
    # ==========================================================================
    # ORDER CREATION
    # ==========================================================================
    
    @classmethod
    def calculate_order_totals(
        cls,
        items: List[Dict[str, Any]],
        seller: Seller,
        shipping_cost: Decimal = Decimal('0.00'),
        discount_amount: Decimal = Decimal('0.00'),
    ) -> OrderSummary:
        """
        Calculate order totals including commission.
        
        Args:
            items: List of items with listing_id, quantity, variant_id (optional)
            seller: Seller instance
            shipping_cost: Shipping cost
            discount_amount: Discount amount
        
        Returns:
            OrderSummary with all calculated amounts
        """
        subtotal = Decimal('0.00')
        item_details = []
        
        for item in items:
            listing = Listing.objects.get(pk=item['listing_id'])
            quantity = item.get('quantity', 1)
            
            # Get variant price if applicable
            if item.get('variant_id'):
                variant = listing.variants.get(pk=item['variant_id'])
                price = variant.price or listing.price
            else:
                price = listing.price
            
            item_total = price * quantity
            subtotal += item_total
            
            item_details.append({
                'listing_id': str(listing.id),
                'listing_title': listing.title,
                'variant_id': item.get('variant_id'),
                'quantity': quantity,
                'unit_price': str(price),
                'total': str(item_total),
            })
        
        # Get commission rate (seller rate or category rate or default)
        commission_rate = seller.commission_rate or cls.DEFAULT_COMMISSION_RATE
        
        # Calculate totals
        total_amount = subtotal + shipping_cost - discount_amount
        platform_commission = total_amount * (commission_rate / 100)
        seller_earnings = total_amount - platform_commission
        
        return OrderSummary(
            order_id='',  # Will be set after order creation
            order_number='',
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            discount_amount=discount_amount,
            total_amount=total_amount,
            commission_rate=commission_rate,
            platform_commission=platform_commission,
            seller_earnings=seller_earnings,
            currency='GHS',
            items=item_details,
        )
    
    @classmethod
    @db_transaction.atomic
    def create_order(
        cls,
        buyer,
        seller: Seller,
        items: List[Dict[str, Any]],
        shipping_info: Dict[str, str],
        shipping_cost: Decimal = Decimal('0.00'),
        discount_amount: Decimal = Decimal('0.00'),
        buyer_notes: str = '',
    ) -> Tuple[MarketplaceOrder, OrderSummary]:
        """
        Create a new marketplace order.
        
        Args:
            buyer: User placing the order
            seller: Seller instance
            items: List of items with listing_id, quantity, variant_id (optional)
            shipping_info: Shipping address information
            shipping_cost: Shipping cost
            discount_amount: Discount amount
            buyer_notes: Notes from buyer
        
        Returns:
            Tuple of (MarketplaceOrder, OrderSummary)
        
        Raises:
            InsufficientStockError: If any item has insufficient stock
            PaymentError: If order creation fails
        """
        # Calculate totals
        summary = cls.calculate_order_totals(items, seller, shipping_cost, discount_amount)
        
        # Validate stock availability
        for item in items:
            listing = Listing.objects.select_for_update().get(pk=item['listing_id'])
            quantity = item.get('quantity', 1)
            
            if listing.track_inventory and not listing.allow_backorder:
                if item.get('variant_id'):
                    variant = listing.variants.get(pk=item['variant_id'])
                    if variant.stock_quantity < quantity:
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
        
        try:
            # Create the order
            order = MarketplaceOrder.objects.create(
                buyer=buyer,
                seller=seller,
                subtotal=summary.subtotal,
                shipping_cost=summary.shipping_cost,
                discount_amount=summary.discount_amount,
                total_amount=summary.total_amount,
                commission_rate=summary.commission_rate,
                platform_commission=summary.platform_commission,
                seller_earnings=summary.seller_earnings,
                currency=summary.currency,
                status='PENDING',
                payment_status='PENDING',
                shipping_name=shipping_info.get('name', buyer.get_full_name()),
                shipping_phone=shipping_info.get('phone', getattr(buyer, 'phone_number', '')),
                shipping_email=shipping_info.get('email', buyer.email),
                shipping_address_line_1=shipping_info.get('address_line_1', ''),
                shipping_address_line_2=shipping_info.get('address_line_2', ''),
                shipping_city=shipping_info.get('city', ''),
                shipping_region=shipping_info.get('region', ''),
                shipping_country=shipping_info.get('country', 'Ghana'),
                buyer_notes=buyer_notes,
            )
            
            # Create order items
            for item in items:
                listing = Listing.objects.get(pk=item['listing_id'])
                quantity = item.get('quantity', 1)
                
                variant = None
                if item.get('variant_id'):
                    variant = listing.variants.get(pk=item['variant_id'])
                    price = variant.price or listing.price
                else:
                    price = listing.price
                
                OrderItem.objects.create(
                    order=order,
                    listing=listing,
                    variant=variant,
                    quantity=quantity,
                    unit_price=price,
                    total_price=price * quantity,
                )
            
            # Update summary with order details
            summary.order_id = str(order.id)
            summary.order_number = order.order_number
            
            logger.info(f"Created order {order.order_number} for buyer {buyer.id}")
            
            return order, summary
        
        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
            raise PaymentError(f"Failed to create order: {str(e)}")
    
    # ==========================================================================
    # PAYMENT INITIALIZATION
    # ==========================================================================
    
    @classmethod
    @db_transaction.atomic
    def initialize_payment(
        cls,
        order: MarketplaceOrder,
        callback_url: str,
        gateway_name: str = None,
        **kwargs
    ) -> PaymentResult:
        """
        Initialize payment for an order.
        
        Args:
            order: MarketplaceOrder instance
            callback_url: URL to redirect after payment
            gateway_name: Payment gateway to use (default: paystack)
            **kwargs: Additional gateway parameters
        
        Returns:
            PaymentResult with authorization_url and payment details
        
        Raises:
            PaymentInitializationError: If initialization fails
        """
        gateway_name = gateway_name or cls.DEFAULT_GATEWAY
        
        # Validate order state
        if order.payment_status == 'PAID':
            return PaymentResult(
                success=False,
                message="Order is already paid",
                error_code="ORDER_ALREADY_PAID"
            )
        
        if order.status in ['CANCELLED', 'REFUNDED']:
            return PaymentResult(
                success=False,
                message=f"Cannot process payment for {order.status.lower()} order",
                error_code="INVALID_ORDER_STATE"
            )
        
        try:
            # Build description
            item_count = order.items.count()
            description = f"El Mercado Order #{order.order_number} ({item_count} item(s))"
            
            # Metadata for tracking
            metadata = {
                'order_id': str(order.id),
                'order_number': order.order_number,
                'seller_id': str(order.seller.id),
                'seller_name': order.seller.display_name,
                'buyer_id': str(order.buyer.id),
                'buyer_email': order.buyer.email,
                'payment_type': 'el_mercado_order',
                'item_count': item_count,
            }
            
            # Create transaction using main payment service
            transaction = TransactionService.create_transaction(
                user=order.buyer,
                amount=order.total_amount,
                currency_code=order.currency,
                description=description,
                transaction_type='payment',
                gateway_name=gateway_name,
                content_object=order,
                metadata=metadata,
                platform_fee=order.platform_commission,
                customer_email=order.buyer.email,
                customer_phone=str(order.shipping_phone),
                customer_name=order.shipping_name,
            )
            
            # Initialize payment with gateway
            result = TransactionService.initialize_payment(
                transaction=transaction,
                callback_url=callback_url,
                **kwargs
            )
            
            # Update order with payment reference
            order.payment_reference = transaction.reference
            order.status = 'AWAITING_PAYMENT'
            order.update_status('AWAITING_PAYMENT', 'Payment initialized')
            
            logger.info(
                f"Payment initialized for order {order.order_number}, "
                f"reference: {transaction.reference}"
            )
            
            return PaymentResult(
                success=True,
                message="Payment initialized successfully",
                data={
                    'authorization_url': result.get('authorization_url'),
                    'access_code': result.get('access_code'),
                    'reference': transaction.reference,
                    'gateway_reference': result.get('gateway_reference'),
                    'order_number': order.order_number,
                    'amount': str(order.total_amount),
                    'currency': order.currency,
                }
            )
        
        except ValueError as e:
            logger.error(f"Payment initialization failed for order {order.order_number}: {str(e)}")
            return PaymentResult(
                success=False,
                message=str(e),
                error_code="INITIALIZATION_FAILED"
            )
        
        except Exception as e:
            logger.error(f"Unexpected error initializing payment for order {order.order_number}: {str(e)}")
            return PaymentResult(
                success=False,
                message="An unexpected error occurred during payment initialization",
                error_code="UNEXPECTED_ERROR"
            )
    
    # ==========================================================================
    # PAYMENT VERIFICATION
    # ==========================================================================
    
    @classmethod
    @db_transaction.atomic
    def verify_payment(cls, reference: str) -> PaymentResult:
        """
        Verify payment and update order status.
        
        Args:
            reference: Transaction reference
        
        Returns:
            PaymentResult with verification status
        """
        try:
            # Get the transaction
            try:
                transaction = Transaction.objects.get(reference=reference)
            except Transaction.DoesNotExist:
                logger.error(f"Transaction not found: {reference}")
                return PaymentResult(
                    success=False,
                    message="Transaction not found",
                    error_code="TRANSACTION_NOT_FOUND"
                )
            
            # Check if already processed
            if transaction.status == 'success':
                # Get the order
                order = cls._get_order_from_transaction(transaction)
                if order and order.payment_status == 'PAID':
                    return PaymentResult(
                        success=True,
                        message="Payment already verified and processed",
                        data={
                            'order_number': order.order_number,
                            'status': order.status,
                            'payment_status': order.payment_status,
                        }
                    )
            
            # Verify with gateway
            try:
                verified_transaction = TransactionService.verify_payment(reference)
            except Exception as e:
                logger.error(f"Gateway verification failed for {reference}: {str(e)}")
                return PaymentResult(
                    success=False,
                    message=f"Payment verification failed: {str(e)}",
                    error_code="VERIFICATION_FAILED"
                )
            
            # Process based on verification result
            if verified_transaction.status == 'success':
                return cls._process_successful_payment(verified_transaction)
            else:
                return cls._process_failed_payment(verified_transaction)
        
        except Exception as e:
            logger.error(f"Unexpected error verifying payment {reference}: {str(e)}")
            return PaymentResult(
                success=False,
                message="An unexpected error occurred during verification",
                error_code="UNEXPECTED_ERROR"
            )
    
    @classmethod
    def _get_order_from_transaction(cls, transaction: Transaction) -> Optional[MarketplaceOrder]:
        """Get the associated order from a transaction."""
        try:
            if transaction.content_type:
                if transaction.content_type.model == 'marketplaceorder':
                    return MarketplaceOrder.objects.get(pk=transaction.object_id)
            
            # Fallback: search by payment reference
            return MarketplaceOrder.objects.filter(
                payment_reference=transaction.reference
            ).first()
        except Exception:
            return None
    
    @classmethod
    @db_transaction.atomic
    def _process_successful_payment(cls, transaction: Transaction) -> PaymentResult:
        """Process a successful payment."""
        order = cls._get_order_from_transaction(transaction)
        
        if not order:
            logger.error(f"Order not found for transaction {transaction.reference}")
            return PaymentResult(
                success=False,
                message="Order not found for this transaction",
                error_code="ORDER_NOT_FOUND"
            )
        
        # Update order status
        order.payment_status = 'PAID'
        order.status = 'PAID'
        order.paid_at = timezone.now()
        order.save()
        order.update_status('PAID', 'Payment received successfully')
        
        # Reserve stock
        cls._reserve_stock(order)
        
        # Credit seller's pending balance (escrow)
        cls._credit_seller_wallet(order)
        
        # Send notifications
        cls._send_payment_notifications(order, transaction)
        
        logger.info(f"Payment successful for order {order.order_number}")
        
        return PaymentResult(
            success=True,
            message="Payment verified and processed successfully",
            data={
                'order_number': order.order_number,
                'order_id': str(order.id),
                'status': order.status,
                'payment_status': order.payment_status,
                'total_amount': str(order.total_amount),
                'seller_earnings': str(order.seller_earnings),
                'paid_at': order.paid_at.isoformat() if order.paid_at else None,
            }
        )
    
    @classmethod
    def _process_failed_payment(cls, transaction: Transaction) -> PaymentResult:
        """Process a failed payment."""
        order = cls._get_order_from_transaction(transaction)
        
        if order:
            order.payment_status = 'FAILED'
            order.save()
            order.update_status('PENDING', f'Payment failed: {transaction.status_message}')
        
        logger.warning(f"Payment failed for transaction {transaction.reference}")
        
        return PaymentResult(
            success=False,
            message=f"Payment failed: {transaction.status_message or 'Unknown error'}",
            error_code="PAYMENT_FAILED",
            data={
                'order_number': order.order_number if order else None,
                'transaction_status': transaction.status,
            }
        )
    
    # ==========================================================================
    # STOCK MANAGEMENT
    # ==========================================================================
    
    @classmethod
    def _reserve_stock(cls, order: MarketplaceOrder):
        """Reserve stock for order items."""
        for item in order.items.select_related('listing', 'variant'):
            listing = item.listing
            
            # Always update order count regardless of inventory tracking
            listing.order_count += item.quantity
            
            if listing.track_inventory:
                if item.variant:
                    item.variant.stock_quantity = max(0, item.variant.stock_quantity - item.quantity)
                    item.variant.save(update_fields=['stock_quantity'])
                else:
                    listing.stock_quantity = max(0, listing.stock_quantity - item.quantity)
                    
                    # Check if sold out
                    if listing.stock_quantity == 0 and not listing.allow_backorder:
                        listing.status = 'SOLD_OUT'
                    
                    listing.save(update_fields=['stock_quantity', 'status', 'order_count'])
            else:
                # For non-tracked inventory, just update order count
                listing.save(update_fields=['order_count'])
    
    @classmethod
    def _restore_stock(cls, order: MarketplaceOrder):
        """Restore stock for cancelled/refunded orders."""
        for item in order.items.select_related('listing', 'variant'):
            listing = item.listing
            
            if listing.track_inventory:
                if item.variant:
                    item.variant.stock_quantity += item.quantity
                    item.variant.save(update_fields=['stock_quantity'])
                else:
                    listing.stock_quantity += item.quantity
                    
                    # Restore status if was sold out
                    if listing.status == 'SOLD_OUT':
                        listing.status = 'ACTIVE'
                    
                    listing.save(update_fields=['stock_quantity', 'status'])
    
    # ==========================================================================
    # WALLET MANAGEMENT
    # ==========================================================================
    
    @classmethod
    def _credit_seller_wallet(cls, order: MarketplaceOrder):
        """
        Credit seller's wallet with pending balance (escrow).
        Funds are held until order completion.
        """
        try:
            wallet, created = SellerWallet.objects.get_or_create(seller=order.seller)
            
            # Add to pending balance (escrow)
            wallet.add_pending(
                amount=order.seller_earnings,
                description=f"Order {order.order_number} - Payment received (pending release)"
            )
            
            logger.info(
                f"Credited pending balance for seller {order.seller.display_name}: "
                f"GHS {order.seller_earnings}"
            )
        
        except Exception as e:
            logger.error(f"Failed to credit seller wallet for order {order.order_number}: {str(e)}")
            # Don't fail the payment, but log for manual handling
    
    @classmethod
    @db_transaction.atomic
    def release_order_funds(cls, order: MarketplaceOrder) -> PaymentResult:
        """
        Release funds from escrow to seller's available balance.
        
        Args:
            order: MarketplaceOrder instance
        
        Returns:
            PaymentResult
        """
        if order.funds_released:
            return PaymentResult(
                success=False,
                message="Funds have already been released for this order",
                error_code="FUNDS_ALREADY_RELEASED"
            )
        
        if order.payment_status != 'PAID':
            return PaymentResult(
                success=False,
                message="Cannot release funds for unpaid order",
                error_code="ORDER_NOT_PAID"
            )
        
        if order.status not in ['DELIVERED', 'COMPLETED']:
            return PaymentResult(
                success=False,
                message="Funds can only be released after delivery/completion",
                error_code="ORDER_NOT_COMPLETED"
            )
        
        try:
            wallet = order.seller.wallet
            
            # Release pending to available
            wallet.release_pending(
                amount=order.seller_earnings,
                description=f"Order {order.order_number} - Funds released"
            )
            
            # Deduct platform commission
            wallet.deduct_fee(
                amount=order.platform_commission,
                description=f"Order {order.order_number} - Platform commission"
            )
            
            # Mark funds as released
            order.funds_released = True
            order.funds_released_at = timezone.now()
            order.save(update_fields=['funds_released', 'funds_released_at'])
            
            logger.info(f"Released funds for order {order.order_number}")
            
            return PaymentResult(
                success=True,
                message="Funds released successfully",
                data={
                    'order_number': order.order_number,
                    'amount_released': str(order.seller_earnings),
                    'commission_deducted': str(order.platform_commission),
                }
            )
        
        except Exception as e:
            logger.error(f"Failed to release funds for order {order.order_number}: {str(e)}")
            return PaymentResult(
                success=False,
                message=f"Failed to release funds: {str(e)}",
                error_code="RELEASE_FAILED"
            )
    
    # ==========================================================================
    # REFUNDS
    # ==========================================================================
    
    @classmethod
    @db_transaction.atomic
    def process_refund(
        cls,
        order: MarketplaceOrder,
        reason: str,
        amount: Optional[Decimal] = None,
        initiated_by=None,
    ) -> PaymentResult:
        """
        Process a refund for an order.
        
        Args:
            order: MarketplaceOrder instance
            reason: Reason for refund
            amount: Refund amount (full refund if None)
            initiated_by: User initiating the refund
        
        Returns:
            PaymentResult
        """
        if order.payment_status != 'PAID':
            return PaymentResult(
                success=False,
                message="Cannot refund an unpaid order",
                error_code="ORDER_NOT_PAID"
            )
        
        # Determine refund amount
        refund_amount = amount or order.total_amount
        
        if refund_amount > order.total_amount:
            return PaymentResult(
                success=False,
                message="Refund amount exceeds order total",
                error_code="INVALID_REFUND_AMOUNT"
            )
        
        try:
            # Get the original transaction
            transaction = Transaction.objects.filter(
                reference=order.payment_reference
            ).first()
            
            if not transaction:
                return PaymentResult(
                    success=False,
                    message="Original transaction not found",
                    error_code="TRANSACTION_NOT_FOUND"
                )
            
            # Process refund using main payment service
            refund_result = RefundService.create_refund(
                transaction=transaction,
                amount=refund_amount,
                reason='customer_request',
                reason_details=reason,
                initiated_by=initiated_by,
            )
            
            # Process the refund
            refund = RefundService.process_refund(refund_result)
            
            if refund.status == 'success':
                # Update order status
                is_full_refund = refund_amount >= order.total_amount
                
                if is_full_refund:
                    order.status = 'REFUNDED'
                    order.payment_status = 'REFUNDED'
                else:
                    order.status = 'REFUNDED'  # Or PARTIALLY_REFUNDED if you want
                    order.payment_status = 'REFUNDED'
                
                order.save()
                order.update_status('REFUNDED', f'Refund processed: {reason}')
                
                # Restore stock
                cls._restore_stock(order)
                
                # Deduct from seller wallet if funds were credited
                cls._deduct_seller_wallet_for_refund(order, refund_amount)
                
                logger.info(f"Refund processed for order {order.order_number}: GHS {refund_amount}")
                
                return PaymentResult(
                    success=True,
                    message="Refund processed successfully",
                    data={
                        'order_number': order.order_number,
                        'refund_amount': str(refund_amount),
                        'refund_reference': refund.reference,
                    }
                )
            else:
                return PaymentResult(
                    success=False,
                    message=f"Refund failed: {refund.status_message}",
                    error_code="REFUND_FAILED"
                )
        
        except Exception as e:
            logger.error(f"Refund failed for order {order.order_number}: {str(e)}")
            return PaymentResult(
                success=False,
                message=f"Refund processing failed: {str(e)}",
                error_code="REFUND_ERROR"
            )
    
    @classmethod
    def _deduct_seller_wallet_for_refund(cls, order: MarketplaceOrder, refund_amount: Decimal):
        """Deduct from seller wallet for refund."""
        try:
            wallet = order.seller.wallet
            
            # Calculate seller's portion of refund
            commission_rate = order.commission_rate / 100
            seller_refund = refund_amount * (1 - commission_rate)
            
            if order.funds_released:
                # If funds were already released, deduct from available
                wallet.available_balance -= seller_refund
                wallet.save(update_fields=['available_balance'])
                
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='REFUND_DEDUCT',
                    amount=-seller_refund,
                    description=f"Order {order.order_number} - Refund deduction",
                    balance_after=wallet.available_balance,
                )
            else:
                # If still in escrow, deduct from pending
                wallet.pending_balance -= seller_refund
                wallet.save(update_fields=['pending_balance'])
                
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='REFUND_DEDUCT',
                    amount=-seller_refund,
                    description=f"Order {order.order_number} - Refund deduction (from pending)",
                    balance_after=wallet.pending_balance,
                )
        
        except Exception as e:
            logger.error(f"Failed to deduct wallet for refund: {str(e)}")
    
    # ==========================================================================
    # NOTIFICATIONS
    # ==========================================================================
    
    @classmethod
    def _send_payment_notifications(cls, order: MarketplaceOrder, transaction: Transaction):
        """Send payment notifications to buyer and seller."""
        try:
            # Import here to avoid circular imports
            from notifications.utils import create_notification
            
            # Notify buyer
            create_notification(
                user=order.buyer,
                notification_type='el_mercado_order_paid',
                title='Payment Successful',
                message=f'Your payment of GHS {order.total_amount} for order #{order.order_number} was successful.',
                data={
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                    'amount': str(order.total_amount),
                }
            )
            
            # Notify seller (if notification enabled)
            if order.seller.notify_new_orders and order.seller.user:
                create_notification(
                    user=order.seller.user,
                    notification_type='el_mercado_new_order',
                    title='New Order Received',
                    message=f'You have a new order #{order.order_number} worth GHS {order.total_amount}.',
                    data={
                        'order_id': str(order.id),
                        'order_number': order.order_number,
                        'amount': str(order.total_amount),
                        'seller_earnings': str(order.seller_earnings),
                    }
                )
        
        except Exception as e:
            logger.warning(f"Failed to send payment notifications: {str(e)}")
    
    # ==========================================================================
    # UTILITIES
    # ==========================================================================
    
    @classmethod
    def get_order_payment_status(cls, order_number: str) -> PaymentResult:
        """
        Get the payment status of an order.
        
        Args:
            order_number: Order number
        
        Returns:
            PaymentResult with order details
        """
        try:
            order = MarketplaceOrder.objects.get(order_number=order_number)
            
            return PaymentResult(
                success=True,
                message="Order found",
                data={
                    'order_number': order.order_number,
                    'status': order.status,
                    'payment_status': order.payment_status,
                    'total_amount': str(order.total_amount),
                    'currency': order.currency,
                    'paid_at': order.paid_at.isoformat() if order.paid_at else None,
                    'created_at': order.created_at.isoformat(),
                }
            )
        
        except MarketplaceOrder.DoesNotExist:
            return PaymentResult(
                success=False,
                message="Order not found",
                error_code="ORDER_NOT_FOUND"
            )
    
    @classmethod
    def get_seller_earnings_summary(cls, seller: Seller) -> Dict[str, Any]:
        """
        Get seller's earnings summary.
        
        Args:
            seller: Seller instance
        
        Returns:
            Dictionary with earnings summary
        """
        from django.db.models import Sum
        
        try:
            wallet, _ = SellerWallet.objects.get_or_create(seller=seller)
            
            # Calculate total earnings from completed orders
            completed_orders = MarketplaceOrder.objects.filter(
                seller=seller,
                payment_status='PAID'
            ).aggregate(
                total_revenue=Sum('total_amount'),
                total_earnings=Sum('seller_earnings'),
                total_commission=Sum('platform_commission'),
            )
            
            return {
                'available_balance': str(wallet.available_balance),
                'pending_balance': str(wallet.pending_balance),
                'total_earned': str(wallet.total_earned),
                'total_withdrawn': str(wallet.total_withdrawn),
                'total_fees_paid': str(wallet.total_fees_paid),
                'currency': wallet.currency,
                'total_revenue': str(completed_orders['total_revenue'] or Decimal('0.00')),
                'total_earnings': str(completed_orders['total_earnings'] or Decimal('0.00')),
                'total_commission': str(completed_orders['total_commission'] or Decimal('0.00')),
            }
        
        except Exception as e:
            logger.error(f"Failed to get seller earnings summary: {str(e)}")
            return {}
    
    @classmethod
    def auto_release_completed_orders(cls) -> List[str]:
        """
        Auto-release funds for orders past the escrow period.
        This should be run as a scheduled task.
        
        Returns:
            List of order numbers that were released
        """
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=cls.ESCROW_HOLD_DAYS)
        
        orders = MarketplaceOrder.objects.filter(
            status='COMPLETED',
            payment_status='PAID',
            funds_released=False,
            delivered_at__lte=cutoff_date,
        )
        
        released = []
        for order in orders:
            result = cls.release_order_funds(order)
            if result.success:
                released.append(order.order_number)
        
        if released:
            logger.info(f"Auto-released funds for {len(released)} orders")
        
        return released


# =============================================================================
# PAYOUT SERVICE IMPORT
# =============================================================================

from .payout_service import (
    PayoutService,
    PayoutResult,
    PayoutError,
    InsufficientBalanceError,
    InvalidBankAccountError,
    PayoutProcessingError,
    PayoutLimitExceededError,
)

# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # Payment Service
    'ElMercadoPaymentService',
    'PaymentResult',
    'OrderSummary',
    'PaymentError',
    'PaymentInitializationError',
    'PaymentVerificationError',
    'InsufficientStockError',
    'OrderNotFoundError',
    'InvalidOrderStateError',
    'RefundError',
    'WalletError',
    
    # Payout Service
    'PayoutService',
    'PayoutResult',
    'PayoutError',
    'InsufficientBalanceError',
    'InvalidBankAccountError',
    'PayoutProcessingError',
    'PayoutLimitExceededError',
]