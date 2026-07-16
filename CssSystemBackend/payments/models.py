"""
Comprehensive Payment System Models
Supports multiple payment gateways, transactions, refunds, wallets, and more
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
from uuid import uuid4
import json
import secrets
import string


class PaymentGateway(models.Model):
    """
    Supported payment gateways (Paystack, Flutterwave, Stripe, etc.)
    """
    GATEWAY_CHOICES = [
        ('paystack', 'Paystack'),
        ('flutterwave', 'Flutterwave'),
        ('stripe', 'Stripe'),
        ('momo_api', 'MTN Mobile Money API'),
        ('manual', 'Manual Payment'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, choices=GATEWAY_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Gateway status
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Supported features
    supports_refunds = models.BooleanField(default=True)
    supports_recurring = models.BooleanField(default=False)
    supports_webhooks = models.BooleanField(default=True)
    
    # Supported currencies
    supported_currencies = models.JSONField(
        default=list,
        help_text="List of supported currency codes"
    )
    
    # Supported payment methods
    supported_methods = models.JSONField(
        default=list,
        help_text="List of supported payment methods"
    )
    
    # Configuration
    config = models.JSONField(
        default=dict,
        help_text="Gateway-specific configuration"
    )
    
    # Fees
    fixed_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fixed fee per transaction"
    )
    percentage_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage fee per transaction"
    )
    
    # Priority (for fallback)
    priority = models.IntegerField(default=0, help_text="Higher priority gateways are tried first")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Payment Gateway"
        verbose_name_plural = "Payment Gateways"
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.display_name} ({self.get_status_display()})"
    
    def calculate_fee(self, amount):
        """Calculate total fee for a transaction"""
        percentage_amount = (amount * self.percentage_fee) / 100
        return self.fixed_fee + percentage_amount


class Currency(models.Model):
    """
    Supported currencies for the platform
    """
    code = models.CharField(max_length=3, primary_key=True, help_text="ISO 4217 currency code")
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    
    # Exchange rate (relative to base currency)
    exchange_rate = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=Decimal('1.0'),
        help_text="Exchange rate to base currency (GHS)"
    )
    
    is_active = models.BooleanField(default=True)
    is_base_currency = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Transaction(models.Model):
    """
    Main transaction model - records all financial transactions
    """
    TRANSACTION_TYPE_CHOICES = [
        ('payment', 'Payment'),
        ('donation', 'Donation'),
        ('refund', 'Refund'),
        ('reversal', 'Reversal'),
        ('transfer', 'Transfer'),
        ('wallet_topup', 'Wallet Top-up'),
        ('wallet_withdrawal', 'Wallet Withdrawal'),
        ('commission', 'Commission'),
        ('fee', 'Fee'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
        ('on_hold', 'On Hold'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    reference = models.CharField(max_length=100, unique=True, db_index=True)
    
    # User (nullable for anonymous transactions)
    from accounts.models import CustomUser
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True,
        help_text="User who initiated the transaction (null for anonymous users)"
    )
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    
    # Gateway
    gateway = models.ForeignKey(
        PaymentGateway,
        on_delete=models.PROTECT,
        related_name='transactions',
        null=True,
        blank=True
    )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    status_message = models.TextField(blank=True)
    
    # Related object (GenericForeignKey for flexibility)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Type of object this payment is for"
    )
    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Description
    description = models.TextField(help_text="What is this transaction for?")
    
    # Fees
    gateway_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fee charged by payment gateway"
    )
    platform_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fee charged by platform"
    )
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount after fees"
    )
    
    # Payment details
    payment_method = models.CharField(max_length=50, blank=True)
    payment_channel = models.CharField(max_length=50, blank=True)
    
    # Gateway response
    gateway_reference = models.CharField(max_length=255, blank=True, db_index=True)
    gateway_response = models.TextField(blank=True)
    gateway_metadata = models.JSONField(default=dict, blank=True)
    
    # Customer info (cached for reporting)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_name = models.CharField(max_length=255, blank=True)
    
    # IP and location tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    
    # Related transactions
    parent_transaction = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_transactions',
        help_text="Original transaction (for refunds/reversals)"
    )
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional transaction metadata"
    )
    
    # Flags
    is_test = models.BooleanField(default=False, help_text="Test transaction")
    requires_manual_review = models.BooleanField(default=False)
    
    # NOTE: Merchandise tracking (validation codes, collection status, variant selections)
    # has been moved to ProductPayment model in the products app
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['gateway', 'status']),
            models.Index(fields=['transaction_type', 'status']),
            models.Index(fields=['reference']),
            models.Index(fields=['gateway_reference']),
            models.Index(fields=['initiated_at']),
        ]
    
    def __str__(self):
        return f"{self.reference} - {self.get_transaction_type_display()} - {self.currency.code} {self.amount}"
    
    def save(self, *args, **kwargs):
        # Calculate net amount
        if not self.net_amount:
            self.net_amount = self.amount - self.gateway_fee - self.platform_fee
        
        # Set completed timestamp
        if self.status == 'success' and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def is_successful(self):
        return self.status == 'success'
    
    @property
    def is_pending(self):
        return self.status in ['pending', 'processing']
    
    @property
    def is_failed(self):
        return self.status in ['failed', 'cancelled', 'expired']
    
    @property
    def total_fees(self):
        return self.gateway_fee + self.platform_fee
    
    @property
    def can_be_refunded(self):
        return (
            self.status == 'success' and
            self.transaction_type == 'payment' and
            not self.child_transactions.filter(transaction_type='refund', status='success').exists()
        )


class PaymentSession(models.Model):
    """
    Payment session for tracking payment flow
    """
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    session_key = models.CharField(max_length=100, unique=True, db_index=True)
    
    # User (can be null for guest checkout)
    from accounts.models import CustomUser
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='payment_sessions'
    )
    
    # Payment details
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    description = models.TextField()
    
    # Related transaction
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='session'
    )
    
    # Gateway
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.PROTECT)
    gateway_session_id = models.CharField(max_length=255, blank=True)
    
    # URLs
    success_url = models.URLField(blank=True)
    cancel_url = models.URLField(blank=True)
    webhook_url = models.URLField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Payment Session"
        verbose_name_plural = "Payment Sessions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Session {self.session_key} - {self.status}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at


class Refund(models.Model):
    """
    Refund model for handling transaction refunds
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('rejected', 'Rejected'),
    ]
    
    REASON_CHOICES = [
        ('customer_request', 'Customer Request'),
        ('duplicate_payment', 'Duplicate Payment'),
        ('fraudulent', 'Fraudulent Transaction'),
        ('order_cancelled', 'Order Cancelled'),
        ('product_unavailable', 'Product Unavailable'),
        ('error', 'Transaction Error'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    reference = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Original transaction
    original_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='refunds'
    )
    
    # Refund transaction (created after refund success)
    refund_transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refund_record'
    )
    
    # Refund details
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount to refund (can be partial)"
    )
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    reason_details = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    status_message = models.TextField(blank=True)
    
    # Gateway response
    gateway_reference = models.CharField(max_length=255, blank=True)
    gateway_response = models.TextField(blank=True)
    
    # Initiated by
    from accounts.models import CustomUser
    initiated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='initiated_refunds'
    )
    
    # Approval (if required)
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_refunds'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Refund"
        verbose_name_plural = "Refunds"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund {self.reference} - {self.amount}"
    
    @property
    def is_successful(self):
        return self.status == 'success'
    
    @property
    def is_partial(self):
        return self.amount < self.original_transaction.amount


