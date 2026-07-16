"""
Donation Admin Configuration
Django admin interface for donation management
Includes gateway transfer functionality for automated disbursements

NOTE: For full standalone dashboard, visit /donations/admin/dashboard/
"""
from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import (
    DonationWallet,
    Donation,
    DonorProfile,
    DonationWithdrawal,
    DonationTransaction
)
from .services import DonationService
from utils.media_mixins import make_media_admin_mixin

# Create media admin mixin for DonationWithdrawal model
DonationWithdrawalMediaAdminMixin = make_media_admin_mixin(['receipt_image'])

@admin.register(DonationWallet)
class DonationWalletAdmin(admin.ModelAdmin):
    """Admin for the donation wallet (singleton)"""
    
    list_display = [
        'id', 'balance_display', 'total_received_display',
        'total_withdrawn_display', 'total_donations_count',
        'total_donors_count', 'updated_at'
    ]
    readonly_fields = [
        'id', 'balance', 'total_received', 'total_withdrawn',
        'total_donations_count', 'total_donors_count',
        'created_at', 'updated_at'
    ]
    
    def has_add_permission(self, request):
        # Only allow one wallet
        return not DonationWallet.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def balance_display(self, obj):
        return f"GH₵{obj.balance:,.2f}"
    balance_display.short_description = "Balance"
    
    def total_received_display(self, obj):
        return f"GH₵{obj.total_received:,.2f}"
    total_received_display.short_description = "Total Received"
    
    def total_withdrawn_display(self, obj):
        return f"GH₵{obj.total_withdrawn:,.2f}"
    total_withdrawn_display.short_description = "Total Withdrawn"


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    """Admin for donations"""
    
    list_display = [
        'reference', 'donor_display', 'amount_display',
        'status', 'is_anonymous', 'completed_at', 'created_at'
    ]
    list_filter = ['status', 'is_anonymous', 'gateway', 'created_at']
    search_fields = ['reference', 'donor_name', 'donor_email', 'donor_phone']
    readonly_fields = [
        'id', 'reference', 'donor', 'donor_name', 'donor_email',
        'donor_phone', 'amount', 'message', 'is_anonymous',
        'status', 'gateway', 'gateway_reference',
        'gateway_response', 'ip_address', 'user_agent',
        'created_at', 'completed_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Donation Info', {
            'fields': ('id', 'reference', 'amount', 'status', 'message')
        }),
        ('Donor Info', {
            'fields': ('donor', 'donor_name', 'donor_email', 'donor_phone')
        }),
        ('Display Options', {
            'fields': ('is_anonymous',)
        }),
        ('Gateway Info', {
            'fields': ('gateway', 'gateway_reference', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Technical Info', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at', 'updated_at')
        }),
    )
    
    def donor_display(self, obj):
        if obj.is_anonymous:
            return format_html('<i>Anonymous</i>')
        return obj.donor_name or obj.donor_email
    donor_display.short_description = "Donor"
    
    def amount_display(self, obj):
        return f"GH₵{obj.amount:,.2f}"
    amount_display.short_description = "Amount"
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    """Admin for donor profiles"""
    
    list_display = [
        'user_name', 'total_donated_display', 'donation_count',
        'first_donation_at', 'last_donation_at'
    ]
    search_fields = ['user__first_name', 'user__last_name', 'user__student_email']
    readonly_fields = [
        'id', 'user', 'total_donated', 'donation_count',
        'first_donation_at', 'last_donation_at',
        'created_at', 'updated_at'
    ]
    ordering = ['-total_donated']
    
    def user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    user_name.short_description = "User"
    
    def total_donated_display(self, obj):
        return f"GH₵{obj.total_donated:,.2f}"
    total_donated_display.short_description = "Total Donated"
    
    def has_add_permission(self, request):
        return False


