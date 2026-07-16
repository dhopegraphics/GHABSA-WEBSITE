"""
El Mercado Seller Dashboard Views
=================================
Custom views for seller dashboard forms that need special handling.
Includes separate seller authentication system (independent from Django users).
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Q
from django.db.models.functions import TruncDate
from decimal import Decimal
from datetime import timedelta
from collections import defaultdict
from functools import wraps
import logging

from .models import (
    Seller, SellerPayoutAccount, PayoutRequest, SellerWallet,
    Conversation, Message, MarketplaceOrder, WalletTransaction
)

logger = logging.getLogger(__name__)


# =============================================================================
# SELLER SESSION MANAGEMENT
# =============================================================================

SELLER_SESSION_KEY = 'seller_id'
SELLER_SESSION_HASH_KEY = 'seller_session_hash'


def get_current_seller(request):
    """
    Get the currently logged in seller from session.
    Returns None if no seller is logged in.
    """
    seller_id = request.session.get(SELLER_SESSION_KEY)
    if not seller_id:
        return None
    
    try:
        seller = Seller.objects.get(id=seller_id)
        # Verify session hash to prevent session fixation
        stored_hash = request.session.get(SELLER_SESSION_HASH_KEY)
        expected_hash = _get_seller_session_hash(seller)
        if stored_hash != expected_hash:
            # Session might be compromised, clear it
            seller_logout(request)
            return None
        return seller
    except Seller.DoesNotExist:
        # Seller was deleted, clear session
        seller_logout(request)
        return None


def _get_seller_session_hash(seller):
    """Generate a hash for session validation"""
    import hashlib
    data = f"{seller.id}{seller.password[:20]}{seller.email}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]


def seller_login(request, seller):
    """
    Log in a seller by setting session data.
    This is separate from Django's auth system.
    """
    request.session[SELLER_SESSION_KEY] = str(seller.id)
    request.session[SELLER_SESSION_HASH_KEY] = _get_seller_session_hash(seller)
    request.session.modified = True
    logger.info(f"Seller {seller.display_name} logged in")


def seller_logout(request):
    """Log out the current seller"""
    seller_id = request.session.get(SELLER_SESSION_KEY)
    if seller_id:
        logger.info(f"Seller {seller_id} logged out")
    request.session.pop(SELLER_SESSION_KEY, None)
    request.session.pop(SELLER_SESSION_HASH_KEY, None)
    request.session.modified = True


def seller_auth_required(view_func):
    """
    Decorator to ensure request has an authenticated seller.
    Uses the separate seller auth system, NOT Django's auth.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        seller = get_current_seller(request)
        if not seller:
            messages.error(request, "Please log in to access the seller dashboard.")
            return redirect('el_mercado:seller_login')
        if seller.status != 'ACTIVE':
            messages.error(request, "Your seller account is not active.")
            seller_logout(request)
            return redirect('el_mercado:seller_login')
        # Attach seller to request for easy access
        request.seller = seller
        return view_func(request, *args, **kwargs)
    return wrapper


# =============================================================================
# SELLER AUTHENTICATION VIEWS
# =============================================================================

def seller_login_view(request):
    """
    Seller login page - separate from Django admin login.
    Uses seller's email/phone and password.
    """
    # If already logged in, redirect to dashboard
    if get_current_seller(request):
        return redirect('seller_admin:index')
    
    if request.method == 'POST':
        email_or_phone = request.POST.get('email_or_phone', '').strip()
        password = request.POST.get('password', '')
        
        if not email_or_phone or not password:
            messages.error(request, "Please enter both email/phone and password.")
            return render(request, 'el_mercado/seller_login.html')
        
        # Authenticate using seller's credentials
        seller, error = Seller.authenticate(email_or_phone, password)
        
        if seller:
            seller_login(request, seller)
            
            # Check if password needs to be changed (first login)
            if not seller.is_credentials_set:
                messages.info(request, "Please change your temporary password.")
                return redirect('el_mercado:seller_change_password')
            
            messages.success(request, f"Welcome back, {seller.display_name}!")
            
            # Redirect to intended page or dashboard
            next_url = request.GET.get('next', request.POST.get('next', ''))
            if next_url:
                return redirect(next_url)
            return redirect('seller_admin:index')
        else:
            messages.error(request, error)
    
    return render(request, 'el_mercado/seller_login.html')


def seller_logout_view(request):
    """Log out the seller and redirect to login page"""
    seller_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('el_mercado:seller_login')


@seller_auth_required
def seller_change_password_view(request):
    """Allow seller to change their password"""
    seller = request.seller
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # For first login, current password is the temp password
        is_first_login = not seller.is_credentials_set
        
        # Validate current password (skip for first login with temp password)
        if not is_first_login and not seller.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return render(request, 'el_mercado/seller_change_password.html', {
                'is_first_login': is_first_login
            })
        
        # Validate new password
        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'el_mercado/seller_change_password.html', {
                'is_first_login': is_first_login
            })
        
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'el_mercado/seller_change_password.html', {
                'is_first_login': is_first_login
            })
        
        # Set new password
        seller.set_password(new_password)
        seller.save()
        
        # Re-login with new session hash
        seller_login(request, seller)
        
        messages.success(request, "Password changed successfully!")
        return redirect('seller_admin:index')
    
    return render(request, 'el_mercado/seller_change_password.html', {
        'is_first_login': not seller.is_credentials_set
    })


