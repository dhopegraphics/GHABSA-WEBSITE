"""
El Mercado Seller Notification Service
=====================================

Handles notifications to sellers for:
- New Order Alerts (Email)
- Message Notifications (SMS)
- Review Alerts (Email)
- Low Stock Alerts (SMS)
- Payout Updates (SMS)

All notifications respect seller's notification preferences.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple
from django.conf import settings

from utils.utils import send_email_notification, normalize_phone, notify_user


logger = logging.getLogger(__name__)


def get_seller_dashboard_url(path: str = '') -> str:
    """
    Get the full URL for the seller dashboard.
    Uses SITE_URL (backend) + seller dashboard path.
    """
    site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000').rstrip('/')
    base_path = '/seller-dashboard'
    if path:
        return f"{site_url}{base_path}/{path.lstrip('/')}"
    return f"{site_url}{base_path}/"


def get_frontend_url(path: str = '') -> str:
    """
    Get the full URL for the frontend.
    Uses FRONTEND_URL setting.
    """
    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://thecssknust.com').rstrip('/')
    if path:
        return f"{frontend_url}/{path.lstrip('/')}"
    return frontend_url


class SellerNotificationService:
    """
    Service for sending notifications to sellers.
    
    Notification Types & Methods:
    - New Orders: Email (detailed, includes order items)
    - Messages: SMS (short, urgent)
    - Reviews: Email (includes review content)
    - Low Stock: SMS (short, urgent)
    - Payouts: SMS (short, status updates)
    """
    
    # ==========================================================================
    # NEW ORDER NOTIFICATION (EMAIL)
    # ==========================================================================
    
    @classmethod
    def send_new_order_notification(cls, order) -> Tuple[bool, str]:
        """
        Send email notification to seller when they receive a new order.
        
        Args:
            order: MarketplaceOrder instance
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            seller = order.seller
            
            # Check if seller has this notification enabled
            if not seller.notify_new_orders:
                logger.info(f"New order notification disabled for seller {seller.display_name}")
                return (True, "Notification disabled by seller")
            
            # Get seller email
            seller_email = seller.email
            if not seller_email:
                logger.warning(f"No email for seller {seller.display_name}")
                return (False, "No seller email")
            
            # Prepare order items
            order_items = []
            for item in order.items.all():
                order_items.append({
                    'product_name': item.listing.title,
                    'variant_name': item.variant.name if item.variant else None,
                    'quantity': item.quantity,
                    'unit_price': str(item.unit_price),
                    'total_price': str(item.total_price),
                })
            
            # Prepare context
            context = {
                'seller_name': seller.display_name,
                'order_number': order.order_number,
                'buyer_name': order.buyer_name or 'Customer',
                'buyer_phone': str(order.buyer_phone) if order.buyer_phone else 'Not provided',
                'order_items': order_items,
                'subtotal': str(order.subtotal),
                'shipping_fee': str(order.shipping_fee),
                'total_amount': str(order.total_amount),
                'seller_earnings': str(order.seller_earnings),
                'delivery_method': order.get_delivery_method_display() if hasattr(order, 'get_delivery_method_display') else order.delivery_method,
                'shipping_address': cls._format_shipping_address(order),
                'order_notes': order.customer_notes or '',
                'order_date': order.created_at,
                'auto_accepted': seller.auto_accept_orders,
                # URLs
                'dashboard_url': get_seller_dashboard_url(),
                'orders_url': get_seller_dashboard_url('el_mercado/marketplaceorder/'),
                'frontend_url': get_frontend_url(),
                'year': datetime.now().year,
            }
            
            subject = f"🛒 New Order #{order.order_number} - GHS {order.total_amount}"
            
            success, message = send_email_notification(
                recipient_email=seller_email,
                subject=subject,
                template_name='el_mercado/emails/seller_new_order.html',
                context=context,
            )
            
            if success:
                logger.info(f"✅ New order email sent to seller {seller.display_name} for order {order.order_number}")
            else:
                logger.error(f"❌ Failed to send new order email to seller: {message}")
            
            return (success, message)
            
        except Exception as e:
            logger.error(f"Error sending new order notification: {str(e)}", exc_info=True)
            return (False, str(e))
    
    # ==========================================================================
    # MESSAGE NOTIFICATION (SMS)
    # ==========================================================================
    
    @classmethod
    def send_message_notification(cls, message) -> Tuple[bool, str]:
        """
        Send SMS notification to seller when they receive a customer message.
        
        Args:
            message: Message instance (from buyer)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            conversation = message.conversation
            seller = conversation.seller
            
            # Check if seller has this notification enabled
            if not seller.notify_messages:
                logger.info(f"Message notification disabled for seller {seller.display_name}")
                return (True, "Notification disabled by seller")
            
            # Only notify for buyer messages
            if message.sender_type != 'BUYER':
                return (True, "Not a buyer message")
            
            # Get seller phone
            seller_phone = str(seller.phone) if seller.phone else None
            if not seller_phone:
                logger.warning(f"No phone for seller {seller.display_name}")
                return (False, "No seller phone")
            
            # Normalize phone for SMS
            normalized_phone = normalize_phone(seller_phone)
            
            # Get buyer name
            buyer_name = conversation.buyer.first_name if conversation.buyer else 'Customer'
            
            # Truncate message preview (SMS should be short)
            content_preview = message.content[:50] + '...' if len(message.content) > 50 else message.content
            
            # Build SMS message (keep it short - under 160 chars)
            sms_message = f"New message from {buyer_name}: \"{content_preview}\" - El Mercado"
            
            # Ensure SMS is not too long
            if len(sms_message) > 160:
                sms_message = f"New message from {buyer_name} on El Mercado. Check your dashboard."
            
            success, result, _ = notify_user(normalized_phone, sms_message)
            
            if success:
                logger.info(f"✅ Message SMS sent to seller {seller.display_name}")
            else:
                logger.error(f"❌ Failed to send message SMS: {result}")
            
            return (success, result)
            
        except Exception as e:
            logger.error(f"Error sending message notification: {str(e)}", exc_info=True)
            return (False, str(e))
    
    # ==========================================================================
    # REVIEW NOTIFICATION (EMAIL)
    # ==========================================================================
    
    @classmethod
    def send_review_notification(cls, review) -> Tuple[bool, str]:
        """
        Send email notification to seller when they receive a new review.
        
        Args:
            review: Review instance
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Get seller (from listing or directly)
            seller = review.seller if review.seller else (review.listing.seller if review.listing else None)
            
            if not seller:
                logger.warning("No seller found for review")
                return (False, "No seller found")
            
            # Check if seller has this notification enabled
            if not seller.notify_reviews:
                logger.info(f"Review notification disabled for seller {seller.display_name}")
                return (True, "Notification disabled by seller")
            
            # Get seller email
            seller_email = seller.email
            if not seller_email:
                logger.warning(f"No email for seller {seller.display_name}")
                return (False, "No seller email")
            
            # Get reviewer name
            reviewer_name = review.reviewer.first_name if review.reviewer else 'Customer'
            
            # Get reviewed item name
            if review.listing:
                reviewed_item = review.listing.title
            else:
                reviewed_item = "Your Store"
            
            # Prepare context
            context = {
                'seller_name': seller.display_name,
                'reviewer_name': reviewer_name,
                'reviewed_item': reviewed_item,
                'rating': review.rating,
                'rating_stars': '★' * review.rating + '☆' * (5 - review.rating),
                'review_title': review.title or '',
                'review_content': review.content,
                'review_type': review.get_review_type_display(),
                'is_verified_purchase': review.is_verified_purchase,
                'review_date': review.created_at,
                # URLs
                'dashboard_url': get_seller_dashboard_url(),
                'reviews_url': get_seller_dashboard_url('el_mercado/review/'),
                'frontend_url': get_frontend_url(),
                'year': datetime.now().year,
            }
            
            # Subject based on rating
            if review.rating >= 4:
                emoji = '🌟'
            elif review.rating == 3:
                emoji = '⭐'
            else:
                emoji = '📝'
            
            subject = f"{emoji} New {review.rating}★ Review on {reviewed_item}"
            
            success, message = send_email_notification(
                recipient_email=seller_email,
                subject=subject,
                template_name='el_mercado/emails/seller_new_review.html',
                context=context,
            )
            
            if success:
                logger.info(f"✅ Review email sent to seller {seller.display_name}")
            else:
                logger.error(f"❌ Failed to send review email: {message}")
            
            return (success, message)
            
        except Exception as e:
            logger.error(f"Error sending review notification: {str(e)}", exc_info=True)
            return (False, str(e))
    
    # ==========================================================================
    # LOW STOCK NOTIFICATION (SMS)
    # ==========================================================================
    
    @classmethod
    def send_low_stock_notification(cls, listing, current_stock: int) -> Tuple[bool, str]:
        """
        Send SMS notification to seller when a product is running low on stock.
        
        Args:
            listing: Listing instance
            current_stock: Current stock quantity
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            seller = listing.seller
            
            # Check if seller has this notification enabled
            if not seller.notify_low_stock:
                logger.info(f"Low stock notification disabled for seller {seller.display_name}")
                return (True, "Notification disabled by seller")
            
            # Get seller phone
            seller_phone = str(seller.phone) if seller.phone else None
            if not seller_phone:
                logger.warning(f"No phone for seller {seller.display_name}")
                return (False, "No seller phone")
            
            # Normalize phone for SMS
            normalized_phone = normalize_phone(seller_phone)
            
            # Truncate product name for SMS
            product_name = listing.title[:30] + '...' if len(listing.title) > 30 else listing.title
            
            # Build SMS message (keep it short - under 160 chars)
            if current_stock == 0:
                sms_message = f"OUT OF STOCK: \"{product_name}\" - Restock now! - El Mercado"
            else:
                sms_message = f"LOW STOCK: \"{product_name}\" has {current_stock} left. Restock soon! - El Mercado"
            
            success, result, _ = notify_user(normalized_phone, sms_message)
            
            if success:
                logger.info(f"✅ Low stock SMS sent to seller {seller.display_name} for {listing.title}")
            else:
                logger.error(f"❌ Failed to send low stock SMS: {result}")
            
            return (success, result)
            
        except Exception as e:
            logger.error(f"Error sending low stock notification: {str(e)}", exc_info=True)
            return (False, str(e))
    
    # ==========================================================================
    # PAYOUT NOTIFICATION (SMS)
    # ==========================================================================
    
    @classmethod
    def send_payout_notification(cls, payout_request, old_status: Optional[str] = None) -> Tuple[bool, str]:
        """
        Send SMS notification to seller about payout status updates.
        
        Args:
            payout_request: PayoutRequest instance
            old_status: Previous status (optional)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            wallet = payout_request.wallet
            seller = wallet.seller
            
            # Check if seller has this notification enabled
            if not seller.notify_payouts:
                logger.info(f"Payout notification disabled for seller {seller.display_name}")
                return (True, "Notification disabled by seller")
            
            # Get seller phone
            seller_phone = str(seller.phone) if seller.phone else None
            if not seller_phone:
                logger.warning(f"No phone for seller {seller.display_name}")
                return (False, "No seller phone")
            
            # Normalize phone for SMS
            normalized_phone = normalize_phone(seller_phone)
            
            # Build SMS message based on status (keep it short)
            status = payout_request.status
            amount = payout_request.amount
            ref = payout_request.reference[-8:]  # Last 8 chars of reference
            
            status_messages = {
                'PENDING': f"Payout GHS{amount} received. Ref:{ref} - Processing soon. - El Mercado",
                'PROCESSING': f"Payout GHS{amount} processing. Ref:{ref} - Expect soon! - El Mercado",
                'COMPLETED': f"Payout GHS{amount} sent! Ref:{ref} - Check your account. - El Mercado",
                'FAILED': f"Payout GHS{amount} failed. Ref:{ref} - Contact support. - El Mercado",
                'CANCELLED': f"Payout GHS{amount} cancelled. Ref:{ref} - El Mercado",
            }
            
            sms_message = status_messages.get(
                status, 
                f"Payout update: GHS{amount} is now {status}. Ref:{ref} - El Mercado"
            )
            
            success, result, _ = notify_user(normalized_phone, sms_message)
            
            if success:
                logger.info(f"✅ Payout SMS sent to seller {seller.display_name} - Status: {status}")
            else:
                logger.error(f"❌ Failed to send payout SMS: {result}")
            
            return (success, result)
            
        except Exception as e:
            logger.error(f"Error sending payout notification: {str(e)}", exc_info=True)
            return (False, str(e))
    
    # ==========================================================================
    # PAYOUT PRESIDENT NOTIFICATION (EMAIL)
    # ==========================================================================
    
    @classmethod
    def send_payout_president_notification(cls, payout_request) -> Tuple[bool, str]:
        """
        Send email notification to the active President when a new payout is created.
        
        This notifies the President about the payout request so they can process
        the manual transfer to the seller.
        
        Args:
            payout_request: PayoutRequest instance (newly created)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            from executives.models import Executive
            from django.db.models import Q
            
            wallet = payout_request.wallet
            seller = wallet.seller
            
            # Get active President
            president = Executive.objects.filter(
                Q(position__name__icontains='president'),
                ~Q(position__name__icontains='vice'),  # Exclude Vice President
                is_active=True
            ).select_related('user', 'position').first()
            
            if not president:
                logger.warning("No active President found for payout notification")
                return (False, "No active President found")
            
            # Get president personal email
            president_email = president.user.personal_email
            if not president_email:
                logger.warning(f"No personal email for President {president.user.get_full_name()}")
                return (False, "No President personal email")
            
            # Calculate amounts
            request_amount = payout_request.amount
            processing_fee = payout_request.processing_fee
            net_amount = payout_request.net_amount
            
            # Get payout account details
            payout_account_info = cls._format_payout_account(payout_request)
            
            # Generate signed confirmation token (valid for 7 days)
            from django.core import signing
            confirmation_token = signing.dumps({'payout_id': str(payout_request.id)})
            
            # Build confirmation URL (frontend page)
            frontend_url = getattr(settings, 'FRONTEND_URL', 'https://thecssknust.com').rstrip('/')
            confirm_url = f"{frontend_url}/el-mercado/confirm-payout?token={confirmation_token}"
            
            # Prepare context
            context = {
                'president_name': president.user.first_name or president.user.get_full_name(),
                'seller_name': seller.display_name,
                'seller_phone': str(seller.phone) if seller.phone else 'Not provided',
                'seller_email': seller.email or 'Not provided',
                'payout_reference': payout_request.reference,
                'request_amount': str(request_amount),
                'processing_fee': str(processing_fee),
                'net_amount': str(net_amount),
                'payout_method': payout_request.get_payout_method_display(),
                'payout_account': payout_account_info,
                'created_at': payout_request.created_at,
                # URLs
                'admin_url': f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/executive-dashboard-cb/el_mercado/payoutrequest/{payout_request.id}/change/",
                'confirm_url': confirm_url,
                'year': datetime.now().year,
            }
            
            subject = f"El Mercado: Seller Withdrawal Request - GHS {net_amount}"
            
            success, message = send_email_notification(
                recipient_email=president_email,
                subject=subject,
                template_name='el_mercado/emails/president_payout_notification.html',
                context=context,
            )
            
            if success:
                logger.info(f"Payout notification email sent to President {president.user.get_full_name()} for payout {payout_request.reference}")
            else:
                logger.error(f"Failed to send payout email to President: {message}")
            
            return (success, message)
            
        except Exception as e:
            logger.error(f"Error sending payout president notification: {str(e)}", exc_info=True)
            return (False, str(e))
    
    @classmethod
    def _format_payout_account(cls, payout_request) -> dict:
        """Format payout account details for display"""
        if payout_request.payout_method == 'MOBILE_MONEY':
            return {
                'type': 'Mobile Money',
                'provider': payout_request.mobile_money_provider,
                'number': str(payout_request.mobile_money_number) if payout_request.mobile_money_number else 'N/A',
                'name': payout_request.account_name or 'N/A',
            }
        else:
            return {
                'type': 'Bank Transfer',
                'bank': payout_request.bank_name,
                'account_number': payout_request.account_number,
                'account_name': payout_request.account_name,
            }
    
    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================
    
    @classmethod
    def _format_shipping_address(cls, order) -> str:
        """Format shipping address for display"""
        if not order.shipping_address:
            return "Not provided"
        
        address = order.shipping_address
        parts = []
        
        if address.get('address_line_1'):
            parts.append(address['address_line_1'])
        if address.get('address_line_2'):
            parts.append(address['address_line_2'])
        if address.get('city'):
            parts.append(address['city'])
        if address.get('region'):
            parts.append(address['region'])
        
        return ', '.join(parts) if parts else "Not provided"
