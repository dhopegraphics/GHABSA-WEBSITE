"""
Payment Views for Voting System - Integrated with Universal Payment System
Handles payment initialization, verification, and webhooks using TransactionService
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
import logging

from .models import VotingEvent, VoterEligibility
from payments.models import Transaction, PaymentGateway, Currency
from payments.services.transaction_service import TransactionService
from .serializers import PaymentInitializationSerializer, PaymentVerificationSerializer

logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ViewSet):
    """
    Payment ViewSet for handling voting payments using Universal Payment System.
    Supports both authenticated and anonymous users for public events.
    
    Endpoints:
    - POST /payments/initialize/ - Initialize payment for voting
    - POST /payments/verify/ - Verify payment
    - GET /payments/{reference}/status/ - Check payment status
    """
    permission_classes = [AllowAny]  # Allow both authenticated and anonymous users
    
    @action(detail=False, methods=['post'], url_path='initialize')
    def initialize_payment(self, request):
        """
        Initialize a payment for a voting event using Universal Payment System.
        Supports both authenticated and anonymous users for public events.
        
        POST /api/voting/payments/initialize/
        
        Request Body:
        {
            "event_slug": "src-elections-2024",
            "currency": "GHS",  // Optional, defaults to GHS
            "gateway": "paystack",  // Optional, defaults to paystack
            "callback_url": "https://yourapp.com/payment/callback",  // Optional
            
            // Required for anonymous users:
            "customer_email": "user@example.com",  // Required if not authenticated
            "customer_phone": "+233XXXXXXXXX",     // Required if not authenticated
            "customer_name": "John Doe"             // Required if not authenticated
        }
        
        Response:
        {
            "status": "success",
            "message": "Payment initialized successfully",
            "data": {
                "transaction_id": "uuid",
                "authorization_url": "https://checkout.paystack.com/...",
                "reference": "TXN-...",
                "amount": "10.00",
                "currency": "GHS"
            }
        }
        """
        try:
            # Validate input
            serializer = PaymentInitializationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Invalid input',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            event_slug = serializer.validated_data['event_slug']
            currency_code = serializer.validated_data.get('currency', 'GHS')
            gateway_code = serializer.validated_data.get('gateway', 'paystack')
            callback_url = serializer.validated_data.get('callback_url')
            
            # Get voting event
            try:
                event = VotingEvent.objects.get(slug=event_slug)
            except VotingEvent.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Voting event not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if payment is required
            if not event.requires_payment:
                return Response({
                    'status': 'error',
                    'message': 'This event does not require payment'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # For anonymous users, verify event is public and has no restrictions
            is_anonymous = not (request.user and request.user.is_authenticated)
            if is_anonymous:
                if event.visibility != 'public':
                    return Response({
                        'status': 'error',
                        'message': 'This event requires authentication. Please log in to proceed with payment.'
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                if event.eligible_years or event.eligible_programs:
                    return Response({
                        'status': 'error',
                        'message': 'This event has eligibility restrictions. Please log in to verify your eligibility.'
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                # Require customer details for anonymous users
                customer_email = serializer.validated_data.get('customer_email')
                customer_phone = serializer.validated_data.get('customer_phone')
                customer_name = serializer.validated_data.get('customer_name')
                
                if not customer_email or not customer_phone or not customer_name:
                    return Response({
                        'status': 'error',
                        'message': 'Customer email, phone, and name are required for payment.',
                        'required_fields': ['customer_email', 'customer_phone', 'customer_name']
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get currency and calculate converted amount if needed
            try:
                from payments.models import Currency
                target_currency = Currency.objects.get(code=currency_code, is_active=True)
                event_currency = Currency.objects.get(code=event.currency or 'GHS', is_active=True)
                
                # Convert event voting fee to target currency
                if event_currency.is_base_currency:
                    # From base to target
                    converted_amount = event.voting_fee * target_currency.exchange_rate
                elif target_currency.is_base_currency:
                    # From event currency to base
                    converted_amount = event.voting_fee / event_currency.exchange_rate
                else:
                    # From event currency to base, then base to target
                    amount_in_base = event.voting_fee / event_currency.exchange_rate
                    converted_amount = amount_in_base * target_currency.exchange_rate
                
            except Currency.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': f'Currency "{currency_code}" not supported'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if payment is required
            if not event.requires_payment:
                return Response({
                    'status': 'error',
                    'message': 'This event does not require payment'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user already paid (skip for anonymous users)
            if request.user and request.user.is_authenticated:
                content_type = ContentType.objects.get_for_model(VotingEvent)
                existing_transaction = Transaction.objects.filter(
                    content_type=content_type,
                    object_id=event.id,
                    user=request.user,
                    status__in=['success', 'completed']
                ).first()
                
                if existing_transaction:
                    return Response({
                        'status': 'error',
                        'message': 'You have already paid for this event',
                        'transaction_id': str(existing_transaction.id)
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get gateway and currency
            try:
                gateway = PaymentGateway.objects.get(name=gateway_code, is_active=True)
            except PaymentGateway.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': f'Payment gateway "{gateway_code}" not available'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                currency = Currency.objects.get(code=currency_code, is_active=True)
            except Currency.objects.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': f'Currency "{currency_code}" not supported'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Prepare metadata
            user_id = str(request.user.id) if request.user and request.user.is_authenticated else 'anonymous'
            user_phone = str(request.user.phone) if request.user and request.user.is_authenticated else 'N/A'
            user_email = request.user.email if request.user and request.user.is_authenticated else 'N/A'
            
            metadata = {
                'event_id': str(event.id),
                'event_slug': event.slug,
                'event_title': event.title,
                'user_id': user_id,
                'user_phone': user_phone,
                'user_email': user_email,
                'is_anonymous': 'true' if is_anonymous else 'false',
                'purpose': 'voting_fee',
                'original_amount': str(event.voting_fee),
                'original_currency': event.currency or 'GHS',
                'target_currency': currency_code,
                'exchange_rate': str(target_currency.exchange_rate) if not target_currency.is_base_currency else str(event_currency.exchange_rate),
            }
            
            # Get customer info - from request for both anonymous and authenticated users
            if is_anonymous:
                # For anonymous users, use provided customer details (already validated)
                customer_email = serializer.validated_data.get('customer_email')
                customer_phone = serializer.validated_data.get('customer_phone')
                customer_name = serializer.validated_data.get('customer_name')
            else:
                # For authenticated users, prefer request data, fallback to user profile
                customer_email = serializer.validated_data.get('customer_email') or request.user.email or f"{request.user.phone}@cssknust.edu.gh"
                customer_phone = serializer.validated_data.get('customer_phone') or str(request.user.phone)
                customer_name = serializer.validated_data.get('customer_name') or request.user.get_full_name()
            
            # Clean phone number for Paystack (remove spaces, dashes, ensure + prefix)
            if customer_phone:
                customer_phone = customer_phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                if not customer_phone.startswith('+'):
                    customer_phone = '+' + customer_phone
            
            # Step 1: Create transaction using Universal Payment System
            # Use converted amount if currency is different from event currency
            transaction_amount = converted_amount if currency_code != (event.currency or 'GHS') else event.voting_fee
            
            # For anonymous users, pass user=None
            transaction_user = request.user if request.user and request.user.is_authenticated else None
            
            transaction_obj = TransactionService.create_transaction(
                gateway_name=gateway_code,
                amount=transaction_amount,
                currency_code=currency_code,
                user=transaction_user,  # Can be None for anonymous users
                content_object=event,
                customer_email=customer_email,
                customer_phone=customer_phone,
                customer_name=customer_name,
                description=f"Voting fee for {event.title}",
                metadata=metadata,
            )
            
            # Step 2: Initialize payment with gateway
            payment_result = TransactionService.initialize_payment(
                transaction=transaction_obj,
                callback_url=callback_url
            )
            
            # Update or create voter eligibility
            with transaction.atomic():
                eligibility, created = VoterEligibility.objects.get_or_create(
                    event=event,
                    user=request.user,
                    defaults={
                        'is_eligible': True,
                        'payment_required': True,
                        'payment_verified': False,
                        'payment_reference': transaction_obj.reference,
                    }
                )
                
                if not created:
                    eligibility.payment_reference = transaction_obj.reference
                    eligibility.payment_required = True
                    eligibility.save()
            
            logger.info(f"Voting payment initialized: {transaction_obj.reference} for user {request.user.phone}")
            
            return Response({
                'status': 'success',
                'message': 'Payment initialized successfully',
                'data': {
                    'transaction_id': str(transaction_obj.id),
                    'authorization_url': payment_result['authorization_url'],
                    'reference': transaction_obj.reference,
                    'amount': str(transaction_obj.amount),
                    'currency': transaction_obj.currency.code,
                    'event': {
                        'slug': event.slug,
                        'title': event.title,
                    }
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.exception(f"Error initializing voting payment: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='verify')
    def verify_payment(self, request):
        """
        Verify a payment using Universal Payment System.
        
        POST /api/voting/payments/verify/
        
        Request Body:
        {
            "reference": "TXN-..."
        }
        
        Response:
        {
            "status": "success",
            "message": "Payment verified successfully",
            "data": {
                "transaction_id": "uuid",
                "status": "success",
                "amount": "10.00",
                "currency": "GHS",
                "paid_at": "2024-01-01T12:00:00Z"
            }
        }
        """
        try:
            serializer = PaymentVerificationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Invalid input',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            reference = serializer.validated_data['reference']
            
            # Get transaction record
            try:
                transaction_obj = Transaction.objects.get(reference=reference)
            except Transaction.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Transaction not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if already verified
            if transaction_obj.status in ['success', 'completed']:
                return Response({
                    'status': 'success',
                    'message': 'Payment already verified',
                    'data': {
                        'transaction_id': str(transaction_obj.id),
                        'status': transaction_obj.status,
                        'amount': str(transaction_obj.amount),
                        'currency': transaction_obj.currency.code,
                    }
                })
            
            # Verify with payment gateway using Universal Payment System
            verification_result = TransactionService.verify_payment(
                reference=reference,
                gateway=transaction_obj.gateway
            )
            
            if not verification_result['success']:
                return Response({
                    'status': 'error',
                    'message': verification_result.get('error', 'Payment verification failed')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get updated transaction
            transaction_obj.refresh_from_db()
            
            # Update voter eligibility if payment successful
            if transaction_obj.status in ['success', 'completed']:
                # Get the voting event from content_object
                event = transaction_obj.content_object
                if isinstance(event, VotingEvent):
                    VoterEligibility.objects.filter(
                        event=event,
                        user=transaction_obj.user
                    ).update(
                        payment_verified=True,
                        payment_date=timezone.now()
                    )
                    logger.info(f"Voting payment verified: {reference}")
                else:
                    logger.warning(f"Transaction {reference} is not linked to a VotingEvent")
            else:
                logger.warning(f"Payment verification result not successful: {reference} - Status: {transaction_obj.status}")
            
            return Response({
                'status': 'success' if transaction_obj.status in ['success', 'completed'] else 'failed',
                'message': f'Payment {transaction_obj.status}',
                'data': {
                    'transaction_id': str(transaction_obj.id),
                    'status': transaction_obj.status,
                    'amount': str(transaction_obj.amount),
                    'currency': transaction_obj.currency.code,
                    'paid_at': transaction_obj.paid_at.isoformat() if transaction_obj.paid_at else None,
                    'reference': transaction_obj.reference,
                }
            })
            
        except Exception as e:
            logger.exception(f"Error verifying payment: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='(?P<reference>[^/.]+)/status')
    def check_status(self, request, reference=None):
        """
        Check payment status.
        
        GET /api/voting/payments/{reference}/status/
        
        Response:
        {
            "status": "success",
            "data": {
                "transaction_id": "uuid",
                "reference": "TXN-...",
                "status": "success",
                "amount": "10.00",
                "currency": "GHS"
            }
        }
        """
        try:
            transaction_obj = Transaction.objects.get(reference=reference)
            
            return Response({
                'status': 'success',
                'data': {
                    'transaction_id': str(transaction_obj.id),
                    'reference': transaction_obj.reference,
                    'status': transaction_obj.status,
                    'amount': str(transaction_obj.amount),
                    'currency': transaction_obj.currency.code,
                    'paid_at': transaction_obj.paid_at.isoformat() if transaction_obj.paid_at else None,
                    'created_at': transaction_obj.created_at.isoformat(),
                }
            })
            
        except Transaction.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Transaction not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(f"Error checking payment status: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Webhook handling is now managed by the universal payment system
# See payments/webhooks.py for webhook implementation
