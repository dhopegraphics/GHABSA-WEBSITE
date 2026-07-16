"""
Payment System Serializers
"""
from rest_framework import serializers
from decimal import Decimal
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


class CurrencySerializer(serializers.ModelSerializer):
    """Serializer for Currency model"""
    
    class Meta:
        model = Currency
        fields = ['code', 'name', 'symbol', 'exchange_rate', 'is_active']


class PaymentGatewaySerializer(serializers.ModelSerializer):
    """Serializer for PaymentGateway model"""
    
    class Meta:
        model = PaymentGateway
        fields = [
            'id', 'name', 'display_name', 'description', 'is_active',
            'status', 'supports_refunds', 'supports_recurring',
            'supported_currencies', 'supported_methods', 'priority'
        ]


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    
    currency_details = CurrencySerializer(source='currency', read_only=True)
    gateway_details = PaymentGatewaySerializer(source='gateway', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'reference', 'user', 'user_name', 'transaction_type',
            'amount', 'currency', 'currency_details', 'gateway', 'gateway_details',
            'status', 'status_message', 'description', 'gateway_fee',
            'platform_fee', 'net_amount', 'payment_method', 'payment_channel',
            'gateway_reference', 'customer_email', 'customer_phone',
            'customer_name', 'initiated_at', 'completed_at', 'metadata',
            'is_test', 'can_be_refunded'
        ]
        read_only_fields = [
            'id', 'reference', 'gateway_fee', 'net_amount', 'gateway_reference',
            'initiated_at', 'completed_at', 'can_be_refunded'
        ]


class PaymentInitializationSerializer(serializers.Serializer):
    """Serializer for payment initialization request"""
    
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    currency = serializers.CharField(max_length=3, default='GHS')
    description = serializers.CharField(max_length=500)
    gateway = serializers.CharField(max_length=50, default='paystack')
    callback_url = serializers.URLField()
    
    # Optional fields
    content_type_id = serializers.IntegerField(required=False)
    object_id = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False, default=dict)
    customer_email = serializers.EmailField(required=False)
    customer_phone = serializers.CharField(required=False, allow_blank=True)
    customer_name = serializers.CharField(required=False, allow_blank=True)
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
    
    def validate_gateway(self, value):
        """Validate gateway exists and is active"""
        try:
            gateway = PaymentGateway.objects.get(name=value, is_active=True, status='active')
        except PaymentGateway.DoesNotExist:
            raise serializers.ValidationError(f"Gateway '{value}' not available")
        return value


class PaymentVerificationSerializer(serializers.Serializer):
    """Serializer for payment verification request"""
    
    reference = serializers.CharField(max_length=100)
    
    def validate_reference(self, value):
        """Validate reference exists"""
        try:
            Transaction.objects.get(reference=value)
        except Transaction.DoesNotExist:
            raise serializers.ValidationError(f"Transaction '{value}' not found")
        return value