def seller_forgot_password_view(request):
    """Handle password reset request"""
    if request.method == 'POST':
        email_or_phone = request.POST.get('email_or_phone', '').strip()
        
        if not email_or_phone:
            messages.error(request, "Please enter your email or phone number.")
            return render(request, 'el_mercado/seller_forgot_password.html')
        
        # Find seller
        try:
            seller = Seller.objects.get(
                Q(email__iexact=email_or_phone) | Q(phone=email_or_phone)
            )
        except Seller.DoesNotExist:
            # Don't reveal if account exists
            messages.success(
                request, 
                "If an account exists with that email/phone, "
                "you will receive a password reset link."
            )
            return render(request, 'el_mercado/seller_forgot_password.html')
        except Seller.MultipleObjectsReturned:
            messages.error(request, "Please contact support for assistance.")
            return render(request, 'el_mercado/seller_forgot_password.html')
        
        # Generate reset token
        token = seller.generate_password_reset_token()
        
        # Send reset email
        reset_url = request.build_absolute_uri(
            f'/el-mercado/seller/reset-password/{token}/'
        )
        
        try:
            from django.core.mail import send_mail
            send_mail(
                subject='El Mercado - Password Reset Request',
                message=(
                    f"Hi {seller.display_name},\n\n"
                    f"We received a request to reset your password.\n\n"
                    f"Click the link below to reset your password:\n"
                    f"{reset_url}\n\n"
                    f"This link will expire in 24 hours.\n\n"
                    f"If you didn't request this, please ignore this email.\n\n"
                    f"El Mercado Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[seller.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
        
        messages.success(
            request, 
            "If an account exists with that email/phone, "
            "you will receive a password reset link."
        )
        return redirect('el_mercado:seller_login')
    
    return render(request, 'el_mercado/seller_forgot_password.html')


def seller_reset_password_view(request, token):
    """Handle password reset with token"""
    # Find seller with valid token
    seller = None
    for s in Seller.objects.filter(password_reset_token=token):
        if s.is_password_reset_token_valid(token):
            seller = s
            break
    
    if not seller:
        messages.error(request, "Invalid or expired reset link. Please request a new one.")
        return redirect('el_mercado:seller_forgot_password')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'el_mercado/seller_reset_password.html', {'token': token})
        
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'el_mercado/seller_reset_password.html', {'token': token})
        
        # Set new password
        seller.set_password(new_password)
        seller.save()
        
        messages.success(request, "Password reset successfully! Please log in.")
        return redirect('el_mercado:seller_login')
    
    return render(request, 'el_mercado/seller_reset_password.html', {'token': token})


# =============================================================================
# LEGACY DECORATOR (for backwards compatibility with existing views)
# =============================================================================

