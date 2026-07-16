"""
Payment System API Views
"""
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.db import transaction as db_transaction
from django.db import models
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.conf import settings
from datetime import datetime, timedelta

from .models import (
    Transaction,
    Refund,
    Wallet,
    WalletTransaction,
    PaymentGateway,
    Currency,
    Expense,
    ExpenseCategory,
    ExpenseRecipient,
    AccountBalance,
    ExpenseAuditLog,
    BudgetAllocation,
)
from .serializers import (
    TransactionSerializer,
    PaymentInitializationSerializer,
    PaymentVerificationSerializer,
    RefundSerializer,
    RefundRequestSerializer,
    WalletSerializer,
    WalletTransactionSerializer,
    PaymentGatewaySerializer,
    CurrencySerializer,
)
from .services.transaction_service import TransactionService
from .services.refund_service import RefundService
from products.payment_service import ProductPaymentService
import logging

logger = logging.getLogger(__name__)


# ============================================
# EXPENSE DASHBOARD VIEW (Staff Only)
# ============================================

@staff_member_required
def expense_dashboard(request):
    """
    Modern standalone expense dashboard for admins.
    Full HTML/CSS/JS with charts and analytics.
    """
    # Get balance information
    balance_info = AccountBalance.get_current_balance()
    
    # Current date
    current_date = datetime.now()
    today = current_date.date()
    first_day_of_month = today.replace(day=1)
    
    # This month's expenses
    month_expenses = Expense.objects.filter(expense_date__gte=first_day_of_month)
    month_stats = {
        'total': month_expenses.filter(status='paid').aggregate(
            total=Sum('amount'))['total'] or 0,
        'count': month_expenses.count(),
        'pending': month_expenses.filter(status='pending').count(),
        'approved': month_expenses.filter(status='approved').count(),
        'paid': month_expenses.filter(status='paid').count(),
    }
    
    # Category breakdown
    category_breakdown = Expense.objects.filter(
        status='paid'
    ).values(
        'category__name', 'category__icon', 'category__color'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')[:6]
    
    # Monthly trend (last 6 months)
    six_months_ago = today - timedelta(days=180)
    monthly_trend = Expense.objects.filter(
        status='paid',
        expense_date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('expense_date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    # Recent expenses
    recent_expenses = Expense.objects.select_related(
        'category', 'recipient', 'created_by'
    ).order_by('-created_at')[:10]
    
    # Top recipients
    top_recipients = Expense.objects.filter(
        status='paid'
    ).values('recipient__name').annotate(
        total=Sum('amount')
    ).order_by('-total')[:5]
    
    # Categories and recipients for the form
    categories = ExpenseCategory.objects.filter(is_active=True)
    recipients = ExpenseRecipient.objects.filter(is_active=True)
    
    context = {
        'balance_info': balance_info,
        'current_date': current_date,
        'month_stats': month_stats,
        'category_breakdown': list(category_breakdown),
        'monthly_trend': list(monthly_trend),
        'recent_expenses': recent_expenses,
        'top_recipients': list(top_recipients),
        'categories': categories,
        'recipients': recipients,
        'user': request.user,
        'active_page': 'dashboard',
    }
    
    return render(request, 'payments/dashboard/index.html', context)


# ============================================
# EXPENSE LIST VIEW
# ============================================

@staff_member_required
def expense_list_view(request):
    """Full page view for all expenses with filtering."""
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    
    expenses = Expense.objects.select_related('category', 'recipient').order_by('-expense_date', '-created_at')
    
    if search_query:
        expenses = expenses.filter(
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(reference__icontains=search_query)
        )
    
    if status_filter:
        expenses = expenses.filter(status=status_filter)
    
    if category_filter:
        expenses = expenses.filter(category_id=category_filter)
    
    # Stats
    all_expenses = Expense.objects.all()
    total_count = all_expenses.count()
    paid_count = all_expenses.filter(status='paid').count()
    pending_count = all_expenses.filter(status='pending').count()
    total_amount = all_expenses.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    
    # Pagination
    paginator = Paginator(expenses, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    categories = ExpenseCategory.objects.filter(is_active=True)
    
    context = {
        'expenses': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'paid_count': paid_count,
        'pending_count': pending_count,
        'total_amount': total_amount,
        'categories': categories,
        'search_query': search_query,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'user': request.user,
        'active_page': 'expenses',
    }
    return render(request, 'payments/dashboard/expenses.html', context)


# ============================================
# EXPENSE ADD VIEW
# ============================================

@staff_member_required
def expense_add_view(request):
    """Add new expense."""
    import uuid
    from datetime import date
    
    if request.method == 'POST':
        try:
            with db_transaction.atomic():
                expense = Expense(
                    title=request.POST.get('title'),
                    description=request.POST.get('description', ''),
                    amount=request.POST.get('amount'),
                    category_id=request.POST.get('category'),
                    recipient_id=request.POST.get('recipient') or None,
                    recipient_name=request.POST.get('recipient_name', ''),
                    expense_date=request.POST.get('expense_date'),
                    status=request.POST.get('status', 'pending'),
                    created_by=request.user,
                )
                
                if 'receipt' in request.FILES:
                    expense.receipt = request.FILES['receipt']
                
                expense.save()
                
                # Create audit log for the new expense
                ExpenseAuditLog.objects.create(
                    expense=expense,
                    action='created',
                    performed_by=request.user,
                    new_values={
                        'title': expense.title,
                        'amount': str(expense.amount),
                        'status': expense.status,
                        'category': str(expense.category_id) if expense.category_id else None,
                    },
                    comments=f'Expense created via dashboard',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                )
                
                # Send SMS if checkbox checked and status is paid
                if request.POST.get('send_sms') and expense.status == 'paid':
                    expense.send_expense_notification_to_executives()
                
                messages.success(request, f'Expense "{expense.title}" created successfully!')
                return redirect('payments:dashboard-expense-list')
                
        except Exception as e:
            messages.error(request, f'Error creating expense: {str(e)}')
    
    categories = ExpenseCategory.objects.filter(is_active=True)
    recipients = ExpenseRecipient.objects.filter(is_active=True)
    balance = AccountBalance.get_current_balance()
    
    context = {
        'categories': categories,
        'recipients': recipients,
        'current_balance': balance.get('current_balance', 0),
        'today': date.today().isoformat(),
        'user': request.user,
        'active_page': 'expenses',
    }
    return render(request, 'payments/dashboard/expense_form.html', context)


# ============================================
# EXPENSE EDIT VIEW
# ============================================

@staff_member_required
def expense_edit_view(request, pk):
    """Edit existing expense."""
    from datetime import date
    
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == 'POST':
        try:
            # Store old values for audit log
            old_values = {
                'title': expense.title,
                'amount': str(expense.amount),
                'status': expense.status,
                'category': str(expense.category_id) if expense.category_id else None,
                'description': expense.description,
            }
            old_status = expense.status
            
            expense.title = request.POST.get('title')
            expense.description = request.POST.get('description', '')
            expense.amount = request.POST.get('amount')
            expense.category_id = request.POST.get('category')
            expense.recipient_id = request.POST.get('recipient') or None
            expense.recipient_name = request.POST.get('recipient_name', '')
            expense.expense_date = request.POST.get('expense_date')
            expense.status = request.POST.get('status')
            
            if 'receipt' in request.FILES:
                expense.receipt = request.FILES['receipt']
            
            expense.save()
            
            # Determine action type based on status change
            if old_status != expense.status:
                if expense.status == 'paid':
                    action = 'paid'
                elif expense.status == 'approved':
                    action = 'approved'
                elif expense.status == 'rejected':
                    action = 'rejected'
                elif expense.status == 'cancelled':
                    action = 'cancelled'
                else:
                    action = 'updated'
            else:
                action = 'updated'
            
            # Create audit log for the update
            ExpenseAuditLog.objects.create(
                expense=expense,
                action=action,
                performed_by=request.user,
                previous_values=old_values,
                new_values={
                    'title': expense.title,
                    'amount': str(expense.amount),
                    'status': expense.status,
                    'category': str(expense.category_id) if expense.category_id else None,
                    'description': expense.description,
                },
                comments=f'Expense {action} via dashboard',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            )
            
            # Send SMS if status changed to paid
            if old_status != 'paid' and expense.status == 'paid' and request.POST.get('send_sms'):
                expense.send_expense_notification_to_executives()
            
            messages.success(request, f'Expense "{expense.title}" updated successfully!')
            return redirect('payments:dashboard-expense-list')
            
        except Exception as e:
            messages.error(request, f'Error updating expense: {str(e)}')
    
    categories = ExpenseCategory.objects.filter(is_active=True)
    recipients = ExpenseRecipient.objects.filter(is_active=True)
    balance = AccountBalance.get_current_balance()
    
    context = {
        'expense': expense,
        'categories': categories,
        'recipients': recipients,
        'current_balance': balance.get('current_balance', 0),
        'today': date.today().isoformat(),
        'user': request.user,
        'active_page': 'expenses',
    }
    return render(request, 'payments/dashboard/expense_form.html', context)


# ============================================
# EXPENSE DELETE VIEW
# ============================================

@staff_member_required
def expense_delete_view(request, pk):
    """Delete expense."""
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == 'POST':
        title = expense.title
        reference = expense.reference
        
        # Create audit log before deleting (we'll keep the log even after expense is deleted)
        ExpenseAuditLog.objects.create(
            expense=expense,
            action='deleted',
            performed_by=request.user,
            previous_values={
                'title': expense.title,
                'reference': expense.reference,
                'amount': str(expense.amount),
                'status': expense.status,
            },
            comments=f'Expense "{title}" ({reference}) deleted via dashboard',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )
        
        expense.delete()
        messages.success(request, f'Expense "{title}" deleted successfully!')
        return redirect('payments:dashboard-expense-list')
    
    return redirect('payments:dashboard-expense-list')


# ============================================
# CATEGORIES VIEW
# ============================================

@staff_member_required
def expense_categories_view(request):
    """Full page view for expense categories."""
    categories = ExpenseCategory.objects.annotate(
        expense_count=Count('expenses'),
        total_spent=Sum('expenses__amount', filter=models.Q(expenses__status='paid'))
    )
    
    active_count = categories.filter(is_active=True).count()
    total_budgeted = categories.aggregate(total=Sum('budget_limit'))['total'] or 0
    
    # Find most used category
    most_used = categories.order_by('-expense_count').first()
    
    context = {
        'categories': categories,
        'active_count': active_count,
        'total_budgeted': total_budgeted,
        'most_used': most_used.name if most_used else '-',
        'user': request.user,
        'active_page': 'categories',
    }
    return render(request, 'payments/dashboard/categories.html', context)


# ============================================
# CATEGORY ADD/EDIT VIEW
# ============================================

@staff_member_required
def category_add_view(request):
    """Add or edit category."""
    edit_id = request.GET.get('edit')
    
    if request.method == 'POST':
        try:
            if edit_id:
                category = get_object_or_404(ExpenseCategory, pk=edit_id)
            else:
                category = ExpenseCategory()
            
            category.name = request.POST.get('name')
            category.icon = request.POST.get('icon', '📁')
            category.color = request.POST.get('color', '#6366f1')
            category.description = request.POST.get('description', '')
            category.budget_limit = request.POST.get('budget_amount') or None
            category.is_active = bool(request.POST.get('is_active'))
            category.save()
            
            messages.success(request, f'Category "{category.name}" saved successfully!')
            
        except Exception as e:
            messages.error(request, f'Error saving category: {str(e)}')
    
    return redirect('payments:expense-categories')


# ============================================
# RECIPIENTS VIEW
# ============================================

@staff_member_required
def expense_recipients_view(request):
    """Full page view for expense recipients."""
    search_query = request.GET.get('q', '')
    type_filter = request.GET.get('type', '')
    
    recipients = ExpenseRecipient.objects.annotate(
        expense_count=Count('expenses'),
        total_received=Sum('expenses__amount', filter=models.Q(expenses__status='paid'))
    )
    
    if search_query:
        recipients = recipients.filter(
            models.Q(name__icontains=search_query) |
            models.Q(email__icontains=search_query) |
            models.Q(phone__icontains=search_query)
        )
    
    if type_filter == 'vendor':
        recipients = recipients.filter(is_vendor=True)
    elif type_filter == 'individual':
        recipients = recipients.filter(is_vendor=False)
    
    vendor_count = recipients.filter(is_vendor=True).count()
    individual_count = recipients.filter(is_vendor=False).count()
    active_count = recipients.filter(is_active=True).count()
    
    context = {
        'recipients': recipients,
        'vendor_count': vendor_count,
        'individual_count': individual_count,
        'active_count': active_count,
        'search_query': search_query,
        'type_filter': type_filter,
        'user': request.user,
        'active_page': 'recipients',
    }
    return render(request, 'payments/dashboard/recipients.html', context)


# ============================================
# RECIPIENT ADD/EDIT VIEW
# ============================================

@staff_member_required
def recipient_add_view(request):
    """Add or edit recipient."""
    edit_id = request.GET.get('edit')
    
    if request.method == 'POST':
        try:
            if edit_id:
                recipient = get_object_or_404(ExpenseRecipient, pk=edit_id)
            else:
                recipient = ExpenseRecipient()
            
            recipient.name = request.POST.get('name')
            recipient.email = request.POST.get('email', '')
            recipient.phone = request.POST.get('phone', '')
            recipient.bank_name = request.POST.get('bank_name', '')
            recipient.account_number = request.POST.get('account_number', '')
            recipient.momo_number = request.POST.get('momo_number', '')
            recipient.momo_provider = request.POST.get('momo_provider', '')
            recipient.is_vendor = bool(request.POST.get('is_vendor'))
            recipient.is_active = bool(request.POST.get('is_active'))
            recipient.notes = request.POST.get('notes', '')
            recipient.save()
            
            messages.success(request, f'Recipient "{recipient.name}" saved successfully!')
            
        except Exception as e:
            messages.error(request, f'Error saving recipient: {str(e)}')
    
    return redirect('payments:expense-recipients')


# ============================================
# BUDGET VIEW
# ============================================

@staff_member_required
def expense_budget_view(request):
    """Full page view for budget allocations."""
    budgets = BudgetAllocation.objects.select_related('category').annotate(
        spent_amount=Sum(
            'category__expenses__amount',
            filter=models.Q(
                category__expenses__status='paid',
                category__expenses__expense_date__gte=models.F('start_date'),
                category__expenses__expense_date__lte=models.F('end_date')
            )
        )
    )
    
    for budget in budgets:
        budget.remaining_amount = budget.allocated_amount - (budget.spent_amount or 0)
    
    total_allocated = budgets.aggregate(total=Sum('allocated_amount'))['total'] or 0
    total_spent = sum((b.spent_amount or 0) for b in budgets)
    total_remaining = total_allocated - total_spent
    utilization_rate = (total_spent / total_allocated * 100) if total_allocated else 0
    
    categories = ExpenseCategory.objects.filter(is_active=True)
    
    context = {
        'budgets': budgets,
        'total_allocated': total_allocated,
        'total_spent': total_spent,
        'total_remaining': total_remaining,
        'utilization_rate': utilization_rate,
        'categories': categories,
        'user': request.user,
        'active_page': 'budget',
    }
    return render(request, 'payments/dashboard/budget.html', context)


# ============================================
# BUDGET ADD/EDIT VIEW
# ============================================

@staff_member_required
def budget_add_view(request):
    """Add or edit budget allocation."""
    edit_id = request.GET.get('edit')
    
    if request.method == 'POST':
        try:
            if edit_id:
                budget = get_object_or_404(BudgetAllocation, pk=edit_id)
            else:
                budget = BudgetAllocation()
            
            budget.category_id = request.POST.get('category')
            budget.allocated_amount = request.POST.get('allocated_amount')
            budget.start_date = request.POST.get('start_date')
            budget.end_date = request.POST.get('end_date')
            budget.notes = request.POST.get('notes', '')
            budget.is_active = bool(request.POST.get('is_active'))
            budget.save()
            
            messages.success(request, 'Budget allocation saved successfully!')
            
        except Exception as e:
            messages.error(request, f'Error saving budget: {str(e)}')
    
    return redirect('payments:expense-budget')


# ============================================
# AUDIT LOG VIEW
# ============================================

@staff_member_required
def expense_audit_view(request):
    """Full page view for expense audit logs."""
    search_query = request.GET.get('q', '')
    action_filter = request.GET.get('action', '')
    date_filter = request.GET.get('date', '')
    
    logs = ExpenseAuditLog.objects.select_related('expense', 'performed_by').order_by('-created_at')
    
    if search_query:
        logs = logs.filter(
            models.Q(expense__title__icontains=search_query) |
            models.Q(expense__reference__icontains=search_query)
        )
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if date_filter:
        logs = logs.filter(created_at__date=date_filter)
    
    # Stats
    total_logs = logs.count()
    created_count = logs.filter(action='created').count()
    updated_count = logs.filter(action='updated').count()
    status_changes = logs.filter(action='status_changed').count()
    
    # Export functionality
    if request.GET.get('export') == 'csv':
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_log.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Time', 'Action', 'Expense', 'Amount', 'User', 'Details'])
        for log in logs[:1000]:
            writer.writerow([
                log.created_at.strftime('%Y-%m-%d'),
                log.created_at.strftime('%H:%M:%S'),
                log.get_action_display(),
                log.expense.title if log.expense else 'N/A',
                log.expense.amount if log.expense else 'N/A',
                log.performed_by.get_full_name() if log.performed_by else 'System',
                log.comments or ''
            ])
        return response
    
    # Pagination
    paginator = Paginator(logs, 30)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'logs': page_obj,
        'page_obj': page_obj,
        'total_logs': total_logs,
        'created_count': created_count,
        'updated_count': updated_count,
        'status_changes': status_changes,
        'search_query': search_query,
        'action_filter': action_filter,
        'date_filter': date_filter,
        'user': request.user,
        'active_page': 'audit',
    }
    return render(request, 'payments/dashboard/audit.html', context)


# ============================================
# BALANCE VIEW
# ============================================

@staff_member_required
def expense_balance_view(request):
    """Full page view for account balance."""
    import json
    from datetime import date
    
    # Handle deposit action
    if request.method == 'POST' and request.POST.get('action') == 'deposit':
        try:
            balance_obj = AccountBalance.get_or_create_singleton()
            
            amount = Decimal(request.POST.get('amount', 0))
            balance_obj.initial_balance += amount
            balance_obj.save()
            
            messages.success(request, f'Deposit of GH₵ {amount:.2f} added successfully!')
            return redirect('payments:expense-balance')
            
        except Exception as e:
            messages.error(request, f'Error adding deposit: {str(e)}')
    
    # Get balance info using the model's method
    balance_info = AccountBalance.get_current_balance()
    balance_obj = AccountBalance.objects.first()
    current_balance = balance_info.get('current_balance', 0)
    total_deposits = balance_info.get('total_income', 0)
    total_withdrawals = balance_info.get('total_expenditure', 0)
    
    today = date.today()
    first_day_of_month = today.replace(day=1)
    
    # This month stats
    month_expenses = Expense.objects.filter(
        status='paid',
        expense_date__gte=first_day_of_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    month_deposits = 0  # Would need deposit tracking model
    net_flow = month_deposits - month_expenses
    
    # Get recent expenses as transactions
    recent_expenses = Expense.objects.filter(status='paid').order_by('-expense_date')[:20]
    transactions = []
    for exp in recent_expenses:
        transactions.append({
            'date': exp.expense_date,
            'description': exp.title,
            'reference': exp.reference,
            'type': 'expense',
            'amount': exp.amount,
            'balance_after': None,
        })
    
    total_transactions = len(transactions)
    
    # Chart data (placeholder - would need more sophisticated tracking)
    balance_dates = json.dumps([])
    balance_values = json.dumps([])
    monthly_labels = json.dumps(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'])
    monthly_deposits = json.dumps([0, 0, 0, 0, 0, 0])
    monthly_expenses = json.dumps([0, 0, 0, 0, 0, 0])
    
    context = {
        'balance_obj': balance_obj,
        'current_balance': current_balance,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'month_deposits': month_deposits,
        'month_expenses': month_expenses,
        'net_flow': net_flow,
        'total_transactions': total_transactions,
        'transactions': transactions,
        'balance_dates': balance_dates,
        'balance_values': balance_values,
        'monthly_labels': monthly_labels,
        'monthly_deposits': monthly_deposits,
        'monthly_expenses': monthly_expenses,
        'user': request.user,
        'active_page': 'balance',
    }
    return render(request, 'payments/dashboard/balance.html', context)


class PaymentGatewayViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing available payment gateways
    
    list: Get all active payment gateways
    retrieve: Get specific gateway details
    """
    queryset = PaymentGateway.objects.filter(is_active=True, status='active')
    serializer_class = PaymentGatewaySerializer
    permission_classes = [IsAuthenticated]


class CurrencyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing supported currencies
    
    list: Get all active currencies
    retrieve: Get specific currency details
    """
    queryset = Currency.objects.filter(is_active=True)
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated]


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing transactions
    
    list: Get user's transactions
    retrieve: Get specific transaction
    initialize_payment: Initialize a new payment
    verify_payment: Verify payment status
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter transactions by authenticated user"""
        user = self.request.user
        queryset = Transaction.objects.filter(user=user)
        
        # Filter by transaction type
        transaction_type = self.request.query_params.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Filter by status
        transaction_status = self.request.query_params.get('status')
        if transaction_status:
            queryset = queryset.filter(status=transaction_status)
        
        # Filter by gateway
        gateway = self.request.query_params.get('gateway')
        if gateway:
            queryset = queryset.filter(gateway__name=gateway)
        
        return queryset.select_related('currency', 'gateway', 'user').order_by('-initiated_at')
    
    @action(detail=False, methods=['post'])
    def initialize_payment(self, request):
        """
        Initialize a new payment
        
        POST /api/transactions/initialize_payment/
        
        Request body:
        {
            "amount": "100.00",
            "currency": "GHS",
            "description": "Payment for product X",
            "gateway": "paystack",
            "callback_url": "https://example.com/callback",
            "metadata": {"order_id": "123"}
        }
        
        Response:
        {
            "transaction": {...},
            "authorization_url": "https://...",
            "access_code": "...",
            "reference": "TXN-..."
        }
        """
        serializer = PaymentInitializationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        try:
            # Create transaction
            transaction = TransactionService.create_transaction(
                user=request.user,
                amount=data['amount'],
                currency_code=data['currency'],
                description=data['description'],
                transaction_type='payment',
                gateway_name=data['gateway'],
                metadata=data.get('metadata', {}),
                customer_email=data.get('customer_email', request.user.email),
                customer_phone=data.get('customer_phone', getattr(request.user, 'phone_number', '')),
                customer_name=data.get('customer_name', request.user.get_full_name()),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            
            # Initialize payment with gateway
            payment_result = TransactionService.initialize_payment(
                transaction=transaction,
                callback_url=data['callback_url']
            )
            
            # Serialize transaction
            transaction_data = TransactionSerializer(transaction).data
            
            return Response({
                'transaction': transaction_data,
                'authorization_url': payment_result['authorization_url'],
                'access_code': payment_result.get('access_code'),
                'reference': transaction.reference,
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_payment(self, request):
        """
        Verify payment status
        
        POST /api/transactions/verify_payment/
        
        Request body:
        {
            "reference": "TXN-..."
        }
        
        Response:
        {
            "transaction": {...},
            "status": "success|failed|pending"
        }
        """
        serializer = PaymentVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reference = serializer.validated_data['reference']
        
        try:
            # Verify payment
            transaction = TransactionService.verify_payment(reference)
            
            # Check if user owns this transaction
            if transaction.user != request.user:
                return Response({
                    'error': 'Transaction not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Serialize transaction
            transaction_data = TransactionSerializer(transaction).data
            
            return Response({
                'transaction': transaction_data,
                'status': transaction.status,
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def retry_verification(self, request):
        """
        Manually retry verification for a pending/failed transaction
        Useful when automatic verification failed due to network issues or high traffic
        
        POST /api/transactions/retry_verification/
        
        Request body:
        {
            "reference": "TXN-..." or Paystack reference from receipt
        }
        
        Response:
        {
            "success": true,
            "transaction": {...},
            "validation_codes": [...],  // For product purchases
            "message": "Transaction verified and completed successfully"
        }
        """
        reference = request.data.get('reference', '').strip()
        
        if not reference:
            return Response({
                'success': False,
                'error': 'Transaction reference is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # First, try to find transaction by reference
            try:
                transaction = Transaction.objects.select_related('gateway', 'user').get(
                    reference=reference
                )
            except Transaction.DoesNotExist:
                # Transaction not found in our system at all
                logger.warning(f"Transaction not found for reference {reference}")
                return Response({
                    'success': False,
                    'error': 'Transaction not found. Please check your reference number.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Security check: Verify the transaction belongs to the requesting user
            if transaction.user != request.user:
                return Response({
                    'success': False,
                    'error': 'You do not have permission to retry this transaction'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check current transaction status
            if transaction.status == 'success':
                # Transaction already successful - return existing details
                from products.serializers import ProductTransactionSerializer
                serializer = ProductTransactionSerializer(transaction, context={'request': request})
                
                return Response({
                    'success': True,
                    'message': 'Transaction was already completed successfully',
                    'transaction': serializer.data,
                    'already_completed': True
                }, status=status.HTTP_200_OK)
            
            if transaction.status not in ['pending', 'failed']:
                return Response({
                    'success': False,
                    'error': f'Cannot retry transaction with status: {transaction.status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"User {request.user.student_id} manually retrying verification for transaction {reference}")
            
            # Retry verification with the payment gateway
            updated_transaction = TransactionService.verify_payment(
                reference=reference
            )
            
            if updated_transaction.status == 'success':
                # If it's a product payment, complete the product purchase
                if updated_transaction.transaction_type == 'payment':
                    try:
                        completion_result = ProductPaymentService.complete_product_payment(
                            transaction=updated_transaction,
                            reduce_stock=True,
                            send_notification=True
                        )
                        
                        logger.info(
                            f"✅ User {request.user.student_id} successfully retried transaction {reference}. "
                            f"Validation codes: {completion_result.get('validation_codes', [])}"
                        )
                        
                        # Serialize full transaction with product details
                        from products.serializers import ProductTransactionSerializer
                        serializer = ProductTransactionSerializer(updated_transaction, context={'request': request})
                        
                        return Response({
                            'success': True,
                            'message': 'Transaction verified and completed successfully! Your purchase has been processed.',
                            'transaction': serializer.data,
                            'validation_codes': completion_result.get('validation_codes', []),
                            'is_cart_checkout': completion_result.get('is_cart_checkout', False)
                        }, status=status.HTTP_200_OK)
                        
                    except Exception as e:
                        logger.error(f"Error completing product payment during manual retry for {reference}: {str(e)}")
                        
                        return Response({
                            'success': False,
                            'error': 'Transaction was verified but we encountered an error processing your purchase. Please contact support.',
                            'reference': reference,
                            'details': str(e)
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    # Non-product transaction
                    transaction_data = TransactionSerializer(updated_transaction).data
                    return Response({
                        'success': True,
                        'message': 'Transaction verified successfully',
                        'transaction': transaction_data
                    }, status=status.HTTP_200_OK)
            else:
                # Verification returned non-success status
                return Response({
                    'success': False,
                    'error': f'Payment verification failed. Transaction status: {updated_transaction.status}',
                    'reference': reference,
                    'status_message': updated_transaction.status_message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error during manual retry verification for {reference}: {str(e)}")
            return Response({
                'success': False,
                'error': 'An error occurred while verifying your transaction. Please try again or contact support.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def unified_checkout(self, request):
        """
        Initialize a unified checkout for items from both Merchandise and El Mercado.
        
        POST /api/transactions/unified_checkout/
        
        Request body:
        {
            "cart_items": [
                {
                    "source": "merchandise",
                    "product_id": "uuid-here",
                    "quantity": 2,
                    "variant_selections": [
                        {"color_id": "uuid", "size_id": "uuid", "quantity": 1},
                        {"color_id": "uuid", "size_id": "uuid", "quantity": 1}
                    ],
                    "is_gift_purchase": false,
                    "purchased_for_phone": null
                },
                {
                    "source": "el_mercado",
                    "listing_id": "uuid-here",
                    "seller_id": "uuid-here",
                    "quantity": 1,
                    "variant_id": "optional-variant-uuid"
                }
            ],
            "callback_url": "https://example.com/callback",
            "shipping_info": {
                "name": "John Doe",
                "phone": "+233...",
                "email": "john@example.com",
                "address_line_1": "123 Main St",
                "city": "Kumasi",
                "region": "Ashanti"
            }
        }
        
        Response:
        {
            "success": true,
            "payment_url": "https://paystack.com/...",
            "reference": "TXN-...",
            "access_code": "...",
            "summary": {
                "merchandise_items": [...],
                "el_mercado_items": [...],
                "merchandise_total": "50.00",
                "el_mercado_total": "30.00",
                "grand_total": "80.00"
            }
        }
        """
        from payments.services.unified_checkout_service import (
            UnifiedCheckoutService,
            UnifiedCheckoutError,
            CartValidationError,
            InsufficientStockError,
            ProductNotFoundError,
            PaymentInitializationError,
        )
        
        cart_items = request.data.get('cart_items', [])
        callback_url = request.data.get('callback_url', '')
        shipping_info = request.data.get('shipping_info', {})
        
        if not cart_items:
            return Response({
                'success': False,
                'error': 'Cart is empty'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not callback_url:
            return Response({
                'success': False,
                'error': 'Callback URL is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if cart contains El Mercado items - require shipping address
        has_el_mercado_items = any(
            item.get('source') == 'el_mercado' for item in cart_items
        )
        
        if has_el_mercado_items:
            # Validate shipping address is provided
            has_valid_shipping = (
                shipping_info.get('shipping_address_id') or
                (shipping_info.get('name') and shipping_info.get('phone') and shipping_info.get('address'))
            )
            
            if not has_valid_shipping:
                return Response({
                    'success': False,
                    'error': 'Shipping address is required for El Mercado items. Please select or add a delivery address.',
                    'error_type': 'shipping_required'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = UnifiedCheckoutService.initialize_checkout(
                user=request.user,
                cart_items=cart_items,
                callback_url=callback_url,
                shipping_info=shipping_info,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            
            return Response({
                'success': True,
                'payment_url': result['payment_url'],
                'reference': result['reference'],
                'access_code': result.get('access_code'),
                'summary': result['summary'],
            }, status=status.HTTP_201_CREATED)
            
        except CartValidationError as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'validation_error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except InsufficientStockError as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'stock_error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except ProductNotFoundError as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'not_found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except PaymentInitializationError as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'payment_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except UnifiedCheckoutError as e:
            return Response({
                'success': False,
                'error': str(e),
                'error_type': 'checkout_error'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Unified checkout error: {str(e)}")
            return Response({
                'success': False,
                'error': 'An error occurred during checkout. Please try again.',
                'details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get', 'post'], permission_classes=[IsAuthenticated])
    def unified_checkout_status(self, request):
        """
        Get status of a unified/cart checkout transaction and complete checkout if needed.
        
        Handles cart checkout references with contextual prefixes:
        - ELM-*: El Mercado only cart purchases
        - TXN-*: Merchandise only cart purchases
        - UNIFIED-*: Mixed cart purchases (both El Mercado and Merchandise)
        
        GET /api/transactions/unified_checkout_status/?reference=ELM-...
        POST /api/transactions/unified_checkout_status/ with {"reference": "TXN-..."}
        
        This endpoint:
        1. Verifies the payment with Paystack if still pending
        2. Completes the checkout (creates orders/payments) if not done
        3. Returns the status and completion results
        
        Response:
        {
            "success": true,
            "reference": "ELM-...",
            "status": "success|pending|failed",
            "is_unified_checkout": true,
            "purchase_type": "el_mercado_only|merchandise_only|mixed",
            "summary": {...},
            "completion_results": {...},
            "validation_codes": [...]
        }
        """
        from payments.services.unified_checkout_service import (
            UnifiedCheckoutService,
            UnifiedCheckoutError,
        )
        
        # Accept reference from query params OR request body
        reference = (
            request.query_params.get('reference', '').strip() or 
            request.data.get('reference', '').strip()
        )
        force_recheck = request.data.get('force_recheck', False)
        
        if not reference:
            return Response({
                'success': False,
                'error': 'Reference is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # First check if user owns this transaction
            transaction = Transaction.objects.filter(
                reference=reference,
                user=request.user
            ).first()
            
            if not transaction:
                return Response({
                    'success': False,
                    'error': 'Transaction not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            metadata = transaction.metadata or {}
            
            # If transaction is still pending or force_recheck, verify with Paystack
            if transaction.status == 'pending' or force_recheck:
                try:
                    verified_transaction = TransactionService.verify_payment(reference)
                    transaction = verified_transaction
                except Exception as e:
                    logger.warning(f"Failed to verify payment {reference}: {str(e)}")
            
            # If payment is successful but checkout not completed, complete it now
            if transaction.status == 'success':
                completion_results = metadata.get('completion_results')
                
                # Check if completion has been done (has results with items)
                has_completed = (
                    completion_results and 
                    (completion_results.get('merchandise_results') or 
                     completion_results.get('el_mercado_results'))
                )
                
                if not has_completed and metadata.get('unified_checkout'):
                    try:
                        logger.info(f"Completing unified checkout via status endpoint: {reference}")
                        completion_results = UnifiedCheckoutService.complete_checkout(
                            transaction=transaction,
                            gateway_response=None,
                        )
                        # Refresh transaction to get updated metadata
                        transaction.refresh_from_db()
                        metadata = transaction.metadata or {}
                    except Exception as e:
                        logger.error(f"Failed to complete checkout {reference}: {str(e)}")
                        return Response({
                            'success': False,
                            'error': f'Payment successful but failed to create orders: {str(e)}',
                            'pending_completion': True,
                            'transaction': {
                                'reference': transaction.reference,
                                'status': transaction.status,
                                'amount': str(transaction.amount),
                            }
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Build response
            completion_results = metadata.get('completion_results', {})
            
            response_data = {
                'success': transaction.status == 'success',
                'reference': reference,
                'status': transaction.status,
                'is_unified_checkout': metadata.get('unified_checkout', False),
                'summary': metadata.get('summary'),
                'transaction': {
                    'reference': transaction.reference,
                    'status': transaction.status,
                    'amount': str(transaction.amount),
                    'currency': transaction.currency.code if transaction.currency else 'GHS',
                },
                'completion_results': completion_results,
                'merchandise_results': completion_results.get('merchandise_results', []),
                'el_mercado_results': completion_results.get('el_mercado_results', []),
                'validation_codes': completion_results.get('validation_codes', []),
                'pending_completion': (
                    transaction.status == 'success' and 
                    not completion_results.get('merchandise_results') and
                    not completion_results.get('el_mercado_results')
                ),
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except UnifiedCheckoutError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error getting unified checkout status: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to get checkout status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RefundViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing refunds
    
    list: Get user's refunds
    retrieve: Get specific refund
    request_refund: Request a new refund
    """
    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter refunds by authenticated user's transactions"""
        user = self.request.user
        return Refund.objects.filter(
            original_transaction__user=user
        ).select_related(
            'original_transaction',
            'refund_transaction',
            'initiated_by',
            'approved_by'
        ).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def request_refund(self, request):
        """
        Request a refund for a transaction
        
        POST /api/refunds/request_refund/
        
        Request body:
        {
            "transaction_reference": "TXN-...",
            "amount": "50.00",  // Optional for partial refund
            "reason": "customer_request",
            "reason_details": "Customer changed their mind"
        }
        
        Response:
        {
            "refund": {...},
            "message": "Refund request created successfully"
        }
        """
        serializer = RefundRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        reference = data['transaction_reference']
        
        try:
            # Get transaction
            transaction = get_object_or_404(Transaction, reference=reference, user=request.user)
            
            # Determine refund amount
            refund_amount = data.get('amount') or transaction.amount
            
            # Create refund
            refund = RefundService.create_refund(
                original_transaction=transaction,
                amount=refund_amount,
                reason=data['reason'],
                reason_details=data.get('reason_details', ''),
                initiated_by=request.user,
                requires_approval=data.get('requires_approval', False)
            )
            
            # If no approval required, process immediately
            if not refund.requires_approval:
                refund = RefundService.process_refund(refund)
            
            # Serialize refund
            refund_data = RefundSerializer(refund).data
            
            return Response({
                'refund': refund_data,
                'message': 'Refund request created successfully'
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing wallets
    
    retrieve: Get user's wallet
    transactions: Get wallet transaction history
    balance: Get current wallet balance
    """
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get authenticated user's wallet"""
        return Wallet.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_wallet(self, request):
        """
        Get current user's wallet
        
        GET /api/wallets/my_wallet/
        
        Response:
        {
            "wallet": {...},
            "balance": "100.00",
            "currency": "GHS"
        }
        """
        wallet, created = Wallet.objects.get_or_create(
            user=request.user,
            defaults={'currency_id': 'GHS'}
        )
        
        serializer = WalletSerializer(wallet)
        
        return Response({
            'wallet': serializer.data,
            'balance': str(wallet.balance),
            'currency': wallet.currency.code,
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """
        Get wallet transaction history
        
        GET /api/wallets/transactions/
        
        Response:
        {
            "transactions": [...]
        }
        """
        wallet = get_object_or_404(Wallet, user=request.user)
        
        transactions = WalletTransaction.objects.filter(
            wallet=wallet
        ).select_related('related_transaction').order_by('-created_at')
        
        serializer = WalletTransactionSerializer(transactions, many=True)
        
        return Response({
            'transactions': serializer.data
        }, status=status.HTTP_200_OK)


# =====================================================
# WALLET VERIFY VIEW (for payment callbacks)
# =====================================================

from rest_framework.views import APIView

class WalletVerifyView(APIView):
    """
    Verify wallet topup payment status.
    
    GET /wallet/verify/?reference=WAL-XXXXXXXX
    POST /wallet/verify/ with {"reference": "WAL-XXXXXXXX"}
    
    This endpoint is used by the payment callback page to check
    if a wallet topup was successful.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        return self._verify(request)
    
    def post(self, request):
        return self._verify(request)
    
    def _verify(self, request):
        reference = request.query_params.get('reference') or request.data.get('reference')
        
        if not reference:
            return Response(
                {'error': 'Reference is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the transaction
        try:
            transaction = Transaction.objects.get(reference=reference)
        except Transaction.DoesNotExist:
            return Response(
                {'status': 'failed', 'error': 'Transaction not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify with Paystack if still pending
        if transaction.status == 'pending':
            try:
                verified_transaction = TransactionService.verify_payment(reference)
                transaction = verified_transaction
            except Exception as e:
                return Response({
                    'status': 'failed',
                    'error': f'Verification failed: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Return the status
        if transaction.status == 'success':
            # Get wallet balance if user is authenticated
            balance = None
            if request.user.is_authenticated:
                try:
                    wallet = Wallet.objects.get(user=request.user)
                    balance = str(wallet.balance)
                except Wallet.DoesNotExist:
                    pass
            
            return Response({
                'status': 'success',
                'message': 'Wallet topup successful',
                'data': {
                    'reference': transaction.reference,
                    'amount': str(transaction.amount),
                    'currency': transaction.currency.code if transaction.currency else 'GHS',
                    'wallet_balance': balance,
                }
            }, status=status.HTTP_200_OK)
        elif transaction.status == 'failed':
            return Response({
                'status': 'failed',
                'message': 'Wallet topup failed',
                'data': {
                    'reference': transaction.reference,
                    'failure_reason': transaction.failure_reason or 'Payment was not successful',
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'status': 'pending',
                'message': 'Payment is still being processed',
                'data': {
                    'reference': transaction.reference,
                }
            }, status=status.HTTP_200_OK)


# =====================================================
# EXPENSE MANAGEMENT VIEWS
# =====================================================

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth, TruncDay
from datetime import datetime, timedelta
from django.utils import timezone

from .models import (
    Expense,
    ExpenseCategory,
    ExpenseRecipient,
    AccountBalance,
    ExpenseAuditLog,
    BudgetAllocation,
)
from .serializers import (
    ExpenseSerializer,
    ExpenseCreateSerializer,
    ExpenseUpdateSerializer,
    ExpenseApprovalSerializer,
    ExpenseCategorySerializer,
    ExpenseRecipientSerializer,
    ExpenseRecipientMinimalSerializer,
    AccountBalanceSerializer,
    FinancialSummarySerializer,
    ExpenseAuditLogSerializer,
    BudgetAllocationSerializer,
    ExpenseAnalyticsSerializer,
)


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing expense categories
    """
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ExpenseCategory.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.annotate(
            expense_count=Count('expenses'),
            total_spent=Sum('expenses__amount', filter=models.Q(expenses__status='paid'))
        )


class ExpenseRecipientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing expense recipients
    """
    queryset = ExpenseRecipient.objects.all()
    serializer_class = ExpenseRecipientSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list' and self.request.query_params.get('minimal') == 'true':
            return ExpenseRecipientMinimalSerializer
        return ExpenseRecipientSerializer
    
    def get_queryset(self):
        queryset = ExpenseRecipient.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by vendor status
        is_vendor = self.request.query_params.get('is_vendor')
        if is_vendor is not None:
            queryset = queryset.filter(is_vendor=is_vendor.lower() == 'true')
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset


class ExpenseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing expenses
    
    list: Get all expenses (with filtering)
    create: Create a new expense
    retrieve: Get specific expense
    update: Update an expense
    destroy: Delete an expense
    approve: Approve an expense
    reject: Reject an expense
    mark_paid: Mark as paid
    resend_sms: Resend SMS notification
    """
    queryset = Expense.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ExpenseCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ExpenseUpdateSerializer
        return ExpenseSerializer
    
    def get_queryset(self):
        queryset = Expense.objects.select_related(
            'category', 'recipient', 'currency', 'created_by', 'approved_by'
        )
        
        # Filter by status
        expense_status = self.request.query_params.get('status')
        if expense_status:
            queryset = queryset.filter(status=expense_status)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(expense_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(expense_date__lte=end_date)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(description__icontains=search) |
                models.Q(reference__icontains=search)
            )
        
        return queryset.order_by('-expense_date', '-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve an expense
        
        POST /api/expenses/{id}/approve/
        """
        expense = self.get_object()
        
        if expense.status != 'pending':
            return Response({
                'error': 'Only pending expenses can be approved'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        expense.status = 'approved'
        expense.approved_by = request.user
        expense.approved_at = timezone.now()
        expense.save()
        
        # Create audit log
        ExpenseAuditLog.objects.create(
            expense=expense,
            action='approved',
            performed_by=request.user,
            comments=f'Approved by {request.user.get_full_name()}'
        )
        
        return Response({
            'message': 'Expense approved successfully',
            'expense': ExpenseSerializer(expense).data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject an expense
        
        POST /api/expenses/{id}/reject/
        {
            "reason": "Rejection reason"
        }
        """
        expense = self.get_object()
        
        if expense.status != 'pending':
            return Response({
                'error': 'Only pending expenses can be rejected'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reason = request.data.get('reason', '')
        if not reason:
            return Response({
                'error': 'Rejection reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        expense.status = 'rejected'
        expense.rejection_reason = reason
        expense.save()
        
        # Create audit log
        ExpenseAuditLog.objects.create(
            expense=expense,
            action='rejected',
            performed_by=request.user,
            comments=f'Rejected: {reason}'
        )
        
        return Response({
            'message': 'Expense rejected',
            'expense': ExpenseSerializer(expense).data
        })
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """
        Mark expense as paid
        
        POST /api/expenses/{id}/mark_paid/
        {
            "payment_reference": "optional reference",
            "payment_date": "2026-01-12"
        }
        """
        expense = self.get_object()
        
        if expense.status not in ['pending', 'approved']:
            return Response({
                'error': 'Expense cannot be marked as paid'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        expense.status = 'paid'
        expense.payment_reference = request.data.get('payment_reference', expense.payment_reference)
        expense.payment_date = request.data.get('payment_date', timezone.now().date())
        
        if not expense.approved_by:
            expense.approved_by = request.user
            expense.approved_at = timezone.now()
        
        expense.save()
        
        # Recalculate balance
        AccountBalance.recalculate_balance(updated_by=request.user)
        
        # Create audit log
        ExpenseAuditLog.objects.create(
            expense=expense,
            action='paid',
            performed_by=request.user,
            comments=f'Marked as paid. Reference: {expense.payment_reference}'
        )
        
        return Response({
            'message': 'Expense marked as paid',
            'expense': ExpenseSerializer(expense).data
        })
    
    @action(detail=True, methods=['post'])
    def resend_sms(self, request, pk=None):
        """
        Resend SMS notification to executives
        
        POST /api/expenses/{id}/resend_sms/
        """
        expense = self.get_object()
        expense.sms_notification_sent = False
        expense.save()
        expense.send_expense_notification_to_executives()
        
        return Response({
            'success': expense.sms_notification_sent,
            'message': 'SMS notification sent' if expense.sms_notification_sent else 'SMS notification failed',
            'error': expense.sms_notification_error if not expense.sms_notification_sent else None
        })


class FinancialSummaryView(APIView):
    """
    API View for getting financial summary
    
    GET /api/expenses/financial-summary/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get balance info
        balance_info = AccountBalance.get_current_balance()
        
        # Get pending expenses
        pending_expenses = Expense.objects.filter(status='pending')
        pending_count = pending_expenses.count()
        pending_amount = pending_expenses.aggregate(total=Sum('amount'))['total'] or 0
        
        # Get this month's data
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        
        this_month_expenses = Expense.objects.filter(
            status='paid',
            expense_date__gte=first_day_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        this_month_income = Transaction.objects.filter(
            status='success',
            transaction_type__in=['payment', 'donation'],
            initiated_at__gte=first_day_of_month
        ).aggregate(total=Sum('net_amount'))['total'] or 0
        
        data = {
            'initial_balance': balance_info['initial_balance'],
            'total_income': balance_info['total_income'],
            'total_expenditure': balance_info['total_expenditure'],
            'current_balance': balance_info['current_balance'],
            'currency': balance_info['currency'],
            'pending_expenses_count': pending_count,
            'pending_expenses_amount': pending_amount,
            'this_month_expenses': this_month_expenses,
            'this_month_income': this_month_income,
        }
        
        serializer = FinancialSummarySerializer(data)
        return Response(serializer.data)


class ExpenseAnalyticsView(APIView):
    """
    API View for expense analytics
    
    GET /api/expenses/analytics/?period=month
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        period = request.query_params.get('period', 'month')
        
        today = timezone.now().date()
        
        if period == 'week':
            period_start = today - timedelta(days=7)
        elif period == 'month':
            period_start = today.replace(day=1)
        elif period == 'quarter':
            month = today.month
            quarter_start_month = ((month - 1) // 3) * 3 + 1
            period_start = today.replace(month=quarter_start_month, day=1)
        elif period == 'year':
            period_start = today.replace(month=1, day=1)
        else:
            period_start = today - timedelta(days=30)
        
        period_end = today
        
        # Get expenses in period
        expenses = Expense.objects.filter(
            status='paid',
            expense_date__gte=period_start,
            expense_date__lte=period_end
        )
        
        # Summary
        summary = expenses.aggregate(
            total=Sum('amount'),
            count=Count('id'),
            avg=Avg('amount')
        )
        
        # By category
        by_category = expenses.values(
            'category__name', 'category__icon', 'category__color'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # By payment method
        by_payment_method = expenses.values(
            'payment_method'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # By status (all expenses, not just paid)
        all_expenses = Expense.objects.filter(
            expense_date__gte=period_start,
            expense_date__lte=period_end
        )
        by_status = {
            'pending': all_expenses.filter(status='pending').count(),
            'approved': all_expenses.filter(status='approved').count(),
            'paid': all_expenses.filter(status='paid').count(),
            'rejected': all_expenses.filter(status='rejected').count(),
        }
        
        # Daily trend
        daily_trend = expenses.annotate(
            day=TruncDay('expense_date')
        ).values('day').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('day')
        
        # Monthly trend (last 6 months)
        six_months_ago = today - timedelta(days=180)
        monthly_trend = Expense.objects.filter(
            status='paid',
            expense_date__gte=six_months_ago
        ).annotate(
            month=TruncMonth('expense_date')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('month')
        
        # Top recipients
        top_recipients = expenses.values(
            'recipient__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:10]
        
        data = {
            'period_start': period_start,
            'period_end': period_end,
            'total_expenses': summary['total'] or 0,
            'expense_count': summary['count'] or 0,
            'average_expense': summary['avg'] or 0,
            'by_category': list(by_category),
            'by_payment_method': list(by_payment_method),
            'by_status': by_status,
            'daily_trend': list(daily_trend),
            'monthly_trend': list(monthly_trend),
            'top_recipients': list(top_recipients),
        }
        
        serializer = ExpenseAnalyticsSerializer(data)
        return Response(serializer.data)


class BudgetAllocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing budget allocations
    """
    queryset = BudgetAllocation.objects.all()
    serializer_class = BudgetAllocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = BudgetAllocation.objects.select_related('category', 'currency', 'created_by')
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by current (date range includes today)
        current = self.request.query_params.get('current')
        if current and current.lower() == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(
                start_date__lte=today,
                end_date__gte=today
            )
        
        return queryset.order_by('-start_date')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AccountBalanceView(APIView):
    """
    API View for account balance
    
    GET /api/expenses/account-balance/
    POST /api/expenses/account-balance/recalculate/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        balance = AccountBalance.get_or_create_singleton()
        balance_info = AccountBalance.get_current_balance()
        
        return Response({
            'id': str(balance.id),
            'initial_balance': str(balance.initial_balance),
            'total_income': str(balance_info['total_income']),
            'total_expenditure': str(balance_info['total_expenditure']),
            'current_balance': str(balance_info['current_balance']),
            'currency': balance_info['currency'],
            'notes': balance.notes,
            'updated_at': balance.updated_at,
        })
    
    def post(self, request):
        """Recalculate balance"""
        balance = AccountBalance.recalculate_balance(updated_by=request.user)
        balance_info = AccountBalance.get_current_balance()
        
        return Response({
            'message': 'Balance recalculated successfully',
            'current_balance': str(balance_info['current_balance']),
            'total_income': str(balance_info['total_income']),
            'total_expenditure': str(balance_info['total_expenditure']),
        })


class ExpenseAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing expense audit logs (read-only)
    """
    queryset = ExpenseAuditLog.objects.all()
    serializer_class = ExpenseAuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ExpenseAuditLog.objects.select_related(
            'expense', 'performed_by'
        )
        
        # Filter by expense
        expense_id = self.request.query_params.get('expense')
        if expense_id:
            queryset = queryset.filter(expense_id=expense_id)
        
        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        return queryset.order_by('-created_at')
