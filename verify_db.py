import os
import psycopg2
from dotenv import load_dotenv

# Load .env from the same directory or parent
load_dotenv()

print("--- Database Connection Test ---")
print(f"HOST: {os.getenv('DB_HOST')}")
print(f"NAME: {os.getenv('DB_NAME')}")
print(f"USER: {os.getenv('DB_USER')}")
print(f"PORT: {os.getenv('DB_PORT')}")
# Do not print password for security

try:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "vetaris"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "password"),
        port=os.getenv("DB_PORT", "5432")
    )
    print("\n✅ SUCCESS: Connected to PostgreSQL successfully!")
    
    cur = conn.cursor()
    cur.execute("SELECT version();")
    db_version = cur.fetchone()
    print(f"Database Version: {db_version[0]}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ FAILURE: Could not connect to database.")
    print(f"Error Details: {e}")
