import json
import os
import psycopg2
from src.database import get_db_connection

PRODUCTS_FILE = 'data/products.json'

def migrate_products():
    print("🚀 Starting Product Migration...")

    if not os.path.exists(PRODUCTS_FILE):
        print(f"❌ Product file not found: {PRODUCTS_FILE}")
        return

    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load JSON: {e}")
        return

    conn = get_db_connection()
    if not conn:
        print("❌ DB Connection failed")
        return

    try:
        cur = conn.cursor()
        
        count = 0
        for p in products:
            # Check if product exists by name to avoid duplicates during re-runs
            cur.execute("SELECT id FROM products WHERE name = %s", (p['name'],))
            existing = cur.fetchone()
            
            if existing:
                print(f"⚠️ Skipped (Already exists): {p['name']}")
                continue

            # Insert product
            cur.execute("""
                INSERT INTO products (name, price, image, description, category, stock, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                p['name'],
                p['price'],
                p['image'],
                p.get('description', ''),
                p.get('category', 'General'),
                100, # Default stock
                True
            ))
            count += 1
            print(f"✅ Migrated: {p['name']}")

        conn.commit()
        cur.close()
        conn.close()
        print(f"🎉 Migration Complete! Added {count} products.")

    except Exception as e:
        print(f"❌ Database error: {e}")
        if conn: conn.close()

if __name__ == "__main__":
    migrate_products()
