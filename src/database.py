import os
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import uuid
import time
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "vetaris")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "password")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if not conn:
        print("Could not connect to database for initialization.")
        return

    try:
        cur = conn.cursor()
        
        # Create Users Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create Sessions Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            );
        """)

        # Create Products Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                image VARCHAR(255),
                description TEXT,
                category VARCHAR(100),
                stock INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create Orders Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                total_amount DECIMAL(10, 2) NOT NULL,
                status VARCHAR(50) DEFAULT 'Hazırlanıyor',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create Order Items Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(id),
                product_id INTEGER NOT NULL,
                product_name VARCHAR(255) NOT NULL,
                quantity INTEGER NOT NULL,
                price_at_purchase DECIMAL(10, 2) NOT NULL
            );
        """)

        # Create Blog Posts Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                slug VARCHAR(255) UNIQUE NOT NULL,
                content TEXT,
                image VARCHAR(255),
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_published BOOLEAN DEFAULT TRUE
            );
        """)
        
        # Check/Add is_admin column if it doesn't exist (for migration)
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;")
        except Exception as e:
            print(f"Notice: Could not alter table (might already exist or other issue): {e}")

        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")

def create_user(email, password):
    # ... (existing code unchanged) ...
    conn = get_db_connection()
    if not conn:
        raise Exception("Database connection failed")

    try:
        cur = conn.cursor()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id, email",
            (email, password_hash)
        )
        user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ DB: New user created - Email: {email}, ID: {user[0]}")
        return user
    except psycopg2.IntegrityError:
        conn.rollback()
        conn.close()
        print(f"⚠️ DB: Duplicate registration attempt for {email}")
        raise ValueError("User already exists") 
    except Exception as e:
        conn.close()
        print(f"❌ DB: Error creating user {email}: {e}")
        raise Exception(f"Database error: {str(e)}")

# ... (keep existing get_user_by_email, verify_password, create_session, get_session, delete_session) ...

def create_order(user_id, items, total_amount):
    conn = get_db_connection()
    if not conn:
        raise Exception("Database connection failed")

    try:
        cur = conn.cursor()
        
        # 1. Create Order
        cur.execute(
            "INSERT INTO orders (user_id, total_amount) VALUES (%s, %s) RETURNING id",
            (user_id, total_amount)
        )
        order_id = cur.fetchone()[0]
        
        # 2. Insert Items
        for item in items:
            cur.execute("""
                INSERT INTO order_items (order_id, product_id, product_name, quantity, price_at_purchase)
                VALUES (%s, %s, %s, %s, %s)
            """, (order_id, item['id'], item['name'], item['quantity'], item['price']))
            
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ DB: Order created - OrderID: {order_id}, UserID: {user_id}")
        return order_id
    except Exception as e:
        # conn.rollback() # Context manager or explicit rollback would be better but keeping simple
        print(f"❌ DB: Error creating order: {e}")
        if conn: conn.close()
        raise e

def get_user_orders(user_id):
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get Orders
        cur.execute("""
            SELECT * FROM orders 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        orders = cur.fetchall()
        
        # For each order, get items (Not super efficient but simple)
        for order in orders:
            cur.execute("""
                SELECT * FROM order_items WHERE order_id = %s
            """, (order['id'],))
            order['items'] = cur.fetchall()
            
        cur.close()
        conn.close()
        return orders
    except Exception as e:
        print(f"❌ DB: Error fetching orders: {e}")
        if conn: conn.close()
        return []

def get_user_by_email(email):
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return user
    except Exception as e:
        print(f"❌ DB: Error getting user {email}: {e}")
        conn.close()
        return None

def verify_password(stored_hash, password):
    result = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    return result

