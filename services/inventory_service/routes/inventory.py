"""
Inventory Service API Routes
REST API endpoints for inventory management
"""

from math import radians, cos, sin, asin, sqrt
import logging
import math
import os
import httpx
from dotenv import load_dotenv
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
GEMINI_API_KEY = "AIzaSyC3xbpIEPibLdf_MPDLP5sE0ww9xXpIc-8"
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

@router.delete("/products/{product_id}", response_model=APIResponse)
async def delete_product(
    product_id: str,
    service: InventoryService = Depends(get_inventory_service)
):
    """Delete a product by its ID"""
    try:
        deleted = await service.delete_product(product_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "success": True,
            "message": "Product deleted successfully",
            "data": {"product_id": product_id},
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete product")


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
    """Assign multiple vehicles to stores based on fulfillment request volume"""
    async with httpx.AsyncClient() as client:
        # 1. Get all available vehicles
        vehicles_response = await client.get("http://localhost:8001/api/v1/vehicles?available_only=true")
        vehicles = vehicles_response.json()["data"]["items"]

        # 2. Get fulfillment messages
        fulfillment_response = await client.get("http://localhost:8001/api/v1/kafka/fulfillment-messages")
        fulfillments = fulfillment_response.json()

    vehicle_pool = [{
        "vehicle_id": v["vehicle_id"],
        "available_volume": v["available_volume_capacity"],
        "available_weight": v["available_weight_capacity"]
    } for v in vehicles]

    vehicle_pool.sort(key=lambda v: v["available_volume"], reverse=True)

    assignments = []
    for fulfillment in fulfillments:
        store_id = fulfillment["store_id"]
        request_id = fulfillment["request_id"]
        products = fulfillment["products"]

        total_volume = sum(p["volume"] * p["requested_quantity"] for p in products)
        total_volume_assigned = 0.0
        vehicles_assigned = []

        for vehicle in vehicle_pool:
            if total_volume_assigned >= total_volume:
                break

            if vehicle["available_volume"] <= 0:
                continue

            assign_volume = min(vehicle["available_volume"], total_volume - total_volume_assigned)

            if assign_volume > 0:
                vehicle["available_volume"] -= assign_volume
                total_volume_assigned += assign_volume

                vehicles_assigned.append({
                    "vehicle_id": vehicle["vehicle_id"],
                    "assigned_volume": assign_volume,
                    "leftover_volume": vehicle["available_volume"]
                })

        # Calculate required vehicles based on best vehicle capacity
        max_vehicle_capacity = max((v["available_volume_capacity"] for v in vehicles), default=0)
        vehicles_required = math.ceil(total_volume / max_vehicle_capacity) if max_vehicle_capacity > 0 else None

        if total_volume_assigned >= total_volume:
            assignments.append({
                "store_id": store_id,
                "request_id": request_id,
                "total_volume_needed": total_volume,
                "total_volume_assigned": total_volume_assigned,
                "vehicles_assigned": vehicles_assigned,
                "vehicles_required": vehicles_required
            })
        else:
            assignments.append({
                "store_id": store_id,
                "request_id": request_id,
                "total_volume_needed": total_volume,
                "total_volume_assigned": total_volume_assigned,
                "vehicles_assigned": vehicles_assigned,
                "vehicles_required": vehicles_required,
                "error": "Insufficient total vehicle volume"
            })

    return {
        "success": True,
        "message": "Vehicle assignments completed",
        "data": {
            "assignments": assignments,
            "unassigned_fulfillments": [a for a in assignments if a["total_volume_assigned"] < a["total_volume_needed"]]
        }
    }

# @router.get("/kafka/vehicle-assignments")
# async def assign_vehicles_to_fulfillment(service: InventoryService = Depends(get_inventory_service)):
#     """Assign multiple vehicles to fulfillments based on total volume needs"""
#     async with httpx.AsyncClient() as client:
#         # 1. Get available vehicles
#         vehicles_response = await client.get("http://localhost:8001/api/v1/vehicles?available_only=true")
#         vehicles = vehicles_response.json()["data"]["items"]

#         # 2. Get fulfillment requests
#         fulfillment_response = await client.get("http://localhost:8001/api/v1/kafka/fulfillment-messages")
#         fulfillments = fulfillment_response.json()

#     # 3. Prepare vehicle pool
#     vehicle_pool = []
#     for v in vehicles:
#         vehicle_pool.append({
#             "vehicle_id": v["vehicle_id"],
#             "available_volume": v["available_volume_capacity"]
#         })

#     # Sort vehicles by descending volume
#     vehicle_pool.sort(key=lambda v: v["available_volume"], reverse=True)

#     assignments = []
#     unassigned = []

#     # 4. Loop through each fulfillment
#     for fulfillment in fulfillments:
#         store_id = fulfillment["store_id"]
#         request_id = fulfillment["request_id"]
#         products = fulfillment["products"]

#         # Calculate total volume needed
#         total_volume = sum(p["volume"] * p["requested_quantity"] for p in products)

#         used_vehicles = []
#         used_capacity = 0.0

#         for vehicle in vehicle_pool:
#             if used_capacity >= total_volume:
#                 break

#             remaining = total_volume - used_capacity
#             take_volume = min(remaining, vehicle["available_volume"])

#             if take_volume > 0:
#                 used_vehicles.append({
#                     "vehicle_id": vehicle["vehicle_id"],
#                     "assigned_volume": take_volume,
#                     "leftover_volume": vehicle["available_volume"] - take_volume
#                 })
#                 used_capacity += take_volume
#                 vehicle["available_volume"] -= take_volume  # Update vehicle pool

#         if used_capacity >= total_volume:
#             assignments.append({
#                 "store_id": store_id,
#                 "request_id": request_id,
#                 "total_volume_needed": total_volume,
#                 "total_volume_assigned": used_capacity,
#                 "vehicles_assigned": used_vehicles,
#                 "total_leftover_volume": sum(v["leftover_volume"] for v in used_vehicles)
#             })
#         else:
#             unassigned.append({
#                 "store_id": store_id,
#                 "request_id": request_id,
#                 "total_volume_needed": total_volume,
#                 "total_volume_assigned": used_capacity,
#                 "vehicles_assigned": used_vehicles,
#                 "error": "Insufficient total vehicle volume"
#             })

#     return {
#         "success": True,
#         "message": "Vehicle assignments completed",
#         "data": {
#             "assignments": assignments,
#             "unassigned_fulfillments": unassigned
#         }
#     }



def haversine(lat1, lon1, lat2, lon2):
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


# @router.get("/ai/generate-prompt")
# async def generate_gemini_prompt(service: InventoryService = Depends(get_inventory_service)):
#      # 🔐 Replace with your actual key
#     GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

#     async with httpx.AsyncClient() as client:
#         try:
#             # Step 1: Get latest restock request
#             restock_resp = await client.get("http://localhost:8001/api/v1/restock-requests")
#             restock_items = restock_resp.json()["data"]["items"]
#             if not restock_items:
#                 return {"success": False, "message": "No restock requests found"}
            
#             restock_request = restock_items[0]
#             store_id = restock_request["store_id"]
#             product_id = restock_request["product_id"]

#             # Step 2: Get all stores and find nearby ones
#             stores_resp = await client.get("http://localhost:8001/api/v1/stores")
#             stores = stores_resp.json()["data"]["items"]
#             current_store = next((s for s in stores if s["store_id"] == store_id), None)
#             if not current_store:
#                 return {"success": False, "message": f"Store {store_id} not found"}
            
#             curr_coords = current_store["address"]["coordinates"]
#             nearby_stores = []
#             for s in stores:
#                 if s["store_id"] != store_id:
#                     dist = haversine(curr_coords["latitude"], curr_coords["longitude"],
#                                      s["address"]["coordinates"]["latitude"],
#                                      s["address"]["coordinates"]["longitude"])
#                     if dist <= 10:
#                         nearby_stores.append({"store_id": s["store_id"], "distance_km": dist})

#             # Step 3: Get products
#             products_resp = await client.get("http://localhost:8001/api/v1/products")
#             products = [
#                 {
#                     "product_id": p["product_id"],
#                     "category": p["category"],
#                     "description": p.get("description", p.get("name"))
#                 }
#                 for p in products_resp.json()["data"]["items"]
#             ]

#             # Step 4: Get inventory
#             inventory_resp = await client.get("http://localhost:8001/api/v1/inventory")
#             inventory_data = inventory_resp.json()["data"]["items"]
#             warehouse_stock = [
#                 {
#                     "store_id": i["store_id"],
#                     "product_id": i["product_id"],
#                     "available_stock": i["available_stock"]
#                 }
#                 for i in inventory_data
#             ]

#             # Step 5: Get vehicle assignment
#             assignment_resp = await client.get("http://localhost:8001/api/v1/kafka/vehicle-assignments")
#             assignments = assignment_resp.json()["data"]["assignments"]
#             target_assignment = next((a for a in assignments if a["store_id"] == store_id), None)

#             # Step 6: Construct prompt
#             prompt = f"""
# We are fulfilling a restock request for store_id: {store_id}, product_id: {product_id}.

# Nearby stores within 10km:
# {nearby_stores}

# Product catalog (category + summary):
# {products}

# Warehouse stock across all stores:
# {warehouse_stock}

# Vehicle Assignment Summary:
# {target_assignment}

# Based on this:
# 1. Suggest how to utilize leftover vehicle space more efficiently (bundling similar items).
# 2. Recommend if rerouting or sharing inventory with nearby stores is beneficial.
# 3. Give actionable SCM strategies to reduce delivery rounds or bundle routes.
# 4. Recommend additional products that can be sent with the current request if volume allows.
#             """.strip()

#             # Step 7: Gemini call
#             payload = {
#                 "contents": [
#                     {
#                         "parts": [
#                             {
#                                 "text": prompt
#                             }
#                         ]
#                     }
#                 ]
#             }
#             headers = {
#                 "Content-Type": "application/json"
                
#             }
            
#             params={
#                 "key":GEMINI_API_KEY
#             }
#             gemini_resp = await client.post(
#                 GEMINI_URL,
#                 headers=headers,
#                 params=params,
#                 json=payload
#             )

#             # Debug logging
#             print("Gemini Status:", gemini_resp.status_code)
#             print("Gemini Response:", gemini_resp.text)

#             if gemini_resp.status_code != 200:
#                 raise HTTPException(status_code=500, detail=f"Gemini AI request failed: {gemini_resp.text}")

#             gemini_data = gemini_resp.json()
#             suggestion = (
#                 gemini_data.get("candidates", [{}])[0]
#                 .get("content", {})
#                 .get("parts", [{}])[0]
#                 .get("text", "No meaningful response from Gemini.")
#             )

#             return {
#                 "success": True,
#                 "prompt": prompt,
#                 "gemini_suggestion": suggestion.strip(),
#                 "timestamp": datetime.utcnow().isoformat()
#             }

#         except Exception as e:
#             import traceback
#             print("Gemini Prompt Error:\n", traceback.format_exc())
#             raise HTTPException(status_code=500, detail=f"Gemini AI request failed: {str(e)}")

@router.get("/ai/generate-prompt")
async def generate_gemini_prompt(service: InventoryService = Depends(get_inventory_service)):
    async with httpx.AsyncClient() as client:
        # 1. Get restock requests to determine store_id and product_id
        restock_resp = await client.get("http://localhost:8001/api/v1/restock-requests")
        restock_items = restock_resp.json()["data"]["items"]
        if not restock_items:
            return {"error": "No restock requests found"}

        restock_request = restock_items[0]  # Take the most recent/pending one
        store_id = restock_request["store_id"]
        product_id = restock_request["product_id"]

        # 2. Get all stores and find nearby ones
        stores_resp = await client.get("http://localhost:8001/api/v1/stores")
        stores_data = stores_resp.json()["data"]["items"]
        current_store = next((s for s in stores_data if s["store_id"] == store_id), None)
        if not current_store:
            return {"error": f"Store {store_id} not found"}

        curr_coords = current_store["address"]["coordinates"]
        nearby_stores = []
        for store in stores_data:
            if store["store_id"] != store_id:
                coords = store["address"]["coordinates"]
                distance = haversine(curr_coords["latitude"], curr_coords["longitude"], coords["latitude"], coords["longitude"])
                if distance <= 10:
                    nearby_stores.append({"store_id": store["store_id"], "distance_km": distance})

        # 3. Get all products (just category and description)
        products_resp = await client.get("http://localhost:8001/api/v1/products")
        products = [
            {"product_id": p["product_id"], "category": p["category"], "description": p["description"] or p["name"]}
            for p in products_resp.json()["data"]["items"]
        ]

        # 4. Get inventory
        inventory_resp = await client.get("http://localhost:8001/api/v1/inventory")
        inventory_data = inventory_resp.json()["data"]["items"]
        warehouse_stock = [
            {"store_id": i["store_id"], "product_id": i["product_id"], "available_stock": i["available_stock"]}
            for i in inventory_data
        ]

        # 5. Get vehicle assignments
        assignment_resp = await client.get("http://localhost:8001/api/v1/kafka/vehicle-assignments")
        assignments = assignment_resp.json()["data"]["assignments"]
        target_assignment = next((a for a in assignments if a["store_id"] == store_id), None)

        # 6. Build the Gemini prompt
        prompt = f"""
We are fulfilling a restock request for store_id: {store_id}, product_id: {product_id}.

Nearby stores within 10km:
{nearby_stores}

Product catalog (category + summary):
{products}

Warehouse stock across all stores:
{warehouse_stock}

Vehicle Assignment Summary:
{target_assignment}

Based on this:
1. Suggest how to utilize leftover vehicle space more efficiently (bundling similar items).
2. Recommend if rerouting or sharing inventory with nearby stores is beneficial.
3. Give actionable SCM strategies to reduce delivery rounds or bundle routes.
4. Recommend additional products that can be sent with the current request if volume allows.
        """

        # 7. Send prompt to Gemini
        gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }
        # gemini_resp = await client.post(gemini_url, headers=headers, params={"key": GEMINI_API_KEY}, json=payload)
        # gemini_data = gemini_resp.json()
        # suggestion = gemini_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No response")

    return {
        "Gemini-key":GEMINI_API_KEY,
        "success": True,
        "prompt": prompt.strip(),
        # "gemini_suggestion": suggestion.strip(),
        # "raw_response": gemini_data  # include full response for debugging
    }

