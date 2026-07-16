"""
El Mercado - Hybrid Multi-Vendor Marketplace Platform
======================================================
Supports B2C (Business-to-Consumer) and P2P (Peer-to-Peer) commerce.

Key Features:
- Seller onboarding with verification and approval workflow
- Wallet system for balance tracking and payouts
- Multi-vendor storefronts
- Product and service listings
- Order management with escrow support
- Reviews and ratings
- Commission and fee handling
- Messaging system between buyers and sellers
- Separate seller authentication system (independent from user accounts)
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from uuid import uuid4
import secrets
import string
from phonenumber_field.modelfields import PhoneNumberField

from accounts.models import CustomUser
from utils.dynamic_storage import DynamicStorage
from utils.media_mixins import MediaUrlMixin


# =============================================================================
# SELLER MODELS
# =============================================================================

class SellerApplication(MediaUrlMixin, models.Model):
    """
    Seller Application for users wanting to become sellers.
    Supports both B2C (Business) and P2P (Individual) sellers.
    """
    
    MEDIA_URL_FIELDS = {
        'id_document': 'id_document_url',
        'business_document': 'business_document_url',
        'proof_of_address': 'proof_of_address_url',
    }
    
    SELLER_TYPE_CHOICES = [
        ('INDIVIDUAL', 'Individual Seller (P2P)'),
        ('BUSINESS', 'Business/Merchant (B2C)'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('REVISION_REQUESTED', 'Revision Requested'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    # Tracking code for non-users to check status
    tracking_code = models.CharField(
        max_length=12,
        unique=True,
        blank=True,
        help_text="Unique code for applicants to check their status"
    )
    
    # Applicant (can be null for non-user sellers applying)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='seller_applications',
        null=True,
        blank=True,
        help_text="User applying to become a seller (null for external applicants)"
    )
    
    # Basic Information
    seller_type = models.CharField(max_length=20, choices=SELLER_TYPE_CHOICES)
    
    # Contact Information (for non-user applicants or additional contact)
    applicant_name = models.CharField(max_length=255, help_text="Full name of applicant")
    applicant_email = models.EmailField(help_text="Contact email")
    applicant_phone = PhoneNumberField(help_text="Contact phone number")
    
    # Business Information (for B2C sellers)
    business_name = models.CharField(max_length=255, blank=True, help_text="Business/Store name")
    business_registration_number = models.CharField(max_length=100, blank=True)
    business_type = models.CharField(max_length=100, blank=True, help_text="e.g., Sole Proprietorship, LLC, etc.")
    
    # Address
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Ghana')
    
    # Verification Documents
    id_document = models.FileField(
        storage=DynamicStorage(),
        upload_to='el_mercado/seller_applications/id_documents/',
        help_text="Government-issued ID (required for all sellers)"
    )
    id_document_url = models.URLField(blank=True, null=True)
    id_document_type = models.CharField(
        max_length=50,
        choices=[
            ('NATIONAL_ID', 'National ID Card'),
            ('PASSPORT', 'Passport'),
            ('DRIVERS_LICENSE', "Driver's License"),
            ('VOTER_ID', "Voter's ID"),
        ]
    )
    
    business_document = models.FileField(
        storage=DynamicStorage(),
        upload_to='el_mercado/seller_applications/business_documents/',
        blank=True,
        null=True,
        help_text="Business registration certificate (required for B2C sellers)"
    )
    business_document_url = models.URLField(blank=True, null=True)
    
    proof_of_address = models.FileField(
        storage=DynamicStorage(),
        upload_to='el_mercado/seller_applications/proof_of_address/',
        blank=True,
        null=True,
        help_text="Utility bill or bank statement"
    )
    proof_of_address_url = models.URLField(blank=True, null=True)
    
    # Application Details
    description = models.TextField(
        help_text="Brief description of what you plan to sell"
    )
    categories_of_interest = models.JSONField(
        default=list,
        help_text="List of category IDs the seller wants to sell in"
    )
    
    # Status & Review
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    status_reason = models.TextField(blank=True, help_text="Reason for rejection or revision request")
    
    reviewed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_seller_applications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Seller Application"
        verbose_name_plural = "Seller Applications"
    
    def __str__(self):
        name = self.business_name if self.seller_type == 'BUSINESS' else self.applicant_name
        return f"{name} - {self.get_status_display()}"
    
    def approve(self, reviewer, send_credentials=True):
        """
        Approve the application and create a Seller profile.
        Generates temporary credentials for the seller portal.
        
        Args:
            reviewer: The admin user approving the application
            send_credentials: Whether to send login credentials (default: True)
        
        Returns:
            tuple: (seller, temporary_password) if send_credentials=True, else seller
        """
        self.status = 'APPROVED'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
        
        # Create Seller profile
        seller = Seller.objects.create(
            application=self,
            user=self.user,
            seller_type=self.seller_type,
            display_name=self.business_name or self.applicant_name,
            email=self.applicant_email,
            phone=self.applicant_phone,
            status='ACTIVE',
        )
        
        # Generate temporary password for seller portal access
        temp_password = seller.generate_temporary_password()
        seller.save()
        
        # Create wallet for seller
        SellerWallet.objects.create(seller=seller)
        
        if send_credentials:
            # Send credentials email automatically
            email_sent = self._send_credentials_email(seller, temp_password)
            return seller, temp_password, email_sent
        return seller
    
    def reject(self, reviewer, reason):
        """Reject the application"""
        self.status = 'REJECTED'
        self.status_reason = reason
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
    
    def _send_credentials_email(self, seller, temp_password):
        """Send credentials email to newly approved seller"""
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from django.conf import settings as django_settings
        from datetime import datetime
        
        if not seller.email:
            return False
        
        login_url = getattr(
            django_settings, 
            'SELLER_PORTAL_LOGIN_URL',
            f"{getattr(django_settings, 'BACKEND_URL', 'https://api.thecssknust.com')}/api/el-mercado/seller/login/"
        )
        
        context = {
            'seller_name': seller.display_name,
            'seller_email': seller.email,
            'seller_phone': str(seller.phone),
            'temp_password': temp_password,
            'login_url': login_url,
            'year': datetime.now().year,
        }
        
        try:
            # Try to render HTML template first
            html_content = render_to_string('el_mercado/emails/seller_credentials.html', context)
            text_content = strip_tags(html_content)
        except Exception:
            # Fallback to plain text if template fails
            text_content = f"""
