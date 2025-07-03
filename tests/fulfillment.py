"""
Test script for Fulfillment Service
"""
import asyncio
import httpx

# ✅ Make sure this matches the actual running port of your fulfillment service
BASE_URL = "http://localhost:8003"

async def test_fulfillment_service():
    """Test the fulfillment service endpoints"""
    async with httpx.AsyncClient() as client:
        print("🤖 Testing Fulfillment Service...")
        
        # 1. Health Check Endpoint
        print("\n1. Testing health check...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                health = response.json()
                print(f"   Service: {health['service']} - {health['status']}")
                print(f"   Dependencies: {health.get('dependencies', {})}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        # 2. Root Endpoint
        print("\n2. Testing root endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                root = response.json()
                print(f"   Message: {root['message']}")
                print(f"   Features: {len(root['data']['features'])} AI features available")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        # 3. Fulfillment Requests Endpoint
        print("\n3. Testing fulfillment requests endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/fulfillment/requests")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Found {data['data']['total']} fulfillment requests")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        # 4. Warehouse Inventory Endpoint
        print("\n4. Testing warehouse inventory endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/warehouse/inventory")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Found {data['data']['total']} warehouse products")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        # 5. AI Product Recommendations
        print("\n5. Testing AI product recommendations...")

        # ✅ Make sure these IDs exist in your database (store and product)
        # You should have already created them using the inventory service
        recommendation_request = {
            "store_id": "FINAL_STORE_001",           # 🔁 Change if using different store
            "primary_product": "FINAL_PROD_001",     # 🔁 Change if using different product
            "delivery_context": {
                "vehicle_capacity": 1000,            # ✅ Make sure value is reasonable
                "delivery_window": "morning"         # ✅ Optional, but can customize
            }
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/optimization/product-recommendations",
                json=recommendation_request
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   AI recommendations generated successfully")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        # 6. Fulfillment Metrics
        print("\n6. Testing fulfillment metrics...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/analytics/fulfillment-metrics")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Fulfillment metrics retrieved successfully")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {e}")
        
        print("\n🎯 Fulfillment Service test completed!")
        print("\n🚀 Ready for advanced testing!")
        print("   Service URL: http://localhost:8003")
        print("   API Docs: http://localhost:8003/docs")
        print("   Key Features:")
        print("     - AI-powered product recommendations")
        print("     - Automatic restock request processing")
        print("     - Warehouse inventory management")
        print("     - Real-time Kafka event processing")

if __name__ == "__main__":
    asyncio.run(test_fulfillment_service())
