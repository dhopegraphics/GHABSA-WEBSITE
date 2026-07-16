"""
Donation Views
API endpoints for public donation system
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth

from .models import (
    DonationWallet,
    Donation,
    DonorProfile,
    DonationWithdrawal,
    DonationTransaction
)
from .serializers import (
    DonationWalletSerializer,
    DonationInitializeSerializer,
    DonationPublicSerializer,
    DonationDetailSerializer,
    DonationAdminSerializer,
    DonorProfileSerializer,
    WithdrawalCreateSerializer,
    DonationWithdrawalPublicSerializer,
    DonationWithdrawalAdminSerializer,
    DonationTransactionSerializer,
    DonationStatsSerializer,
    TopDonorSerializer
)
from .services import DonationService


class IsAdminUser(permissions.BasePermission):
    """Permission for admin users only"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or 
            request.user.is_superuser or
            getattr(request.user, 'is_executive', False)
        )


class PublicDonationView(APIView):
    """
    Public endpoint for donation page data
    No authentication required
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """
        Get all public donation data:
        - Wallet statistics
        - Recent donations
        - Recent withdrawals
        - Top donors
        """
        # Get wallet stats
        wallet = DonationWallet.get_wallet()
        wallet_data = DonationWalletSerializer(wallet).data
        
        # Get recent donations (public display)
        recent_donations = DonationService.get_recent_donations(limit=20)
        donations_data = DonationPublicSerializer(recent_donations, many=True).data
        
        # Get recent withdrawals (public display)
        recent_withdrawals = DonationService.get_recent_withdrawals(limit=20)
        withdrawals_data = DonationWithdrawalPublicSerializer(recent_withdrawals, many=True).data
        
        # Get top public donors (non-anonymous)
        top_donors = self._get_top_donors()
        
        # Monthly donation stats for chart
        monthly_stats = self._get_monthly_stats()
        
        return Response({
            'wallet': wallet_data,
            'recent_donations': donations_data,
            'recent_withdrawals': withdrawals_data,
            'top_donors': top_donors,
            'monthly_stats': monthly_stats,
        })
    
    def _get_top_donors(self, limit=10):
        """Get top donors who are not anonymous"""
        # Get from donor profiles (registered users)
        top_profiles = DonorProfile.objects.select_related('user').order_by(
            '-total_donated'
        )[:limit]
        
        result = []
        for profile in top_profiles:
            # Check if user has any non-anonymous donations
            has_public_donation = Donation.objects.filter(
                donor=profile.user,
                status='completed',
                is_anonymous=False
            ).exists()
            
            if has_public_donation:
                result.append({
                    'name': f"{profile.user.first_name} {profile.user.last_name}",
                    'total_donated': float(profile.total_donated),
                    'donation_count': profile.donation_count,
                    'is_anonymous': False
                })
        
        return result
    
    def _get_monthly_stats(self, months=12):
        """Get donation statistics by month"""
        from django.utils import timezone
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=365)
        
        monthly = Donation.objects.filter(
            status='completed',
            completed_at__gte=start_date
        ).annotate(
            month=TruncMonth('completed_at')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('month')
        
        return [
            {
                'month': item['month'].strftime('%Y-%m') if item['month'] else '',
                'total': float(item['total']) if item['total'] else 0,
                'count': item['count']
            }
            for item in monthly
        ]


class DonationInitializeView(APIView):
    """
    Initialize a new donation payment
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Initialize a donation"""
        serializer = DonationInitializeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'success': False, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        # Get donor if authenticated
        donor = request.user if request.user.is_authenticated else None
        
        # Get IP and user agent
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Initialize donation
        result = DonationService.initialize_donation(
            amount=data['amount'],
            email=data['email'],
            donor_name=data.get('donor_name', ''),
            phone=data.get('phone', ''),
            message=data.get('message', ''),
            is_anonymous=data.get('is_anonymous', False),
            donor=donor,
            callback_url=data.get('callback_url'),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if result['success']:
            return Response({
                'success': True,
                'authorization_url': result['authorization_url'],
                'reference': result['reference'],
                'access_code': result.get('access_code', ''),
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Failed to initialize donation')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class DonationVerifyView(APIView):
    """
    Verify a donation payment
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, reference):
        """Verify donation by reference"""
        result = DonationService.verify_donation(reference)
        
        if result['success']:
            donation = result['donation']
            return Response({
                'success': True,
                'message': result.get('message', 'Donation verified'),
                'donation': {
                    'reference': donation.reference,
                    'amount': float(donation.amount),
                    'donor_name': donation.get_display_name(),
                    'status': donation.status,
                    'completed_at': donation.completed_at,
                }
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Verification failed')
            }, status=status.HTTP_400_BAD_REQUEST)


