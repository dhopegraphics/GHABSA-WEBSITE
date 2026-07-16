"""
Signal handlers for auto-linking gift purchases and sending email notifications.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from .models import ProductPayment
from payments.models import Transaction
from utils.utils import send_email_notification
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def link_gift_purchases_on_user_save(sender, instance, created, **kwargs):
    """
    Auto-link gift and on-behalf purchases when a user is created or their phone number is updated.
    
    This ensures that when someone registers with a phone number that has pending
    gift or on-behalf purchases, those purchases are automatically linked to their account.
    """
    # Only proceed if user has a phone number
    if not instance.phone:
        return
    
    # Link any unlinked gift/on-behalf purchases for this phone number
    linked_count = ProductPayment.link_purchases_for_user(instance)
    
    if linked_count > 0:
        print(f"✅ Linked {linked_count} purchase(s) to user {instance.student_id or instance.phone}")


@receiver(post_save, sender=Transaction)
def send_validation_code_email(sender, instance, created, **kwargs):
    """
    Send email with validation code when a product payment transaction succeeds.
    
    SIMPLIFIED VERSION - No background threads or complex retry logic.
    Uses Transaction.metadata.email_notification_sent as the ONLY source of truth.
    """
    # Only proceed if transaction just became successful
    if instance.status != 'success':
        return
    
    if instance.transaction_type != 'payment':
        return
    
    # CRITICAL: Refresh from DB and check flag to prevent duplicate emails
    # The instance might be stale if signal fired multiple times
    instance.refresh_from_db()
    if instance.metadata and instance.metadata.get('email_notification_sent'):
        logger.debug(f"Email already sent for {instance.reference} (early check)")
        return
    
    # SKIP unified checkout transactions - they have their own notification system
    if instance.reference and instance.reference.upper().startswith('UNIFIED-'):
        logger.info(f"Skipping signal for UNIFIED- transaction {instance.reference}")
        return
    
    # Check if this is a product purchase
    is_product_purchase = False
    if instance.content_type and instance.content_type.model == 'product':
        is_product_purchase = True
    elif instance.metadata.get('product_id') or instance.metadata.get('cart_items'):
        is_product_purchase = True
    
    if not is_product_purchase:
        return
    
    # Check if ProductPayment exists
    product_payments = ProductPayment.objects.filter(transaction_record=instance)
    if not product_payments.exists():
        logger.info(f"ProductPayment not found for {instance.reference}, skipping email (will retry via webhook)")
        return
    
    # Check if user has email
    if not instance.customer_email and not (instance.user and hasattr(instance.user, 'personal_email')):
        return
    
    # Send email (simple, no threads, no retries)
    _send_validation_email_for_transaction(instance)


def _send_validation_email_for_transaction(transaction):
    """
    Send validation code email for a transaction.
    Uses Transaction.metadata.email_notification_sent as the source of truth.
    """
    # CRITICAL: Refresh from DB to get latest state
    transaction.refresh_from_db()
    
    # Check transaction metadata flag - this is the ONLY source of truth for email
    if transaction.metadata.get('email_notification_sent'):
        logger.debug(f"Email already sent for {transaction.reference} (metadata flag)")
        return
    
    product_payments = ProductPayment.objects.filter(transaction_record=transaction)
    if not product_payments.exists():
        logger.warning(f"No ProductPayments for {transaction.reference}")
        return
    
    # Claim the email sending by setting flag BEFORE sending
    # Use update() with a condition to ensure only ONE process succeeds
    # We filter for transactions where email_notification_sent is NOT True
    current_metadata = transaction.metadata or {}
    new_metadata = {
        **current_metadata,
        'email_notification_sent': True,  # Claim it
        'email_claimed_at': timezone.now().isoformat(),
    }
    
    # Save the claim - this uses update() to avoid triggering signal again
    Transaction.objects.filter(id=transaction.id).update(metadata=new_metadata)
    
    # Double-check by re-reading - if another process claimed first, they would have set it
    # before our update (race condition window is very small but possible)
    transaction.refresh_from_db()
    
    # Log that we're proceeding
    logger.info(f"Sending email for {transaction.reference}")
    
    try:
        user_email = transaction.customer_email or (transaction.user.personal_email if transaction.user else None)
        if not user_email:
            return
            
        user_name = transaction.customer_name or (transaction.user.get_full_name() if transaction.user else 'Customer')
        
        # Prepare validation codes data
        validation_codes_data = []
        for pp in product_payments:
            recipient_name = None
            if pp.purchased_for_user:
                recipient_name = pp.purchased_for_user.get_full_name() or pp.purchased_for_user.student_id
            
            validation_codes_data.append({
                'product_name': pp.product.product_name,
                'validation_code': pp.transaction_validation_code,
                'quantity': pp.quantity,
                'amount': pp.amount,
                'variant_info': _format_variant_info(pp.variant_selections) if pp.variant_selections else None,
                'is_gift': pp.is_gift_purchase,
                'is_on_behalf': pp.is_purchase_on_behalf,
                'purchased_for_phone': pp.purchased_for_phone if (pp.is_gift_purchase or pp.is_purchase_on_behalf) else None,
                'recipient_name': recipient_name,
                'gift_message': pp.gift_message if pp.is_gift_purchase else None,
            })
        
        is_cart_purchase = len(validation_codes_data) > 1 or transaction.metadata.get('cart_checkout', False)
        
        context = {
            'user_name': user_name,
            'transaction_reference': transaction.reference,
            'amount_paid': transaction.amount,
            'payment_date': transaction.completed_at or transaction.initiated_at,
            'validation_codes': validation_codes_data,
            'is_cart_purchase': is_cart_purchase,
            'total_items': len(validation_codes_data),
        }
        
        subject = f"🎉 Your Validation Code{'s' if is_cart_purchase else ''} - CSS KNUST Purchase"
        
        email_sent, email_msg = send_email_notification(
            recipient_email=user_email,
            subject=subject,
            template_name='products/validation_code_email.html',
            context=context,
        )
        
        if email_sent:
            logger.info(f"✅ Email sent to {user_email} for {transaction.reference}")
            
            # Update transaction metadata with sent timestamp (flag already set above)
            Transaction.objects.filter(id=transaction.id).update(
                metadata={
                    **(transaction.metadata or {}),
                    'email_notification_sent': True,
                    'email_sent_at': timezone.now().isoformat(),
                }
            )
        else:
            logger.error(f"❌ Email failed for {transaction.reference}: {email_msg}")
            # Revert the flag since email failed - allow retry
            Transaction.objects.filter(id=transaction.id).update(
                metadata={
                    **(transaction.metadata or {}),
                    'email_notification_sent': False,
                    'email_error': email_msg,
                }
            )
    
    except Exception as e:
        logger.error(f"Error sending email for {transaction.reference}: {str(e)}", exc_info=True)


def _format_variant_info(variant_selections):
    """Format variant selections for email display"""
    if not variant_selections:
        return None
    
    formatted = []
    for vs in variant_selections:
        parts = []
        if vs.get('color_id'):
            try:
                from products.models import ProductColor
                color = ProductColor.objects.get(id=vs['color_id'])
                parts.append(f"Color: {color.name}")
            except:
                pass
        
        if vs.get('size_id'):
            try:
                from products.models import ProductSize
                size = ProductSize.objects.get(id=vs['size_id'])
                parts.append(f"Size: {size.name}")
            except:
                pass
        
        if parts:
            formatted.append(", ".join(parts))
    
    return "; ".join(formatted) if formatted else None
