"""
Transaction Service
Handles transaction creation, updates, and management
"""
from typing import Dict, Any, Optional
from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from ..models import Transaction, PaymentGateway, Currency, PaymentSession
from .gateway_base import BasePaymentGateway
from .paystack_gateway import PaystackGateway
import uuid
import logging

logger = logging.getLogger(__name__)


class TransactionService:
    """
    Service for managing transactions
    
    Provides methods for:
    - Creating transactions
    - Updating transaction status
    - Processing payments
    - Automatic rollback on errors
    """
    
    # Map gateway names to gateway classes
    GATEWAY_MAP = {
        'paystack': PaystackGateway,
        # Add more gateways here
        # 'flutterwave': FlutterwaveGateway,
        # 'stripe': StripeGateway,
    }
    
    @classmethod
    def get_gateway_instance(cls, gateway_name: str) -> BasePaymentGateway:
        """
        Get gateway instance by name
        
        Args:
            gateway_name: Name of the gateway (e.g., 'paystack')
        
        Returns:
            BasePaymentGateway instance
        
        Raises:
            ValueError: If gateway not found or not supported
        """
        try:
            gateway_model = PaymentGateway.objects.get(
                name=gateway_name,
                is_active=True,
                status='active'
            )
        except PaymentGateway.DoesNotExist:
            raise ValueError(f"Gateway '{gateway_name}' not found or not active")
        
        gateway_class = cls.GATEWAY_MAP.get(gateway_name)
        if not gateway_class:
            raise ValueError(f"Gateway '{gateway_name}' not implemented")
        
        return gateway_class(gateway_model)
    
    @classmethod
    def generate_reference(cls, prefix: str = 'TXN') -> str:
        """
        Generate unique transaction reference
        
        Args:
            prefix: Reference prefix
        
        Returns:
            Unique reference string
        """
        return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"
    
    @classmethod
    @db_transaction.atomic
    def create_transaction(
        cls,
        user,
        amount: Decimal,
        currency_code: str,
        description: str,
        transaction_type: str = 'payment',
        gateway_name: Optional[str] = None,
        content_object=None,
        metadata: Optional[Dict] = None,
        **kwargs
    ) -> Transaction:
        """
        Create a new transaction
        
        Args:
            user: User initiating transaction
            amount: Transaction amount
            currency_code: Currency code (e.g., 'GHS')
            description: Transaction description
            transaction_type: Type of transaction
            gateway_name: Payment gateway to use
            content_object: Related object (product, event, etc.)
            metadata: Additional metadata
            **kwargs: Additional transaction fields
        
        Returns:
            Transaction instance
        """
        # Get currency
        try:
            currency = Currency.objects.get(code=currency_code, is_active=True)
        except Currency.DoesNotExist:
            raise ValueError(f"Currency '{currency_code}' not found or not active")
        
        # Get gateway if specified
        gateway = None
        if gateway_name:
            try:
                gateway = PaymentGateway.objects.get(
                    name=gateway_name,
                    is_active=True,
                    status='active'
                )
            except PaymentGateway.DoesNotExist:
                raise ValueError(f"Gateway '{gateway_name}' not found or not active")
        
        # Generate reference if not provided
        reference = kwargs.pop('reference', None) or cls.generate_reference()
        
        # Calculate fees
        gateway_fee = Decimal('0.00')
        if gateway:
            gateway_fee = gateway.calculate_fee(amount)
        
        platform_fee = kwargs.pop('platform_fee', Decimal('0.00'))
        net_amount = amount - gateway_fee - platform_fee
        
        # Get content type if content object provided
        content_type = None
        object_id = None
        if content_object:
            content_type = ContentType.objects.get_for_model(content_object)
            object_id = str(content_object.pk)
        
        # Create transaction
        transaction = Transaction.objects.create(
            reference=reference,
            user=user,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            gateway=gateway,
            description=description,
            content_type=content_type,
            object_id=object_id,
            gateway_fee=gateway_fee,
            platform_fee=platform_fee,
            net_amount=net_amount,
            metadata=metadata or {},
            customer_email=kwargs.pop('customer_email', user.email),
            customer_phone=kwargs.pop('customer_phone', getattr(user, 'phone_number', '')),
            customer_name=kwargs.pop('customer_name', user.get_full_name()),
            ip_address=kwargs.pop('ip_address', None),
            user_agent=kwargs.pop('user_agent', ''),
            **kwargs
        )
        
        return transaction
    
    @classmethod
    @db_transaction.atomic
    def initialize_payment(
        cls,
        transaction: Transaction,
        callback_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Initialize payment with gateway
        
        Args:
            transaction: Transaction to initialize
            callback_url: URL to redirect after payment
            **kwargs: Additional gateway parameters
        
        Returns:
            Dict with authorization_url and other payment details
        
        Raises:
            ValueError: If transaction invalid or gateway not set
        """
        if not transaction.gateway:
            raise ValueError("Transaction has no payment gateway")
        
        if transaction.status != 'pending':
            raise ValueError(f"Cannot initialize payment for transaction with status '{transaction.status}'")
        
        # Get gateway instance
        gateway = cls.get_gateway_instance(transaction.gateway.name)
        
        try:
            # Initialize payment with gateway
            result = gateway.initialize_payment(
                amount=transaction.amount,
                email=transaction.customer_email,
                reference=transaction.reference,
                callback_url=callback_url,
                metadata=transaction.metadata,
                currency=transaction.currency.code,
                **kwargs
            )
            
            # Update transaction
            transaction.status = 'processing'
            transaction.gateway_reference = result.get('gateway_reference')
            transaction.gateway_metadata = result
            transaction.save()
            
            return result
        
        except Exception as e:
            # Mark transaction as failed
            transaction.status = 'failed'
            transaction.status_message = str(e)
            transaction.save()
            raise
    
    @classmethod
    def verify_payment(cls, reference: str) -> Transaction:
        """
        Verify payment and update transaction
        
        NOTE: Removed @db_transaction.atomic decorator to avoid nested atomic block
        issues when called from views that already have atomic operations.
        The caller is responsible for transaction management if needed.
        
        Args:
            reference: Transaction reference (our internal reference)
        
        Returns:
            Updated Transaction instance
        
        Raises:
            ValueError: If transaction not found
        """
        try:
            transaction = Transaction.objects.get(reference=reference)
        except Transaction.DoesNotExist:
            raise ValueError(f"Transaction with reference '{reference}' not found")
        
        if not transaction.gateway:
            raise ValueError("Transaction has no payment gateway")
        
        # Get gateway instance
        gateway = cls.get_gateway_instance(transaction.gateway.name)
        
        try:
            # CRITICAL FIX: Try multiple verification methods
            # 1. Try gateway_reference if it exists and is different from our reference
            # 2. Try our reference (works if Paystack used it as their reference)
            # 3. If both fail, we're out of luck until we sync with Paystack transaction list
            
            verification_error = None
            result = None
            
            # Try with gateway_reference first (if it's different from our reference)
            if transaction.gateway_reference and transaction.gateway_reference != reference:
                try:
                    logger.info(f"Attempting verification with gateway_reference: {transaction.gateway_reference}")
                    result = gateway.verify_payment(transaction.gateway_reference)
                except Exception as e:
                    verification_error = e
                    logger.warning(f"Verification with gateway_reference failed: {str(e)[:100]}")
            
            # If that didn't work, try our reference
            if not result:
                try:
                    logger.info(f"Attempting verification with our reference: {reference}")
                    result = gateway.verify_payment(reference)
                except Exception as e:
                    verification_error = e
                    logger.warning(f"Verification with our reference failed: {str(e)[:100]}")
            
            # If both failed, raise the last error
            if not result:
                if verification_error:
                    raise verification_error
                else:
                    raise ValueError("Verification failed with no error details")
            
            # Update transaction based on gateway response
            transaction.status = result.get('status', 'failed')
            transaction.gateway_response = str(result.get('gateway_response', {}))
            transaction.payment_channel = result.get('channel', '')
            transaction.gateway_reference = result.get('gateway_reference', transaction.gateway_reference)
            
            # IMPORTANT: Update gateway_reference with transaction_id if we got it
            # This ensures future verifications will use Paystack's actual ID
            if result.get('transaction_id') and not transaction.gateway_reference:
                transaction.gateway_reference = result['transaction_id']
                logger.info(f"Updated gateway_reference to Paystack transaction ID: {result['transaction_id']}")
            
            # Update fees if provided
            if 'fees' in result:
                transaction.gateway_fee = result['fees']
                transaction.net_amount = transaction.amount - transaction.gateway_fee - transaction.platform_fee
            
            # Set completion timestamp
            if transaction.status == 'success':
                transaction.completed_at = timezone.now()
            
            transaction.save()
            
            return transaction
        
        except Exception as e:
            transaction.status = 'failed'
            transaction.status_message = str(e)
            transaction.save()
            raise
    
    @classmethod
    @db_transaction.atomic
    def complete_transaction(
        cls,
        transaction: Transaction,
        gateway_response: Optional[Dict] = None
    ) -> Transaction:
        """
        Mark transaction as complete
        
        Args:
            transaction: Transaction to complete
            gateway_response: Gateway response data
        
        Returns:
            Updated Transaction instance
        """
        transaction.status = 'success'
        transaction.completed_at = timezone.now()
        
        if gateway_response:
            transaction.gateway_response = str(gateway_response)
        
        transaction.save()
        return transaction
    
    @classmethod
    @db_transaction.atomic
    def fail_transaction(
        cls,
        transaction: Transaction,
        reason: str,
        gateway_response: Optional[Dict] = None
    ) -> Transaction:
        """
        Mark transaction as failed
        
        Args:
            transaction: Transaction to fail
            reason: Failure reason
            gateway_response: Gateway response data
        
        Returns:
            Updated Transaction instance
        """
        transaction.status = 'failed'
        transaction.status_message = reason
        
        if gateway_response:
            transaction.gateway_response = str(gateway_response)
        
        transaction.save()
        return transaction
    
    @classmethod
    def get_user_transactions(
        cls,
        user,
        transaction_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> list:
        """
        Get user's transactions
        
        Args:
            user: User instance
            transaction_type: Filter by transaction type
            status: Filter by status
            limit: Maximum number of transactions
        
        Returns:
            List of Transaction instances
        """
        queryset = Transaction.objects.filter(user=user)
        
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return list(queryset[:limit])
    
    @classmethod
    def get_transaction_by_reference(cls, reference: str) -> Optional[Transaction]:
        """
        Get transaction by reference
        
        Args:
            reference: Transaction reference
        
        Returns:
            Transaction instance or None
        """
        try:
            return Transaction.objects.get(reference=reference)
        except Transaction.DoesNotExist:
            return None