def seller_required(view_func):
    """
    Decorator to ensure user is an active seller.
    This is the LEGACY decorator that uses Django's user authentication.
    For new views, use @seller_auth_required instead.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # First try the new seller auth system
        seller = get_current_seller(request)
        if seller:
            request.seller = seller
            if seller.status != 'ACTIVE':
                messages.error(request, "Your seller account is not active.")
                return redirect('el_mercado:seller_login')
            return view_func(request, *args, **kwargs)
        
        # Fall back to Django user auth (legacy)
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access the seller dashboard.")
            return redirect('el_mercado:seller_login')
        
        if not hasattr(request.user, 'seller_profile'):
            messages.error(request, "You don't have a seller account.")
            return redirect('seller_admin:index')
        if request.user.seller_profile.status != 'ACTIVE':
            messages.error(request, "Your seller account is not active.")
            return redirect('seller_admin:index')
        
        request.seller = request.user.seller_profile
        return view_func(request, *args, **kwargs)
    return wrapper


@seller_auth_required
def add_payout_account(request):
    """Handle payout account creation with custom form"""
    seller = request.seller
    
    if request.method == 'POST':
        account_type = request.POST.get('account_type', 'bank').upper()
        is_primary = request.POST.get('is_primary') == 'on'
        
        try:
            if account_type == 'BANK':
                bank_name = request.POST.get('bank_name', '')
                account_number = request.POST.get('account_number', '')
                account_holder_name = request.POST.get('account_holder_name', '')
                branch = request.POST.get('branch', '')
                
                # Map bank codes
                bank_codes = {
                    'gcb': 'GCB',
                    'ecobank': 'ECO',
                    'stanbic': 'STB',
                    'fidelity': 'FID',
                    'absa': 'ABS',
                    'calbank': 'CAL',
                    'uba': 'UBA',
                    'zenith': 'ZEN',
                    'access': 'ACC',
                    'prudential': 'PRU',
                    'gtbank': 'GTB',
                    'other': 'OTH',
                }
                
                bank_names = {
                    'gcb': 'Ghana Commercial Bank',
                    'ecobank': 'Ecobank Ghana',
                    'stanbic': 'Stanbic Bank',
                    'fidelity': 'Fidelity Bank',
                    'absa': 'Absa Bank Ghana',
                    'calbank': 'CalBank',
                    'uba': 'United Bank for Africa',
                    'zenith': 'Zenith Bank',
                    'access': 'Access Bank',
                    'prudential': 'Prudential Bank',
                    'gtbank': 'GT Bank',
                    'other': bank_name or 'Other',
                }
                
                if not bank_name or not account_number or not account_holder_name:
                    messages.error(request, "Please fill in all required fields.")
                    return redirect('seller_admin:el_mercado_sellerpayoutaccount_add')
                
                account = SellerPayoutAccount.objects.create(
                    seller=seller,
                    account_type='BANK',
                    bank_name=bank_names.get(bank_name, bank_name),
                    bank_code=bank_codes.get(bank_name, ''),
                    account_number=account_number,
                    account_name=account_holder_name,
                    is_default=is_primary,
                )
                
            else:  # MOBILE_MONEY
                momo_provider = request.POST.get('momo_provider', '')
                momo_number = request.POST.get('momo_number', '')
                momo_name = request.POST.get('momo_name', '')
                
                provider_names = {
                    'mtn': 'MTN Mobile Money',
                    'vodafone': 'Vodafone Cash',
                    'airteltigo': 'AirtelTigo Money',
                }
                
                if not momo_provider or not momo_number or not momo_name:
                    messages.error(request, "Please fill in all required fields.")
                    return redirect('seller_admin:el_mercado_sellerpayoutaccount_add')
                
                account = SellerPayoutAccount.objects.create(
                    seller=seller,
                    account_type='MOBILE_MONEY',
                    mobile_money_provider=provider_names.get(momo_provider, momo_provider),
                    mobile_money_number=momo_number,
                    mobile_money_name=momo_name,
                    is_default=is_primary,
                )
            
            messages.success(request, f"Payout account added successfully!")
            return redirect('seller_admin:el_mercado_sellerpayoutaccount_changelist')
            
        except Exception as e:
            messages.error(request, f"Error adding account: {str(e)}")
            return redirect('seller_admin:el_mercado_sellerpayoutaccount_add')
    
    # GET request - handled by admin template
    return redirect('seller_admin:el_mercado_sellerpayoutaccount_add')


@seller_auth_required
@require_POST
def set_primary_payout_account(request, account_id):
    """Set a payout account as the primary/default account"""
    seller = request.seller
    
    try:
        # Get the account (must belong to this seller)
        account = SellerPayoutAccount.objects.get(id=account_id, seller=seller)
        
        # Unset all other accounts as default
        SellerPayoutAccount.objects.filter(seller=seller).update(is_default=False)
        
        # Set this account as default
        account.is_default = True
        account.save(update_fields=['is_default'])
        
        account_name = account.account_name or account.mobile_money_name or "Account"
        messages.success(request, f"'{account_name}' is now your primary payout account.")
        
    except SellerPayoutAccount.DoesNotExist:
        messages.error(request, "Account not found.")
    except Exception as e:
        messages.error(request, f"Error setting primary account: {str(e)}")
    
    return redirect('seller_admin:el_mercado_sellerpayoutaccount_changelist')


@seller_auth_required
@require_POST
def cancel_payout_request(request, payout_id):
    """Cancel a pending payout request and restore wallet balance"""
    seller = request.seller
    
    try:
        # Get the payout (must belong to this seller)
        payout = PayoutRequest.objects.get(id=payout_id, wallet__seller=seller)
        
        if payout.status != 'PENDING':
            messages.error(request, "Only pending payout requests can be cancelled.")
            return redirect('seller_admin:el_mercado_payoutrequest_changelist')
        
        # Get the wallet
        wallet = payout.wallet
        
        # Restore the amount to available balance
        wallet.available_balance += payout.amount
        wallet.save(update_fields=['available_balance', 'updated_at'])
        
        # Create wallet transaction record for the refund
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='PAYOUT_REFUND',
            amount=payout.amount,  # Positive for credit
            description=f'Cancelled payout request {payout.reference} - funds returned',
            balance_after=wallet.available_balance
        )
        
        # Update payout status
        payout.status = 'CANCELLED'
        payout.status_message = 'Cancelled by seller'
        payout.save(update_fields=['status', 'status_message', 'updated_at'])
        
        messages.success(request, f"Payout request {payout.reference} cancelled. GH₵{payout.amount} has been returned to your available balance.")
        
    except PayoutRequest.DoesNotExist:
        messages.error(request, "Payout request not found.")
    except Exception as e:
        logger.error(f"Error cancelling payout request: {e}")
        messages.error(request, f"Error cancelling payout: {str(e)}")
    
    return redirect('seller_admin:el_mercado_payoutrequest_changelist')


@seller_auth_required
def request_payout(request):
    """Handle payout request creation"""
    seller = request.seller
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            account_id = request.POST.get('payout_account')
            
            # Validate amount
            wallet = seller.wallet
            min_payout = Decimal('50.00')
            
            if amount < min_payout:
                messages.error(request, f"Minimum payout amount is GH₵{min_payout}")
                return redirect('seller_admin:el_mercado_payoutrequest_add')
            
            if amount > wallet.available_balance:
                messages.error(request, "Insufficient available balance.")
                return redirect('seller_admin:el_mercado_payoutrequest_add')
            
            # Get payout account
            try:
                account = SellerPayoutAccount.objects.get(id=account_id, seller=seller)
            except SellerPayoutAccount.DoesNotExist:
                messages.error(request, "Please select a valid payout account.")
                return redirect('seller_admin:el_mercado_payoutrequest_add')
            
            # Calculate processing fee from settings
            from el_mercado.models import MarketplaceSettings
            settings = MarketplaceSettings.get_settings()
            fee_percentage = settings.payout_processing_fee_percentage / Decimal('100')
            processing_fee = (amount * fee_percentage).quantize(Decimal('0.01'))
            net_amount = amount - processing_fee
            
            # Create payout request
            payout = PayoutRequest.objects.create(
                wallet=wallet,
                amount=amount,
                processing_fee=processing_fee,
                net_amount=net_amount,
                currency='GHS',
                payout_method=account.account_type,
            )
            
            # Copy account details to payout
            if account.account_type == 'BANK':
                payout.bank_name = account.bank_name
                payout.bank_code = account.bank_code
                payout.account_number = account.account_number
                payout.account_name = account.account_name
            else:
                payout.mobile_money_provider = account.mobile_money_provider
                payout.mobile_money_number = str(account.mobile_money_number)
                payout.account_name = account.mobile_money_name
            
            payout.save()
            
            # Deduct full amount from available balance
            wallet.available_balance -= amount
            wallet.save(update_fields=['available_balance', 'updated_at'])
            
            # Create wallet transaction record
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='PAYOUT_HOLD',
                amount=-amount,  # Negative for deduction
                description=f'Payout request {payout.reference} (Net: GH₵{net_amount} after GH₵{processing_fee} fee)',
                balance_after=wallet.available_balance
            )
            
            messages.success(request, f"Payout request submitted! You will receive GH₵{net_amount} (GH₵{amount} - GH₵{processing_fee} processing fee)")
            return redirect('seller_admin:el_mercado_payoutrequest_changelist')
            
        except (ValueError, TypeError) as e:
            messages.error(request, "Please enter a valid amount.")
            return redirect('seller_admin:el_mercado_payoutrequest_add')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('seller_admin:el_mercado_payoutrequest_add')
    
    return redirect('seller_admin:el_mercado_payoutrequest_add')


@seller_auth_required
def pause_store(request):
    """Toggle vacation mode for seller's store"""
    if request.method == 'POST':
        seller = request.seller
        vacation_message = request.POST.get('vacation_message', '')
        
        seller.vacation_mode = not seller.vacation_mode
        if seller.vacation_mode:
            seller.vacation_message = vacation_message
            messages.success(request, "Your store has been paused. Customers won't see your listings.")
        else:
            seller.vacation_message = ''
            messages.success(request, "Your store is now active again!")
        
        seller.save()
        
    return redirect('seller_admin:el_mercado_seller_changelist')


