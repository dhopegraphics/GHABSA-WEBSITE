"""
Mentorship Payment Services
Integrates mentorship payments with the main payment system.
"""
from typing import Dict, Any, Optional
from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from .models import (
    MentorPayment,
    ApprovedMentor,
    MentorshipRelationship,
    MenteeApplication,
)
from payments.models import Transaction, Currency
from payments.services.transaction_service import TransactionService
from accounts.models import CustomUser


class MentorshipPaymentService:
    """
    Service for handling mentorship-related payments.
    
    Provides methods for:
    - Initializing mentor offerings/payments
    - Processing mentee-to-mentor payments
    - Handling society incentive payments
    - Syncing payment statuses
    """
    
    @classmethod
    @db_transaction.atomic
    def create_mentor_offering_payment(
        cls,
        mentee: CustomUser,
        mentor: ApprovedMentor,
        amount: Decimal,
        description: str = "",
        callback_url: str = "",
        relationship: Optional[MentorshipRelationship] = None,
        gateway_name: str = "paystack",
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Create a payment from mentee to mentor (offering).
        
        Args:
            mentee: The mentee making the payment
            mentor: The mentor receiving the payment
            amount: Payment amount
            description: Payment description
            callback_url: URL to redirect after payment
            relationship: Optional mentorship relationship
            gateway_name: Payment gateway to use
            metadata: Additional metadata
        
        Returns:
            Dict with mentor_payment, transaction, and authorization_url
        """
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        
        # Build description
        if not description:
            description = f"Mentorship offering from {mentee.get_full_name()} to {mentor.full_name}"
        
        # Create MentorPayment record first
        mentor_payment = MentorPayment.objects.create(
            mentor=mentor,
            mentee=mentee,
            relationship=relationship,
            amount=amount,
            payment_type='offering',
            status='pending',
            description=description,
            callback_url=callback_url,
        )
        
        # Get ContentType for MentorPayment
        content_type = ContentType.objects.get_for_model(MentorPayment)
        
        # Build metadata
        payment_metadata = {
            'payment_type': 'mentor_offering',
            'mentor_id': str(mentor.id),
            'mentor_name': mentor.full_name,
            'mentee_id': str(mentee.id),
            'mentee_name': mentee.get_full_name(),
            'mentor_payment_id': str(mentor_payment.id),
        }
        if relationship:
            payment_metadata['relationship_id'] = str(relationship.id)
        if metadata:
            payment_metadata.update(metadata)
        
        try:
            # Create transaction using the payment system
            transaction = TransactionService.create_transaction(
                user=mentee,
                amount=amount,
                currency_code='GHS',
                description=description,
                transaction_type='payment',
                gateway_name=gateway_name,
                content_object=mentor_payment,
                metadata=payment_metadata,
                customer_email=mentee.email,
                customer_phone=getattr(mentee, 'phone_number', ''),
                customer_name=mentee.get_full_name(),
            )
            
            # Link transaction to mentor payment
            mentor_payment.transaction = transaction
            mentor_payment.transaction_reference = transaction.reference
            mentor_payment.save()
            
            # Initialize payment with gateway
            payment_result = TransactionService.initialize_payment(
                transaction=transaction,
                callback_url=callback_url
            )
            
            return {
                'mentor_payment': mentor_payment,
                'transaction': transaction,
                'authorization_url': payment_result.get('authorization_url'),
                'access_code': payment_result.get('access_code'),
                'reference': transaction.reference,
            }
        
        except Exception as e:
            # Update mentor payment status on failure
            mentor_payment.status = 'failed'
            mentor_payment.save()
            raise e
    
    @classmethod
    @db_transaction.atomic
    def create_society_incentive_payment(
        cls,
        mentor: ApprovedMentor,
        amount: Decimal,
        description: str = "",
        initiated_by: Optional[CustomUser] = None,
        metadata: Optional[Dict] = None,
    ) -> MentorPayment:
        """
        Create a society incentive payment to a mentor.
        This is typically initiated by admin/society.
        
        Args:
            mentor: The mentor receiving the incentive
            amount: Incentive amount
            description: Payment description
            initiated_by: Admin/staff who initiated
            metadata: Additional metadata
        
        Returns:
            MentorPayment record
        """
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        
        if not description:
            description = f"Society incentive payment to {mentor.full_name}"
        
        # Create MentorPayment record
        mentor_payment = MentorPayment.objects.create(
            mentor=mentor,
            mentee=None,  # No mentee for society payments
            relationship=None,
            amount=amount,
            payment_type='incentive',
            status='pending',
            description=description,
        )
        
        # Note: Society payments may be processed differently
        # (e.g., bank transfer, manual processing)
        # The transaction can be linked later when processed
        
        return mentor_payment
    
    @classmethod
    def verify_and_sync_payment(cls, reference: str) -> MentorPayment:
        """
        Verify payment status and sync with mentor payment.
        
        Args:
            reference: Transaction reference
        
        Returns:
            Updated MentorPayment
        """
        try:
            # Get the mentor payment by reference
            mentor_payment = MentorPayment.objects.get(transaction_reference=reference)
        except MentorPayment.DoesNotExist:
            # Try to find by transaction
            try:
                transaction = Transaction.objects.get(reference=reference)
                mentor_payment = MentorPayment.objects.get(transaction=transaction)
            except (Transaction.DoesNotExist, MentorPayment.DoesNotExist):
                raise ValueError(f"Mentor payment with reference '{reference}' not found")
        
        # Verify with payment gateway
        if mentor_payment.transaction:
            transaction = TransactionService.verify_payment(reference)
            mentor_payment.sync_with_transaction()
        
        return mentor_payment
    
    @classmethod
    def get_mentor_earnings(cls, mentor: ApprovedMentor) -> Dict[str, Any]:
        """
        Get mentor's earnings summary.
        
        Args:
            mentor: The mentor
        
        Returns:
            Dict with earnings breakdown
        """
        from django.db.models import Sum, Count
        
        payments = MentorPayment.objects.filter(mentor=mentor)
        
        completed_payments = payments.filter(status='completed')
        pending_payments = payments.filter(status='pending')
        
        total_earnings = completed_payments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        offerings_total = completed_payments.filter(
            payment_type='offering'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        incentives_total = completed_payments.filter(
            payment_type='incentive'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        pending_amount = pending_payments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        return {
            'total_earnings': total_earnings,
            'offerings_total': offerings_total,
            'incentives_total': incentives_total,
            'pending_amount': pending_amount,
            'completed_count': completed_payments.count(),
            'pending_count': pending_payments.count(),
        }
    
    @classmethod
    def get_mentee_payments(cls, mentee: CustomUser) -> Dict[str, Any]:
        """
        Get mentee's payment history.
        
        Args:
            mentee: The mentee
        
        Returns:
            Dict with payment history
        """
        from django.db.models import Sum
        
        payments = MentorPayment.objects.filter(mentee=mentee)
        
        completed_payments = payments.filter(status='completed')
        
        total_paid = completed_payments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        return {
            'total_paid': total_paid,
            'payment_count': completed_payments.count(),
            'payments': payments.select_related('mentor', 'transaction').order_by('-created_at'),
        }
    
    @classmethod
    @db_transaction.atomic
    def process_mentee_application_payment(
        cls,
        application: MenteeApplication,
        callback_url: str = "",
        gateway_name: str = "paystack",
    ) -> Optional[Dict[str, Any]]:
        """
        Process payment for mentee application offering.
        
        Args:
            application: The mentee application
            callback_url: URL to redirect after payment
            gateway_name: Payment gateway to use
        
        Returns:
            Payment result dict or None if no payment needed
        """
        # Check if application has monetary offering
        if application.offering_type != 'monetary' or not application.offering_amount:
            return None
        
        if application.offering_amount <= 0:
            return None
        
        # Get or create relationship if application is accepted
        relationship = getattr(application, 'resulting_relationship', None)
        
        description = f"Mentorship offering from {application.applicant.get_full_name()} to {application.mentor.full_name}"
        
        return cls.create_mentor_offering_payment(
            mentee=application.applicant,
            mentor=application.mentor,
            amount=application.offering_amount,
            description=description,
            callback_url=callback_url,
            relationship=relationship,
            gateway_name=gateway_name,
            metadata={
                'mentee_application_id': str(application.id),
                'area': application.area.name,
            }
        )


# Webhook handler for payment completion
def handle_mentor_payment_webhook(transaction: Transaction) -> None:
    """
    Handle payment webhook for mentor payments.
    Called when a mentor payment transaction status changes.
    
    Args:
        transaction: The transaction that was updated
    """
    try:
        # Find linked mentor payment
        mentor_payment = MentorPayment.objects.get(transaction=transaction)
        mentor_payment.sync_with_transaction()
        
        # If payment completed, credit mentor's wallet
        if mentor_payment.status == 'completed':
            MentorWalletService.credit_mentor_wallet(
                mentor=mentor_payment.mentor,
                amount=mentor_payment.amount,
                description=f"Donation from {mentor_payment.mentee.get_full_name() if mentor_payment.mentee else 'Anonymous'}",
                related_payment=mentor_payment
            )
            
    except MentorPayment.DoesNotExist:
        # Transaction not linked to mentor payment
        pass


class MentorWalletService:
    """
    Service for managing mentor wallets and donations.
    Automatically creates wallets on first donation and credits earnings.
    """
    
    @classmethod
    def get_or_create_mentor_wallet(cls, mentor: ApprovedMentor) -> 'Wallet':
        """
        Get or create a wallet for the mentor.
        
        Args:
            mentor: The approved mentor
            
        Returns:
            Wallet instance
        """
        from payments.models import Wallet, Currency
        
        try:
            wallet = Wallet.objects.get(user=mentor.user)
        except Wallet.DoesNotExist:
            # Create wallet with GHS currency
            currency = Currency.objects.get(code='GHS')
            wallet = Wallet.objects.create(
                user=mentor.user,
                balance=Decimal('0.00'),
                currency=currency,
                status='active'
            )
        
        return wallet
    
    @classmethod
    @db_transaction.atomic
    def credit_mentor_wallet(
        cls,
        mentor: ApprovedMentor,
        amount: Decimal,
        description: str,
        related_payment: MentorPayment = None
    ) -> Dict[str, Any]:
        """
        Credit a mentor's wallet and update their earnings.
        Creates wallet if it doesn't exist.
        
        Args:
            mentor: The mentor to credit
            amount: Amount to credit
            description: Transaction description
            related_payment: Optional related MentorPayment
            
        Returns:
            Dict with wallet transaction details
        """
        from payments.models import WalletTransaction
        from uuid import uuid4
        
        # Get or create wallet
        wallet = cls.get_or_create_mentor_wallet(mentor)
        
        if wallet.status != 'active':
            raise ValueError("Mentor wallet is not active")
        
        # Record balance before
        balance_before = wallet.balance
        
        # Credit the wallet
        wallet.credit(amount)
        
        # Create wallet transaction record
        wallet_txn = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='credit',
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            related_transaction=related_payment.transaction if related_payment and related_payment.transaction else None,
            description=description,
            reference=f"MW-{uuid4().hex[:8].upper()}",
            metadata={
                'payment_type': 'mentor_donation',
                'mentor_payment_id': str(related_payment.id) if related_payment else None,
            }
        )
        
        return {
            'wallet_transaction': wallet_txn,
            'new_balance': wallet.balance,
            'amount_credited': amount,
        }
    
    @classmethod
    def get_mentor_wallet_info(cls, mentor: ApprovedMentor) -> Dict[str, Any]:
        """
        Get mentor's wallet information.
        
        Args:
            mentor: The approved mentor
            
        Returns:
            Dict with wallet info or None if no wallet
        """
        from payments.models import Wallet
        
        try:
            wallet = Wallet.objects.get(user=mentor.user)
            return {
                'has_wallet': True,
                'balance': wallet.balance,
                'currency': wallet.currency.code,
                'status': wallet.status,
                'wallet_id': str(wallet.id),
            }
        except Wallet.DoesNotExist:
            return {
                'has_wallet': False,
                'balance': Decimal('0.00'),
                'currency': 'GHS',
                'status': None,
                'wallet_id': None,
            }
    
    @classmethod
    def check_mentee_mentor_relationship(
        cls,
        mentee: CustomUser,
        mentor: ApprovedMentor
    ) -> Dict[str, Any]:
        """
        Check if a mentee has a relationship with a mentor.
        
        Args:
            mentee: The mentee user
            mentor: The approved mentor
            
        Returns:
            Dict with relationship info
        """
        from mentorship.models import MentorshipRelationship, MenteeApplication
        
        # Check for active relationship
        relationship = MentorshipRelationship.objects.filter(
            mentee=mentee,
            mentor=mentor,
            status='active'
        ).first()
        
        # Check for pending application
        pending_application = MenteeApplication.objects.filter(
            applicant=mentee,
            mentor=mentor,
            status='pending'
        ).first()
        
        # Check for accepted application (which creates relationship)
        accepted_application = MenteeApplication.objects.filter(
            applicant=mentee,
            mentor=mentor,
            status='accepted'
        ).first()
        
        return {
            'has_relationship': relationship is not None,
            'relationship_id': str(relationship.id) if relationship else None,
            'relationship_status': relationship.status if relationship else None,
            'has_pending_application': pending_application is not None,
            'has_accepted_application': accepted_application is not None,
            'can_donate': relationship is not None or accepted_application is not None,
        }


class MentorDonationService:
    """
    Service for handling donations to mentors.
    Integrates with wallet system and payment gateway.
    """
    
    @classmethod
    @db_transaction.atomic
    def create_donation(
        cls,
        donor: CustomUser,
        mentor: ApprovedMentor,
        amount: Decimal,
        message: str = "",
        callback_url: str = "",
        gateway_name: str = "paystack",
    ) -> Dict[str, Any]:
        """
        Create a donation from a user to a mentor.
        
        Args:
            donor: The user making the donation
            mentor: The mentor receiving the donation
            amount: Donation amount
            message: Optional message from donor
            callback_url: URL to redirect after payment
            gateway_name: Payment gateway to use
            
        Returns:
            Dict with payment details and authorization URL
        """
        if amount <= 0:
            raise ValueError("Donation amount must be greater than zero")
        
        # Check for existing relationship
        relationship_info = MentorWalletService.check_mentee_mentor_relationship(donor, mentor)
        relationship = None
        
        if relationship_info['relationship_id']:
            from mentorship.models import MentorshipRelationship
            relationship = MentorshipRelationship.objects.get(id=relationship_info['relationship_id'])
        
        # Build description
        description = f"Donation to {mentor.full_name}"
        if message:
            description += f": {message}"
        
        # Create the payment using existing service
        result = MentorshipPaymentService.create_mentor_offering_payment(
            mentee=donor,
            mentor=mentor,
            amount=amount,
            description=description,
            callback_url=callback_url,
            relationship=relationship,
            gateway_name=gateway_name,
            metadata={
                'payment_type': 'donation',
                'message': message,
                'donor_name': donor.get_full_name(),
                'has_relationship': relationship_info['has_relationship'],
            }
        )
        
        return result
    
    @classmethod
    def get_mentor_donation_stats(cls, mentor: ApprovedMentor) -> Dict[str, Any]:
        """
        Get donation statistics for a mentor.
        
        Args:
            mentor: The approved mentor
            
        Returns:
            Dict with donation stats
        """
        from django.db.models import Sum, Count
        
        donations = MentorPayment.objects.filter(
            mentor=mentor,
            payment_type='offering'
        )
        
        completed = donations.filter(status='completed')
        
        total_received = completed.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        donor_count = completed.values('mentee').distinct().count()
        
        # Get wallet info
        wallet_info = MentorWalletService.get_mentor_wallet_info(mentor)
        
        return {
            'total_donations_received': total_received,
            'total_donors': donor_count,
            'total_donations_count': completed.count(),
            'wallet_balance': wallet_info['balance'],
            'has_wallet': wallet_info['has_wallet'],
        }
