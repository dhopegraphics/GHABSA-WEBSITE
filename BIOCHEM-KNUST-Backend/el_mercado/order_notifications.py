"""
El Mercado Order Status Notification Service
============================================

Handles email notifications when El Mercado order status changes.
"""

import logging
from typing import Optional
from django.utils import timezone

from utils.utils import send_email_notification


logger = logging.getLogger(__name__)


class ElMercadoOrderNotificationService:
    """Service for sending El Mercado order status change emails"""
    
    # Status display mappings
    STATUS_DISPLAY = {
        'pending': {
            'label': 'Order Placed',
            'icon': '📋',
            'color': '#6c757d',
            'message': 'Your order has been received and is awaiting seller confirmation.',
        },
        'confirmed': {
            'label': 'Confirmed',
            'icon': '✅',
            'color': '#28a745',
            'message': 'The seller has confirmed your order and is preparing it for shipment.',
        },
        'processing': {
            'label': 'Processing',
            'icon': '⚙️',
            'color': '#17a2b8',
            'message': 'Your order is being prepared for shipment.',
        },
        'shipped': {
            'label': 'Shipped',
            'icon': '🚚',
            'color': '#007bff',
            'message': 'Your order is on its way! The seller will contact you with delivery details.',
        },
        'delivered': {
            'label': 'Delivered',
            'icon': '🎉',
            'color': '#28a745',
            'message': 'Your order has been delivered! Thank you for shopping with us.',
        },
        'cancelled': {
            'label': 'Cancelled',
            'icon': '❌',
            'color': '#dc3545',
            'message': 'This order has been cancelled. If you have questions, please contact the seller.',
        },
        'refunded': {
            'label': 'Refunded',
            'icon': '💰',
            'color': '#ffc107',
            'message': 'A refund has been initiated for this order. Funds will be returned to your account.',
        },
    }
    
    @classmethod
    def send_status_change_email(
        cls,
        order,
        old_status: Optional[str] = None,
    ) -> bool:
        """
        Send email notification when order status changes.
        
        Args:
            order: MarketplaceOrder instance
            old_status: Previous status (if any)
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Get buyer email
            buyer_email = None
            if order.buyer and hasattr(order.buyer, 'personal_email'):
                buyer_email = order.buyer.personal_email
            elif order.buyer_email:
                buyer_email = order.buyer_email
            
            if not buyer_email:
                logger.warning(f"No email address for order {order.order_number}")
                return False
            
            buyer_name = order.buyer_name or (
                order.buyer.get_full_name() if order.buyer else "Valued Customer"
            )
            
            # Get status information
            status_info = cls.STATUS_DISPLAY.get(order.status, {
                'label': order.status.title(),
                'icon': '📦',
                'color': '#6c757d',
                'message': f'Your order status has been updated to {order.status}.',
            })
            
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
            
            # Prepare email context
            context = {
                'buyer_name': buyer_name,
                'order_number': order.order_number,
                'status': order.status,
                'status_label': status_info['label'],
                'status_icon': status_info['icon'],
                'status_color': status_info['color'],
                'status_message': status_info['message'],
                'old_status': old_status,
                'seller_name': order.seller.display_name,
                'order_items': order_items,
                'subtotal': str(order.subtotal),
                'shipping_fee': str(order.shipping_fee),
                'total_amount': str(order.total_amount),
                'order_date': order.created_at,
                'updated_at': order.updated_at,
                'shipping_address': cls._format_shipping_address(order),
                'tracking_number': order.tracking_number,
                'estimated_delivery': order.estimated_delivery_date,
            }
            
            subject = f"{status_info['icon']} Order {status_info['label']} - #{order.order_number}"
            
            email_sent, email_msg = send_email_notification(
                recipient_email=buyer_email,
                subject=subject,
                template_name='el_mercado/order_status_change_email.html',
                context=context,
            )
            
            if email_sent:
                logger.info(f"✅ Status change email sent for order {order.order_number} to {buyer_email}")
                return True
            else:
                logger.error(f"❌ Failed to send status email for order {order.order_number}: {email_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending status change email for order {order.order_number}: {str(e)}", exc_info=True)
            return False
    
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