@seller_auth_required
@require_POST
def toggle_auto_accept(request):
    """Toggle auto-accept orders setting for seller"""
    seller = request.seller
    seller.auto_accept_orders = not seller.auto_accept_orders
    seller.save(update_fields=['auto_accept_orders', 'updated_at'])
    
    if seller.auto_accept_orders:
        messages.success(request, "Auto-accept orders is now enabled. New paid orders will be automatically accepted.")
    else:
        messages.info(request, "Auto-accept orders is now disabled. You will need to manually accept each order.")
    
    return redirect('seller_admin:el_mercado_seller_changelist')


@seller_auth_required
def delete_store_request(request):
    """Request store deletion (soft delete / deactivation)"""
    if request.method == 'POST':
        seller = request.seller
        confirmation = request.POST.get('confirmation', '')
        
        if confirmation.lower() == seller.display_name.lower():
            # Soft delete - set status to inactive and clear data
            seller.status = 'INACTIVE'
            seller.status_reason = 'Store deleted by owner'
            seller.save()
            
            # Deactivate all listings
            seller.listings.update(status='ARCHIVED')
            
            messages.warning(request, "Your store has been deactivated. Contact support to fully delete your account.")
            return redirect('seller_admin:index')
        else:
            messages.error(request, "Store name confirmation didn't match. Deletion cancelled.")
    
    return redirect('seller_admin:el_mercado_seller_changelist')


