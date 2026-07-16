"""
El Mercado Category Seeder
==========================
Run with: python manage.py shell < el_mercado/seed_categories.py
Or: python manage.py runscript seed_categories (if using django-extensions)
"""

from el_mercado.models import Category
from django.utils.text import slugify

# Define marketplace categories
CATEGORIES = [
    # Main Categories
    {
        "name": "Electronics",
        "icon": "📱",
        "description": "Phones, laptops, gadgets, and electronic accessories",
        "display_order": 1,
        "subcategories": [
            {"name": "Phones & Tablets", "icon": "📱", "description": "Mobile phones and tablets"},
            {"name": "Laptops & Computers", "icon": "💻", "description": "Laptops, desktops, and accessories"},
            {"name": "Audio & Headphones", "icon": "🎧", "description": "Speakers, earbuds, and headphones"},
            {"name": "Gaming", "icon": "🎮", "description": "Gaming consoles, accessories, and games"},
            {"name": "Cameras & Photography", "icon": "📷", "description": "Cameras, lenses, and photography equipment"},
            {"name": "Accessories", "icon": "🔌", "description": "Chargers, cables, and electronic accessories"},
        ]
    },
    {
        "name": "Fashion",
        "icon": "👕",
        "description": "Clothing, shoes, and fashion accessories",
        "display_order": 2,
        "subcategories": [
            {"name": "Men's Clothing", "icon": "👔", "description": "Shirts, pants, suits, and more"},
            {"name": "Women's Clothing", "icon": "👗", "description": "Dresses, tops, skirts, and more"},
            {"name": "Shoes & Footwear", "icon": "👟", "description": "Sneakers, heels, sandals, and boots"},
            {"name": "Bags & Accessories", "icon": "👜", "description": "Handbags, backpacks, and accessories"},
            {"name": "Jewelry & Watches", "icon": "💍", "description": "Rings, necklaces, watches, and more"},
            {"name": "African Wear", "icon": "🇬🇭", "description": "Traditional African clothing and designs"},
        ]
    },
    {
        "name": "Home & Living",
        "icon": "🏠",
        "description": "Furniture, decor, and home essentials",
        "display_order": 3,
        "subcategories": [
            {"name": "Furniture", "icon": "🛋️", "description": "Sofas, beds, tables, and chairs"},
            {"name": "Kitchen & Dining", "icon": "🍽️", "description": "Cookware, utensils, and dining sets"},
            {"name": "Home Decor", "icon": "🖼️", "description": "Art, mirrors, rugs, and decorations"},
            {"name": "Bedding & Bath", "icon": "🛏️", "description": "Sheets, towels, and bathroom items"},
            {"name": "Lighting", "icon": "💡", "description": "Lamps, bulbs, and lighting fixtures"},
            {"name": "Storage & Organization", "icon": "📦", "description": "Shelves, boxes, and organizers"},
        ]
    },
    {
        "name": "Books & Stationery",
        "icon": "📚",
        "description": "Books, study materials, and office supplies",
        "display_order": 4,
        "subcategories": [
            {"name": "Textbooks", "icon": "📖", "description": "Academic textbooks and course materials"},
            {"name": "Novels & Fiction", "icon": "📕", "description": "Fiction, literature, and stories"},
            {"name": "Study Materials", "icon": "📝", "description": "Past questions, notes, and guides"},
            {"name": "Office Supplies", "icon": "✏️", "description": "Pens, paper, folders, and more"},
            {"name": "Art Supplies", "icon": "🎨", "description": "Drawing, painting, and craft materials"},
        ]
    },
    {
        "name": "Health & Beauty",
        "icon": "💄",
        "description": "Skincare, makeup, and health products",
        "display_order": 5,
        "subcategories": [
            {"name": "Skincare", "icon": "🧴", "description": "Moisturizers, serums, and skin treatments"},
            {"name": "Makeup & Cosmetics", "icon": "💄", "description": "Foundation, lipstick, and makeup tools"},
            {"name": "Hair Care", "icon": "💇", "description": "Shampoos, conditioners, and hair styling"},
            {"name": "Fragrances", "icon": "🌸", "description": "Perfumes, colognes, and body sprays"},
            {"name": "Personal Care", "icon": "🧼", "description": "Hygiene and personal care products"},
            {"name": "Health & Wellness", "icon": "💊", "description": "Vitamins, supplements, and health aids"},
        ]
    },
    {
        "name": "Food & Groceries",
        "icon": "🍕",
        "description": "Food items, snacks, and groceries",
        "display_order": 6,
        "subcategories": [
            {"name": "Snacks & Beverages", "icon": "🍿", "description": "Chips, drinks, and snack foods"},
            {"name": "Homemade Foods", "icon": "🍲", "description": "Home-cooked meals and local delicacies"},
            {"name": "Baked Goods", "icon": "🍰", "description": "Cakes, pastries, and baked treats"},
            {"name": "Fresh Produce", "icon": "🥗", "description": "Fruits, vegetables, and fresh items"},
            {"name": "Groceries", "icon": "🛒", "description": "Essential grocery items"},
        ]
    },
    {
        "name": "Services",
        "icon": "🔧",
        "description": "Professional and personal services",
        "display_order": 7,
        "subcategories": [
            {"name": "Tutoring & Education", "icon": "👨‍🏫", "description": "Academic tutoring and lessons"},
            {"name": "Tech & IT Services", "icon": "💻", "description": "Software, web development, and IT support"},
            {"name": "Design & Creative", "icon": "🎨", "description": "Graphic design, video editing, and creative work"},
            {"name": "Writing & Translation", "icon": "✍️", "description": "Content writing, editing, and translation"},
            {"name": "Photography & Video", "icon": "📸", "description": "Event coverage and media production"},
            {"name": "Repairs & Maintenance", "icon": "🔧", "description": "Phone, laptop, and equipment repairs"},
            {"name": "Beauty & Styling", "icon": "💅", "description": "Makeup, hair styling, and beauty services"},
            {"name": "Event Planning", "icon": "🎉", "description": "Party planning and event coordination"},
        ]
    },
    {
        "name": "Sports & Fitness",
        "icon": "⚽",
        "description": "Sports equipment and fitness gear",
        "display_order": 8,
        "subcategories": [
            {"name": "Sports Equipment", "icon": "⚽", "description": "Balls, rackets, and sports gear"},
            {"name": "Gym & Fitness", "icon": "🏋️", "description": "Weights, yoga mats, and fitness equipment"},
            {"name": "Sportswear", "icon": "👟", "description": "Athletic clothing and shoes"},
            {"name": "Outdoor & Camping", "icon": "🏕️", "description": "Tents, backpacks, and outdoor gear"},
        ]
    },
    {
        "name": "Vehicles & Transport",
        "icon": "🚗",
        "description": "Vehicles, parts, and transportation items",
        "display_order": 9,
        "subcategories": [
            {"name": "Bicycles", "icon": "🚲", "description": "Bikes, parts, and cycling accessories"},
            {"name": "Motorcycles", "icon": "🏍️", "description": "Motorbikes and motorcycle parts"},
            {"name": "Vehicle Parts", "icon": "🔧", "description": "Car and vehicle spare parts"},
            {"name": "Vehicle Accessories", "icon": "🚗", "description": "Car accessories and gadgets"},
        ]
    },
    {
        "name": "Other",
        "icon": "📦",
        "description": "Other items and miscellaneous",
        "display_order": 10,
        "subcategories": [
            {"name": "Collectibles", "icon": "🏆", "description": "Rare items and collectibles"},
            {"name": "Musical Instruments", "icon": "🎸", "description": "Guitars, keyboards, and instruments"},
            {"name": "Pets & Supplies", "icon": "🐕", "description": "Pet food, accessories, and supplies"},
            {"name": "Tickets & Vouchers", "icon": "🎫", "description": "Event tickets and gift vouchers"},
        ]
    },
]


