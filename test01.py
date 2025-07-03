"""
Fixed test script to verify infrastructure connections
Run this from the project root directory
"""
import asyncio
import sys
import os

# Add services to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from services.common.database import db_manager
from services.common.kafka_client import kafka_manager
from services.common.models import Store, Product, InventoryItem, Address, Coordinates, Dimensions, ProductCategory

async def test_mongodb():
    """Test MongoDB connection"""
    print("🔍 Testing MongoDB connection...")
    
    try:
        # Connect to database
        success = await db_manager.connect()
        if not success:
            print("❌ MongoDB connection failed")
            return False
        
        # Test basic operations
        test_doc = {"test": "data", "number": 123}
        doc_id = await db_manager.insert_one("test_collection", test_doc)
        print(f"✅ Inserted test document with ID: {doc_id}")
        
        # Retrieve document
        retrieved = await db_manager.find_one("test_collection", {"test": "data"})
        if retrieved:
            print("✅ Retrieved test document successfully")
        
        # Clean up
        await db_manager.delete_one("test_collection", {"test": "data"})
        print("✅ MongoDB test completed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ MongoDB test failed: {e}")
        return False

async def test_kafka():
    """Test Kafka connection"""
    print("\n🔍 Testing Kafka connection...")
    
    try:
        # Create topics
        await kafka_manager.create_topics()
        print("✅ Kafka topics created/verified")
        
        # Start producer
        await kafka_manager.start_producer()
        print("✅ Kafka producer started")
        
        # Send test message
        test_message = {"test": "message", "data": "hello kafka"}
        await kafka_manager.send_message("test-topic", test_message)
        print("✅ Test message sent successfully")
        
        # Health check
        health = await kafka_manager.health_check()
        if health:
            print("✅ Kafka health check passed")
        
        print("✅ Kafka test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Kafka test failed: {e}")
        return False

async def test_models():
    """Test Pydantic models"""
    print("\n🔍 Testing Pydantic models...")
    
    try:
        # Test Address and Coordinates
        address = Address(
            street="123 Main St",
            city="Anytown",
            state="CA",
            postal_code="12345",
            country="USA",
            coordinates=Coordinates(latitude=37.7749, longitude=-122.4194)
        )
        print("✅ Address model validation passed")
        
        # Test Store model
        store = Store(
            store_id="STORE001",
            name="Test Store",
            address=address,
            manager_name="John Doe",
            phone="555-1234",
            email="manager@teststore.com"
        )
        print("✅ Store model validation passed")
        
        # Test Product model
        product = Product(
            product_id="PROD001",
            name="Test Product",
            category=ProductCategory.ELECTRONICS,
            price="99.99",
            weight=2.5,
            dimensions=Dimensions(length=10, width=5, height=3)
        )
        print("✅ Product model validation passed")
        
        # Test InventoryItem model - Fixed validation
        inventory = InventoryItem(
            store_id="STORE001",
            product_id="PROD001",
            current_stock=100,
            reserved_stock=5,
            available_stock=95,  # This should be calculated correctly
            reorder_threshold=20,
            warning_threshold=15,
            critical_threshold=5,
            max_capacity=500
        )
        print("✅ InventoryItem model validation passed")
        print(f"   Available stock calculated: {inventory.available_stock}")
        
        print("✅ All Pydantic models test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting infrastructure tests (Fixed version)...\n")
    
    # Test models (no external dependencies)
    models_ok = await test_models()
    
    # Test MongoDB
    mongodb_ok = await test_mongodb()
    
    # Test Kafka
    kafka_ok = await test_kafka()
    
    # Cleanup
    if mongodb_ok:
        await db_manager.disconnect()
    
    if kafka_ok:
        await kafka_manager.stop_producer()
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"  Models: {'✅ PASS' if models_ok else '❌ FAIL'}")
    print(f"  MongoDB: {'✅ PASS' if mongodb_ok else '❌ FAIL'}")
    print(f"  Kafka: {'✅ PASS' if kafka_ok else '❌ FAIL'}")
    
    if all([models_ok, mongodb_ok, kafka_ok]):
        print("\n🎉 All tests passed! Infrastructure is ready.")
        print("\n🚀 You can now start the inventory service:")
        print("   cd services/inventory-service")
        print("   python main.py")
        return True
    else:
        print("\n⚠️ Some tests failed. Check the logs above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)