from django.db import models
from uuid import uuid4
import secrets
# CloudinaryField replaced with ImageField using DynamicStorage
# from cloudinary.models import CloudinaryField
from phonenumber_field.modelfields import PhoneNumberField
import string
from django.conf import settings
from utils.cloudinary_utils import get_optimized_cloudinary_url, get_card_image_url
from utils.media_mixins import MediaUrlMixin
from utils.dynamic_storage import DynamicStorage

# Create your models here.

type_of_product = [
    ("cloth", "cloth"),
    ("books", "books"),
    ("utilities", "utilities"),
    ("tickets", "tickets"),
]


class ProductColor(models.Model):
    """
    Available colors for products (e.g., Black, White, Blue, Red)
    Reusable across different products
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True, help_text="Color name (e.g., Black, Navy Blue)")
    hex_code = models.CharField(max_length=7, blank=True, help_text="Hex color code (e.g., #000000)")
    is_active = models.BooleanField(default=True, help_text="Available for selection")
    display_order = models.IntegerField(default=0, help_text="Display order (lower numbers first)")
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "Product Color"
        verbose_name_plural = "Product Colors"
    
    def __str__(self):
        return self.name


class ProductSize(models.Model):
    """
    Available sizes for products (e.g., S, M, L, XL, XXL)
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True, help_text="Size name (e.g., Small, Medium, Large)")
    code = models.CharField(max_length=10, unique=True, help_text="Size code (e.g., S, M, L, XL)")
    is_active = models.BooleanField(default=True, help_text="Available for selection")
    display_order = models.IntegerField(default=0, help_text="Display order (lower numbers first)")
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "Product Size"
        verbose_name_plural = "Product Sizes"
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class ProductColorImage(MediaUrlMixin, models.Model):
    """
    Through table for Product-Color relationship with color-specific images
    Allows each product to have different images for each color
    """
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'color_image': 'color_image_url',
    }
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='color_images')
    color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, related_name='product_images')
    
    # Color-specific product image
    color_image = models.ImageField(
        storage=DynamicStorage(),
        upload_to="ProductColorImages/",
        blank=True,
        null=True,
        help_text="Upload product image in this color"
    )
    color_image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide image URL for this color instead of uploading"
    )
    
    display_order = models.IntegerField(default=0, help_text="Display order for this color on the product")
    
    class Meta:
        ordering = ['product', 'display_order']
        unique_together = [['product', 'color']]
        verbose_name = "Product Color Image"
        verbose_name_plural = "Product Color Images"
    
    def get_image_url(self, optimized=True, width=400):
        """Get the appropriate image URL (uploaded or external) with optional optimization"""
        url = None
        if self.color_image:
            url = self.color_image.url
        else:
            url = self.color_image_url
        
        if url and optimized:
            return get_optimized_cloudinary_url(url, width=width)
        return url
    
    def __str__(self):
        return f"{self.product.product_name} - {self.color.name}"