Hello {seller.display_name},

Congratulations! Your El Mercado seller application has been approved.

Your seller dashboard login credentials have been generated:

LOGIN DETAILS:
--------------
Login URL: {login_url}
Email: {seller.email}
Phone: {seller.phone}
Temporary Password: {temp_password}

IMPORTANT: Please change your password after your first login for security.

You can now:
- Add your products/services
- Manage your store
- Track your orders
- View your earnings

Welcome to El Mercado!

Best regards,
The El Mercado Team
            """
            html_content = None
        
        try:
            email = EmailMultiAlternatives(
                subject='🛍️ El Mercado - Welcome! Your Seller Account is Approved',
                body=text_content,
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                to=[seller.email],
            )
            
            if html_content:
                email.attach_alternative(html_content, "text/html")
            
            email.send(fail_silently=False)
            return True
        except Exception as e:
            # Log the error but don't fail the approval process
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send credentials email to {seller.email}: {e}")
            return False
    
    def request_revision(self, reviewer, reason):
        """Request revision/additional documents"""
        self.status = 'REVISION_REQUESTED'
        self.status_reason = reason
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
    
    def generate_tracking_code(self):
        """Generate a unique tracking code for the application"""
        import random
        import string
        while True:
            # Format: ELM-XXXXXXXX (8 alphanumeric chars)
            code = 'ELM-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not SellerApplication.objects.filter(tracking_code=code).exists():
                return code
    
    def save(self, *args, **kwargs):
        # Generate tracking code if not set
        if not self.tracking_code:
            self.tracking_code = self.generate_tracking_code()
        super().save(*args, **kwargs)


class Seller(MediaUrlMixin, models.Model):
    """
    Approved Seller profile.
    Sellers can be linked to a user or operate independently (for businesses).
    
    Authentication System:
    - Sellers have their own separate authentication system
    - Uses email/phone + password (independent from Django user system)
    - Credentials are generated on approval and sent to seller
    - Sellers can reset their password without needing a user account
    """
    
    MEDIA_URL_FIELDS = {
        'logo': 'logo_url',
        'banner': 'banner_url',
    }
    
    SELLER_TYPE_CHOICES = [
        ('INDIVIDUAL', 'Individual Seller (P2P)'),
        ('BUSINESS', 'Business/Merchant (B2C)'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('BANNED', 'Banned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    # Link to application
    application = models.OneToOneField(
        SellerApplication,
        on_delete=models.PROTECT,
        related_name='seller_profile'
    )
    
    # User link (optional - businesses may not have a user account)
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='seller_profile'
    )
    
    # =========================================================================
    # SELLER AUTHENTICATION FIELDS (Separate from Django User Auth)
    # =========================================================================
    password = models.CharField(
        max_length=128,
        blank=True,
        help_text="Hashed password for seller portal login"
    )
    is_credentials_set = models.BooleanField(
        default=False,
        help_text="Whether seller has set up their login credentials"
    )
    password_reset_token = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Token for password reset"
    )
    password_reset_token_created = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the reset token was created"
    )
    last_login = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last successful seller portal login"
    )
    failed_login_attempts = models.IntegerField(
        default=0,
        help_text="Number of consecutive failed login attempts"
    )
    locked_until = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Account locked until this time due to failed attempts"
    )
    
    # Seller Details
    seller_type = models.CharField(max_length=20, choices=SELLER_TYPE_CHOICES)
    display_name = models.CharField(max_length=255, help_text="Public display name")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    
    # Contact
    email = models.EmailField()
    phone = PhoneNumberField()
    
    # Branding
    logo = models.ImageField(
        storage=DynamicStorage(),
        upload_to='el_mercado/sellers/logos/',
        blank=True,
        null=True
    )
    logo_url = models.URLField(blank=True, null=True)
    
    banner = models.ImageField(
        storage=DynamicStorage(),
        upload_to='el_mercado/sellers/banners/',
        blank=True,
        null=True
    )
    banner_url = models.URLField(blank=True, null=True)
    
    description = models.TextField(blank=True, help_text="About the seller/store")
    
    # Policies
    shipping_policy = models.TextField(
        blank=True,
        help_text="Seller's shipping policy and estimated delivery times"
    )
    return_policy = models.TextField(
        blank=True,
        help_text="Seller's return and refund policy"
    )
    
    # Social Links
    website = models.URLField(blank=True, null=True, help_text="Your business website")
    instagram = models.CharField(max_length=100, blank=True, help_text="Instagram username")
    twitter = models.CharField(max_length=100, blank=True, help_text="Twitter/X username")
    facebook = models.CharField(max_length=100, blank=True, help_text="Facebook page name")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    status_reason = models.TextField(blank=True)
    
    # Verification & Trust
    is_verified = models.BooleanField(default=False, help_text="Verified seller badge")
    verification_level = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1-5 verification level"
    )
    
    # Ratings
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.IntegerField(default=0)
    total_sales = models.IntegerField(default=0)
    
    # Commission Rate (can be customized per seller)
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Platform commission percentage"
    )
    
    # Settings
    auto_accept_orders = models.BooleanField(
        default=True,
        help_text="Automatically accept incoming orders"
    )
    vacation_mode = models.BooleanField(
        default=False,
        help_text="Temporarily disable store"
    )
    vacation_message = models.TextField(blank=True)
    
    # Notification Preferences
    notify_new_orders = models.BooleanField(
        default=True,
        help_text="Receive notifications for new orders"
    )
    notify_messages = models.BooleanField(
        default=True,
        help_text="Receive notifications for new customer messages"
    )
    notify_reviews = models.BooleanField(
        default=True,
        help_text="Receive notifications for new reviews"
    )
    notify_low_stock = models.BooleanField(
        default=True,
        help_text="Receive notifications when items are low in stock"
    )
    notify_payouts = models.BooleanField(
        default=True,
        help_text="Receive notifications for payout updates"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Seller"
        verbose_name_plural = "Sellers"
    
    def __str__(self):
        return f"{self.display_name} ({self.get_seller_type_display()})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.display_name)
            slug = base_slug
            counter = 1
            while Seller.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        return self.status == 'ACTIVE' and not self.vacation_mode
    
    def update_rating(self):
        """Recalculate average rating from reviews"""
        from django.db.models import Avg
        reviews = self.reviews.filter(is_approved=True)
        avg = reviews.aggregate(avg=Avg('rating'))['avg']
        self.average_rating = avg or Decimal('0.00')
        self.total_reviews = reviews.count()
        self.save(update_fields=['average_rating', 'total_reviews'])
    
    # =========================================================================
    # SELLER AUTHENTICATION METHODS
    # =========================================================================
    
    def set_password(self, raw_password):
        """Set password using Django's password hasher"""
        self.password = make_password(raw_password)
        self.is_credentials_set = True
        self.password_reset_token = None
        self.password_reset_token_created = None
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def check_password(self, raw_password):
        """Verify password against stored hash"""
        return check_password(raw_password, self.password)
    
    def generate_temporary_password(self):
        """Generate a temporary password for new sellers"""
        # Generate a secure 12-character password
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        self.set_password(password)
        self.is_credentials_set = False  # Mark as temporary
        return password
    
    def generate_password_reset_token(self):
        """Generate a password reset token"""
        self.password_reset_token = secrets.token_urlsafe(48)
        self.password_reset_token_created = timezone.now()
        self.save(update_fields=['password_reset_token', 'password_reset_token_created'])
        return self.password_reset_token
    
    def is_password_reset_token_valid(self, token, max_age_hours=24):
        """Check if the password reset token is valid and not expired"""
        if not self.password_reset_token or self.password_reset_token != token:
            return False
        if not self.password_reset_token_created:
            return False
        expiry_time = self.password_reset_token_created + timezone.timedelta(hours=max_age_hours)
        return timezone.now() < expiry_time
    
    def is_account_locked(self):
        """Check if account is locked due to failed login attempts"""
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False
    
    def record_failed_login(self, max_attempts=5, lockout_minutes=30):
        """Record a failed login attempt and potentially lock the account"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=lockout_minutes)
        self.save(update_fields=['failed_login_attempts', 'locked_until'])
    
    def record_successful_login(self):
        """Record a successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = timezone.now()
        self.save(update_fields=['failed_login_attempts', 'locked_until', 'last_login'])
    
    @classmethod
    def authenticate(cls, email_or_phone, password):
        """
        Authenticate a seller by email or phone number.
        Returns (seller, error_message) tuple.
        """
        from django.db.models import Q
        
        try:
            # Try to find seller by email or phone
            seller = cls.objects.get(
                Q(email__iexact=email_or_phone) | Q(phone=email_or_phone)
            )
        except cls.DoesNotExist:
            return None, "Invalid credentials"
        except cls.MultipleObjectsReturned:
            # Shouldn't happen, but handle it
            return None, "Multiple accounts found. Please contact support."
        
        # Check if account is locked
        if seller.is_account_locked():
            remaining = (seller.locked_until - timezone.now()).seconds // 60
            return None, f"Account is locked. Try again in {remaining} minutes."
        
        # Check if seller is active
        if seller.status == 'SUSPENDED':
            return None, "Your seller account is suspended. Please contact support."
        if seller.status == 'BANNED':
            return None, "Your seller account has been banned."
        if seller.status == 'INACTIVE':
            return None, "Your seller account is inactive."
        
        # Verify password
        if not seller.check_password(password):
            seller.record_failed_login()
            remaining_attempts = 5 - seller.failed_login_attempts
            if remaining_attempts > 0:
                return None, f"Invalid credentials. {remaining_attempts} attempts remaining."
            else:
                return None, "Account locked due to too many failed attempts."
        
        # Successful authentication
        seller.record_successful_login()
        return seller, None


