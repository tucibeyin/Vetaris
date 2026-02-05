import psycopg2
from src.database import get_db_connection

def debug_admin():
    email = "admin@vetaris.com"
    conn = get_db_connection()
    if not conn:
        print("❌ Could not connect to database")
        return

    try:
        cur = conn.cursor()
        
        # Check User
        print(f"\n🔍 Inspecting User: {email}")
        cur.execute("SELECT id, email, is_admin, created_at FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        
        if user:
            print(f"✅ User Found:")
            print(f"ID: {user[0]}")
            print(f"Email: {user[1]}")
            print(f"Is Admin: {user[2]} (Type: {type(user[2])})")
            print(f"Created At: {user[3]}")
            
            # Check Sessions
            print(f"\n🔍 Checking Active Sessions for User ID {user[0]}:")
            cur.execute("SELECT session_id, expires_at FROM sessions WHERE user_id = %s", (user[0],))
            sessions = cur.fetchall()
            for s in sessions:
                print(f"Session: {s[0]} | Expires: {s[1]}")
        else:
            print("❌ User NOT found in database!")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_admin()
