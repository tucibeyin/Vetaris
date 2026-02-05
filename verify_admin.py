import requests
import json
import time

BASE_URL = "http://localhost:8801"
SESSION_COOKIE = None

def login_admin():
    global SESSION_COOKIE
    print("🔹 Testing Admin Login...")
    url = f"{BASE_URL}/api/auth/login"
    data = {"email": "admin@vetaris.com", "password": "admin"}
    
    try:
        res = requests.post(url, json=data)
        if res.status_code == 200:
            print(f"✅ Login Success: {res.json()}")
            SESSION_COOKIE = res.cookies
            return True
        else:
            print(f"❌ Login Failed: {res.status_code} {res.text}")
            return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def check_auth_me():
    print("🔹 Checking Auth Status...")
    url = f"{BASE_URL}/api/auth/me"
    res = requests.get(url, cookies=SESSION_COOKIE)
    if res.status_code == 200 and res.json().get('is_admin'):
        print(f"✅ Auth Verified: Admin Access Granted")
    else:
        print(f"❌ Auth Failed: {res.text}")

def create_product():
    print("🔹 Testing Product Creation...")
    url = f"{BASE_URL}/api/products"
    data = {
        "name": "Test Vitamin Auto",
        "price": 99.99,
        "image": "/images/test.png",
        "description": "Auto created product",
        "category": "Test",
        "stock": 50
    }
    
    res = requests.post(url, json=data, cookies=SESSION_COOKIE)
    if res.status_code == 201:
        product = res.json()
        print(f"✅ Product Created: ID {product.get('id')} - {product.get('name')}")
        return product.get('id')
    else:
        print(f"❌ Create Failed: {res.status_code} {res.text}")
        return None

def verify_public_list(product_id):
    print("🔹 Verifying Public Product List...")
    url = f"{BASE_URL}/api/products"
    res = requests.get(url) # No cookies/public
    
    if res.status_code == 200:
        products = res.json()
        found = any(p['id'] == product_id for p in products)
        if found:
            print(f"✅ Success: New product found in public list.")
        else:
            print(f"❌ Failed: New product NOT found in list.")
    else:
        print(f"❌ Public List Failed: {res.status_code}")

def run_tests():
    # Wait for server to start if running alongside
    time.sleep(2)
    
    if login_admin():
        check_auth_me()
        pid = create_product()
        if pid:
            verify_public_list(pid)

if __name__ == "__main__":
    run_tests()
