"""
El Mercado Signals
=================

Signal handlers for El Mercado models.

Notifications:
- New Order Alerts (Email) - Seller receives email when new order is placed
- Message Notifications (SMS) - Seller receives SMS when customer messages them
- Review Alerts (Email) - Seller receives email when they get a new review
- Low Stock Alerts (SMS) - Seller receives SMS when product stock is low
- Payout Updates (SMS) - Seller receives SMS about payout status changes

All notifications respect seller's notification preferences.
"""

import logging
import threading
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from el_mercado.models import MarketplaceOrder, Message, Review, Listing, PayoutRequest
from el_mercado.order_notifications import ElMercadoOrderNotificationService
from el_mercado.seller_notifications import SellerNotificationService


logger = logging.getLogger(__name__)


@receiver(pre_save, sender=MarketplaceOrder)
def track_order_status_change(sender, instance, **kwargs):
    """
    Track order status changes before save to enable status change email notifications.
    """
    if instance.pk:  # Only for existing orders
        try:
            old_order = MarketplaceOrder.objects.get(pk=instance.pk)
            instance._old_status = old_order.status
        except MarketplaceOrder.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=MarketplaceOrder)
def handle_order_post_save(sender, instance, created, **kwargs):
    """
    Handle order post-save actions:
    1. Auto-accept orders if seller has auto_accept_orders enabled
    2. Send status change email notifications
    """
    # Handle auto-accept for new paid orders
    if created and instance.status == 'PAID' and instance.payment_status == 'PAID':
        try:
            seller = instance.seller
            if seller.auto_accept_orders:
                # Auto-accept the order by changing status to PROCESSING
                # Use update() to avoid triggering this signal again
                MarketplaceOrder.objects.filter(pk=instance.pk).update(
                    status='PROCESSING',
                    status_history=instance.status_history + [{
                        'from_status': 'PAID',
                        'to_status': 'PROCESSING',
                        'changed_at': timezone.now().isoformat(),
                        'changed_by': 'system',
                        'notes': 'Auto-accepted by seller settings'
                    }]
                )
                
                # Add to seller's pending balance
                try:
                    if hasattr(seller, 'wallet'):
                        seller.wallet.add_pending(
                            instance.seller_earnings, 
                            f"Order {instance.order_number} (auto-accepted)"
                        )
                except Exception as e:
                    logger.warning(f"Failed to add to seller wallet for order {instance.order_number}: {e}")
                
                logger.info(f"Order {instance.order_number} auto-accepted for seller {seller.display_name}")
                
                # Refresh instance and send notification
                instance.refresh_from_db()
                try:
                    ElMercadoOrderNotificationService.send_status_change_email(
                        order=instance,
                        old_status='PAID',
                    )
                except Exception as e:
                    logger.error(f"Failed to send auto-accept email for {instance.order_number}: {e}")
                
                # Send new order notification to seller (in background)
                try:
                    _send_seller_new_order_notification_async(instance)
                except Exception as e:
                    logger.error(f"Failed to send seller notification for auto-accepted order {instance.order_number}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to auto-accept order {instance.order_number}: {str(e)}", exc_info=True)
        return  # Don't process status change email for auto-accepted orders (already sent above)
    
    # Send new order notification to seller for new PAID orders (non-auto-accept)
    if created and instance.status == 'PAID' and instance.payment_status == 'PAID':
        try:
            _send_seller_new_order_notification_async(instance)
        except Exception as e:
            logger.error(f"Failed to send seller notification for order {instance.order_number}: {e}")
    
    # Don't send buyer email on order creation (pending status is expected)
    if created:
        return
    
    # Check if status changed and send notification
    old_status = getattr(instance, '_old_status', None)
    
    if old_status and old_status != instance.status:
        logger.info(f"Order {instance.order_number} status changed from {old_status} to {instance.status}")
        
        # Send status change email to buyer
        try:
            ElMercadoOrderNotificationService.send_status_change_email(
                order=instance,
                old_status=old_status,
            )
        except Exception as e:
            logger.error(f"Failed to send order status email for {instance.order_number}: {str(e)}", exc_info=True)


def _send_seller_new_order_notification_async(order):
    """Send new order notification to seller in background thread"""
    def _send():
        try:
            SellerNotificationService.send_new_order_notification(order)
        except Exception as e:
            logger.error(f"Background new order notification failed for {order.order_number}: {e}")
    
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


# =============================================================================
# MESSAGE NOTIFICATION SIGNALS (SMS)
# =============================================================================

@receiver(post_save, sender=Message)
def handle_message_post_save(sender, instance, created, **kwargs):
    """
    Send SMS notification to seller when they receive a new message from a buyer.
    """
    if not created:
        return
    
    # Only notify for buyer messages
    if instance.sender_type != 'BUYER':
        return
    
    try:
        # Send notification in background to not slow down message sending
        _send_message_notification_async(instance)
    except Exception as e:
        logger.error(f"Failed to queue message notification: {str(e)}", exc_info=True)