class ProductVariantStock(models.Model):
    """
    Track inventory at the color+size variant level.
    
    Each combination of product + color + size has its own stock count.
    This enables:
    - Automatic removal of colors/sizes from availability when out of stock
    - Per-variant low stock alerts
    - Accurate stock checking during checkout
    - Stock reservation for cart items
    
    Examples:
    - T-Shirt (Black, Size M) → 50 units
    - T-Shirt (Black, Size L) → 30 units
    - T-Shirt (White, Size M) → 0 units (automatically hidden)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='variant_stocks'
    )
    color = models.ForeignKey(
        ProductColor,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='variant_stocks',
        help_text="Color for this variant (null if product has no colors)"
    )
    size = models.ForeignKey(
        ProductSize,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='variant_stocks',
        help_text="Size for this variant (null if product has no sizes)"
    )
    
    # Stock tracking
    stock_quantity = models.IntegerField(
        default=0,
        help_text="Available quantity for this specific variant"
    )
    low_stock_threshold = models.IntegerField(
        default=5,
        help_text="Alert when stock goes below this number"
    )
    
    # Reserved stock (items in cart but not yet purchased)
    reserved_quantity = models.IntegerField(
        default=0,
        help_text="Quantity reserved in active carts (not yet purchased)"
    )
    
    # SKU for this variant (optional)
    sku = models.CharField(
        max_length=100,
        blank=True,
        help_text="Stock Keeping Unit for this variant (e.g., TSHIRT-BLK-M)"
    )
    
    # Restock tracking
    last_restocked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this variant was last restocked"
    )
    restock_quantity = models.IntegerField(
        default=0,
        help_text="Quantity added in last restock"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'product_variant_stock'
        ordering = ['product', 'color', 'size']
        verbose_name = 'Product Variant Stock'
        verbose_name_plural = 'Product Variant Stocks'
        unique_together = [['product', 'color', 'size']]
        indexes = [
            models.Index(fields=['product', 'stock_quantity']),
            models.Index(fields=['color', 'stock_quantity']),
            models.Index(fields=['size', 'stock_quantity']),
        ]
    
    def __str__(self):
        parts = [self.product.product_name]
        if self.color:
            parts.append(self.color.name)
        if self.size:
            parts.append(self.size.code)
        return f"{' - '.join(parts)} ({self.stock_quantity} in stock)"
    
    def clean(self):
        """Validate that color/size match product configuration"""
        from django.core.exceptions import ValidationError
        
        errors = {}
        
        if self.product:
            # If product has colors, color must be set and in available_colors
            if self.product.has_colors:
                if not self.color:
                    errors['color'] = 'Color is required for this product'
            else:
                if self.color:
                    errors['color'] = 'This product does not have color variants'
            
            # If product has sizes, size must be set and in available_sizes
            if self.product.has_sizes:
                if not self.size:
                    errors['size'] = 'Size is required for this product'
            else:
                if self.size:
                    errors['size'] = 'This product does not have size variants'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        # Auto-generate SKU if not provided
        if not self.sku and self.product:
            sku_parts = [self.product.product_name[:10].upper().replace(' ', '-')]
            if self.color:
                sku_parts.append(self.color.name[:3].upper())
            if self.size:
                sku_parts.append(self.size.code.upper())
            self.sku = '-'.join(sku_parts)
        
        super().save(*args, **kwargs)
        
        # After saving, update product availability
        if self.product:
            self.product.sync_availability_from_stock()
    
    @property
    def available_quantity(self):
        """Get quantity available for purchase (stock minus reserved)"""
        return max(0, self.stock_quantity - self.reserved_quantity)
    
    @property
    def is_in_stock(self):
        """Check if this variant has available stock"""
        return self.available_quantity > 0
    
    @property
    def is_low_stock(self):
        """Check if stock is running low"""
        return 0 < self.available_quantity <= self.low_stock_threshold
    
    def reduce_stock(self, quantity=1, release_reserved=True):
        """
        Reduce stock after successful purchase.
        
        Args:
            quantity: Number of items to reduce
            release_reserved: If True, also reduce reserved_quantity
        
        Returns:
            bool: True if successful, False if insufficient stock
        """
        if self.available_quantity >= quantity:
            self.stock_quantity -= quantity
            if release_reserved and self.reserved_quantity >= quantity:
                self.reserved_quantity -= quantity
            self.save()
            return True
        return False
    
    def reserve_stock(self, quantity=1):
        """
        Reserve stock for cart items.
        
        Args:
            quantity: Number of items to reserve
        
        Returns:
            bool: True if successful, False if insufficient stock
        """
        if self.available_quantity >= quantity:
            self.reserved_quantity += quantity
            self.save()
            return True
        return False
    
    def release_reservation(self, quantity=1):
        """Release reserved stock (e.g., cart abandoned or item removed)"""
        self.reserved_quantity = max(0, self.reserved_quantity - quantity)
        self.save()
    
    def restock(self, quantity, notes=''):
        """
        Add stock to this variant.
        
        Args:
            quantity: Number of items to add
            notes: Optional notes about the restock
        """
        from django.utils import timezone
        
        self.stock_quantity += quantity
        self.last_restocked_at = timezone.now()
        self.restock_quantity = quantity
        self.save()
        
        # Create audit log
        ProductVariantStockAudit.objects.create(
            variant_stock=self,
            action='restock',
            quantity_change=quantity,
            quantity_after=self.stock_quantity,
            notes=notes
        )


class ProductVariantStockAudit(models.Model):
    """
    Audit log for variant stock changes.
    Track all stock movements for inventory management.
    """
    
    ACTION_CHOICES = [
        ('restock', 'Restocked'),
        ('sale', 'Sold'),
        ('reserved', 'Reserved'),
        ('released', 'Released Reservation'),
        ('adjustment', 'Manual Adjustment'),
        ('returned', 'Returned'),
        ('damaged', 'Marked as Damaged'),
        ('initial', 'Initial Stock'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    variant_stock = models.ForeignKey(
        ProductVariantStock,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    quantity_change = models.IntegerField(
        help_text="Positive for additions, negative for reductions"
    )
    quantity_after = models.IntegerField(
        help_text="Stock quantity after this change"
    )
    
    # Related records
    payment = models.ForeignKey(
        'ProductPayment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_audits'
    )
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_audit_actions'
    )
    
    class Meta:
        db_table = 'product_variant_stock_audit'
        ordering = ['-created_at']
        verbose_name = 'Variant Stock Audit'
        verbose_name_plural = 'Variant Stock Audits'
    
    def __str__(self):
        return f"{self.variant_stock} - {self.get_action_display()} ({self.quantity_change:+d})"


class Product(MediaUrlMixin, models.Model):
    
    # Media URL field mappings for auto-population
    MEDIA_URL_FIELDS = {
        'product_image': 'product_image_url',
    }
    
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available for Sale'),
        ('OUT_OF_STOCK', 'Out of Stock'),
        ('COMING_SOON', 'Coming Soon'),
        ('NOT_AVAILABLE', 'Not Available'),
    ]
    
    product_id = models.UUIDField(
        default=uuid4, primary_key=True, unique=True, editable=False
    )
    product_image = models.ImageField(storage=DynamicStorage(), upload_to="ProductImages/", blank=True, null=True)
    product_image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Alternative: Provide product image URL instead of uploading"
    )
    product_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Product description")
    type_of_product = models.CharField(max_length=255, choices=type_of_product)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    
    # Inventory Management
    stock_quantity = models.IntegerField(default=0, help_text="Available quantity in stock")
    low_stock_threshold = models.IntegerField(default=5, help_text="Alert when stock goes below this number")
    
    # Availability Control
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE', help_text="Product availability status")
    is_active = models.BooleanField(default=True, help_text="Show/hide product on website")
    
    # Sales Timing (for event tickets, pre-orders, etc.)
    sales_start_date = models.DateTimeField(null=True, blank=True, help_text="When sales begin (leave empty for immediate availability)")
    sales_end_date = models.DateTimeField(null=True, blank=True, help_text="When sales end (leave empty for no end date)")
    
    # Variant Configuration
    has_colors = models.BooleanField(default=False, help_text="Does this product have color options?")
    has_sizes = models.BooleanField(default=False, help_text="Does this product have size options?")
    available_colors = models.ManyToManyField(
        ProductColor,
        blank=True,
        related_name='products',
        help_text="Available colors for this product"
    )
    available_sizes = models.ManyToManyField(
        ProductSize,
        blank=True,
        related_name='products',
        help_text="Available sizes for this product"
    )
    
    # ===========================================
    # Eligibility/Restriction Configuration
    # ===========================================
    # Target Audience Type
    AUDIENCE_CHOICES = [
        ('ALL', 'Everyone (All Students)'),
        ('STAFF', 'Staff Only'),
        ('EXECUTIVES', 'Executives Only'),
        ('APPOINTEES', 'Appointees Only'),
        ('EXECUTIVES_AND_APPOINTEES', 'Executives and Appointees'),
    ]
    target_audience = models.CharField(
        max_length=30,
        choices=AUDIENCE_CHOICES,
        default='ALL',
        help_text="Who can purchase this product"
    )
    
    # Programme Restrictions
    restrict_by_programme = models.BooleanField(
        default=False,
        help_text="Restrict this product to specific programmes"
    )
    PROGRAMME_CHOICES = [
        ('CS', 'BSc Computer Science'),
        ('IT', 'BSc Information Technology'),
    ]
    allowed_programmes = models.JSONField(
        default=list,
        blank=True,
        help_text="List of allowed programme codes (e.g., ['CS', 'IT']). Only applies if restrict_by_programme is True."
    )
    
    # Year Group Restrictions
    restrict_by_year = models.BooleanField(
        default=False,
        help_text="Restrict this product to specific year groups"
    )
    allowed_years = models.JSONField(
        default=list,
        blank=True,
        help_text="List of allowed year numbers (e.g., [1, 2, 3, 4]). Only applies if restrict_by_year is True."
    )
    
    # Custom eligibility message (optional)
    eligibility_message = models.CharField(
        max_length=255,
        blank=True,
        help_text="Custom message explaining who can purchase (shown when user is not eligible)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return str(self.product_name)
    
    def is_available_for_purchase(self):
        """Check if product can be purchased right now"""
        from django.utils import timezone
        now = timezone.now()
        
        # Check if product is active
        if not self.is_active:
            return False
        
        # Check status
        if self.status != 'AVAILABLE':
            return False
        
        # Check stock
        if self.stock_quantity <= 0:
            return False
        
        # Check sales timing
        if self.sales_start_date and now < self.sales_start_date:
            return False
        
        if self.sales_end_date and now > self.sales_end_date:
            return False
        
        return True
    
    def get_availability_message(self):
        """Get user-friendly availability message"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return "Not available"
        
        if self.status == 'OUT_OF_STOCK' or self.stock_quantity <= 0:
            return "Out of stock"
        
        if self.status == 'COMING_SOON':
            if self.sales_start_date:
                return f"Available from {self.sales_start_date.strftime('%B %d, %Y')}"
            return "Coming soon"
        
        if self.status == 'NOT_AVAILABLE':
            return "Not available"
        
        if self.sales_start_date and now < self.sales_start_date:
            return f"Sales start {self.sales_start_date.strftime('%B %d, %Y at %I:%M %p')}"
        
        if self.sales_end_date and now > self.sales_end_date:
            return "Sales ended"
        
        if self.stock_quantity <= self.low_stock_threshold:
            return f"Only {self.stock_quantity} left!"
        
        return "Available"
    
    def is_low_stock(self):
        """Check if stock is running low"""
        return 0 < self.stock_quantity <= self.low_stock_threshold
    
    def check_user_eligibility(self, user):
        """
        Check if a user is eligible to purchase this product.
        
        Returns:
            tuple: (is_eligible: bool, message: str)
        """
        if user is None:
            # For unauthenticated users, we just show the product but they can't buy
            return False, "Please login to purchase"
        
        # Check target audience
        audience_result = self._check_audience_eligibility(user)
        if not audience_result[0]:
            return audience_result
        
        # Check programme restriction
        programme_result = self._check_programme_eligibility(user)
        if not programme_result[0]:
            return programme_result
        
        # Check year group restriction
        year_result = self._check_year_eligibility(user)
        if not year_result[0]:
            return year_result
        
        return True, ""
    
    def _check_audience_eligibility(self, user):
        """Check if user meets the target audience requirement"""
        from executives.models import Executive, Appointee
        
        # ALL - Everyone can purchase
        if self.target_audience == 'ALL':
            return True, ""
        
        # STAFF - Only Django staff users
        if self.target_audience == 'STAFF':
            if user.is_staff:
                return True, ""
            return False, self.eligibility_message or "This product is for staff members only"
        
        # Check if user is an executive
        is_executive = Executive.objects.filter(user=user, is_active=True).exists()
        
        # Check if user is an appointee
        is_appointee = Appointee.objects.filter(user=user, is_active=True).exists()
        
        # EXECUTIVES - Only executives (not appointees)
        if self.target_audience == 'EXECUTIVES':
            if is_executive:
                return True, ""
            return False, self.eligibility_message or "This product is for executives only"
        
        # APPOINTEES - Only appointees (not executives)
        if self.target_audience == 'APPOINTEES':
            if is_appointee:
                return True, ""
            return False, self.eligibility_message or "This product is for committee appointees only"
        
        # EXECUTIVES_AND_APPOINTEES - Both executives and appointees
        if self.target_audience == 'EXECUTIVES_AND_APPOINTEES':
            if is_executive or is_appointee:
                return True, ""
            return False, self.eligibility_message or "This product is for executives and committee appointees only"
        
        return True, ""
    
    def _check_programme_eligibility(self, user):
        """Check if user's programme is allowed"""
        if not self.restrict_by_programme:
            return True, ""
        
        if not self.allowed_programmes:
            return True, ""
        
        user_programme = getattr(user, 'program', None)
        if not user_programme:
            return False, self.eligibility_message or "Please update your programme in your profile to purchase"
        
        if user_programme in self.allowed_programmes:
            return True, ""
        
        # Build friendly programme names for message
        programme_names = []
        programme_map = {'CS': 'Computer Science', 'IT': 'Information Technology'}
        for code in self.allowed_programmes:
            programme_names.append(programme_map.get(code, code))
        
        return False, self.eligibility_message or f"This product is only for {' and '.join(programme_names)} students"
    
    def _check_year_eligibility(self, user):
        """Check if user's year group is allowed"""
        if not self.restrict_by_year:
            return True, ""
        
        if not self.allowed_years:
            return True, ""
        
        # Get user's current year
        user_year = None
        if hasattr(user, 'get_year'):
            try:
                user_year = user.get_year()
            except:
                pass
        
        if not user_year:
            return False, self.eligibility_message or "Unable to determine your year group. Please update your profile."
        
        if user_year in self.allowed_years:
            return True, ""
        
        # Build friendly year list for message
        year_str = ', '.join([f"Year {y}" for y in sorted(self.allowed_years)])
        return False, self.eligibility_message or f"This product is only for {year_str} students"
    
    def get_eligibility_info(self, user=None):
        """
        Get complete eligibility information for display.
        
        Returns:
            dict: Contains is_eligible, eligibility_message, and restriction_details
        """
        is_eligible, message = self.check_user_eligibility(user) if user else (False, "Please login to purchase")
        
        # Build restriction details for display
        restrictions = []
        
        if self.target_audience != 'ALL':
            audience_labels = {
                'STAFF': 'Staff Only',
                'EXECUTIVES': 'Executives Only',
                'APPOINTEES': 'Appointees Only',
                'EXECUTIVES_AND_APPOINTEES': 'Executives & Appointees',
            }
            restrictions.append(audience_labels.get(self.target_audience, self.target_audience))
        
        if self.restrict_by_programme and self.allowed_programmes:
            programme_map = {'CS': 'CS', 'IT': 'IT'}
            programmes = [programme_map.get(p, p) for p in self.allowed_programmes]
            restrictions.append(f"{' / '.join(programmes)} only")
        
        if self.restrict_by_year and self.allowed_years:
            years = [f"Year {y}" for y in sorted(self.allowed_years)]
            restrictions.append(f"{', '.join(years)} only")
        
        return {
            'is_eligible': is_eligible,
            'eligibility_message': message,
            'has_restrictions': bool(restrictions),
            'restriction_summary': ' • '.join(restrictions) if restrictions else None,
        }

    def reduce_stock(self, quantity=1, color=None, size=None):
        """
        Reduce stock after successful purchase.
        
        For products with variants, reduces variant-level stock and auto-updates availability.
        For simple products, reduces the overall stock_quantity.
        
        Args:
            quantity: Number of items to reduce
            color: ProductColor instance or UUID (required if has_colors)
            size: ProductSize instance or UUID (required if has_sizes)
        
        Returns:
            bool: True if successful, False if insufficient stock
        """
        # For products with variants, use variant stock system
        if self.has_colors or self.has_sizes:
            variant_stock = self.get_variant_stock(color=color, size=size)
            if variant_stock:
                success = variant_stock.reduce_stock(quantity)
                if success:
                    # Sync overall stock and availability
                    self.sync_stock_from_variants()
                return success
            return False
        
        # For simple products without variants
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            if self.stock_quantity == 0:
                self.status = 'OUT_OF_STOCK'
            self.save()
            return True
        return False
    
    def get_variant_stock(self, color=None, size=None):
        """
        Get the ProductVariantStock for a specific color+size combination.
        
        Args:
            color: ProductColor instance, UUID string, or None
            size: ProductSize instance, UUID string, or None
        
        Returns:
            ProductVariantStock or None
        """
        from uuid import UUID
        
        # Convert UUIDs to instances if needed
        if color and not isinstance(color, ProductColor):
            try:
                color = ProductColor.objects.get(id=UUID(str(color)) if not isinstance(color, UUID) else color)
            except ProductColor.DoesNotExist:
                return None
        
        if size and not isinstance(size, ProductSize):
            try:
                size = ProductSize.objects.get(id=UUID(str(size)) if not isinstance(size, UUID) else size)
            except ProductSize.DoesNotExist:
                return None
        
        try:
            return ProductVariantStock.objects.get(
                product=self,
                color=color,
                size=size
            )
        except ProductVariantStock.DoesNotExist:
            return None
    
    def get_or_create_variant_stock(self, color=None, size=None, initial_stock=0):
        """
        Get or create a ProductVariantStock for a specific color+size combination.
        
        Args:
            color: ProductColor instance or UUID
            size: ProductSize instance or UUID
            initial_stock: Initial stock quantity if creating new
        
        Returns:
            tuple: (ProductVariantStock, created: bool)
        """
        from uuid import UUID
        
        # Convert UUIDs to instances if needed
        if color and not isinstance(color, ProductColor):
            color = ProductColor.objects.get(id=UUID(str(color)) if not isinstance(color, UUID) else color)
        
        if size and not isinstance(size, ProductSize):
            size = ProductSize.objects.get(id=UUID(str(size)) if not isinstance(size, UUID) else size)
        
        return ProductVariantStock.objects.get_or_create(
            product=self,
            color=color,
            size=size,
            defaults={'stock_quantity': initial_stock}
        )
    
    def get_available_stock(self, color=None, size=None):
        """
        Get available stock for a specific variant or total stock.
        
        Args:
            color: ProductColor instance, UUID, or None
            size: ProductSize instance, UUID, or None
        
        Returns:
            int: Available quantity
        """
        if not self.has_colors and not self.has_sizes:
            # Simple product without variants
            return self.stock_quantity
        
        if color or size:
            # Specific variant
            variant_stock = self.get_variant_stock(color=color, size=size)
            return variant_stock.available_quantity if variant_stock else 0
        
        # Total across all variants
        return self.variant_stocks.aggregate(
            total=models.Sum('stock_quantity')
        )['total'] or 0
    
    def check_variant_availability(self, color=None, size=None, quantity=1):
        """
        Check if a specific variant is available in the requested quantity.
        
        Args:
            color: ProductColor instance, UUID, or None
            size: ProductSize instance, UUID, or None
            quantity: Quantity needed
        
        Returns:
            tuple: (is_available: bool, available_quantity: int, message: str)
        """
        if not self.has_colors and not self.has_sizes:
            # Simple product
            available = self.stock_quantity
            if available >= quantity:
                return True, available, "In stock"
            elif available > 0:
                return False, available, f"Only {available} available"
            else:
                return False, 0, "Out of stock"
        
        variant_stock = self.get_variant_stock(color=color, size=size)
        
        if not variant_stock:
            return False, 0, "This variant is not available"
        
        available = variant_stock.available_quantity
        
        if available >= quantity:
            return True, available, "In stock"
        elif available > 0:
            return False, available, f"Only {available} available"
        else:
            return False, 0, "Out of stock"
    
    def sync_availability_from_stock(self):
        """
        Synchronize available_colors and available_sizes based on variant stock levels.
        
        This method:
        1. Sets available_colors to only colors that have stock in at least one size
        2. Sets available_sizes to only sizes that have stock in at least one color
        3. Updates overall product status based on total stock
        
        Call this after any stock change to keep availability accurate.
        """
        if not self.has_colors and not self.has_sizes:
            # Simple product - just check stock_quantity
            if self.stock_quantity == 0:
                self.status = 'OUT_OF_STOCK'
                self.save(update_fields=['status'])
            return
        
        # Find colors and sizes that have stock from variant_stocks table
        # This is the SOURCE OF TRUTH - we don't rely on available_colors/available_sizes
        colors_with_stock = set()
        sizes_with_stock = set()
        
        for variant in self.variant_stocks.filter(stock_quantity__gt=0):
            if variant.color_id:
                colors_with_stock.add(variant.color_id)
            if variant.size_id:
                sizes_with_stock.add(variant.size_id)
        
        # Update available_colors to colors that have stock
        if self.has_colors:
            current_available = set(self.available_colors.values_list('id', flat=True))
            
            if colors_with_stock != current_available:
                # Update to only colors with stock
                self.available_colors.set(ProductColor.objects.filter(id__in=colors_with_stock))
        
        # Update available_sizes to sizes that have stock
        if self.has_sizes:
            current_available = set(self.available_sizes.values_list('id', flat=True))
            
            if sizes_with_stock != current_available:
                # Update to only sizes with stock
                self.available_sizes.set(ProductSize.objects.filter(id__in=sizes_with_stock))
        
        # Update overall product status
        total_stock = self.variant_stocks.aggregate(
            total=models.Sum('stock_quantity')
        )['total'] or 0
        
        self.stock_quantity = total_stock
        
        if total_stock == 0:
            self.status = 'OUT_OF_STOCK'
        elif self.status == 'OUT_OF_STOCK':
            self.status = 'AVAILABLE'
        
        self.save(update_fields=['stock_quantity', 'status'])
    
    def sync_stock_from_variants(self):
        """
        Sync the overall stock_quantity from variant stocks.
        Also triggers availability sync.
        """
        total = self.variant_stocks.aggregate(
            total=models.Sum('stock_quantity')
        )['total'] or 0
        
        self.stock_quantity = total
        self.save(update_fields=['stock_quantity'])
        self.sync_availability_from_stock()
    
    def initialize_variant_stocks(self, stock_per_variant=0):
        """
        Initialize ProductVariantStock entries for all color+size combinations.
        
        Call this when setting up a new product with variants, or when adding
        new colors/sizes to an existing product.
        
        Args:
            stock_per_variant: Initial stock for each variant (default 0)
        
        Returns:
            list: Created ProductVariantStock instances
        """
        created_stocks = []
        
        if self.has_colors and self.has_sizes:
            # Create stock entries for each color+size combination
            for color in self.available_colors.all():
                for size in self.available_sizes.all():
                    stock, created = ProductVariantStock.objects.get_or_create(
                        product=self,
                        color=color,
                        size=size,
                        defaults={'stock_quantity': stock_per_variant}
                    )
                    if created:
                        created_stocks.append(stock)
        
        elif self.has_colors:
            # Only colors, no sizes
            for color in self.available_colors.all():
                stock, created = ProductVariantStock.objects.get_or_create(
                    product=self,
                    color=color,
                    size=None,
                    defaults={'stock_quantity': stock_per_variant}
                )
                if created:
                    created_stocks.append(stock)
        
        elif self.has_sizes:
            # Only sizes, no colors
            for size in self.available_sizes.all():
                stock, created = ProductVariantStock.objects.get_or_create(
                    product=self,
                    color=None,
                    size=size,
                    defaults={'stock_quantity': stock_per_variant}
                )
                if created:
                    created_stocks.append(stock)
        
        # Update total stock
        self.sync_stock_from_variants()
        
        return created_stocks
    
    def get_stock_matrix(self):
        """
        Get a matrix view of stock levels for all color+size combinations.
        Useful for admin display and inventory management.
        
        Returns:
            dict: {
                'colors': [{'id': uuid, 'name': str, 'hex_code': str, 'in_stock': bool}],
                'sizes': [{'id': uuid, 'name': str, 'code': str, 'in_stock': bool}],
                'matrix': {
                    color_id: {
                        size_id: {
                            'stock': int,
                            'reserved': int,
                            'available': int,
                            'is_low': bool
                        }
                    }
                },
                'totals': {
                    'by_color': {color_id: total_stock},
                    'by_size': {size_id: total_stock},
                    'overall': int
                }
            }
        """
        result = {
            'colors': [],
            'sizes': [],
            'matrix': {},
            'totals': {
                'by_color': {},
                'by_size': {},
                'overall': 0
            }
        }
        
        if not self.has_colors and not self.has_sizes:
            result['totals']['overall'] = self.stock_quantity
            return result
        
        # Get all colors and sizes for this product
        all_colors = list(self.available_colors.all())
        all_sizes = list(self.available_sizes.all())
        
        # Also include colors/sizes that have stock but might not be in available_ lists
        variant_stocks = list(self.variant_stocks.select_related('color', 'size'))
        
        # Build color list
        color_ids_with_stock = {}
        for color in all_colors:
            color_total = sum(
                v.stock_quantity for v in variant_stocks 
                if v.color_id == color.id
            )
            color_ids_with_stock[color.id] = color_total
            result['colors'].append({
                'id': str(color.id),
                'name': color.name,
                'hex_code': color.hex_code,
                'in_stock': color_total > 0,
                'total_stock': color_total
            })
            result['totals']['by_color'][str(color.id)] = color_total
        
        # Build size list
        for size in all_sizes:
            size_total = sum(
                v.stock_quantity for v in variant_stocks 
                if v.size_id == size.id
            )
            result['sizes'].append({
                'id': str(size.id),
                'name': size.name,
                'code': size.code,
                'in_stock': size_total > 0,
                'total_stock': size_total
            })
            result['totals']['by_size'][str(size.id)] = size_total
        
        # Build stock matrix
        for color in all_colors:
            result['matrix'][str(color.id)] = {}
            for size in all_sizes:
                variant = next(
                    (v for v in variant_stocks if v.color_id == color.id and v.size_id == size.id),
                    None
                )
                if variant:
                    result['matrix'][str(color.id)][str(size.id)] = {
                        'stock': variant.stock_quantity,
                        'reserved': variant.reserved_quantity,
                        'available': variant.available_quantity,
                        'is_low': variant.is_low_stock,
                        'sku': variant.sku
                    }
                else:
                    result['matrix'][str(color.id)][str(size.id)] = {
                        'stock': 0,
                        'reserved': 0,
                        'available': 0,
                        'is_low': False,
                        'sku': None
                    }
        
        result['totals']['overall'] = sum(v.stock_quantity for v in variant_stocks)
        
        return result
    
    def get_available_variants(self):
        """
        Get all available color+size combinations that have stock.
        
        Returns:
            list: [
                {
                    'color': {'id': uuid, 'name': str, 'hex_code': str},
                    'size': {'id': uuid, 'name': str, 'code': str},
                    'stock': int,
                    'available': int
                }
            ]
        """
        variants = []
        
        for stock in self.variant_stocks.filter(stock_quantity__gt=0).select_related('color', 'size'):
            variant = {
                'stock': stock.stock_quantity,
                'available': stock.available_quantity,
                'sku': stock.sku
            }
            
            if stock.color:
                variant['color'] = {
                    'id': str(stock.color.id),
                    'name': stock.color.name,
                    'hex_code': stock.color.hex_code
                }
            else:
                variant['color'] = None
            
            if stock.size:
                variant['size'] = {
                    'id': str(stock.size.id),
                    'name': stock.size.name,
                    'code': stock.size.code
                }
            else:
                variant['size'] = None
            
            variants.append(variant)
        
        return variants
    
    def get_sizes_for_color(self, color):
        """
        Get available sizes for a specific color that have stock.
        
        Args:
            color: ProductColor instance or UUID
        
        Returns:
            QuerySet: ProductSize instances available in this color
        """
        from uuid import UUID
        
        if not isinstance(color, ProductColor):
            try:
                color = ProductColor.objects.get(id=UUID(str(color)) if not isinstance(color, UUID) else color)
            except ProductColor.DoesNotExist:
                return ProductSize.objects.none()
        
        # Get size IDs that have stock for this color
        size_ids = self.variant_stocks.filter(
            color=color,
            stock_quantity__gt=0
        ).values_list('size_id', flat=True)
        
        return ProductSize.objects.filter(id__in=size_ids).order_by('display_order')
    
    def get_colors_for_size(self, size):
        """
        Get available colors for a specific size that have stock.
        
        Args:
            size: ProductSize instance or UUID
        
        Returns:
            QuerySet: ProductColor instances available in this size
        """
        from uuid import UUID
        
        if not isinstance(size, ProductSize):
            try:
                size = ProductSize.objects.get(id=UUID(str(size)) if not isinstance(size, UUID) else size)
            except ProductSize.DoesNotExist:
                return ProductColor.objects.none()
        
        # Get color IDs that have stock for this size
        color_ids = self.variant_stocks.filter(
            size=size,
            stock_quantity__gt=0
        ).values_list('color_id', flat=True)
        
        return ProductColor.objects.filter(id__in=color_ids).order_by('display_order')
    
    def get_successful_purchases(self):
        """Get all successful purchase transactions for this product"""
        from django.contrib.contenttypes.models import ContentType
        from payments.models import Transaction
        
        content_type = ContentType.objects.get_for_model(Product)
        return Transaction.objects.filter(
            content_type=content_type,
            object_id=str(self.product_id),
            transaction_type='payment',
            status='success'
        ).select_related('user', 'currency').order_by('-completed_at')
    
    def get_total_sales(self):
        """Get total sales amount for this product"""
        from decimal import Decimal
        purchases = self.get_successful_purchases()
        return purchases.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
    
    def get_total_quantity_sold(self):
        """Get total quantity sold"""
        purchases = self.get_successful_purchases()
        total = 0
        for purchase in purchases:
            total += purchase.metadata.get('quantity', 1)
        return total
    
    def get_price_for_user(self, user=None):
        """
        Get the effective price for a specific user, considering all applicable discounts.
        
        Returns:
            dict: {
                'original_price': Decimal,
                'final_price': Decimal,
                'discount_applied': bool,
                'discount_amount': Decimal,
                'discount_percentage': Decimal or None,
                'discount_type': str or None,  # 'percentage' or 'fixed_price'
                'discount_name': str or None,
                'discount_reason': str or None,  # Why this discount applies
            }
        """
        from decimal import Decimal
        
        result = {
            'original_price': self.price,
            'final_price': self.price,
            'discount_applied': False,
            'discount_amount': Decimal('0.00'),
            'discount_percentage': None,
            'discount_type': None,
            'discount_name': None,
            'discount_reason': None,
        }
        
        if not user or not user.is_authenticated:
            return result
        
        # Get the best applicable discount for this user
        best_discount = ProductDiscount.get_best_discount_for_user(self, user)
        
        if best_discount:
            final_price, discount_amount = best_discount.calculate_price(self.price)
            result.update({
                'final_price': final_price,
                'discount_applied': True,
                'discount_amount': discount_amount,
                'discount_percentage': best_discount.discount_percentage if best_discount.discount_type == 'PERCENTAGE' else None,
                'discount_type': 'percentage' if best_discount.discount_type == 'PERCENTAGE' else 'fixed_price',
                'discount_name': best_discount.name,
                'discount_reason': best_discount.get_discount_reason(user),
            })
        
        return result


