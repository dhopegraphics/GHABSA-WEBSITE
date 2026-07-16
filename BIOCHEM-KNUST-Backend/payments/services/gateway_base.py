"""
Base Payment Gateway Abstract Class
All payment gateway implementations must inherit from this
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal


class PaymentGatewayException(Exception):
    """Base exception for payment gateway errors"""
    pass


class PaymentInitializationError(PaymentGatewayException):
    """Raised when payment initialization fails"""
    pass


class PaymentVerificationError(PaymentGatewayException):
    """Raised when payment verification fails"""
    pass


class RefundError(PaymentGatewayException):
    """Raised when refund processing fails"""
    pass


class WebhookVerificationError(PaymentGatewayException):
    """Raised when webhook signature verification fails"""
    pass


class BasePaymentGateway(ABC):
    """
    Abstract base class for payment gateway integrations
    
    All payment gateways must implement these methods to ensure
    consistent behavior across different providers.
    """
    
    def __init__(self, gateway_model):
        """
        Initialize the gateway with configuration
        
        Args:
            gateway_model: PaymentGateway model instance
        """
        self.gateway = gateway_model
        self.config = gateway_model.config
        self.name = gateway_model.name
        self.is_test_mode = self.config.get('test_mode', False)
    
    @abstractmethod
    def initialize_payment(
        self,
        amount: Decimal,
        email: str,
        reference: str,
        callback_url: str,
        metadata: Optional[Dict[str, Any]] = None,
        currency: str = 'GHS',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Initialize a payment transaction
        
        Args:
            amount: Transaction amount
            email: Customer email
            reference: Unique transaction reference
            callback_url: URL to redirect after payment
            metadata: Additional transaction metadata
            currency: Currency code (default: GHS)
            **kwargs: Additional gateway-specific parameters
        
        Returns:
            Dict containing:
                - authorization_url: URL to redirect customer
                - access_code: Gateway access code
                - reference: Transaction reference
                - gateway_reference: Gateway's internal reference
                
        Raises:
            PaymentInitializationError: If initialization fails
        """
        pass
    
    @abstractmethod
    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """
        Verify a payment transaction
        
        Args:
            reference: Transaction reference to verify
        
        Returns:
            Dict containing:
                - status: Transaction status (success, failed, pending)
                - amount: Transaction amount
                - currency: Currency code
                - paid_at: Payment timestamp (if successful)
                - gateway_reference: Gateway's internal reference
                - customer: Customer details (email, name, etc.)
                - channel: Payment channel used
                - metadata: Transaction metadata
                - gateway_response: Full gateway response
                
        Raises:
            PaymentVerificationError: If verification fails
        """
        pass
    
    @abstractmethod
    def process_refund(
        self,
        transaction_reference: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a refund for a successful transaction
        
        Args:
            transaction_reference: Original transaction reference
            amount: Refund amount (None for full refund)
            reason: Reason for refund
            **kwargs: Additional gateway-specific parameters
        
        Returns:
            Dict containing:
                - status: Refund status (success, failed, pending)
                - refund_reference: Gateway refund reference
                - amount: Refunded amount
                - gateway_response: Full gateway response
                
        Raises:
            RefundError: If refund processing fails
        """
        pass
    
    @abstractmethod
    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Verify webhook signature to ensure authenticity
        
        Args:
            payload: Raw webhook payload
            signature: Signature from webhook headers
            headers: Full request headers
        
        Returns:
            bool: True if signature is valid, False otherwise
            
        Raises:
            WebhookVerificationError: If verification fails critically
        """
        pass
    
    @abstractmethod
    def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process webhook event from gateway
        
        Args:
            payload: Webhook payload
        
        Returns:
            Dict containing:
                - event_type: Type of event (charge.success, refund.completed, etc.)
                - reference: Transaction reference
                - status: Current transaction status
                - data: Event-specific data
                
        Raises:
            PaymentGatewayException: If webhook processing fails
        """
        pass
    
    def calculate_fee(self, amount: Decimal) -> Decimal:
        """
        Calculate gateway fee for a transaction
        
        Args:
            amount: Transaction amount
        
        Returns:
            Decimal: Gateway fee
        """
        return self.gateway.calculate_fee(amount)
    
    def get_supported_currencies(self) -> list:
        """
        Get list of supported currencies
        
        Returns:
            List of currency codes
        """
        return self.gateway.supported_currencies or []
    
    def get_supported_payment_methods(self) -> list:
        """
        Get list of supported payment methods
        
        Returns:
            List of payment method codes
        """
        return self.gateway.supported_methods or []
    
    def is_available(self) -> bool:
        """
        Check if gateway is available for use
        
        Returns:
            bool: True if gateway is active and operational
        """
        return (
            self.gateway.is_active and
            self.gateway.status == 'active'
        )
    
    @abstractmethod
    def get_transaction_status(self, reference: str) -> str:
        """
        Get current status of a transaction
        
        Args:
            reference: Transaction reference
        
        Returns:
            str: Transaction status (success, failed, pending, etc.)
        """
        pass
    
    def format_amount(self, amount: Decimal) -> int:
        """
        Format amount for gateway (usually convert to smallest currency unit)
        
        Most gateways require amounts in kobo/cents (e.g., GHS 10.00 = 1000 pesewas)
        
        Args:
            amount: Amount in main currency unit
        
        Returns:
            int: Amount in smallest currency unit
        """
        return int(amount * 100)
    
    def parse_amount(self, amount: int) -> Decimal:
        """
        Parse amount from gateway (convert from smallest currency unit)
        
        Args:
            amount: Amount in smallest currency unit
        
        Returns:
            Decimal: Amount in main currency unit
        """
        if amount is None:
            return Decimal('0.00')
        return Decimal(str(amount / 100))
