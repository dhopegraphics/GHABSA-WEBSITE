"""
Donations System Models
Public donation platform for Biochemistry Society, KNUST
Supports anonymous/public donations, withdrawal tracking, and comprehensive records
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from uuid import uuid4

from accounts.models import CustomUser
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage


class DonationWallet(models.Model):
    """
    Society's donation wallet - Singleton model
    This is separate from user personal wallets
    Holds all donated funds for the society
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    # Balance
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Current balance in the donation wallet"
    )
    
    # Statistics
    total_received = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total amount ever received"
    )
    total_withdrawn = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total amount ever withdrawn"
    )
    total_donations_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of donations received"
    )
    total_donors_count = models.PositiveIntegerField(
        default=0,
        help_text="Total unique donors"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Donation Wallet"
        verbose_name_plural = "Donation Wallet"
    
    def __str__(self):
        return f"Society Donation Wallet - GH₵{self.balance}"
    
    @classmethod
    def get_wallet(cls):
        """Get or create the singleton donation wallet"""
        wallet, created = cls.objects.get_or_create(
            pk='00000000-0000-0000-0000-000000000001'
        )
        return wallet
    
    def add_donation(self, amount, is_new_donor=False):
        """Add a donation to the wallet"""
        self.balance += amount
        self.total_received += amount
        self.total_donations_count += 1
        if is_new_donor:
            self.total_donors_count += 1
        self.save()
    
    def withdraw(self, amount):
        """Withdraw from the wallet"""
        if amount > self.balance:
            raise ValueError("Insufficient balance in donation wallet")
        self.balance -= amount
        self.total_withdrawn += amount
        self.save()


class Donation(models.Model):
    """
    Individual donation record
    Tracks each donation with optional anonymity
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    reference = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Donor info (nullable for anonymous donations without account)
    donor = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donations',
        help_text="User who made the donation (null for guest donations)"
    )
    
    # Donor details (captured at time of donation)
    donor_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name to display (or 'Anonymous')"
    )
    donor_email = models.EmailField(blank=True)
    donor_phone = models.CharField(max_length=20, blank=True)
    
    # Anonymity setting
    is_anonymous = models.BooleanField(
        default=False,
        help_text="If true, donor name will be hidden publicly"
    )
    # Note: Donation amounts are ALWAYS public for transparency
    
    # Amount
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))]
    )
    
    # Message
    message = models.TextField(
        blank=True,
        help_text="Optional message from donor"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Payment gateway info
    gateway = models.CharField(max_length=50, default='paystack')
    gateway_reference = models.CharField(max_length=255, blank=True, db_index=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Donation"
        verbose_name_plural = "Donations"
    
    def __str__(self):
        donor_display = self.get_display_name()
        return f"{donor_display} - GH₵{self.amount} ({self.status})"
    
    def get_display_name(self):
        """Get the name to display publicly"""
        if self.is_anonymous:
            return "Anonymous Donor"
        return self.donor_name or "Anonymous Donor"
    
    def get_display_amount(self):
        """Get the amount to display publicly - always shown for transparency"""
        return self.amount
    
    def save(self, *args, **kwargs):
        # Generate reference if not set
        if not self.reference:
            self.reference = f"DON-{timezone.now().strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class DonorProfile(models.Model):
    """
    Track cumulative donation statistics per user
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='donor_profile'
    )
    
    # Statistics
    total_donated = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total amount donated by this user"
    )
    donation_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of donations made"
    )
    
    # First and last donation dates
    first_donation_at = models.DateTimeField(null=True, blank=True)
    last_donation_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Donor Profile"
        verbose_name_plural = "Donor Profiles"
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - GH₵{self.total_donated} total"
    
    def add_donation(self, amount):
        """Record a donation"""
        self.total_donated += amount
        self.donation_count += 1
        now = timezone.now()
        if not self.first_donation_at:
            self.first_donation_at = now
        self.last_donation_at = now
        self.save()