@seller_auth_required
@require_POST
def send_message(request, conversation_id):
    """Send a message as a seller in a conversation"""
    seller = request.seller
    
    # Get the conversation (must belong to this seller)
    conversation = get_object_or_404(
        Conversation, 
        id=conversation_id, 
        seller=seller
    )
    
    message_content = request.POST.get('message', '').strip()
    
    if not message_content:
        messages.error(request, "Please enter a message.")
        return redirect('seller_admin:el_mercado_conversation_change', conversation.pk)
    
    try:
        # Get Django user if authenticated, otherwise None
        sender_user = request.user if request.user.is_authenticated else None
        
        # Create the message
        Message.objects.create(
            conversation=conversation,
            sender_type='SELLER',
            sender_user=sender_user,
            content=message_content,
            is_read=False
        )
        
        # Update conversation last message time
        conversation.last_message_at = timezone.now()
        
        # Increment buyer unread count
        conversation.buyer_unread_count += 1
        
        # Reset seller unread count (seller has seen and replied)
        conversation.seller_unread_count = 0
        
        conversation.save()
        
        messages.success(request, "Message sent successfully!")
        
    except Exception as e:
        messages.error(request, f"Failed to send message: {str(e)}")
    
    return redirect('seller_admin:el_mercado_conversation_change', conversation.pk)


@seller_auth_required
def get_conversation_messages(request, conversation_id):
    """Get messages for a conversation as JSON (for AJAX loading)"""
    seller = request.seller
    
    # Get the conversation (must belong to this seller)
    conversation = get_object_or_404(
        Conversation, 
        id=conversation_id, 
        seller=seller
    )
    
    # Mark messages as read
    conversation.seller_unread_count = 0
    conversation.save(update_fields=['seller_unread_count'])
    conversation.messages.filter(sender_type='BUYER', is_read=False).update(
        is_read=True, 
        read_at=timezone.now()
    )
    
    # Get all messages
    messages_list = conversation.messages.all().order_by('created_at')
    
    # Serialize messages
    data = []
    for msg in messages_list:
        data.append({
            'id': str(msg.id),
            'sender_type': msg.sender_type,
            'content': msg.content,
            'created_at': msg.created_at.isoformat(),
            'is_read': msg.is_read,
        })
    
    return JsonResponse({'messages': data})


@seller_auth_required
def start_conversation_with_customer(request, order_id):
    """
    Start or find a conversation with the customer for a specific order.
    If a conversation with this buyer already exists (with or without order link), redirect to it.
    Otherwise, create a new conversation linked to the order.
    """
    seller = request.seller
    
    # Get the order (must belong to this seller)
    order = get_object_or_404(
        MarketplaceOrder,
        id=order_id,
        seller=seller
    )
    
    buyer = order.buyer
    
    # Check if a conversation already exists between this seller and buyer
    # First, check if there's one linked to this order
    conversation = Conversation.objects.filter(
        seller=seller,
        buyer=buyer,
        order=order
    ).first()
    
    if not conversation:
        # Check for any conversation with this buyer (could be from a listing inquiry)
        conversation = Conversation.objects.filter(
            seller=seller,
            buyer=buyer
        ).first()
        
        if conversation:
            # Link the order to the existing conversation if not already linked
            if not conversation.order:
                conversation.order = order
                conversation.save(update_fields=['order', 'updated_at'])
    
    if not conversation:
        # Create a new conversation linked to this order
        # Get the first listing from the order items if available
        first_item = order.items.first()
        listing = first_item.listing if first_item else None
        
        conversation = Conversation.objects.create(
            seller=seller,
            buyer=buyer,
            listing=listing,
            order=order,
            last_message_at=timezone.now()
        )
        
        # Create a system message to indicate the conversation was started about an order
        Message.objects.create(
            conversation=conversation,
            sender_type='SYSTEM',
            content=f"Conversation started regarding Order #{order.order_number}",
            is_read=True
        )
        
        messages.success(request, f"Started conversation about Order #{order.order_number}")
    
    # Redirect to the conversation detail page
    return redirect('seller_admin:el_mercado_conversation_change', conversation.pk)


# =============================================================================
# ORDER STATUS UPDATE VIEWS
# =============================================================================

@seller_auth_required
@require_POST
def accept_order(request, order_id):
    """Accept a pending/paid order"""
    seller = request.seller
    
    order = get_object_or_404(
        MarketplaceOrder,
        id=order_id,
        seller=seller
    )
    
    # Can only accept PAID or PENDING orders
    if order.status not in ['PAID', 'PENDING']:
        messages.error(request, f"Cannot accept order with status '{order.get_status_display()}'. Only paid or pending orders can be accepted.")
        return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)
    
    try:
        order.update_status('PROCESSING', 'Accepted by seller')
        
        # Add to seller's pending balance if paid
        if order.payment_status == 'PAID':
            try:
                order.seller.wallet.add_pending(order.seller_earnings, f"Order {order.order_number}")
            except Exception:
                pass  # Wallet might not exist yet
        
        messages.success(request, f"Order #{order.order_number} has been accepted and is now being processed.")
    except Exception as e:
        messages.error(request, f"Failed to accept order: {str(e)}")
    
    return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)


