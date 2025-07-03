"""
Debug script to see detailed error messages
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8001"

async def debug_service():
    """Debug the service to see actual error messages"""
    async with httpx.AsyncClient() as client:
        print("🔍 Debugging Inventory Service errors...")
        
        # 1. Test Root endpoint
        print("\n1. Testing root endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/")
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                print(f"   Error: {response.text}")
            else:
                print(f"   Success: {response.json()}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        # 2. Test Store Creation
        print("\n2. Testing store creation...")
        store_data = {
            "store_id": "DEBUG_STORE_001",
            "name": "Debug Store",
            "address": {
                "street": "123 Debug St",
                "city": "Debug City",
                "state": "DC",
                "postal_code": "12345",
                "country": "USA",
                "coordinates": {
                    "latitude": 40.7128,
                    "longitude": -74.0060
                }
            },
            "manager_name": "Debug Manager",
            "phone": "555-0123",
            "email": "debug@store.com"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/v1/stores", json=store_data)
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                print(f"   Error Response: {response.text}")
                print(f"   Response Headers: {response.headers}")
            else:
                result = response.json()
                print(f"   Success: {result}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        # 3. Test Inventory Creation (after ensuring store exists)
        print("\n3. Testing inventory creation...")
        inventory_data = {
            "store_id": "DEBUG_STORE_001",
            "product_id": "TEST_PROD_001",  # This was created successfully
            "current_stock": 100,
            "reserved_stock": 0,
            "available_stock": 100,
            "reorder_threshold": 20,
            "warning_threshold": 15,
            "critical_threshold": 5,
            "max_capacity": 200
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/v1/inventory", json=inventory_data)
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                print(f"   Error Response: {response.text}")
                try:
                    error_detail = response.json()
                    print(f"   Error Detail: {json.dumps(error_detail, indent=2)}")
                except:
                    pass
            else:
                result = response.json()
                print(f"   Success: {result}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        # 4. Test Sales (only if inventory exists)
        print("\n4. Testing sales...")
        sale_data = {
            "store_id": "DEBUG_STORE_001",
            "product_id": "TEST_PROD_001",
            "quantity": 5,
            "unit_price": "99.99",
            "discount": "0.00",
            "tax": "8.00"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/v1/sales", json=sale_data)
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                print(f"   Error Response: {response.text}")
            else:
                result = response.json()
                print(f"   Success: {result}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        # 5. Check service logs suggestion
        print("\n💡 Also check the service terminal/logs for detailed error messages!")
        print("   Look for stack traces and error details in the service output.")

if __name__ == "__main__":
    asyncio.run(debug_service())