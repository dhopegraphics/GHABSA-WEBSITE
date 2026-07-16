from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.shortcuts import render
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework import status, viewsets
from products.repository import ProductRepo
from products.models import ProductPayment
from products.serializers import (
    ProductListSerializer,
    ProductPaymentInitializeSerializer,
    ProductPaymentVerifySerializer,
    MerchandiseCollectionSerializer,
    ProductTransactionSerializer,
    CartCheckoutSerializer,
    ProductPaymentSerializer,
)
from products.payment_service import ProductPaymentService
from payments.services.transaction_service import TransactionService
import logging

logger = logging.getLogger('products')
payment_logger = logging.getLogger('payments')


class IsStaffUser(IsAuthenticated):
    """
    Custom permission: User must be authenticated AND be a staff member.
    Used for merchandise validation endpoints.
    """
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_staff


class ProductListView(ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Return only active products"""
        return ProductRepo.get_active_products()
    
    def get_serializer_context(self):
        """Pass request to serializer for user-specific pricing"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# NEW: Integrated payment views

class ProductPaymentViewSet(viewsets.ViewSet):
    """
    ViewSet for product payment operations using integrated payment system
    
    Actions:
    - initialize: Initialize a product payment
    - verify: Verify payment status
    - my_purchases: Get user's product purchases
    - collect: Mark merchandise as collected (staff only)
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def initialize(self, request):
        """
        Initialize a product payment
        
        POST /api/products/payments/initialize/
        
        Request body:
        {
            "product_id": "uuid",
            "quantity": 1,
            "gateway": "paystack",
            "callback_url": "https://..."
        }
        
        Returns:
        {
            "success": true,
            "transaction_id": "uuid",
            "reference": "TXN-...",
            "payment_url": "https://paystack.com/...",
            "amount": "50.00",
            "currency": "GHS"
        }
        """
        serializer = ProductPaymentInitializeSerializer(data=request.data)
        
        if not serializer.is_valid():
            # Log validation errors for debugging
            logger.error(f"Payment initialization validation errors: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get IP and user agent from request
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            logger.info(f"Validation passed, initializing payment for user: {request.user.id}")
            payment_logger.info(f"Product payment init - Product: {serializer.validated_data['product_id']}, Gateway: {serializer.validated_data['gateway']}, Quantity: {serializer.validated_data['quantity']}")
            
            variant_selections = serializer.validated_data.get('variant_selections', [])
            if variant_selections:
                logger.debug(f"Variant selections: {variant_selections}")
            
            # Extract purchase type parameters
            is_gift_purchase = serializer.validated_data.get('is_gift_purchase', False)
            is_purchase_on_behalf = serializer.validated_data.get('is_purchase_on_behalf', False)
            purchased_for_phone = serializer.validated_data.get('purchased_for_phone')
            gift_message = serializer.validated_data.get('gift_message')
            
            logger.info(f"Purchase type data received: is_gift={is_gift_purchase}, is_on_behalf={is_purchase_on_behalf}, phone={purchased_for_phone}, message={gift_message}")
            
            result = ProductPaymentService.initialize_product_payment(
                user=request.user,
                product_id=serializer.validated_data['product_id'],
                gateway_name=serializer.validated_data['gateway'],
                callback_url=serializer.validated_data['callback_url'],
                quantity=serializer.validated_data['quantity'],
                variant_selections=variant_selections,
                ip_address=ip_address,
                user_agent=user_agent,
                is_gift_purchase=is_gift_purchase,
                is_purchase_on_behalf=is_purchase_on_behalf,
                purchased_for_phone=purchased_for_phone,
                gift_message=gift_message,
            )
            
            transaction = result['transaction']
            
            return Response({
                'success': True,
                'transaction_id': str(transaction.id),
                'reference': transaction.reference,
                'payment_url': result['payment_url'],
                'access_code': result['access_code'],
                'amount': str(transaction.amount),
                'currency': transaction.currency.code,
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"ValueError during payment initialization: {e}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Unexpected error during payment initialization: {e}")
            return Response({
                'success': False,
                'error': 'Payment initialization failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def cart_checkout(self, request):
        """
        Initialize payment for multiple cart items
        
        POST /api/products/payments/cart_checkout/
        
        Request body:
        {
            "cart_items": [
                {
                    "product_id": "uuid",
                    "quantity": 2,
                    "variant_selections": [
                        {"color_id": "uuid", "size_id": "uuid", "quantity": 1},
                        {"color_id": "uuid", "size_id": "uuid", "quantity": 1}
                    ]
                },
                {
                    "product_id": "uuid2",
                    "quantity": 1,
                    "variant_selections": []
                }
            ],
            "gateway": "paystack",
            "callback_url": "https://..."
        }
        
        Returns:
        {
            "success": true,
            "transaction_id": "uuid",
            "reference": "TXN-...",
            "payment_url": "https://paystack.com/...",
            "amount": "150.00",
            "currency": "GHS",
            "items_count": 2
        }
        """
        serializer = CartCheckoutSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"Cart checkout validation errors: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            cart_items = serializer.validated_data['cart_items']
            
            logger.info(f"Cart checkout for user: {request.user.id}, items: {len(cart_items)}")
            payment_logger.info(f"Cart checkout - Items: {len(cart_items)}, Gateway: {serializer.validated_data['gateway']}")
            
            result = ProductPaymentService.initialize_cart_payment(
                user=request.user,
                cart_items=cart_items,
                gateway_name=serializer.validated_data['gateway'],
                callback_url=serializer.validated_data['callback_url'],
                # Purchase type fields
                is_gift_purchase=serializer.validated_data.get('is_gift_purchase', False),
                is_purchase_on_behalf=serializer.validated_data.get('is_purchase_on_behalf', False),
                purchased_for_phone=serializer.validated_data.get('purchased_for_phone'),
                gift_message=serializer.validated_data.get('gift_message'),
                # Additional fields
                ip_address=ip_address,
                user_agent=user_agent,
            )
            
            transaction = result['transaction']
            
            return Response({
                'success': True,
                'transaction_id': str(transaction.id),
                'reference': transaction.reference,
                'payment_url': result['payment_url'],
                'access_code': result['access_code'],
                'amount': str(transaction.amount),
                'currency': transaction.currency.code,
                'items_count': len(cart_items),
                'total_amount': result['total_amount'],
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"ValueError during cart checkout: {e}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Unexpected error during cart checkout: {e}")
            return Response({
                'success': False,
                'error': 'Cart checkout failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """
        Verify a product payment with smart retry logic.
        
        Flow:
        1. First check if ProductPayment already exists → return success immediately
        2. If no ProductPayment, check Transaction status
        3. If pending, re-verify with Paystack to get actual status
        4. If Paystack says success, call complete_product_payment
        5. Return validation codes and success
        
        POST /api/products/payments/verify/
        
        Request body:
        {
            "reference": "TXN-...",
            "force_recheck": false  // Optional: force re-verify with Paystack
        }
        """
        import time
        
        serializer = ProductPaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reference = serializer.validated_data['reference']
        force_recheck = request.data.get('force_recheck', False)
        
        # Helper function to fetch validation codes from ProductPayment records
        def get_validation_codes_from_db(txn):
            """Fetch validation codes from ProductPayment records in database"""
            from products.models import ProductColor, ProductSize
            
            product_payments = ProductPayment.objects.filter(transaction_record=txn).select_related('product')
            codes = []
            for pp in product_payments:
                # Format variant selections with color/size names
                formatted_variants = []
                if pp.variant_selections:
                    for selection in pp.variant_selections:
                        variant_item = {'quantity': selection.get('quantity', 1)}
                        
                        # Get color details
                        color_id = selection.get('color_id')
                        if color_id:
                            try:
                                color = ProductColor.objects.get(id=color_id)
                                variant_item['color'] = color.name
                                variant_item['color_hex'] = color.hex_code
                            except ProductColor.DoesNotExist:
                                pass
                        
                        # Get size details  
                        size_id = selection.get('size_id')
                        if size_id:
                            try:
                                size = ProductSize.objects.get(id=size_id)
                                variant_item['size'] = size.name
                            except ProductSize.DoesNotExist:
                                pass
                        
                        formatted_variants.append(variant_item)
                
                codes.append({
                    'code': pp.transaction_validation_code,
                    'product_name': pp.product.product_name if pp.product else 'Unknown',
                    'quantity': pp.quantity,
                    'is_gift': pp.is_gift_purchase,
                    'is_on_behalf': pp.is_purchase_on_behalf,
                    'recipient_phone': str(pp.purchased_for_phone) if pp.purchased_for_phone else None,
                    'recipient_name': pp.purchased_for_user.get_full_name() if pp.purchased_for_user else None,
                    'variant_selections': formatted_variants,
                })
            return codes, product_payments
        
        def get_single_product_payment_data(txn):
            """Get data for single item checkout from ProductPayment"""
            pp = txn.product_payments.first()
            if pp:
                return {
                    'validation_code': pp.transaction_validation_code,
                    'merchandise_collected': pp.merchandise_collected,
                    'product_payment_id': str(pp.id),
                    'product_name': pp.product.product_name if pp.product else None,
                }
            return None
        
        # Get transaction
        transaction = ProductPaymentService.get_product_transaction(reference)
        
        if not transaction:
            return Response({
                'success': False,
                'error': 'Transaction not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user owns this transaction
        if transaction.user != request.user:
            return Response({
                'success': False,
                'error': 'Unauthorized'
            }, status=status.HTTP_403_FORBIDDEN)
        
        is_cart_checkout = transaction.metadata.get('cart_checkout', False)
        
        # ============================================================
        # STEP 1: Check if ProductPayment already exists
        # If it does, we can return success immediately without re-verifying
        # ============================================================
        existing_codes, existing_payments = get_validation_codes_from_db(transaction)
        
        if existing_payments.exists() and not force_recheck:
            payment_logger.info(f"ProductPayment already exists for {reference}, returning cached data")
            transaction_data = ProductTransactionSerializer(transaction).data
            
            if is_cart_checkout:
                return Response({
                    'success': True,
                    'transaction': transaction_data,
                    'is_cart_checkout': True,
                    'items_count': len(existing_codes),
                    'validation_codes': existing_codes,
                    'pending_completion': False,
                    'from_cache': True,
                    'message': 'Payment verified successfully'
                }, status=status.HTTP_200_OK)
            else:
                pp_data = get_single_product_payment_data(transaction)
                return Response({
                    'success': True,
                    'transaction': transaction_data,
                    'is_cart_checkout': False,
                    'validation_code': pp_data['validation_code'] if pp_data else None,
                    'validation_codes': existing_codes,  # Include full details with variant_selections
                    'merchandise_collected': pp_data['merchandise_collected'] if pp_data else False,
                    'product_name': pp_data['product_name'] if pp_data else None,
                    'amount_paid': str(transaction.amount),
                    'product_payment_id': pp_data['product_payment_id'] if pp_data else None,
                    'pending_completion': False,
                    'from_cache': True,
                    'message': 'Payment verified successfully'
                }, status=status.HTTP_200_OK)
        
        # ============================================================
        # STEP 2: No ProductPayment exists - Check/Update Transaction status
        # If pending or force_recheck, verify with Paystack
        # ============================================================
        if transaction.status == 'pending' or force_recheck:
            try:
                payment_logger.info(f"Verifying payment with gateway for {reference}")
                transaction = TransactionService.verify_payment(reference)
                payment_logger.info(f"Gateway verification complete: status={transaction.status}")
            except Exception as e:
                logger.error(f"Payment verification failed: {str(e)}", exc_info=True)
                return Response({
                    'success': False,
                    'error': 'Payment verification failed',
                    'details': str(e),
                    'transaction_status': transaction.status
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============================================================
        # STEP 3: If transaction is successful, complete product payment
        # This creates ProductPayment records and validation codes
        # ============================================================
        completion_result = None
        
        if transaction.status == 'success':
            # Use retry logic with exponential backoff
            max_attempts = 3
            retry_delay = 1.0
            
            for attempt in range(max_attempts):
                try:
                    completion_result = ProductPaymentService.complete_product_payment(
                        transaction=transaction,
                        reduce_stock=True,
                        send_notification=True,
                    )
                    payment_logger.info(f"Product payment completed on attempt {attempt + 1}")
                    break
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed: {str(e)}")
                    if attempt < max_attempts - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    # Continue to response even if completion failed - we'll indicate pending_completion
            
            # If completion_result is None, try fetching from DB one more time
            # (in case webhook completed it while we were retrying)
            if not completion_result:
                time.sleep(0.5)  # Brief wait
                existing_codes, existing_payments = get_validation_codes_from_db(transaction)
                if existing_payments.exists():
                    payment_logger.info(f"Found ProductPayments created by another process")
        
        # ============================================================
        # STEP 4: Build and return response
        # ============================================================
        transaction.refresh_from_db()  # Get latest state
        transaction_data = ProductTransactionSerializer(transaction).data
        
        if is_cart_checkout:
            validation_codes = []
            
            # Priority: completion_result > metadata > database
            if completion_result and completion_result.get('validation_codes'):
                validation_codes = completion_result['validation_codes']
            elif transaction.metadata.get('validation_codes'):
                validation_codes = transaction.metadata['validation_codes']
            else:
                validation_codes, _ = get_validation_codes_from_db(transaction)
            
            return Response({
                'success': True,
                'transaction': transaction_data,
                'is_cart_checkout': True,
                'items_count': len(validation_codes),
                'validation_codes': validation_codes,
                'pending_completion': transaction.status == 'success' and not validation_codes,
                'message': 'Payment verified successfully' if transaction.status == 'success' else f'Payment status: {transaction.status}'
            }, status=status.HTTP_200_OK)
        else:
            # Single item checkout
            validation_code = None
            merchandise_collected = False
            product_name = None
            product_payment_id = None
            
            if completion_result:
                validation_code = completion_result.get('validation_code')
                product_name = completion_result.get('product_name')
                product_payment_id = completion_result.get('product_payment_id')
            
            # Fallback to database
            if not validation_code:
                pp_data = get_single_product_payment_data(transaction)
                if pp_data:
                    validation_code = pp_data['validation_code']
                    merchandise_collected = pp_data['merchandise_collected']
                    product_name = pp_data['product_name']
                    product_payment_id = pp_data['product_payment_id']
            
            # Get validation_codes with full variant details
            validation_codes_full, _ = get_validation_codes_from_db(transaction)
            
            return Response({
                'success': True,
                'transaction': transaction_data,
                'is_cart_checkout': False,
                'validation_code': validation_code,
                'validation_codes': validation_codes_full,  # Include full details with variant_selections
                'merchandise_collected': merchandise_collected,
                'product_name': product_name,
                'amount_paid': str(transaction.amount),
                'product_payment_id': product_payment_id,
                'pending_completion': transaction.status == 'success' and not validation_code,
                'message': 'Payment verified successfully' if transaction.status == 'success' else f'Payment status: {transaction.status}'
            }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def my_purchases(self, request):
        """
        Get authenticated user's product purchases
        
        GET /api/products/payments/my_purchases/
        
        Query params:
        - status: Filter by status (success, pending, collected)
        
        Returns list of ProductPayment records (individual product purchases).
        Each item in a cart checkout will appear as a separate entry with its own validation code.
        Includes purchases bought BY the user AND purchases bought FOR the user (gift purchases).
        """
        from products.models import ProductPayment
        from django.db.models import Q
        
        status_filter = request.query_params.get('status')
        
        # Get ProductPayment records for this user
        # Include purchases where:
        # 1. User is the buyer (who paid)
        # 2. User is the recipient (gift purchases)
        # 3. Fallback: transaction_record.user matches (for old data where buyer might be NULL)
        queryset = ProductPayment.objects.filter(
            Q(buyer=request.user) | 
            Q(purchased_for_user=request.user) |
            Q(transaction_record__user=request.user),
            payment_successful=True
        ).select_related(
            'product', 'transaction_record', 'buyer', 'purchased_for_user'
        ).distinct().order_by('-payed_at')
        
        # Apply status filter
        if status_filter:
            if status_filter == 'collected':
                queryset = queryset.filter(merchandise_taken=True)
            elif status_filter == 'pending':
                queryset = queryset.filter(payment_successful=False)
            elif status_filter == 'success':
                # Show all successful payments, including collected ones
                queryset = queryset.filter(payment_successful=True)
        
        serializer = ProductPaymentSerializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'purchases': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def collect(self, request):
        """
        Mark merchandise as collected using validation code
        
        POST /api/products/payments/collect/
        
        Request body:
        {
            "validation_code": "ABC123"
        }
        
        Returns collection details
        
        Note: In production, you may want to restrict this to staff only
        """
        serializer = MerchandiseCollectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = ProductPaymentService.mark_merchandise_collected(
                validation_code=serializer.validated_data['validation_code'],
                collected_by=request.user,
            )
            
            return Response({
                'success': True,
                'message': 'Merchandise marked as collected',
                **result
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def update_variant_preferences(self, request):
        """
        Update variant preferences for an existing purchase (retroactive)
        
        NEW ARCHITECTURE: Updates ProductPayment.variant_selections (product-specific data)
        INCLUDES PREFERENCE CHANGE TRACKING: Enforces 1-change limit and collection lock
        
        POST /api/products/payments/update_variant_preferences/
        
        Request body:
        {
            "reference": "TXN-XXX",
            "variant_selections": [
                {"color_id": "uuid", "size_id": "uuid", "quantity": 1},
                {"color_id": "uuid", "size_id": "uuid", "quantity": 1}
            ]
        }
        
        Returns updated transaction
        """
        from products.serializers import VariantSelectionSerializer
        from payments.models import Transaction
        from products.models import ProductColor, ProductSize, ProductPayment
        
        reference = request.data.get('reference')
        variant_selections = request.data.get('variant_selections', [])
        
        if not reference:
            return Response({
                'success': False,
                'error': 'Transaction reference is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get transaction and verify ownership
            transaction = Transaction.objects.get(reference=reference, user=request.user)
            
            if transaction.status != 'success':
                return Response({
                    'success': False,
                    'error': 'Can only update preferences for successful purchases'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate variant selections
            serializer = VariantSelectionSerializer(data=variant_selections, many=True)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': 'Invalid variant selections',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Format variant selections
            raw_selections = []  # Store in ProductPayment
            formatted_selections = []  # Backward compatibility
            
            for selection in serializer.validated_data:
                # Raw selection for ProductPayment (new architecture)
                raw_selections.append({
                    'color_id': str(selection.get('color_id')) if selection.get('color_id') else None,
                    'size_id': str(selection.get('size_id')) if selection.get('size_id') else None,
                    'quantity': selection['quantity']
                })
                
                # Formatted for metadata (backward compatibility)
                formatted = {'quantity': selection['quantity']}
                
                if selection.get('color_id'):
                    try:
                        color = ProductColor.objects.get(id=selection['color_id'])
                        formatted['color'] = {
                            'id': str(color.id),
                            'name': color.name,
                            'hex_code': color.hex_code
                        }
                    except ProductColor.DoesNotExist:
                        pass
                
                if selection.get('size_id'):
                    try:
                        size = ProductSize.objects.get(id=selection['size_id'])
                        formatted['size'] = {
                            'id': str(size.id),
                            'name': size.name,
                            'code': size.code
                        }
                    except ProductSize.DoesNotExist:
                        pass
                
                formatted_selections.append(formatted)
            
            # NEW ARCHITECTURE: Store in ProductPayment (product-specific data)
            logger.debug(f"Looking for ProductPayment for reference: {reference}")
            product_payment = None
            
            # First try: via ForeignKey relationship (transaction can have multiple product_payments)
            try:
                # Get the first associated ProductPayment (for single product purchases)
                # For cart purchases, variant selections are stored per-item in complete_product_payment
                product_payment = transaction.product_payments.first()
                if product_payment:
                    logger.debug(f"Found ProductPayment via transaction.product_payments: {product_payment.payment_id}")
                else:
                    logger.debug("No ProductPayment via ForeignKey relationship")
                    raise Exception("No ProductPayment found")
            except Exception as e:
                logger.debug(f"No ProductPayment via ForeignKey relationship: {e}")
                
                # Second try: lookup by reference
                try:
                    product_payment = ProductPayment.objects.get(reference=reference)
                    logger.debug(f"Found ProductPayment by reference lookup: {product_payment.payment_id}")
                    
                    # Link it if not already linked
                    if not product_payment.transaction_record:
                        product_payment.transaction_record = transaction
                        logger.debug("Linking ProductPayment to Transaction")
                except ProductPayment.DoesNotExist:
                    logger.warning(f"No ProductPayment found for reference: {reference}")
                except Exception as lookup_error:
                    logger.error(f"Error looking up ProductPayment: {lookup_error}")
            
            # Update variant selections if we found the record
            if product_payment:
                # Check if product actually needs preferences
                needs_prefs, missing = product_payment.needs_preferences()
                
                if needs_prefs and not raw_selections:
                    return Response({
                        'success': False,
                        'error': f'This product requires {" and ".join(missing)} preferences. Please provide variant selections.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Validate preference change is allowed
                can_change, reason = product_payment.can_change_preferences()
                if not can_change:
                    return Response({
                        'success': False,
                        'error': reason,
                        'preference_change_count': product_payment.preference_change_count,
                        'preferences_locked': product_payment.preferences_locked,
                        'merchandise_taken': product_payment.merchandise_taken
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                logger.debug(f"Updating ProductPayment.variant_selections from {product_payment.variant_selections} to {raw_selections}")
                
                # Use the model's update_preferences method with tracking
                try:
                    success, message = product_payment.update_preferences(raw_selections)
                    logger.info(f"ProductPayment preferences updated: {message}")
                    logger.debug(f"   Change count: {product_payment.preference_change_count}")
                    logger.debug(f"   Locked: {product_payment.preferences_locked}")
                    logger.debug(f"   Final selections: {product_payment.variant_selections}")
                except ValueError as ve:
                    return Response({
                        'success': False,
                        'error': str(ve)
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                logger.warning(f"Could not find ProductPayment to update variant selections")
                return Response({
                    'success': False,
                    'error': 'Product payment record not found'
                }, status=status.HTTP_404_NOT_FOUND)

            
            # TEMPORARY: Also update Transaction (for backward compatibility during migration)
            transaction.variant_selections = raw_selections
            
            # Also update metadata (backward compatibility)
            if transaction.metadata is None:
                transaction.metadata = {}
            
            transaction.metadata['variant_selections'] = formatted_selections
            transaction.save()
            
            return Response({
                'success': True,
                'message': 'Variant preferences updated successfully',
                'preference_change_count': product_payment.preference_change_count,
                'preferences_locked': product_payment.preferences_locked,
                'changes_remaining': max(0, 1 - product_payment.preference_change_count),
                'transaction': ProductTransactionSerializer(transaction).data
            }, status=status.HTTP_200_OK)
            
        except Transaction.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Transaction not found or you do not have permission to update it'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating variant preferences: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StaffMerchandiseValidationViewSet(viewsets.ViewSet):
    """
    ViewSet for STAFF-ONLY merchandise validation operations.
    
    Used by staff members to:
    - Look up purchases by validation code
    - Mark merchandise as collected (single or bulk)
    - Mark items as unavailable
    - Handle substitutions
    
    All endpoints require staff authentication.
    """
    
    permission_classes = [IsStaffUser]
    
    @action(detail=False, methods=['post'])
    def lookup(self, request):
        """
        Look up a purchase by validation code.
        
        POST /api/products/staff/validation/lookup/
        
        Request body:
        {
            "validation_code": "ABC123"
        }
        
        Returns full collection status and details.
        """
        validation_code = request.data.get('validation_code', '').strip().upper()
        
        if not validation_code:
            return Response({
                'success': False,
                'error': 'Validation code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(validation_code) != 6:
            return Response({
                'success': False,
                'error': 'Validation code must be exactly 6 characters'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            collection_status = ProductPaymentService.get_collection_status(validation_code)
            
            if not collection_status.get('payment_successful'):
                return Response({
                    'success': False,
                    'error': 'Payment was not successful for this validation code'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                **collection_status
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Staff validation lookup error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'An error occurred while looking up the validation code'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def collect(self, request):
        """
        Mark merchandise as collected (single or bulk).
        
        POST /api/products/staff/validation/collect/
        
        For single full collection:
        {
            "validation_code": "ABC123"
        }
        
        For partial/variant collection:
        {
            "validation_code": "ABC123",
            "variant_collections": [
                {
                    "variant_index": 0,
                    "quantity": 1,
                    "substituted": false,
                    "substitution_notes": ""
                }
            ]
        }
        
        Returns updated collection status.
        """
        validation_code = request.data.get('validation_code', '').strip().upper()
        variant_collections = request.data.get('variant_collections', None)
        
        if not validation_code:
            return Response({
                'success': False,
                'error': 'Validation code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            collector_name = request.user.get_full_name() or request.user.username
            
            result = ProductPaymentService.mark_merchandise_collected(
                validation_code=validation_code,
                collected_by=collector_name,
                variant_collections=variant_collections
            )
            
            return Response({
                'success': True,
                'message': 'Items collected successfully' if result.get('fully_collected') else 'Items partially collected',
                **result
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Staff validation collect error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def bulk_collect(self, request):
        """
        Bulk collect multiple validation codes at once.
        
        POST /api/products/staff/validation/bulk_collect/
        
        Request body:
        {
            "validation_codes": ["ABC123", "DEF456", "GHI789"]
        }
        
        Returns results for each code (success/error).
        """
        validation_codes = request.data.get('validation_codes', [])
        
        if not validation_codes:
            return Response({
                'success': False,
                'error': 'At least one validation code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(validation_codes) > 50:
            return Response({
                'success': False,
                'error': 'Maximum 50 validation codes per bulk operation'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        collector_name = request.user.get_full_name() or request.user.username
        results = []
        success_count = 0
        error_count = 0
        
        for code in validation_codes:
            code = code.strip().upper()
            if not code or len(code) != 6:
                results.append({
                    'validation_code': code,
                    'success': False,
                    'error': 'Invalid validation code format'
                })
                error_count += 1
                continue
            
            try:
                result = ProductPaymentService.mark_merchandise_collected(
                    validation_code=code,
                    collected_by=collector_name
                )
                results.append({
                    'validation_code': code,
                    'success': True,
                    'customer_name': result.get('customer_name'),
                    'product_name': result.get('product_name'),
                    'quantity': result.get('quantity'),
                    'fully_collected': result.get('fully_collected'),
                    'collection_summary': result.get('collection_summary')
                })
                success_count += 1
            except ValueError as e:
                results.append({
                    'validation_code': code,
                    'success': False,
                    'error': str(e)
                })
                error_count += 1
            except Exception as e:
                logger.error(f"Bulk collect error for {code}: {str(e)}")
                results.append({
                    'validation_code': code,
                    'success': False,
                    'error': 'An unexpected error occurred'
                })
                error_count += 1
        
        return Response({
            'success': True,
            'total_processed': len(validation_codes),
            'success_count': success_count,
            'error_count': error_count,
            'results': results
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def mark_unavailable(self, request):
        """
        Mark a specific variant as unavailable.
        
        POST /api/products/staff/validation/mark_unavailable/
        
        Request body:
        {
            "validation_code": "ABC123",
            "variant_index": 0,
            "reason": "Out of stock"
        }
        """
        validation_code = request.data.get('validation_code', '').strip().upper()
        variant_index = request.data.get('variant_index')
        reason = request.data.get('reason', '')
        
        if not validation_code:
            return Response({
                'success': False,
                'error': 'Validation code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if variant_index is None:
            return Response({
                'success': False,
                'error': 'Variant index is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            marker_name = request.user.get_full_name() or request.user.username
            
            result = ProductPaymentService.mark_variant_unavailable(
                validation_code=validation_code,
                variant_index=int(variant_index),
                reason=reason,
                marked_by=marker_name
            )
            
            return Response({
                'success': True,
                'message': 'Variant marked as unavailable',
                **result
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Staff mark unavailable error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def bulk_lookup(self, request):
        """
        Look up multiple validation codes at once.
        Useful for staff to check a batch of codes before processing.
        
        POST /api/products/staff/validation/bulk_lookup/
        
        Request body:
        {
            "validation_codes": ["ABC123", "DEF456", "GHI789"]
        }
        
        Returns status for each code.
        """
        validation_codes = request.data.get('validation_codes', [])
        
        if not validation_codes:
            return Response({
                'success': False,
                'error': 'At least one validation code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(validation_codes) > 50:
            return Response({
                'success': False,
                'error': 'Maximum 50 validation codes per bulk lookup'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        results = []
        
        for code in validation_codes:
            code = code.strip().upper()
            if not code or len(code) != 6:
                results.append({
                    'validation_code': code,
                    'success': False,
                    'error': 'Invalid validation code format'
                })
                continue
            
            try:
                collection_status = ProductPaymentService.get_collection_status(code)
                
                if not collection_status.get('payment_successful'):
                    results.append({
                        'validation_code': code,
                        'success': False,
                        'error': 'Payment not successful'
                    })
                else:
                    results.append({
                        'validation_code': code,
                        'success': True,
                        'customer_name': collection_status.get('customer_name'),
                        'product_name': collection_status.get('product_name'),
                        'quantity': collection_status.get('quantity'),
                        'amount_paid': collection_status.get('amount_paid'),
                        'collection_summary': collection_status.get('collection_summary'),
                        'merchandise_taken': collection_status.get('merchandise_taken'),
                        'formatted_collection_details': collection_status.get('formatted_collection_details')
                    })
            except ValueError as e:
                results.append({
                    'validation_code': code,
                    'success': False,
                    'error': str(e)
                })
            except Exception as e:
                logger.error(f"Bulk lookup error for {code}: {str(e)}")
                results.append({
                    'validation_code': code,
                    'success': False,
                    'error': 'Lookup failed'
                })
        
        # Summary statistics
        valid_count = sum(1 for r in results if r['success'])
        pending_count = sum(1 for r in results if r['success'] and r.get('collection_summary', {}).get('overall_status') == 'pending')
        collected_count = sum(1 for r in results if r['success'] and r.get('collection_summary', {}).get('overall_status') == 'collected')
        
        return Response({
            'success': True,
            'total_codes': len(validation_codes),
            'valid_count': valid_count,
            'pending_count': pending_count,
            'collected_count': collected_count,
            'results': results
        }, status=status.HTTP_200_OK)


