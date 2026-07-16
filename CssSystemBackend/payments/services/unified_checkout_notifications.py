"""
Unified Checkout Notification Service
======================================

Handles email notifications for unified checkout purchases,
including both merchandise validation codes and El Mercado orders.
"""

import logging
from typing import List, Dict, Any
from decimal import Decimal

from django.utils import timezone
from utils.utils import send_email_notification


logger = logging.getLogger(__name__)


class UnifiedCheckoutNotificationService:
    """Service for sending unified checkout email notifications"""
    
    @classmethod
    def send_purchase_confirmation_email(
        cls,
        transaction,
        merchandise_results: List[Dict[str, Any]],
        el_mercado_results: List[Dict[str, Any]],
    ) -> bool:
        """
        Send unified purchase confirmation email with both merchandise and El Mercado details.
        
        Args:
            transaction: Transaction instance
            merchandise_results: List of merchandise purchase results with validation codes
            el_mercado_results: List of El Mercado order results
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Get user email
            user_email = transaction.customer_email or (
                transaction.user.personal_email if transaction.user and hasattr(transaction.user, 'personal_email') else None
            )
            
            if not user_email:
                logger.warning(f"No email address found for transaction {transaction.reference}")
                return False
            
            user_name = transaction.customer_name or (
                transaction.user.get_full_name() if transaction.user else "Valued Customer"
            )
            
            # Prepare merchandise validation codes
            merchandise_items = []
            for result in merchandise_results:
                if result.get('status') == 'success':
                    merchandise_items.append({
                        'product_name': result.get('product_name'),
                        'quantity': result.get('quantity', 1),
                        'validation_code': result.get('validation_code'),
                        'is_gift': result.get('is_gift_purchase', False),
                        'is_on_behalf': result.get('is_purchase_on_behalf', False),
                        'purchased_for_phone': result.get('purchased_for_phone'),
                        'gift_message': result.get('gift_message'),
                    })
            
            # Prepare El Mercado orders
            el_mercado_orders = []
            for result in el_mercado_results:
                if result.get('status') == 'success':
                    el_mercado_orders.append({
                        'order_number': result.get('order_number'),
                        'seller_name': result.get('seller_name'),
                        'items': result.get('items', []),
                        'total_amount': result.get('total_amount'),
                        'expected_delivery': result.get('expected_delivery'),
                    })
            
            # Prepare email context
            has_merchandise = len(merchandise_items) > 0
            has_el_mercado = len(el_mercado_orders) > 0
            
            # Determine purchase type for contextual email
            if has_el_mercado and not has_merchandise:
                purchase_type = 'el_mercado_only'
                subject = "🛍️ Order Confirmed - El Mercado | CSS KNUST"
            elif has_merchandise and not has_el_mercado:
                purchase_type = 'merchandise_only'
                subject = "🎉 Purchase Confirmed - CSS KNUST Merchandise"
            else:
                purchase_type = 'mixed'
                subject = "🎉 Your Purchase Confirmation - CSS KNUST"
            
            context = {
                'user_name': user_name,
                'transaction_reference': transaction.reference,
                'amount_paid': transaction.amount,
                'payment_date': transaction.completed_at or transaction.initiated_at,
                'merchandise_items': merchandise_items,
                'el_mercado_orders': el_mercado_orders,
                'has_merchandise': has_merchandise,
                'has_el_mercado': has_el_mercado,
                'purchase_type': purchase_type,
            }
            
            email_sent, email_msg = send_email_notification(
                recipient_email=user_email,
                subject=subject,
                template_name='payments/unified_checkout_confirmation_email.html',
                context=context,
            )
            
            if email_sent:
                logger.info(f"✅ Unified checkout email ({purchase_type}) sent to {user_email} for transaction {transaction.reference}")
                return True
            else:
                logger.error(f"❌ Failed to send unified checkout email to {user_email}: {email_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending unified checkout email for {transaction.reference}: {str(e)}", exc_info=True)
            return False