# =============================================================================
# WALLET & PAYOUT MODELS
# =============================================================================

class SellerWallet(models.Model):
    """
    Seller's wallet for tracking balance, pending amounts, and payouts.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    seller = models.OneToOneField(
        Seller,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    
    # Balances
    available_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Available for withdrawal"
    )
    pending_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="From orders not yet completed/released"
    )
    total_earned = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total earnings (lifetime)"
    )
    total_withdrawn = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total amount withdrawn"
    )
    total_fees_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total platform fees paid"
    )
    
    # Currency
    currency = models.CharField(max_length=3, default='GHS')
    
    # Settings
    minimum_payout_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('50.00'),
        help_text="Minimum amount for payout request"
    )
    auto_payout_enabled = models.BooleanField(
        default=False,
        help_text="Automatically request payout when threshold is reached"
    )
    auto_payout_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('500.00'),
        help_text="Balance threshold for auto-payout"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Seller Wallet"
        verbose_name_plural = "Seller Wallets"
    
    def __str__(self):
        return f"{self.seller.display_name}'s Wallet - {self.currency} {self.available_balance}"
    
    def add_pending(self, amount, description=""):
        """Add amount to pending balance (from new order)"""
        self.pending_balance += amount
        self.save(update_fields=['pending_balance', 'updated_at'])
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='CREDIT_PENDING',
            amount=amount,
            description=description,
            balance_after=self.available_balance
        )
    
    def release_pending(self, amount, description=""):
        """Move amount from pending to available (order completed)"""
        if amount > self.pending_balance:
            raise ValueError("Amount exceeds pending balance")
        
        self.pending_balance -= amount
        self.available_balance += amount
        self.total_earned += amount
        self.save(update_fields=['pending_balance', 'available_balance', 'total_earned', 'updated_at'])
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='RELEASE',
            amount=amount,
            description=description,
            balance_after=self.available_balance
        )
    
    def deduct_fee(self, amount, description="Platform commission"):
        """Deduct platform fee from pending amount"""
        self.total_fees_paid += amount
        self.save(update_fields=['total_fees_paid', 'updated_at'])
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='FEE',
            amount=amount,
            description=description,
            balance_after=self.available_balance
        )
    
    def withdraw(self, amount, description=""):
        """Withdraw from available balance"""
        if amount > self.available_balance:
            raise ValueError("Amount exceeds available balance")
        
        self.available_balance -= amount
        self.total_withdrawn += amount
        self.save(update_fields=['available_balance', 'total_withdrawn', 'updated_at'])
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='WITHDRAWAL',
            amount=amount,
            description=description,
            balance_after=self.available_balance
        )


class WalletTransaction(models.Model):
    """
    Transaction history for seller wallets.
    """
    
    TRANSACTION_TYPE_CHOICES = [
        ('CREDIT_PENDING', 'Credit (Pending)'),
        ('RELEASE', 'Release to Available'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('FEE', 'Platform Fee'),
        ('REFUND_DEDUCT', 'Refund Deduction'),
        ('ADJUSTMENT', 'Manual Adjustment'),
        ('BONUS', 'Bonus/Incentive'),
        ('PAYOUT_HOLD', 'Payout Hold'),
        ('PAYOUT_COMPLETE', 'Payout Completed'),
        ('PAYOUT_REFUND', 'Payout Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    wallet = models.ForeignKey(
        SellerWallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    
    # Reference to related objects
    reference_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    reference_id = models.CharField(max_length=255, blank=True)
    reference_object = GenericForeignKey('reference_type', 'reference_id')
    
    # Balance snapshot
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Wallet Transaction"
        verbose_name_plural = "Wallet Transactions"
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount}"


class PayoutRequest(models.Model):
    """
    Seller payout/withdrawal requests.
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYOUT_METHOD_CHOICES = [
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('PAYSTACK', 'Paystack Transfer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    reference = models.CharField(max_length=100, unique=True)
    
    wallet = models.ForeignKey(
        SellerWallet,
        on_delete=models.CASCADE,
        related_name='payout_requests'
    )
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    processing_fee = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Fee charged for processing the payout"
    )
    net_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount seller receives after processing fee"
    )
    currency = models.CharField(max_length=3, default='GHS')
    
    # Payout details
    payout_method = models.CharField(max_length=20, choices=PAYOUT_METHOD_CHOICES)
    
    # Bank details (if bank transfer)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_code = models.CharField(max_length=20, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    account_name = models.CharField(max_length=255, blank=True)
    
    # Mobile Money details
    mobile_money_provider = models.CharField(max_length=50, blank=True)
    mobile_money_number = PhoneNumberField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    status_message = models.TextField(blank=True)
    
    # Gateway reference (for tracking)
    gateway_reference = models.CharField(max_length=255, blank=True)
    
    # Processing
    processed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_payouts'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payout Request"
        verbose_name_plural = "Payout Requests"
    
    def __str__(self):
        return f"{self.reference} - {self.currency} {self.amount} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            import secrets
            self.reference = f"PO-{secrets.token_hex(6).upper()}"
        super().save(*args, **kwargs)