@admin.register(DonationWithdrawal)
class DonationWithdrawalAdmin(DonationWithdrawalMediaAdminMixin, admin.ModelAdmin):
    """
    Admin for donation withdrawals with gateway transfer support
    Allows direct transfers via Paystack to recipients
    
    NOTE: For full dashboard experience, visit /donations/admin/dashboard/
    """
    
    # Custom template with dashboard button
    change_list_template = 'admin/donations/donationwithdrawal/change_list.html'
    
    list_display = [
        'reference', 'amount_display', 'recipient_name',
        'purpose_short', 'category', 'transfer_method_badge',
        'status_badge', 'initiated_by_name', 'completed_at'
    ]
    list_filter = ['status', 'transfer_method', 'category', 'created_at']
    search_fields = [
        'reference', 'recipient_name', 'purpose', 'recipient_account',
        'initiated_by__first_name', 'initiated_by__last_name'
    ]
    readonly_fields = [
        'id', 'reference', 'balance_before', 'balance_after',
        'gateway_transfer_code', 'gateway_recipient_code',
        'gateway_reference', 'gateway_response', 'gateway_fee',
        'created_at', 'approved_at', 'completed_at', 'updated_at',
        'transfer_status_info', 'gateway_receipt_display'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    actions = ['process_gateway_transfer', 'verify_transfers', 'mark_as_completed_manual']
    
    def changelist_view(self, request, extra_context=None):
        """Add link to standalone dashboard"""
        extra_context = extra_context or {}
        extra_context['show_dashboard_button'] = True
        return super().changelist_view(request, extra_context=extra_context)
    
    fieldsets = (
        ('Withdrawal Info', {
            'fields': (
                'id', 'reference', 'amount', 'status', 'status_message'
            )
        }),
        ('Transfer Method', {
            'fields': ('transfer_method', 'transfer_status_info'),
            'description': 'Choose "Gateway Transfer" for automatic Paystack disbursement'
        }),
        ('Recipient Info', {
            'fields': (
                'recipient_name', 'recipient_account', 
                'recipient_bank', 'recipient_bank_code'
            ),
            'description': 'For gateway transfers, select the correct bank/provider code'
        }),
        ('Purpose', {
            'fields': ('purpose', 'description', 'category')
        }),
        ('Manual Transfer Documentation', {
            'fields': ('receipt_image',),
            'classes': ('collapse',),
            'description': 'Only needed for manual transfers'
        }),
        ('Gateway Transfer Details', {
            'fields': (
                'gateway', 'gateway_transfer_code', 'gateway_recipient_code',
                'gateway_reference', 'gateway_fee', 'gateway_receipt_display'
            ),
            'classes': ('collapse',),
            'description': 'Automatically filled when processing gateway transfer'
        }),
        ('Gateway Response (Debug)', {
            'fields': ('gateway_response',),
            'classes': ('collapse',),
        }),
        ('Authorization', {
            'fields': ('initiated_by', 'approved_by')
        }),
        ('Balance Tracking', {
            'fields': ('balance_before', 'balance_after'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'approved_at', 'completed_at', 'updated_at')
        }),
    )
    
    def get_changeform_initial_data(self, request):
        """Set default values for new withdrawals"""
        wallet = DonationWallet.get_wallet()
        return {
            'balance_before': wallet.balance,
            'balance_after': wallet.balance,
            'initiated_by': request.user,
        }
    
    def save_model(self, request, obj, form, change):
        """Set initiated_by and balance tracking on save"""
        if not change:  # New withdrawal
            obj.initiated_by = request.user
            wallet = DonationWallet.get_wallet()
            obj.balance_before = wallet.balance
            obj.balance_after = wallet.balance - obj.amount
        super().save_model(request, obj, form, change)
    
    def amount_display(self, obj):
        return format_html(
            '<strong style="color: #d32f2f;">{}</strong>',
            f"GH₵{obj.amount:,.2f}"
        )
    amount_display.short_description = "Amount"
    
    def purpose_short(self, obj):
        return obj.purpose[:40] + "..." if len(obj.purpose) > 40 else obj.purpose
    purpose_short.short_description = "Purpose"
    
    def initiated_by_name(self, obj):
        return f"{obj.initiated_by.first_name} {obj.initiated_by.last_name}"
    initiated_by_name.short_description = "Initiated By"
    
    def transfer_method_badge(self, obj):
        colors = {
            'manual': '#757575',
            'gateway': '#1976d2',
        }
        labels = {
            'manual': '📝 Manual',
            'gateway': '⚡ Gateway',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            colors.get(obj.transfer_method, '#757575'),
            labels.get(obj.transfer_method, obj.transfer_method)
        )
    transfer_method_badge.short_description = "Method"
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ff9800',
            'approved': '#2196f3',
            'processing': '#9c27b0',
            'completed': '#4caf50',
            'rejected': '#f44336',
            'failed': '#d32f2f',
        }
        icons = {
            'pending': '⏳',
            'approved': '✅',
            'processing': '🔄',
            'completed': '✓',
            'rejected': '❌',
            'failed': '⚠️',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px;">{} {}</span>',
            colors.get(obj.status, '#757575'),
            icons.get(obj.status, ''),
            obj.get_status_display()
        )
    status_badge.short_description = "Status"
    
    def transfer_status_info(self, obj):
        """Display transfer status with helpful info"""
        if obj.transfer_method == 'gateway':
            if obj.status == 'completed':
                return format_html(
                    '<div style="background: #e8f5e9; padding: 10px; border-radius: 4px;">'
                    '<strong style="color: #2e7d32;">✓ Gateway Transfer Completed</strong><br>'
                    '<small>Transfer Code: {}</small><br>'
                    '<small>Fee: {}</small>'
                    '</div>',
                    obj.gateway_transfer_code or 'N/A',
                    f"GH₵{obj.gateway_fee:,.2f}"
                )
            elif obj.status == 'processing':
                return format_html(
                    '<div style="background: #fff3e0; padding: 10px; border-radius: 4px;">'
                    '<strong style="color: #e65100;">🔄 Transfer Processing</strong><br>'
                    '<small>Transfer Code: {}</small>'
                    '</div>',
                    obj.gateway_transfer_code or 'Pending'
                )
            elif obj.status == 'failed':
                return format_html(
                    '<div style="background: #ffebee; padding: 10px; border-radius: 4px;">'
                    '<strong style="color: #c62828;">⚠️ Transfer Failed</strong><br>'
                    '<small>{}</small>'
                    '</div>',
                    obj.status_message or 'Unknown error'
                )
        
        if obj.status == 'pending':
            return format_html(
                '<div style="background: #e3f2fd; padding: 10px; border-radius: 4px;">'
                '<strong>📝 Pending Approval</strong><br>'
                '<small>Select this withdrawal and use "Process Gateway Transfer" action '
                'to send money directly via Paystack.</small>'
                '</div>'
            )
        
        return format_html(
            '<div style="background: #f5f5f5; padding: 10px; border-radius: 4px;">'
            '<small>Status: {}</small>'
            '</div>',
            obj.get_status_display()
        )
    transfer_status_info.short_description = "Transfer Status"
    
    def gateway_receipt_display(self, obj):
        """Display gateway receipt/proof"""
        if obj.transfer_method == 'gateway' and obj.status == 'completed':
            return format_html(
                '<div style="background: #f5f5f5; padding: 15px; border-radius: 4px; '
                'font-family: monospace; font-size: 12px;">'
                '<strong>PAYSTACK TRANSFER RECEIPT</strong><br>'
                '─────────────────────────────<br>'
                'Reference: {}<br>'
                'Transfer Code: {}<br>'
                'Amount: {}<br>'
                'Fee: {}<br>'
                'Recipient: {}<br>'
                'Account: {}<br>'
                'Bank: {}<br>'
                'Status: COMPLETED ✓<br>'
                'Date: {}<br>'
                '─────────────────────────────<br>'
                '<em>Verified by Paystack</em>'
                '</div>',
                obj.reference,
                obj.gateway_transfer_code or 'N/A',
                f"GH₵{obj.amount:,.2f}",
                f"GH₵{obj.gateway_fee:,.2f}",
                obj.recipient_name,
                obj.recipient_account,
                obj.get_recipient_bank_code_display() if obj.recipient_bank_code else obj.recipient_bank,
                obj.completed_at.strftime('%Y-%m-%d %H:%M:%S') if obj.completed_at else 'N/A'
            )
        return "N/A - Gateway transfer not completed"
    gateway_receipt_display.short_description = "Gateway Receipt"
    
    def receipt_preview(self, obj):
        if obj.receipt_image:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-height: 100px;" />'
                '</a>',
                obj.receipt_image.url,
                obj.receipt_image.url
            )
        return "No receipt"
    receipt_preview.short_description = "Receipt"
    
    # ==========================================
    # ADMIN ACTIONS
    # ==========================================
    
    @admin.action(description="⚡ Process Gateway Transfer (Send via Paystack)")
    def process_gateway_transfer(self, request, queryset):
        """Process selected withdrawals via Paystack transfer"""
        processed = 0
        failed = 0
        
        for withdrawal in queryset:
            if withdrawal.status not in ['pending', 'approved']:
                self.message_user(
                    request,
                    f"⚠️ {withdrawal.reference}: Cannot process - status is {withdrawal.status}",
                    messages.WARNING
                )
                continue
            
            if not withdrawal.recipient_account:
                self.message_user(
                    request,
                    f"❌ {withdrawal.reference}: Missing recipient account number",
                    messages.ERROR
                )
                failed += 1
                continue
            
            if not withdrawal.recipient_bank_code:
                self.message_user(
                    request,
                    f"❌ {withdrawal.reference}: Missing bank/provider code. Please edit and select one.",
                    messages.ERROR
                )
                failed += 1
                continue
            
            # Process the transfer
            result = DonationService.initiate_gateway_transfer(
                withdrawal=withdrawal,
                performed_by=request.user
            )
            
            if result['success']:
                processed += 1
                self.message_user(
                    request,
                    f"✅ {withdrawal.reference}: Transfer initiated - {result.get('message', 'Success')}",
                    messages.SUCCESS
                )
            else:
                failed += 1
                self.message_user(
                    request,
                    f"❌ {withdrawal.reference}: {result.get('error', 'Unknown error')}",
                    messages.ERROR
                )
        
        if processed:
            self.message_user(
                request,
                f"🎉 Successfully initiated {processed} gateway transfer(s)",
                messages.SUCCESS
            )
    
    @admin.action(description="🔍 Verify Transfer Status")
    def verify_transfers(self, request, queryset):
        """Verify status of gateway transfers"""
        for withdrawal in queryset:
            if not withdrawal.gateway_transfer_code:
                self.message_user(
                    request,
                    f"⚠️ {withdrawal.reference}: No transfer code - not a gateway transfer",
                    messages.WARNING
                )
                continue
            
            result = DonationService.verify_transfer(withdrawal.gateway_transfer_code)
            
            if result['success']:
                transfer_status = result.get('transfer_status', 'unknown')
                
                # Update withdrawal if status changed
                if transfer_status == 'success' and withdrawal.status != 'completed':
                    DonationService.complete_gateway_transfer(
                        withdrawal=withdrawal,
                        transfer_status='success',
                        gateway_data=result.get('details', {})
                    )
                    self.message_user(
                        request,
                        f"✅ {withdrawal.reference}: Transfer completed!",
                        messages.SUCCESS
                    )
                elif transfer_status in ['failed', 'reversed']:
                    DonationService.complete_gateway_transfer(
                        withdrawal=withdrawal,
                        transfer_status=transfer_status,
                        gateway_data=result.get('details', {})
                    )
                    self.message_user(
                        request,
                        f"⚠️ {withdrawal.reference}: Transfer {transfer_status}",
                        messages.WARNING
                    )
                else:
                    self.message_user(
                        request,
                        f"🔄 {withdrawal.reference}: Status is '{transfer_status}'",
                        messages.INFO
                    )
            else:
                self.message_user(
                    request,
                    f"❌ {withdrawal.reference}: Verification failed - {result.get('error')}",
                    messages.ERROR
                )
    
    @admin.action(description="✓ Mark as Completed (Manual Transfer)")
    def mark_as_completed_manual(self, request, queryset):
        """Mark manual transfers as completed"""
        from .models import DonationTransaction, DonationWallet
        
        completed = 0
        for withdrawal in queryset:
            if withdrawal.status == 'completed':
                continue
            
            if withdrawal.transfer_method == 'gateway':
                self.message_user(
                    request,
                    f"⚠️ {withdrawal.reference}: Use 'Verify Transfer Status' for gateway transfers",
                    messages.WARNING
                )
                continue
            
            # For manual transfers, mark as completed
            wallet = DonationWallet.get_wallet()
            
            if withdrawal.status == 'pending':
                # Need to deduct from wallet
                if withdrawal.amount > wallet.balance:
                    self.message_user(
                        request,
                        f"❌ {withdrawal.reference}: Insufficient wallet balance",
                        messages.ERROR
                    )
                    continue
                
                balance_before = wallet.balance
                wallet.withdraw(withdrawal.amount)
                withdrawal.balance_before = balance_before
                withdrawal.balance_after = wallet.balance
            
            withdrawal.status = 'completed'
            withdrawal.completed_at = timezone.now()
            withdrawal.approved_by = request.user
            withdrawal.approved_at = timezone.now()
            withdrawal.transfer_method = 'manual'
            withdrawal.save()
            
            # Create transaction record
            DonationTransaction.objects.create(
                transaction_type='withdrawal',
                amount=withdrawal.amount,
                withdrawal=withdrawal,
                balance_before=withdrawal.balance_before,
                balance_after=withdrawal.balance_after,
                description=f"Manual transfer: {withdrawal.purpose}",
                performed_by=request.user
            )
            
            completed += 1
        
        if completed:
            self.message_user(
                request,
                f"✅ Marked {completed} withdrawal(s) as completed",
                messages.SUCCESS
            )


