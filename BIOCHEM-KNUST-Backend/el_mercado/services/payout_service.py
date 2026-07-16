"""
El Mercado Payout Service
=========================

Handles seller payout operations including:
- Payout request creation and processing
- Bank account management
- Payout status tracking
- Bulk payout processing
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

from django.db import transaction as db_transaction
from django.utils import timezone

from payments.models import Transaction
from payments.services.paystack_gateway import PaystackGateway

from el_mercado.models import (
    Seller,
    SellerWallet,
    WalletTransaction,
    PayoutRequest,
    SellerPayoutAccount,
    MarketplaceSettings,
)

logger = logging.getLogger(__name__)


# =============================================================================
# EXCEPTIONS
# =============================================================================

class PayoutError(Exception):
    """Base exception for payout errors"""
    pass


class InsufficientBalanceError(PayoutError):
    """Error when balance is insufficient for payout"""
    pass


class InvalidBankAccountError(PayoutError):
    """Error when bank account is invalid"""
    pass


class PayoutProcessingError(PayoutError):
    """Error during payout processing"""
    pass


class PayoutLimitExceededError(PayoutError):
    """Error when payout limit is exceeded"""
    pass


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PayoutResult:
    """Result of a payout operation"""
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


# =============================================================================
# PAYOUT SERVICE
# =============================================================================

class PayoutService:
    """
    Service for handling seller payouts.
    
    Integrates with payment gateway for transfers and
    manages wallet balances accordingly.
    """
    
    # Maximum daily payout limit per seller
    MAX_DAILY_PAYOUT = Decimal('10000.00')
    
    @classmethod
    def get_settings(cls):
        """Get marketplace settings (cached per request)"""
        return MarketplaceSettings.get_settings()
    
    @classmethod
    def get_minimum_payout(cls) -> Decimal:
        """Get minimum payout amount from settings"""
        return cls.get_settings().minimum_payout_amount
    
    @classmethod
    def get_payout_fee_percentage(cls) -> Decimal:
        """Get payout processing fee percentage from settings"""
        return cls.get_settings().payout_processing_fee_percentage
    
    @classmethod
    def get_payout_transaction_fee(cls) -> Decimal:
        """Get flat payout transaction fee from settings"""
        return cls.get_settings().payout_transaction_fee
    
    # ==========================================================================
    # BANK ACCOUNT MANAGEMENT
    # ==========================================================================
    
    @classmethod
    def add_bank_account(
        cls,
        seller: Seller,
        bank_code: str,
        account_number: str,
        account_name: str = None,
    ) -> PayoutResult:
        """
        Add or update seller's bank account.
        
        Args:
            seller: Seller instance
            bank_code: Bank code (e.g., for Paystack)
            account_number: Bank account number
            account_name: Account holder name (optional, will be verified)
        
        Returns:
            PayoutResult
        """
        try:
            # Verify account with payment gateway
            gateway = PaystackGateway()
            verification = gateway.verify_bank_account(
                account_number=account_number,
                bank_code=bank_code,
            )
            
            if not verification.get('status'):
                return PayoutResult(
                    success=False,
                    message=verification.get('message', 'Account verification failed'),
                    error_code='ACCOUNT_VERIFICATION_FAILED'
                )
            
            verified_name = verification.get('data', {}).get('account_name', account_name)
            
            # Create transfer recipient with Paystack
            recipient_result = gateway.create_transfer_recipient(
                name=verified_name,
                account_number=account_number,
                bank_code=bank_code,
            )
            
            if not recipient_result.get('status'):
                return PayoutResult(
                    success=False,
                    message='Failed to register account for payouts',
                    error_code='RECIPIENT_CREATION_FAILED'
                )
            
            recipient_code = recipient_result.get('data', {}).get('recipient_code')
            
            # Update seller
            seller.bank_code = bank_code
            seller.bank_account_number = account_number
            seller.bank_account_name = verified_name
            seller.payout_recipient_code = recipient_code
            seller.bank_verified = True
            seller.save(update_fields=[
                'bank_code', 'bank_account_number', 'bank_account_name',
                'payout_recipient_code', 'bank_verified'
            ])
            
            logger.info(f"Bank account added for seller {seller.id}")
            
            return PayoutResult(
                success=True,
                message='Bank account added successfully',
                data={
                    'account_name': verified_name,
                    'account_number': account_number[-4:].rjust(len(account_number), '*'),
                    'bank_code': bank_code,
                }
            )
        
        except Exception as e:
            logger.error(f"Failed to add bank account: {str(e)}")
            return PayoutResult(
                success=False,
                message=f'Failed to add bank account: {str(e)}',
                error_code='BANK_ACCOUNT_ERROR'
            )
    
    @classmethod
    def get_bank_list(cls) -> PayoutResult:
        """
        Get list of supported banks.
        
        Returns:
            PayoutResult with list of banks
        """
        try:
            gateway = PaystackGateway()
            banks = gateway.get_banks(country='ghana')
            
            return PayoutResult(
                success=True,
                message='Banks retrieved successfully',
                data={'banks': banks}
            )
        
        except Exception as e:
            logger.error(f"Failed to get bank list: {str(e)}")
            return PayoutResult(
                success=False,
                message='Failed to retrieve bank list',
                error_code='BANK_LIST_ERROR'
            )
    
    # ==========================================================================
    # PAYOUT OPERATIONS
    # ==========================================================================
    
    @classmethod
    def calculate_payout_fee(cls, amount: Decimal) -> Decimal:
        """Calculate payout processing fee from settings."""
        fee_percentage = cls.get_payout_fee_percentage()
        percentage_fee = amount * (fee_percentage / 100)
        return percentage_fee.quantize(Decimal('0.01'))
    
    @classmethod
    def validate_payout_request(
        cls,
        seller: Seller,
        amount: Decimal,
    ) -> PayoutResult:
        """
        Validate a payout request before processing.
        
        Args:
            seller: Seller instance
            amount: Requested payout amount
        
        Returns:
            PayoutResult with validation status
        """
        # Check minimum amount
        minimum_payout = cls.get_minimum_payout()
        if amount < minimum_payout:
            return PayoutResult(
                success=False,
                message=f'Minimum payout amount is GHS {minimum_payout}',
                error_code='MINIMUM_NOT_MET'
            )
        
        # Check for verified payout account
        payout_account = SellerPayoutAccount.objects.filter(
            seller=seller,
            is_verified=True,
            is_default=True
        ).first()
        
        if not payout_account:
            # Try any verified account
            payout_account = SellerPayoutAccount.objects.filter(
                seller=seller,
                is_verified=True
            ).first()
        
        if not payout_account:
            return PayoutResult(
                success=False,
                message='Please add and verify your payout account first',
                error_code='ACCOUNT_NOT_VERIFIED'
            )
        
        # Check available balance
        try:
            wallet = seller.wallet
        except SellerWallet.DoesNotExist:
            return PayoutResult(
                success=False,
                message='Wallet not found',
                error_code='WALLET_NOT_FOUND'
            )
        
        if wallet.available_balance < amount:
            return PayoutResult(
                success=False,
                message=f'Insufficient balance. Available: GHS {wallet.available_balance}',
                error_code='INSUFFICIENT_BALANCE'
            )
        
        # Check daily limit
        daily_payouts = cls._get_daily_payout_total(wallet)
        if daily_payouts + amount > cls.MAX_DAILY_PAYOUT:
            remaining = cls.MAX_DAILY_PAYOUT - daily_payouts
            return PayoutResult(
                success=False,
                message=f'Daily payout limit exceeded. Remaining today: GHS {remaining}',
                error_code='DAILY_LIMIT_EXCEEDED'
            )
        
        # Check for pending payouts
        pending_payout = PayoutRequest.objects.filter(
            wallet=wallet,
            status__in=['PENDING', 'PROCESSING']
        ).exists()
        
        if pending_payout:
            return PayoutResult(
                success=False,
                message='You have a pending payout request. Please wait for it to complete.',
                error_code='PENDING_PAYOUT_EXISTS'
            )
        
        # Calculate fee
        fee = cls.calculate_payout_fee(amount)
        net_amount = amount - fee
        
        # Mask account number
        if payout_account.account_type == 'BANK':
            masked_account = payout_account.account_number[-4:].rjust(10, '*')
            account_name = payout_account.account_name
        else:
            masked_account = str(payout_account.mobile_money_number)[-4:].rjust(10, '*')
            account_name = payout_account.mobile_money_name
        
        return PayoutResult(
            success=True,
            message='Payout request is valid',
            data={
                'amount': str(amount),
                'fee': str(fee),
                'net_amount': str(net_amount),
                'available_balance': str(wallet.available_balance),
                'account': masked_account,
                'account_name': account_name,
                'account_type': payout_account.account_type,
            }
        )
    
    @classmethod
    def _get_daily_payout_total(cls, wallet: SellerWallet) -> Decimal:
        """Get total payout amount for today."""
        from datetime import datetime, time
        
        today_start = timezone.make_aware(
            datetime.combine(timezone.now().date(), time.min)
        )
        
        total = PayoutRequest.objects.filter(
            wallet=wallet,
            created_at__gte=today_start,
            status__in=['PENDING', 'PROCESSING', 'COMPLETED']
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        return total
    
    @classmethod
    @db_transaction.atomic
    def request_payout(
        cls,
        seller: Seller,
        amount: Decimal,
        payout_account_id: str = None,
        notes: str = '',
    ) -> PayoutResult:
        """
        Create a payout request.
        
        Args:
            seller: Seller instance
            amount: Payout amount
            payout_account_id: ID of payout account to use (optional, uses default)
            notes: Optional notes
        
        Returns:
            PayoutResult
        """
        # Validate first
        validation = cls.validate_payout_request(seller, amount)
        if not validation.success:
            return validation
        
        # Get payout account
        if payout_account_id:
            payout_account = SellerPayoutAccount.objects.filter(
                id=payout_account_id,
                seller=seller,
                is_verified=True
            ).first()
        else:
            payout_account = SellerPayoutAccount.objects.filter(
                seller=seller,
                is_verified=True,
                is_default=True
            ).first() or SellerPayoutAccount.objects.filter(
                seller=seller,
                is_verified=True
            ).first()
        
        if not payout_account:
            return PayoutResult(
                success=False,
                message='No verified payout account found',
                error_code='NO_PAYOUT_ACCOUNT'
            )
        
        fee = cls.calculate_payout_fee(amount)
        net_amount = amount - fee
        wallet = seller.wallet
        
        try:
            # Determine payout method and details
            if payout_account.account_type == 'BANK':
                payout_method = 'BANK_TRANSFER'
                bank_name = payout_account.bank_name
                bank_code = payout_account.bank_code
                account_number = payout_account.account_number
                account_name = payout_account.account_name
                mobile_money_provider = ''
                mobile_money_number = None
            else:
                payout_method = 'MOBILE_MONEY'
                bank_name = ''
                bank_code = ''
                account_number = ''
                account_name = payout_account.mobile_money_name
                mobile_money_provider = payout_account.mobile_money_provider
                mobile_money_number = payout_account.mobile_money_number
            
            # Create payout request
            payout = PayoutRequest.objects.create(
                wallet=wallet,
                amount=amount,
                payout_method=payout_method,
                bank_name=bank_name,
                bank_code=bank_code,
                account_number=account_number,
                account_name=account_name,
                mobile_money_provider=mobile_money_provider,
                mobile_money_number=mobile_money_number,
                status='PENDING',
            )
            
            # Deduct from wallet (hold)
            wallet.available_balance -= amount
            wallet.save(update_fields=['available_balance'])
            
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='PAYOUT_HOLD',
                amount=-amount,
                description=f"Payout request #{payout.reference} - On hold",
                balance_after=wallet.available_balance,
            )
            
            logger.info(f"Payout request created: {payout.reference}")
            
            return PayoutResult(
                success=True,
                message='Payout request submitted successfully',
                data={
                    'payout_reference': payout.reference,
                    'amount': str(amount),
                    'fee': str(fee),
                    'net_amount': str(net_amount),
                    'status': payout.status,
                    'estimated_completion': 'Within 24 hours',
                }
            )
        
        except Exception as e:
            logger.error(f"Failed to create payout request: {str(e)}")
            return PayoutResult(
                success=False,
                message='Failed to submit payout request',
                error_code='PAYOUT_REQUEST_FAILED'
            )
    
    @classmethod
    @db_transaction.atomic
    def process_payout(cls, payout: PayoutRequest) -> PayoutResult:
        """
        Process a pending payout request.
        
        Args:
            payout: PayoutRequest instance
        
        Returns:
            PayoutResult
        """
        if payout.status != 'PENDING':
            return PayoutResult(
                success=False,
                message=f'Payout is {payout.status.lower()}, cannot process',
                error_code='INVALID_PAYOUT_STATUS'
            )
        
        try:
            payout.status = 'PROCESSING'
            payout.processed_at = timezone.now()
            payout.save(update_fields=['status', 'processed_at'])
            
            # Initialize transfer with Paystack
            gateway = PaystackGateway()
            transfer_result = gateway.initiate_transfer(
                amount=int(payout.net_amount * 100),  # Convert to kobo
                recipient=payout.recipient_code,
                reason=f"El Mercado Payout - {payout.reference}",
                reference=payout.reference,
            )
            
            if not transfer_result.get('status'):
                # Transfer initiation failed
                payout.status = 'FAILED'
                payout.failure_reason = transfer_result.get('message', 'Transfer initiation failed')
                payout.save(update_fields=['status', 'failure_reason'])
                
                # Restore wallet balance
                cls._restore_wallet_balance(payout)
                
                return PayoutResult(
                    success=False,
                    message=payout.failure_reason,
                    error_code='TRANSFER_FAILED'
                )
            
            # Transfer initiated, update payout with transfer code
            payout.gateway_reference = transfer_result.get('data', {}).get('transfer_code')
            payout.save(update_fields=['gateway_reference'])
            
            logger.info(f"Transfer initiated for payout {payout.reference}")
            
            return PayoutResult(
                success=True,
                message='Payout is being processed',
                data={
                    'payout_reference': payout.reference,
                    'transfer_code': payout.gateway_reference,
                    'status': payout.status,
                }
            )
        
        except Exception as e:
            logger.error(f"Failed to process payout {payout.reference}: {str(e)}")
            payout.status = 'FAILED'
            payout.failure_reason = str(e)
            payout.save(update_fields=['status', 'failure_reason'])
            
            # Restore wallet balance
            cls._restore_wallet_balance(payout)
            
            return PayoutResult(
                success=False,
                message='Payout processing failed',
                error_code='PROCESSING_ERROR'
            )
    
    @classmethod
    @db_transaction.atomic
    def complete_payout(cls, payout: PayoutRequest) -> PayoutResult:
        """
        Mark a payout as completed (called by webhook).
        
        Args:
            payout: PayoutRequest instance
        
        Returns:
            PayoutResult
        """
        if payout.status != 'PROCESSING':
            return PayoutResult(
                success=False,
                message=f'Payout is {payout.status.lower()}, cannot complete',
                error_code='INVALID_PAYOUT_STATUS'
            )
        
        try:
            payout.status = 'COMPLETED'
            payout.completed_at = timezone.now()
            payout.save(update_fields=['status', 'completed_at'])
            
            # Update wallet stats
            wallet = payout.wallet
            wallet.total_withdrawn += payout.amount
            wallet.save(update_fields=['total_withdrawn'])
            
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='PAYOUT_COMPLETE',
                amount=-payout.amount,
                description=f"Payout completed #{payout.reference}",
                balance_after=wallet.available_balance,
            )
            
            logger.info(f"Payout completed: {payout.reference}")
            
            # Send notification
            cls._send_payout_notification(payout, 'completed')
            
            return PayoutResult(
                success=True,
                message='Payout completed successfully',
                data={
                    'payout_reference': payout.reference,
                    'amount': str(payout.amount),
                    'completed_at': payout.completed_at.isoformat(),
                }
            )
        
        except Exception as e:
            logger.error(f"Failed to complete payout {payout.reference}: {str(e)}")
            return PayoutResult(
                success=False,
                message='Failed to complete payout',
                error_code='COMPLETION_ERROR'
            )
    
    @classmethod
    @db_transaction.atomic
    def fail_payout(cls, payout: PayoutRequest, reason: str) -> PayoutResult:
        """
        Mark a payout as failed (called by webhook or admin).
        
        Args:
            payout: PayoutRequest instance
            reason: Failure reason
        
        Returns:
            PayoutResult
        """
        if payout.status not in ['PENDING', 'PROCESSING']:
            return PayoutResult(
                success=False,
                message=f'Payout is {payout.status.lower()}, cannot fail',
                error_code='INVALID_PAYOUT_STATUS'
            )
        
        try:
            payout.status = 'FAILED'
            payout.failure_reason = reason
            payout.save(update_fields=['status', 'failure_reason'])
            
            # Restore wallet balance
            cls._restore_wallet_balance(payout)
            
            logger.info(f"Payout failed: {payout.reference} - {reason}")
            
            # Send notification
            cls._send_payout_notification(payout, 'failed')
            
            return PayoutResult(
                success=True,
                message='Payout marked as failed',
                data={
                    'payout_reference': payout.reference,
                    'reason': reason,
                }
            )
        
        except Exception as e:
            logger.error(f"Failed to mark payout as failed: {str(e)}")
            return PayoutResult(
                success=False,
                message='Failed to update payout status',
                error_code='STATUS_UPDATE_ERROR'
            )
    
    @classmethod
    def _restore_wallet_balance(cls, payout: PayoutRequest):
        """Restore wallet balance after failed payout."""
        try:
            wallet = payout.wallet
            wallet.available_balance += payout.amount
            wallet.save(update_fields=['available_balance'])
            
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='PAYOUT_REFUND',
                amount=payout.amount,
                description=f"Payout failed #{payout.reference} - Refunded",
                balance_after=wallet.available_balance,
            )
        except Exception as e:
            logger.error(f"Failed to restore wallet balance: {str(e)}")
    
    @classmethod
    def _send_payout_notification(cls, payout: PayoutRequest, status: str):
        """Send payout notification to seller."""
        try:
            from notifications.utils import create_notification
            
            seller = payout.wallet.seller
            
            if status == 'completed':
                title = 'Payout Successful'
                message = f'Your payout of GHS {payout.amount} has been sent to your account.'
            else:
                title = 'Payout Failed'
                message = f'Your payout request of GHS {payout.amount} has failed. {payout.status_message}'
            
            if seller.user:
                create_notification(
                    user=seller.user,
                    notification_type=f'el_mercado_payout_{status}',
                    title=title,
                    message=message,
                    data={
                        'payout_reference': payout.reference,
                        'amount': str(payout.amount),
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to send payout notification: {str(e)}")
    
    # ==========================================================================
    # QUERY METHODS
    # ==========================================================================
    
    @classmethod
    def get_payout_history(
        cls,
        seller: Seller,
        status: str = None,
        limit: int = 20,
    ) -> PayoutResult:
        """
        Get seller's payout history.
        
        Args:
            seller: Seller instance
            status: Filter by status (optional)
            limit: Number of records to return
        
        Returns:
            PayoutResult with payout history
        """
        try:
            # Get wallet first
            try:
                wallet = seller.wallet
            except SellerWallet.DoesNotExist:
                return PayoutResult(
                    success=True,
                    message='No payout history',
                    data={'payouts': []}
                )
            
            payouts = PayoutRequest.objects.filter(wallet=wallet).order_by('-created_at')
            
            if status:
                payouts = payouts.filter(status=status)
            
            payouts = payouts[:limit]
            
            payout_list = []
            for p in payouts:
                # Determine masked account based on payout method
                if p.payout_method == 'BANK_TRANSFER':
                    masked_account = p.account_number[-4:].rjust(10, '*') if p.account_number else '****'
                else:
                    masked_account = str(p.mobile_money_number)[-4:].rjust(10, '*') if p.mobile_money_number else '****'
                
                payout_list.append({
                    'reference': p.reference,
                    'amount': str(p.amount),
                    'payout_method': p.payout_method,
                    'status': p.status,
                    'account': masked_account,
                    'account_name': p.account_name or p.mobile_money_provider,
                    'created_at': p.created_at.isoformat(),
                    'completed_at': p.completed_at.isoformat() if p.completed_at else None,
                    'status_message': p.status_message,
                })
            
            return PayoutResult(
                success=True,
                message=f'Found {len(payout_list)} payouts',
                data={'payouts': payout_list}
            )
        
        except Exception as e:
            logger.error(f"Failed to get payout history: {str(e)}")
            return PayoutResult(
                success=False,
                message='Failed to retrieve payout history',
                error_code='QUERY_ERROR'
            )
    
    @classmethod
    def get_payout_by_reference(cls, reference: str) -> PayoutResult:
        """
        Get a payout by reference.
        
        Args:
            reference: Payout reference
        
        Returns:
            PayoutResult with payout details
        """
        try:
            payout = PayoutRequest.objects.select_related('wallet__seller').get(reference=reference)
            
            # Determine masked account based on payout method
            if payout.payout_method == 'BANK_TRANSFER':
                masked_account = payout.account_number[-4:].rjust(10, '*') if payout.account_number else '****'
            else:
                masked_account = str(payout.mobile_money_number)[-4:].rjust(10, '*') if payout.mobile_money_number else '****'
            
            return PayoutResult(
                success=True,
                message='Payout found',
                data={
                    'reference': payout.reference,
                    'seller_id': str(payout.wallet.seller.id),
                    'amount': str(payout.amount),
                    'payout_method': payout.payout_method,
                    'status': payout.status,
                    'account': masked_account,
                    'account_name': payout.account_name,
                    'bank_name': payout.bank_name,
                    'bank_code': payout.bank_code,
                    'mobile_provider': payout.mobile_money_provider,
                    'created_at': payout.created_at.isoformat(),
                    'processed_at': payout.processed_at.isoformat() if payout.processed_at else None,
                    'completed_at': payout.completed_at.isoformat() if payout.completed_at else None,
                    'status_message': payout.status_message,
                    'gateway_reference': payout.gateway_reference,
                }
            )
        
        except PayoutRequest.DoesNotExist:
            return PayoutResult(
                success=False,
                message='Payout not found',
                error_code='PAYOUT_NOT_FOUND'
            )
        
        except Exception as e:
            logger.error(f"Failed to get payout: {str(e)}")
            return PayoutResult(
                success=False,
                message='Failed to retrieve payout',
                error_code='QUERY_ERROR'
            )
    
    # ==========================================================================
    # AUTO-PAYOUT PROCESSING
    # ==========================================================================
    
    @classmethod
    def process_auto_payouts(cls) -> PayoutResult:
        """
        Process automatic payouts for all eligible sellers.
        
        This should be run periodically (e.g., via Celery task or cron job).
        Checks each wallet with auto_payout_enabled and processes if threshold is met.
        
        Returns:
            PayoutResult with summary of processed payouts
        """
        processed = []
        failed = []
        skipped = []
        
        # Get all wallets with auto-payout enabled
        eligible_wallets = SellerWallet.objects.filter(
            auto_payout_enabled=True,
            available_balance__gte=models.F('auto_payout_threshold')
        ).select_related('seller')
        
        logger.info(f"Found {eligible_wallets.count()} wallets eligible for auto-payout")
        
        for wallet in eligible_wallets:
            try:
                # Check if seller has a default payout account
                payout_account = SellerPayoutAccount.objects.filter(
                    seller=wallet.seller,
                    is_default=True
                ).first()
                
                if not payout_account:
                    payout_account = SellerPayoutAccount.objects.filter(
                        seller=wallet.seller
                    ).first()
                
                if not payout_account:
                    skipped.append({
                        'seller': wallet.seller.display_name,
                        'reason': 'No payout account'
                    })
                    continue
                
                # Check for pending payouts
                has_pending = PayoutRequest.objects.filter(
                    wallet=wallet,
                    status__in=['PENDING', 'PROCESSING']
                ).exists()
                
                if has_pending:
                    skipped.append({
                        'seller': wallet.seller.display_name,
                        'reason': 'Has pending payout'
                    })
                    continue
                
                # Process auto-payout
                result = cls.process_single_auto_payout(wallet, payout_account)
                
                if result.success:
                    processed.append({
                        'seller': wallet.seller.display_name,
                        'amount': str(wallet.available_balance),
                        'reference': result.data.get('payout_reference') if result.data else None
                    })
                else:
                    failed.append({
                        'seller': wallet.seller.display_name,
                        'reason': result.message
                    })
                    
            except Exception as e:
                logger.error(f"Error processing auto-payout for wallet {wallet.id}: {str(e)}")
                failed.append({
                    'seller': wallet.seller.display_name,
                    'reason': str(e)
                })
        
        return PayoutResult(
            success=True,
            message=f'Processed {len(processed)} auto-payouts',
            data={
                'processed': processed,
                'failed': failed,
                'skipped': skipped,
                'total_processed': len(processed),
                'total_failed': len(failed),
                'total_skipped': len(skipped)
            }
        )
    
    @classmethod
    @db_transaction.atomic
    def process_single_auto_payout(
        cls,
        wallet: SellerWallet,
        payout_account: SellerPayoutAccount
    ) -> PayoutResult:
        """
        Process a single auto-payout for a wallet.
        
        First checks Paystack balance. If sufficient, processes instantly.
        Otherwise, queues for manual processing.
        
        Args:
            wallet: SellerWallet instance
            payout_account: SellerPayoutAccount to use
        
        Returns:
            PayoutResult
        """
        from payments.models import PaymentGateway
        
        amount = wallet.available_balance
        seller = wallet.seller
        
        logger.info(f"Processing auto-payout for {seller.display_name}: GH₵{amount}")
        
        # Create payout request
        if payout_account.account_type == 'BANK':
            payout_method = 'BANK_TRANSFER'
            bank_name = payout_account.bank_name
            bank_code = payout_account.bank_code
            account_number = payout_account.account_number
            account_name = payout_account.account_name
            mobile_money_provider = ''
            mobile_money_number = None
        else:
            payout_method = 'MOBILE_MONEY'
            bank_name = ''
            bank_code = ''
            account_number = ''
            account_name = payout_account.mobile_money_name or ''
            mobile_money_provider = payout_account.mobile_money_provider
            mobile_money_number = payout_account.mobile_money_number
        
        try:
            # Create the payout request
            payout = PayoutRequest.objects.create(
                wallet=wallet,
                amount=amount,
                payout_method=payout_method,
                bank_name=bank_name,
                bank_code=bank_code,
                account_number=account_number,
                account_name=account_name,
                mobile_money_provider=mobile_money_provider,
                mobile_money_number=mobile_money_number,
                status='PENDING',
                status_message='Auto-payout initiated'
            )
            
            # Deduct from wallet
            wallet.available_balance -= amount
            wallet.save(update_fields=['available_balance'])
            
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='WITHDRAWAL',
                amount=amount,
                description=f"Auto-payout #{payout.reference}",
                balance_after=wallet.available_balance
            )
            
            # Try to process via Paystack
            try:
                gateway_model = PaymentGateway.objects.filter(
                    code='paystack',
                    is_active=True
                ).first()
                
                if gateway_model:
                    gateway = PaystackGateway(gateway_model)
                    
                    # Check Paystack balance
                    balance_check = gateway.can_process_transfer(amount, 'GHS')
                    
                    if balance_check.get('can_transfer'):
                        # Create recipient if needed and process transfer
                        transfer_result = cls._process_paystack_transfer(
                            gateway, payout, payout_account
                        )
                        
                        if transfer_result.success:
                            payout.status = 'PROCESSING'
                            payout.status_message = 'Transfer initiated via Paystack'
                            payout.gateway_reference = transfer_result.data.get('transfer_code', '')
                            payout.processed_at = timezone.now()
                            payout.save()
                            
                            logger.info(f"Auto-payout {payout.reference} sent to Paystack")
                            
                            return PayoutResult(
                                success=True,
                                message='Auto-payout processed via Paystack',
                                data={
                                    'payout_reference': payout.reference,
                                    'amount': str(amount),
                                    'method': 'paystack_instant'
                                }
                            )
                    
                    # Insufficient Paystack balance - queue for manual processing
                    payout.status_message = (
                        f"Queued for manual processing. Paystack balance: GH₵{balance_check.get('available_balance', 0)}"
                    )
                    payout.save()
                    
                    logger.info(
                        f"Auto-payout {payout.reference} queued (insufficient Paystack balance)"
                    )
                    
                    # Send notification to seller
                    cls._send_payout_queued_notification(payout)
                    
                    return PayoutResult(
                        success=True,
                        message='Payout queued for manual processing within 24 hours',
                        data={
                            'payout_reference': payout.reference,
                            'amount': str(amount),
                            'method': 'manual_queue',
                            'reason': 'Insufficient Paystack balance for instant transfer'
                        }
                    )
                    
            except Exception as e:
                logger.warning(f"Paystack processing failed, queuing: {str(e)}")
                payout.status_message = f"Queued - Paystack error: {str(e)}"
                payout.save()
            
            # No gateway or error - queue for manual
            cls._send_payout_queued_notification(payout)
            
            return PayoutResult(
                success=True,
                message='Payout queued for manual processing within 24 hours',
                data={
                    'payout_reference': payout.reference,
                    'amount': str(amount),
                    'method': 'manual_queue'
                }
            )
            
        except Exception as e:
            logger.error(f"Auto-payout failed for {seller.display_name}: {str(e)}")
            return PayoutResult(
                success=False,
                message=str(e),
                error_code='AUTO_PAYOUT_FAILED'
            )
    
    @classmethod
    def _process_paystack_transfer(
        cls,
        gateway: 'PaystackGateway',
        payout: PayoutRequest,
        payout_account: SellerPayoutAccount
    ) -> PayoutResult:
        """
        Process a payout via Paystack transfer.
        
        Creates recipient if needed and initiates transfer.
        """
        try:
            # Determine recipient type and details
            if payout.payout_method == 'MOBILE_MONEY':
                recipient_type = 'mobile_money'
                # Map provider to Paystack bank code
                provider_codes = {
                    'MTN Mobile Money': 'MTN',
                    'MTN': 'MTN',
                    'Vodafone Cash': 'VOD',
                    'Vodafone': 'VOD',
                    'AirtelTigo Money': 'ATL',
                    'AirtelTigo': 'ATL',
                }
                bank_code = provider_codes.get(
                    payout.mobile_money_provider, 
                    payout.mobile_money_provider.upper()[:3]
                )
                account_number = str(payout.mobile_money_number).replace('+233', '0').replace('+', '')
                name = payout.account_name or payout_account.mobile_money_name or payout.wallet.seller.display_name
            else:
                recipient_type = 'ghipss'  # Ghana bank transfer
                bank_code = payout.bank_code
                account_number = payout.account_number
                name = payout.account_name or payout_account.account_name
            
            # Create transfer recipient
            recipient_result = gateway.create_transfer_recipient(
                recipient_type=recipient_type,
                name=name,
                account_number=account_number,
                bank_code=bank_code,
                currency='GHS',
                metadata={
                    'seller_id': str(payout.wallet.seller.id),
                    'payout_reference': payout.reference
                }
            )
            
            if not recipient_result.get('success'):
                return PayoutResult(
                    success=False,
                    message=recipient_result.get('message', 'Failed to create recipient'),
                    error_code='RECIPIENT_CREATION_FAILED'
                )
            
            recipient_code = recipient_result.get('recipient_code')
            
            # Generate transfer reference
            import secrets
            transfer_ref = f"em-po-{payout.reference.lower()}-{secrets.token_hex(4)}"
            
            # Initiate transfer
            transfer_result = gateway.initiate_transfer(
                amount=payout.amount,
                recipient_code=recipient_code,
                reference=transfer_ref,
                reason=f"El Mercado Payout - {payout.reference}",
                currency='GHS'
            )
            
            if not transfer_result.get('success'):
                return PayoutResult(
                    success=False,
                    message=transfer_result.get('message', 'Transfer failed'),
                    error_code='TRANSFER_FAILED'
                )
            
            return PayoutResult(
                success=True,
                message='Transfer initiated',
                data={
                    'transfer_code': transfer_result.get('transfer_code'),
                    'reference': transfer_result.get('reference'),
                    'status': transfer_result.get('status')
                }
            )
            
        except Exception as e:
            logger.error(f"Paystack transfer error: {str(e)}")
            return PayoutResult(
                success=False,
                message=str(e),
                error_code='PAYSTACK_ERROR'
            )
    
    @classmethod
    def _send_payout_queued_notification(cls, payout: PayoutRequest):
        """Send notification that payout is queued for manual processing."""
        try:
            from notifications.utils import create_notification
            
            seller = payout.wallet.seller
            
            if seller.user:
                create_notification(
                    user=seller.user,
                    notification_type='el_mercado_payout_queued',
                    title='Payout Request Received',
                    message=(
                        f'Your payout of GH₵{payout.amount} has been queued. '
                        'This will be processed within 24 hours.'
                    ),
                    data={
                        'payout_reference': payout.reference,
                        'amount': str(payout.amount),
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to send payout queued notification: {str(e)}")


# Import fix
from django.db import models