class DonationWebhookView(APIView):
    """
    DEPRECATED: This endpoint redirects to the unified webhook handler.
    
    Please update your Paystack webhook URL to:
   https://cssknust.pythonanywhere.com/payments/webhooks/paystack/
    
    This endpoint is kept for backwards compatibility only.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Redirect to unified webhook handler"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.warning(
            "DEPRECATED: Webhook received on /donations/webhook/ - "
            "Please update Paystack webhook URL to /payments/webhooks/paystack/"
        )
        
        # Forward to the unified payment webhook handler
        from payments.webhooks import PaystackWebhookView
        return PaystackWebhookView().post(request)


class DonationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for donations
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return DonationAdminSerializer
        return DonationDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin can see all
        if user.is_staff or user.is_superuser:
            return Donation.objects.all()
        
        # Regular users see only their own
        return Donation.objects.filter(donor=user)
    
    @action(detail=False, methods=['get'])
    def my_donations(self, request):
        """Get current user's donations"""
        donations = Donation.objects.filter(donor=request.user).order_by('-created_at')
        serializer = DonationDetailSerializer(donations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get current user's donor profile"""
        try:
            profile = DonorProfile.objects.get(user=request.user)
            serializer = DonorProfileSerializer(profile)
            return Response(serializer.data)
        except DonorProfile.DoesNotExist:
            return Response({
                'total_donated': 0,
                'donation_count': 0,
                'first_donation_at': None,
                'last_donation_at': None
            })


class WithdrawalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for donation withdrawals (admin only for write operations)
    """
    serializer_class = DonationWithdrawalPublicSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [permissions.AllowAny()]
    
    def get_serializer_class(self):
        if self.request.user.is_authenticated and (
            self.request.user.is_staff or self.request.user.is_superuser
        ):
            return DonationWithdrawalAdminSerializer
        return DonationWithdrawalPublicSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Public can only see completed withdrawals
        if not user.is_authenticated or not (user.is_staff or user.is_superuser):
            return DonationWithdrawal.objects.filter(status='completed')
        
        # Admin sees all
        return DonationWithdrawal.objects.all()
    
    def create(self, request, *args, **kwargs):
        """Create a new withdrawal (admin only)"""
        serializer = WithdrawalCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'success': False, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        result = DonationService.process_withdrawal(
            amount=data['amount'],
            recipient_name=data['recipient_name'],
            purpose=data['purpose'],
            initiated_by=request.user,
            recipient_account=data.get('recipient_account', ''),
            recipient_bank=data.get('recipient_bank', ''),
            description=data.get('description', ''),
            category=data.get('category', 'other'),
            receipt_image=request.FILES.get('receipt_image'),
        )
        
        if result['success']:
            withdrawal = result['withdrawal']
            return Response({
                'success': True,
                'message': 'Withdrawal processed successfully',
                'withdrawal': DonationWithdrawalAdminSerializer(withdrawal).data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Failed to process withdrawal')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def upload_receipt(self, request, pk=None):
        """Upload receipt for a withdrawal"""
        withdrawal = self.get_object()
        
        receipt = request.FILES.get('receipt_image')
        if not receipt:
            return Response(
                {'error': 'No receipt file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        withdrawal.receipt_image = receipt
        withdrawal.save()
        
        return Response({
            'success': True,
            'message': 'Receipt uploaded successfully',
            'receipt_url': withdrawal.receipt_image.url if withdrawal.receipt_image else None
        })


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for donation transactions (audit log)
    """
    serializer_class = DonationTransactionSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return DonationTransaction.objects.all()


class AdminDonationStatsView(APIView):
    """
    Admin-only detailed statistics
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Get detailed admin statistics"""
        wallet = DonationWallet.get_wallet()
        
        # Donation stats by status
        status_stats = Donation.objects.values('status').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        # Withdrawal stats by category
        category_stats = DonationWithdrawal.objects.filter(
            status='completed'
        ).values('category').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        # Recent transactions
        recent_transactions = DonationTransaction.objects.order_by('-created_at')[:50]
        
        return Response({
            'wallet': DonationWalletSerializer(wallet).data,
            'donation_status_stats': list(status_stats),
            'withdrawal_category_stats': list(category_stats),
            'recent_transactions': DonationTransactionSerializer(
                recent_transactions, many=True
            ).data,
        })
