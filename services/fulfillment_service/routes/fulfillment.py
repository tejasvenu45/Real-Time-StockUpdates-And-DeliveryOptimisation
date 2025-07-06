"""
Fulfillment Service API Routes
REST API endpoints for warehouse fulfillment and AI-powered optimization
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from datetime import datetime

from services.common.database import DatabaseManager, get_database
from services.common.models import Priority
from services.fulfillment_service.services.fulfillment_service import FulfillmentService

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

async def get_fulfillment_service(db: DatabaseManager = Depends(get_database)) -> FulfillmentService:
    """Dependency injection for fulfillment service"""
    return FulfillmentService(db)

# =============================================================================
# FULFILLMENT REQUEST ENDPOINTS
# =============================================================================

@router.get("/fulfillment/requests")
async def get_fulfillment_requests(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    store_id: Optional[str] = Query(None, description="Filter by store"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Get fulfillment requests with filtering and pagination"""
    try:
        requests = await service.get_fulfillment_requests(
            status=status,
            priority=priority,
            store_id=store_id,
            page=page,
            size=size
        )
        total = await service.count_fulfillment_requests(
            status=status,
            priority=priority,
            store_id=store_id
        )
        
        return {
            "success": True,
            "message": "Fulfillment requests retrieved successfully",
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
        logger.error(f"Error retrieving fulfillment requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve fulfillment requests")

@router.post("/fulfillment/process-request")
async def process_fulfillment_request(
    request_id: str = Body(..., embed=True),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Manually trigger processing of a specific fulfillment request"""
    try:
        result = await service.process_fulfillment_request(request_id)
        return {
            "success": True,
            "message": "Fulfillment request processed successfully",
            "data": serialize_for_json(result),
            "timestamp": datetime.utcnow().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing fulfillment request {request_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process fulfillment request")

@router.put("/fulfillment/requests/{request_id}/status")
async def update_request_status(
    request_id: str,
    status: str = Body(..., embed=True),
    notes: Optional[str] = Body(None, embed=True),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Update the status of a fulfillment request"""
    try:
        success = await service.update_request_status(request_id, status, notes)
        if not success:
            raise HTTPException(status_code=404, detail="Fulfillment request not found")
        
        return {
            "success": True,
            "message": "Request status updated successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating request status for {request_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update request status")

# =============================================================================
# AI OPTIMIZATION ENDPOINTS
# =============================================================================

@router.post("/optimization/optimize-shipment")
async def optimize_shipment(
    shipment_data: Dict[str, Any] = Body(...),
    use_ai: bool = Query(True, description="Use AI for optimization"),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Use AI to optimize a shipment with product recommendations"""
    try:
        optimization_result = await service.optimize_shipment_with_ai(
            shipment_data, 
            use_ai=use_ai
        )
        
        return {
            "success": True,
            "message": "Shipment optimized successfully",
            "data": serialize_for_json(optimization_result),
            "timestamp": datetime.utcnow().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error optimizing shipment: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize shipment")

@router.post("/optimization/product-recommendations")
async def get_product_recommendations(
    request_data: Dict[str, Any] = Body(...),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Get AI-powered product recommendations for a delivery"""
    try:
        recommendations = await service.get_ai_product_recommendations(request_data)
        
        return {
            "success": True,
            "message": "Product recommendations generated successfully",
            "data": serialize_for_json(recommendations),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating product recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")

@router.post("/optimization/consolidate-orders")
async def consolidate_orders(
    store_ids: List[str] = Body(...),
    max_distance_km: float = Body(50.0),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Consolidate orders for nearby stores to optimize delivery efficiency"""
    try:
        consolidation_result = await service.consolidate_nearby_orders(
            store_ids, 
            max_distance_km
        )
        
        return {
            "success": True,
            "message": "Orders consolidated successfully",
            "data": serialize_for_json(consolidation_result),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error consolidating orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to consolidate orders")

# =============================================================================
# WAREHOUSE MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/warehouse/inventory")
async def get_warehouse_inventory(
    product_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    low_stock_only: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Get warehouse inventory levels"""
    try:
        inventory = await service.get_warehouse_inventory(
            product_id=product_id,
            category=category,
            low_stock_only=low_stock_only,
            page=page,
            size=size
        )
        total = await service.count_warehouse_inventory(
            product_id=product_id,
            category=category,
            low_stock_only=low_stock_only
        )
        
        return {
            "success": True,
            "message": "Warehouse inventory retrieved successfully",
            "data": {
                "items": serialize_for_json(inventory),
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error retrieving warehouse inventory: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve warehouse inventory")

@router.post("/warehouse/allocate")
async def allocate_warehouse_stock(
    allocation_data: Dict[str, Any] = Body(...),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Allocate warehouse stock for a delivery"""
    try:
        allocation_result = await service.allocate_warehouse_stock(allocation_data)
        
        return {
            "success": True,
            "message": "Stock allocated successfully",
            "data": serialize_for_json(allocation_result),
            "timestamp": datetime.utcnow().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error allocating warehouse stock: {e}")
        raise HTTPException(status_code=500, detail="Failed to allocate stock")

@router.put("/warehouse/inventory/{product_id}")
async def update_warehouse_inventory(
    product_id: str,
    update_data: Dict[str, Any] = Body(...),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Update warehouse inventory levels"""
    try:
        success = await service.update_warehouse_inventory(product_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Product not found in warehouse")
        
        return {
            "success": True,
            "message": "Warehouse inventory updated successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating warehouse inventory for {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update warehouse inventory")

# =============================================================================
# ANALYTICS AND REPORTING ENDPOINTS
# =============================================================================

@router.get("/analytics/fulfillment-metrics")
async def get_fulfillment_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    store_id: Optional[str] = Query(None),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Get fulfillment performance metrics"""
    try:
        metrics = await service.get_fulfillment_metrics(
            start_date=start_date,
            end_date=end_date,
            store_id=store_id
        )
        
        return {
            "success": True,
            "message": "Fulfillment metrics retrieved successfully",
            "data": serialize_for_json(metrics),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error retrieving fulfillment metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve fulfillment metrics")

@router.get("/analytics/warehouse-utilization")
async def get_warehouse_utilization(
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Get warehouse utilization and capacity analytics"""
    try:
        utilization = await service.get_warehouse_utilization()
        
        return {
            "success": True,
            "message": "Warehouse utilization retrieved successfully",
            "data": serialize_for_json(utilization),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error retrieving warehouse utilization: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve warehouse utilization")

@router.get("/analytics/ai-recommendations-performance")
async def get_ai_performance_metrics(
    days: int = Query(30, ge=1, le=365),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Get AI recommendation system performance metrics"""
    try:
        ai_metrics = await service.get_ai_performance_metrics(days=days)
        
        return {
            "success": True,
            "message": "AI performance metrics retrieved successfully",
            "data": serialize_for_json(ai_metrics),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error retrieving AI performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve AI performance metrics")

# =============================================================================
# MANUAL STOCK REQUEST ENDPOINTS
# =============================================================================

@router.post("/requests/manual")
async def create_manual_stock_request(
    request_data: Dict[str, Any] = Body(...),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Create manual stock request from store"""
    try:
        request_id = await service.create_manual_stock_request(request_data)
        return {
            "success": True,
            "message": "Manual stock request created successfully",
            "data": {"request_id": request_id},
            "timestamp": datetime.utcnow().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating manual stock request: {e}")
        raise HTTPException(status_code=500, detail="Failed to create manual stock request")

@router.get("/requests/manual")
async def get_manual_stock_requests(
    store_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Get manual stock requests with filtering"""
    try:
        requests = await service.get_manual_stock_requests(
            store_id=store_id,
            status=status,
            page=page,
            size=size
        )
        total = await service.count_manual_stock_requests(store_id=store_id, status=status)
        
        return {
            "success": True,
            "message": "Manual stock requests retrieved successfully",
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
        logger.error(f"Error retrieving manual stock requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve manual stock requests")

# =============================================================================
# VEHICLE MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/vehicles")
async def create_vehicle(
    vehicle_data: Dict[str, Any] = Body(...),
    service: FulfillmentService = Depends(get_fulfillment_service)
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
    service: FulfillmentService = Depends(get_fulfillment_service)
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
    service: FulfillmentService = Depends(get_fulfillment_service)
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
    service: FulfillmentService = Depends(get_fulfillment_service)
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
    service: FulfillmentService = Depends(get_fulfillment_service)
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

# =============================================================================
# AI DELIVERY OPTIMIZATION ENDPOINTS
# =============================================================================

@router.get("/optimization/delivery-recommendations")
async def get_delivery_recommendations(
    include_manual_requests: bool = Query(True),
    include_auto_requests: bool = Query(True),
    max_distance_km: float = Query(100.0, ge=1.0),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Get AI-powered delivery recommendations"""
    try:
        recommendations = await service.get_ai_delivery_recommendations(
            include_manual_requests=include_manual_requests,
            include_auto_requests=include_auto_requests,
            max_distance_km=max_distance_km
        )
        
        return {
            "success": True,
            "message": "AI delivery recommendations generated successfully",
            "data": serialize_for_json(recommendations),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating delivery recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate delivery recommendations")

@router.post("/fulfillment/execute-delivery")
async def execute_delivery_plan(
    delivery_plan: Dict[str, Any] = Body(...),
    warehouse_manager: str = Body(..., embed=True),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Execute delivery plan based on warehouse manager decision"""
    try:
        execution_result = await service.execute_delivery_plan(delivery_plan, warehouse_manager)
        
        return {
            "success": True,
            "message": "Delivery plan executed successfully",
            "data": serialize_for_json(execution_result),
            "timestamp": datetime.utcnow().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing delivery plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute delivery plan")

@router.get("/delivery-plans")
async def get_delivery_plans(
    status: Optional[str] = Query(None),
    vehicle_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: FulfillmentService = Depends(get_fulfillment_service)
):
    """Get delivery plans with filtering"""
    try:
        plans = await service.get_delivery_plans(
            status=status,
            vehicle_id=vehicle_id,
            page=page,
            size=size
        )
        total = await service.count_delivery_plans(status=status, vehicle_id=vehicle_id)
        
        return {
            "success": True,
            "message": "Delivery plans retrieved successfully",
            "data": {
                "items": serialize_for_json(plans),
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error retrieving delivery plans: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve delivery plans")