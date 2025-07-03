"""
Setup initial warehouse data for testing
Run this once to populate warehouse inventory
"""
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from services.common.database import db_manager

async def setup_warehouse_data():
    """Create initial warehouse inventory data"""
    print("🏭 Setting up warehouse data...")
    
    try:
        await db_manager.connect()
        
        # Sample warehouse inventory
        warehouse_inventory = [
            {
                "product_id": "PROD001",
                "available_stock": 1000,
                "reserved_stock": 0,
                "reorder_threshold": 100,
                "max_capacity": 2000,
                "location": "A1-A10",
                "last_restock_date": "2025-07-01T00:00:00Z"
            },
            {
                "product_id": "FIXED_PROD_001",
                "available_stock": 500,
                "reserved_stock": 0,
                "reorder_threshold": 50,
                "max_capacity": 1000,
                "location": "B1-B5",
                "last_restock_date": "2025-07-01T00:00:00Z"
            },
            {
                "product_id": "FINAL_PROD_001",
                "available_stock": 800,
                "reserved_stock": 0,
                "reorder_threshold": 80,
                "max_capacity": 1500,
                "location": "C1-C8",
                "last_restock_date": "2025-07-01T00:00:00Z"
            }
        ]
        
        # Clear existing warehouse inventory
        collection = db_manager.get_collection("warehouse_inventory")
        await collection.delete_many({})
        
        # Insert new warehouse inventory
        for item in warehouse_inventory:
            await db_manager.insert_one("warehouse_inventory", item)
            print(f"   ✅ Added warehouse stock for {item['product_id']}: {item['available_stock']} units")
        
        print(f"\n✅ Warehouse setup complete! Added {len(warehouse_inventory)} products to warehouse inventory.")
        
    except Exception as e:
        print(f"❌ Error setting up warehouse data: {e}")
        return False
    finally:
        await db_manager.disconnect()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(setup_warehouse_data())
    if success:
        print("\n🚀 Ready to start Fulfillment Service!")
    else:
        print("\n⚠️ Setup failed. Check the error messages above.")