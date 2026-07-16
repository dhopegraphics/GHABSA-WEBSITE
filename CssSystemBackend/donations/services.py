"""
Donation Services
Handles donation payment processing, verification, and wallet management
Integrates with main payment system for unified transaction tracking
"""
import logging
import requests
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from .models import (
    DonationWallet,
    Donation,
    DonorProfile,
    DonationWithdrawal,
    DonationTransaction
)
from payments.models import Transaction as MainTransaction, Currency, PaymentGateway

logger = logging.getLogger(__name__)


class DonationService:
    """
    Service class for handling donation operations
    Integrated with main payment system for unified transaction tracking
    """
    
    PAYSTACK_SECRET_KEY = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    PAYSTACK_BASE_URL = 'https://api.paystack.co'
    
    @classmethod
    def get_headers(cls):
        """Get Paystack API headers"""
        return {
            'Authorization': f'Bearer {cls.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
    
    @classmethod
    def _create_main_transaction(cls, donation: Donation, gateway_data: dict):
        """
        Create a record in the main Transaction model for unified tracking.
        This allows admins/executives to see all transactions in one place.
        """
        try:
            # Get or create default currency (GHS)
            currency, _ = Currency.objects.get_or_create(
                code='GHS',
                defaults={
                    'name': 'Ghanaian Cedi',
                    'symbol': 'GH₵',
                    'is_active': True,
                    'is_base_currency': True
                }
            )
            
            # Get Paystack gateway (if exists)
            gateway = PaymentGateway.objects.filter(name='paystack').first()
            
            # Get content type for donation
            content_type = ContentType.objects.get_for_model(Donation)
            
            # Calculate fees from gateway response
            fees = gateway_data.get('fees', 0)
            gateway_fee = Decimal(str(fees / 100)) if fees else Decimal('0.00')
            
            # Create main transaction record
            # Use donation reference directly (already has DON- prefix)
            MainTransaction.objects.create(
                reference=donation.reference,
                user=donation.donor,
                transaction_type='donation',
                amount=donation.amount,
                currency=currency,
                gateway=gateway,
                status='success',
                content_type=content_type,
                object_id=str(donation.pk),
                description=f"Donation{' (Anonymous)' if donation.is_anonymous else f' from {donation.donor_name}'}: {donation.message[:100] if donation.message else 'Supporting student welfare'}",
                gateway_fee=gateway_fee,
                platform_fee=Decimal('0.00'),  # No platform fee for donations
                net_amount=donation.amount - gateway_fee,
                payment_method=gateway_data.get('channel', 'card'),
                payment_channel=gateway_data.get('channel', ''),
                gateway_reference=gateway_data.get('reference', donation.reference),
                gateway_response=str(gateway_data),
                gateway_metadata={
                    'donation_id': str(donation.id),
                    'is_anonymous': donation.is_anonymous,
                    'donor_email': donation.donor_email,
                },
                customer_email=donation.donor_email,
                customer_phone=donation.donor_phone,
                customer_name=donation.donor_name if not donation.is_anonymous else 'Anonymous Donor',
                ip_address=donation.ip_address,
                user_agent=donation.user_agent,
                completed_at=donation.completed_at,
                metadata={
                    'source': 'donations',
                    'donation_reference': donation.reference,
                    'welfare_fund': True,
                }
            )
            
            logger.info(f"Created main transaction for donation: {donation.reference}")
            
        except Exception as e:
            # Log error but don't fail the donation
            logger.error(f"Failed to create main transaction for donation {donation.reference}: {str(e)}")
    
    @classmethod
    def initialize_donation(
        cls,
        amount: Decimal,
        email: str,
        donor_name: str = "",
        phone: str = "",
        message: str = "",
        is_anonymous: bool = False,
        donor: 'CustomUser' = None,
        callback_url: str = None,
        ip_address: str = None,
        user_agent: str = ""
    ):
        """
        Initialize a donation payment with Paystack
        
        Args:
            amount: Donation amount in GHS
            email: Donor's email address
            donor_name: Name of the donor
            phone: Donor's phone number
            message: Optional donation message
            is_anonymous: Whether to hide donor identity publicly
            donor: CustomUser if logged in
            callback_url: URL to redirect after payment
            ip_address: Donor's IP address
            user_agent: Donor's user agent
            
        Returns:
            dict: {success: bool, donation: Donation, authorization_url: str, ...}
        """
        try:
            # If donor not provided, try to find user by email
            if not donor and email:
                from accounts.models import CustomUser
                # Check student_email first, then personal_email
                donor = CustomUser.objects.filter(student_email=email).first()
                if not donor:
                    donor = CustomUser.objects.filter(personal_email=email).first()
                if donor:
                    logger.info(f"Found existing user by email {email}: {donor.id}")
            
            # Create donation record
            donation = Donation.objects.create(
                donor=donor,
                donor_name=donor_name or (f"{donor.first_name} {donor.last_name}" if donor else ""),
                donor_email=email,
                donor_phone=phone,
                amount=amount,
                message=message,
                is_anonymous=is_anonymous,
                status='pending',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Prepare Paystack payload
            amount_kobo = int(amount * 100)  # Convert to pesewas
            
            payload = {
                'email': email,
                'amount': amount_kobo,
                'currency': 'GHS',
                'reference': donation.reference,
                'metadata': {
                    'donation_id': str(donation.id),
                    'donor_name': donor_name,
                    'is_anonymous': is_anonymous,
                    'message': message[:200] if message else "",
                    'type': 'donation',
                    'custom_fields': [
                        {
                            'display_name': 'Donation Type',
                            'variable_name': 'donation_type',
                            'value': 'CS Society Support'
                        },
                        {
                            'display_name': 'Donor Name',
                            'variable_name': 'donor_name',
                            'value': donor_name if not is_anonymous else 'Anonymous'
                        }
                    ]
                }
            }
            
            if callback_url:
                payload['callback_url'] = callback_url
            
            # Initialize transaction with Paystack
            response = requests.post(
                f'{cls.PAYSTACK_BASE_URL}/transaction/initialize',
                json=payload,
                headers=cls.get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status'):
                data = response_data.get('data', {})
                donation.gateway_reference = data.get('reference', '')
                donation.status = 'processing'
                donation.save()
                
                logger.info(f"Donation initialized: {donation.reference}")
                
                return {
                    'success': True,
                    'donation': donation,
                    'authorization_url': data.get('authorization_url'),
                    'access_code': data.get('access_code'),
                    'reference': donation.reference
                }
            else:
                donation.status = 'failed'
                donation.gateway_response = response_data
                donation.save()
                
                logger.error(f"Failed to initialize donation: {response_data}")
                
                return {
                    'success': False,
                    'error': response_data.get('message', 'Failed to initialize payment'),
                    'donation': donation
                }
                
        except requests.RequestException as e:
            logger.error(f"Network error initializing donation: {str(e)}")
            return {
                'success': False,
                'error': 'Network error. Please try again.'
            }
        except Exception as e:
            logger.error(f"Error initializing donation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    @transaction.atomic
    def verify_donation(cls, reference: str):
        """
        Verify a donation payment with Paystack
        
        Args:
            reference: Donation reference
            
        Returns:
            dict: {success: bool, donation: Donation, message: str, ...}
        """
        try:
            # Get donation record
            try:
                donation = Donation.objects.select_for_update().get(reference=reference)
            except Donation.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Donation not found'
                }
            
            # If already completed, return success
            if donation.status == 'completed':
                return {
                    'success': True,
                    'donation': donation,
                    'message': 'Donation already verified'
                }
            
            # Verify with Paystack
            response = requests.get(
                f'{cls.PAYSTACK_BASE_URL}/transaction/verify/{reference}',
                headers=cls.get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            donation.gateway_response = response_data
            
            if response.status_code == 200 and response_data.get('status'):
                data = response_data.get('data', {})
                paystack_status = data.get('status', '')
                
                if paystack_status == 'success':
                    # Payment successful - update donation and wallet
                    donation.status = 'completed'
                    donation.completed_at = timezone.now()
                    donation.gateway_reference = data.get('reference', '')
                    
                    # Try to link donor if not already linked (user might exist)
                    if not donation.donor and donation.donor_email:
                        from accounts.models import CustomUser
                        user = CustomUser.objects.filter(student_email=donation.donor_email).first()
                        if not user:
                            user = CustomUser.objects.filter(personal_email=donation.donor_email).first()
                        if user:
                            donation.donor = user
                            if not donation.donor_name:
                                donation.donor_name = f"{user.first_name} {user.last_name}"
                            logger.info(f"Linked donation {donation.reference} to existing user {user.id}")
                    
                    donation.save()
                    
                    # Check if this is a new donor and create/update donor profile
                    is_new_donor = False
                    if donation.donor:
                        donor_profile, created = DonorProfile.objects.get_or_create(
                            user=donation.donor
                        )
                        is_new_donor = created
                        donor_profile.add_donation(donation.amount)
                        logger.info(f"{'Created' if created else 'Updated'} DonorProfile for user {donation.donor.id}")
                    else:
                        # Check by email for truly guest donors (no matching user in system)
                        existing = Donation.objects.filter(
                            donor_email=donation.donor_email,
                            status='completed'
                        ).exclude(pk=donation.pk).exists()
                        is_new_donor = not existing
                    
                    # Add to donation wallet
                    wallet = DonationWallet.get_wallet()
                    balance_before = wallet.balance
                    wallet.add_donation(donation.amount, is_new_donor)
                    
                    # Create transaction record (internal donation ledger)
                    DonationTransaction.objects.create(
                        transaction_type='donation',
                        amount=donation.amount,
                        donation=donation,
                        balance_before=balance_before,
                        balance_after=wallet.balance,
                        description=f"Donation from {donation.get_display_name()}"
                    )
                    
                    # Also create a record in the MAIN Transaction model
                    # So admins/executives can see all transactions in one place
                    cls._create_main_transaction(donation, data)
                    
                    logger.info(f"Donation verified: {reference} - GH₵{donation.amount}")
                    
                    return {
                        'success': True,
                        'donation': donation,
                        'message': 'Donation successful! Thank you for your support.'
                    }
                else:
                    donation.status = 'failed'
                    donation.save()
                    
                    return {
                        'success': False,
                        'donation': donation,
                        'error': f'Payment {paystack_status}'
                    }
            else:
                donation.status = 'failed'
                donation.save()
                
                return {
                    'success': False,
                    'donation': donation,
                    'error': response_data.get('message', 'Verification failed')
                }
                
        except requests.RequestException as e:
            logger.error(f"Network error verifying donation: {str(e)}")
            return {
                'success': False,
                'error': 'Network error during verification'
            }
        except Exception as e:
            logger.error(f"Error verifying donation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    @transaction.atomic
    def process_withdrawal(
        cls,
        amount: Decimal,
        recipient_name: str,
        purpose: str,
        initiated_by: 'CustomUser',
        recipient_account: str = "",
        recipient_bank: str = "",
        description: str = "",
        category: str = "other",
        receipt_image=None,
        approved_by: 'CustomUser' = None,
        auto_complete: bool = True
    ):
        """
        Process a withdrawal from the donation wallet
        
        Args:
            amount: Withdrawal amount
            recipient_name: Name of the recipient
            purpose: Purpose of withdrawal
            initiated_by: Admin initiating the withdrawal
            recipient_account: Account number (optional)
            recipient_bank: Bank name (optional)
            description: Detailed description
            category: Expense category
            receipt_image: Receipt/proof image
            approved_by: Admin who approved
            auto_complete: Whether to auto-complete the withdrawal
            
        Returns:
            dict: {success: bool, withdrawal: DonationWithdrawal, ...}
        """
        try:
            # Get wallet
            wallet = DonationWallet.get_wallet()
            
            # Check balance
            if amount > wallet.balance:
                return {
                    'success': False,
                    'error': f'Insufficient balance. Available: GH₵{wallet.balance}'
                }
            
            balance_before = wallet.balance
            
            # Create withdrawal record
            withdrawal = DonationWithdrawal.objects.create(
                amount=amount,
                recipient_name=recipient_name,
                recipient_account=recipient_account,
                recipient_bank=recipient_bank,
                purpose=purpose,
                description=description,
                category=category,
                receipt_image=receipt_image,
                initiated_by=initiated_by,
                approved_by=approved_by or initiated_by,
                status='approved' if auto_complete else 'pending',
                balance_before=balance_before,
                balance_after=balance_before - amount,
                approved_at=timezone.now() if auto_complete else None
            )
            
            if auto_complete:
                # Deduct from wallet
                wallet.withdraw(amount)
                
                withdrawal.status = 'completed'
                withdrawal.completed_at = timezone.now()
                withdrawal.save()
                
                # Create transaction record
                DonationTransaction.objects.create(
                    transaction_type='withdrawal',
                    amount=amount,
                    withdrawal=withdrawal,
                    balance_before=balance_before,
                    balance_after=wallet.balance,
                    description=f"Withdrawal for: {purpose}",
                    performed_by=initiated_by
                )
            
            logger.info(f"Withdrawal processed: {withdrawal.reference} - GH₵{amount}")
            
            return {
                'success': True,
                'withdrawal': withdrawal,
                'message': 'Withdrawal processed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error processing withdrawal: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def get_public_statistics(cls):
        """
        Get public donation statistics for display
        
        Returns:
            dict: Donation statistics
        """
        wallet = DonationWallet.get_wallet()
        
        return {
            'total_balance': float(wallet.balance),
            'total_received': float(wallet.total_received),
            'total_withdrawn': float(wallet.total_withdrawn),
            'total_donations': wallet.total_donations_count,
            'total_donors': wallet.total_donors_count,
        }
    
    @classmethod
    def get_recent_donations(cls, limit: int = 20, include_anonymous: bool = True):
        """
        Get recent completed donations for public display
        
        Args:
            limit: Number of donations to return
            include_anonymous: Whether to include anonymous donations
            
        Returns:
            QuerySet: Recent donations
        """
        qs = Donation.objects.filter(status='completed')
        
        if not include_anonymous:
            qs = qs.filter(is_anonymous=False)
        
        return qs.order_by('-completed_at')[:limit]
    
    @classmethod
    def get_recent_withdrawals(cls, limit: int = 20):
        """
        Get recent completed withdrawals for public display
        
        Args:
            limit: Number of withdrawals to return
            
        Returns:
            QuerySet: Recent withdrawals
        """
        return DonationWithdrawal.objects.filter(
            status='completed'
        ).order_by('-completed_at')[:limit]
    
    # ==========================================
    # PAYSTACK TRANSFER METHODS
    # ==========================================
    
    # Bank codes for Paystack Ghana transfers
    PAYSTACK_BANK_CODES = {
        # Mobile Money
        'mtn': 'MTN',
        'vod': 'VOD',
        'atl': 'ATL',
        # Banks
        'gcb': 'GCB',
        'ecobank': 'ECO',
        'absa': 'ABB',
        'stanbic': 'STB',
        'uba': 'UBA',
        'fidelity': 'FID',
        'calbank': 'CAL',
        'zenith': 'ZEN',
        'access': 'ABG',
        'gt_bank': 'GTB',
        'prudential': 'PRU',
        'fnb': 'FNB',
        'republic': 'REP',
        'societe': 'SGG',
        'adb': 'ADB',
        'nib': 'NIB',
    }
    
    @classmethod
    def get_paystack_bank_code(cls, bank_code: str) -> str:
        """Get Paystack bank code from our internal code"""
        return cls.PAYSTACK_BANK_CODES.get(bank_code, bank_code)
    
    @classmethod
    def get_paystack_banks(cls):
        """
        Fetch list of supported banks from Paystack
        
        Returns:
            dict: {success: bool, banks: list}
        """
        try:
            response = requests.get(
                f'{cls.PAYSTACK_BASE_URL}/bank?country=ghana',
                headers=cls.get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status'):
                return {
                    'success': True,
                    'banks': response_data.get('data', [])
                }
            else:
                return {
                    'success': False,
                    'error': response_data.get('message', 'Failed to fetch banks')
                }
                
        except Exception as e:
            logger.error(f"Error fetching banks: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def create_transfer_recipient(
        cls,
        name: str,
        account_number: str,
        bank_code: str,
        recipient_type: str = "mobile_money"
    ):
        """
        Create a transfer recipient in Paystack
        
        Args:
            name: Recipient name
            account_number: Account/phone number
            bank_code: Bank or mobile money provider code
            recipient_type: 'mobile_money' or 'nuban' (bank account)
            
        Returns:
            dict: {success: bool, recipient_code: str, ...}
        """
        try:
            # Determine if mobile money or bank
            mobile_money_codes = ['MTN', 'VOD', 'ATL']
            paystack_bank_code = cls.get_paystack_bank_code(bank_code)
            
            if paystack_bank_code in mobile_money_codes:
                recipient_type = 'mobile_money'
            else:
                recipient_type = 'nuban'
            
            payload = {
                'type': recipient_type,
                'name': name,
                'account_number': account_number,
                'bank_code': paystack_bank_code,
                'currency': 'GHS'
            }
            
            response = requests.post(
                f'{cls.PAYSTACK_BASE_URL}/transferrecipient',
                json=payload,
                headers=cls.get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code in [200, 201] and response_data.get('status'):
                data = response_data.get('data', {})
                return {
                    'success': True,
                    'recipient_code': data.get('recipient_code'),
                    'details': data
                }
            else:
                return {
                    'success': False,
                    'error': response_data.get('message', 'Failed to create recipient')
                }
                
        except Exception as e:
            logger.error(f"Error creating transfer recipient: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    @transaction.atomic
    def initiate_gateway_transfer(
        cls,
        withdrawal: DonationWithdrawal,
        performed_by: 'CustomUser'
    ):
        """
        Initiate a gateway transfer for a withdrawal
        
        Args:
            withdrawal: DonationWithdrawal object
            performed_by: Admin performing the transfer
            
        Returns:
            dict: {success: bool, transfer_code: str, ...}
        """
        try:
            # Validate withdrawal status
            if withdrawal.status not in ['pending', 'approved']:
                return {
                    'success': False,
                    'error': f'Cannot process withdrawal with status: {withdrawal.status}'
                }
            
            # Check wallet balance
            wallet = DonationWallet.get_wallet()
            if withdrawal.amount > wallet.balance:
                return {
                    'success': False,
                    'error': f'Insufficient balance. Available: GH₵{wallet.balance}'
                }
            
            # Create transfer recipient if not exists
            if not withdrawal.gateway_recipient_code:
                recipient_result = cls.create_transfer_recipient(
                    name=withdrawal.recipient_name,
                    account_number=withdrawal.recipient_account,
                    bank_code=withdrawal.recipient_bank_code
                )
                
                if not recipient_result['success']:
                    withdrawal.status = 'failed'
                    withdrawal.status_message = f"Failed to create recipient: {recipient_result['error']}"
                    withdrawal.save()
                    return recipient_result
                
                withdrawal.gateway_recipient_code = recipient_result['recipient_code']
                withdrawal.save()
            
            # Initiate transfer
            amount_pesewas = int(withdrawal.amount * 100)
            
            payload = {
                'source': 'balance',
                'amount': amount_pesewas,
                'recipient': withdrawal.gateway_recipient_code,
                'reason': f"{withdrawal.purpose[:50]} - {withdrawal.reference}",
                'reference': withdrawal.reference,
                'currency': 'GHS'
            }
            
            response = requests.post(
                f'{cls.PAYSTACK_BASE_URL}/transfer',
                json=payload,
                headers=cls.get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            withdrawal.gateway_response = response_data
            
            if response.status_code in [200, 201] and response_data.get('status'):
                data = response_data.get('data', {})
                
                withdrawal.transfer_method = 'gateway'
                withdrawal.gateway_transfer_code = data.get('transfer_code', '')
                withdrawal.gateway_reference = data.get('reference', withdrawal.reference)
                withdrawal.status = 'processing'
                withdrawal.status_message = 'Transfer initiated, awaiting completion'
                withdrawal.approved_by = performed_by
                withdrawal.approved_at = timezone.now()
                
                # Record balance tracking (but DON'T deduct yet - wait for completion)
                # Funds will be deducted only when transfer is confirmed successful
                withdrawal.balance_before = wallet.balance
                withdrawal.balance_after = wallet.balance - withdrawal.amount  # Expected after completion
                withdrawal.save()
                
                logger.info(f"Gateway transfer initiated: {withdrawal.reference}")
                
                return {
                    'success': True,
                    'transfer_code': withdrawal.gateway_transfer_code,
                    'status': data.get('status'),
                    'message': 'Transfer initiated successfully'
                }
            else:
                withdrawal.status = 'failed'
                withdrawal.status_message = response_data.get('message', 'Transfer initiation failed')
                withdrawal.save()
                
                return {
                    'success': False,
                    'error': response_data.get('message', 'Transfer failed')
                }
                
        except Exception as e:
            logger.error(f"Error initiating gateway transfer: {str(e)}")
            withdrawal.status = 'failed'
            withdrawal.status_message = str(e)
            withdrawal.save()
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def finalize_transfer_with_otp(cls, withdrawal: DonationWithdrawal, otp: str):
        """
        Finalize a transfer that requires OTP verification.
        Paystack requires OTP for certain types of transfers.
        
        Args:
            withdrawal: DonationWithdrawal object with gateway_transfer_code
            otp: The OTP received via SMS/email
            
        Returns:
            dict: {success: bool, message: str, ...}
        """
        try:
            if not withdrawal.gateway_transfer_code:
                return {'success': False, 'error': 'No transfer code found'}
            
            # Call Paystack's finalize transfer endpoint
            payload = {
                'transfer_code': withdrawal.gateway_transfer_code,
                'otp': otp
            }
            
            response = requests.post(
                f'{cls.PAYSTACK_BASE_URL}/transfer/finalize_transfer',
                json=payload,
                headers=cls.get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            withdrawal.gateway_response = response_data
            
            if response.status_code in [200, 201] and response_data.get('status'):
                data = response_data.get('data', {})
                transfer_status = data.get('status', '').lower()
                
                if transfer_status in ['success', 'pending']:
                    # For pending, the transfer is being processed
                    if transfer_status == 'pending':
                        withdrawal.status_message = 'Transfer is being processed'
                        withdrawal.save()
                        return {
                            'success': True,
                            'message': 'OTP verified. Transfer is being processed.',
                            'status': 'pending'
                        }
                    
                    # For success, complete the transfer
                    result = cls.complete_gateway_transfer(
                        withdrawal=withdrawal,
                        transfer_status='success',
                        gateway_data=data
                    )
                    
                    return {
                        'success': True,
                        'message': 'Transfer completed successfully!',
                        'status': 'completed'
                    }
                else:
                    withdrawal.status = 'failed'
                    withdrawal.status_message = f'Transfer {transfer_status}'
                    withdrawal.save()
                    return {
                        'success': False,
                        'error': f'Transfer {transfer_status}',
                        'status': 'failed'
                    }
            else:
                error_msg = response_data.get('message', 'OTP verification failed')
                withdrawal.status_message = error_msg
                withdrawal.save()
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"Error finalizing transfer with OTP: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def verify_transfer(cls, transfer_code: str):
        """
        Verify the status of a transfer
        
        Args:
            transfer_code: Paystack transfer code
            
        Returns:
            dict: {success: bool, status: str, ...}
        """
        try:
            response = requests.get(
                f'{cls.PAYSTACK_BASE_URL}/transfer/{transfer_code}',
                headers=cls.get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status'):
                data = response_data.get('data', {})
                return {
                    'success': True,
                    'transfer_status': data.get('status'),
                    'amount': data.get('amount'),
                    'recipient': data.get('recipient'),
                    'details': data
                }
            else:
                return {
                    'success': False,
                    'error': response_data.get('message', 'Verification failed')
                }
                
        except Exception as e:
            logger.error(f"Error verifying transfer: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    @transaction.atomic
    def complete_gateway_transfer(
        cls,
        withdrawal: DonationWithdrawal,
        transfer_status: str,
        gateway_data: dict = None
    ):
        """
        Complete a gateway transfer based on webhook/verification
        
        Args:
            withdrawal: DonationWithdrawal object
            transfer_status: Status from gateway (success, failed, reversed)
            gateway_data: Additional data from gateway
        """
        try:
            if transfer_status == 'success':
                # NOW deduct from wallet (only on confirmed success)
                wallet = DonationWallet.get_wallet()
                
                # Verify we have sufficient balance
                if withdrawal.amount > wallet.balance:
                    logger.error(f"Insufficient balance for completed transfer: {withdrawal.reference}")
                    withdrawal.status = 'failed'
                    withdrawal.status_message = 'Insufficient wallet balance at completion'
                    withdrawal.save()
                    return {'success': False, 'error': 'Insufficient balance'}
                
                # Record balance before deduction
                balance_before = wallet.balance
                
                # Actually deduct from wallet
                wallet.withdraw(withdrawal.amount)
                
                # Update withdrawal with actual balances
                withdrawal.balance_before = balance_before
                withdrawal.balance_after = wallet.balance
                withdrawal.status = 'completed'
                withdrawal.completed_at = timezone.now()
                withdrawal.status_message = 'Transfer completed successfully'
                
                if gateway_data:
                    withdrawal.gateway_response = gateway_data
                    # Extract fee if available
                    fees = gateway_data.get('fees', 0)
                    if fees:
                        withdrawal.gateway_fee = Decimal(str(fees / 100))
                
                # Create transaction record
                DonationTransaction.objects.create(
                    transaction_type='withdrawal',
                    amount=withdrawal.amount,
                    withdrawal=withdrawal,
                    balance_before=balance_before,
                    balance_after=wallet.balance,
                    description=f"Gateway transfer: {withdrawal.purpose}",
                    performed_by=withdrawal.approved_by
                )
                
                logger.info(f"Gateway transfer completed: {withdrawal.reference}")
                
            elif transfer_status in ['failed', 'reversed']:
                # No need to refund - funds were never deducted (only deducted on success)
                withdrawal.status = 'failed'
                withdrawal.status_message = f'Transfer {transfer_status}'
                # Reset balance_after to same as before (no deduction occurred)
                withdrawal.balance_after = withdrawal.balance_before
                
                logger.warning(f"Gateway transfer failed/reversed: {withdrawal.reference}")
            
            withdrawal.save()
            
            return {'success': True, 'status': withdrawal.status}
            
        except Exception as e:
            logger.error(f"Error completing gateway transfer: {str(e)}")
            return {'success': False, 'error': str(e)}
