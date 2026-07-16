"""
Payment System Admin Interface
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count
from .models import (
    PaymentGateway,
    Currency,
    Transaction,
    PaymentSession,
    Refund,
    Wallet,
    WalletTransaction,
    PaymentWebhook,
)


@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    """
    Admin interface for Payment Gateways
    
    Security Notes:
    - Gateway credentials (API keys) should NOT be stored in config field
    - Use environment variables for sensitive data
    - Config field is for non-sensitive settings only
    """
    
    list_display = [
        'display_name', 'name', 'status_badge', 'supports_refunds',
        'priority', 'created_at'
    ]
    list_filter = ['is_active', 'status', 'supports_refunds', 'supports_recurring']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'display_name', 'description')
        }),
        ('Status', {
            'fields': ('is_active', 'status', 'priority')
        }),
        ('Features', {
            'fields': (
                'supports_refunds', 'supports_recurring', 'supports_webhooks',
                'supported_currencies', 'supported_methods'
            )
        }),
        ('Fees', {
            'fields': ('fixed_fee', 'percentage_fee')
        }),
        ('Configuration', {
            'fields': ('config',),
            'classes': ('collapse',),
            'description': '⚠️ DO NOT store API keys here! Use environment variables.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'active': 'green',
            'inactive': 'red',
            'maintenance': 'orange',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    """Admin interface for Currencies"""
    
    list_display = ['code', 'name', 'symbol', 'exchange_rate', 'is_active', 'is_base_currency']
    list_filter = ['is_active', 'is_base_currency']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Admin interface for Transactions (READ-ONLY for security)
    
    Security Notes:
    - Transactions cannot be created/edited/deleted manually
    - All transactions must go through payment gateway APIs
    - Only viewing and marking for review is allowed
    - This prevents fraud and maintains audit trail integrity
    """
    
    list_display = [
        'reference', 'user_link', 'transaction_type', 'amount_display',
        'status_badge', 'gateway', 'initiated_at'
    ]
    list_filter = [
        'transaction_type', 'status', 'gateway', 'currency',
        'is_test', 'requires_manual_review', 'initiated_at'
    ]
    search_fields = [
        'reference', 'gateway_reference', 'user__personal_email', 'user__student_email',
        'user__first_name', 'user__last_name', 'description'
    ]
    readonly_fields = [
        'id', 'reference', 'user', 'transaction_type', 'status', 'status_message',
        'description', 'amount', 'currency', 'gateway_fee', 'platform_fee', 
        'net_amount', 'gateway', 'gateway_reference', 'payment_method', 
        'payment_channel', 'customer_email', 'customer_phone', 'customer_name',
        'content_type', 'object_id', 'ip_address', 'user_agent', 'location',
        'initiated_at', 'completed_at', 'expires_at', 'updated_at',
        'metadata', 'gateway_metadata', 'gateway_response', 'is_test',
        'can_be_refunded'
        # NOTE: Merchandise tracking moved to ProductPayment model in products app
    ]
    date_hierarchy = 'initiated_at'
    
    # Prevent any modifications to transactions
    def has_add_permission(self, request):
        """Prevent manual transaction creation"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent transaction deletion (audit trail)"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent transaction modification (except marking for review)"""
        # Only allow viewing, not editing
        if obj is not None:
            return False
        return True
    
    fieldsets = (
        ('Transaction Details', {
            'fields': (
                'id', 'reference', 'user', 'transaction_type', 'status',
                'status_message', 'description'
            )
        }),
        ('Amount', {
            'fields': (
                'amount', 'currency', 'gateway_fee', 'platform_fee', 'net_amount'
            )
        }),
        ('Payment Gateway', {
            'fields': ('gateway', 'gateway_reference', 'payment_method', 'payment_channel')
        }),
        ('Customer Info', {
            'fields': ('customer_email', 'customer_phone', 'customer_name')
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('ip_address', 'user_agent', 'location'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('initiated_at', 'completed_at', 'expires_at', 'updated_at')
        }),
        ('Metadata', {
            'fields': ('metadata', 'gateway_metadata', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Flags', {
            'fields': ('is_test', 'requires_manual_review', 'can_be_refunded')
        }),
    )
    
    # Only allow marking for review, no other modifications
    actions = ['mark_for_review', 'export_transactions']
    
    def user_link(self, obj):
        """Display user as clickable link (handles guest/anonymous transactions)"""
        if obj.user:
            url = reverse('admin:accounts_customuser_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())
        # For guest transactions (e.g., anonymous donations)
        return format_html('<span style="color: gray;"><i>Guest</i></span>')
    user_link.short_description = 'User'
    
    def amount_display(self, obj):
        """Display amount with currency"""
        return f"{obj.currency.symbol}{obj.amount}"
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'success': 'green',
            'failed': 'red',
            'pending': 'orange',
            'processing': 'blue',
            'cancelled': 'gray',
            'refunded': 'purple',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def mark_for_review(self, request, queryset):
        """Mark selected transactions for manual review"""
        count = queryset.update(requires_manual_review=True)
        self.message_user(request, f'{count} transactions marked for review')
    mark_for_review.short_description = 'Mark for manual review'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'currency', 'gateway')


@admin.register(PaymentSession)
class PaymentSessionAdmin(admin.ModelAdmin):
    """Admin interface for Payment Sessions"""
    
    list_display = [
        'session_key', 'user', 'amount', 'gateway', 'status',
        'created_at', 'expires_at'
    ]
    list_filter = ['status', 'gateway', 'created_at']
    search_fields = ['session_key', 'user__personal_email', 'user__student_email', 'gateway_session_id']
    readonly_fields = ['id', 'session_key', 'created_at', 'expires_at', 'completed_at']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    """
    Admin interface for Refunds
    
    Security Notes:
    - Refunds can only be approved, not created manually
    - Refund amount and transaction cannot be edited
    - Only status and approval fields are editable
    - This prevents unauthorized refund creation
    """
    
    list_display = [
        'reference', 'original_transaction_link', 'amount', 'reason',
        'status_badge', 'requires_approval', 'created_at'
    ]
    list_filter = [
        'status', 'reason', 'requires_approval', 'created_at'
    ]
    search_fields = [
        'reference', 'gateway_reference',
        'original_transaction__reference'
    ]
    readonly_fields = [
        'id', 'reference', 'original_transaction', 'refund_transaction',
        'amount', 'reason', 'reason_details', 'gateway_reference',
        'gateway_response', 'initiated_by', 'created_at', 'processed_at',
        'completed_at', 'is_successful', 'is_partial'
    ]
    
    # Prevent manual refund creation
    def has_add_permission(self, request):
        """Prevent manual refund creation (must use RefundService)"""
        return False
    
    # Prevent refund deletion
    def has_delete_permission(self, request, obj=None):
        """Prevent refund deletion (audit trail)"""
        return False
    
    fieldsets = (
        ('Refund Details', {
            'fields': (
                'id', 'reference', 'original_transaction', 'refund_transaction',
                'amount', 'reason', 'reason_details', 'status', 'status_message'
            )
        }),
        ('Gateway', {
            'fields': ('gateway_reference', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Approval', {
            'fields': (
                'requires_approval', 'initiated_by', 'approved_by', 'approved_at'
            ),
            'description': 'Admins can approve refunds that require approval'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at', 'completed_at')
        }),
        ('Properties', {
            'fields': ('is_successful', 'is_partial')
        }),
    )
    
    # Only allow approval action
    actions = ['approve_refunds']
    
    def original_transaction_link(self, obj):
        """Display original transaction as clickable link"""
        url = reverse('admin:payments_transaction_change', args=[obj.original_transaction.id])
        return format_html('<a href="{}">{}</a>', url, obj.original_transaction.reference)
    original_transaction_link.short_description = 'Original Transaction'
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'success': 'green',
            'failed': 'red',
            'pending': 'orange',
            'processing': 'blue',
            'rejected': 'gray',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def approve_refunds(self, request, queryset):
        """Approve selected refunds"""
        count = 0
        for refund in queryset.filter(requires_approval=True, approved_by__isnull=True):
            refund.approved_by = request.user
            refund.save()
            count += 1
        self.message_user(request, f'{count} refunds approved')
    approve_refunds.short_description = 'Approve selected refunds'


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """
    Admin interface for Wallets (READ-ONLY for security)
    
    Security Notes:
    - Wallet balances cannot be manually edited
    - All balance changes must go through WalletTransaction
    - This prevents unauthorized fund manipulation
    - Admins can only view and lock/unlock wallets
    """
    
    list_display = [
        'user_link', 'balance_display', 'status', 'is_locked', 'created_at'
    ]
    list_filter = ['status', 'is_locked', 'currency']
    search_fields = ['user__personal_email', 'user__student_email', 'user__first_name', 'user__last_name']
    readonly_fields = [
        'id', 'user', 'balance', 'currency', 'created_at', 'updated_at'
    ]
    
    # Prevent wallet creation/deletion
    def has_add_permission(self, request):
        """Prevent manual wallet creation (auto-created on first use)"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent wallet deletion (preserve user data)"""
        return False
    
    fieldsets = (
        ('Wallet Details', {
            'fields': ('id', 'user', 'balance', 'currency')
        }),
        ('Limits', {
            'fields': ('daily_limit', 'transaction_limit'),
            'description': 'Transaction limits can be adjusted by admin'
        }),
        ('Status', {
            'fields': ('status', 'is_locked', 'lock_reason'),
            'description': 'Admins can lock/unlock wallets for security'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    # Allow admin to lock/unlock wallets but not modify balance
    actions = ['lock_wallets', 'unlock_wallets']
    
    def lock_wallets(self, request, queryset):
        """Lock selected wallets"""
        count = queryset.update(is_locked=True, lock_reason='Locked by admin')
        self.message_user(request, f'{count} wallets locked')
    lock_wallets.short_description = 'Lock selected wallets'
    
    def unlock_wallets(self, request, queryset):
        """Unlock selected wallets"""
        count = queryset.update(is_locked=False, lock_reason='')
        self.message_user(request, f'{count} wallets unlocked')
    unlock_wallets.short_description = 'Unlock selected wallets'
    
    def user_link(self, obj):
        """Display user as clickable link"""
        url = reverse('admin:accounts_customuser_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())
    user_link.short_description = 'User'
    
    def balance_display(self, obj):
        """Display balance with currency"""
        return f"{obj.currency.symbol}{obj.balance}"
    balance_display.short_description = 'Balance'


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    """
    Admin interface for Wallet Transactions (READ-ONLY for security)
    
    Security Notes:
    - Wallet transactions cannot be created/edited/deleted manually
    - All transactions must go through WalletService
    - This maintains transaction integrity and audit trail
    """
    
    list_display = [
        'reference', 'wallet_user', 'transaction_type', 'amount',
        'balance_after', 'created_at'
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['reference', 'wallet__user__personal_email', 'wallet__user__student_email', 'description']
    readonly_fields = [
        'id', 'wallet', 'reference', 'transaction_type', 'amount',
        'balance_before', 'balance_after', 'related_transaction',
        'description', 'metadata', 'created_at'
    ]
    
    # Prevent any modifications
    def has_add_permission(self, request):
        """Prevent manual wallet transaction creation"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent wallet transaction deletion (audit trail)"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent wallet transaction modification"""
        if obj is not None:
            return False
        return True
    
    def wallet_user(self, obj):
        """Get wallet's user"""
        return obj.wallet.user.get_full_name()
    wallet_user.short_description = 'User'


@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(admin.ModelAdmin):
    """Admin interface for Payment Webhooks"""
    
    list_display = [
        'event_id', 'gateway', 'event_type', 'status_badge',
        'is_verified', 'processing_attempts', 'received_at'
    ]
    list_filter = [
        'gateway', 'status', 'is_verified', 'event_type', 'received_at'
    ]
    search_fields = ['event_id', 'event_type', 'transaction__reference']
    readonly_fields = [
        'id', 'received_at', 'processed_at', 'processing_attempts'
    ]
    
    fieldsets = (
        ('Webhook Details', {
            'fields': (
                'id', 'gateway', 'event_type', 'event_id', 'transaction'
            )
        }),
        ('Payload', {
            'fields': ('payload', 'headers', 'signature'),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': (
                'status', 'is_verified', 'processing_attempts',
                'error_message', 'received_at', 'processed_at'
            )
        }),
    )
    
    actions = ['retry_processing']
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'processed': 'green',
            'failed': 'red',
            'pending': 'orange',
            'processing': 'blue',
            'ignored': 'gray',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def retry_processing(self, request, queryset):
        """Retry processing failed webhooks"""
        count = queryset.filter(status='failed').update(
            status='pending',
            error_message=''
        )
        self.message_user(request, f'{count} webhooks queued for retry')
    retry_processing.short_description = 'Retry processing'


# =====================================================
# EXPENSE MANAGEMENT ADMIN
# =====================================================

from .models import (
    ExpenseCategory,
    ExpenseRecipient,
    Expense,
    AccountBalance,
    ExpenseAuditLog,
    BudgetAllocation,
)
from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from datetime import datetime, timedelta
from django.utils.safestring import mark_safe
import json


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    """Admin interface for Expense Categories"""
    
    change_list_template = 'admin/payments/expensecategory/change_list.html'
    
    list_display = ['category_display', 'description_short', 'budget_limit_display', 
                    'expense_count', 'total_spent', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'expense_count', 'total_spent']
    
    fieldsets = (
        ('Category Details', {
            'fields': ('name', 'description', 'icon', 'color')
        }),
        ('Budget', {
            'fields': ('budget_limit',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('expense_count', 'total_spent'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['total_categories'] = ExpenseCategory.objects.count()
        extra_context['active_count'] = ExpenseCategory.objects.filter(is_active=True).count()
        extra_context['total_expenses'] = Expense.objects.count()
        extra_context['with_budget'] = ExpenseCategory.objects.filter(budget_limit__isnull=False).exclude(budget_limit=0).count()
        return super().changelist_view(request, extra_context=extra_context)
    
    def category_display(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; '
            'border-radius: 20px; font-weight: 500;">{} {}</span>',
            obj.color, obj.icon, obj.name
        )
    category_display.short_description = 'Category'
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def budget_limit_display(self, obj):
        if obj.budget_limit:
            formatted_budget = '{:,.2f}'.format(float(obj.budget_limit))
            return format_html(
                '<span style="font-weight: 600;">GHS {}</span>',
                formatted_budget
            )
        return '-'
    budget_limit_display.short_description = 'Budget Limit'
    
    def expense_count(self, obj):
        count = obj.expenses.count()
        return format_html(
            '<span style="background: #e0e7ff; color: #4338ca; padding: 2px 8px; '
            'border-radius: 10px; font-size: 12px;">{}</span>',
            count
        )
    expense_count.short_description = 'Expenses'
    
    def total_spent(self, obj):
        total = obj.expenses.filter(status='paid').aggregate(
            total=Sum('amount')
        )['total'] or 0
        formatted_total = '{:,.2f}'.format(float(total))
        return format_html(
            '<span style="color: #dc2626; font-weight: 600;">GHS {}</span>',
            formatted_total
        )
    total_spent.short_description = 'Total Spent'


@admin.register(ExpenseRecipient)
class ExpenseRecipientAdmin(admin.ModelAdmin):
    """Admin interface for Expense Recipients"""
    
    change_list_template = 'admin/payments/expenserecipient/change_list.html'
    
    list_display = ['name', 'contact_info', 'payment_info', 'is_vendor_badge', 
                    'expense_count', 'total_received', 'is_active']
    list_filter = ['is_vendor', 'is_active', 'momo_provider']
    search_fields = ['name', 'phone', 'email', 'account_number', 'momo_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_vendor', 'is_active')
        }),
        ('Contact Details', {
            'fields': ('phone', 'email', 'address')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'account_number'),
            'classes': ('collapse',)
        }),
        ('Mobile Money', {
            'fields': ('momo_provider', 'momo_number'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['total_recipients'] = ExpenseRecipient.objects.count()
        extra_context['vendor_count'] = ExpenseRecipient.objects.filter(is_vendor=True).count()
        extra_context['individual_count'] = ExpenseRecipient.objects.filter(is_vendor=False).count()
        extra_context['total_paid'] = Expense.objects.filter(status='paid').aggregate(
            total=Sum('amount'))['total'] or 0
        return super().changelist_view(request, extra_context=extra_context)
    
    def contact_info(self, obj):
        parts = []
        if obj.phone:
            parts.append(f'📞 {obj.phone}')
        if obj.email:
            parts.append(f'✉️ {obj.email}')
        return format_html('<br>'.join(parts)) if parts else '-'
    contact_info.short_description = 'Contact'
    
    def payment_info(self, obj):
        parts = []
        if obj.bank_name and obj.account_number:
            parts.append(f'🏦 {obj.bank_name}: {obj.account_number}')
        if obj.momo_number:
            provider = dict(ExpenseRecipient._meta.get_field('momo_provider').choices).get(obj.momo_provider, '')
            parts.append(f'📱 {provider}: {obj.momo_number}')
        return format_html('<br>'.join(parts)) if parts else '-'
    payment_info.short_description = 'Payment Details'
    
    def is_vendor_badge(self, obj):
        if obj.is_vendor:
            return format_html(
                '<span style="background: #fef3c7; color: #d97706; padding: 2px 8px; '
                'border-radius: 10px; font-size: 11px; font-weight: 600;">VENDOR</span>'
            )
        return format_html(
            '<span style="background: #dbeafe; color: #2563eb; padding: 2px 8px; '
            'border-radius: 10px; font-size: 11px; font-weight: 600;">INDIVIDUAL</span>'
        )
    is_vendor_badge.short_description = 'Type'
    
    def expense_count(self, obj):
        return obj.expenses.count()
    expense_count.short_description = 'Expenses'
    
    def total_received(self, obj):
        total = obj.expenses.filter(status='paid').aggregate(
            total=Sum('amount')
        )['total'] or 0
        formatted_total = '{:,.2f}'.format(float(total))
        return format_html(
            '<span style="color: #059669; font-weight: 600;">GHS {}</span>',
            formatted_total
        )
    total_received.short_description = 'Total Received'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """
    Modern Expense Management Admin with Analytics Dashboard
    """
    
    # Use custom template with dashboard
    change_list_template = 'admin/payments/expense/change_list.html'
    
    list_display = [
        'reference_styled', 'title', 'category_badge', 'amount_styled',
        'recipient_display', 'status_badge', 'priority_badge',
        'expense_date', 'created_by_display', 'sms_status'
    ]
    list_filter = [
        'status', 'priority', 'category', 'payment_method',
        'expense_date', 'created_at', 'sms_notification_sent'
    ]
    search_fields = [
        'reference', 'title', 'description', 'recipient__name',
        'recipient_name', 'created_by__first_name', 'created_by__last_name',
        'event_name', 'payment_reference'
    ]
    readonly_fields = [
        'id', 'reference', 'created_at', 'updated_at',
        'sms_notification_sent', 'sms_notification_error'
    ]
    date_hierarchy = 'expense_date'
    autocomplete_fields = ['recipient', 'category', 'created_by', 'approved_by']
    
    fieldsets = (
        ('📋 Expense Details', {
            'fields': (
                ('reference', 'status'),
                'title',
                'description',
                ('category', 'priority'),
                'event_name',
            ),
            'classes': ('wide',)
        }),
        ('💰 Amount & Payment', {
            'fields': (
                ('amount', 'currency'),
                ('payment_method', 'payment_reference'),
                'payment_date',
            )
        }),
        ('👤 Recipient Information', {
            'fields': (
                'recipient',
                'recipient_name',
                'recipient_details',
            ),
            'description': 'Select an existing recipient or enter details manually'
        }),
        ('✅ Approval', {
            'fields': (
                ('created_by', 'approved_by'),
                'approved_at',
                'rejection_reason',
            )
        }),
        ('📎 Attachments', {
            'fields': (
                'receipt_image',
                'receipt_url',
                'attachments',
            ),
            'classes': ('collapse',)
        }),
        ('📝 Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('📱 SMS Notification', {
            'fields': (
                'sms_notification_sent',
                'sms_notification_error',
            ),
            'classes': ('collapse',)
        }),
        ('📅 Timestamps', {
            'fields': (
                'expense_date',
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'approve_expenses', 'reject_expenses', 'mark_as_paid',
        'resend_sms_notification', 'export_expenses'
    ]
    
    class Media:
        css = {
            'all': ['admin/css/expense_admin.css']
        }
        js = ['admin/js/expense_admin.js']
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['total_expenses'] = Expense.objects.count()
        extra_context['paid_count'] = Expense.objects.filter(status='paid').count()
        extra_context['pending_count'] = Expense.objects.filter(status='pending').count()
        extra_context['total_amount'] = Expense.objects.filter(status='paid').aggregate(
            total=Sum('amount'))['total'] or 0
        return super().changelist_view(request, extra_context=extra_context)
    
    def reference_styled(self, obj):
        return format_html(
            '<code style="background: #f1f5f9; padding: 3px 8px; border-radius: 4px; '
            'font-family: monospace; font-size: 12px; color: #475569;">{}</code>',
            obj.reference
        )
    reference_styled.short_description = 'Reference'
    reference_styled.admin_order_field = 'reference'
    
    def category_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 15px; font-size: 11px; font-weight: 500; white-space: nowrap;">'
            '{} {}</span>',
            obj.category.color, obj.category.icon, obj.category.name
        )
    category_badge.short_description = 'Category'
    category_badge.admin_order_field = 'category__name'
    
    def amount_styled(self, obj):
        formatted_amount = '{:,.2f}'.format(float(obj.amount))
        return format_html(
            '<span style="font-weight: 700; font-size: 14px; color: #dc2626;">'
            '{} {}</span>',
            obj.currency.symbol if obj.currency else 'GH₵',
            formatted_amount
        )
    amount_styled.short_description = 'Amount'
    amount_styled.admin_order_field = 'amount'
    
    def recipient_display(self, obj):
        name = obj.recipient.name if obj.recipient else obj.recipient_name or '-'
        if obj.recipient and obj.recipient.is_vendor:
            return format_html(
                '<span style="color: #d97706;">🏪 {}</span>', name
            )
        return format_html('<span>👤 {}</span>', name)
    recipient_display.short_description = 'Recipient'
    
    def status_badge(self, obj):
        colors = {
            'pending': ('#f59e0b', '#fef3c7'),
            'approved': ('#3b82f6', '#dbeafe'),
            'rejected': ('#ef4444', '#fee2e2'),
            'paid': ('#10b981', '#d1fae5'),
            'cancelled': ('#6b7280', '#f3f4f6'),
        }
        text_color, bg_color = colors.get(obj.status, ('#6b7280', '#f3f4f6'))
        icons = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌',
            'paid': '💵',
            'cancelled': '🚫',
        }
        return format_html(
            '<span style="background: {}; color: {}; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600; white-space: nowrap;">'
            '{} {}</span>',
            bg_color, text_color, icons.get(obj.status, ''), obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def priority_badge(self, obj):
        colors = {
            'low': '#10b981',
            'medium': '#3b82f6',
            'high': '#f59e0b',
            'urgent': '#ef4444',
        }
        return format_html(
            '<span style="color: {}; font-weight: 600; font-size: 11px;">{}</span>',
            colors.get(obj.priority, '#6b7280'),
            obj.get_priority_display().upper()
        )
    priority_badge.short_description = 'Priority'
    priority_badge.admin_order_field = 'priority'
    
    def created_by_display(self, obj):
        if obj.created_by:
            return format_html(
                '<span style="color: #4f46e5;">👤 {}</span>',
                obj.created_by.get_full_name() or obj.created_by.username
            )
        return '-'
    created_by_display.short_description = 'Created By'
    
    def sms_status(self, obj):
        if obj.sms_notification_sent:
            return format_html(
                '<span style="color: #10b981;" title="SMS sent to executives">📱✅</span>'
            )
        elif obj.sms_notification_error:
            return format_html(
                '<span style="color: #ef4444;" title="{}">📱❌</span>',
                obj.sms_notification_error[:100]
            )
        return format_html(
            '<span style="color: #9ca3af;">📱⏳</span>'
        )
    sms_status.short_description = 'SMS'
    
    def approve_expenses(self, request, queryset):
        """Approve selected expenses"""
        count = queryset.filter(status='pending').update(
            status='approved',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{count} expense(s) approved')
    approve_expenses.short_description = '✅ Approve selected expenses'
    
    def reject_expenses(self, request, queryset):
        """Reject selected expenses"""
        count = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f'{count} expense(s) rejected')
    reject_expenses.short_description = '❌ Reject selected expenses'
    
    def mark_as_paid(self, request, queryset):
        """Mark selected expenses as paid"""
        count = queryset.filter(status__in=['pending', 'approved']).update(
            status='paid',
            payment_date=timezone.now().date()
        )
        # Recalculate balance after marking as paid
        AccountBalance.recalculate_balance(updated_by=request.user)
        self.message_user(request, f'{count} expense(s) marked as paid')
    mark_as_paid.short_description = '💵 Mark as paid'
    
    def resend_sms_notification(self, request, queryset):
        """Resend SMS notification to executives"""
        success_count = 0
        for expense in queryset:
            expense.sms_notification_sent = False
            expense.save()
            expense.send_expense_notification_to_executives()
            if expense.sms_notification_sent:
                success_count += 1
        self.message_user(
            request, 
            f'SMS resent for {success_count}/{queryset.count()} expense(s)'
        )
    resend_sms_notification.short_description = '📱 Resend SMS notification'
    
    def export_expenses(self, request, queryset):
        """Export expenses to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="expenses.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Reference', 'Date', 'Title', 'Category', 'Amount', 'Currency',
            'Recipient', 'Payment Method', 'Status', 'Created By', 'Notes'
        ])
        
        for expense in queryset:
            writer.writerow([
                expense.reference,
                expense.expense_date,
                expense.title,
                expense.category.name,
                expense.amount,
                expense.currency.code if expense.currency else 'GHS',
                expense.recipient_display_name,
                expense.get_payment_method_display(),
                expense.get_status_display(),
                expense.created_by.get_full_name() if expense.created_by else '',
                expense.notes
            ])
        
        return response
    export_expenses.short_description = '📊 Export to CSV'
    
    def save_model(self, request, obj, form, change):
        """Set created_by on new expenses"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AccountBalance)
class AccountBalanceAdmin(admin.ModelAdmin):
    """
    Admin interface for Account Balance with Financial Summary Dashboard
    """
    
    change_list_template = 'admin/payments/accountbalance/change_list.html'
    
    list_display = ['balance_summary', 'income_display', 'expenditure_display', 
                    'current_balance_display', 'updated_at']
    readonly_fields = [
        'id', 'total_income', 'total_expenditure', 'current_balance_computed',
        'created_at', 'updated_at', 'last_updated_by', 'financial_dashboard'
    ]
    
    fieldsets = (
        ('💰 Financial Dashboard', {
            'fields': ('financial_dashboard',),
            'classes': ('wide',)
        }),
        ('💵 Balance Details', {
            'fields': (
                'initial_balance',
                'total_income',
                'total_expenditure',
                'current_balance_computed',
                'currency',
            )
        }),
        ('📝 Notes', {
            'fields': ('notes',)
        }),
        ('📅 Metadata', {
            'fields': ('id', 'last_updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['recalculate_balance']
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        balance_info = AccountBalance.get_current_balance()
        extra_context['current_balance'] = balance_info['current_balance']
        extra_context['total_income'] = balance_info['total_income']
        extra_context['total_expenses'] = balance_info['total_expenditure']
        obj = AccountBalance.objects.first()
        extra_context['last_updated'] = obj.updated_at if obj else None
        return super().changelist_view(request, extra_context=extra_context)
    
    def has_add_permission(self, request):
        """Only allow one AccountBalance instance"""
        return not AccountBalance.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of AccountBalance"""
        return False
    
    def balance_summary(self, obj):
        return format_html(
            '<span style="font-weight: 700; font-size: 14px;">Account Balance</span>'
        )
    balance_summary.short_description = 'Account'
    
    def income_display(self, obj):
        balance_info = AccountBalance.get_current_balance()
        formatted_income = '{:,.2f}'.format(float(balance_info['total_income']))
        return format_html(
            '<span style="color: #10b981; font-weight: 700; font-size: 14px;">'
            '📈 GHS {}</span>',
            formatted_income
        )
    income_display.short_description = 'Total Income'
    
    def expenditure_display(self, obj):
        balance_info = AccountBalance.get_current_balance()
        formatted_expenditure = '{:,.2f}'.format(float(balance_info['total_expenditure']))
        return format_html(
            '<span style="color: #ef4444; font-weight: 700; font-size: 14px;">'
            '📉 GHS {}</span>',
            formatted_expenditure
        )
    expenditure_display.short_description = 'Total Expenditure'
    
    def current_balance_display(self, obj):
        balance_info = AccountBalance.get_current_balance()
        balance = balance_info['current_balance']
        color = '#10b981' if balance >= 0 else '#ef4444'
        formatted_balance = '{:,.2f}'.format(float(balance))
        return format_html(
            '<span style="color: {}; font-weight: 700; font-size: 16px;">'
            '💳 GHS {}</span>',
            color, formatted_balance
        )
    current_balance_display.short_description = 'Current Balance'
    
    def current_balance_computed(self, obj):
        balance_info = AccountBalance.get_current_balance()
        formatted_balance = '{:,.2f}'.format(float(balance_info['current_balance']))
        return format_html(
            '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
            'color: white; padding: 20px; border-radius: 12px; text-align: center;">'
            '<div style="font-size: 14px; opacity: 0.9;">Current Balance</div>'
            '<div style="font-size: 32px; font-weight: 700; margin: 10px 0;">'
            'GHS {}</div>'
            '</div>',
            formatted_balance
        )
    current_balance_computed.short_description = 'Current Balance'
    
    def financial_dashboard(self, obj):
        balance_info = AccountBalance.get_current_balance()
        
        # Get monthly income trend
        from datetime import datetime, timedelta
        today = datetime.now().date()
        six_months_ago = today - timedelta(days=180)
        
        # Get monthly expenses
        monthly_expenses = Expense.objects.filter(
            status='paid',
            expense_date__gte=six_months_ago
        ).annotate(
            month=TruncMonth('expense_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        # Get monthly income
        monthly_income = Transaction.objects.filter(
            status='success',
            transaction_type__in=['payment', 'donation'],
            initiated_at__gte=six_months_ago
        ).annotate(
            month=TruncMonth('initiated_at')
        ).values('month').annotate(
            total=Sum('net_amount')
        ).order_by('month')
        
        # Recent transactions
        recent_income = Transaction.objects.filter(
            status='success',
            transaction_type__in=['payment', 'donation']
        ).order_by('-completed_at')[:5]
        
        recent_expenses = Expense.objects.filter(
            status='paid'
        ).order_by('-expense_date')[:5]
        
        html = f'''
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <!-- Summary Cards -->
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px;">
                <!-- Initial Balance Card -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 24px; border-radius: 16px; color: white; box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">💰 Initial Balance</div>
                    <div style="font-size: 28px; font-weight: 700;">GHS {balance_info['initial_balance']:,.2f}</div>
                </div>
                
                <!-- Total Income Card -->
                <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                    padding: 24px; border-radius: 16px; color: white; box-shadow: 0 10px 40px rgba(17, 153, 142, 0.3);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">📈 Total Income</div>
                    <div style="font-size: 28px; font-weight: 700;">GHS {balance_info['total_income']:,.2f}</div>
                </div>
                
                <!-- Total Expenditure Card -->
                <div style="background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); 
                    padding: 24px; border-radius: 16px; color: white; box-shadow: 0 10px 40px rgba(235, 51, 73, 0.3);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">📉 Total Expenditure</div>
                    <div style="font-size: 28px; font-weight: 700;">GHS {balance_info['total_expenditure']:,.2f}</div>
                </div>
                
                <!-- Current Balance Card -->
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 24px; border-radius: 16px; color: white; box-shadow: 0 10px 40px rgba(240, 147, 251, 0.3);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">💳 Current Balance</div>
                    <div style="font-size: 28px; font-weight: 700;">GHS {balance_info['current_balance']:,.2f}</div>
                </div>
            </div>
            
            <!-- Quick Stats -->
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                <!-- Recent Income -->
                <div style="background: white; border-radius: 16px; padding: 24px; 
                    box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                    <h3 style="margin: 0 0 20px; color: #1f2937; font-size: 18px; 
                        display: flex; align-items: center; gap: 8px;">
                        📈 Recent Income
                    </h3>
                    <div style="space-y: 12px;">
        '''
        
        for txn in recent_income:
            html += f'''
                        <div style="display: flex; justify-content: space-between; align-items: center;
                            padding: 12px; background: #f0fdf4; border-radius: 8px; margin-bottom: 8px;">
                            <div>
                                <div style="font-weight: 600; color: #166534;">{txn.description[:30]}...</div>
                                <div style="font-size: 12px; color: #6b7280;">
                                    {txn.completed_at.strftime('%d %b %Y') if txn.completed_at else '-'}
                                </div>
                            </div>
                            <div style="font-weight: 700; color: #10b981;">
                                +GHS {txn.net_amount:,.2f}
                            </div>
                        </div>
            '''
        
        html += '''
                    </div>
                </div>
                
                <!-- Recent Expenses -->
                <div style="background: white; border-radius: 16px; padding: 24px; 
                    box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                    <h3 style="margin: 0 0 20px; color: #1f2937; font-size: 18px; 
                        display: flex; align-items: center; gap: 8px;">
                        📉 Recent Expenses
                    </h3>
                    <div style="space-y: 12px;">
        '''
        
        for exp in recent_expenses:
            html += f'''
                        <div style="display: flex; justify-content: space-between; align-items: center;
                            padding: 12px; background: #fef2f2; border-radius: 8px; margin-bottom: 8px;">
                            <div>
                                <div style="font-weight: 600; color: #991b1b;">{exp.title[:30]}</div>
                                <div style="font-size: 12px; color: #6b7280;">
                                    {exp.expense_date.strftime('%d %b %Y')} • {exp.category.name}
                                </div>
                            </div>
                            <div style="font-weight: 700; color: #ef4444;">
                                -GHS {exp.amount:,.2f}
                            </div>
                        </div>
            '''
        
        html += '''
                    </div>
                </div>
            </div>
        </div>
        '''
        
        return mark_safe(html)
    financial_dashboard.short_description = 'Financial Overview'
    
    def recalculate_balance(self, request, queryset):
        """Recalculate account balance from transactions and expenses"""
        AccountBalance.recalculate_balance(updated_by=request.user)
        self.message_user(request, 'Account balance recalculated successfully')
    recalculate_balance.short_description = '🔄 Recalculate balance'


@admin.register(ExpenseAuditLog)
class ExpenseAuditLogAdmin(admin.ModelAdmin):
    """Admin interface for Expense Audit Logs (READ-ONLY)"""
    
    change_list_template = 'admin/payments/expenseauditlog/change_list.html'
    
    list_display = [
        'expense_reference', 'action_badge', 'performed_by_display',
        'created_at', 'ip_address'
    ]
    list_filter = ['action', 'created_at']
    search_fields = ['expense__reference', 'performed_by__username', 'comments']
    readonly_fields = [
        'id', 'expense', 'action', 'performed_by', 'previous_values',
        'new_values', 'comments', 'ip_address', 'user_agent', 'created_at'
    ]
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['total_logs'] = ExpenseAuditLog.objects.count()
        extra_context['create_count'] = ExpenseAuditLog.objects.filter(action='created').count()
        extra_context['update_count'] = ExpenseAuditLog.objects.filter(action='updated').count()
        extra_context['approve_count'] = ExpenseAuditLog.objects.filter(action='approved').count()
        return super().changelist_view(request, extra_context=extra_context)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def expense_reference(self, obj):
        return format_html(
            '<code style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">{}</code>',
            obj.expense.reference
        )
    expense_reference.short_description = 'Expense'
    
    def action_badge(self, obj):
        colors = {
            'created': '#3b82f6',
            'updated': '#f59e0b',
            'approved': '#10b981',
            'rejected': '#ef4444',
            'paid': '#8b5cf6',
            'cancelled': '#6b7280',
            'deleted': '#ef4444',
        }
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            colors.get(obj.action, '#6b7280'),
            obj.get_action_display()
        )
    action_badge.short_description = 'Action'
    
    def performed_by_display(self, obj):
        if obj.performed_by:
            return obj.performed_by.get_full_name() or obj.performed_by.username
        return '-'
    performed_by_display.short_description = 'By'


@admin.register(BudgetAllocation)
class BudgetAllocationAdmin(admin.ModelAdmin):
    """Admin interface for Budget Allocations"""
    
    change_list_template = 'admin/payments/budgetallocation/change_list.html'
    
    list_display = [
        'name', 'category_display', 'allocated_amount_display',
        'spent_display', 'remaining_display', 'utilization_bar',
        'period_display', 'is_active'
    ]
    list_filter = ['is_active', 'category', 'start_date']
    search_fields = ['name', 'category__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'spent_amount', 
                       'remaining_amount', 'utilization_percentage']
    
    fieldsets = (
        ('Budget Details', {
            'fields': ('name', 'category', 'is_active')
        }),
        ('Amount', {
            'fields': ('allocated_amount', 'currency')
        }),
        ('Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Statistics', {
            'fields': ('spent_amount', 'remaining_amount', 'utilization_percentage'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes', 'created_by'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['total_budgets'] = BudgetAllocation.objects.count()
        extra_context['total_allocated'] = BudgetAllocation.objects.filter(is_active=True).aggregate(
            total=Sum('allocated_amount'))['total'] or 0
        # Calculate total spent from expenses
        extra_context['total_spent'] = Expense.objects.filter(status='paid').aggregate(
            total=Sum('amount'))['total'] or 0
        extra_context['remaining'] = extra_context['total_allocated'] - extra_context['total_spent']
        return super().changelist_view(request, extra_context=extra_context)
    
    def category_display(self, obj):
        if obj.category:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; '
                'border-radius: 10px; font-size: 11px;">{} {}</span>',
                obj.category.color, obj.category.icon, obj.category.name
            )
        return format_html(
            '<span style="background: #e0e7ff; color: #4338ca; padding: 2px 8px; '
            'border-radius: 10px; font-size: 11px;">General</span>'
        )
    category_display.short_description = 'Category'
    
    def allocated_amount_display(self, obj):
        formatted_amount = '{:,.2f}'.format(float(obj.allocated_amount))
        return format_html(
            '<span style="font-weight: 600;">GHS {}</span>',
            formatted_amount
        )
    allocated_amount_display.short_description = 'Allocated'
    
    def spent_display(self, obj):
        formatted_spent = '{:,.2f}'.format(float(obj.spent_amount))
        return format_html(
            '<span style="color: #ef4444;">GHS {}</span>',
            formatted_spent
        )
    spent_display.short_description = 'Spent'
    
    def remaining_display(self, obj):
        remaining = obj.remaining_amount
        color = '#10b981' if remaining >= 0 else '#ef4444'
        formatted_remaining = '{:,.2f}'.format(float(remaining))
        return format_html(
            '<span style="color: {}; font-weight: 600;">GHS {}</span>',
            color, formatted_remaining
        )
    remaining_display.short_description = 'Remaining'
    
    def utilization_bar(self, obj):
        percentage = min(obj.utilization_percentage, 100)
        color = '#10b981' if percentage < 70 else '#f59e0b' if percentage < 90 else '#ef4444'
        over_budget = obj.is_over_budget
        
        return format_html(
            '<div style="width: 100px; background: #e5e7eb; border-radius: 10px; overflow: hidden;">'
            '<div style="width: {}%; background: {}; height: 8px;"></div>'
            '</div>'
            '<span style="font-size: 11px; color: {}; margin-left: 8px;">'
            '{}{}%</span>',
            percentage, color, color,
            '⚠️ ' if over_budget else '',
            obj.utilization_percentage
        )
    utilization_bar.short_description = 'Utilization'
    
    def period_display(self, obj):
        return format_html(
            '<span style="font-size: 12px;">{} → {}</span>',
            obj.start_date.strftime('%d %b %Y'),
            obj.end_date.strftime('%d %b %Y')
        )
    period_display.short_description = 'Period'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