class Wallet(models.Model):
    """
    User wallet for storing balance
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    # User
    from accounts.models import CustomUser
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    
    # Balance
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default='GHS')
    
    # Limits
    daily_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Daily spending limit"
    )
    transaction_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Per transaction limit"
    )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_locked = models.BooleanField(default=False)
    lock_reason = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.currency.code} {self.balance}"
    
    def can_debit(self, amount):
        """Check if wallet can be debited"""
        return (
            self.status == 'active' and
            not self.is_locked and
            self.balance >= amount
        )
    
    def debit(self, amount, description):
        """Debit wallet"""
        if not self.can_debit(amount):
            raise ValueError("Insufficient balance or wallet locked")
        
        self.balance -= amount
        self.save()
        
        # Create transaction record
        # This will be handled in the service layer
    
    def credit(self, amount):
        """Credit wallet"""
        if self.status != 'active':
            raise ValueError("Wallet not active")
        
        self.balance += amount
        self.save()


class WalletTransaction(models.Model):
    """
    Wallet transaction history
    """
    TRANSACTION_TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction details
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Related transaction
    related_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions'
    )
    
    # Description
    description = models.TextField()
    reference = models.CharField(max_length=100, unique=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Wallet Transaction"
        verbose_name_plural = "Wallet Transactions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.wallet.user.get_full_name()} - {self.transaction_type} - {self.amount}"


class PaymentWebhook(models.Model):
    """
    Store webhook events from payment gateways
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('ignored', 'Ignored'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    # Gateway
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.CASCADE, related_name='webhooks')
    
    # Event details
    event_type = models.CharField(max_length=100)
    event_id = models.CharField(max_length=255, blank=True, db_index=True)
    
    # Payload
    payload = models.JSONField()
    headers = models.JSONField(default=dict)
    
    # Signature verification
    signature = models.CharField(max_length=500, blank=True)
    is_verified = models.BooleanField(default=False)
    
    # Processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processing_attempts = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    # Related transaction
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhooks'
    )
    
    # Timestamps
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Payment Webhook"
        verbose_name_plural = "Payment Webhooks"
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['gateway', 'event_type']),
            models.Index(fields=['event_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.gateway.display_name} - {self.event_type} - {self.status}"

# =====================================================
# EXPENSE MANAGEMENT SYSTEM
# =====================================================

class ExpenseCategory(models.Model):
    """
    Categories for organizing expenses (e.g., Office Supplies, Events, Logistics)
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50, 
        default='💰',
        help_text="Emoji or icon identifier for the category"
    )
    color = models.CharField(
        max_length=20,
        default='#6366f1',
        help_text="Hex color code for category visualization"
    )
    is_active = models.BooleanField(default=True)
    budget_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional monthly budget limit for this category"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.icon} {self.name}"


class ExpenseRecipient(models.Model):
    """
    People or entities that receive expense payments
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    momo_number = models.CharField(max_length=20, blank=True, help_text="Mobile Money number")
    momo_provider = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('mtn', 'MTN Mobile Money'),
            ('vodafone', 'Vodafone Cash'),
            ('airteltigo', 'AirtelTigo Money'),
        ]
    )
    address = models.TextField(blank=True)
    is_vendor = models.BooleanField(default=False, help_text="Is this recipient a vendor/supplier?")
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Expense Recipient"
        verbose_name_plural = "Expense Recipients"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Expense(models.Model):
    """
    Main expense model for tracking all expenditures
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('momo', 'Mobile Money'),
        ('cheque', 'Cheque'),
        ('card', 'Card Payment'),
        ('petty_cash', 'Petty Cash'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    reference = models.CharField(max_length=50, unique=True, db_index=True, editable=False)
    
    # What the expense is for
    title = models.CharField(max_length=255, help_text="Brief title for the expense")
    description = models.TextField(help_text="Detailed description of what the expense is for")
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name='expenses'
    )
    
    # Amount details
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default='GHS')
    
    # Who receives the money
    recipient = models.ForeignKey(
        ExpenseRecipient,
        on_delete=models.PROTECT,
        related_name='expenses',
        null=True,
        blank=True,
        help_text="Person or entity who received the money"
    )
    recipient_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Recipient name if not using ExpenseRecipient model"
    )
    recipient_details = models.TextField(
        blank=True,
        help_text="Additional recipient details (account, phone, etc.)"
    )
    
    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    payment_reference = models.CharField(max_length=100, blank=True, help_text="Bank reference, MoMo ID, Cheque number, etc.")
    payment_date = models.DateField(null=True, blank=True)
    
    # Status and approvals
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Who created and approved
    from accounts.models import CustomUser
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_expenses',
        help_text="Executive who recorded this expense"
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_expenses',
        help_text="Executive who approved this expense"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Supporting documents
    receipt_image = models.ImageField(upload_to='expense_receipts/', blank=True, null=True)
    receipt_url = models.URLField(blank=True, help_text="URL to receipt image if hosted externally")
    attachments = models.JSONField(
        default=list,
        blank=True,
        help_text="List of attachment URLs"
    )
    
    # Event/Project association
    event_name = models.CharField(max_length=255, blank=True, help_text="Associated event or project name")
    
    # SMS notification tracking
    sms_notification_sent = models.BooleanField(default=False, editable=False)
    sms_notification_error = models.TextField(blank=True, editable=False)
    
    # Notes and remarks
    notes = models.TextField(blank=True, help_text="Internal notes about this expense")
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection if status is rejected")
    
    # Timestamps
    expense_date = models.DateField(help_text="Date when the expense occurred")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"
        ordering = ['-expense_date', '-created_at']
        indexes = [
            models.Index(fields=['status', 'expense_date']),
            models.Index(fields=['category', 'expense_date']),
            models.Index(fields=['created_by', 'status']),
            models.Index(fields=['reference']),
        ]
    
    def __str__(self):
        return f"{self.reference} - {self.title} - {self.currency.code} {self.amount}"
    
    def save(self, *args, **kwargs):
        # Generate reference number if not set
        if not self.reference:
            from datetime import datetime
            prefix = "EXP"
            date_str = datetime.now().strftime("%Y%m%d")
            # Get count for today
            count = Expense.objects.filter(
                reference__startswith=f"{prefix}{date_str}"
            ).count() + 1
            self.reference = f"{prefix}{date_str}{count:04d}"
        
        # Track if this is a new expense for SMS notification
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        # Send SMS notification to executives for new expenses
        if is_new and not self.sms_notification_sent:
            self.send_expense_notification_to_executives()
    
    def send_expense_notification_to_executives(self):
        """Send SMS notification to financial and president executives about this expense"""
        from executives.models import Executive
        from utils.utils import notify_user
        from django.db.models import Q
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Get current account balance for context
            balance_info = AccountBalance.get_current_balance()
            current_balance = balance_info.get('current_balance', Decimal('0.00'))
            
            # Ensure proper Decimal types for formatting (handle potential string values)
            try:
                amount_value = Decimal(str(self.amount)) if self.amount else Decimal('0.00')
            except (TypeError, ValueError):
                amount_value = Decimal('0.00')
            
            try:
                balance_value = Decimal(str(current_balance)) if current_balance else Decimal('0.00')
            except (TypeError, ValueError):
                balance_value = Decimal('0.00')
            
            # Safely format date
            expense_date_str = str(self.expense_date) if self.expense_date else 'N/A'
            
            # Compose message without emojis
            message = (
                "NEW EXPENSE RECORDED\n"
                "-------------------\n"
                f"Ref: {self.reference}\n"
                f"{self.title}\n"
                f"Amount: GHS {amount_value:,.2f}\n"
                f"Category: {self.category.name}\n"
                f"Recipient: {self.recipient.name if self.recipient else self.recipient_name or 'N/A'}\n"
                f"Date: {expense_date_str}\n"
                "-------------------\n"
                f"CURRENT BALANCE: GHS {balance_value:,.2f}\n"
                "-------------------\n"
                f"By: {self.created_by.get_full_name() if self.created_by else 'System'}"
            )
            
            # Get active executives with financial or president positions only
            # Using Q objects with OR instead of union() to avoid ORDER BY issues in compound queries
            active_executives = Executive.objects.filter(
                Q(position__name__icontains='financial') | Q(position__name__icontains='president'),
                is_active=True
            ).select_related('user', 'position')
            
            errors = []
            success_count = 0
            
            for executive in active_executives:
                # Properly convert PhoneNumber object to string for SMS
                if executive.user.phone:
                    # PhoneNumber objects need special handling
                    phone_obj = executive.user.phone
                    # Convert to national format (0XXXXXXXXX) which is expected by notify_user
                    if hasattr(phone_obj, 'as_national'):
                        # Use national format and clean it
                        phone = phone_obj.as_national.replace(' ', '').replace('-', '')
                    else:
                        # Fallback to string conversion
                        phone = str(phone_obj).replace('+233', '0')
                    
                    logger.info(f"Sending SMS to {executive.position.name} {executive.user.get_full_name()} at {phone}")
                    
                    try:
                        success, msg, campaign_id = notify_user(phone, message)
                        if success:
                            success_count += 1
                            logger.info(f"Expense SMS sent successfully to {executive.position.name} {executive.user.get_full_name()} ({phone})")
                        else:
                            error_msg = f"{executive.position.name} {executive.user.get_full_name()}: {msg}"
                            errors.append(error_msg)
                            logger.warning(f"Failed to send SMS to {executive.position.name} {executive.user.get_full_name()}: {msg}")
                    except Exception as e:
                        error_msg = f"{executive.position.name} {executive.user.get_full_name()}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(f"Exception sending SMS to {executive.position.name} {executive.user.get_full_name()}: {str(e)}", exc_info=True)
                else:
                    logger.warning(f"No phone number for {executive.position.name} {executive.user.get_full_name()}")
            
            # Update notification status
            self.sms_notification_sent = success_count > 0
            if errors:
                self.sms_notification_error = f"Sent to {success_count} executives. Errors: " + "; ".join(errors[:5])
            else:
                self.sms_notification_error = ""
            
            Expense.objects.filter(pk=self.pk).update(
                sms_notification_sent=self.sms_notification_sent,
                sms_notification_error=self.sms_notification_error
            )
            
            logger.info(f"Expense notification sent to {success_count}/{active_executives.count()} financial/president executives")
            
        except Exception as e:
            logger.error(f"Failed to send expense notification: {str(e)}", exc_info=True)
            Expense.objects.filter(pk=self.pk).update(
                sms_notification_sent=False,
                sms_notification_error=str(e)
            )
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_paid(self):
        return self.status == 'paid'
    
    @property
    def formatted_amount(self):
        return f"{self.currency.code} {self.amount:,.2f}"
    
    @property
    def recipient_display_name(self):
        if self.recipient:
            return self.recipient.name
        return self.recipient_name or "Unknown"


class AccountBalance(models.Model):
    """
    Tracks the overall account balance and financial summary.
    This is a singleton model - only one record should exist.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    # Total income from successful transactions
    total_income = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total money received from all successful transactions"
    )
    
    # Total expenditure
    total_expenditure = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total money spent on expenses"
    )
    
    # Initial/Starting balance (set manually if needed)
    initial_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Starting balance (if there was existing money before system implementation)"
    )
    
    # Currency
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default='GHS')
    
    # Last updated by
    from accounts.models import CustomUser
    last_updated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notes
    notes = models.TextField(blank=True, help_text="Any notes about the balance")
    
    class Meta:
        verbose_name = "Account Balance"
        verbose_name_plural = "Account Balances"
    
    def __str__(self):
        return f"Account Balance: {self.currency.code if self.currency_id else 'GHS'} {self.current_balance:,.2f}"
    
    @property
    def current_balance(self):
        """Calculate current balance"""
        return self.initial_balance + self.total_income - self.total_expenditure
    
    @classmethod
    def get_or_create_singleton(cls):
        """Get or create the singleton AccountBalance instance"""
        obj, created = cls.objects.get_or_create(
            defaults={'currency_id': 'GHS'}
        )
        return obj
    
    @classmethod
    def _calculate_merchandise_income(cls):
        """
        Calculate total income from merchandise-only transactions.
        Excludes:
        - El Mercado only transactions (unified_checkout with purchase_type='el_mercado_only')
        - El Mercado portion of mixed cart transactions
        
        Includes:
        - TXN-* (Merchandise transactions - both direct and cart checkout)
        - DON-* (Donations)
        - WAL-* (Wallet top-ups)
        - Merchandise portion of mixed cart transactions
        - Other non-marketplace transactions
        
        Cart checkout transactions have metadata:
        - unified_checkout: True
        - purchase_type: 'el_mercado_only', 'merchandise_only', or 'mixed'
        - merchandise_total: decimal string
        - el_mercado_total: decimal string
        """
        from django.db.models import Q
        
        total_income = Decimal('0.00')
        
        # Get all successful payment/donation/wallet transactions
        transactions = Transaction.objects.filter(
            status='success',
            transaction_type__in=['payment', 'donation', 'wallet_topup']
        )
        
        for txn in transactions:
            metadata = txn.metadata or {}
            
            # Check if this is a unified/cart checkout transaction
            if metadata.get('unified_checkout'):
                purchase_type = metadata.get('purchase_type', 'mixed')
                
                # Skip El Mercado only purchases
                if purchase_type == 'el_mercado_only':
                    continue
                
                # Merchandise only via cart - include fully
                if purchase_type == 'merchandise_only':
                    total_income += txn.net_amount or Decimal('0.00')
                    continue
                
                # Mixed cart - include only merchandise portion
                merchandise_total_str = metadata.get('merchandise_total', '0.00')
                try:
                    merchandise_total = Decimal(str(merchandise_total_str))
                except:
                    merchandise_total = Decimal('0.00')
                
                if merchandise_total > 0:
                    grand_total_str = metadata.get('grand_total', str(txn.amount))
                    try:
                        grand_total = Decimal(str(grand_total_str))
                    except:
                        grand_total = txn.amount
                    
                    if grand_total > 0:
                        merchandise_ratio = merchandise_total / grand_total
                        merchandise_net = txn.net_amount * merchandise_ratio
                        total_income += merchandise_net
                continue
            
            # Non-cart transactions - include all (TXN-*, DON-*, WAL-*, VOTE-*, etc.)
            total_income += txn.net_amount or Decimal('0.00')
        
        return total_income
    
    @classmethod
    def get_current_balance(cls):
        """Get current balance with computed values (merchandise only, excludes El Mercado)"""
        obj = cls.get_or_create_singleton()
        
        # Calculate total income from merchandise transactions only
        total_income = cls._calculate_merchandise_income()
        
        # Calculate total expenditure from paid expenses
        total_expenditure = Expense.objects.filter(
            status='paid'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        return {
            'initial_balance': obj.initial_balance,
            'total_income': total_income,
            'total_expenditure': total_expenditure,
            'current_balance': obj.initial_balance + total_income - total_expenditure,
            'currency': obj.currency_id or 'GHS'
        }
    
    @classmethod
    def recalculate_balance(cls, updated_by=None):
        """Recalculate and update the balance from transactions and expenses (merchandise only)"""
        obj = cls.get_or_create_singleton()
        
        # Calculate total income from merchandise transactions only
        obj.total_income = cls._calculate_merchandise_income()
        
        # Calculate total expenditure from paid expenses
        obj.total_expenditure = Expense.objects.filter(
            status='paid'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        if updated_by:
            obj.last_updated_by = updated_by
        
        obj.save()
        return obj


class ExpenseAuditLog(models.Model):
    """
    Audit log for tracking all changes to expenses
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Marked as Paid'),
        ('cancelled', 'Cancelled'),
        ('deleted', 'Deleted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    # Who performed the action
    from accounts.models import CustomUser
    performed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True
    )
    
    # Previous and new values (for updates)
    previous_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    # Comments
    comments = models.TextField(blank=True)
    
    # IP tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Expense Audit Log"
        verbose_name_plural = "Expense Audit Logs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.expense.reference} - {self.get_action_display()} by {self.performed_by}"


class BudgetAllocation(models.Model):
    """
    Budget allocation for different categories or periods
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Budget name (e.g., 'Q1 2026 Event Budget')")
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.CASCADE,
        related_name='budgets',
        null=True,
        blank=True,
        help_text="Category this budget applies to (leave empty for general budget)"
    )
    
    # Budget amounts
    allocated_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default='GHS')
    
    # Period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    from accounts.models import CustomUser
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Budget Allocation"
        verbose_name_plural = "Budget Allocations"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} - {self.currency.code} {self.allocated_amount:,.2f}"
    
    @property
    def spent_amount(self):
        """Calculate how much has been spent against this budget"""
        filters = {
            'status': 'paid',
            'expense_date__gte': self.start_date,
            'expense_date__lte': self.end_date,
        }
        if self.category:
            filters['category'] = self.category
        
        return Expense.objects.filter(**filters).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
    
    @property
    def remaining_amount(self):
        return self.allocated_amount - self.spent_amount
    
    @property
    def utilization_percentage(self):
        if self.allocated_amount == 0:
            return 0
        return round((self.spent_amount / self.allocated_amount) * 100, 2)
    
    @property
    def is_over_budget(self):
        return self.spent_amount > self.allocated_amount