def create_session(user_id):
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        session_id = str(uuid.uuid4())
        # 30 days expiration
        expires_at = time.time() + (30 * 24 * 60 * 60) 
        
        cur.execute(
            "INSERT INTO sessions (session_id, user_id, expires_at) VALUES (%s, %s, to_timestamp(%s))",
            (session_id, user_id, expires_at)
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ DB: Session created for UserID: {user_id}")
        return session_id
    except Exception as e:
        print(f"❌ DB: Error creating session: {e}")
        conn.close()
        return None

def get_session(session_id):
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT s.*, u.email, u.is_admin 
            FROM sessions s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.session_id = %s AND s.expires_at > CURRENT_TIMESTAMP
        """, (session_id,))
        session = cur.fetchone()
        cur.close()
        conn.close()
        return session
    except Exception as e:
        print(f"Error getting session: {e}")
        conn.close()
        return None

def delete_session(session_id):
    conn = get_db_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error deleting session: {e}")
        conn.close()

# --- Product Management ---

def get_all_products(include_inactive=False):
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = "SELECT * FROM products"
        if not include_inactive:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY id ASC"
        
        cur.execute(query)
        products = cur.fetchall()
        cur.close()
        conn.close()
        
        # Format types (Decimal to float) handled in server.py json_serial, 
        # but good to be aware.
        return products
    except Exception as e:
        print(f"Error getting products: {e}")
        conn.close()
        return []

def get_product(product_id):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cur.fetchone()
        cur.close()
        conn.close()
        return product
    except Exception as e:
        print(f"Error getting product {product_id}: {e}")
        conn.close()
        return None

def create_product(data):
    conn = get_db_connection()
    if not conn:
        raise Exception("DB Connection failed")
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            INSERT INTO products (name, price, image, description, category, stock, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            data.get('name'),
            data.get('price'),
            data.get('image'),
            data.get('description', ''),
            data.get('category', 'General'),
            data.get('stock', 0),
            data.get('is_active', True)
        ))
        product = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return product
    except Exception as e:
        print(f"Error creating product: {e}")
        conn.close()
        raise e

def update_product(product_id, data):
    conn = get_db_connection()
    if not conn:
        raise Exception("DB Connection failed")
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build dynamic query
        fields = []
        values = []
        for key, value in data.items():
            fields.append(f"{key} = %s")
            values.append(value)
        
        if not fields:
            return None # Nothing to update
            
        values.append(product_id)
        query = f"UPDATE products SET {', '.join(fields)} WHERE id = %s RETURNING *"
        
        cur.execute(query, tuple(values))
        product = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return product
    except Exception as e:
        print(f"Error updating product: {e}")
        conn.close()
        raise e

def delete_product(product_id):
    """Soft delete"""
    return update_product(product_id, {"is_active": False})

def get_all_orders():
    """Admin: Get all orders"""
    conn = get_db_connection()
    if not conn: return []
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT o.*, u.email as user_email 
            FROM orders o 
            LEFT JOIN users u ON o.user_id = u.id 
            ORDER BY o.created_at DESC
        """)
        orders = cur.fetchall()
        
        # Get items for each order
        for order in orders:
             cur.execute("SELECT * FROM order_items WHERE order_id = %s", (order['id'],))
             order['items'] = cur.fetchall()
             
        cur.close()
        conn.close()
        return orders
    except Exception as e:
        print(f"Error getting all orders: {e}")
        conn.close()
        return []

def update_order_status(order_id, status):
    conn = get_db_connection()
    if not conn: return None
    try:
        cur = conn.cursor()
        cur.execute("UPDATE orders SET status = %s WHERE id = %s", (status, order_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating order status: {e}")
        conn.close()
        return False

# --- Blog Management ---

def get_all_posts(public_only=False):
    conn = get_db_connection()
    if not conn: return []
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = "SELECT * FROM blog_posts"
        if public_only:
            query += " WHERE is_published = TRUE"
        query += " ORDER BY created_at DESC"
        cur.execute(query)
        posts = cur.fetchall()
        cur.close()
        conn.close()
        return posts
    except Exception as e:
        print(f"Error fetching posts: {e}")
        conn.close()
        return []

def get_post(post_id):
    conn = get_db_connection()
    if not conn: return None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Check if ID is int or slug
        if str(post_id).isdigit():
             cur.execute("SELECT * FROM blog_posts WHERE id = %s", (int(post_id),))
        else:
             cur.execute("SELECT * FROM blog_posts WHERE slug = %s", (post_id,))
             
        post = cur.fetchone()
        cur.close()
        conn.close()
        return post
    except Exception as e:
        print(f"Error fetching post {post_id}: {e}")
        conn.close()
        return None

def create_post(data):
    conn = get_db_connection()
    if not conn: return None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        slug = data.get('title').lower().replace(' ', '-').replace('ç','c').replace('ğ','g').replace('ı','i').replace('ö','o').replace('ş','s').replace('ü','u')
        # Simple slug deduplication could be added here
        
        cur.execute("""
            INSERT INTO blog_posts (title, slug, content, image, summary, is_published)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            data.get('title'),
            slug,
            data.get('content'),
            data.get('image'),
            data.get('summary', ''),
            data.get('is_published', True)
        ))
        post = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return post
    except Exception as e:
        print(f"Error creating post: {e}")
        conn.close()
        raise e

def update_post(post_id, data):
    conn = get_db_connection()
    if not conn: return None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        fields = []
        values = []
        for key, value in data.items():
            if key in ['title', 'content', 'image', 'summary', 'is_published']:
                fields.append(f"{key} = %s")
                values.append(value)
        
        if not fields: return None
        
        values.append(post_id)
        # Safe dynamic query
        query = f"UPDATE blog_posts SET {', '.join(fields)} WHERE id = %s RETURNING *"
        cur.execute(query, tuple(values))

        post = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return post
    except Exception as e:
        print(f"Error updating post: {e}")
        conn.close()
        raise e

def delete_post(post_id):
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM blog_posts WHERE id = %s", (post_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting post: {e}")
        conn.close()
        return False

