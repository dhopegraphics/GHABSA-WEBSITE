"""
Unified Payment Webhook Handlers

This is the SINGLE webhook endpoint for ALL Paystack events across the entire system.
Configure this URL in Paystack Dashboard: https://yourdomain.com/payments/webhooks/paystack/

Payment Services Covered:
-------------------------
1. DONATIONS (DON-* prefix or metadata.type = 'donation')
   - charge.success → verify and complete donation
   - charge.failed → mark donation as failed

2. PRODUCTS/MERCHANDISE (TXN-* prefix, linked to Product content type)
   - charge.success → complete payment, reduce stock, send notifications
   - charge.failed → mark transaction as failed

3. UNIFIED CHECKOUT (UNIFIED-* prefix or metadata.unified_checkout = true)
   - charge.success → process mixed cart (Merchandise + El Mercado items)
   - Creates ProductPayment for merchandise, MarketplaceOrder for El Mercado
   - charge.failed → mark transaction as failed

4. VOTING PAYMENTS (TXN-* prefix, linked to VotingEvent content type)
   - charge.success → enable voting eligibility
   - charge.failed → mark transaction as failed

5. MENTORSHIP PAYMENTS (TXN-* prefix)
   - charge.success → complete mentor/mentee payment
   - charge.failed → mark transaction as failed

6. WALLET TOPUPS (WAL-* prefix or metadata.type = 'wallet_topup')
   - charge.success → credit user wallet
   - charge.failed → mark topup as failed

7. EL MERCADO ORDERS (ELM-* prefix or metadata.payment_type = 'el_mercado_order')
   - charge.success → verify payment, credit seller wallet
   - charge.failed → mark order as failed

8. DONATION WITHDRAWALS (gateway_transfer_code or WD-* reference)
   - transfer.success → complete withdrawal, update wallet
   - transfer.failed → mark withdrawal as failed, restore balance
   - transfer.reversed → handle reversed transfer

9. REFUNDS (gateway refund ID)
   - refund.processed → mark refund as completed
   - refund.failed → mark refund as failed

Reference Prefix Summary:
-------------------------
Cart Checkout (uses unified_checkout=True in metadata):
- ELM-*     → El Mercado only cart purchases
- TXN-*     → Merchandise only cart purchases  
- UNIFIED-* → Mixed cart purchases (El Mercado + Merchandise)

Other Payments:
- TXN-*     → Direct merchandise/products/voting/mentorship (no unified_checkout metadata)
- DON-*     → Donations
- WAL-*     → Wallet Top-ups
- WD-*      → Withdrawals
- REF-*     → Refunds

Webhook Events Handled:
- charge.success / charge.failed (payments, donations, wallet topups, unified checkout)
- transfer.success / transfer.failed / transfer.reversed (donation withdrawals)
- refund.processed / refund.failed (refunds)
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction as db_transaction
from django.utils import timezone
import hmac
import hashlib
import json
import logging
from django.conf import settings

from .models import PaymentWebhook, PaymentGateway, Transaction

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhookView(APIView):
    """
    Unified Paystack webhook handler for the entire system
    
    POST /payments/webhooks/paystack/
    
    This handles:
    1. Payment charges (products, merchandise, etc.)
    2. Donation payments
    3. Transfer events (donation withdrawals)
    4. Refunds
    
    Configure in Paystack Dashboard → Settings → API Keys & Webhooks
    """
    authentication_classes = []  # No authentication for webhooks
    permission_classes = []
    
    def post(self, request):
        """Process incoming Paystack webhook"""
        
        # Get signature from headers
        signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE', '')
        
        if not signature:
            logger.warning("Paystack webhook received without signature")
            return Response({'error': 'Missing signature'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get raw payload
        try:
            payload_str = request.body.decode('utf-8')
            payload = json.loads(payload_str)
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.error(f"Failed to decode webhook payload: {str(e)}")
            return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify signature using secret key directly
        secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        computed_signature = hmac.new(
            secret_key.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        if not hmac.compare_digest(computed_signature, signature):
            logger.warning(f"Invalid webhook signature for event: {payload.get('event')}")
            return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get or create Paystack gateway for recording
        gateway = None
        try:
            gateway = PaymentGateway.objects.get(name='paystack')
        except PaymentGateway.DoesNotExist:
            logger.warning("Paystack gateway not found in database, webhook will still be processed")
        
        # Store webhook record
        webhook = None
        if gateway:
            webhook = PaymentWebhook.objects.create(
                gateway=gateway,
                event_type=payload.get('event', 'unknown'),
                event_id=str(payload.get('data', {}).get('id', '')),
                payload=payload,
                headers=dict(request.headers),
                signature=signature,
                is_verified=True,
                status='pending'
            )
        
        # Process the webhook
        try:
            event_type = payload.get('event', '')
            data = payload.get('data', {})
            
            logger.info(f"Processing Paystack webhook: {event_type}")
            
            # Route to appropriate handler
            if event_type == 'charge.success':
                self._handle_charge_success(data, webhook)
            
            elif event_type == 'charge.failed':
                self._handle_charge_failed(data, webhook)
            
            elif event_type == 'transfer.success':
                self._handle_transfer_success(data, webhook)
            
            elif event_type == 'transfer.failed':
                self._handle_transfer_failed(data, webhook)
            
            elif event_type == 'transfer.reversed':
                self._handle_transfer_reversed(data, webhook)
            
            elif event_type == 'refund.processed':
                self._handle_refund_processed(data, webhook)
            
            elif event_type == 'refund.failed':
                self._handle_refund_failed(data, webhook)
            
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                if webhook:
                    webhook.status = 'ignored'
                    webhook.save()
            
            # Mark as processed
            if webhook and webhook.status == 'pending':
                webhook.status = 'processed'
                webhook.processed_at = timezone.now()
                webhook.save()
            
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Failed to process webhook: {str(e)}", exc_info=True)
            if webhook:
                webhook.status = 'failed'
                webhook.error_message = str(e)
                webhook.processing_attempts += 1
                webhook.save()
            
            # Return 200 to prevent Paystack from retrying immediately
            # We can retry failed webhooks manually
            return Response({'status': 'received'}, status=status.HTTP_200_OK)
    
    # ==========================================
    # CHARGE HANDLERS (Payments & Donations)
    # ==========================================
    
    def _handle_charge_success(self, data, webhook):
        """
        Handle successful charge event
        
        This processes:
        - Donations (DON- prefix or metadata.type = donation)
        - Regular payments (merchandise, products, voting, mentorship)
        - Wallet topups (WAL- prefix or metadata.type = wallet_topup)
        - El Mercado orders (metadata.payment_type = el_mercado_order)
        - Unified checkout (UNIFIED- prefix or metadata.unified_checkout = true)
        """
        reference = data.get('reference', '')
        metadata = data.get('metadata', {}) or {}
        payment_type = metadata.get('type', '')
        
        logger.info(f"Processing charge.success for: {reference} (type: {payment_type})")
        
        # Route based on payment type
        if payment_type == 'donation' or reference.startswith('DON-'):
            self._process_donation_charge(reference, data, webhook)
        elif payment_type == 'wallet_topup' or reference.startswith('WAL-'):
            self._process_wallet_topup(reference, data, webhook)
        elif payment_type == 'el_mercado_order' or metadata.get('payment_type') == 'el_mercado_order':
            self._process_el_mercado_charge(reference, data, webhook)
        elif metadata.get('unified_checkout') or reference.startswith('UNIFIED-'):
            # Unified checkout - handles cart purchases (ELM-*, TXN-*, UNIFIED-*)
            # Note: Cart checkouts use contextual prefixes but all have unified_checkout=True in metadata
            self._process_unified_checkout_charge(reference, data, webhook)
        else:
            # Regular payment - process through main transaction system
            # Handles: TXN-* (products, voting, mentorship, etc.)
            self._process_payment_charge(reference, data, webhook)
    
    def _handle_charge_failed(self, data, webhook):
        """Handle failed charge event"""
        reference = data.get('reference', '')
        metadata = data.get('metadata', {}) or {}
        payment_type = metadata.get('type', '')
        
        logger.info(f"Processing charge.failed for: {reference} (type: {payment_type})")
        
        # Route based on payment type
        if payment_type == 'donation' or reference.startswith('DON-'):
            self._process_donation_charge_failed(reference, data, webhook)
        elif payment_type == 'wallet_topup' or reference.startswith('WAL-'):
            self._process_wallet_topup_failed(reference, data, webhook)
        elif payment_type == 'el_mercado_order' or metadata.get('payment_type') == 'el_mercado_order':
            self._process_el_mercado_charge_failed(reference, data, webhook)
        elif metadata.get('unified_checkout') or reference.startswith('UNIFIED-'):
            # Unified checkout failed (handles ELM-*, TXN-*, UNIFIED-* from cart checkout)
            self._process_unified_checkout_charge_failed(reference, data, webhook)
        else:
            self._process_payment_charge_failed(reference, data, webhook)
    
    def _process_donation_charge(self, reference, data, webhook):
        """Process successful donation payment"""
        try:
            from donations.services import DonationService
            
            result = DonationService.verify_donation(reference)
            
            if result.get('success'):
                logger.info(f"Donation {reference} verified successfully via webhook")
            else:
                logger.warning(f"Donation verification failed: {result.get('error')}")
        except ImportError:
            logger.error("Donations app not available")
        except Exception as e:
            logger.error(f"Error processing donation charge: {str(e)}")
    
    def _process_donation_charge_failed(self, reference, data, webhook):
        """Process failed donation payment"""
        try:
            from donations.models import Donation
            
            donation = Donation.objects.filter(reference=reference).first()
            if donation and donation.status not in ['failed', 'completed']:
                donation.status = 'failed'
                donation.gateway_response = data
                donation.save()
                logger.info(f"Donation {reference} marked as failed via webhook")
        except ImportError:
            logger.error("Donations app not available")
        except Exception as e:
            logger.error(f"Error processing failed donation: {str(e)}")
    
    def _process_payment_charge(self, reference, data, webhook):
        """
        Process successful payment through main transaction system
        Enhanced with better error handling and automatic product payment completion
        """
        try:
            from .services.transaction_service import TransactionService
            from products.payment_service import ProductPaymentService
            
            transaction = TransactionService.get_transaction_by_reference(reference)
            
            if not transaction:
                logger.warning(f"Transaction not found for reference: {reference}")
                logger.warning(
                    f"⚠️ Transaction {reference} will be retried by scheduled task. "
                    f"Run: python manage.py retry_pending_transactions"
                )
                # Note: On PythonAnywhere, run retry_pending_transactions as scheduled task
                # instead of using Celery async queue
                return
            
            # Link webhook to transaction
            if webhook:
                webhook.transaction = transaction
                webhook.save()
            
            # Extract Paystack transaction ID and update gateway_reference
            # This is CRITICAL - Paystack's actual ID (shown as "Receipt Number" in dashboard)
            paystack_transaction_id = data.get('id')  # This is the actual Paystack transaction ID
            if paystack_transaction_id and not transaction.gateway_reference:
                transaction.gateway_reference = str(paystack_transaction_id)
                transaction.save(update_fields=['gateway_reference'])
                logger.info(f"Updated gateway_reference to Paystack transaction ID: {paystack_transaction_id}")
            
            # Update transaction if not already successful
            if transaction.status != 'success':
                TransactionService.complete_transaction(
                    transaction=transaction,
                    gateway_response=data
                )
                logger.info(f"Transaction {reference} marked as successful via webhook")
                
                # Handle product-specific post-payment actions
                if transaction.transaction_type == 'payment':
                    try:
                        # Complete the product payment (create ProductPayment, reduce stock, send notifications)
                        completion_result = ProductPaymentService.complete_product_payment(
                            transaction=transaction,
                            reduce_stock=True,
                            send_notification=True
                        )
                        logger.info(
                            f"✅ Product payment completed for {reference} via webhook. "
                            f"Validation codes: {completion_result.get('validation_codes', [])}"
                        )
                    except Exception as e:
                        logger.error(f"Error completing product payment via webhook for {reference}: {str(e)}")
                        logger.warning(
                            f"⚠️ Product payment completion failed for {reference}. "
                            f"Will be retried by scheduled task: python manage.py retry_pending_transactions"
                        )
                        # Note: Scheduled task will retry this transaction
            else:
                logger.info(f"Transaction {reference} already marked as successful")
        
        except Exception as e:
            logger.error(f"Error processing payment charge via webhook: {str(e)}", exc_info=True)
            logger.warning(
                f"⚠️ Webhook processing failed for {reference}. "
                f"Scheduled task will retry: python manage.py retry_pending_transactions"
            )
            raise
    
    def _process_payment_charge_failed(self, reference, data, webhook):
        """Process failed payment"""
        try:
            from .services.transaction_service import TransactionService
            
            transaction = TransactionService.get_transaction_by_reference(reference)
            
            if not transaction:
                logger.warning(f"Transaction not found for reference: {reference}")
                return
            
            # Link webhook to transaction
            if webhook:
                webhook.transaction = transaction
                webhook.save()
            
            # Update transaction if not already failed
            if transaction.status not in ['failed', 'cancelled']:
                TransactionService.fail_transaction(
                    transaction=transaction,
                    reason="Payment failed at gateway",
                    gateway_response=data
                )
                logger.info(f"Transaction {reference} marked as failed via webhook")
        
        except Exception as e:
            logger.error(f"Error processing failed payment: {str(e)}")
            raise
    
    def _process_wallet_topup(self, reference, data, webhook):
        """Process successful wallet topup"""
        try:
            from .models import Transaction, WalletTransaction, Wallet
            from .services.transaction_service import TransactionService
            from decimal import Decimal
            
            transaction = TransactionService.get_transaction_by_reference(reference)
            
            if not transaction:
                logger.warning(f"Wallet topup transaction not found: {reference}")
                return
            
            # Link webhook to transaction
            if webhook:
                webhook.transaction = transaction
                webhook.save()
            
            if transaction.status != 'success':
                TransactionService.complete_transaction(
                    transaction=transaction,
                    gateway_response=data
                )
                
                # Credit the wallet
                if transaction.user:
                    # Get or create wallet
                    wallet, created = Wallet.objects.get_or_create(
                        user=transaction.user,
                        defaults={'currency_id': 'GHS', 'balance': Decimal('0.00')}
                    )
                    
                    balance_before = wallet.balance
                    wallet.credit(transaction.amount)
                    balance_after = wallet.balance
                    
                    # Create wallet transaction record
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='credit',
                        amount=transaction.amount,
                        balance_before=balance_before,
                        balance_after=balance_after,
                        reference=reference,
                        description=f"Wallet topup via {data.get('channel', 'paystack')}",
                        related_transaction=transaction
                    )
                    logger.info(f"Wallet credited {transaction.amount} for user {transaction.user.id}")
                
                logger.info(f"Wallet topup {reference} completed via webhook")
        
        except Exception as e:
            logger.error(f"Error processing wallet topup: {str(e)}")
    
    def _process_wallet_topup_failed(self, reference, data, webhook):
        """Process failed wallet topup"""
        try:
            from .services.transaction_service import TransactionService
            
            transaction = TransactionService.get_transaction_by_reference(reference)
            
            if not transaction:
                logger.warning(f"Wallet topup transaction not found: {reference}")
                return
            
            if webhook:
                webhook.transaction = transaction
                webhook.save()
            
            if transaction.status not in ['failed', 'cancelled']:
                TransactionService.fail_transaction(
                    transaction=transaction,
                    reason="Wallet topup failed at gateway",
                    gateway_response=data
                )
                logger.info(f"Wallet topup {reference} marked as failed via webhook")
        
        except Exception as e:
            logger.error(f"Error processing failed wallet topup: {str(e)}")
    
    # ==========================================
    # EL MERCADO HANDLERS
    # ==========================================
    
    def _process_el_mercado_charge(self, reference, data, webhook):
        """
        Process successful El Mercado marketplace order payment.
        
        This handles:
        - Verifying payment through ElMercadoPaymentService
        - Updating order status
        - Crediting seller wallet (escrow)
        - Reducing stock
        - Sending notifications
        """
        try:
            from el_mercado.services import ElMercadoPaymentService
            
            logger.info(f"Processing El Mercado payment for reference: {reference}")
            
            # Verify payment through El Mercado payment service
            result = ElMercadoPaymentService.verify_payment(reference)
            
            if result.success:
                logger.info(
                    f"✅ El Mercado order payment verified successfully: "
                    f"Order #{result.data.get('order_number')}"
                )
            else:
                logger.warning(
                    f"El Mercado payment verification issue: {result.message}"
                )
            
            # Link webhook to transaction if exists
            if webhook:
                from .models import Transaction
                transaction = Transaction.objects.filter(reference=reference).first()
                if transaction:
                    webhook.transaction = transaction
                    webhook.save()
        
        except ImportError:
            logger.error("El Mercado app not available")
        except Exception as e:
            logger.error(f"Error processing El Mercado charge: {str(e)}", exc_info=True)
    
    def _process_el_mercado_charge_failed(self, reference, data, webhook):
        """Process failed El Mercado payment"""
        try:
            from el_mercado.models import MarketplaceOrder
            
            order = MarketplaceOrder.objects.filter(payment_reference=reference).first()
            
            if order and order.payment_status not in ['FAILED', 'PAID']:
                order.payment_status = 'FAILED'
                order.save()
                order.update_status('PENDING', 'Payment failed at gateway')
                logger.info(f"El Mercado order {order.order_number} marked as payment failed")
                
            # Link webhook to transaction
            if webhook:
                from .models import Transaction
                transaction = Transaction.objects.filter(reference=reference).first()
                if transaction:
                    webhook.transaction = transaction
                    webhook.save()
        
        except ImportError:
            logger.error("El Mercado app not available")
        except Exception as e:
            logger.error(f"Error processing failed El Mercado charge: {str(e)}")

    # ==========================================
    # UNIFIED CHECKOUT HANDLERS
    # ==========================================
    
    def _process_unified_checkout_charge(self, reference, data, webhook):
        """
        Process successful unified checkout payment.
        
        This handles mixed carts containing items from both:
        - Merchandise (products app)
        - El Mercado (marketplace listings)
        
        The UnifiedCheckoutService.complete_checkout() method:
        - Creates ProductPayment records for merchandise items
        - Creates MarketplaceOrder records for El Mercado items
        - Reduces stock for both
        - Generates validation codes
        - Sends notifications
        """
        try:
            from .services.transaction_service import TransactionService
            from .services.unified_checkout_service import UnifiedCheckoutService
            
            logger.info(f"Processing unified checkout payment for reference: {reference}")
            
            transaction = TransactionService.get_transaction_by_reference(reference)
            
            if not transaction:
                logger.warning(f"Unified checkout transaction not found: {reference}")
                return
            
            # Link webhook to transaction
            if webhook:
                webhook.transaction = transaction
                webhook.save()
            
            # Extract Paystack transaction ID
            paystack_transaction_id = data.get('id')
            if paystack_transaction_id and not transaction.gateway_reference:
                transaction.gateway_reference = str(paystack_transaction_id)
                transaction.save(update_fields=['gateway_reference'])
            
            # Update transaction status if not already successful
            if transaction.status != 'success':
                TransactionService.complete_transaction(
                    transaction=transaction,
                    gateway_response=data
                )
                logger.info(f"Unified checkout transaction {reference} marked as successful")
                
                # Complete the unified checkout (process both merchandise and el_mercado items)
                try:
                    completion_result = UnifiedCheckoutService.complete_checkout(
                        transaction=transaction,
                        gateway_response=data,
                    )
                    
                    merch_count = len(completion_result.get('merchandise_results', []))
                    em_count = len(completion_result.get('el_mercado_results', []))
                    validation_codes = completion_result.get('validation_codes', [])
                    errors = completion_result.get('errors', [])
                    
                    logger.info(
                        f"✅ Unified checkout completed for {reference}: "
                        f"Merchandise items: {merch_count}, El Mercado orders: {em_count}, "
                        f"Validation codes: {len(validation_codes)}"
                    )
                    
                    if errors:
                        logger.warning(
                            f"⚠️ Unified checkout had some errors for {reference}: {errors}"
                        )
                        transaction.requires_manual_review = True
                        transaction.save(update_fields=['requires_manual_review'])
                        
                except Exception as e:
                    logger.error(
                        f"Error completing unified checkout for {reference}: {str(e)}",
                        exc_info=True
                    )
                    transaction.requires_manual_review = True
                    transaction.save(update_fields=['requires_manual_review'])
            else:
                logger.info(f"Unified checkout {reference} already marked as successful")
        
        except Exception as e:
            logger.error(f"Error processing unified checkout charge: {str(e)}", exc_info=True)
    
    def _process_unified_checkout_charge_failed(self, reference, data, webhook):
        """Process failed unified checkout payment"""
        try:
            from .services.transaction_service import TransactionService
            
            logger.info(f"Processing failed unified checkout for reference: {reference}")
            
            transaction = TransactionService.get_transaction_by_reference(reference)
            
            if not transaction:
                logger.warning(f"Unified checkout transaction not found: {reference}")
                return
            
            # Link webhook to transaction
            if webhook:
                webhook.transaction = transaction
                webhook.save()
            
            if transaction.status not in ['failed', 'cancelled']:
                TransactionService.fail_transaction(
                    transaction=transaction,
                    reason="Unified checkout payment failed at gateway",
                    gateway_response=data
                )
                logger.info(f"Unified checkout {reference} marked as failed via webhook")
        
        except Exception as e:
            logger.error(f"Error processing failed unified checkout: {str(e)}")

    def _handle_product_payment_completion(self, transaction):
        """Handle product payment completion after successful charge"""
        try:
            from products.payment_service import ProductPaymentService
            from products.models import Product
            from django.contrib.contenttypes.models import ContentType
            
            # Check if this is a product payment
            if transaction.content_type:
                product_content_type = ContentType.objects.get_for_model(Product)
                
                if transaction.content_type == product_content_type:
                    logger.info(f"Processing product payment completion for {transaction.reference}")
                    
                    ProductPaymentService.complete_product_payment(
                        transaction=transaction,
                        reduce_stock=True,
                        send_notification=True,
                    )
                    
                    logger.info(f"Product payment completed for {transaction.reference}")
        except ImportError:
            logger.warning("Products app not available for payment completion")
        except Exception as e:
            logger.error(f"Failed to complete product payment for {transaction.reference}: {str(e)}")
            transaction.requires_manual_review = True
            transaction.save()
        except ImportError:
            logger.warning("Products app not available for payment completion")
        except Exception as e:
            logger.error(f"Failed to complete product payment for {transaction.reference}: {str(e)}")
            transaction.requires_manual_review = True
            transaction.save()
    
    # ==========================================
    # TRANSFER HANDLERS (Withdrawals & Payouts)
    # ==========================================
    
    def _handle_transfer_success(self, data, webhook):
        """
        Handle successful transfer event
        
        This is called when:
        - A donation withdrawal transfer is completed
        - An El Mercado seller payout is completed
        """
        transfer_code = data.get('transfer_code', '')
        reference = data.get('reference', '')
        
        logger.info(f"Processing transfer.success: {transfer_code} / {reference}")
        
        # Check if this is an El Mercado payout (PO- prefix or em-po- prefix)
        if reference and (reference.startswith('PO-') or reference.startswith('em-po-')):
            self._process_el_mercado_payout_success(reference, transfer_code, data, webhook)
            return
        
        # Otherwise process as donation withdrawal
        try:
            from donations.models import DonationWithdrawal
            from donations.services import DonationService
            
            # Find the withdrawal
            withdrawal = None
            if transfer_code:
                withdrawal = DonationWithdrawal.objects.filter(
                    gateway_transfer_code=transfer_code
                ).first()
            
            if not withdrawal and reference:
                withdrawal = DonationWithdrawal.objects.filter(
                    reference=reference
                ).first()
            
            if withdrawal:
                # Only process if not already completed
                if withdrawal.status in ['processing', 'approved', 'pending']:
                    DonationService.complete_gateway_transfer(
                        withdrawal=withdrawal,
                        transfer_status='success',
                        gateway_data=data
                    )
                    logger.info(f"Withdrawal {withdrawal.reference} completed via webhook")
                else:
                    logger.info(f"Withdrawal {withdrawal.reference} already in {withdrawal.status} status")
            else:
                logger.warning(f"No withdrawal found for transfer: {transfer_code} / {reference}")
        
        except ImportError:
            logger.error("Donations app not available for transfer processing")
        except Exception as e:
            logger.error(f"Error processing transfer success: {str(e)}")
    
    def _handle_transfer_failed(self, data, webhook):
        """Handle failed transfer event"""
        transfer_code = data.get('transfer_code', '')
        reference = data.get('reference', '')
        
        logger.info(f"Processing transfer.failed: {transfer_code} / {reference}")
        
        # Check if this is an El Mercado payout (PO- prefix or em-po- prefix)
        if reference and (reference.startswith('PO-') or reference.startswith('em-po-')):
            self._process_el_mercado_payout_failed(reference, transfer_code, data, webhook)
            return
        
        try:
            from donations.models import DonationWithdrawal
            from donations.services import DonationService
            
            withdrawal = None
            if transfer_code:
                withdrawal = DonationWithdrawal.objects.filter(
                    gateway_transfer_code=transfer_code
                ).first()
            
            if not withdrawal and reference:
                withdrawal = DonationWithdrawal.objects.filter(
                    reference=reference
                ).first()
            
            if withdrawal and withdrawal.status in ['processing', 'approved', 'pending']:
                DonationService.complete_gateway_transfer(
                    withdrawal=withdrawal,
                    transfer_status='failed',
                    gateway_data=data
                )
                logger.info(f"Withdrawal {withdrawal.reference} marked as failed via webhook")
        
        except ImportError:
            logger.error("Donations app not available")
        except Exception as e:
            logger.error(f"Error processing transfer failure: {str(e)}")
    
    def _handle_transfer_reversed(self, data, webhook):
        """
        Handle reversed transfer event
        
        This occurs when a transfer couldn't be completed and funds are returned
        """
        transfer_code = data.get('transfer_code', '')
        reference = data.get('reference', '')
        
        logger.info(f"Processing transfer.reversed: {transfer_code} / {reference}")
        
        try:
            from donations.models import DonationWithdrawal
            from donations.services import DonationService
            
            withdrawal = None
            if transfer_code:
                withdrawal = DonationWithdrawal.objects.filter(
                    gateway_transfer_code=transfer_code
                ).first()
            
            if not withdrawal and reference:
                withdrawal = DonationWithdrawal.objects.filter(
                    reference=reference
                ).first()
            
            if withdrawal and withdrawal.status in ['processing', 'approved', 'pending']:
                DonationService.complete_gateway_transfer(
                    withdrawal=withdrawal,
                    transfer_status='failed',  # Treat reversed as failed
                    gateway_data=data
                )
                withdrawal.status_message = 'Transfer reversed by gateway - funds returned to Paystack balance'
                withdrawal.save()
                logger.info(f"Withdrawal {withdrawal.reference} marked as reversed via webhook")
        
        except ImportError:
            logger.error("Donations app not available")
        except Exception as e:
            logger.error(f"Error processing transfer reversal: {str(e)}")
    
    # ==========================================
    # EL MERCADO PAYOUT HANDLERS
    # ==========================================
    
    def _process_el_mercado_payout_success(self, reference, transfer_code, data, webhook):
        """Process successful El Mercado seller payout transfer."""
        try:
            from el_mercado.services import PayoutService
            from el_mercado.models import PayoutRequest
            
            # Extract the original payout reference
            # Format: em-po-{payout_reference}-{random}
            payout_reference = reference
            if reference.startswith('em-po-'):
                # Extract: em-po-PO-XXXX-random → PO-XXXX
                parts = reference.split('-')
                if len(parts) >= 4:
                    # Reconstruct PO-XXXX from parts[2] and parts[3]
                    payout_reference = f"{parts[2]}-{parts[3]}"
            
            payout = PayoutRequest.objects.filter(reference=payout_reference).first()
            
            if not payout:
                # Try the full reference
                payout = PayoutRequest.objects.filter(reference=reference).first()
            
            if not payout:
                # Try by gateway reference
                payout = PayoutRequest.objects.filter(gateway_reference=transfer_code).first()
            
            if payout:
                if payout.status == 'PROCESSING':
                    # Update gateway reference if not set
                    if transfer_code and not payout.gateway_reference:
                        payout.gateway_reference = transfer_code
                        payout.save(update_fields=['gateway_reference'])
                    
                    # Complete the payout
                    result = PayoutService.complete_payout(payout)
                    
                    if result.success:
                        logger.info(f"✅ El Mercado payout {reference} completed via webhook")
                    else:
                        logger.warning(f"El Mercado payout completion issue: {result.message}")
                else:
                    logger.info(f"El Mercado payout {reference} already in {payout.status} status")
            else:
                logger.warning(f"No El Mercado payout found for transfer: {reference} / {transfer_code}")
        
        except ImportError:
            logger.error("El Mercado app not available for payout processing")
        except Exception as e:
            logger.error(f"Error processing El Mercado payout success: {str(e)}", exc_info=True)
    
    def _process_el_mercado_payout_failed(self, reference, transfer_code, data, webhook):
        """Process failed El Mercado seller payout transfer."""
        try:
            from el_mercado.services import PayoutService
            from el_mercado.models import PayoutRequest
            
            # Extract the original payout reference
            payout_reference = reference
            if reference.startswith('em-po-'):
                parts = reference.split('-')
                if len(parts) >= 4:
                    payout_reference = f"{parts[2]}-{parts[3]}"
            
            payout = PayoutRequest.objects.filter(reference=payout_reference).first()
            
            if not payout:
                payout = PayoutRequest.objects.filter(reference=reference).first()
            
            if not payout:
                payout = PayoutRequest.objects.filter(gateway_reference=transfer_code).first()
            
            if payout and payout.status in ['PENDING', 'PROCESSING']:
                failure_reason = data.get('reason', 'Transfer failed at gateway')
                result = PayoutService.fail_payout(payout, failure_reason)
                
                if result.success:
                    logger.info(f"El Mercado payout {reference} marked as failed via webhook")
                else:
                    logger.warning(f"Failed to update payout status: {result.message}")
            else:
                logger.warning(f"No pending El Mercado payout found for: {reference}")
        
        except ImportError:
            logger.error("El Mercado app not available")
        except Exception as e:
            logger.error(f"Error processing El Mercado payout failure: {str(e)}")

    # ==========================================
    # REFUND HANDLERS
    # ==========================================
    
    def _handle_refund_processed(self, data, webhook):
        """Handle successful refund"""
        reference = data.get('transaction_reference', '')
        refund_id = data.get('id')
        
        logger.info(f"Refund processed for transaction: {reference}, refund ID: {refund_id}")
        
        try:
            from .models import Refund
            
            # Find refund by gateway reference
            refund = Refund.objects.filter(
                gateway_reference=str(refund_id)
            ).first()
            
            if refund and refund.status not in ['completed', 'success']:
                refund.status = 'completed'
                refund.completed_at = timezone.now()
                refund.gateway_response = data
                refund.save()
                logger.info(f"Refund {refund.reference} marked as completed via webhook")
        
        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}")
    
    def _handle_refund_failed(self, data, webhook):
        """Handle failed refund"""
        reference = data.get('transaction_reference', '')
        refund_id = data.get('id')
        
        logger.warning(f"Refund failed for transaction: {reference}, refund ID: {refund_id}")
        
        try:
            from .models import Refund
            
            refund = Refund.objects.filter(
                gateway_reference=str(refund_id)
            ).first()
            
            if refund and refund.status not in ['failed', 'completed']:
                refund.status = 'failed'
                refund.status_message = 'Refund failed at gateway'
                refund.gateway_response = data
                refund.save()
                logger.info(f"Refund {refund.reference} marked as failed via webhook")
        
        except Exception as e:
            logger.error(f"Error processing failed refund: {str(e)}")


# Legacy webhook view for backwards compatibility
# This redirects to the unified handler
@method_decorator(csrf_exempt, name='dispatch')
class DonationWebhookRedirect(APIView):
    """
    Redirect old donation webhook URL to unified handler
    
    NOTE: Update your Paystack webhook URL to /payments/webhooks/paystack/
    This redirect is for backwards compatibility only.
    """
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        logger.warning("Received webhook on deprecated /donations/webhook/ endpoint. Please update to /payments/webhooks/paystack/")
        # Forward to unified handler
        return PaystackWebhookView().post(request)