class SellerPayoutAccount(models.Model):
    """
    Saved payout accounts for sellers.
    """
    
    ACCOUNT_TYPE_CHOICES = [
        ('BANK', 'Bank Account'),
        ('MOBILE_MONEY', 'Mobile Money'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        related_name='payout_accounts'
    )
    
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    is_default = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # Bank details
    bank_name = models.CharField(max_length=100, blank=True)
    bank_code = models.CharField(max_length=20, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    account_name = models.CharField(max_length=255, blank=True)
    
    # Mobile Money
    mobile_money_provider = models.CharField(max_length=50, blank=True)
    mobile_money_number = PhoneNumberField(blank=True, null=True)
    mobile_money_name = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Seller Payout Account"
        verbose_name_plural = "Seller Payout Accounts"
    
    def __str__(self):
        if self.account_type == 'BANK':
            return f"{self.bank_name} - {self.account_number[-4:]}"
        return f"{self.mobile_money_provider} - {self.mobile_money_number}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default account per seller
        if self.is_default:
            SellerPayoutAccount.objects.filter(
                seller=self.seller,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# =============================================================================
# STORE & PRODUCT MODELS
# =============================================================================

class Category(models.Model):
    """
    Product/Service categories.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class or emoji")
    image = models.ImageField(
        storage=DynamicStorage(),
        upload_to='el_mercado/categories/',
        blank=True,
        null=True
    )
    
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Commission override for category
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Override default commission for this category"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "Category"
        verbose_name_plural = "Categories"
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Listing(MediaUrlMixin, models.Model):
    """
    Product or Service listing by a seller.
    """
    
    MEDIA_URL_FIELDS = {
        'main_image': 'main_image_url',
    }
    
    LISTING_TYPE_CHOICES = [
        ('PRODUCT', 'Physical Product'),
        ('DIGITAL', 'Digital Product'),
        ('SERVICE', 'Service'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_REVIEW', 'Pending Review'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SOLD_OUT', 'Sold Out'),
        ('ARCHIVED', 'Archived'),
        ('REJECTED', 'Rejected'),
    ]
    
    CONDITION_CHOICES = [
        ('NEW', 'New'),
        ('LIKE_NEW', 'Like New'),
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
        ('USED', 'Used'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        related_name='listings'
    )
    
    # Basic Info
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField()
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPE_CHOICES)
    
    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='listings'
    )
    tags = models.JSONField(default=list, blank=True)
    
    # Pricing
    price = models.DecimalField(max_digits=12, decimal_places=2)
    compare_at_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original price for showing discounts"
    )
    currency = models.CharField(max_length=3, default='GHS')
    
    # Inventory (for products)
    stock_quantity = models.IntegerField(default=0)
    track_inventory = models.BooleanField(default=True)
    allow_backorder = models.BooleanField(default=False)
    low_stock_threshold = models.IntegerField(default=5)
    
    # Condition (for P2P/used items)
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='NEW'
    )
    
    # Images
    main_image = models.ImageField(
        storage=DynamicStorage(),
        upload_to='el_mercado/listings/',
        blank=True,
        null=True
    )
    main_image_url = models.URLField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    rejection_reason = models.TextField(blank=True)
    
    # Shipping (for physical products)
    requires_shipping = models.BooleanField(default=True)
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Weight in kg"
    )
    shipping_info = models.TextField(blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    
    # Stats
    view_count = models.IntegerField(default=0)
    favorite_count = models.IntegerField(default=0)
    order_count = models.IntegerField(default=0)
    
    # Ratings
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00')
    )
    review_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Listing"
        verbose_name_plural = "Listings"
        indexes = [
            models.Index(fields=['status', 'seller']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['price']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.seller.display_name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Listing.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    @property
    def is_in_stock(self):
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0 or self.allow_backorder
    
    @property
    def is_low_stock(self):
        return self.track_inventory and 0 < self.stock_quantity <= self.low_stock_threshold
    
    @property
    def discount_percentage(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return int(((self.compare_at_price - self.price) / self.compare_at_price) * 100)
        return 0
    
    def publish(self):
        """Publish the listing"""
        self.status = 'ACTIVE'
        self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at'])
    
    def reduce_stock(self, quantity=1):
        """Reduce stock after purchase"""
        if self.track_inventory:
            self.stock_quantity = max(0, self.stock_quantity - quantity)
            if self.stock_quantity == 0 and not self.allow_backorder:
                self.status = 'SOLD_OUT'
            self.save(update_fields=['stock_quantity', 'status'])


class ListingImage(MediaUrlMixin, models.Model):
    """
    Additional images for listings.
    """
    
    MEDIA_URL_FIELDS = {
        'image': 'image_url',
    }
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='images'
    )
    
    image = models.ImageField(
        storage=DynamicStorage(),
        upload_to='el_mercado/listings/gallery/'
    )
    image_url = models.URLField(blank=True, null=True)
    
    alt_text = models.CharField(max_length=255, blank=True)
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order']
        verbose_name = "Listing Image"
        verbose_name_plural = "Listing Images"


class ListingVariant(models.Model):
    """
    Product variants (size, color, etc.)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    
    name = models.CharField(max_length=100, help_text="e.g., 'Red / Large'")
    sku = models.CharField(max_length=100, blank=True)
    
    # Variant attributes
    attributes = models.JSONField(
        default=dict,
        help_text="e.g., {'color': 'Red', 'size': 'Large'}"
    )
    
    # Pricing override
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Override base price"
    )
    
    # Inventory
    stock_quantity = models.IntegerField(default=0)
    
    # Image
    image = models.ImageField(
        storage=DynamicStorage(),
        upload_to='el_mercado/listings/variants/',
        blank=True,
        null=True
    )
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Listing Variant"
        verbose_name_plural = "Listing Variants"
    
    def __str__(self):
        return f"{self.listing.title} - {self.name}"
    
    @property
    def effective_price(self):
        return self.price if self.price else self.listing.price


# =============================================================================
# ORDER MODELS
# =============================================================================

class MarketplaceOrder(models.Model):
    """
    Order placed by a buyer (must be a registered user).
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('AWAITING_PAYMENT', 'Awaiting Payment'),
        ('PAID', 'Paid'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
        ('DISPUTED', 'Disputed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    order_number = models.CharField(max_length=50, unique=True)
    
    # Buyer (MUST be a user)
    buyer = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='marketplace_orders'
    )
    
    # Seller
    seller = models.ForeignKey(
        Seller,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    
    # Amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='GHS')
    
    # Commission
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)
    seller_earnings = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    status_history = models.JSONField(default=list)
    
    # Payment
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PAID', 'Paid'),
            ('FAILED', 'Failed'),
            ('REFUNDED', 'Refunded'),
        ],
        default='PENDING'
    )
    payment_reference = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Shipping Address
    shipping_name = models.CharField(max_length=255)
    shipping_phone = PhoneNumberField()
    shipping_email = models.EmailField(blank=True)
    shipping_address_line_1 = models.CharField(max_length=255)
    shipping_address_line_2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_region = models.CharField(max_length=100, blank=True)
    shipping_country = models.CharField(max_length=100, default='Ghana')
    shipping_digital_address = models.CharField(max_length=20, blank=True, help_text="Ghana Post GPS Digital Address (e.g., GA-123-4567)")
    shipping_landmark = models.CharField(max_length=255, blank=True, help_text="Nearby landmark for easy location")
    delivery_instructions = models.TextField(blank=True, help_text="Special delivery instructions")
    
    # Link to saved shipping address
    shipping_address = models.ForeignKey(
        'accounts.ShippingAddress',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text="Reference to buyer's saved shipping address"
    )
    
    # Tracking
    tracking_number = models.CharField(max_length=100, blank=True)
    tracking_url = models.URLField(blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery Verification Code
    # This code is generated when the order is shipped and given to the buyer.
    # The buyer must give this code to the seller upon delivery to confirm receipt.
    delivery_code = models.CharField(
        max_length=6, 
        blank=True,
        help_text="6-digit code buyer gives to seller to confirm delivery"
    )
    delivery_code_generated_at = models.DateTimeField(null=True, blank=True)
    delivery_verified = models.BooleanField(
        default=False,
        help_text="Whether delivery has been verified with the code"
    )
    delivery_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    buyer_notes = models.TextField(blank=True)
    seller_notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Escrow
    funds_released = models.BooleanField(
        default=False,
        help_text="Whether seller funds have been released"
    )
    funds_released_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Marketplace Order"
        verbose_name_plural = "Marketplace Orders"
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            import secrets
            self.order_number = f"EM-{timezone.now().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
        
        # Calculate seller earnings
        self.platform_commission = self.total_amount * (self.commission_rate / 100)
        self.seller_earnings = self.total_amount - self.platform_commission
        
        super().save(*args, **kwargs)
    
    def update_status(self, new_status, note=""):
        """Update order status with history"""
        old_status = self.status
        self.status = new_status
        
        self.status_history.append({
            'from': old_status,
            'to': new_status,
            'note': note,
            'timestamp': timezone.now().isoformat()
        })
        
        self.save(update_fields=['status', 'status_history', 'updated_at'])
        
        # Auto-increment seller's total_sales when order is completed
        if new_status == 'COMPLETED' and old_status != 'COMPLETED':
            self.seller.total_sales += 1
            self.seller.save(update_fields=['total_sales'])
    
    def generate_delivery_code(self):
        """
        Generate a 6-digit delivery verification code.
        This code should be shown to the buyer and they give it to the seller
        upon receiving the order to confirm delivery.
        """
        import random
        self.delivery_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.delivery_code_generated_at = timezone.now()
        self.save(update_fields=['delivery_code', 'delivery_code_generated_at'])
        return self.delivery_code
    
    def verify_delivery_code(self, code):
        """
        Verify the delivery code provided by the seller.
        Returns True if code matches, False otherwise.
        """
        if not self.delivery_code:
            return False
        
        if self.delivery_code == code.strip():
            self.delivery_verified = True
            self.delivery_verified_at = timezone.now()
            self.delivered_at = timezone.now()
            self.save(update_fields=['delivery_verified', 'delivery_verified_at', 'delivered_at'])
            return True
        return False
    
    def release_funds(self):
        """Release funds to seller wallet"""
        if self.funds_released:
            return False
        
        wallet = self.seller.wallet
        
        # Track platform commission fee
        if self.platform_commission > 0:
            wallet.deduct_fee(
                self.platform_commission, 
                f"Platform commission - Order {self.order_number}"
            )
        
        # Release net amount to seller's available balance
        net_amount = self.seller_earnings
        wallet.release_pending(net_amount, f"Order {self.order_number} completed")
        
        self.funds_released = True
        self.funds_released_at = timezone.now()
        self.save(update_fields=['funds_released', 'funds_released_at'])
        
        return True


class OrderItem(models.Model):
    """
    Individual items in an order.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    order = models.ForeignKey(
        MarketplaceOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    listing = models.ForeignKey(
        Listing,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )
    variant = models.ForeignKey(
        ListingVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Snapshot of listing at time of order
    listing_title = models.CharField(max_length=255)
    listing_image_url = models.URLField(blank=True)
    variant_name = models.CharField(max_length=100, blank=True)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
    
    def __str__(self):
        return f"{self.quantity}x {self.listing_title}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


# =============================================================================
# REVIEW & RATING MODELS
# =============================================================================

class Review(models.Model):
    """
    Reviews for listings and sellers.
    """
    
    REVIEW_TYPE_CHOICES = [
        ('LISTING', 'Listing Review'),
        ('SELLER', 'Seller Review'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPE_CHOICES)
    
    # Reviewer (buyer)
    reviewer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='marketplace_reviews'
    )
    
    # Reviewed entity
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reviews'
    )
    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reviews'
    )
    
    # Related order
    order = models.ForeignKey(
        MarketplaceOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews'
    )
    
    # Review content
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_verified_purchase = models.BooleanField(default=False)
    
    # Seller response
    seller_response = models.TextField(blank=True)
    seller_responded_at = models.DateTimeField(null=True, blank=True)
    
    # Helpfulness
    helpful_count = models.IntegerField(default=0)
    unhelpful_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
    
    def __str__(self):
        target = self.listing.title if self.listing else self.seller.display_name
        return f"{self.rating}★ review for {target}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update listing/seller ratings
        if self.listing:
            self.listing.average_rating = self.listing.reviews.filter(
                is_approved=True
            ).aggregate(avg=models.Avg('rating'))['avg'] or Decimal('0.00')
            self.listing.review_count = self.listing.reviews.filter(is_approved=True).count()
            self.listing.save(update_fields=['average_rating', 'review_count'])
        
        if self.seller:
            self.seller.update_rating()


# =============================================================================
# COMMUNICATION MODELS
# =============================================================================

class Conversation(models.Model):
    """
    Conversation thread between buyer and seller.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    buyer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='buyer_conversations'
    )
    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    
    # Optional link to listing or order
    listing = models.ForeignKey(
        Listing,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations'
    )
    order = models.ForeignKey(
        MarketplaceOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations'
    )
    
    # Status
    is_archived_by_buyer = models.BooleanField(default=False)
    is_archived_by_seller = models.BooleanField(default=False)
    
    # Unread counts
    buyer_unread_count = models.IntegerField(default=0)
    seller_unread_count = models.IntegerField(default=0)
    
    # Last message timestamp (for sorting)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_message_at']
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        unique_together = [['buyer', 'seller', 'listing']]
    
    def __str__(self):
        return f"Chat: {self.buyer.get_full_name()} ↔ {self.seller.display_name}"


class Message(models.Model):
    """
    Individual messages in a conversation.
    """
    
    SENDER_TYPE_CHOICES = [
        ('BUYER', 'Buyer'),
        ('SELLER', 'Seller'),
        ('SYSTEM', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPE_CHOICES)
    sender_user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marketplace_messages'
    )
    
    content = models.TextField()
    
    # Attachments
    attachment = models.FileField(
        storage=DynamicStorage(),
        upload_to='el_mercado/messages/',
        blank=True,
        null=True
    )
    attachment_name = models.CharField(max_length=255, blank=True)
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Message"
        verbose_name_plural = "Messages"
    
    def __str__(self):
        return f"{self.get_sender_type_display()}: {self.content[:50]}..."
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update conversation
        self.conversation.last_message_at = self.created_at
        
        if self.sender_type == 'BUYER':
            self.conversation.seller_unread_count += 1
        elif self.sender_type == 'SELLER':
            self.conversation.buyer_unread_count += 1
        
        self.conversation.save(update_fields=['last_message_at', 'buyer_unread_count', 'seller_unread_count'])


# =============================================================================
# FAVORITES & WISHLIST
# =============================================================================

class Favorite(models.Model):
    """
    User's favorite/wishlisted listings.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='marketplace_favorites'
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['user', 'listing']]
        verbose_name = "Favorite"
        verbose_name_plural = "Favorites"
    
    def __str__(self):
        return f"{self.user.get_full_name()} ♥ {self.listing.title}"


class FollowedSeller(models.Model):
    """
    Users following sellers for updates.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='followed_sellers'
    )
    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        related_name='followers'
    )
    
    # Notification preferences
    notify_new_listings = models.BooleanField(default=True)
    notify_sales = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['user', 'seller']]
        verbose_name = "Followed Seller"
        verbose_name_plural = "Followed Sellers"
    
    def __str__(self):
        return f"{self.user.get_full_name()} follows {self.seller.display_name}"


# =============================================================================
# DISPUTE MODELS
# =============================================================================

class Dispute(models.Model):
    """
    Order disputes between buyers and sellers.
    """
    
    REASON_CHOICES = [
        ('NOT_RECEIVED', 'Item Not Received'),
        ('NOT_AS_DESCRIBED', 'Item Not As Described'),
        ('DAMAGED', 'Item Damaged'),
        ('WRONG_ITEM', 'Wrong Item Received'),
        ('QUALITY_ISSUE', 'Quality Issue'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('UNDER_REVIEW', 'Under Review'),
        ('AWAITING_SELLER', 'Awaiting Seller Response'),
        ('AWAITING_BUYER', 'Awaiting Buyer Response'),
        ('RESOLVED_BUYER_FAVOR', 'Resolved in Buyer Favor'),
        ('RESOLVED_SELLER_FAVOR', 'Resolved in Seller Favor'),
        ('RESOLVED_COMPROMISE', 'Resolved with Compromise'),
        ('CLOSED', 'Closed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    reference = models.CharField(max_length=50, unique=True)
    
    order = models.ForeignKey(
        MarketplaceOrder,
        on_delete=models.CASCADE,
        related_name='disputes'
    )
    
    # Initiator
    initiated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='initiated_disputes'
    )
    
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField()
    
    # Evidence
    evidence = models.JSONField(
        default=list,
        help_text="List of evidence URLs and descriptions"
    )
    
    # Status
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='OPEN')
    
    # Resolution
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_disputes'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Refund amount (if applicable)
    refund_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Dispute"
        verbose_name_plural = "Disputes"
    
    def __str__(self):
        return f"Dispute {self.reference} - {self.get_reason_display()}"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            import secrets
            self.reference = f"DSP-{secrets.token_hex(6).upper()}"
        super().save(*args, **kwargs)


# =============================================================================
# PLATFORM SETTINGS & CONFIGURATION
# =============================================================================

class CommissionRate(models.Model):
    """
    Commission rates for different product/service categories.
    """
    
    CATEGORY_TYPE_CHOICES = [
        ('STANDARD', 'Standard Products'),
        ('DIGITAL', 'Digital Products'),
        ('SERVICES', 'Services'),
        ('HANDMADE', 'Handmade/Custom Items'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    category_type = models.CharField(
        max_length=20,
        choices=CATEGORY_TYPE_CHOICES,
        unique=True
    )
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Commission percentage for this category type"
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Commission Rate"
        verbose_name_plural = "Commission Rates"
        ordering = ['category_type']
    
    def __str__(self):
        return f"{self.get_category_type_display()}: {self.rate}%"
    
    @classmethod
    def get_rate(cls, category_type):
        """Get commission rate for a category type"""
        try:
            return cls.objects.get(category_type=category_type, is_active=True).rate
        except cls.DoesNotExist:
            # Fallback to marketplace default
            return MarketplaceSettings.get_settings().default_commission_rate


class MarketplaceSettings(models.Model):
    """
    Global marketplace settings (singleton).
    """
    
    # Commission
    default_commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00'),
        help_text="Default platform commission percentage (fallback)"
    )
    
    # Payment Processing
    payment_processing_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('2.5'),
        help_text="Payment gateway fee percentage"
    )
    payment_processing_fee_fixed = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Fixed payment gateway fee (GHS)"
    )
    
    # Payout Fees
    payout_transaction_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('5.00'),
        help_text="Fee per payout/withdrawal (GHS)"
    )
    payout_processing_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.7'),
        help_text="Payout processing fee percentage"
    )
    
    # Payout settings
    minimum_payout_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('50.00')
    )
    payout_processing_days = models.IntegerField(
        default=3,
        help_text="Days before funds can be withdrawn after order completion"
    )
    
    # Order settings
    auto_complete_days = models.IntegerField(
        default=7,
        help_text="Days after delivery to auto-complete order"
    )
    dispute_window_days = models.IntegerField(
        default=14,
        help_text="Days after delivery buyer can open dispute"
    )
    
    # Listing settings
    require_listing_approval = models.BooleanField(
        default=False,
        help_text="Require admin approval for new listings"
    )
    max_images_per_listing = models.IntegerField(default=10)
    
    # Updated
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Marketplace Settings"
        verbose_name_plural = "Marketplace Settings"
    
    def __str__(self):
        return "Marketplace Settings"
    
    @classmethod
    def get_settings(cls):
        """Get or create singleton settings"""
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings
