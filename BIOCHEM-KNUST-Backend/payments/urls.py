"""
Payment System URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TransactionViewSet,
    RefundViewSet,
    WalletViewSet,
    PaymentGatewayViewSet,
    CurrencyViewSet,
    WalletVerifyView,  # Added for wallet topup verification
    # Expense Management
    ExpenseViewSet,
    ExpenseCategoryViewSet,
    ExpenseRecipientViewSet,
    BudgetAllocationViewSet,
    ExpenseAuditLogViewSet,
    FinancialSummaryView,
    ExpenseAnalyticsView,
    AccountBalanceView,
    # Dashboard Views
    expense_dashboard,
    expense_list_view,
    expense_categories_view,
    expense_recipients_view,
    expense_budget_view,
    expense_audit_view,
    expense_balance_view,
    expense_add_view,
    expense_edit_view,
    expense_delete_view,
    category_add_view,
    recipient_add_view,
    budget_add_view,
)
from .webhooks import PaystackWebhookView

app_name = 'payments'

# Create router
router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'refunds', RefundViewSet, basename='refund')
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'gateways', PaymentGatewayViewSet, basename='gateway')
router.register(r'currencies', CurrencyViewSet, basename='currency')

# Expense Management
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'expense-categories', ExpenseCategoryViewSet, basename='expense-category')
router.register(r'expense-recipients', ExpenseRecipientViewSet, basename='expense-recipient')
router.register(r'budgets', BudgetAllocationViewSet, basename='budget')
router.register(r'expense-audit-logs', ExpenseAuditLogViewSet, basename='expense-audit-log')

# URL patterns
urlpatterns = [
    # Modern Expense Dashboard (Full Pages)
    path('expense-dashboard/', expense_dashboard, name='expense-dashboard'),
    path('expense-dashboard/expenses/', expense_list_view, name='dashboard-expense-list'),
    path('expense-dashboard/expenses/add/', expense_add_view, name='expense-add'),
    path('expense-dashboard/expenses/<uuid:pk>/edit/', expense_edit_view, name='expense-edit'),
    path('expense-dashboard/expenses/<uuid:pk>/delete/', expense_delete_view, name='expense-delete'),
    path('expense-dashboard/categories/', expense_categories_view, name='expense-categories'),
    path('expense-dashboard/categories/add/', category_add_view, name='category-add'),
    path('expense-dashboard/recipients/', expense_recipients_view, name='expense-recipients'),
    path('expense-dashboard/recipients/add/', recipient_add_view, name='recipient-add'),
    path('expense-dashboard/budget/', expense_budget_view, name='expense-budget'),
    path('expense-dashboard/budget/add/', budget_add_view, name='budget-add'),
    path('expense-dashboard/audit/', expense_audit_view, name='expense-audit'),
    path('expense-dashboard/balance/', expense_balance_view, name='expense-balance'),
    
    # API endpoints
    path('api/', include(router.urls)),
    
    # Wallet verification endpoint (for payment callbacks)
    path('wallet/verify/', WalletVerifyView.as_view(), name='wallet-verify'),
    
    # Expense Management API
    path('api/financial-summary/', FinancialSummaryView.as_view(), name='financial-summary'),
    path('api/expense-analytics/', ExpenseAnalyticsView.as_view(), name='expense-analytics'),
    path('api/account-balance/', AccountBalanceView.as_view(), name='account-balance'),
    
    # Webhook endpoints
    path('webhooks/paystack/', PaystackWebhookView.as_view(), name='paystack-webhook'),
]