def _send_message_notification_async(message):
    """Send message notification in background thread"""
    def _send():
        try:
            SellerNotificationService.send_message_notification(message)
        except Exception as e:
            logger.error(f"Background message notification failed: {e}")
    
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


# =============================================================================
# REVIEW NOTIFICATION SIGNALS (EMAIL)
# =============================================================================

@receiver(post_save, sender=Review)
def handle_review_post_save(sender, instance, created, **kwargs):
    """
    Send email notification to seller when they receive a new review.
    """
    if not created:
        return
    
    try:
        # Send notification in background
        _send_review_notification_async(instance)
    except Exception as e:
        logger.error(f"Failed to queue review notification: {str(e)}", exc_info=True)


def _send_review_notification_async(review):
    """Send review notification in background thread"""
    def _send():
        try:
            SellerNotificationService.send_review_notification(review)
        except Exception as e:
            logger.error(f"Background review notification failed: {e}")
    
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


# =============================================================================
# LOW STOCK NOTIFICATION SIGNALS (SMS)
# =============================================================================

@receiver(pre_save, sender=Listing)
def track_listing_stock_change(sender, instance, **kwargs):
    """
    Track stock changes before save to detect low stock conditions.
    """
    if instance.pk:
        try:
            old_listing = Listing.objects.get(pk=instance.pk)
            instance._old_stock = old_listing.stock_quantity
        except Listing.DoesNotExist:
            instance._old_stock = None
    else:
        instance._old_stock = None


@receiver(post_save, sender=Listing)
def handle_listing_stock_change(sender, instance, created, **kwargs):
    """
    Send SMS notification to seller when product stock falls below threshold.
    Only triggers when:
    - Stock crosses the low_stock_threshold (from above to at/below)
    - Stock becomes 0 (out of stock)
    - Track inventory is enabled
    """
    if created:
        return
    
    # Only check if inventory tracking is enabled
    if not instance.track_inventory:
        return
    
    old_stock = getattr(instance, '_old_stock', None)
    if old_stock is None:
        return
    
    current_stock = instance.stock_quantity
    threshold = instance.low_stock_threshold
    
    # Check if stock just crossed the threshold (from above to at/below)
    crossed_threshold = old_stock > threshold and current_stock <= threshold
    
    # Check if just went out of stock
    just_out_of_stock = old_stock > 0 and current_stock == 0
    
    if crossed_threshold or just_out_of_stock:
        try:
            _send_low_stock_notification_async(instance, current_stock)
        except Exception as e:
            logger.error(f"Failed to queue low stock notification for {instance.title}: {str(e)}", exc_info=True)


def _send_low_stock_notification_async(listing, current_stock):
    """Send low stock notification in background thread"""
    def _send():
        try:
            SellerNotificationService.send_low_stock_notification(listing, current_stock)
        except Exception as e:
            logger.error(f"Background low stock notification failed for {listing.title}: {e}")
    
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


# =============================================================================
# PAYOUT NOTIFICATION SIGNALS (SMS)
# =============================================================================

@receiver(pre_save, sender=PayoutRequest)
def track_payout_status_change(sender, instance, **kwargs):
    """
    Track payout status changes before save.
    """
    if instance.pk:
        try:
            old_payout = PayoutRequest.objects.get(pk=instance.pk)
            instance._old_payout_status = old_payout.status
        except PayoutRequest.DoesNotExist:
            instance._old_payout_status = None
    else:
        instance._old_payout_status = None


@receiver(post_save, sender=PayoutRequest)
def handle_payout_post_save(sender, instance, created, **kwargs):
    """
    Send SMS notification to seller about payout status updates.
    Send email notification to President when new payout is created.
    Triggers on:
    - New payout request created
    - Payout status changed
    """
    try:
        old_status = getattr(instance, '_old_payout_status', None)
        
        # DISABLED: Seller SMS notification for payout status
        # if created or (old_status and old_status != instance.status):
        #     _send_payout_notification_async(instance, old_status)
        
        # Send email to President ONLY for new payout requests
        if created:
            _send_payout_president_notification_async(instance)
            
    except Exception as e:
        logger.error(f"Failed to queue payout notification for {instance.reference}: {str(e)}", exc_info=True)


def _send_payout_notification_async(payout_request, old_status=None):
    """Send payout notification in background thread"""
    def _send():
        try:
            SellerNotificationService.send_payout_notification(payout_request, old_status)
        except Exception as e:
            logger.error(f"Background payout notification failed for {payout_request.reference}: {e}")
    
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


def _send_payout_president_notification_async(payout_request):
    """Send payout notification to President in background thread"""
    def _send():
        try:
            SellerNotificationService.send_payout_president_notification(payout_request)
        except Exception as e:
            logger.error(f"Background president payout notification failed for {payout_request.reference}: {e}")
    
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()

