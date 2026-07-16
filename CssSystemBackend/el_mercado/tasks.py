"""
El Mercado Celery Tasks
=======================

Background tasks for the marketplace including:
- Auto-payout processing
- Order status updates
- Notification sending
"""

from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(name='el_mercado.process_auto_payouts')
def process_auto_payouts():
    """
    Process automatic payouts for all eligible sellers.
    
    This task should be scheduled to run periodically (e.g., every hour or daily).
    It checks all wallets with auto_payout_enabled and processes payouts
    for those that have reached their threshold.
    
    Usage in Django/Celery beat schedule:
        CELERY_BEAT_SCHEDULE = {
            'process-auto-payouts': {
                'task': 'el_mercado.process_auto_payouts',
                'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
            },
        }
    """
    from el_mercado.services.payout_service import PayoutService
    
    logger.info("Starting auto-payout processing...")
    
    try:
        result = PayoutService.process_auto_payouts()
        
        if result.success:
            data = result.data or {}
            logger.info(
                f"Auto-payout processing complete: "
                f"{data.get('total_processed', 0)} processed, "
                f"{data.get('total_failed', 0)} failed, "
                f"{data.get('total_skipped', 0)} skipped"
            )
            
            # Log details if any failed
            if data.get('failed'):
                for failure in data['failed']:
                    logger.warning(
                        f"Failed payout for {failure.get('seller')}: {failure.get('reason')}"
                    )
        else:
            logger.error(f"Auto-payout processing failed: {result.message}")
        
        return result.to_dict()
        
    except Exception as e:
        logger.exception(f"Auto-payout task error: {str(e)}")
        raise


@shared_task(name='el_mercado.process_pending_payout')
def process_pending_payout(payout_id: str):
    """
    Process a single pending payout request.
    
    Args:
        payout_id: UUID of the PayoutRequest to process
    """
    from el_mercado.models import PayoutRequest
    from el_mercado.services.payout_service import PayoutService
    
    logger.info(f"Processing payout {payout_id}...")
    
    try:
        payout = PayoutRequest.objects.get(id=payout_id)
        
        if payout.status != 'PENDING':
            logger.info(f"Payout {payout_id} is {payout.status}, skipping")
            return {'status': 'skipped', 'reason': f'Status is {payout.status}'}
        
        result = PayoutService.process_payout(payout)
        
        if result.success:
            logger.info(f"Payout {payout_id} processing initiated")
        else:
            logger.error(f"Payout {payout_id} failed: {result.message}")
        
        return result.to_dict()
        
    except PayoutRequest.DoesNotExist:
        logger.error(f"Payout {payout_id} not found")
        return {'status': 'error', 'message': 'Payout not found'}
    except Exception as e:
        logger.exception(f"Error processing payout {payout_id}: {str(e)}")
        raise


@shared_task(name='el_mercado.verify_transfer_status')
def verify_transfer_status(payout_id: str):
    """
    Verify the status of a Paystack transfer for a payout.
    
    Args:
        payout_id: UUID of the PayoutRequest to verify
    """
    from el_mercado.models import PayoutRequest
    from el_mercado.services.payout_service import PayoutService
    from payments.models import PaymentGateway
    from payments.services.paystack_gateway import PaystackGateway
    
    logger.info(f"Verifying transfer status for payout {payout_id}...")
    
    try:
        payout = PayoutRequest.objects.get(id=payout_id)
        
        if payout.status != 'PROCESSING' or not payout.gateway_reference:
            logger.info(f"Payout {payout_id} not in PROCESSING status or no gateway reference")
            return {'status': 'skipped'}
        
        # Get Paystack gateway
        gateway_model = PaymentGateway.objects.filter(
            code='paystack',
            is_active=True
        ).first()
        
        if not gateway_model:
            logger.error("Paystack gateway not configured")
            return {'status': 'error', 'message': 'Gateway not configured'}
        
        gateway = PaystackGateway(gateway_model)
        
        # Extract the transfer reference from gateway_reference
        # Format could be "TRF_xxx" or just the reference we sent
        transfer_ref = payout.gateway_reference
        if transfer_ref.startswith('TRF_'):
            # Need to use verify by transfer code, which might need different endpoint
            # For now, try with the reference we have
            pass
        
        # Verify transfer
        result = gateway.verify_transfer(transfer_ref)
        
        if result.get('success'):
            status = result.get('status', '').lower()
            
            if status == 'success':
                PayoutService.complete_payout(payout)
                logger.info(f"Payout {payout_id} completed successfully")
                return {'status': 'completed'}
                
            elif status in ['failed', 'reversed']:
                reason = f"Transfer {status}"
                PayoutService.fail_payout(payout, reason)
                logger.warning(f"Payout {payout_id} {status}")
                return {'status': status}
                
            else:
                # Still pending
                logger.info(f"Payout {payout_id} still processing (status: {status})")
                return {'status': 'pending'}
        else:
            logger.warning(f"Could not verify transfer for payout {payout_id}: {result.get('message')}")
            return {'status': 'unknown', 'message': result.get('message')}
            
    except PayoutRequest.DoesNotExist:
        logger.error(f"Payout {payout_id} not found")
        return {'status': 'error', 'message': 'Payout not found'}
    except Exception as e:
        logger.exception(f"Error verifying transfer {payout_id}: {str(e)}")
        raise


@shared_task(name='el_mercado.check_processing_payouts')
def check_processing_payouts():
    """
    Check all payouts in PROCESSING status and verify their transfer status.
    
    Should be run periodically (e.g., every 30 minutes).
    """
    from el_mercado.models import PayoutRequest
    from django.utils import timezone
    from datetime import timedelta
    
    logger.info("Checking processing payouts...")
    
    # Get payouts that have been processing for at least 5 minutes
    cutoff_time = timezone.now() - timedelta(minutes=5)
    
    processing_payouts = PayoutRequest.objects.filter(
        status='PROCESSING',
        processed_at__lte=cutoff_time
    )
    
    count = processing_payouts.count()
    logger.info(f"Found {count} payouts to verify")
    
    verified = 0
    for payout in processing_payouts:
        if payout.gateway_reference:
            verify_transfer_status.delay(str(payout.id))
            verified += 1
    
    return {'total': count, 'queued_for_verification': verified}


@shared_task(name='el_mercado.send_delivery_reminder')
def send_delivery_reminder(order_id: str):
    """
    Send a reminder to the buyer about confirming delivery.
    
    Args:
        order_id: UUID of the order
    """
    from el_mercado.models import MarketplaceOrder
    
    logger.info(f"Sending delivery reminder for order {order_id}")
    
    try:
        order = MarketplaceOrder.objects.get(id=order_id)
        
        if order.status != 'SHIPPED':
            logger.info(f"Order {order_id} is not shipped, skipping reminder")
            return {'status': 'skipped'}
        
        # Send notification to buyer
        try:
            from notifications.utils import create_notification
            
            create_notification(
                user=order.buyer,
                notification_type='el_mercado_delivery_reminder',
                title='Confirm Your Delivery',
                message=(
                    f'Your order {order.order_number} has been shipped. '
                    f'Please confirm delivery with the seller using your delivery code.'
                ),
                data={
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                }
            )
            logger.info(f"Delivery reminder sent for order {order_id}")
            return {'status': 'sent'}
            
        except Exception as e:
            logger.warning(f"Failed to send delivery reminder: {str(e)}")
            return {'status': 'error', 'message': str(e)}
        
    except MarketplaceOrder.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        return {'status': 'error', 'message': 'Order not found'}