@seller_auth_required
@require_POST
def decline_order(request, order_id):
    """Decline/cancel an order"""
    from el_mercado.services import MarketplacePaymentService
    
    seller = request.seller
    
    order = get_object_or_404(
        MarketplaceOrder,
        id=order_id,
        seller=seller
    )
    
    # Can only decline orders that haven't been shipped
    if order.status in ['SHIPPED', 'DELIVERED', 'COMPLETED']:
        messages.error(request, f"Cannot decline order that has already been {order.get_status_display().lower()}.")
        return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)
    
    decline_reason = request.POST.get('decline_reason', 'Declined by seller')
    
    try:
        # If order was paid, process refund
        if order.payment_status == 'PAID':
            # Get Django user if authenticated for logging purposes
            initiated_by_user = request.user if request.user.is_authenticated else None
            
            refund_result = MarketplacePaymentService.process_refund(
                order=order,
                reason=decline_reason,
                initiated_by=initiated_by_user
            )
            
            if not refund_result.success:
                messages.error(request, f"Failed to process refund: {refund_result.message}")
                return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)
            
            # Restore stock (refund service handles this too, but ensure it happens)
            MarketplacePaymentService._restore_stock(order)
            
            # Remove pending balance from wallet
            wallet = order.seller.wallet
            if order.total_amount > 0:
                # Deduct the pending amount that was added when order was created
                wallet.pending_balance -= order.seller_earnings
                wallet.save(update_fields=['pending_balance'])
                
                # Log transaction
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='REFUND_DEDUCT',
                    amount=-order.seller_earnings,
                    description=f"Order {order.order_number} declined - pending funds removed",
                    balance_after=wallet.available_balance
                )
            
            messages.success(request, f"Order #{order.order_number} has been declined and refund processed.")
        else:
            # Order not yet paid, just cancel
            order.update_status('CANCELLED', decline_reason)
            messages.warning(request, f"Order #{order.order_number} has been cancelled.")
            
    except Exception as e:
        logger.error(f"Failed to decline order {order_id}: {str(e)}")
        messages.error(request, f"Failed to decline order: {str(e)}")
    
    return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)


@seller_auth_required
@require_POST
def ship_order(request, order_id):
    """Mark an order as shipped"""
    seller = request.seller
    
    order = get_object_or_404(
        MarketplaceOrder,
        id=order_id,
        seller=seller
    )
    
    if order.status != 'PROCESSING':
        messages.error(request, f"Cannot ship order with status '{order.get_status_display()}'. Only processing orders can be shipped.")
        return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)
    
    tracking_number = request.POST.get('tracking_number', '').strip()
    tracking_url = request.POST.get('tracking_url', '').strip()
    shipping_carrier = request.POST.get('shipping_carrier', '').strip()
    
    try:
        order.tracking_number = tracking_number
        order.tracking_url = tracking_url
        order.shipped_at = timezone.now()
        
        # Save shipping carrier in notes if provided
        if shipping_carrier:
            current_notes = order.seller_notes or ''
            order.seller_notes = f"{current_notes}\nShipping carrier: {shipping_carrier}".strip()
        
        order.save(update_fields=['tracking_number', 'tracking_url', 'shipped_at', 'seller_notes'])
        order.update_status('SHIPPED', 'Shipped by seller')
        
        # Generate delivery verification code for the buyer
        delivery_code = order.generate_delivery_code()
        
        messages.success(request, f"Order #{order.order_number} has been marked as shipped.")
        messages.info(request, "A delivery verification code has been sent to the buyer. They must give you this code upon delivery to confirm receipt.")
        
        if tracking_number:
            messages.info(request, f"Tracking: {tracking_number}")
        
        # TODO: Send notification to buyer with the delivery code
            
    except Exception as e:
        messages.error(request, f"Failed to ship order: {str(e)}")
    
    return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)


@seller_auth_required
@require_POST
def verify_delivery(request, order_id):
    """Verify delivery using the buyer's code and complete the order"""
    seller = request.seller
    
    order = get_object_or_404(
        MarketplaceOrder,
        id=order_id,
        seller=seller
    )
    
    if order.status != 'SHIPPED':
        messages.error(request, f"Cannot verify delivery. Order status is '{order.get_status_display()}', must be 'Shipped'.")
        return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)
    
    delivery_code = request.POST.get('delivery_code', '').strip()
    
    if not delivery_code:
        messages.error(request, "Please enter the delivery verification code from the buyer.")
        return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)
    
    try:
        if order.verify_delivery_code(delivery_code):
            order.update_status('DELIVERED', 'Delivery verified with code by seller')
            messages.success(request, f"✅ Delivery verified! Order #{order.order_number} has been marked as delivered.")
            
            # Note: Funds will be released when admin/seller marks order as COMPLETED
            # This gives a window for any issues to be resolved before finalizing payment
            messages.info(request, "Order is now delivered. Mark as 'Completed' to release funds to your wallet.")
        else:
            messages.error(request, "❌ Invalid delivery code. Please ask the buyer for the correct 6-digit code.")
    except Exception as e:
        messages.error(request, f"Failed to verify delivery: {str(e)}")
    
    return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)