class ProductDiscount(models.Model):
    """
    Model for special pricing/discounts on products for specific user groups or individuals.
    
    Supports two types of discounts:
    1. Percentage discount (e.g., 15% off)
    2. Fixed price (e.g., GHS 60 instead of GHS 70)
    
    Can be targeted at:
    - All users
    - Executives only
    - Appointees only
    - Executives and Appointees
    - Specific individual users
    """
    
    DISCOUNT_TYPE_CHOICES = [
        ('PERCENTAGE', 'Percentage Discount'),
        ('FIXED_PRICE', 'Fixed Price'),
    ]
    
    TARGET_AUDIENCE_CHOICES = [
        ('ALL', 'All Users'),
        ('EXECUTIVES', 'Executives Only'),
        ('APPOINTEES', 'Appointees Only'),
        ('EXECUTIVES_AND_APPOINTEES', 'Executives and Appointees'),
        ('SPECIFIC_USERS', 'Specific Users'),
        ('STAFF', 'Staff Members'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    # Basic info
    name = models.CharField(
        max_length=100,
        help_text="Internal name for this discount (e.g., 'Executive Discount', 'Early Bird')"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description explaining this discount"
    )
    
    # Product association
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='discounts',
        help_text="Product this discount applies to"
    )
    
    # Discount type and value
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default='PERCENTAGE',
        help_text="Type of discount to apply"
    )
    
    # For percentage discount
    discount_percentage = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        null=True,
        blank=True,
        help_text="Percentage discount (e.g., 15 for 15% off). Required if discount_type is PERCENTAGE."
    )
    
    # For fixed price
    fixed_price = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        null=True,
        blank=True,
        help_text="Fixed price for eligible users (e.g., 60.00 instead of 70.00). Required if discount_type is FIXED_PRICE."
    )
    
    # Target audience
    target_audience = models.CharField(
        max_length=30,
        choices=TARGET_AUDIENCE_CHOICES,
        default='EXECUTIVES_AND_APPOINTEES',
        help_text="Who qualifies for this discount"
    )
    
    # For specific users (when target_audience is 'SPECIFIC_USERS')
    specific_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='product_discounts',
        help_text="Specific users who qualify for this discount (only used when target_audience is SPECIFIC_USERS)"
    )
    
    # Validity period
    is_active = models.BooleanField(
        default=True,
        help_text="Is this discount currently active?"
    )
    valid_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this discount becomes valid (leave empty for immediate)"
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this discount expires (leave empty for no expiry)"
    )
    
    # Usage limits
    max_uses = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of times this discount can be used (leave empty for unlimited)"
    )
    times_used = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this discount has been used"
    )
    max_uses_per_user = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum uses per user (leave empty for unlimited)"
    )
    
    # Priority (for when multiple discounts apply)
    priority = models.IntegerField(
        default=0,
        help_text="Higher priority discounts are applied first. If two discounts have same priority, the better one wins."
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_discounts',
        help_text="Admin who created this discount"
    )
    
    class Meta:
        ordering = ['-priority', '-created_at']
        verbose_name = "Product Discount"
        verbose_name_plural = "Product Discounts"
        indexes = [
            models.Index(fields=['product', 'is_active']),
            models.Index(fields=['target_audience', 'is_active']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        discount_str = f"{self.discount_percentage}%" if self.discount_type == 'PERCENTAGE' else f"GHS {self.fixed_price}"
        return f"{self.name} - {discount_str} on {self.product.product_name}"
    
    def clean(self):
        """Validate the discount configuration"""
        from django.core.exceptions import ValidationError
        
        errors = {}
        
        # Validate discount value based on type
        if self.discount_type == 'PERCENTAGE':
            if self.discount_percentage is None:
                errors['discount_percentage'] = 'Percentage is required for percentage discounts'
            elif self.discount_percentage <= 0 or self.discount_percentage > 100:
                errors['discount_percentage'] = 'Percentage must be between 0 and 100'
        
        elif self.discount_type == 'FIXED_PRICE':
            if self.fixed_price is None:
                errors['fixed_price'] = 'Fixed price is required for fixed price discounts'
            elif self.fixed_price < 0:
                errors['fixed_price'] = 'Fixed price cannot be negative'
            elif self.product and self.fixed_price >= self.product.price:
                errors['fixed_price'] = 'Fixed price should be less than the original product price'
        
        # Validate date range
        if self.valid_from and self.valid_until and self.valid_from >= self.valid_until:
            errors['valid_until'] = 'End date must be after start date'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def is_currently_valid(self):
        """Check if the discount is currently valid based on dates and active status"""
        from django.utils import timezone
        
        if not self.is_active:
            return False
        
        now = timezone.now()
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        # Check total usage limit
        if self.max_uses and self.times_used >= self.max_uses:
            return False
        
        return True
    
    def is_applicable_to_user(self, user):
        """Check if this discount applies to a specific user"""
        from executives.models import Executive, Appointee
        
        if not self.is_currently_valid():
            return False
        
        if not user or not user.is_authenticated:
            return False
        
        # Check per-user usage limit
        if self.max_uses_per_user:
            user_usage_count = ProductDiscountUsage.objects.filter(
                discount=self,
                user=user
            ).count()
            if user_usage_count >= self.max_uses_per_user:
                return False
        
        # Check target audience
        if self.target_audience == 'ALL':
            return True
        
        if self.target_audience == 'STAFF':
            return user.is_staff
        
        if self.target_audience == 'SPECIFIC_USERS':
            return self.specific_users.filter(id=user.id).exists()
        
        # Check executive/appointee status
        is_executive = Executive.objects.filter(user=user, is_active=True).exists()
        is_appointee = Appointee.objects.filter(user=user, is_active=True).exists()
        
        if self.target_audience == 'EXECUTIVES':
            return is_executive
        
        if self.target_audience == 'APPOINTEES':
            return is_appointee
        
        if self.target_audience == 'EXECUTIVES_AND_APPOINTEES':
            return is_executive or is_appointee
        
        return False
    
    def calculate_price(self, original_price):
        """
        Calculate the discounted price.
        
        Returns:
            tuple: (final_price, discount_amount)
        """
        from decimal import Decimal, ROUND_HALF_UP
        
        original_price = Decimal(str(original_price))
        
        if self.discount_type == 'PERCENTAGE':
            discount_amount = (original_price * self.discount_percentage / 100).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            final_price = original_price - discount_amount
        else:  # FIXED_PRICE
            final_price = self.fixed_price
            discount_amount = original_price - final_price
        
        return final_price, discount_amount
    
    def get_discount_reason(self, user):
        """Get a human-readable reason why this discount applies to the user"""
        from executives.models import Executive, Appointee
        
        if self.target_audience == 'ALL':
            return f"Special offer: {self.name}"
        
        if self.target_audience == 'STAFF':
            return "Staff discount"
        
        if self.target_audience == 'SPECIFIC_USERS':
            return f"Personal discount: {self.name}"
        
        is_executive = Executive.objects.filter(user=user, is_active=True).exists()
        is_appointee = Appointee.objects.filter(user=user, is_active=True).exists()
        
        if self.target_audience == 'EXECUTIVES' and is_executive:
            return "Executive discount"
        
        if self.target_audience == 'APPOINTEES' and is_appointee:
            return "Appointee discount"
        
        if self.target_audience == 'EXECUTIVES_AND_APPOINTEES':
            if is_executive:
                return "Executive discount"
            if is_appointee:
                return "Appointee discount"
        
        return self.name
    
    def record_usage(self, user, transaction=None):
        """Record that this discount was used"""
        self.times_used += 1
        self.save(update_fields=['times_used'])
        
        # Create usage record
        ProductDiscountUsage.objects.create(
            discount=self,
            user=user,
            transaction=transaction
        )
    
    @classmethod
    def get_best_discount_for_user(cls, product, user):
        """
        Get the best applicable discount for a user on a product.
        
        Returns the discount that provides the lowest final price.
        """
        applicable_discounts = []
        
        for discount in cls.objects.filter(product=product, is_active=True):
            if discount.is_applicable_to_user(user):
                final_price, _ = discount.calculate_price(product.price)
                applicable_discounts.append((discount, final_price))
        
        if not applicable_discounts:
            return None
        
        # Sort by priority (higher first), then by final_price (lower is better)
        applicable_discounts.sort(key=lambda x: (-x[0].priority, x[1]))
        
        return applicable_discounts[0][0]
    
    @classmethod
    def get_all_discounts_for_user(cls, product, user):
        """
        Get all applicable discounts for a user on a product.
        Useful for displaying all available offers.
        """
        applicable_discounts = []
        
        for discount in cls.objects.filter(product=product, is_active=True):
            if discount.is_applicable_to_user(user):
                applicable_discounts.append(discount)
        
        return applicable_discounts


class ProductDiscountUsage(models.Model):
    """
    Track discount usage for per-user limits and analytics
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    discount = models.ForeignKey(
        ProductDiscount,
        on_delete=models.CASCADE,
        related_name='usages'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='discount_usages'
    )
    transaction = models.ForeignKey(
        'payments.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='discount_usages'
    )
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-used_at']
        verbose_name = "Discount Usage"
        verbose_name_plural = "Discount Usages"
        indexes = [
            models.Index(fields=['discount', 'user']),
            models.Index(fields=['used_at']),
        ]
    
    def __str__(self):
        return f"{self.user} used {self.discount.name} on {self.used_at}"


class ProductPayment(models.Model):
    payment_id = models.UUIDField(
        unique=True, primary_key=True, default=uuid4, editable=False
    )
    
    # Link to main Transaction (financial record) - supports cart checkout (multiple ProductPayments per Transaction)
    transaction_record = models.ForeignKey(
        'payments.Transaction',
        on_delete=models.CASCADE,
        related_name='product_payments',
        null=True,
        blank=True,
        help_text="Main transaction record - multiple ProductPayments can link to one Transaction (cart checkout)"
    )
    
    # Legacy fields (for backward compatibility with old payment flow)
    reference = models.CharField(max_length=255, null=True, blank=True, editable=False)
    transaction_validation_code = models.CharField(
        max_length=100, unique=True, editable=False
    )
    transaction = models.CharField(max_length=50, blank=True)  # OLD field - kept for backward compatibility
    
    # ========== User/Buyer Tracking ==========
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_payments_made',
        help_text="The user who actually paid for this product"
    )
    
    phone = PhoneNumberField(null=True)
    
    # ========== Purchase Type Fields ==========
    # Distinguish between gift purchases and purchases on behalf of someone
    is_gift_purchase = models.BooleanField(
        default=False,
        help_text="True if this is a gift (with optional gift message, surprise element)"
    )
    is_purchase_on_behalf = models.BooleanField(
        default=False,
        help_text="True if buying on behalf of someone else (they requested it, more transactional)"
    )
    purchased_for_phone = PhoneNumberField(
        null=True,
        blank=True,
        help_text="Phone number of the person this product was purchased for"
    )
    purchased_for_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_payments_received',
        help_text="The user this product was purchased for (auto-linked when user with phone registers)"
    )
    gift_message = models.TextField(
        blank=True,
        null=True,
        help_text="Optional gift message (only for gift purchases)"
    )
    gift_linked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this purchase was linked to the recipient user account"
    )
    
    customer_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Customer full name"
    )
    customer_email = models.EmailField(
        null=True,
        blank=True,
        help_text="Customer email address"
    )
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(
        decimal_places=2, 
        max_digits=10,
        null=True,
        blank=True,
        help_text="Amount paid for this product purchase"
    )
    price_at_purchase = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        null=True,
        blank=True,
        help_text="Product price at the time of purchase (for price change tracking)"
    )
    
    # Discount Information (if a discount was applied)
    discount_applied = models.BooleanField(
        default=False,
        help_text="Whether a discount was applied to this purchase"
    )
    discount = models.ForeignKey(
        'ProductDiscount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        help_text="The discount that was applied (if any)"
    )
    original_price = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        null=True,
        blank=True,
        help_text="Original price before discount"
    )
    discount_amount = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        null=True,
        blank=True,
        help_text="Amount saved due to discount (per unit)"
    )
    discount_type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Type of discount: 'percentage' or 'fixed_price'"
    )
    discount_percentage = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        null=True,
        blank=True,
        help_text="Discount percentage (if percentage discount)"
    )
    discount_reason = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Reason for discount (e.g., 'Executive discount')"
    )
    
    quantity = models.IntegerField(
        default=1,
        help_text="Number of items purchased"
    )
    payed_at = models.DateTimeField(auto_now_add=True, verbose_name="Date Payed")
    payment_successful = models.BooleanField(default=False)
    
    # Academic Year Tracking
    academic_year = models.CharField(
        max_length=20,
        blank=True,
        editable=False,
        help_text="Academic year of purchase (e.g., '2025/2026'). Auto-calculated based on purchase date."
    )
    
    # Product Variant Selections (colors/sizes)
    variant_selections = models.JSONField(
        default=list,
        blank=True,
        help_text="Customer's color/size preferences. Format: [{'color_id': 'uuid', 'size_id': 'uuid', 'quantity': 1}]"
    )
    
    # Preference Change Tracking
    preference_change_count = models.IntegerField(
        default=0,
        help_text="Number of times customer has changed their variant preferences (max 1 change allowed)"
    )
    preferences_last_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When preferences were last updated"
    )
    preferences_locked = models.BooleanField(
        default=False,
        help_text="If True, preferences cannot be changed anymore (after collection or max changes)"
    )
    
    # Enhanced Collection Tracking (per-variant)
    collection_details = models.JSONField(
        default=list,
        blank=True,
        help_text="""
        Per-variant collection tracking. Format:
        [{
            'variant_index': 0,
            'color_id': 'uuid',
            'size_id': 'uuid',
            'ordered_quantity': 2,
            'collected_quantity': 1,
            'collected_at': '2025-12-19T10:30:00Z',
            'collected_by': 'admin_username',
            'substituted': false,
            'substitution_notes': '',
            'status': 'partial'  # 'pending', 'partial', 'collected', 'unavailable'
        }]
        """
    )
    
    # Legacy Merchandise Collection Tracking (overall status)
    merchandise_taken = models.BooleanField(default=False, help_text="Legacy: All items collected (True if all variants collected)")
    merchandise_taken_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When merchandise was collected (first collection timestamp)"
    )
    taken_by = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Staff who verified collection"
    )
    
    # Notification Tracking
    notification_sent = models.BooleanField(
        default=False,
        editable=False,
        help_text="Whether any notification was sent"
    )
    sms_sent = models.BooleanField(
        default=False,
        editable=False,
        help_text="Whether SMS notification was sent"
    )
    push_sent = models.BooleanField(
        default=False,
        editable=False,
        help_text="Whether push notification was sent"
    )
    sms_campaign_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        editable=False,
        help_text="MNotify SMS campaign ID"
    )
    notification_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
        help_text="When notification was sent"
    )
    notification_error = models.TextField(
        blank=True,
        null=True,
        editable=False,
        help_text="Notification error details if sending failed"
    )

    class Meta:
        verbose_name = "Product Payment"
        verbose_name_plural = "Product Payments"

        db_table = "product_payment"

    def generate_unique_validation_code(self):
        """Generate a unique 6-character transaction validation code."""
        while True:
            code = "".join(
                secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6)
            )
            # Check if the code is unique in the database
            if not ProductPayment.objects.filter(
                transaction_validation_code=code
            ).exists():
                return code
    
    @staticmethod
    def calculate_academic_year(date):
        """
        Calculate academic year based on date.
        
        Academic year runs from September 15 to September 14 of next year.
        
        Logic:
        - Before September 15: Current academic year (e.g., Aug 2025 → 2024/2025)
        - From September 15 onwards: Next academic year (e.g., Sept 15, 2025 → 2025/2026)
        
        Examples:
        - September 14, 2025 → 2024/2025
        - September 15, 2025 → 2025/2026
        - December 13, 2025 → 2025/2026
        - August 30, 2026 → 2025/2026
        - September 15, 2026 → 2026/2027
        
        Args:
            date: datetime object
        
        Returns:
            str: Academic year in format "YYYY/YYYY" (e.g., "2025/2026")
        """
        from datetime import date as date_class
        
        year = date.year
        month = date.month
        day = date.day
        
        # If before September 15, we're in the previous academic year
        # e.g., August 2025 → 2024/2025
        if month < 9 or (month == 9 and day < 15):
            start_year = year - 1
            end_year = year
        else:
            # From September 15 onwards, we're in the next academic year
            # e.g., September 15, 2025 → 2025/2026
            start_year = year
            end_year = year + 1
        
        return f"{start_year}/{end_year}"

    def save(self, *args, **kwargs):
        # Auto-set amount from product if not provided
        if not self.amount and self.product:
            self.amount = self.product.price * self.quantity
        
        # Store price at purchase time for historical tracking
        if not self.price_at_purchase and self.product:
            self.price_at_purchase = self.product.price
        
        # Auto-generate validation code if not already set
        if not self.transaction_validation_code:
            self.transaction_validation_code = self.generate_unique_validation_code()
        
        # Auto-calculate academic year if not already set
        if not self.academic_year and self.payed_at:
            self.academic_year = self.calculate_academic_year(self.payed_at)
        
        return super().save(*args, **kwargs)
    
    def get_total_amount(self):
        """Calculate total amount (price × quantity)"""
        if self.amount:
            return self.amount
        if self.product:
            return self.product.price * self.quantity
        return 0
    
    # ========== Enhanced Collection Tracking Methods ==========
    
    def initialize_collection_details(self):
        """
        Initialize collection_details from variant_selections if not already set.
        Call this after payment completion to set up per-variant tracking.
        """
        if self.collection_details:
            return  # Already initialized
        
        if not self.variant_selections:
            # Single item without variants
            self.collection_details = [{
                'variant_index': 0,
                'color_id': None,
                'size_id': None,
                'ordered_quantity': self.quantity,
                'collected_quantity': 0,
                'collected_at': None,
                'collected_by': None,
                'substituted': False,
                'substitution_notes': '',
                'status': 'pending'
            }]
        else:
            # Multiple variants
            self.collection_details = []
            for idx, selection in enumerate(self.variant_selections):
                self.collection_details.append({
                    'variant_index': idx,
                    'color_id': selection.get('color_id'),
                    'size_id': selection.get('size_id'),
                    'ordered_quantity': selection.get('quantity', 1),
                    'collected_quantity': 0,
                    'collected_at': None,
                    'collected_by': None,
                    'substituted': False,
                    'substitution_notes': '',
                    'status': 'pending'
                })
        self.save(update_fields=['collection_details'])
    
    def get_collection_summary(self):
        """
        Get a summary of collection status across all variants.
        
        Returns:
            dict: {
                'total_ordered': int,
                'total_collected': int,
                'total_pending': int,
                'variants_count': int,
                'variants_collected': int,
                'variants_partial': int,
                'variants_pending': int,
                'overall_status': str  # 'pending', 'partial', 'collected'
            }
        """
        if not self.collection_details:
            self.initialize_collection_details()
        
        total_ordered = 0
        total_collected = 0
        variants_collected = 0
        variants_partial = 0
        variants_pending = 0
        
        for detail in self.collection_details:
            ordered = detail.get('ordered_quantity', 1)
            collected = detail.get('collected_quantity', 0)
            total_ordered += ordered
            total_collected += collected
            
            status = detail.get('status', 'pending')
            if status == 'collected':
                variants_collected += 1
            elif status == 'partial':
                variants_partial += 1
            else:
                variants_pending += 1
        
        # Determine overall status
        if total_collected == 0:
            overall_status = 'pending'
        elif total_collected >= total_ordered:
            overall_status = 'collected'
        else:
            overall_status = 'partial'
        
        return {
            'total_ordered': total_ordered,
            'total_collected': total_collected,
            'total_pending': total_ordered - total_collected,
            'variants_count': len(self.collection_details),
            'variants_collected': variants_collected,
            'variants_partial': variants_partial,
            'variants_pending': variants_pending,
            'overall_status': overall_status
        }
    
    def collect_variant(self, variant_index: int, quantity: int, collected_by: str = None, 
                       substituted: bool = False, substitution_notes: str = ''):
        """
        Mark a specific variant as collected (full or partial).
        
        Args:
            variant_index: Index of the variant in collection_details
            quantity: Number of items collected for this variant
            collected_by: Staff username who verified collection
            substituted: Whether a substitute was given instead
            substitution_notes: Notes about substitution (e.g., "Given red instead of blue")
        
        Returns:
            dict: Updated variant detail
        """
        from django.utils import timezone
        
        if not self.collection_details:
            self.initialize_collection_details()
        
        if variant_index >= len(self.collection_details):
            raise ValueError(f"Invalid variant index: {variant_index}")
        
        detail = self.collection_details[variant_index]
        ordered_qty = detail.get('ordered_quantity', 1)
        already_collected = detail.get('collected_quantity', 0)
        
        # Update collection
        new_collected = min(already_collected + quantity, ordered_qty)
        detail['collected_quantity'] = new_collected
        detail['collected_at'] = timezone.now().isoformat()
        detail['collected_by'] = collected_by
        detail['substituted'] = substituted
        detail['substitution_notes'] = substitution_notes
        
        # Update status
        if new_collected >= ordered_qty:
            detail['status'] = 'collected'
        elif new_collected > 0:
            detail['status'] = 'partial'
        else:
            detail['status'] = 'pending'
        
        self.collection_details[variant_index] = detail
        
        # Update legacy fields for backward compatibility
        summary = self.get_collection_summary()
        if summary['overall_status'] == 'collected':
            self.merchandise_taken = True
        
        if not self.merchandise_taken_at:
            self.merchandise_taken_at = timezone.now()
        
        if not self.taken_by:
            self.taken_by = collected_by
        
        self.save()
        return detail
    
    def mark_variant_unavailable(self, variant_index: int, reason: str = '', marked_by: str = None):
        """
        Mark a variant as unavailable (out of stock, discontinued, etc.)
        
        Args:
            variant_index: Index of the variant
            reason: Reason for unavailability
            marked_by: Staff who marked it
        """
        from django.utils import timezone
        
        if not self.collection_details:
            self.initialize_collection_details()
        
        if variant_index >= len(self.collection_details):
            raise ValueError(f"Invalid variant index: {variant_index}")
        
        detail = self.collection_details[variant_index]
        detail['status'] = 'unavailable'
        detail['collected_at'] = timezone.now().isoformat()
        detail['collected_by'] = marked_by
        detail['substitution_notes'] = f"UNAVAILABLE: {reason}" if reason else "UNAVAILABLE"
        
        self.collection_details[variant_index] = detail
        self.save()
        return detail
    
    def get_formatted_collection_details(self):
        """
        Get collection details with full color/size names for display.
        
        Returns:
            list: Collection details with resolved color/size names
        """
        if not self.collection_details:
            self.initialize_collection_details()
        
        formatted = []
        for detail in self.collection_details:
            item = detail.copy()
            
            # Resolve color name
            color_id = detail.get('color_id')
            if color_id:
                try:
                    color = ProductColor.objects.get(id=color_id)
                    item['color_name'] = color.name
                    item['color_hex'] = color.hex_code
                except ProductColor.DoesNotExist:
                    item['color_name'] = 'Unknown Color'
                    item['color_hex'] = '#888888'
            else:
                item['color_name'] = None
                item['color_hex'] = None
            
            # Resolve size name
            size_id = detail.get('size_id')
            if size_id:
                try:
                    size = ProductSize.objects.get(id=size_id)
                    item['size_name'] = size.name
                    item['size_code'] = size.code
                except ProductSize.DoesNotExist:
                    item['size_name'] = 'Unknown Size'
                    item['size_code'] = '?'
            else:
                item['size_name'] = None
                item['size_code'] = None
            
            formatted.append(item)
        
        return formatted
    
    # ========== Preference Change Tracking Methods ==========
    
    def can_change_preferences(self):
        """
        Check if variant preferences can still be changed.
        
        Rules:
        - Cannot change if merchandise is collected (any variant)
        - Cannot change if preferences are locked
        - Can only change once (preference_change_count < 1)
        
        Returns:
            tuple: (can_change: bool, reason: str)
        """
        # Check if preferences are locked
        if self.preferences_locked:
            return False, "Preferences are locked and cannot be changed"
        
        # Check if merchandise is collected
        if self.merchandise_taken:
            return False, "Cannot change preferences after merchandise is collected"
        
        # Check if collection has started (any variant partially collected)
        if self.collection_details:
            for detail in self.collection_details:
                if detail.get('collected_quantity', 0) > 0:
                    return False, "Cannot change preferences after collection has started"
        
        # Check change count (allow only 1 change)
        if self.preference_change_count >= 1:
            return False, "Preference change limit reached (maximum 1 change allowed)"
        
        return True, ""
    
    def needs_preferences(self):
        """
        Check if this product payment requires variant preferences.
        
        Returns:
            tuple: (needs: bool, missing: list)
        """
        if not self.product:
            return False, []
        
        missing = []
        needs_colors = self.product.has_colors
        needs_sizes = self.product.has_sizes
        
        if not needs_colors and not needs_sizes:
            return False, []
        
        # Check if preferences are empty
        if not self.variant_selections or len(self.variant_selections) == 0:
            if needs_colors:
                missing.append('color')
            if needs_sizes:
                missing.append('size')
            return True, missing
        
        # Check if all selections have required fields
        for idx, selection in enumerate(self.variant_selections):
            if needs_colors and not selection.get('color_id'):
                missing.append(f'color for item {idx + 1}')
            if needs_sizes and not selection.get('size_id'):
                missing.append(f'size for item {idx + 1}')
        
        return len(missing) > 0, missing
    
    def update_preferences(self, new_variant_selections, force=False):
        """
        Update variant preferences with validation and tracking.
        
        Args:
            new_variant_selections: New variant selections to set
            force: If True, bypass change limit (for admin/support)
        
        Returns:
            tuple: (success: bool, message: str)
        
        Raises:
            ValueError: If preferences cannot be changed
        """
        from django.utils import timezone
        
        # Validate if change is allowed
        if not force:
            can_change, reason = self.can_change_preferences()
            if not can_change:
                raise ValueError(reason)
        
        # Store old preferences for audit
        old_preferences = self.variant_selections.copy() if self.variant_selections else []
        
        # Update preferences
        self.variant_selections = new_variant_selections
        self.preference_change_count += 1
        self.preferences_last_updated_at = timezone.now()
        
        # Lock preferences after first change (unless force)
        if not force and self.preference_change_count >= 1:
            self.preferences_locked = True
        
        # Reinitialize collection details with new preferences
        self.collection_details = []
        self.initialize_collection_details()
        
        self.save(update_fields=[
            'variant_selections', 
            'preference_change_count', 
            'preferences_last_updated_at',
            'preferences_locked',
            'collection_details'
        ])
        
        return True, "Preferences updated successfully"
    
    def lock_preferences(self):
        """Lock preferences to prevent further changes."""
        self.preferences_locked = True
        self.save(update_fields=['preferences_locked'])
    
    # ========== "On Behalf Of" / Gift Purchase Methods ==========
    
    def get_recipient_user(self):
        """
        Get the user who should receive this purchase.
        
        For gift purchases: Returns purchased_for_user if linked, otherwise None
        For regular purchases: Returns buyer
        
        Returns:
            CustomUser or None: The recipient user
        """
        if self.is_gift_purchase:
            return self.purchased_for_user
        return self.buyer
    
    def get_owner_user(self):
        """
        Alias for get_recipient_user for clarity.
        Returns the user who "owns" this purchase (who it's for).
        """
        return self.get_recipient_user()
    
    def link_to_recipient(self, user):
        """
        Link this gift or on-behalf purchase to a recipient user account.
        Called when a user with matching phone number is found.
        
        Args:
            user: The user to link this purchase to
        
        Returns:
            bool: True if linked, False if already linked or not a gift/on-behalf purchase
        """
        from django.utils import timezone
        
        # Must be either a gift or on-behalf purchase
        if not self.is_gift_purchase and not self.is_purchase_on_behalf:
            return False
        
        if self.purchased_for_user:
            # Already linked
            return False
        
        # Verify phone matches
        if user.phone and self.purchased_for_phone:
            # Normalize phone numbers for comparison
            user_phone_str = str(user.phone).replace('+', '').replace(' ', '')
            purchase_phone_str = str(self.purchased_for_phone).replace('+', '').replace(' ', '')
            
            if user_phone_str == purchase_phone_str:
                self.purchased_for_user = user
                self.gift_linked_at = timezone.now()
                self.save(update_fields=['purchased_for_user', 'gift_linked_at'])
                return True
        
        return False
    
    @staticmethod
    def link_purchases_for_user(user):
        """
        Find and link all unlinked gift and on-behalf purchases for a user based on their phone number.
        Called when a user registers or updates their phone number.
        
        Args:
            user: The user to link purchases to
        
        Returns:
            int: Number of purchases linked
        """
        if not user.phone:
            return 0
        
        # Find unlinked gift/on-behalf purchases with matching phone
        user_phone_str = str(user.phone).replace('+', '').replace(' ', '')
        
        # Include both gift purchases AND on-behalf purchases
        from django.db.models import Q
        unlinked_purchases = ProductPayment.objects.filter(
            Q(is_gift_purchase=True) | Q(is_purchase_on_behalf=True),
            purchased_for_user__isnull=True,
            purchased_for_phone__isnull=False
        )
        
        linked_count = 0
        for purchase in unlinked_purchases:
            purchase_phone_str = str(purchase.purchased_for_phone).replace('+', '').replace(' ', '')
            if user_phone_str == purchase_phone_str:
                if purchase.link_to_recipient(user):
                    linked_count += 1
        
        return linked_count

    def __str__(self):
        return str(self.transaction_validation_code)


class ProductAudit(models.Model):
    """
    Audit log for tracking all product changes including price changes.
    Enables price-based revenue analytics and change tracking.
    """
    ACTION_CHOICES = [
        ('create', 'Product Created'),
        ('update', 'Product Updated'),
        ('delete', 'Product Deleted'),
        ('price_change', 'Price Changed'),
        ('stock_change', 'Stock Changed'),
        ('status_change', 'Status Changed'),
    ]
    
    audit_id = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='product_changes'
    )
    
    # Change tracking
    old_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="Previous field values before change"
    )
    new_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="New field values after change"
    )
    changed_fields = models.JSONField(
        default=list,
        blank=True,
        help_text="List of fields that were changed"
    )
    
    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Additional notes about the change")
    
    class Meta:
        db_table = 'product_audit'
        ordering = ['-changed_at']
        verbose_name = 'Product Audit Log'
        verbose_name_plural = 'Product Audit Logs'
    
    def __str__(self):
        return f"{self.product.product_name} - {self.get_action_display()} by {self.changed_by} at {self.changed_at}"
    
    def get_price_change_display(self):
        """Display price change in readable format"""
        if self.action == 'price_change' and 'price' in self.old_values and 'price' in self.new_values:
            old_price = self.old_values['price']
            new_price = self.new_values['price']
            diff = float(new_price) - float(old_price)
            percentage = (diff / float(old_price)) * 100 if float(old_price) > 0 else 0
            
            if diff > 0:
                return f"GH₵ {old_price} → GH₵ {new_price} (+{diff:.2f}, +{percentage:.1f}%)"
            else:
                return f"GH₵ {old_price} → GH₵ {new_price} ({diff:.2f}, {percentage:.1f}%)"
        return "N/A"