class DonationWithdrawal(MediaUrlMixin, models.Model):
    """
    Track withdrawals from the donation wallet
    Admin-only operation with full transparency
    Supports direct gateway transfers (Paystack) for automated disbursements
    """
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'receipt_image': 'receipt_image_url',
    }
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('failed', 'Failed'),
    ]
    
    CATEGORY_CHOICES = [
        ('medical', 'Medical Emergency'),
        ('financial_hardship', 'Financial Hardship'),
        ('bereavement', 'Bereavement Support'),
        ('accommodation', 'Accommodation Support'),
        ('feeding', 'Feeding Support'),
        ('welfare', 'General Welfare'),
        ('emergency', 'Emergency Support'),
        ('other', 'Other Welfare'),
    ]
    
    TRANSFER_METHOD_CHOICES = [
        ('manual', 'Manual Transfer'),
        ('gateway', 'Gateway Transfer (Paystack)'),
    ]
    
    BANK_CHOICES = [
        # Mobile Money
        ('mtn', 'MTN Mobile Money'),
        ('vod', 'Vodafone Cash'),
        ('atl', 'AirtelTigo Money'),
        # Banks
        ('gcb', 'GCB Bank'),
        ('ecobank', 'Ecobank Ghana'),
        ('absa', 'Absa Bank Ghana'),
        ('stanbic', 'Stanbic Bank'),
        ('uba', 'UBA Ghana'),
        ('fidelity', 'Fidelity Bank'),
        ('calbank', 'CalBank'),
        ('zenith', 'Zenith Bank'),
        ('access', 'Access Bank'),
        ('gt_bank', 'GT Bank'),
        ('prudential', 'Prudential Bank'),
        ('fnb', 'First National Bank'),
        ('republic', 'Republic Bank'),
        ('societe', 'Societe Generale'),
        ('adb', 'Agricultural Development Bank'),
        ('nib', 'National Investment Bank'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    reference = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Amount
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))]
    )
    
    # Transfer method
    transfer_method = models.CharField(
        max_length=20,
        choices=TRANSFER_METHOD_CHOICES,
        default='manual',
        help_text="How the transfer will be processed"
    )
    
    # Recipient info
    recipient_name = models.CharField(
        max_length=255,
        help_text="Name of recipient/vendor"
    )
    recipient_account = models.CharField(
        max_length=255,
        blank=True,
        help_text="Account number or mobile money number"
    )
    recipient_bank = models.CharField(
        max_length=255,
        blank=True,
        help_text="Bank name or mobile money provider"
    )
    recipient_bank_code = models.CharField(
        max_length=50,
        choices=BANK_CHOICES,
        blank=True,
        help_text="Bank/Provider code for gateway transfers"
    )
    
    # Purpose
    purpose = models.CharField(
        max_length=500,
        help_text="What is this withdrawal for?"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the expense"
    )
    category = models.CharField(
        max_length=100,
        choices=CATEGORY_CHOICES,
        default='other',
        help_text="Category of expense"
    )
    
    # Proof/Documentation (for manual transfers)
    receipt_image = models.ImageField(
        storage=DynamicStorage(),
        upload_to='donations/receipts/',
        null=True,
        blank=True,
        help_text="Receipt or proof of payment (for manual transfers)"
    )
    receipt_image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide receipt image URL instead of uploading"
    )
    
    # Gateway transfer fields (for automated transfers)
    gateway = models.CharField(max_length=50, default='paystack', blank=True)
    gateway_transfer_code = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Paystack transfer code"
    )
    gateway_recipient_code = models.CharField(
        max_length=255,
        blank=True,
        help_text="Paystack recipient code"
    )
    gateway_reference = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Gateway transaction reference"
    )
    gateway_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full gateway response data"
    )
    gateway_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fee charged by gateway for transfer"
    )
    
    # Admin who made the withdrawal
    initiated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='initiated_withdrawals',
        help_text="Admin who initiated the withdrawal"
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_withdrawals',
        help_text="Admin who approved the withdrawal"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    status_message = models.TextField(blank=True)
    
    # Balance tracking
    balance_before = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Wallet balance before withdrawal"
    )
    balance_after = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Wallet balance after withdrawal"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Donation Withdrawal"
        verbose_name_plural = "Donation Withdrawals"
    
    def __str__(self):
        return f"GH₵{self.amount} to {self.recipient_name} - {self.purpose[:50]}"
    
    def save(self, *args, **kwargs):
        # Generate reference if not set
        if not self.reference:
            self.reference = f"WD-{timezone.now().strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8].upper()}"
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """
        Override delete to restore wallet balance if a completed withdrawal is deleted.
        This prevents orphaned deductions when withdrawals are removed.
        """
        # Only restore if this withdrawal was actually completed (funds were deducted)
        if self.status == 'completed':
            wallet = DonationWallet.get_wallet()
            wallet.balance += self.amount
            wallet.total_withdrawn -= self.amount
            wallet.save()
            
            # Also delete related transaction records to keep ledger clean
            self.transactions.all().delete()
        
        super().delete(*args, **kwargs)


class DonationTransaction(models.Model):
    """
    Ledger of all transactions affecting the donation wallet
    For complete audit trail
    """
    TRANSACTION_TYPE_CHOICES = [
        ('donation', 'Donation Received'),
        ('withdrawal', 'Withdrawal'),
        ('refund', 'Refund'),
        ('adjustment', 'Manual Adjustment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    # Type and amount
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Related records
    donation = models.ForeignKey(
        Donation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    withdrawal = models.ForeignKey(
        DonationWithdrawal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    
    # Balance tracking
    balance_before = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Description
    description = models.TextField()
    
    # Who performed the action (for adjustments)
    performed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donation_transactions_performed'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Donation Transaction"
        verbose_name_plural = "Donation Transactions"
    
    def __str__(self):
        return f"{self.transaction_type} - GH₵{self.amount} at {self.created_at}"
