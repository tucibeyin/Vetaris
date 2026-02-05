import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import database

def fix_images():
    print("Connecting to database...")
    database.init_db()
    conn = database.get_db_connection()
    if not conn:
        print("Failed to connect to DB")
        return

    cur = conn.cursor()
    
    # Map Product Name -> Correct Image Path
    updates = [
        ('/images/formula-a.png', 'Vetaris Formül A'),
        ('/images/formula-b.png', 'Vetaris Formül B'),
        ('/images/spray.png', 'Vetaris Bakım Spreyi')
    ]
    
    print("Updating image paths...")
    for img, name in updates:
        cur.execute("UPDATE products SET image = %s WHERE name = %s", (img, name))
        if cur.rowcount > 0:
            print(f"✅ Updated {name} -> {img}")
        else:
            print(f"⚠️ Product not found: {name}")
        
    conn.commit()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    fix_images()
