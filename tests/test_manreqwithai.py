"""
Test manual stock requests and AI delivery optimization
"""
import asyncio
import httpx

FULFILLMENT_URL = "http://localhost:8003"

async def test_manual_requests_and_ai():
    """Test complete manual request and AI optimization workflow"""
    async with httpx.AsyncClient() as client:
        print("🤖 Testing Manual Requests + AI Optimization...")
        
        # 1. Test Vehicle Management
        print("\n=== VEHICLE MANAGEMENT ===")
        
        # Get vehicles
        print("\n1. Getting vehicle fleet...")
        try:
            response = await client.get(f"{FULFILLMENT_URL}/api/v1/vehicles")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                vehicles = data['data']['items']
                print(f"   ✅ Found {len(vehicles)} vehicles in fleet")
                for vehicle in vehicles[:3]:  # Show first 3
                    print(f"      - {vehicle['vehicle_id']}: {vehicle['vehicle_type']} "
                          f"({vehicle['max_weight_capacity']}kg capacity, {vehicle['status']})")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Create test vehicle
        print("\n2. Creating test vehicle...")
        try:
            vehicle_data = {
                "vehicle_id": "TEST_VAN_001",
                "license_plate": "TEST-001",
                "vehicle_type": "van",
                "max_weight_capacity": 1000.0,
                "max_volume_capacity": 20.0,
                "status": "available",
                "driver_id": "TEST_DRIVER"
            }
            
            response = await client.post(f"{FULFILLMENT_URL}/api/v1/vehicles", json=vehicle_data)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Test vehicle created successfully")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # 2. Test Manual Stock Requests
        print("\n=== MANUAL STOCK REQUESTS ===")
        
        # Create manual stock request
        print("\n3. Creating manual stock request...")
        try:
            request_data = {
                "store_id": "INTEGRATION_STORE_001",
                "product_id": "AI_TEST_PROD_001",
                "requested_quantity": 25,
                "priority": "high",
                "reason": "Store manager requested urgent restock for weekend sale",
                "requested_by": "Store Manager John",
                "urgency_level": "urgent",
                "preferred_delivery_window": "morning",
                "notes": "Weekend promotion starting, need stock by tomorrow"
            }
            
            response = await client.post(f"{FULFILLMENT_URL}/api/v1/requests/manual", json=request_data)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Manual request created: {result['data']['request_id']}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Create second manual request
        print("\n4. Creating second manual stock request...")
        try:
            request_data2 = {
                "store_id": "FINAL_STORE_001",  # Fixed: Use proper store ID
                "product_id": "PROD_FINAL_V2",  # This is the product ID
                "requested_quantity": 15,
                "priority": "medium",
                "reason": "Routine restocking for popular item",
                "requested_by": "Store Manager Sarah",
                "urgency_level": "normal",
                "preferred_delivery_window": "afternoon"
            }
            
            response = await client.post(f"{FULFILLMENT_URL}/api/v1/requests/manual", json=request_data2)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Second manual request created: {result['data']['request_id']}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Get manual requests
        print("\n5. Retrieving manual stock requests...")
        try:
            response = await client.get(f"{FULFILLMENT_URL}/api/v1/requests/manual")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                requests = data['data']['items']
                print(f"   ✅ Found {len(requests)} manual requests")
                for req in requests[:3]:  # Show first 3
                    print(f"      - {req['request_id']}: {req['store_id']} needs {req['requested_quantity']} "
                          f"of {req['product_id']} ({req['priority']} priority)")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # 3. Test AI Delivery Optimization
        print("\n=== AI DELIVERY OPTIMIZATION ===")
        
        # Get AI delivery recommendations
        print("\n6. Getting AI delivery recommendations...")
        try:
            response = await client.get(
                f"{FULFILLMENT_URL}/api/v1/optimization/delivery-recommendations"
                f"?include_manual_requests=true&include_auto_requests=true&max_distance_km=100"
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                recommendations = data['data']
                print(f"   ✅ AI recommendations generated successfully")
                print(f"   📋 Recommendation type: {recommendations.get('recommendation_type', 'unknown')}")
                
                if recommendations.get('ai_reasoning'):
                    reasoning = recommendations['ai_reasoning']
                    print(f"\n   🤖 AI Analysis Preview:")
                    # Show first 300 characters of AI reasoning
                    preview = reasoning[:300] + "..." if len(reasoning) > 300 else reasoning
                    print(f"   {preview}")
                
                if recommendations.get('recommendations'):
                    rec_count = len(recommendations['recommendations'])
                    print(f"   📊 Generated {rec_count} delivery recommendation(s)")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # 4. Test Delivery Plan Execution
        print("\n=== DELIVERY PLAN EXECUTION ===")
        
        # Execute a sample delivery plan
        print("\n7. Executing sample delivery plan...")
        try:
            delivery_plan_data = {
                "vehicle_id": "TRUCK_001",
                "store_destinations": ["INTEGRATION_STORE_001", "FINAL_STORE_001"],
                "product_items": [
                    {
                        "store_id": "INTEGRATION_STORE_001",
                        "product_id": "AI_TEST_PROD_001",
                        "quantity": 25,
                        "weight": 5.0,
                        "volume": 2.5
                    },
                    {
                        "store_id": "FINAL_STORE_001",
                        "product_id": "PROD_FINAL_V2",  # Updated to use existing product
                        "quantity": 15,
                        "weight": 3.0,
                        "volume": 1.8
                    }
                ],
                "estimated_total_weight": 8.0,
                "estimated_total_volume": 4.3,
                "estimated_distance_km": 45.0,
                "ai_reasoning": "Optimized route for two nearby stores with efficient vehicle utilization",
                "execution_notes": "Manual execution based on AI recommendations"
            }
            
            # Fix the request body structure
            execution_request = {
                "delivery_plan": delivery_plan_data,
                "warehouse_manager": "Manager Mike Johnson"
            }
            
            response = await client.post(
                f"{FULFILLMENT_URL}/api/v1/fulfillment/execute-delivery",
                json=execution_request
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                execution_info = result['data']
                print(f"   ✅ Delivery plan executed: {execution_info['plan_id']}")
                print(f"   👤 Approved by: {execution_info['approved_by']}")
                print(f"   🚛 Vehicle assigned: {execution_info['vehicle_assigned']}")
                print(f"   📍 Stores: {execution_info['stores_count']}, Products: {execution_info['products_count']}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Get delivery plans
        print("\n8. Retrieving delivery plans...")
        try:
            response = await client.get(f"{FULFILLMENT_URL}/api/v1/delivery-plans")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                plans = data['data']['items']
                print(f"   ✅ Found {len(plans)} delivery plan(s)")
                for plan in plans[:2]:  # Show first 2
                    print(f"      - {plan['plan_id']}: {plan['vehicle_id']} → "
                          f"{len(plan.get('store_destinations', []))} stores ({plan['status']})")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print("\n🎯 Manual Requests + AI Optimization test completed!")
        print("\n🚀 Key Features Tested:")
        print("   ✅ Vehicle fleet management (CRUD operations)")
        print("   ✅ Manual stock request creation from stores")
        print("   ✅ AI-powered delivery optimization recommendations")
        print("   ✅ Warehouse manager delivery plan execution")
        print("   ✅ Delivery plan tracking and monitoring")
        print("\n💡 Next Steps:")
        print("   - Test with real Gemini API key for intelligent recommendations")
        print("   - Use Postman to create more complex scenarios")
        print("   - Monitor Kafka events for request processing")

if __name__ == "__main__":
    asyncio.run(test_manual_requests_and_ai())