from src import database

print("--- Initializing Database Tables ---")
try:
    database.init_db()
    print("✅ Tables initialized successfully (or already existed).")
except Exception as e:
    print(f"❌ Failed to initialize tables: {e}")
