"""
Seed vehicle data into the database
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from services.common.database import db_manager

async def seed_vehicle_data():
    """Create initial vehicle fleet data"""
    print("🚛 Setting up vehicle fleet data...")
    
    try:
        await db_manager.connect()
        
        # Sample vehicle fleet
        vehicles = [
            {
                "vehicle_id": "TRUCK_001",
                "license_plate": "WH-TRK-001",
                "vehicle_type": "truck",
                "max_weight_capacity": 2000.0,  # kg
                "max_volume_capacity": 40.0,    # cubic meters
                "current_weight": 0.0,
                "current_volume": 0.0,
                "status": "available",
                "driver_id": "DRIVER_001",
                "fuel_level": 85.0,
                "maintenance_due_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "created_at": datetime.utcnow()
            },
            {
                "vehicle_id": "TRUCK_002", 
                "license_plate": "WH-TRK-002",
                "vehicle_type": "truck",
                "max_weight_capacity": 1500.0,
                "max_volume_capacity": 35.0,
                "current_weight": 0.0,
                "current_volume": 0.0,
                "status": "available",
                "driver_id": "DRIVER_002",
                "fuel_level": 92.0,
                "maintenance_due_date": (datetime.utcnow() + timedelta(days=45)).isoformat(),
                "created_at": datetime.utcnow()
            },
            {
                "vehicle_id": "VAN_001",
                "license_plate": "WH-VAN-001", 
                "vehicle_type": "van",
                "max_weight_capacity": 800.0,
                "max_volume_capacity": 15.0,
                "current_weight": 0.0,
                "current_volume": 0.0,
                "status": "available",
                "driver_id": "DRIVER_003",
                "fuel_level": 78.0,
                "maintenance_due_date": (datetime.utcnow() + timedelta(days=20)).isoformat(),
                "created_at": datetime.utcnow()
            },
            {
                "vehicle_id": "VAN_002",
                "license_plate": "WH-VAN-002",
                "vehicle_type": "van", 
                "max_weight_capacity": 750.0,
                "max_volume_capacity": 12.0,
                "current_weight": 0.0,
                "current_volume": 0.0,
                "status": "maintenance",
                "driver_id": None,
                "fuel_level": 45.0,
                "maintenance_due_date": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow()
            },
            {
                "vehicle_id": "PICKUP_001",
                "license_plate": "WH-PK-001",
                "vehicle_type": "pickup",
                "max_weight_capacity": 500.0,
                "max_volume_capacity": 8.0,
                "current_weight": 0.0,
                "current_volume": 0.0,
                "status": "available",
                "driver_id": "DRIVER_004",
                "fuel_level": 95.0,
                "maintenance_due_date": (datetime.utcnow() + timedelta(days=60)).isoformat(),
                "created_at": datetime.utcnow()
            }
        ]
        
        # Clear existing vehicles
        collection = db_manager.get_collection("vehicles")
        await collection.delete_many({})
        
        # Insert new vehicles
        for vehicle in vehicles:
            await db_manager.insert_one("vehicles", vehicle)
            available_capacity = vehicle['max_weight_capacity'] - vehicle['current_weight']
            print(f"   ✅ Added {vehicle['vehicle_type']}: {vehicle['vehicle_id']} "
                  f"(Capacity: {vehicle['max_weight_capacity']}kg, Available: {available_capacity}kg)")
        
        print(f"\n✅ Vehicle fleet setup complete! Added {len(vehicles)} vehicles.")
        print("\n📊 Fleet Summary:")
        print(f"   - Trucks: 2 (Heavy duty delivery)")
        print(f"   - Vans: 2 (Medium capacity delivery)")  
        print(f"   - Pickup: 1 (Small/urgent delivery)")
        print(f"   - Available: {len([v for v in vehicles if v['status'] == 'available'])}")
        print(f"   - In Maintenance: {len([v for v in vehicles if v['status'] == 'maintenance'])}")
        
    except Exception as e:
        print(f"❌ Error setting up vehicle data: {e}")
        return False
    finally:
        await db_manager.disconnect()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(seed_vehicle_data())
    if success:
        print("\n🚀 Ready to test vehicle management!")
    else:
        print("\n⚠️ Setup failed. Check the error messages above.")