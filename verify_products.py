import requests
import json

BASE_URL = "http://localhost:8801"

def verify_products():
    print(f"--- Vetaris Products Verification ---")
    print(f"Target: {BASE_URL}/api/products")

    try:
        res = requests.get(f"{BASE_URL}/api/products")
        if res.status_code == 200:
            products = res.json()
            print(f"✅ Success! Retrieved {len(products)} products.")
            if len(products) > 0:
                print(f"Sample: {products[0].get('name')}")
        else:
            print(f"❌ Failed: {res.status_code} {res.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    verify_products()