class RefundSerializer(serializers.ModelSerializer):
    """Serializer for Refund model"""
    
    original_transaction_reference = serializers.CharField(
        source='original_transaction.reference',
        read_only=True
    )
    refund_transaction_reference = serializers.CharField(
        source='refund_transaction.reference',
        read_only=True,
        allow_null=True
    )
    initiated_by_name = serializers.CharField(
        source='initiated_by.get_full_name',
        read_only=True,
        allow_null=True
    )
    approved_by_name = serializers.CharField(
        source='approved_by.get_full_name',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Refund
        fields = [
            'id', 'reference', 'original_transaction', 'original_transaction_reference',
            'refund_transaction', 'refund_transaction_reference', 'amount', 'reason',
            'reason_details', 'status', 'status_message', 'gateway_reference',
            'initiated_by', 'initiated_by_name', 'requires_approval',
            'approved_by', 'approved_by_name', 'approved_at', 'created_at',
            'processed_at', 'completed_at', 'is_successful', 'is_partial'
        ]
        read_only_fields = [
            'id', 'reference', 'refund_transaction', 'status', 'status_message',
            'gateway_reference', 'approved_at', 'created_at', 'processed_at',
            'completed_at', 'is_successful', 'is_partial'
        ]


class RefundRequestSerializer(serializers.Serializer):
    """Serializer for refund request"""
    
    transaction_reference = serializers.CharField(max_length=100)
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    reason = serializers.ChoiceField(choices=Refund.REASON_CHOICES)
    reason_details = serializers.CharField(required=False, allow_blank=True)
    requires_approval = serializers.BooleanField(default=False)
    
    def validate_transaction_reference(self, value):
        """Validate transaction exists and can be refunded"""
        try:
            transaction = Transaction.objects.get(reference=value)
            if not transaction.can_be_refunded:
                raise serializers.ValidationError("Transaction cannot be refunded")
        except Transaction.DoesNotExist:
            raise serializers.ValidationError(f"Transaction '{value}' not found")
        return value


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for Wallet model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    currency_details = CurrencySerializer(source='currency', read_only=True)
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user', 'user_name', 'balance', 'currency', 'currency_details',
            'daily_limit', 'transaction_limit', 'status', 'is_locked',
            'lock_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'balance', 'created_at', 'updated_at']


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for WalletTransaction model"""
    
    wallet_user = serializers.CharField(source='wallet.user.get_full_name', read_only=True)
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'wallet', 'wallet_user', 'transaction_type', 'amount',
            'balance_before', 'balance_after', 'related_transaction',
            'description', 'reference', 'metadata', 'created_at'
        ]
        read_only_fields = [
            'id', 'balance_before', 'balance_after', 'reference', 'created_at'
        ]


class PaymentSessionSerializer(serializers.ModelSerializer):
    """Serializer for PaymentSession model"""
    
    transaction_reference = serializers.CharField(
        source='transaction.reference',
        read_only=True,
        allow_null=True
    )
    currency_details = CurrencySerializer(source='currency', read_only=True)
    gateway_details = PaymentGatewaySerializer(source='gateway', read_only=True)
    
    class Meta:
        model = PaymentSession
        fields = [
            'id', 'session_key', 'user', 'amount', 'currency', 'currency_details',
            'description', 'transaction', 'transaction_reference', 'gateway',
            'gateway_details', 'gateway_session_id', 'success_url', 'cancel_url',
            'webhook_url', 'status', 'metadata', 'created_at', 'expires_at',
            'completed_at'
        ]
        read_only_fields = [
            'id', 'session_key', 'gateway_session_id', 'status', 'created_at',
            'expires_at', 'completed_at'
        ]


class PaymentWebhookSerializer(serializers.ModelSerializer):
    """Serializer for PaymentWebhook model"""
    
    gateway_name = serializers.CharField(source='gateway.display_name', read_only=True)
    transaction_reference = serializers.CharField(
        source='transaction.reference',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = PaymentWebhook
        fields = [
            'id', 'gateway', 'gateway_name', 'event_type', 'event_id',
            'payload', 'signature', 'is_verified', 'status',
            'processing_attempts', 'error_message', 'transaction',
            'transaction_reference', 'received_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'is_verified', 'status', 'processing_attempts',
            'error_message', 'received_at', 'processed_at'
        ]

# =====================================================
# EXPENSE MANAGEMENT SERIALIZERS
# =====================================================

from .models import (
    ExpenseCategory,
    ExpenseRecipient,
    Expense,
    AccountBalance,
    ExpenseAuditLog,
    BudgetAllocation,
)


class ExpenseCategorySerializer(serializers.ModelSerializer):
    """Serializer for ExpenseCategory model"""
    
    expense_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    
    class Meta:
        model = ExpenseCategory
        fields = [
            'id', 'name', 'description', 'icon', 'color',
            'is_active', 'budget_limit', 'expense_count', 'total_spent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_expense_count(self, obj):
        return obj.expenses.count()
    
    def get_total_spent(self, obj):
        from django.db.models import Sum
        total = obj.expenses.filter(status='paid').aggregate(
            total=Sum('amount')
        )['total'] or 0
        return float(total)


class ExpenseRecipientSerializer(serializers.ModelSerializer):
    """Serializer for ExpenseRecipient model"""
    
    expense_count = serializers.SerializerMethodField()
    total_received = serializers.SerializerMethodField()
    
    class Meta:
        model = ExpenseRecipient
        fields = [
            'id', 'name', 'phone', 'email', 'account_number', 'bank_name',
            'momo_number', 'momo_provider', 'address', 'is_vendor',
            'is_active', 'notes', 'expense_count', 'total_received',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_expense_count(self, obj):
        return obj.expenses.count()
    
    def get_total_received(self, obj):
        from django.db.models import Sum
        total = obj.expenses.filter(status='paid').aggregate(
            total=Sum('amount')
        )['total'] or 0
        return float(total)


class ExpenseRecipientMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for ExpenseRecipient (for dropdown/select)"""
    
    class Meta:
        model = ExpenseRecipient
        fields = ['id', 'name', 'is_vendor']


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for Expense model"""
    
    category_details = ExpenseCategorySerializer(source='category', read_only=True)
    recipient_details = ExpenseRecipientSerializer(source='recipient', read_only=True)
    currency_details = CurrencySerializer(source='currency', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True, allow_null=True)
    recipient_display = serializers.CharField(source='recipient_display_name', read_only=True)
    formatted_amount = serializers.CharField(read_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'reference', 'title', 'description', 'category', 'category_details',
            'amount', 'currency', 'currency_details', 'formatted_amount',
            'recipient', 'recipient_details', 'recipient_name', 'recipient_details',
            'recipient_display', 'payment_method', 'payment_reference', 'payment_date',
            'status', 'priority', 'created_by', 'created_by_name',
            'approved_by', 'approved_by_name', 'approved_at',
            'receipt_image', 'receipt_url', 'attachments', 'event_name',
            'sms_notification_sent', 'notes', 'rejection_reason',
            'expense_date', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reference', 'created_at', 'updated_at',
            'sms_notification_sent', 'approved_at'
        ]
    
    def create(self, validated_data):
        # Set created_by from request user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class ExpenseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating expenses (simplified)"""
    
    class Meta:
        model = Expense
        fields = [
            'title', 'description', 'category', 'amount', 'currency',
            'recipient', 'recipient_name', 'recipient_details',
            'payment_method', 'payment_reference', 'payment_date',
            'priority', 'receipt_image', 'receipt_url', 'attachments',
            'event_name', 'notes', 'expense_date'
        ]
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class ExpenseUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating expenses"""
    
    class Meta:
        model = Expense
        fields = [
            'title', 'description', 'category', 'amount',
            'recipient', 'recipient_name', 'recipient_details',
            'payment_method', 'payment_reference', 'payment_date',
            'priority', 'receipt_image', 'receipt_url', 'attachments',
            'event_name', 'notes', 'expense_date', 'status', 'rejection_reason'
        ]


class ExpenseApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting expenses"""
    
    action = serializers.ChoiceField(choices=['approve', 'reject', 'paid', 'cancel'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    payment_reference = serializers.CharField(required=False, allow_blank=True)
    payment_date = serializers.DateField(required=False)
    
    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting an expense'
            })
        return data


class ExpenseAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for ExpenseAuditLog model"""
    
    expense_reference = serializers.CharField(source='expense.reference', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True)
    
    class Meta:
        model = ExpenseAuditLog
        fields = [
            'id', 'expense', 'expense_reference', 'action',
            'performed_by', 'performed_by_name', 'previous_values',
            'new_values', 'comments', 'ip_address', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AccountBalanceSerializer(serializers.ModelSerializer):
    """Serializer for AccountBalance model"""
    
    current_balance = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    currency_details = CurrencySerializer(source='currency', read_only=True)
    
    class Meta:
        model = AccountBalance
        fields = [
            'id', 'total_income', 'total_expenditure', 'initial_balance',
            'current_balance', 'currency', 'currency_details',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_income', 'total_expenditure', 'current_balance',
            'created_at', 'updated_at'
        ]


class FinancialSummarySerializer(serializers.Serializer):
    """Serializer for financial summary data"""
    
    initial_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_income = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_expenditure = serializers.DecimalField(max_digits=15, decimal_places=2)
    current_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency = serializers.CharField()
    
    # Additional stats
    pending_expenses_count = serializers.IntegerField()
    pending_expenses_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    this_month_expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    this_month_income = serializers.DecimalField(max_digits=15, decimal_places=2)


class BudgetAllocationSerializer(serializers.ModelSerializer):
    """Serializer for BudgetAllocation model"""
    
    category_details = ExpenseCategorySerializer(source='category', read_only=True)
    currency_details = CurrencySerializer(source='currency', read_only=True)
    spent_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    remaining_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    utilization_percentage = serializers.FloatField(read_only=True)
    is_over_budget = serializers.BooleanField(read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True
    )
    
    class Meta:
        model = BudgetAllocation
        fields = [
            'id', 'name', 'category', 'category_details', 'allocated_amount',
            'currency', 'currency_details', 'start_date', 'end_date',
            'is_active', 'spent_amount', 'remaining_amount',
            'utilization_percentage', 'is_over_budget',
            'created_by', 'created_by_name', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'spent_amount', 'remaining_amount', 'utilization_percentage',
            'is_over_budget', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class ExpenseAnalyticsSerializer(serializers.Serializer):
    """Serializer for expense analytics"""
    
    # Time period
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    
    # Summary
    total_expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    expense_count = serializers.IntegerField()
    average_expense = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # By category
    by_category = serializers.ListField(
        child=serializers.DictField()
    )
    
    # By payment method
    by_payment_method = serializers.ListField(
        child=serializers.DictField()
    )
    
    # By status
    by_status = serializers.DictField()
    
    # Trend data (for charts)
    daily_trend = serializers.ListField(
        child=serializers.DictField()
    )
    monthly_trend = serializers.ListField(
        child=serializers.DictField()
    )
    
    # Top recipients
    top_recipients = serializers.ListField(
        child=serializers.DictField()
    )