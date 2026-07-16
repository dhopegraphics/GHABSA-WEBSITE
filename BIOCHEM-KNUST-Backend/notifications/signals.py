"""
Real-time Push Notification Signals
Triggers immediate push notifications when specific actions occur

Triggers:
- HelpDesk: When someone responds to a user's request
- Events: When a new event is created
- Payments: When a payment is successful
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='helpdesk.HelpDeskResponse')
def notify_helpdesk_response(sender, instance, created, **kwargs):
    """
    Send push notification when someone responds to a HelpDesk request
    Only notifies the request owner, not the responder themselves
    """
    if not created:
        return  # Only for new responses
    
    try:
        request = instance.request
        request_owner = request.author
        responder = instance.author
        
        # Don't notify if user is responding to their own request
        if request_owner.id == responder.id:
            logger.info(f"Skipping self-response notification for request {request.tracking_id}")
            return
        
        # Build detailed notification
        responder_name = f"{responder.first_name} {responder.last_name}"
        response_preview = instance.content[:100] + "..." if len(instance.content) > 100 else instance.content
        
        # Check if there are multiple new responses
        recent_responses = request.responses.filter(
            created_at__gte=timezone.now() - timedelta(minutes=5)
        ).exclude(author=request_owner).count()
        
        if recent_responses > 1:
            title = f"💬 {recent_responses} new responses"
            body = f"{responder_name} (latest): \"{response_preview}\""
        else:
            title = f"💬 {responder_name} responded"
            body = f"On '{request.title[:40]}': \"{response_preview}\""
        
        # Import here to avoid circular imports
        from notifications.services import NotificationService
        
        # Send push notification
        NotificationService.send_push_notification(
            user=request_owner,
            title=title,
            body=body,
            data={
                'type': 'helpdesk_response_added',
                'category': 'HelpDesk',
                'request_id': str(request.id),
                'tracking_id': request.tracking_id,
                'response_id': str(instance.id),
                'responder_name': responder_name,
            },
            sound='default',
            category='helpdesk_response',
        )
        
        logger.info(f"✅ Sent HelpDesk notification to {request_owner.phone} for request {request.tracking_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to send HelpDesk notification: {str(e)}", exc_info=True)


@receiver(post_save, sender='events.Event')
def notify_new_event(sender, instance, created, **kwargs):
    """
    Send push notification to ALL active users when a new event is created
    Uses background task to avoid blocking the event creation
    """
    if not created:
        return  # Only for new events
    
    try:
        from accounts.models import CustomUser
        from notifications.services import NotificationService
        
        # Build event notification
        event = instance
        
        # Get date and venue info
        date_str = event.event_date.strftime('%B %d, %Y at %I:%M %p') if event.event_date else 'Date TBA'
        venue_str = event.venue if event.venue else 'Venue TBA'
        
        # Event type emoji
        event_type_emoji = "🎤" if event.event_type == "talk" else "🎉" if event.event_type == "social" else "📚"
        
        title = f"{event_type_emoji} New Event: {event.event_name}"
        body = f"{event.event_type.title() if event.event_type else 'Event'} • 📅 {date_str} • 📍 {venue_str}"
        
        # Get all active users with valid push devices
        # Use push_devices relationship to filter users who have at least one active device
        active_users = CustomUser.objects.filter(
            is_active=True,
            push_devices__is_active=True,
            push_devices__device_token__isnull=False
        ).exclude(push_devices__device_token='').distinct()
        
        success_count = 0
        failed_count = 0
        
        # Send to all users (consider using celery for large user bases)
        for user in active_users:
            try:
                NotificationService.send_push_notification(
                    user=user,
                    title=title,
                    body=body,
                    data={
                        'type': 'event_created',
                        'category': 'Events',
                        'event_id': str(event.event_id),
                        'event_name': event.event_name,
                        'event_type': event.event_type,
                        'event_date': event.event_date.isoformat() if event.event_date else None,
                    },
                    sound='default',
                    category='event_created',
                )
                success_count += 1
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to send event notification to {user.phone}: {str(e)}")
        
        logger.info(f"✅ Sent new event notification to {success_count} users (failed: {failed_count})")
        
    except Exception as e:
        logger.error(f"❌ Failed to send new event notifications: {str(e)}", exc_info=True)


@receiver(post_save, sender='payments.Transaction')
def notify_payment_status(sender, instance, created, update_fields, **kwargs):
    """
    HYBRID APPROACH: Send push notification when payment status changes
    Acts as a SAFETY NET fallback if complete_product_payment() doesn't send notification
    
    Triggers on:
    - Payment success (only if notification not already sent)
    - Payment failed (always send failure notifications)
    
    IDEMPOTENCY: Checks transaction metadata to see if notification already sent
    by ProductPaymentService.complete_product_payment() and skips if so.
    This prevents duplicates while providing automatic fallback coverage.
    """
    # Skip if no user associated
    if not instance.user:
        return
    
    # Skip if this is not a payment transaction
    if instance.transaction_type != 'payment':
        return
    
    # SKIP unified checkout transactions - they have their own notification system
    if instance.reference and instance.reference.upper().startswith('UNIFIED-'):
        return
    
    try:
        from notifications.services import NotificationService
        
        transaction = instance
        user = transaction.user
        
        # Get product details
        product = transaction.content_object
        product_name = product.product_name if product and hasattr(product, 'product_name') else 'item'
        
        # Only send notification for specific status changes
        if transaction.status == 'success':
            # SUCCESS: Check if notification already sent by complete_product_payment
            notification_already_sent = False
            if transaction.metadata:
                notification_info = transaction.metadata.get('notification_sent', {})
                notification_already_sent = notification_info.get('push_sent', False)
            
            if notification_already_sent:
                logger.info(
                    f"⏭️  Skipping signal notification for {transaction.reference} - "
                    f"already sent by complete_product_payment()"
                )
                return
            
            # If we reach here, complete_product_payment didn't send notification
            # Check if ProductPayment exists - if not, we MUST create it
            from products.models import ProductPayment
            product_payment = ProductPayment.objects.filter(
                transaction_record=transaction
            ).first()
            
            # CRITICAL SAFETY NET: Create ProductPayment if it doesn't exist
            # This should NEVER happen, but we must ensure customer gets their validation code
            if not product_payment:
                logger.error(
                    f"🚨 CRITICAL: Transaction {transaction.reference} is SUCCESS but no ProductPayment exists! "
                    f"Attempting emergency recovery..."
                )
                try:
                    from products.payment_service import ProductPaymentService
                    completion_result = ProductPaymentService.complete_product_payment(
                        transaction=transaction,
                        reduce_stock=True,
                        send_notification=True,  # This will send notification
                    )
                    logger.info(f"✅ Emergency ProductPayment creation successful for {transaction.reference}")
                    # complete_product_payment already sent notification, so return early
                    return
                except Exception as e:
                    logger.error(f"❌ Emergency ProductPayment creation FAILED for {transaction.reference}: {e}", exc_info=True)
                    # Continue to send notification even without ProductPayment
            
            # Send fallback notification (this is the SAFETY NET)
            logger.warning(
                f"⚠️  Sending FALLBACK notification for {transaction.reference} via signal - "
                f"complete_product_payment() may not have been called"
            )
            
            # Get validation code from ProductPayment if available
            validation_code = None
            if product_payment:
                validation_code = product_payment.transaction_validation_code
            
            title = f"🎉 Purchase Successful!"
            if validation_code:
                body = f"Your {product_name} purchase is confirmed. Validation Code: {validation_code}"
            else:
                body = f"Your {product_name} purchase is confirmed. Check your purchases for details."
            
            NotificationService.send_push_notification(
                user=user,
                title=title,
                body=body,
                data={
                    'type': 'payment_success',
                    'category': 'Payments',
                    'transaction_id': str(transaction.id),
                    'reference': transaction.reference,
                    'amount': str(transaction.amount),
                    'product_name': product_name,
                    'validation_code': validation_code,
                    'screen': 'purchases',
                },
                sound='default',
                category='payment_success',
            )
            
            # Mark that we sent it
            if not transaction.metadata:
                transaction.metadata = {}
            transaction.metadata['notification_sent'] = {
                'push_sent': True,
                'sms_sent': False,
                'sent_at': timezone.now().isoformat(),
                'sent_by': 'signal_fallback',
            }
            transaction.save(update_fields=['metadata'])
            
            logger.info(f"✅ Sent FALLBACK payment success notification to {user.phone} for {transaction.reference}")
        
        elif transaction.status == 'failed':
            # FAILED: Always send failure notifications (they're less common and important)
            
            # Check if already sent to avoid spam
            if transaction.metadata and transaction.metadata.get('failure_notification_sent'):
                logger.info(f"⏭️  Skipping duplicate failure notification for {transaction.reference}")
                return
            
            title = f"❌ Payment Failed"
            reason = transaction.status_message or 'Payment could not be processed'
            body = f"Your {product_name} payment of GH₵{transaction.amount} failed. {reason[:50]}. Please try again."
            
            NotificationService.send_push_notification(
                user=user,
                title=title,
                body=body,
                data={
                    'type': 'payment_failed',
                    'category': 'Payments',
                    'transaction_id': str(transaction.id),
                    'reference': transaction.reference,
                    'amount': str(transaction.amount),
                    'reason': reason,
                    'product_name': product_name,
                },
                sound='default',
                category='payment_failed',
            )
            
            # Mark failure notification as sent
            if not transaction.metadata:
                transaction.metadata = {}
            transaction.metadata['failure_notification_sent'] = True
            transaction.save(update_fields=['metadata'])
            
            logger.info(f"✅ Sent payment failed notification to {user.phone} for {transaction.reference}")
        
    except Exception as e:
        logger.error(f"❌ Failed to send payment notification via signal: {str(e)}", exc_info=True)


# Optional: Signal for when merchandise is collected
@receiver(post_save, sender='payments.Transaction')
def notify_merchandise_collected(sender, instance, created, update_fields, **kwargs):
    """
    Send confirmation when user collects their merchandise
    Only triggers when merchandise_collected changes from False to True
    """
    if created:
        return  # Skip for new transactions
    
    # Check if merchandise_collected field exists and was updated
    if not hasattr(instance, 'merchandise_collected'):
        return
    
    # Only notify if status is success and merchandise was just collected
    if instance.status == 'success' and instance.merchandise_collected:
        # Check if this is a recent change (not a historical record)
        if update_fields and 'merchandise_collected' not in update_fields:
            return
        
        try:
            from notifications.services import NotificationService
            
            user = instance.user
            if not user:
                return
            
            product = instance.content_object
            product_name = product.product_name if product and hasattr(product, 'product_name') else 'item'
            
            title = f"✅ Collection Confirmed: {product_name}"
            body = f"Thank you for collecting your purchase! Enjoy your {product_name}."
            
            NotificationService.send_push_notification(
                user=user,
                title=title,
                body=body,
                data={
                    'type': 'payment_collected',
                    'category': 'Payments',
                    'transaction_id': str(instance.id),
                },
                sound='default',
                category='payment_collected',
            )
            
            logger.info(f"✅ Sent merchandise collection confirmation to {user.phone}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send collection confirmation: {str(e)}", exc_info=True)
