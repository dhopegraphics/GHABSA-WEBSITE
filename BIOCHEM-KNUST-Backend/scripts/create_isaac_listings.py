"""
Script to create sample listings for Isaac Mensah seller.
Run with: python manage.py shell < scripts/create_isaac_listings.py
"""
from el_mercado.models import Seller, Category, Listing
from decimal import Decimal

seller = Seller.objects.get(slug='isaac-mensah')

# Get categories
phones = Category.objects.get(name='Phones & Tablets')
textbooks = Category.objects.get(name='Textbooks')
mens_clothing = Category.objects.get(name="Men's Clothing")
furniture = Category.objects.get(name='Furniture')
sports = Category.objects.get(name='Sports Equipment')

listings_data = [
    # Phones & Tablets
    {
        'title': 'iPhone 13 Pro Max - 256GB (Used, Excellent)',
        'description': 'Selling my iPhone 13 Pro Max in excellent condition. 256GB storage, Sierra Blue color. Battery health at 89%. Comes with original box and charger. No scratches or dents.',
        'listing_type': 'PRODUCT',
        'category': phones,
        'price': Decimal('4500.00'),
        'compare_at_price': Decimal('6500.00'),
        'stock_quantity': 1,
        'condition': 'LIKE_NEW',
        'status': 'ACTIVE',
    },
    {
        'title': 'Samsung Galaxy Tab S8 - WiFi',
        'description': 'Brand new Samsung Galaxy Tab S8. Perfect for students - great for note-taking and reading. Comes with S Pen included.',
        'listing_type': 'PRODUCT',
        'category': phones,
        'price': Decimal('3200.00'),
        'stock_quantity': 2,
        'condition': 'NEW',
        'status': 'ACTIVE',
    },
    # Textbooks
    {
        'title': 'Introduction to Algorithms (CLRS) - 4th Edition',
        'description': 'The essential algorithms textbook. Used for CS 201. Some highlighting but in good condition overall.',
        'listing_type': 'PRODUCT',
        'category': textbooks,
        'price': Decimal('180.00'),
        'compare_at_price': Decimal('350.00'),
        'stock_quantity': 1,
        'condition': 'GOOD',
        'status': 'ACTIVE',
    },
    {
        'title': 'Database System Concepts - 7th Edition',
        'description': 'Perfect for CS 315 Database course. Clean copy with no markings.',
        'listing_type': 'PRODUCT',
        'category': textbooks,
        'price': Decimal('150.00'),
        'stock_quantity': 1,
        'condition': 'LIKE_NEW',
        'status': 'ACTIVE',
    },
    {
        'title': 'Computer Networks by Tanenbaum - 6th Ed',
        'description': 'Great networking textbook. Covers everything from physical layer to application layer.',
        'listing_type': 'PRODUCT',
        'category': textbooks,
        'price': Decimal('120.00'),
        'stock_quantity': 3,
        'condition': 'GOOD',
        'status': 'ACTIVE',
    },
    # Mens Clothing
    {
        'title': 'Nike Air Jordan Sneakers - Size 43',
        'description': 'Original Nike Air Jordan 1 Retro High. Barely worn, still fresh. Size EU 43 / US 9.5',
        'listing_type': 'PRODUCT',
        'category': mens_clothing,
        'price': Decimal('850.00'),
        'compare_at_price': Decimal('1200.00'),
        'stock_quantity': 1,
        'condition': 'LIKE_NEW',
        'status': 'ACTIVE',
    },
    {
        'title': 'Formal Shirts Bundle (3 pieces)',
        'description': 'Three quality formal shirts - white, blue, and striped. Size M. Perfect for presentations and interviews.',
        'listing_type': 'PRODUCT',
        'category': mens_clothing,
        'price': Decimal('200.00'),
        'stock_quantity': 2,
        'condition': 'GOOD',
        'status': 'ACTIVE',
    },
    # Furniture
    {
        'title': 'Study Desk with Chair - Compact',
        'description': 'Perfect study setup for hostel rooms. Desk 100x60cm with comfortable chair. Easy to assemble.',
        'listing_type': 'PRODUCT',
        'category': furniture,
        'price': Decimal('450.00'),
        'stock_quantity': 1,
        'condition': 'GOOD',
        'status': 'ACTIVE',
    },
    # Sports
    {
        'title': 'Wilson Tennis Racket - Pro Staff',
        'description': 'Professional grade tennis racket. Great for intermediate to advanced players. Includes cover.',
        'listing_type': 'PRODUCT',
        'category': sports,
        'price': Decimal('380.00'),
        'stock_quantity': 1,
        'condition': 'GOOD',
        'status': 'ACTIVE',
    },
    {
        'title': 'Yoga Mat - Premium Quality',
        'description': 'Thick, non-slip yoga mat. 6mm thickness for comfort. Navy blue color.',
        'listing_type': 'PRODUCT',
        'category': sports,
        'price': Decimal('85.00'),
        'stock_quantity': 5,
        'condition': 'NEW',
        'status': 'ACTIVE',
    },
]

created = 0
for data in listings_data:
    listing, was_created = Listing.objects.get_or_create(
        seller=seller,
        title=data['title'],
        defaults=data
    )
    if was_created:
        listing.publish()
        created += 1
        print(f'Created: {listing.title}')
    else:
        print(f'Exists: {listing.title}')

print(f'\nTotal created: {created}')
print(f'Total listings for {seller.display_name}: {seller.listings.count()}')
