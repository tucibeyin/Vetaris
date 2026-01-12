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
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")

def create_user(email, password):
    conn = get_db_connection()
    if not conn:
        return None

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
        return user
    except psycopg2.IntegrityError:
        conn.rollback()
        conn.close()
        print("User with this email already exists.")
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        conn.close()
        return None

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
        print(f"Error getting user: {e}")
        conn.close()
        return None

def verify_password(stored_hash, password):
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))

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
        return session_id
    except Exception as e:
        print(f"Error creating session: {e}")
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
