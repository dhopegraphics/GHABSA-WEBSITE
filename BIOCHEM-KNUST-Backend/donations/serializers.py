"""
Donation Serializers
API serializers for donation system
"""
from rest_framework import serializers
from decimal import Decimal

from .models import (
    DonationWallet,
    Donation,
    DonorProfile,
    DonationWithdrawal,
    DonationTransaction
)


class DonationWalletSerializer(serializers.ModelSerializer):
    """Serializer for the donation wallet - public stats"""
    
    class Meta:
        model = DonationWallet
        fields = [
            'balance',
            'total_received',
            'total_withdrawn',
            'total_donations_count',
            'total_donors_count',
            'updated_at'
        ]
        read_only_fields = fields


class DonationInitializeSerializer(serializers.Serializer):
    """Serializer for initializing a donation"""
    
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('1.00'),
        help_text="Donation amount in GHS (minimum GH₵1.00)"
    )
    email = serializers.EmailField(
        help_text="Donor's email address"
    )
    donor_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Name to display (optional)"
    )
    phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="Donor's phone number (optional)"
    )
    message = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Optional message with donation"
    )
    is_anonymous = serializers.BooleanField(
        default=False,
        help_text="Hide donor identity publicly"
    )
    callback_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="URL to redirect after payment"
    )


class DonationPublicSerializer(serializers.ModelSerializer):
    """Serializer for public donation display"""
    
    display_name = serializers.SerializerMethodField()
    display_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Donation
        fields = [
            'id',
            'display_name',
            'display_amount',
            'message',
            'is_anonymous',
            'completed_at',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_display_name(self, obj):
        """Get the public display name"""
        return obj.get_display_name()
    
    def get_display_amount(self, obj):
        """Get the public display amount"""
        amount = obj.get_display_amount()
        return float(amount) if amount else None


class DonationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for donation - authenticated users viewing their own"""
    
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Donation
        fields = [
            'id',
            'reference',
            'donor_name',
            'donor_email',
            'amount',
            'message',
            'is_anonymous',
            'status',
            'display_name',
            'completed_at',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_display_name(self, obj):
        return obj.get_display_name()


class DonationAdminSerializer(serializers.ModelSerializer):
    """Full serializer for admin view"""
    
    donor_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Donation
        fields = [
            'id',
            'reference',
            'donor',
            'donor_info',
            'donor_name',
            'donor_email',
            'donor_phone',
            'amount',
            'message',
            'is_anonymous',
            'status',
            'gateway',
            'gateway_reference',
            'ip_address',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_donor_info(self, obj):
        if obj.donor:
            return {
                'id': str(obj.donor.id),
                'name': f"{obj.donor.first_name} {obj.donor.last_name}",
                'email': obj.donor.student_email or obj.donor.personal_email,
                'phone': obj.donor.phone,
            }
        return None


class DonorProfileSerializer(serializers.ModelSerializer):
    """Serializer for donor profile"""
    
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DonorProfile
        fields = [
            'id',
            'user_name',
            'total_donated',
            'donation_count',
            'first_donation_at',
            'last_donation_at',
        ]
        read_only_fields = fields
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


class WithdrawalCreateSerializer(serializers.Serializer):
    """Serializer for creating a withdrawal"""
    
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('1.00'),
        help_text="Withdrawal amount"
    )
    recipient_name = serializers.CharField(
        max_length=255,
        help_text="Name of recipient/vendor"
    )
    recipient_account = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Account number or mobile money number"
    )
    recipient_bank = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Bank name or mobile money provider"
    )
    purpose = serializers.CharField(
        max_length=500,
        help_text="What is this withdrawal for?"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Detailed description"
    )
    category = serializers.ChoiceField(
        choices=DonationWithdrawal.CATEGORY_CHOICES,
        default='other',
        help_text="Category of expense"
    )


class DonationWithdrawalPublicSerializer(serializers.ModelSerializer):
    """Serializer for public withdrawal display"""
    
    initiated_by_name = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()
    
    class Meta:
        model = DonationWithdrawal
        fields = [
            'id',
            'reference',
            'amount',
            'recipient_name',
            'purpose',
            'description',
            'category',
            'category_display',
            'initiated_by_name',
            'receipt_image',
            'completed_at',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_initiated_by_name(self, obj):
        return f"{obj.initiated_by.first_name} {obj.initiated_by.last_name}"
    
    def get_category_display(self, obj):
        return obj.get_category_display()


class DonationWithdrawalAdminSerializer(serializers.ModelSerializer):
    """Full serializer for admin withdrawal view"""
    
    initiated_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = DonationWithdrawal
        fields = [
            'id',
            'reference',
            'amount',
            'recipient_name',
            'recipient_account',
            'recipient_bank',
            'purpose',
            'description',
            'category',
            'category_display',
            'receipt_image',
            'initiated_by',
            'initiated_by_name',
            'approved_by',
            'approved_by_name',
            'status',
            'status_display',
            'status_message',
            'balance_before',
            'balance_after',
            'approved_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_initiated_by_name(self, obj):
        return f"{obj.initiated_by.first_name} {obj.initiated_by.last_name}"
    
    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return f"{obj.approved_by.first_name} {obj.approved_by.last_name}"
        return None
    
    def get_category_display(self, obj):
        return obj.get_category_display()
    
    def get_status_display(self, obj):
        return obj.get_status_display()


class DonationTransactionSerializer(serializers.ModelSerializer):
    """Serializer for donation transactions"""
    
    type_display = serializers.SerializerMethodField()
    performed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DonationTransaction
        fields = [
            'id',
            'transaction_type',
            'type_display',
            'amount',
            'donation',
            'withdrawal',
            'balance_before',
            'balance_after',
            'description',
            'performed_by_name',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_type_display(self, obj):
        return obj.get_transaction_type_display()
    
    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return f"{obj.performed_by.first_name} {obj.performed_by.last_name}"
        return None


class DonationStatsSerializer(serializers.Serializer):
    """Serializer for public donation statistics"""
    
    total_balance = serializers.FloatField()
    total_received = serializers.FloatField()
    total_withdrawn = serializers.FloatField()
    total_donations = serializers.IntegerField()
    total_donors = serializers.IntegerField()


class TopDonorSerializer(serializers.Serializer):
    """Serializer for top donors"""
    
    name = serializers.CharField()
    total_donated = serializers.FloatField()
    donation_count = serializers.IntegerField()
    is_anonymous = serializers.BooleanField(default=False)
