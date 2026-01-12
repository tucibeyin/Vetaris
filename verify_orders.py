import requests
import json
import sys

BASE_URL = "http://localhost:8801"
EMAIL = "test_order_user@vetaris.com"
PASSWORD = "password123"

def run_test():
    session = requests.Session()
    
    print(f"--- Vetaris Order System Verification ---")
    print(f"Target: {BASE_URL}")

    # 1. Register
    print(f"\n1. Registering user {EMAIL}...")
    try:
        res = session.post(f"{BASE_URL}/api/auth/register", json={"email": EMAIL, "password": PASSWORD})
        if res.status_code in [200, 201]:
            print("✅ Registration successful")
        elif res.status_code == 409:
             print("ℹ️ User already exists (OK)")
        else:
            print(f"❌ Registration failed: {res.status_code} {res.text}")
            return
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 2. Login
    print(f"\n2. Logging in...")
    res = session.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    if res.status_code == 200:
        print("✅ Login successful")
    else:
        print(f"❌ Login failed: {res.status_code} {res.text}")
        return

    # 3. Create Order
    print(f"\n3. Creating Order...")
    order_payload = {
        "items": [
            {"id": 1, "name": "Vetaris Formül A", "price": 450.00, "quantity": 1},
            {"id": 2, "name": "Vetaris Bakım Spreyi", "price": 150.00, "quantity": 2}
        ],
        "total": 750.00
    }
    
    res = session.post(f"{BASE_URL}/api/orders", json=order_payload)
    if res.status_code == 200:
        data = res.json()
        print(f"✅ Order Created! Order ID: {data.get('order_id')}")
    else:
        print(f"❌ Create Order failed: {res.status_code} {res.text}")
        return

    # 4. Get Orders
    print(f"\n4. Fetching Order History...")
    res = session.get(f"{BASE_URL}/api/orders")
    if res.status_code == 200:
        orders = res.json()
        print(f"✅ Orders fetched. Count: {len(orders)}")
        if len(orders) > 0:
            latest = orders[0]
            print(f"   Latest Order ID: {latest['id']}")
            print(f"   Total: {latest['total_amount']}")
            print(f"   Status: {latest['status']}")
            print(f"   Items: {len(latest['items'])}")
            for item in latest['items']:
                print(f"     - {item['product_name']} x{item['quantity']}")
        else:
            print("❌ No orders found!")
    else:
         print(f"❌ Get Orders failed: {res.status_code} {res.text}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    run_test()
