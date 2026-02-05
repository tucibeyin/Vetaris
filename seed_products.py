import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import database

def seed_products():
    print("Connecting to database...")
    database.init_db()
    
    current_products = database.get_all_products(include_inactive=True)
    if len(current_products) > 0:
        print(f"⚠️ Database already has {len(current_products)} products. Skipping seed.")
        return

    print("Seeding products...")
    
    products = [
        {
            "name": "Vetaris Formül A",
            "price": 450.00,
            "image": "/images/formula-a.jpg",
            "description": "Eklem sağlığı ve hareketlilik için özel formül. Glukozamin ve Kondroitin içerir.",
            "category": "Takviye",
            "stock": 100,
            "is_active": True
        },
        {
            "name": "Vetaris Formül B",
            "price": 380.00,
            "image": "/images/formula-b.jpg",
            "description": "Tüy ve deri sağlığı için biotin ve çinko destekli formül.",
            "category": "Bakım",
            "stock": 150,
            "is_active": True
        },
        {
            "name": "Vetaris Bakım Spreyi",
            "price": 120.00,
            "image": "/images/spray.jpg",
            "description": "Pati ve tüy temizliği için doğal içerikli bakım spreyi.",
            "category": "Hijyen",
            "stock": 200,
            "is_active": True
        }
    ]

    for p in products:
        try:
            created = database.create_product(p)
            print(f"✅ Created: {created['name']}")
        except Exception as e:
            print(f"❌ Failed to create {p['name']}: {e}")

if __name__ == "__main__":
    seed_products()
