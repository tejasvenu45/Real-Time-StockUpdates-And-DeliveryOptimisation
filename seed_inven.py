"""
Add existing products to warehouse inventory
"""
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from services.common.database import db_manager

async def add_products_to_warehouse():
    """Add all existing products to warehouse inventory"""
    print("📦 Adding products to warehouse inventory...")
    
    try:
        await db_manager.connect()
        
        # Get all products from catalog
        products = await db_manager.find_many("products", {})
        print(f"Found {len(products)} products in catalog")
        
        # Get existing warehouse inventory
        existing_warehouse = await db_manager.find_many("warehouse_inventory", {})
        existing_product_ids = {item["product_id"] for item in existing_warehouse}
        
        # Add missing products to warehouse
        added_count = 0
        for product in products:
            product_id = product["product_id"]
            
            if product_id not in existing_product_ids:
                # Calculate storage requirements based on product
                weight = product.get("weight", 1.0)
                dimensions = product.get("dimensions", {})
                volume = (dimensions.get("length", 10) * 
                         dimensions.get("width", 10) * 
                         dimensions.get("height", 10)) / 1000000  # Convert to m³
                
                warehouse_item = {
                    "product_id": product_id,
                    "available_stock": 500,  # Default stock level
                    "reserved_stock": 0,
                    "reorder_threshold": 50,
                    "max_capacity": 1000,
                    "location": f"W{(added_count % 10) + 1}-A{(added_count % 5) + 1}",  # Auto-assign location
                    "last_restock_date": "2025-07-06T00:00:00Z",
                    "product_weight": weight,
                    "product_volume": volume
                }
                
                await db_manager.insert_one("warehouse_inventory", warehouse_item)
                print(f"   ✅ Added to warehouse: {product_id} ({product.get('name', 'Unknown')})")
                print(f"      - Stock: 500 units, Location: {warehouse_item['location']}")
                added_count += 1
            else:
                print(f"   ⚠️ Already in warehouse: {product_id}")
        
        print(f"\n✅ Warehouse update complete!")
        print(f"   - Products in catalog: {len(products)}")
        print(f"   - Added to warehouse: {added_count}")
        print(f"   - Total warehouse inventory: {len(existing_warehouse) + added_count}")
        
        # Show current warehouse inventory
        print(f"\n📋 Current Warehouse Inventory:")
        warehouse_items = await db_manager.find_many("warehouse_inventory", {})
        for item in warehouse_items[:5]:  # Show first 5
            print(f"   - {item['product_id']}: {item['available_stock']} units at {item['location']}")
        if len(warehouse_items) > 5:
            print(f"   ... and {len(warehouse_items) - 5} more products")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating warehouse: {e}")
        return False
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    success = asyncio.run(add_products_to_warehouse())
    if success:
        print("\n🚀 All products are now available in warehouse!")
        print("   You can now create manual stock requests for any product.")
    else:
        print("\n⚠️ Setup failed. Check the error messages above.")