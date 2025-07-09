"""
Inventory Service API Routes
REST API endpoints for inventory management
"""
import logging
from typing import Dict, Any, List, Optional, Callable
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from datetime import datetime
import httpx
from services.common.kafka_client import get_kafka_manager, KafkaManager
from services.common.database import DatabaseManager, get_database
from services.common.models import (
    Store, Product, InventoryItem, InventoryItemCreate, SaleTransaction, RestockRequest,
    StoreCreateRequest, ProductCreateRequest, InventoryUpdateRequest, SaleRequest,
    APIResponse, PaginatedResponse, Priority
)
from services.inventory_service.services.inventory_service import InventoryService

logger = logging.getLogger(__name__)

router = APIRouter()

def serialize_for_json(obj):
    """Helper function to serialize objects for JSON response"""
    from datetime import datetime
    from decimal import Decimal
    from bson import ObjectId
    import enum
    
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, enum.Enum):
        return obj.value
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj

async def get_inventory_service(db: DatabaseManager = Depends(get_database)) -> InventoryService:
    """Dependency injection for inventory service"""
    return InventoryService(db)

# =============================================================================
# STORE ENDPOINTS
# =============================================================================

@router.post("/stores", response_model=APIResponse)
async def create_store(
    store_data: StoreCreateRequest,
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a new store"""
    try:
        store_id = await service.create_store(store_data)
        return {
            "success": True,
            "message": "Store created successfully",
            "data": {"store_id": store_id},
            "timestamp": datetime.utcnow().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating store: {e}")
        raise HTTPException(status_code=500, detail="Failed to create store")

@router.get("/stores", response_model=APIResponse)
async def get_stores(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get all stores with pagination"""
    try:
        stores = await service.get_stores(page=page, size=size, status=status)
        total = await service.count_stores(status=status)
        
        return {
            "success": True,
            "message": "Stores retrieved successfully",
            "data": {
                "items": serialize_for_json(stores),
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error retrieving stores: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve stores")

@router.get("/stores/{store_id}", response_model=APIResponse)
async def get_store(
    store_id: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get a specific store by ID"""
    try:
        store = await service.get_store(store_id)
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        return {
            "success": True,
            "message": "Store retrieved successfully",
            "data": serialize_for_json(store),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving store {store_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve store")

@router.put("/stores/{store_id}", response_model=APIResponse)
async def update_store(
    store_id: str,
    store_data: StoreCreateRequest,
    service: InventoryService = Depends(get_inventory_service)
):
    """Update a store"""
    try:
        success = await service.update_store(store_id, store_data)
        if not success:
            raise HTTPException(status_code=404, detail="Store not found")
        
        return {
            "success": True,
            "message": "Store updated successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating store {store_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update store")

# =============================================================================
# PRODUCT ENDPOINTS
# =============================================================================

@router.post("/products", response_model=APIResponse)
async def create_product(
    product_data: ProductCreateRequest,
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a new product"""
    try:
        product_id = await service.create_product(product_data)
        return {
            "success": True,
            "message": "Product created successfully",
            "data": {"product_id": product_id},
            "timestamp": datetime.utcnow().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail="Failed to create product")

@router.get("/products", response_model=APIResponse)
async def get_products(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None),
    active_only: bool = Query(True),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get all products with pagination"""
    try:
        products = await service.get_products(
            page=page, 
            size=size, 
            category=category, 
            active_only=active_only
        )
        total = await service.count_products(category=category, active_only=active_only)
        
        return {
            "success": True,
            "message": "Products retrieved successfully",
            "data": {
                "items": serialize_for_json(products),
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error retrieving products: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve products")

@router.get("/products/{product_id}", response_model=APIResponse)
async def get_product(
    product_id: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get a specific product by ID"""
    try:
        product = await service.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "success": True,
            "message": "Product retrieved successfully",
            "data": serialize_for_json(product),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve product")

# =============================================================================
# INVENTORY ENDPOINTS
# =============================================================================

@router.post("/inventory", response_model=APIResponse)
async def create_inventory_item(
    inventory_data: InventoryItemCreate,
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a new inventory item"""
    try:
        inventory_id = await service.create_inventory_item(inventory_data)
        return {
            "success": True,
            "message": "Inventory item created successfully",
            "data": {"inventory_id": inventory_id},
            "timestamp": datetime.utcnow().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating inventory item: {e}")
        raise HTTPException(status_code=500, detail="Failed to create inventory item")

@router.get("/inventory", response_model=APIResponse)
async def get_inventory(
    store_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    low_stock_only: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get inventory items with filtering and pagination"""
    try:
        inventory_items = await service.get_inventory_items(
            store_id=store_id,
            product_id=product_id,
            low_stock_only=low_stock_only,
            page=page,
            size=size
        )
        total = await service.count_inventory_items(
            store_id=store_id,
            product_id=product_id,
            low_stock_only=low_stock_only
        )
        
        return {
            "success": True,
            "message": "Inventory retrieved successfully",
            "data": {
                "items": serialize_for_json(inventory_items),
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error retrieving inventory: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve inventory")

@router.get("/inventory/{store_id}/{product_id}", response_model=APIResponse)
async def get_inventory_item(
    store_id: str,
    product_id: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get specific inventory item"""
    try:
        inventory = await service.get_inventory_item(store_id, product_id)
        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        return {
            "success": True,
            "message": "Inventory item retrieved successfully",
            "data": serialize_for_json(inventory),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving inventory for {store_id}/{product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve inventory item")

@router.put("/inventory/{store_id}/{product_id}", response_model=APIResponse)
async def update_inventory(
    store_id: str,
    product_id: str,
    update_data: InventoryUpdateRequest,
    service: InventoryService = Depends(get_inventory_service)
):
    """Update inventory levels"""
    try:
        success = await service.update_inventory(store_id, product_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        return {
            "success": True,
            "message": "Inventory updated successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating inventory for {store_id}/{product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update inventory")

# =============================================================================
# SALES ENDPOINTS
# =============================================================================

@router.post("/sales", response_model=APIResponse)
async def record_sale(
    sale_data: SaleRequest,
    service: InventoryService = Depends(get_inventory_service)
):
    """Record a sale transaction"""
    try:
        transaction_id = await service.record_sale(sale_data)
        return {
            "success": True,
            "message": "Sale recorded successfully",
            "data": {"transaction_id": transaction_id},
            "timestamp": datetime.utcnow().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error recording sale: {e}")
        raise HTTPException(status_code=500, detail="Failed to record sale")

@router.get("/sales", response_model=APIResponse)
async def get_sales(
    store_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get sales transactions with filtering"""
    try:
        sales = await service.get_sales(
            store_id=store_id,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            size=size
        )
        total = await service.count_sales(
            store_id=store_id,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "success": True,
            "message": "Sales retrieved successfully",
            "data": {
                "items": serialize_for_json(sales),
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error retrieving sales: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sales")

# =============================================================================
# RESTOCK REQUEST ENDPOINTS
# =============================================================================

@router.post("/restock-requests", response_model=APIResponse)
async def create_restock_request(
    store_id: str,
    product_id: str,
    quantity: int,
    priority: Priority = Priority.MEDIUM,
    reason: str = "Manual request",
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a restock request"""
    try:
        request_id = await service.create_restock_request(
            store_id=store_id,
            product_id=product_id,
            quantity=quantity,
            priority=priority,
            reason=reason
        )
        return {
            "success": True,
            "message": "Restock request created successfully",
            "data": {"request_id": request_id},
            "timestamp": datetime.utcnow().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating restock request: {e}")
        raise HTTPException(status_code=500, detail="Failed to create restock request")

@router.get("/restock-requests", response_model=APIResponse)
async def get_restock_requests(
    store_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[Priority] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get restock requests with filtering"""
    try:
        requests = await service.get_restock_requests(
            store_id=store_id,
            status=status,
            priority=priority,
            page=page,
            size=size
        )
        total = await service.count_restock_requests(
            store_id=store_id,
            status=status,
            priority=priority
        )
        
        return {
            "success": True,
            "message": "Restock requests retrieved successfully",
            "data": {
                "items": serialize_for_json(requests),
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error retrieving restock requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve restock requests")

# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================

@router.get("/kafka/restock-messages")
async def fetch_restock_messages(kafka: KafkaManager = Depends(get_kafka_manager)) -> List[dict]:
    return await kafka.get_all_restock_messages()


@router.get("/analytics/inventory-summary", response_model=APIResponse)
async def get_inventory_summary(
    store_id: Optional[str] = Query(None),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get inventory summary analytics"""
    try:
        summary = await service.get_inventory_summary(store_id)
        return {
            "success": True,
            "message": "Inventory summary retrieved successfully",
            "data": serialize_for_json(summary),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting inventory summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get inventory summary")

@router.get("/analytics/low-stock-alerts", response_model=APIResponse)
async def get_low_stock_alerts(
    store_id: Optional[str] = Query(None),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get low stock alerts"""
    try:
        alerts = await service.get_low_stock_alerts(store_id)
        return {
            "success": True,
            "message": "Low stock alerts retrieved successfully",
            "data": serialize_for_json(alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting low stock alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get low stock alerts")

@router.post("/kafka/process-fulfillment")
async def process_fulfillment_requests(kafka: KafkaManager = Depends(get_kafka_manager)):
    await kafka.process_restock_requests_and_generate_fulfillments()
    return {"message": "Fulfillment events generated and sent"}

@router.get("/kafka/fulfillment-messages")
async def get_fulfillment_messages(kafka: KafkaManager = Depends(get_kafka_manager)):
    return kafka.fulfillment_messages
##VEhicels"""

@router.post("/vehicles")
async def create_vehicle(
    vehicle_data: Dict[str, Any] = Body(...),
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a new vehicle"""
    try:
        vehicle_id = await service.create_vehicle(vehicle_data)
        return {
            "success": True,
            "message": "Vehicle created successfully",
            "data": {"vehicle_id": vehicle_id},
            "timestamp": datetime.utcnow().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating vehicle: {e}")
        raise HTTPException(status_code=500, detail="Failed to create vehicle")

@router.get("/vehicles")
async def get_vehicles(
    status: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get vehicles with filtering"""
    try:
        vehicles = await service.get_vehicles(
            status=status,
            vehicle_type=vehicle_type,
            page=page,
            size=size
        )
        total = await service.count_vehicles(status=status, vehicle_type=vehicle_type)
        
        return {
            "success": True,
            "message": "Vehicles retrieved successfully",
            "data": {
                "items": serialize_for_json(vehicles),
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error retrieving vehicles: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve vehicles")

@router.get("/vehicles/{vehicle_id}")
async def get_vehicle(
    vehicle_id: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get specific vehicle by ID"""
    try:
        vehicle = await service.get_vehicle(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        return {
            "success": True,
            "message": "Vehicle retrieved successfully",
            "data": serialize_for_json(vehicle),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving vehicle {vehicle_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve vehicle")

@router.put("/vehicles/{vehicle_id}")
async def update_vehicle(
    vehicle_id: str,
    vehicle_data: Dict[str, Any] = Body(...),
    service: InventoryService = Depends(get_inventory_service)
):
    """Update vehicle information"""
    try:
        success = await service.update_vehicle(vehicle_id, vehicle_data)
        if not success:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        return {
            "success": True,
            "message": "Vehicle updated successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vehicle {vehicle_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update vehicle")

@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Delete a vehicle"""
    try:
        success = await service.delete_vehicle(vehicle_id)
        if not success:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        return {
            "success": True,
            "message": "Vehicle deleted successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vehicle {vehicle_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete vehicle")


# # @router.get("/kafka/vehicle-assignments")
# # async def assign_vehicles_to_fulfillment(service: InventoryService = Depends(get_inventory_service)):


#     """Assign vehicles to stores based on fulfillment request volume"""
#     async with httpx.AsyncClient() as client:
#         # 1. Get all available vehicles
#         vehicles_response = await client.get("http://localhost:8001/api/v1/vehicles?available_only=true")
#         vehicles = vehicles_response.json()["data"]["items"]

#         # 2. Get fulfillment messages
#         fulfillment_response = await client.get("http://localhost:8001/api/v1/kafka/fulfillment-messages")
#         fulfillments = fulfillment_response.json()

#     # 3. Preprocess volume per fulfillment
#     assignments = []
#     vehicle_pool = []

#     for v in vehicles:
#         vehicle_pool.append({
#             "vehicle_id": v["vehicle_id"],
#             "available_volume": v["available_volume_capacity"],
#             "available_weight": v["available_weight_capacity"]
#         })

#     # Sort vehicles descending by available volume
#     vehicle_pool.sort(key=lambda v: v["available_volume"], reverse=True)

#     for fulfillment in fulfillments:
#         store_id = fulfillment["store_id"]
#         request_id = fulfillment["request_id"]
#         products = fulfillment["products"]

#         total_volume = sum(p["volume"] * p["requested_quantity"] for p in products)

#         assigned_vehicle = None
#         for vehicle in vehicle_pool:
#             if vehicle["available_volume"] >= total_volume:
#                 assigned_vehicle = vehicle
#                 vehicle["available_volume"] -= total_volume  # Update remaining volume
#                 break

#         if assigned_vehicle:
#             assignments.append({
#                 "store_id": store_id,
#                 "request_id": request_id,
#                 "vehicle_id": assigned_vehicle["vehicle_id"],
#                 "total_volume_needed": total_volume,
#                 "vehicle_remaining_volume": assigned_vehicle["available_volume"]
#             })
#         else:
#             assignments.append({
#                 "store_id": store_id,
#                 "request_id": request_id,
#                 "vehicle_id": None,
#                 "total_volume_needed": total_volume,
#                 "error": "No vehicle with enough volume available"
#             })

#     return {
#         "success": True,
#         "message": "Vehicle assignments completed",
#         "data": {
#             "assignments": assignments,
#             "unassigned_fulfillments": [a for a in assignments if a["vehicle_id"] is None]
#         }
#     }
@router.get("/kafka/vehicle-assignments")
async def assign_vehicles_to_fulfillment(service: InventoryService = Depends(get_inventory_service)):
    """Assign multiple vehicles to fulfillments based on total volume needs"""
    async with httpx.AsyncClient() as client:
        # 1. Get available vehicles
        vehicles_response = await client.get("http://localhost:8001/api/v1/vehicles?available_only=true")
        vehicles = vehicles_response.json()["data"]["items"]

        # 2. Get fulfillment requests
        fulfillment_response = await client.get("http://localhost:8001/api/v1/kafka/fulfillment-messages")
        fulfillments = fulfillment_response.json()

    # 3. Prepare vehicle pool
    vehicle_pool = []
    for v in vehicles:
        vehicle_pool.append({
            "vehicle_id": v["vehicle_id"],
            "available_volume": v["available_volume_capacity"]
        })

    # Sort vehicles by descending volume
    vehicle_pool.sort(key=lambda v: v["available_volume"], reverse=True)

    assignments = []
    unassigned = []

    # 4. Loop through each fulfillment
    for fulfillment in fulfillments:
        store_id = fulfillment["store_id"]
        request_id = fulfillment["request_id"]
        products = fulfillment["products"]

        # Calculate total volume needed
        total_volume = sum(p["volume"] * p["requested_quantity"] for p in products)

        used_vehicles = []
        used_capacity = 0.0

        for vehicle in vehicle_pool:
            if used_capacity >= total_volume:
                break

            remaining = total_volume - used_capacity
            take_volume = min(remaining, vehicle["available_volume"])

            if take_volume > 0:
                used_vehicles.append({
                    "vehicle_id": vehicle["vehicle_id"],
                    "assigned_volume": take_volume,
                    "leftover_volume": vehicle["available_volume"] - take_volume
                })
                used_capacity += take_volume
                vehicle["available_volume"] -= take_volume  # Update vehicle pool

        if used_capacity >= total_volume:
            assignments.append({
                "store_id": store_id,
                "request_id": request_id,
                "total_volume_needed": total_volume,
                "total_volume_assigned": used_capacity,
                "vehicles_assigned": used_vehicles,
                "total_leftover_volume": sum(v["leftover_volume"] for v in used_vehicles)
            })
        else:
            unassigned.append({
                "store_id": store_id,
                "request_id": request_id,
                "total_volume_needed": total_volume,
                "total_volume_assigned": used_capacity,
                "vehicles_assigned": used_vehicles,
                "error": "Insufficient total vehicle volume"
            })

    return {
        "success": True,
        "message": "Vehicle assignments completed",
        "data": {
            "assignments": assignments,
            "unassigned_fulfillments": unassigned
        }
    }
