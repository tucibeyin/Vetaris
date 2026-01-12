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
            SELECT s.*, u.email 
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