@seller_auth_required
@require_POST
def mark_delivered(request, order_id):
    """
    Mark an order as delivered WITHOUT code verification.
    This should only be used as a fallback when buyer confirms via other means.
    The preferred method is verify_delivery with the code.
    """
    seller = request.seller
    
    order = get_object_or_404(
        MarketplaceOrder,
        id=order_id,
        seller=seller
    )
    
    if order.status != 'SHIPPED':
        messages.error(request, f"Cannot mark as delivered. Order status is '{order.get_status_display()}', must be 'Shipped'.")
        return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)
    
    # Require delivery code verification
    messages.error(request, "Please use the delivery code verification. Ask the buyer for their 6-digit delivery code to confirm receipt.")
    return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)


@seller_auth_required
@require_POST
def complete_order(request, order_id):
    """
    Mark a delivered order as completed and release funds to seller.
    This is the final step after delivery confirmation.
    """
    seller = request.seller
    
    order = get_object_or_404(
        MarketplaceOrder,
        id=order_id,
        seller=seller
    )
    
    if order.status != 'DELIVERED':
        messages.error(request, f"Cannot complete order. Order status is '{order.get_status_display()}', must be 'Delivered'.")
        return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)
    
    if order.funds_released:
        messages.warning(request, "Funds have already been released for this order.")
        return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)
    
    try:
        # Release funds to seller wallet
        if order.release_funds():
            # Set completed timestamp
            from django.utils import timezone
            order.completed_at = timezone.now()
            order.save(update_fields=['completed_at'])
            
            order.update_status('COMPLETED', 'Order completed and funds released by seller')
            messages.success(request, f"✅ Order #{order.order_number} completed! GH₵{order.seller_earnings} has been released to your wallet.")
        else:
            messages.error(request, "Failed to release funds. Please contact support.")
    except Exception as e:
        messages.error(request, f"Failed to complete order: {str(e)}")
    
    return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)


@seller_auth_required
@require_POST
def save_order_notes(request, order_id):
    """Save seller notes for an order"""
    seller = request.seller
    
    order = get_object_or_404(
        MarketplaceOrder,
        id=order_id,
        seller=seller
    )
    
    seller_notes = request.POST.get('seller_notes', '').strip()
    
    try:
        order.seller_notes = seller_notes
        order.save(update_fields=['seller_notes'])
        messages.success(request, "Notes saved successfully.")
    except Exception as e:
        messages.error(request, f"Failed to save notes: {str(e)}")
    
    return redirect('seller_admin:el_mercado_marketplaceorder_change', order.pk)


# =============================================================================
# WALLET & TRANSACTION VIEWS
# =============================================================================

@seller_auth_required
def transaction_history(request):
    """View transaction history for seller's wallet"""
    seller = request.seller
    
    try:
        wallet = seller.wallet
        transactions = WalletTransaction.objects.filter(
            wallet=wallet
        ).order_by('-created_at')
        
        # Filter by type if provided
        tx_type = request.GET.get('type', 'all')
        if tx_type != 'all':
            transactions = transactions.filter(transaction_type=tx_type)
        
        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(transactions, 25)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context = {
            'wallet': wallet,
            'transactions': page_obj,
            'tx_type': tx_type,
            'transaction_types': WalletTransaction.TRANSACTION_TYPE_CHOICES,
            'title': 'Transaction History',
            'site_header': 'El Mercado - Seller Portal',
        }
        
        return render(request, 'seller_admin/el_mercado/wallet/transaction_history.html', context)
        
    except SellerWallet.DoesNotExist:
        messages.error(request, "Wallet not found.")
        return redirect('seller_admin:index')


@seller_auth_required
def payout_settings(request):
    """Manage payout settings including auto-payout"""
    seller = request.seller
    
    try:
        wallet = seller.wallet
    except SellerWallet.DoesNotExist:
        messages.error(request, "Wallet not found.")
        return redirect('seller_admin:index')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_settings':
            # Update auto-payout settings
            auto_payout_enabled = request.POST.get('auto_payout_enabled') == 'on'
            
            try:
                auto_payout_threshold = Decimal(request.POST.get('auto_payout_threshold', '500'))
                minimum_payout = Decimal(request.POST.get('minimum_payout_amount', '50'))
                
                # Validate
                if auto_payout_threshold < Decimal('100'):
                    messages.error(request, "Auto-payout threshold must be at least GH₵100")
                    return redirect('seller_admin:payout_settings')
                
                if minimum_payout < Decimal('50'):
                    messages.error(request, "Minimum payout must be at least GH₵50")
                    return redirect('seller_admin:payout_settings')
                
                wallet.auto_payout_enabled = auto_payout_enabled
                wallet.auto_payout_threshold = auto_payout_threshold
                wallet.minimum_payout_amount = minimum_payout
                wallet.save(update_fields=[
                    'auto_payout_enabled', 'auto_payout_threshold', 
                    'minimum_payout_amount', 'updated_at'
                ])
                
                if auto_payout_enabled:
                    messages.success(request, f"Auto-payout enabled! Payouts will be processed automatically when your balance reaches GH₵{auto_payout_threshold}")
                else:
                    messages.success(request, "Auto-payout disabled. You'll need to request payouts manually.")
                    
            except (ValueError, TypeError):
                messages.error(request, "Invalid amount entered.")
            
        elif action == 'set_default_account':
            account_id = request.POST.get('default_account')
            if account_id:
                # Unset all defaults
                SellerPayoutAccount.objects.filter(seller=seller).update(is_default=False)
                # Set new default
                SellerPayoutAccount.objects.filter(
                    id=account_id, seller=seller
                ).update(is_default=True)
                messages.success(request, "Default payout account updated.")
        
        return redirect('seller_admin:payout_settings')
    
    # GET request
    payout_accounts = SellerPayoutAccount.objects.filter(seller=seller).order_by('-is_default', '-created_at')
    
    context = {
        'wallet': wallet,
        'payout_accounts': payout_accounts,
        'title': 'Payout Settings',
        'site_header': 'El Mercado - Seller Portal',
    }
    
    return render(request, 'seller_admin/el_mercado/wallet/payout_settings.html', context)


