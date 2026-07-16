"""
Refund Service
Handles refund processing and automatic reversals
"""
from typing import Optional
from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils import timezone
import uuid
import logging

from ..models import Refund, Transaction
from .transaction_service import TransactionService

logger = logging.getLogger(__name__)


class RefundService:
    """
    Service for managing refunds
    
    Features:
    - Process full and partial refunds
    - Automatic refunds on errors
    - Approval workflow
    - Gateway integration
    """
    
    @classmethod
    def generate_refund_reference(cls) -> str:
        """
        Generate unique refund reference
        
        Returns:
            Unique reference string
        """
        return f"RFD-{uuid.uuid4().hex[:16].upper()}"
    
    @classmethod
    @db_transaction.atomic
    def create_refund(
        cls,
        original_transaction: Transaction,
        amount: Decimal,
        reason: str,
        reason_details: str = '',
        initiated_by=None,
        requires_approval: bool = False,
        **kwargs
    ) -> Refund:
        """
        Create a refund request
        
        Args:
            original_transaction: Original transaction to refund
            amount: Amount to refund (can be partial)
            reason: Refund reason code
            reason_details: Detailed explanation
            initiated_by: User who initiated refund
            requires_approval: Whether refund needs approval
            **kwargs: Additional metadata
        
        Returns:
            Refund instance
        
        Raises:
            ValueError: If refund invalid
        """
        # Validate transaction
        if not original_transaction.can_be_refunded:
            raise ValueError("Transaction cannot be refunded")
        
        if amount > original_transaction.amount:
            raise ValueError("Refund amount cannot exceed transaction amount")
        
        if amount <= 0:
            raise ValueError("Refund amount must be positive")
        
        # Check if already fully refunded
        total_refunded = sum(
            r.amount for r in original_transaction.refunds.filter(status='success')
        )
        
        if total_refunded + amount > original_transaction.amount:
            raise ValueError(
                f"Total refund amount ({total_refunded + amount}) "
                f"would exceed transaction amount ({original_transaction.amount})"
            )
        
        # Generate reference
        reference = cls.generate_refund_reference()
        
        # Create refund
        refund = Refund.objects.create(
            reference=reference,
            original_transaction=original_transaction,
            amount=amount,
            reason=reason,
            reason_details=reason_details,
            initiated_by=initiated_by,
            requires_approval=requires_approval,
            status='pending',
            metadata=kwargs.get('metadata', {})
        )
        
        return refund
    
    @classmethod
    @db_transaction.atomic
    def process_refund(cls, refund: Refund) -> Refund:
        """
        Process a refund with the payment gateway
        
        Args:
            refund: Refund to process
        
        Returns:
            Updated Refund instance
        
        Raises:
            ValueError: If refund cannot be processed
        """
        # Check if already processed
        if refund.status in ['success', 'rejected']:
            raise ValueError(f"Refund already {refund.status}")
        
        # Check approval if required
        if refund.requires_approval and not refund.approved_by:
            raise ValueError("Refund requires approval before processing")
        
        original_transaction = refund.original_transaction
        
        # Check if transaction has gateway
        if not original_transaction.gateway:
            raise ValueError("Original transaction has no payment gateway")
        
        # Get gateway instance
        gateway = TransactionService.get_gateway_instance(
            original_transaction.gateway.name
        )
        
        try:
            # Update status to processing
            refund.status = 'processing'
            refund.processed_at = timezone.now()
            refund.save()
            
            # Process refund with gateway
            result = gateway.process_refund(
                transaction_reference=original_transaction.reference,
                amount=refund.amount,
                reason=refund.reason_details,
            )
            
            # Create refund transaction
            refund_transaction = TransactionService.create_transaction(
                user=original_transaction.user,
                amount=refund.amount,
                currency_code=original_transaction.currency.code,
                description=f"Refund for {original_transaction.reference}",
                transaction_type='refund',
                gateway_name=original_transaction.gateway.name,
                parent_transaction=original_transaction,
                reference=result.get('refund_reference', cls.generate_refund_reference()),
                status=result.get('status', 'pending'),
                gateway_response=str(result.get('gateway_response', {})),
            )
            
            # Update refund
            refund.refund_transaction = refund_transaction
            refund.gateway_reference = result.get('refund_reference')
            refund.gateway_response = str(result.get('gateway_response', {}))
            refund.status = result.get('status', 'pending')
            refund.completed_at = timezone.now() if refund.status == 'success' else None
            refund.save()
            
            # Update original transaction status
            if refund.status == 'success':
                total_refunded = sum(
                    r.amount for r in original_transaction.refunds.filter(status='success')
                )
                
                if total_refunded >= original_transaction.amount:
                    original_transaction.status = 'refunded'
                else:
                    original_transaction.status = 'partially_refunded'
                
                original_transaction.save()
            
            return refund
        
        except Exception as e:
            # Mark refund as failed
            refund.status = 'failed'
            refund.status_message = str(e)
            refund.save()
            raise
    
    @classmethod
    @db_transaction.atomic
    def approve_refund(cls, refund: Refund, approved_by) -> Refund:
        """
        Approve a refund request
        
        Args:
            refund: Refund to approve
            approved_by: User approving the refund
        
        Returns:
            Updated Refund instance
        """
        if not refund.requires_approval:
            raise ValueError("Refund does not require approval")
        
        if refund.approved_by:
            raise ValueError("Refund already approved")
        
        refund.approved_by = approved_by
        refund.approved_at = timezone.now()
        refund.save()
        
        return refund
    
    @classmethod
    @db_transaction.atomic
    def reject_refund(cls, refund: Refund, reason: str = '') -> Refund:
        """
        Reject a refund request
        
        Args:
            refund: Refund to reject
            reason: Rejection reason
        
        Returns:
            Updated Refund instance
        """
        refund.status = 'rejected'
        refund.status_message = reason
        refund.save()
        
        return refund
    
    @classmethod
    @db_transaction.atomic
    def auto_refund_on_error(
        cls,
        transaction: Transaction,
        error_message: str
    ) -> Optional[Refund]:
        """
        Automatically create and process refund when product creation fails
        
        This is the key feature requested: automatic refunds when payment
        succeeds but product/service creation fails.
        
        Args:
            transaction: Transaction to refund
            error_message: Error that occurred
        
        Returns:
            Refund instance if created, None otherwise
        """
        # Only refund successful payments
        if transaction.status != 'success':
            return None
        
        try:
            # Create refund
            refund = cls.create_refund(
                original_transaction=transaction,
                amount=transaction.amount,  # Full refund
                reason='error',
                reason_details=f"Automatic refund due to error: {error_message}",
                requires_approval=False,  # No approval needed for auto-refunds
            )
            
            # Process immediately
            refund = cls.process_refund(refund)
            
            return refund
        
        except Exception as e:
            # Log error but don't raise - we don't want to fail the entire flow
            # In production, you'd log this to monitoring system
            logger.error(f"Auto-refund failed: {str(e)}", exc_info=True)
            return None
    
    @classmethod
    def get_refund_by_reference(cls, reference: str) -> Optional[Refund]:
        """
        Get refund by reference
        
        Args:
            reference: Refund reference
        
        Returns:
            Refund instance or None
        """
        try:
            return Refund.objects.get(reference=reference)
        except Refund.DoesNotExist:
            return None
    
    @classmethod
    def get_transaction_refunds(cls, transaction: Transaction) -> list:
        """
        Get all refunds for a transaction
        
        Args:
            transaction: Transaction instance
        
        Returns:
            List of Refund instances
        """
        return list(transaction.refunds.all().order_by('-created_at'))
