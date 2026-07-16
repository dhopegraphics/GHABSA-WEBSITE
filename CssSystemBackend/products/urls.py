from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.views import ProductListView, ProductPaymentViewSet, StaffMerchandiseValidationViewSet

# Create router for ViewSets
router = DefaultRouter()
router.register(r'payments', ProductPaymentViewSet, basename='product-payments')
router.register(r'staff/validation', StaffMerchandiseValidationViewSet, basename='staff-validation')

urlpatterns = [
    # Product listing
    path(
        "products/",
        ProductListView.as_view(),
        name="products",
    ),
    
    # Integrated payment endpoints via ViewSet router
    # /products/payments/initialize/
    # /products/payments/verify/
    # /products/payments/my_purchases/
    # /products/payments/collect/
    # /products/payments/cart_checkout/
    # /products/payments/update_variant_preferences/
    
    # Staff validation endpoints (requires is_staff=True)
    # /products/staff/validation/lookup/
    # /products/staff/validation/collect/
    # /products/staff/validation/bulk_collect/
    # /products/staff/validation/bulk_lookup/
    # /products/staff/validation/mark_unavailable/
    path('', include(router.urls)),
]
