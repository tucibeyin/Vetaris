import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import database

def verify_products():
    print("Connecting to database...")
    database.init_db()
    
    products = database.get_all_products(include_inactive=True)
    print(f"Total Products Found: {len(products)}")
    
    if len(products) == 0:
        print("⚠️ No products found in the database.")
    else:
        for p in products:
            print(f"- [{p['id']}] {p['name']} (Price: {p['price']}, Active: {p['is_active']})")

if __name__ == "__main__":
    verify_products()
