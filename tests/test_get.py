"""
Test script to verify GET endpoints are working after pagination fix
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8001"

async def test_get_endpoints():
    """Test all GET endpoints in inventory service"""
    async with httpx.AsyncClient() as client:
        print("🔍 Testing GET endpoints after pagination fix...")
        
        # 1. Test Stores
        print("\n1. Testing GET /stores...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/stores")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {data['data']['total']} stores")
                print(f"   ✅ Page {data['data']['page']} of {data['data']['pages']}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # 2. Test Products
        print("\n2. Testing GET /products...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/products")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {data['data']['total']} products")
                print(f"   ✅ Page {data['data']['page']} of {data['data']['pages']}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # 3. Test Inventory
        print("\n3. Testing GET /inventory...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/inventory")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {data['data']['total']} inventory items")
                print(f"   ✅ Page {data['data']['page']} of {data['data']['pages']}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # 4. Test Sales
        print("\n4. Testing GET /sales...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/sales")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {data['data']['total']} sales transactions")
                print(f"   ✅ Page {data['data']['page']} of {data['data']['pages']}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # 5. Test Restock Requests
        print("\n5. Testing GET /restock-requests...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/restock-requests")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Found {data['data']['total']} restock requests")
                print(f"   ✅ Page {data['data']['page']} of {data['data']['pages']}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # 6. Test Analytics
        print("\n6. Testing GET /analytics...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/analytics/inventory-summary")
            print(f"   Inventory Summary: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Analytics working")
            else:
                print(f"   ❌ Error: {response.text}")
                
            response = await client.get(f"{BASE_URL}/api/v1/analytics/low-stock-alerts")
            print(f"   Low Stock Alerts: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Low stock alerts working")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # 7. Test Pagination
        print("\n7. Testing pagination...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/stores?page=1&size=2")
            print(f"   Stores with pagination: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Page 1: {len(data['data']['items'])} items")
                print(f"   ✅ Total: {data['data']['total']}, Pages: {data['data']['pages']}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print("\n🎯 GET endpoints test completed!")
        print("   All endpoints should now return 200 with proper pagination!")

if __name__ == "__main__":
    asyncio.run(test_get_endpoints())