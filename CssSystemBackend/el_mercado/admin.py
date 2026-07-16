from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import (
    SellerApplication, Seller, SellerWallet, WalletTransaction,
    PayoutRequest, SellerPayoutAccount, Category, Listing, ListingImage,
    ListingVariant, MarketplaceOrder, OrderItem, Review, Conversation,
    Message, Favorite, FollowedSeller, Dispute, MarketplaceSettings,
    CommissionRate
)


# =============================================================================
# INLINE ADMINS
# =============================================================================

class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1
    fields = ['image', 'alt_text', 'display_order']


class ListingVariantInline(admin.TabularInline):
    model = ListingVariant
    extra = 0
    fields = ['name', 'sku', 'attributes', 'price', 'stock_quantity', 'is_active']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['listing_title', 'variant_name', 'unit_price', 'quantity', 'total_price']
    can_delete = False


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['sender_type', 'content', 'created_at', 'is_read']
    can_delete = False


class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = ['transaction_type', 'amount', 'description', 'balance_after', 'created_at']
    can_delete = False
    max_num = 20
    ordering = ['-created_at']


# =============================================================================
# SELLER ADMINS
# =============================================================================

@admin.register(SellerApplication)
class SellerApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'tracking_code', 'applicant_name', 'seller_type', 'business_name', 
        'status_badge', 'created_at', 'reviewed_by'
    ]
    list_filter = ['status', 'seller_type', 'created_at']
    search_fields = ['applicant_name', 'applicant_email', 'business_name', 'tracking_code']
    readonly_fields = ['id', 'tracking_code', 'created_at', 'updated_at', 'reviewed_at']
    
    fieldsets = (
        ('Application Info', {
            'fields': ('id', 'tracking_code', 'user', 'seller_type', 'status', 'status_reason')
        }),
        ('Contact Information', {
            'fields': ('applicant_name', 'applicant_email', 'applicant_phone')
        }),
        ('Business Information', {
            'fields': ('business_name', 'business_registration_number', 'business_type'),
            'classes': ('collapse',)
        }),
        ('Address', {
            'fields': ('address_line_1', 'address_line_2', 'city', 'region', 'country')
        }),
        ('Verification Documents', {
            'fields': (
                'id_document', 'id_document_type',
                'business_document', 'proof_of_address'
            )
        }),
        ('Application Details', {
            'fields': ('description', 'categories_of_interest')
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_applications', 'reject_applications']
    
    def status_badge(self, obj):
        colors = {
            'PENDING': '#FFA500',
            'UNDER_REVIEW': '#3498db',
            'APPROVED': '#27ae60',
            'REJECTED': '#e74c3c',
            'REVISION_REQUESTED': '#9b59b6',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def approve_applications(self, request, queryset):
        approved_count = 0
        for app in queryset.filter(status__in=['PENDING', 'UNDER_REVIEW']):
            app.approve(request.user)
            approved_count += 1
        self.message_user(request, f"Approved {approved_count} application(s)")
    approve_applications.short_description = "Approve selected applications"
    
    def reject_applications(self, request, queryset):
        rejected_count = queryset.filter(status__in=['PENDING', 'UNDER_REVIEW']).update(
            status='REJECTED',
            status_reason='Rejected via bulk action',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"Rejected {rejected_count} application(s)")
    reject_applications.short_description = "Reject selected applications"
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to handle status changes properly.
        When status is changed to APPROVED, automatically create the Seller profile.
        """
        if change:  # Only on update, not create
            # Get the original object from database
            original = SellerApplication.objects.get(pk=obj.pk)
            
            # Check if status was changed TO 'APPROVED' from a non-approved status
            if obj.status == 'APPROVED' and original.status != 'APPROVED':
                # Check if seller profile already exists
                if not Seller.objects.filter(application=obj).exists():
                    # Use the approve method to create seller profile
                    obj.status = original.status  # Reset to original status first
                    super().save_model(request, obj, form, change)  # Save other changes
                    
                    # Approve and get email status
                    result = obj.approve(request.user)
                    if isinstance(result, tuple) and len(result) == 3:
                        seller, temp_password, email_sent = result
                        if email_sent:
                            self.message_user(
                                request, 
                                f"✅ Application approved and credentials sent to {seller.email}",
                                level='success'
                            )
                        else:
                            self.message_user(
                                request,
                                f"⚠️ Application approved but email failed. Password: {temp_password}",
                                level='warning'
                            )
                    else:
                        self.message_user(
                            request,
                            "✅ Application approved",
                            level='success'
                        )
                    return
            
            # Check if status was changed TO 'REJECTED' from a non-rejected status  
            elif obj.status == 'REJECTED' and original.status != 'REJECTED':
                obj.reviewed_by = request.user
                obj.reviewed_at = timezone.now()
        
        super().save_model(request, obj, form, change)


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'seller_type', 'status_badge', 'is_verified',
        'has_credentials', 'average_rating', 'total_sales', 'commission_rate', 'created_at'
    ]
    list_filter = ['status', 'seller_type', 'is_verified', 'vacation_mode', 'is_credentials_set']
    search_fields = ['display_name', 'email', 'slug']
    readonly_fields = [
        'id', 'slug', 'average_rating', 'total_reviews', 'total_sales', 
        'created_at', 'updated_at', 'last_login', 'failed_login_attempts', 'locked_until'
    ]
    actions = ['generate_credentials', 'reset_login_attempts']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'application', 'user', 'seller_type', 'display_name', 'slug')
        }),
        ('Contact', {
            'fields': ('email', 'phone')
        }),
        ('Authentication', {
            'fields': ('is_credentials_set', 'last_login', 'failed_login_attempts', 'locked_until'),
            'description': 'Seller portal login credentials (separate from user accounts)'
        }),
        ('Branding', {
            'fields': ('logo', 'banner', 'description')
        }),
        ('Status', {
            'fields': ('status', 'status_reason', 'is_verified', 'verification_level')
        }),
        ('Statistics', {
            'fields': ('average_rating', 'total_reviews', 'total_sales')
        }),
        ('Settings', {
            'fields': ('commission_rate', 'auto_accept_orders', 'vacation_mode', 'vacation_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'ACTIVE': '#27ae60',
            'INACTIVE': '#95a5a6',
            'SUSPENDED': '#e67e22',
            'BANNED': '#e74c3c',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def has_credentials(self, obj):
        """Show if seller has login credentials set up"""
        if obj.password:
            if obj.is_credentials_set:
                return format_html(
                    '<span style="color: #27ae60;">✓ Set</span>'
                )
            else:
                return format_html(
                    '<span style="color: #e67e22;">⏳ Temp</span>'
                )
        return format_html(
            '<span style="color: #e74c3c;">✗ None</span>'
        )
    has_credentials.short_description = 'Credentials'
    
    @admin.action(description='Generate/Send login credentials to selected sellers')
    def generate_credentials(self, request, queryset):
        """Generate new credentials for selected sellers and email them"""
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from django.conf import settings as django_settings
        from datetime import datetime
        
        success_count = 0
        email_count = 0
        
        for seller in queryset:
            # Generate temporary password
            temp_password = seller.generate_temporary_password()
            seller.save()
            success_count += 1
            
            # Try to send email
            if seller.email:
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
                    html_content = render_to_string('el_mercado/emails/seller_credentials.html', context)
                    text_content = strip_tags(html_content)
                    
                    email = EmailMultiAlternatives(
                        subject='🛍️ El Mercado - Your Seller Dashboard is Ready!',
                        body=text_content,
                        from_email=django_settings.DEFAULT_FROM_EMAIL,
                        to=[seller.email],
                    )
                    email.attach_alternative(html_content, "text/html")
                    email.send(fail_silently=False)
                    email_count += 1
                except Exception as e:
                    self.message_user(
                        request, 
                        f"Generated credentials for {seller.display_name} but email failed: {e}",
                        level='warning'
                    )
        
        self.message_user(
            request,
            f"Generated credentials for {success_count} seller(s). "
            f"Sent {email_count} email notification(s)."
        )
    
    @admin.action(description='Reset failed login attempts (unlock accounts)')
    def reset_login_attempts(self, request, queryset):
        """Reset failed login attempts for selected sellers"""
        count = queryset.update(failed_login_attempts=0, locked_until=None)
        self.message_user(
            request,
            f"Reset login attempts for {count} seller(s). Accounts are now unlocked."
        )


# =============================================================================
# WALLET & PAYOUT ADMINS
# =============================================================================

@admin.register(SellerWallet)
class SellerWalletAdmin(admin.ModelAdmin):
    list_display = [
        'seller', 'available_balance', 'pending_balance',
        'total_earned', 'total_withdrawn', 'currency'
    ]
    search_fields = ['seller__display_name']
    readonly_fields = [
        'id', 'available_balance', 'pending_balance', 'total_earned',
        'total_withdrawn', 'total_fees_paid', 'created_at', 'updated_at'
    ]
    inlines = [WalletTransactionInline]
    
    fieldsets = (
        ('Seller', {
            'fields': ('id', 'seller', 'currency')
        }),
        ('Balances', {
            'fields': ('available_balance', 'pending_balance', 'total_earned', 'total_withdrawn', 'total_fees_paid')
        }),
        ('Payout Settings', {
            'fields': ('minimum_payout_amount', 'auto_payout_enabled', 'auto_payout_threshold')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'transaction_type', 'amount', 'balance_after', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['wallet__seller__display_name', 'description']
    readonly_fields = ['id', 'created_at']


@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'wallet', 'amount_display', 'payout_amount_display', 'currency',
        'payout_method', 'status_badge', 'created_at'
    ]
    list_filter = ['status', 'payout_method', 'created_at']
    search_fields = ['reference', 'wallet__seller__display_name']
    readonly_fields = ['id', 'reference', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Request Info', {
            'fields': ('id', 'reference', 'wallet', 'amount', 'processing_fee', 'net_amount', 'currency', 'status', 'status_message'),
            'description': '<strong style="color: #27ae60; font-size: 14px;">💰 NET AMOUNT is what will be sent to the seller\'s account</strong>'
        }),
        ('Payout Method', {
            'fields': ('payout_method',)
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'bank_code', 'account_number', 'account_name'),
            'classes': ('collapse',)
        }),
        ('Mobile Money', {
            'fields': ('mobile_money_provider', 'mobile_money_number'),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': ('gateway_reference', 'processed_by', 'processed_at', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_processing', 'mark_completed']
    
    def amount_display(self, obj):
        """Show requested amount with fee breakdown"""
        return format_html(
            '<div style="line-height: 1.6;">'
            '<strong style="font-size: 13px;">{} {}</strong><br>'
            '<small style="color: #e74c3c;">- {} {} fee</small>'
            '</div>',
            obj.currency, obj.amount,
            obj.currency, obj.processing_fee
        )
    amount_display.short_description = 'Requested'
    
    def payout_amount_display(self, obj):
        """Highlight the actual amount to be sent"""
        return format_html(
            '<div style="background: linear-gradient(135deg, #27ae60, #229954); '
            'color: white; padding: 8px 12px; border-radius: 6px; text-align: center; '
            'font-weight: bold; font-size: 14px;">'
            '💸 {} {}<br>'
            '<small style="opacity: 0.9; font-size: 11px;">AMOUNT TO SEND</small>'
            '</div>',
            obj.currency, obj.net_amount
        )
    payout_amount_display.short_description = '💰 Payout Amount'
    
    def status_badge(self, obj):
        colors = {
            'PENDING': '#FFA500',
            'PROCESSING': '#3498db',
            'COMPLETED': '#27ae60',
            'FAILED': '#e74c3c',
            'CANCELLED': '#95a5a6',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def mark_processing(self, request, queryset):
        queryset.filter(status='PENDING').update(
            status='PROCESSING',
            processed_by=request.user,
            processed_at=timezone.now()
        )
    mark_processing.short_description = "Mark as Processing"
    
    def mark_completed(self, request, queryset):
        for payout in queryset.filter(status='PROCESSING'):
            payout.wallet.withdraw(payout.amount, f"Payout {payout.reference}")
            payout.status = 'COMPLETED'
            payout.completed_at = timezone.now()
            payout.save()
    mark_completed.short_description = "Mark as Completed"


@admin.register(SellerPayoutAccount)
class SellerPayoutAccountAdmin(admin.ModelAdmin):
    list_display = ['seller', 'account_type', 'is_default', 'is_verified', 'created_at']
    list_filter = ['account_type', 'is_default', 'is_verified']
    search_fields = ['seller__display_name']


# =============================================================================
# CATEGORY & LISTING ADMINS
# =============================================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'display_order', 'commission_rate']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'name']


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'seller', 'category', 'price', 'stock_quantity',
        'status_badge', 'average_rating', 'order_count', 'created_at'
    ]
    list_filter = ['status', 'listing_type', 'category', 'condition', 'created_at']
    search_fields = ['title', 'description', 'seller__display_name']
    readonly_fields = [
        'id', 'slug', 'view_count', 'favorite_count', 'order_count',
        'average_rating', 'review_count', 'created_at', 'updated_at', 'published_at'
    ]
    inlines = [ListingImageInline, ListingVariantInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'seller', 'title', 'slug', 'description', 'listing_type')
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_at_price', 'currency')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'track_inventory', 'allow_backorder', 'low_stock_threshold')
        }),
        ('Condition & Shipping', {
            'fields': ('condition', 'requires_shipping', 'weight', 'shipping_info')
        }),
        ('Images', {
            'fields': ('main_image',)
        }),
        ('Status', {
            'fields': ('status', 'rejection_reason', 'published_at')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('view_count', 'favorite_count', 'order_count', 'average_rating', 'review_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['publish_listings', 'archive_listings']
    
    def status_badge(self, obj):
        colors = {
            'DRAFT': '#95a5a6',
            'PENDING_REVIEW': '#FFA500',
            'ACTIVE': '#27ae60',
            'INACTIVE': '#7f8c8d',
            'SOLD_OUT': '#e74c3c',
            'ARCHIVED': '#34495e',
            'REJECTED': '#c0392b',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def publish_listings(self, request, queryset):
        for listing in queryset.filter(status__in=['DRAFT', 'INACTIVE']):
            listing.publish()
        self.message_user(request, f"Published {queryset.count()} listing(s)")
    publish_listings.short_description = "Publish selected listings"
    
    def archive_listings(self, request, queryset):
        queryset.update(status='ARCHIVED')
        self.message_user(request, f"Archived {queryset.count()} listing(s)")
    archive_listings.short_description = "Archive selected listings"


# =============================================================================
# ORDER ADMINS
# =============================================================================

@admin.register(MarketplaceOrder)
class MarketplaceOrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'buyer', 'seller', 'total_amount',
        'status_badge', 'payment_status', 'funds_released', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'funds_released', 'created_at']
    search_fields = ['order_number', 'buyer__email', 'seller__display_name']
    readonly_fields = [
        'id', 'order_number', 'platform_commission', 'seller_earnings',
        'status_history', 'created_at', 'updated_at'
    ]
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('id', 'order_number', 'buyer', 'seller', 'status', 'status_history')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'shipping_cost', 'discount_amount', 'total_amount', 'currency')
        }),
        ('Commission', {
            'fields': ('commission_rate', 'platform_commission', 'seller_earnings')
        }),
        ('Payment', {
            'fields': ('payment_status', 'payment_reference', 'paid_at')
        }),
        ('Shipping Address', {
            'fields': (
                'shipping_name', 'shipping_phone', 'shipping_email',
                'shipping_address_line_1', 'shipping_address_line_2',
                'shipping_city', 'shipping_region', 'shipping_country'
            )
        }),
        ('Tracking', {
            'fields': ('tracking_number', 'tracking_url', 'shipped_at', 'delivered_at')
        }),
        ('Notes', {
            'fields': ('buyer_notes', 'seller_notes', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('Escrow', {
            'fields': ('funds_released', 'funds_released_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_shipped', 'mark_delivered', 'mark_completed', 'release_funds']
    
    def status_badge(self, obj):
        colors = {
            'PENDING': '#FFA500',
            'AWAITING_PAYMENT': '#9b59b6',
            'PAID': '#3498db',
            'PROCESSING': '#1abc9c',
            'SHIPPED': '#2980b9',
            'DELIVERED': '#27ae60',
            'COMPLETED': '#2ecc71',
            'CANCELLED': '#95a5a6',
            'REFUNDED': '#e74c3c',
            'DISPUTED': '#c0392b',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def mark_shipped(self, request, queryset):
        for order in queryset.filter(status__in=['PAID', 'PROCESSING']):
            order.update_status('SHIPPED', 'Marked shipped by admin')
            order.shipped_at = timezone.now()
            order.save(update_fields=['shipped_at'])
    mark_shipped.short_description = "Mark as Shipped"
    
    def mark_delivered(self, request, queryset):
        for order in queryset.filter(status='SHIPPED'):
            order.update_status('DELIVERED', 'Marked delivered by admin')
            order.delivered_at = timezone.now()
            order.save(update_fields=['delivered_at'])
    mark_delivered.short_description = "Mark as Delivered"
    
    def mark_completed(self, request, queryset):
        """Mark orders as completed and release funds"""
        from django.utils import timezone
        count = 0
        for order in queryset.filter(status='DELIVERED', funds_released=False):
            if order.release_funds():
                order.completed_at = timezone.now()
                order.save(update_fields=['completed_at'])
                order.update_status('COMPLETED', 'Order completed and funds released by admin')
                count += 1
        self.message_user(request, f"{count} order(s) marked as completed and funds released")
    mark_completed.short_description = "Mark as Completed (Release Funds)"
    
    def release_funds(self, request, queryset):
        for order in queryset.filter(funds_released=False, status__in=['DELIVERED', 'COMPLETED']):
            order.release_funds()
        self.message_user(request, "Funds released successfully")
    release_funds.short_description = "Release funds to sellers"


# =============================================================================
# REVIEW & COMMUNICATION ADMINS
# =============================================================================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'reviewer', 'review_type', 'rating_stars', 'listing', 'seller',
        'is_approved', 'is_verified_purchase', 'created_at'
    ]
    list_filter = ['review_type', 'rating', 'is_approved', 'is_verified_purchase', 'created_at']
    search_fields = ['reviewer__email', 'listing__title', 'seller__display_name', 'content']
    readonly_fields = ['id', 'helpful_count', 'unhelpful_count', 'created_at', 'updated_at']
    
    def rating_stars(self, obj):
        return '★' * obj.rating + '☆' * (5 - obj.rating)
    rating_stars.short_description = 'Rating'


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = [
        'buyer', 'seller', 'listing', 'order',
        'buyer_unread_count', 'seller_unread_count', 'last_message_at'
    ]
    list_filter = ['created_at']
    search_fields = ['buyer__email', 'seller__display_name']
    inlines = [MessageInline]


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'order', 'reason', 'status_badge',
        'refund_amount', 'created_at'
    ]
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['reference', 'order__order_number']
    readonly_fields = ['id', 'reference', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Dispute Info', {
            'fields': ('id', 'reference', 'order', 'initiated_by', 'reason', 'description')
        }),
        ('Evidence', {
            'fields': ('evidence',)
        }),
        ('Status', {
            'fields': ('status', 'resolution_notes', 'resolved_by', 'resolved_at')
        }),
        ('Refund', {
            'fields': ('refund_amount',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'OPEN': '#e74c3c',
            'UNDER_REVIEW': '#FFA500',
            'AWAITING_SELLER': '#9b59b6',
            'AWAITING_BUYER': '#3498db',
            'RESOLVED_BUYER_FAVOR': '#27ae60',
            'RESOLVED_SELLER_FAVOR': '#2980b9',
            'RESOLVED_COMPROMISE': '#1abc9c',
            'CLOSED': '#95a5a6',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# =============================================================================
# FAVORITES & FOLLOWS
# =============================================================================

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'listing', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__personal_email', 'user__student_email', 'listing__title']


@admin.register(FollowedSeller)
class FollowedSellerAdmin(admin.ModelAdmin):
    list_display = ['user', 'seller', 'notify_new_listings', 'notify_sales', 'created_at']
    list_filter = ['notify_new_listings', 'notify_sales', 'created_at']
    search_fields = ['user__personal_email', 'user__student_email', 'seller__display_name']


# =============================================================================
# SETTINGS
# =============================================================================

@admin.register(CommissionRate)
class CommissionRateAdmin(admin.ModelAdmin):
    list_display = [
        'category_type', 'get_category_name', 'rate', 'is_active', 'created_at', 'updated_at'
    ]
    list_filter = ['is_active', 'category_type']
    search_fields = ['description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Category Information', {
            'fields': ('category_type', 'description')
        }),
        ('Rate Settings', {
            'fields': ('rate', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_category_name(self, obj):
        """Display friendly category name"""
        return obj.get_category_type_display()
    get_category_name.short_description = 'Category Name'


@admin.register(MarketplaceSettings)
class MarketplaceSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'default_commission_rate', 'minimum_payout_amount',
        'payout_processing_days', 'auto_complete_days', 'updated_at'
    ]
    
    fieldsets = (
        ('Commission Settings', {
            'fields': ('default_commission_rate',)
        }),
        ('Payment Processing Fees', {
            'fields': (
                'payment_processing_fee_percentage',
                'payment_processing_fee_fixed'
            )
        }),
        ('Payout Fees', {
            'fields': (
                'payout_transaction_fee',
                'payout_processing_fee_percentage'
            )
        }),
        ('Payout Settings', {
            'fields': (
                'minimum_payout_amount',
                'payout_processing_days'
            )
        }),
        ('Order Settings', {
            'fields': ('auto_complete_days',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not MarketplaceSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
