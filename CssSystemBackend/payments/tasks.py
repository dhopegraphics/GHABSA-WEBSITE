"""
Celery tasks for payment processing - DISABLED FOR PYTHONANYWHERE
Handles automatic retry of pending/failed transactions

NOTE: Celery does not work on PythonAnywhere free/hacker accounts.
Use Django management commands instead:
  - python manage.py retry_pending_transactions (every 5-10 min)
  - python manage.py cleanup_abandoned_transactions (daily)

Set up as scheduled tasks in PythonAnywhere dashboard.
"""
# from celery import shared_task  # DISABLED for PythonAnywhere
from django.utils import timezone
from django.db import transaction as db_transaction
from datetime import timedelta
from decimal import Decimal
import logging

from .models import Transaction
from .services.transaction_service import TransactionService
from products.payment_service import ProductPaymentService

logger = logging.getLogger(__name__)

# NOTE: All Celery @shared_task decorators have been disabled.
# Functions remain for reference but should not be called directly.


@shared_task(bind=True, max_retries=3)
def retry_pending_transaction(self, transaction_id):
    """
    Retry verification for a single pending transaction
    
    Args:
        transaction_id: UUID of the transaction to verify
    """
    try:
        transaction = Transaction.objects.select_for_update().get(id=transaction_id)
        
        # Only process if still pending
        if transaction.status != 'pending':
            logger.info(f"Transaction {transaction.reference} is no longer pending (status: {transaction.status})")
            return {
                'success': False,
                'message': f'Transaction status is {transaction.status}',
                'reference': transaction.reference
            }
        
        logger.info(f"Retrying verification for transaction {transaction.reference}")
        
        # Verify with payment gateway
        result = TransactionService.verify_payment(
            reference=transaction.reference,
            gateway_name=transaction.gateway.name
        )
        
        if result.get('status') == 'success':
            transaction_obj = result.get('transaction')
            
            # If it's a product payment, complete the product purchase
            if transaction_obj.transaction_type == 'payment':
                try:
                    # Complete the product payment (create ProductPayment, send notifications, etc.)
                    completion_result = ProductPaymentService.complete_product_payment(
                        transaction=transaction_obj,
                        reduce_stock=True,
                        send_notification=True
                    )
                    
                    logger.info(
                        f"✅ Successfully completed pending transaction {transaction.reference}. "
                        f"Validation codes: {completion_result.get('validation_codes', [])}"
                    )
                    
                    return {
                        'success': True,
                        'message': 'Transaction verified and completed successfully',
                        'reference': transaction.reference,
                        'validation_codes': completion_result.get('validation_codes', [])
                    }
                except Exception as e:
                    logger.error(f"Error completing product payment for {transaction.reference}: {str(e)}")
                    # Transaction was verified but product completion failed - may need manual intervention
                    return {
                        'success': False,
                        'message': f'Transaction verified but completion failed: {str(e)}',
                        'reference': transaction.reference,
                        'needs_manual_review': True
                    }
            else:
                logger.info(f"Transaction {transaction.reference} verified but is not a product payment")
                return {
                    'success': True,
                    'message': 'Transaction verified (non-product payment)',
                    'reference': transaction.reference
                }
        else:
            logger.warning(f"Transaction {transaction.reference} verification returned: {result.get('message')}")
            return {
                'success': False,
                'message': result.get('message', 'Verification failed'),
                'reference': transaction.reference
            }
            
    except Transaction.DoesNotExist:
        logger.error(f"Transaction {transaction_id} not found")
        return {
            'success': False,
            'message': 'Transaction not found'
        }
    except Exception as e:
        logger.error(f"Error retrying transaction {transaction_id}: {str(e)}")
        # Retry the task
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task
def check_and_retry_pending_transactions():
    """
    Periodic task to check all pending transactions and retry verification
    
    This task should be run every 5-10 minutes via Celery Beat
    
    Logic:
    - Find transactions that are pending for more than 5 minutes
    - Exclude transactions older than 24 hours (likely abandoned)
    - Retry verification for each transaction
    """
    now = timezone.now()
    min_age = now - timedelta(minutes=5)  # At least 5 minutes old
    max_age = now - timedelta(hours=24)   # Not older than 24 hours
    
    # Find pending transactions within the time window
    pending_transactions = Transaction.objects.filter(
        status='pending',
        initiated_at__gte=max_age,
        initiated_at__lte=min_age
    ).select_related('gateway', 'user')
    
    total_count = pending_transactions.count()
    
    if total_count == 0:
        logger.info("No pending transactions to retry")
        return {
            'checked': 0,
            'retried': 0,
            'message': 'No pending transactions found'
        }
    
    logger.info(f"Found {total_count} pending transactions to retry")
    
    retried_count = 0
    success_count = 0
    
    for transaction in pending_transactions:
        # Skip if already being processed (has recent verification attempts)
        if hasattr(transaction, 'last_verification_attempt'):
            last_attempt = transaction.last_verification_attempt
            if last_attempt and (now - last_attempt) < timedelta(minutes=2):
                logger.debug(f"Skipping {transaction.reference} - recently attempted")
                continue
        
        try:
            # Update last verification attempt timestamp (you may need to add this field)
            # transaction.last_verification_attempt = now
            # transaction.save(update_fields=['last_verification_attempt'])
            
            # Queue the retry task
            retry_pending_transaction.delay(str(transaction.id))
            retried_count += 1
            
        except Exception as e:
            logger.error(f"Error queuing retry for transaction {transaction.reference}: {str(e)}")
    
    logger.info(f"Queued {retried_count} transactions for retry verification")
    
    return {
        'checked': total_count,
        'retried': retried_count,
        'message': f'Queued {retried_count} of {total_count} pending transactions for retry'
    }


@shared_task
def cleanup_abandoned_transactions():
    """
    Mark very old pending transactions as failed/abandoned
    Run this daily to clean up abandoned transactions
    """
    cutoff_time = timezone.now() - timedelta(hours=48)
    
    abandoned_transactions = Transaction.objects.filter(
        status='pending',
        initiated_at__lt=cutoff_time
    )
    
    count = abandoned_transactions.count()
    
    if count > 0:
        abandoned_transactions.update(
            status='failed',
            failure_reason='Transaction abandoned - exceeded 48 hour timeout',
            completed_at=timezone.now()
        )
        logger.info(f"Marked {count} abandoned transactions as failed")
    
    return {
        'cleaned': count,
        'message': f'Marked {count} abandoned transactions as failed'
    }
