"""
Final test after all fixes (V2)
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8001"

async def test_final_v2():
    """Test all critical functions using fresh data"""
    async with httpx.AsyncClient() as client:
        print("🔁 Running final test with new store and product IDs...")

        # 1. Root check
        print("\n1. Checking root endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/")
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📡 Message: {response.json().get('message')}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

        # 2. Store creation
        store_data = {
            "store_id": "teststore01",
            "name": "Test Store V2",
            "address": {
                "street": "456 Version St",
                "city": "Testville",
                "state": "TS",
                "postal_code": "99999",
                "country": "Testland",
                "coordinates": {
                    "latitude": 12.9711,
                    "longitude": 77.5969
                }
            },
            "manager_name": "Mr. Test",
            "phone": "123-456-7890",
            "email": "testv2@store.com"
        }
        print("\n2. Creating store...")
        try:
            response = await client.post(f"{BASE_URL}/api/v1/stores", json=store_data)
            print(f"   ✅ Status: {response.status_code}")
            print(f"   🏪 Store ID: {response.json().get('data', {}).get('store_id')}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

        # 3. Product creation
        product_data = {
            "product_id": "testproduct01",
            "name": "Test Product V2",
            "category": "electronics",
            "price": "299.99",
            "weight": 2.5,
            "dimensions": {
                "length": 20,
                "width": 10,
                "height": 5
            }
        }
        print("\n3. Creating product...")
        try:
            response = await client.post(f"{BASE_URL}/api/v1/products", json=product_data)
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📦 Product ID: {response.json().get('data', {}).get('product_id')}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

        # 4. Inventory creation (no available_stock)
        inventory_data = {
            "store_id": "teststore01",
            "product_id": "testproduct01",
            "current_stock": 120,
            "reserved_stock": 10,
            "reorder_threshold": 30,
            "warning_threshold": 20,
            "critical_threshold": 10,
            "max_capacity": 200
        }
        print("\n4. Creating inventory item...")
        try:
            response = await client.post(f"{BASE_URL}/api/v1/inventory", json=inventory_data)
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📊 Inventory ID: {response.json().get('data', {}).get('inventory_id')}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

        # 5. Record sale
        sale_data = {
            "store_id": "teststore01",
            "product_id": "testproduct01",
            "quantity": 3,
            "unit_price": "299.99",
            "discount": "0.00",
            "tax": "24.00"
        }
        print("\n5. Recording sale...")
        try:
            response = await client.post(f"{BASE_URL}/api/v1/sales", json=sale_data)
            print(f"   ✅ Status: {response.status_code}")
            print(f"   🧾 Transaction ID: {response.json().get('data', {}).get('transaction_id')}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

        print("\n🎉 Final test (V2) completed! Check above for any ❌.")

if __name__ == "__main__":
    asyncio.run(test_final_v2())
