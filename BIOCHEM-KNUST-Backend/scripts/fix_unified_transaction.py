"""
Fix stuck unified checkout transaction UNIFIED-C65F34E977334819
Run with: python manage.py shell < scripts/fix_unified_transaction.py
"""
from payments.models import Transaction
from products.models import ProductPayment, Product, ProductColor, ProductSize
from el_mercado.models import Listing, MarketplaceOrder, Seller
from decimal import Decimal
import secrets
import string

def generate_unique_code():
    while True:
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        if not ProductPayment.objects.filter(transaction_validation_code=code).exists():
            return code

# Get the problematic transaction
txn = Transaction.objects.filter(reference='UNIFIED-C65F34E977334819').first()
if not txn:
    print('Transaction not found')
    exit()

metadata = txn.metadata
print(f'Processing transaction: {txn.reference}')

# Check if ProductPayments already exist
existing_pps = ProductPayment.objects.filter(transaction_record=txn).count()
print(f'Existing ProductPayments: {existing_pps}')

if existing_pps == 0:
    # Process merchandise items
    merch_items = metadata.get('merchandise_items', [])
    for item in merch_items:
        item_metadata = item.get('metadata', {})
        product_id = item_metadata.get('product_id')
        variant_selections = item_metadata.get('variant_selections', [])
        
        product = Product.objects.get(product_id=product_id)
        print(f'Processing merchandise: {product.product_name}')
        
        if variant_selections:
            for sel in variant_selections:
                color = ProductColor.objects.filter(id=sel.get('color_id')).first()
                size = ProductSize.objects.filter(id=sel.get('size_id')).first()
                validation_code = generate_unique_code()
                
                pp = ProductPayment.objects.create(
                    buyer=txn.user,
                    product=product,
                    transaction_record=txn,
                    quantity=sel.get('quantity', 1),
                    amount=Decimal(item_metadata.get('unit_price', '0')) * sel.get('quantity', 1),
                    price_at_purchase=Decimal(item_metadata.get('unit_price', '0')),
                    variant_selections=[{
                        'color_id': str(color.id) if color else None,
                        'size_id': str(size.id) if size else None,
                        'quantity': sel.get('quantity', 1),
                    }] if (color or size) else [],
                    transaction_validation_code=validation_code,
                    payment_successful=True,
                )
                color_name = color.name if color else 'No color'
                size_code = size.code if size else 'No size'
                print(f'  Created ProductPayment: {validation_code} ({color_name}, {size_code})')
        else:
            validation_code = generate_unique_code()
            pp = ProductPayment.objects.create(
                buyer=txn.user,
                product=product,
                transaction_record=txn,
                quantity=item_metadata.get('quantity', 1),
                amount=Decimal(item_metadata.get('unit_price', '0')) * item_metadata.get('quantity', 1),
                price_at_purchase=Decimal(item_metadata.get('unit_price', '0')),
                transaction_validation_code=validation_code,
                payment_successful=True,
            )
            print(f'  Created ProductPayment: {validation_code}')

# Check if MarketplaceOrders already exist
existing_orders = MarketplaceOrder.objects.filter(payment_reference=txn.reference).count()
print(f'Existing MarketplaceOrders: {existing_orders}')

if existing_orders == 0:
    # Process El Mercado items
    el_mercado_items = metadata.get('el_mercado_items', [])
    for item in el_mercado_items:
        item_metadata = item.get('metadata', {})
        listing_id = item_metadata.get('listing_id')
        seller_id = item_metadata.get('seller_id')
        
        listing = Listing.objects.filter(id=listing_id).first()
        seller = Seller.objects.filter(id=seller_id).first()
        
        if listing and seller:
            shipping_info = metadata.get('shipping_info', {})
            
            # Calculate values
            total_price = Decimal(item.get('total_price', '0'))
            commission_rate = Decimal(item_metadata.get('commission_rate', '10'))
            platform_commission = total_price * (commission_rate / 100)
            seller_earnings = total_price - platform_commission
            
            order = MarketplaceOrder.objects.create(
                buyer=txn.user,
                seller=seller,
                subtotal=total_price,
                total_amount=total_price,
                platform_commission=platform_commission,
                commission_rate=commission_rate,
                seller_earnings=seller_earnings,
                shipping_name=shipping_info.get('name', ''),
                shipping_phone=shipping_info.get('phone', ''),
                shipping_email=shipping_info.get('email', ''),
                shipping_address_line_1=shipping_info.get('address', ''),
                shipping_city=shipping_info.get('city', ''),
                shipping_region=shipping_info.get('region', ''),
                status='PAID',
                payment_status='PAID',
                payment_reference=txn.reference,
                paid_at=txn.completed_at,
            )
            
            # Create OrderItem
            from el_mercado.models import OrderItem
            OrderItem.objects.create(
                order=order,
                listing=listing,
                quantity=item_metadata.get('quantity', 1),
                unit_price=Decimal(item_metadata.get('unit_price', '0')),
                total_price=total_price,
            )
            
            print(f'Created MarketplaceOrder: {order.order_number} for {listing.title}')

print('Done!')