def seed_categories():
    """Create categories in the database"""
    created_count = 0
    
    for cat_data in CATEGORIES:
        subcategories = cat_data.pop('subcategories', [])
        
        # Create or get parent category
        parent, created = Category.objects.get_or_create(
            slug=slugify(cat_data['name']),
            defaults={
                'name': cat_data['name'],
                'icon': cat_data.get('icon', ''),
                'description': cat_data.get('description', ''),
                'display_order': cat_data.get('display_order', 0),
                'is_active': True,
            }
        )
        
        if created:
            created_count += 1
            print(f"✅ Created category: {parent.name}")
        else:
            print(f"⏭️  Category exists: {parent.name}")
        
        # Create subcategories
        for idx, sub_data in enumerate(subcategories):
            sub, sub_created = Category.objects.get_or_create(
                slug=slugify(f"{cat_data['name']}-{sub_data['name']}"),
                defaults={
                    'name': sub_data['name'],
                    'icon': sub_data.get('icon', ''),
                    'description': sub_data.get('description', ''),
                    'parent': parent,
                    'display_order': idx,
                    'is_active': True,
                }
            )
            
            if sub_created:
                created_count += 1
                print(f"  ✅ Created subcategory: {sub.name}")
            else:
                print(f"  ⏭️  Subcategory exists: {sub.name}")
    
    print(f"\n🎉 Done! Created {created_count} categories.")
    return created_count


if __name__ == "__main__":
    seed_categories()