@admin.register(DonationTransaction)
class DonationTransactionAdmin(admin.ModelAdmin):
    """Admin for donation transactions (audit log)"""
    
    list_display = [
        'created_at', 'transaction_type', 'amount_display',
        'balance_before_display', 'balance_after_display',
        'description_short', 'performed_by_name'
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['description', 'donation__reference', 'withdrawal__reference']
    readonly_fields = [
        'id', 'transaction_type', 'amount', 'donation',
        'withdrawal', 'balance_before', 'balance_after',
        'description', 'performed_by', 'created_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def amount_display(self, obj):
        prefix = "+" if obj.transaction_type == 'donation' else "-"
        return f"{prefix}GH₵{obj.amount:,.2f}"
    amount_display.short_description = "Amount"
    
    def balance_before_display(self, obj):
        return f"GH₵{obj.balance_before:,.2f}"
    balance_before_display.short_description = "Before"
    
    def balance_after_display(self, obj):
        return f"GH₵{obj.balance_after:,.2f}"
    balance_after_display.short_description = "After"
    
    def description_short(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_short.short_description = "Description"
    
    def performed_by_name(self, obj):
        if obj.performed_by:
            return f"{obj.performed_by.first_name} {obj.performed_by.last_name}"
        return "-"
    performed_by_name.short_description = "By"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