@seller_auth_required
def earnings_chart_data(request):
    """
    API endpoint to fetch earnings data for charts.
    Returns daily earnings data for the specified period.
    """
    seller = request.seller
    wallet = getattr(seller, 'wallet', None)
    
    if not wallet:
        return JsonResponse({'error': 'No wallet found'}, status=404)
    
    # Get period from query params (default: 7 days)
    period = request.GET.get('period', '7')
    try:
        days = int(period)
        if days not in [7, 30, 90]:
            days = 7
    except (ValueError, TypeError):
        days = 7
    
    # Calculate date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    # Get transactions grouped by date
    transactions = WalletTransaction.objects.filter(
        wallet=wallet,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date', 'transaction_type', 'amount')
    
    # Initialize daily data
    daily_earnings = defaultdict(lambda: {'earnings': Decimal('0'), 'payouts': Decimal('0')})
    
    # Populate with actual data
    for txn in transactions:
        date_str = txn['date'].strftime('%Y-%m-%d')
        
        # Earnings: Only count CREDIT_PENDING (initial sale credit) and BONUS
        # Note: RELEASE just moves funds from pending to available, not a new earning
        if txn['transaction_type'] in ['CREDIT_PENDING', 'BONUS']:
            daily_earnings[date_str]['earnings'] += abs(txn['amount'])
        # Payouts/Withdrawals
        elif txn['transaction_type'] in ['WITHDRAWAL', 'PAYOUT_COMPLETE']:
            daily_earnings[date_str]['payouts'] += abs(txn['amount'])
    
    # Generate labels and data for all days in range
    labels = []
    earnings_data = []
    payouts_data = []
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Format label based on period length
        if days <= 7:
            label = current_date.strftime('%a')  # Mon, Tue, etc.
        elif days <= 30:
            label = current_date.strftime('%d %b')  # 01 Jan, 02 Jan, etc.
        else:
            label = current_date.strftime('%d/%m')  # 01/01, 02/01, etc.
        
        labels.append(label)
        earnings_data.append(float(daily_earnings[date_str]['earnings']))
        payouts_data.append(float(daily_earnings[date_str]['payouts']))
        
        current_date += timedelta(days=1)
    
    # Calculate totals for the period
    total_earnings = sum(earnings_data)
    total_payouts = sum(payouts_data)
    
    return JsonResponse({
        'labels': labels,
        'datasets': [
            {
                'label': 'Earnings',
                'data': earnings_data,
                'borderColor': '#7c3aed',
                'backgroundColor': 'rgba(124, 58, 237, 0.1)',
                'fill': True,
                'tension': 0.4,
            },
            {
                'label': 'Payouts',
                'data': payouts_data,
                'borderColor': '#ec4899',
                'backgroundColor': 'rgba(236, 72, 153, 0.1)',
                'fill': True,
                'tension': 0.4,
            }
        ],
        'summary': {
            'total_earnings': total_earnings,
            'total_payouts': total_payouts,
            'net': total_earnings - total_payouts,
            'period_days': days,
        }
    })


# =============================================================================
# REVIEW REPLY
# =============================================================================

@seller_auth_required
@require_POST
def reply_to_review(request, review_id):
    """Handle seller replying to a review"""
    from .models import Review
    
    seller = request.seller
    
    try:
        # Get review that belongs to this seller (either directly or via listing)
        review = Review.objects.filter(
            pk=review_id
        ).filter(
            Q(seller=seller) | Q(listing__seller=seller)
        ).first()
        
        if not review:
            return JsonResponse({
                'success': False,
                'error': 'Review not found or you do not have permission to reply.'
            }, status=404)
        
        response_text = request.POST.get('response', '').strip()
        
        if not response_text:
            return JsonResponse({
                'success': False,
                'error': 'Response cannot be empty.'
            }, status=400)
        
        review.seller_response = response_text
        review.seller_responded_at = timezone.now()
        review.save(update_fields=['seller_response', 'seller_responded_at'])
        
        return JsonResponse({
            'success': True,
            'message': 'Response submitted successfully!',
            'response': response_text,
            'responded_at': review.seller_responded_at.strftime('%b %d, %Y')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)