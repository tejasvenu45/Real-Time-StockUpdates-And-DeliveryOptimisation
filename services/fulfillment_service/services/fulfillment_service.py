# fulfillment_service.py
"""
Fulfillment Service Business Logic
Manual warehouse fulfillment and order optimization
"""
import os
import json
import uuid
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal

from services.common.database import DatabaseManager
from services.common.kafka_client import kafka_manager
from services.common.models import Priority

logger = logging.getLogger(__name__)

class FulfillmentService:
    """Manual fulfillment and warehouse management service"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    # =============================================================================
    # KAFKA MESSAGE HANDLERS
    # =============================================================================
    
    async def handle_restock_request(self, message: Dict[str, Any], key: str, offset: int, partition: int):
        """Handle incoming restock request from Kafka"""
        try:
            logger.info(f"Processing restock request: {key}")
            
            # Extract request details
            store_id = message.get('store_id')
            product_id = message.get('product_id')
            requested_quantity = message.get('requested_quantity')
            priority = message.get('priority', 'medium')
            reason = message.get('reason', 'Auto-generated request')
            
            # Create fulfillment request
            request_id = f"FUL_{uuid.uuid4().hex[:8].upper()}"
            
            fulfillment_request = {
                "request_id": request_id,
                "store_id": store_id,
                "product_id": product_id,
                "requested_quantity": requested_quantity,
                "priority": priority,
                "reason": reason,
                "status": "pending",
                "kafka_offset": offset,
                "kafka_partition": partition,
                "processing_notes": [],
                "created_at": datetime.utcnow()
            }
            
            # Save to database
            await self.db.insert_one("fulfillment_requests", fulfillment_request)
            
            # Process immediately if high priority
            if priority in ['high', 'critical']:
                await self.process_fulfillment_request(request_id)
            
            logger.info(f"Restock request processed: {request_id}")
            
        except Exception as e:
            logger.error(f"Error handling restock request: {e}")
    
    async def handle_inventory_update(self, message: Dict[str, Any], key: str, offset: int, partition: int):
        """Handle inventory update events to sync warehouse state"""
        try:
            store_id = message.get('store_id')
            product_id = message.get('product_id')
            current_stock = message.get('current_stock')
            change_type = message.get('change_type')
            
            # Update store inventory cache in warehouse system
            await self.sync_store_inventory(store_id, product_id, current_stock, change_type)
            
            logger.debug(f"Inventory update processed for {store_id}/{product_id}")
            
        except Exception as e:
            logger.error(f"Error handling inventory update: {e}")
    
    # =============================================================================
    # FULFILLMENT REQUEST PROCESSING
    # =============================================================================
    
    async def get_fulfillment_requests(self, status: Optional[str] = None, 
                                     priority: Optional[str] = None,
                                     store_id: Optional[str] = None,
                                     page: int = 1, size: int = 20) -> List[Dict]:
        """Get fulfillment requests with filtering"""
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if priority:
            filter_dict["priority"] = priority
        if store_id:
            filter_dict["store_id"] = store_id
        
        skip = (page - 1) * size
        sort = [("created_at", -1)]
        
        try:
            requests = await self.db.find_many("fulfillment_requests", filter_dict, limit=size, sort=sort, skip=skip)
            # Convert ObjectId and other non-serializable objects
            serialized_requests = []
            for request in requests:
                if isinstance(request, dict):
                    # Remove or convert ObjectId
                    if '_id' in request:
                        request['_id'] = str(request['_id'])
                    serialized_requests.append(request)
            
            return serialized_requests
        except Exception as e:
            logger.error(f"Error retrieving fulfillment requests: {e}")
            return []
    
    async def count_fulfillment_requests(self, status: Optional[str] = None,
                                       priority: Optional[str] = None,
                                       store_id: Optional[str] = None) -> int:
        """Count fulfillment requests"""
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if priority:
            filter_dict["priority"] = priority
        if store_id:
            filter_dict["store_id"] = store_id
        
        try:
            return await self.db.count_documents("fulfillment_requests", filter_dict)
        except Exception as e:
            logger.error(f"Error counting fulfillment requests: {e}")
            return 0
    
    async def process_fulfillment_request(self, request_id: str) -> Dict[str, Any]:
        """Process a fulfillment request manually"""
        try:
            # Get request details
            request = await self.db.find_one("fulfillment_requests", {"request_id": request_id})
            if not request:
                raise ValueError(f"Fulfillment request {request_id} not found")
            
            # Update status to processing
            await self.update_request_status(request_id, "processing", "Started manual processing")
            
            # Check warehouse availability
            availability = await self.check_warehouse_availability(
                request['product_id'], 
                request['requested_quantity']
            )
            
            if not availability['available']:
                await self.update_request_status(
                    request_id, 
                    "insufficient_stock", 
                    f"Insufficient warehouse stock. Available: {availability['current_stock']}"
                )
                return {"status": "insufficient_stock", "availability": availability}
            
            # Use manual optimization
            optimization_result = await self.manual_fulfillment_optimization(request)
            
            # Create shipment plan
            shipment_plan = await self.create_shipment_plan(request, optimization_result)
            
            # Update request status
            await self.update_request_status(
                request_id, 
                "ready_for_allocation", 
                f"Ready for allocation. Shipment planned with {len(shipment_plan['products'])} products."
            )
            
            return {
                "request_id": request_id,
                "status": "ready_for_allocation",
                "shipment_plan": shipment_plan,
                "optimization": optimization_result
            }
            
        except Exception as e:
            logger.error(f"Error processing fulfillment request {request_id}: {e}")
            await self.update_request_status(
                request_id, 
                "error", 
                f"Processing failed: {str(e)}"
            )
            raise
    
    async def update_request_status(self, request_id: str, status: str, notes: Optional[str] = None) -> bool:
        """Update fulfillment request status"""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if notes:
            # Add note to processing_notes array
            request = await self.db.find_one("fulfillment_requests", {"request_id": request_id})
            if request:
                processing_notes = request.get("processing_notes", [])
                processing_notes.append({
                    "timestamp": datetime.utcnow(),
                    "note": notes,
                    "status": status
                })
                update_data["processing_notes"] = processing_notes
        
        return await self.db.update_one("fulfillment_requests", {"request_id": request_id}, update_data)
    
    # =============================================================================
    # MANUAL OPTIMIZATION
    # =============================================================================
    
    async def manual_fulfillment_optimization(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Manual fulfillment optimization without AI"""
        try:
            store_id = request['store_id']
            product_id = request['product_id']
            requested_quantity = request['requested_quantity']
            
            # Get product information for calculations
            product = await self.db.find_one("products", {"product_id": product_id})
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            # Calculate weight and volume
            unit_weight = product.get('weight', 1.0)
            dimensions = product.get('dimensions', {})
            unit_volume = (
                dimensions.get('length', 1.0) * 
                dimensions.get('width', 1.0) * 
                dimensions.get('height', 1.0)
            ) / 1000000  # Convert cm³ to m³
            
            total_weight = unit_weight * requested_quantity
            total_volume = unit_volume * requested_quantity
            
            return {
                "optimization_type": "manual",
                "primary_quantity": requested_quantity,
                "total_weight": total_weight,
                "total_volume": total_volume,
                "unit_weight": unit_weight,
                "unit_volume": unit_volume,
                "optimization_strategy": "Direct fulfillment of requested quantity",
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Manual optimization failed: {e}")
            return {
                "optimization_type": "fallback",
                "primary_quantity": request['requested_quantity'],
                "total_weight": 0,
                "total_volume": 0,
                "optimization_strategy": f"Fallback optimization due to error: {str(e)}",
                "generated_at": datetime.utcnow().isoformat()
            }
    
    # =============================================================================
    # WAREHOUSE MANAGEMENT
    # =============================================================================
    
    async def check_warehouse_availability(self, product_id: str, quantity: int) -> Dict[str, Any]:
        """Check if warehouse has sufficient stock"""
        warehouse_item = await self.db.find_one("warehouse_inventory", {"product_id": product_id})
        
        if not warehouse_item:
            return {
                "available": False,
                "current_stock": 0,
                "requested": quantity,
                "shortage": quantity
            }
        
        current_stock = warehouse_item.get("available_stock", 0)
        available = current_stock >= quantity
        
        return {
            "available": available,
            "current_stock": current_stock,
            "requested": quantity,
            "shortage": max(0, quantity - current_stock)
        }
    
    async def allocate_warehouse_stock(self, allocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Allocate warehouse stock for delivery"""
        request_id = allocation_data['request_id']
        products = allocation_data['products']
        
        allocated_items = []
        allocation_errors = []
        
        for product in products:
            product_id = product['product_id']
            quantity = product['quantity']
            
            try:
                # Check availability
                availability = await self.check_warehouse_availability(product_id, quantity)
                
                if availability['available']:
                    # Reserve the stock
                    await self.db.update_one(
                        "warehouse_inventory",
                        {"product_id": product_id},
                        {
                            "$inc": {"available_stock": -quantity, "reserved_stock": quantity},
                            "last_allocation_date": datetime.utcnow()
                        }
                    )
                    
                    allocated_items.append({
                        "product_id": product_id,
                        "allocated_quantity": quantity,
                        "status": "allocated"
                    })
                else:
                    allocation_errors.append({
                        "product_id": product_id,
                        "requested_quantity": quantity,
                        "available_quantity": availability['current_stock'],
                        "error": "insufficient_stock"
                    })
                    
            except Exception as e:
                allocation_errors.append({
                    "product_id": product_id,
                    "error": str(e)
                })
        
        # Record allocation
        allocation_record = {
            "allocation_id": f"ALLOC_{uuid.uuid4().hex[:8].upper()}",
            "request_id": request_id,
            "allocated_items": allocated_items,
            "allocation_errors": allocation_errors,
            "status": "completed" if not allocation_errors else "partial",
            "created_at": datetime.utcnow()
        }
        
        await self.db.insert_one("warehouse_allocations", allocation_record)
        
        return allocation_record
    
    async def get_warehouse_inventory(self, product_id: Optional[str] = None,
                                     low_stock_only: bool = False,
                                     page: int = 1, size: int = 20) -> List[Dict]:
        """Get warehouse inventory"""
        filter_dict = {}
        if product_id:
            filter_dict["product_id"] = product_id
        if low_stock_only:
            filter_dict["available_stock"] = {"$lt": 50}  # Configurable threshold
        
        skip = (page - 1) * size
        sort = [("product_id", 1)]
        
        try:
            inventory = await self.db.find_many("warehouse_inventory", filter_dict, limit=size, sort=sort, skip=skip)
            for item in inventory:
                if '_id' in item:
                    item['_id'] = str(item['_id'])
            return inventory
        except Exception as e:
            logger.error(f"Error retrieving warehouse inventory: {e}")
            return []
    
    async def count_warehouse_inventory(self, product_id: Optional[str] = None,
                                       low_stock_only: bool = False) -> int:
        """Count warehouse inventory items"""
        filter_dict = {}
        if product_id:
            filter_dict["product_id"] = product_id
        if low_stock_only:
            filter_dict["available_stock"] = {"$lt": 50}
        
        try:
            return await self.db.count_documents("warehouse_inventory", filter_dict)
        except Exception as e:
            logger.error(f"Error counting warehouse inventory: {e}")
            return 0
    
    async def update_warehouse_inventory(self, product_id: str, update_data: Dict) -> bool:
        """Update warehouse inventory"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            return await self.db.update_one("warehouse_inventory", {"product_id": product_id}, update_data)
        except Exception as e:
            logger.error(f"Error updating warehouse inventory {product_id}: {e}")
            return False
    
    # =============================================================================
    # VEHICLE MANAGEMENT
    # =============================================================================
    
    async def create_vehicle(self, vehicle_data: Dict[str, Any]) -> str:
        """Create a new vehicle"""
        # Validate required fields
        required_fields = ["vehicle_id", "license_plate", "vehicle_type", "max_weight_capacity", "max_volume_capacity"]
        for field in required_fields:
            if field not in vehicle_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Check if vehicle already exists
        existing = await self.db.find_one("vehicles", {"vehicle_id": vehicle_data["vehicle_id"]})
        if existing:
            raise ValueError(f"Vehicle with ID {vehicle_data['vehicle_id']} already exists")
        
        # Create vehicle document
        vehicle_doc = {
            **vehicle_data,
            "status": vehicle_data.get("status", "available"),
            "current_weight": 0,
            "current_volume": 0,
            "created_at": datetime.utcnow()
        }
        
        # Insert into database
        await self.db.insert_one("vehicles", vehicle_doc)
        
        logger.info(f"Created vehicle: {vehicle_data['vehicle_id']}")
        return vehicle_data["vehicle_id"]
    
    async def get_vehicles(self, status: Optional[str] = None,
                          vehicle_type: Optional[str] = None,
                          available_only: bool = False,
                          page: int = 1, size: int = 20) -> List[Dict]:
        """Get vehicles with filtering"""
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if vehicle_type:
            filter_dict["vehicle_type"] = vehicle_type
        if available_only:
            filter_dict["status"] = "available"
        
        skip = (page - 1) * size
        sort = [("created_at", -1)]
        
        try:
            vehicles = await self.db.find_many("vehicles", filter_dict, limit=size, sort=sort, skip=skip)
            # Convert ObjectId for serialization
            for vehicle in vehicles:
                if '_id' in vehicle:
                    vehicle['_id'] = str(vehicle['_id'])
                # Calculate available capacity
                vehicle['available_weight_capacity'] = max(0, vehicle.get('max_weight_capacity', 0) - vehicle.get('current_weight', 0))
                vehicle['available_volume_capacity'] = max(0, vehicle.get('max_volume_capacity', 0) - vehicle.get('current_volume', 0))
            return vehicles
        except Exception as e:
            logger.error(f"Error retrieving vehicles: {e}")
            return []
    
    async def get_vehicle(self, vehicle_id: str) -> Optional[Dict]:
        """Get specific vehicle by ID"""
        try:
            vehicle = await self.db.find_one("vehicles", {"vehicle_id": vehicle_id})
            if vehicle and '_id' in vehicle:
                vehicle['_id'] = str(vehicle['_id'])
                # Calculate available capacity
                vehicle['available_weight_capacity'] = max(0, vehicle.get('max_weight_capacity', 0) - vehicle.get('current_weight', 0))
                vehicle['available_volume_capacity'] = max(0, vehicle.get('max_volume_capacity', 0) - vehicle.get('current_volume', 0))
            return vehicle
        except Exception as e:
            logger.error(f"Error retrieving vehicle {vehicle_id}: {e}")
            return None
    
    async def update_vehicle(self, vehicle_id: str, vehicle_data: Dict[str, Any]) -> bool:
        """Update vehicle information"""
        try:
            vehicle_data["updated_at"] = datetime.utcnow()
            return await self.db.update_one("vehicles", {"vehicle_id": vehicle_id}, vehicle_data)
        except Exception as e:
            logger.error(f"Error updating vehicle {vehicle_id}: {e}")
            return False
    
    async def delete_vehicle(self, vehicle_id: str) -> bool:
        """Delete a vehicle"""
        try:
            return await self.db.delete_one("vehicles", {"vehicle_id": vehicle_id})
        except Exception as e:
            logger.error(f"Error deleting vehicle {vehicle_id}: {e}")
            return False
    
    async def count_vehicles(self, status: Optional[str] = None,
                           vehicle_type: Optional[str] = None,
                           available_only: bool = False) -> int:
        """Count vehicles"""
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if vehicle_type:
            filter_dict["vehicle_type"] = vehicle_type
        if available_only:
            filter_dict["status"] = "available"
        
        try:
            return await self.db.count_documents("vehicles", filter_dict)
        except Exception as e:
            logger.error(f"Error counting vehicles: {e}")
            return 0
    
    # =============================================================================
    # DELIVERY OPTIMIZATION (MANUAL)
    # =============================================================================
    
    async def get_delivery_recommendations(self, store_id: Optional[str] = None,
                                         priority_filter: Optional[str] = None,
                                         include_manual_requests: bool = True,
                                         include_auto_requests: bool = True) -> Dict[str, Any]:
        """Get manual delivery recommendations"""
        try:
            # Gather all pending requests
            all_requests = []
            
            if include_manual_requests:
                manual_requests = await self.db.find_many("manual_stock_requests", {"status": "pending"})
                for req in manual_requests:
                    req["request_type"] = "manual"
                all_requests.extend(manual_requests)
            
            if include_auto_requests:
                auto_requests = await self.db.find_many("fulfillment_requests", {"status": "ready_for_allocation"})
                for req in auto_requests:
                    req["request_type"] = "automatic"
                all_requests.extend(auto_requests)
            
            # Filter by store if specified
            if store_id:
                all_requests = [req for req in all_requests if req.get('store_id') == store_id]
            
            # Filter by priority if specified
            if priority_filter:
                all_requests = [req for req in all_requests if req.get('priority') == priority_filter]
            
            if not all_requests:
                return {
                    "recommendations": [],
                    "message": "No pending requests found matching criteria",
                    "total_requests": 0,
                    "unique_stores": 0
                }
            
            # Group requests by store
            store_groups = {}
            for req in all_requests:
                store_id = req['store_id']
                if store_id not in store_groups:
                    store_groups[store_id] = []
                store_groups[store_id].append(req)
            
            # Create recommendations
            recommendations = await self._create_manual_delivery_recommendations(store_groups)
            
            return {
                "recommendations": recommendations,
                "total_requests": len(all_requests),
                "unique_stores": len(store_groups),
                "grouped_by_store": True,
                "optimization_type": "manual"
            }
            
        except Exception as e:
            logger.error(f"Error generating delivery recommendations: {e}")
            return {
                "recommendations": [],
                "message": f"Error generating recommendations: {str(e)}",
                "total_requests": 0,
                "unique_stores": 0
            }
    
    async def _create_manual_delivery_recommendations(self, store_groups: Dict[str, List[Dict]]) -> List[Dict]:
        """Create manual delivery recommendations"""
        recommendations = []
        
        for store_id, requests in store_groups.items():
            # Get store info
            store = await self.db.find_one("stores", {"store_id": store_id})
            store_name = store.get('name', store_id) if store else store_id
            
            # Calculate total weight and volume for all requests to this store
            total_weight = 0
            total_volume = 0
            products_summary = []
            
            for req in requests:
                product = await self.db.find_one("products", {"product_id": req['product_id']})
                if product:
                    unit_weight = product.get('weight', 1.0)
                    dimensions = product.get('dimensions', {})
                    unit_volume = (
                        dimensions.get('length', 1.0) * 
                        dimensions.get('width', 1.0) * 
                        dimensions.get('height', 1.0)
                    ) / 1000000  # Convert cm³ to m³
                    
                    req_weight = unit_weight * req['requested_quantity']
                    req_volume = unit_volume * req['requested_quantity']
                    
                    total_weight += req_weight
                    total_volume += req_volume
                    
                    products_summary.append({
                        "product_id": req['product_id'],
                        "product_name": product.get('name', 'Unknown'),
                        "quantity": req['requested_quantity'],
                        "weight": req_weight,
                        "volume": req_volume,
                        "priority": req.get('priority', 'medium'),
                        "request_type": req.get('request_type', 'unknown')
                    })
            
            # Find suitable vehicles
            suitable_vehicles = await self._find_suitable_vehicles(total_weight, total_volume)
            
            recommendation = {
                "recommendation_id": f"REC_{uuid.uuid4().hex[:8].upper()}",
                "store_id": store_id,
                "store_name": store_name,
                "total_requests": len(requests),
                "total_weight": round(total_weight, 2),
                "total_volume": round(total_volume, 4),
                "products": products_summary,
                "suitable_vehicles": suitable_vehicles,
                "delivery_priority": self._calculate_delivery_priority(requests),
                "estimated_delivery_time": "2-4 hours",  # Placeholder
                "created_at": datetime.utcnow().isoformat()
            }
            
            recommendations.append(recommendation)
        
        # Sort by priority and total weight
        recommendations.sort(key=lambda x: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["delivery_priority"], 3),
            -x["total_weight"]
        ))
        
        return recommendations
    
    async def _find_suitable_vehicles(self, required_weight: float, required_volume: float) -> List[Dict]:
        """Find vehicles that can handle the required weight and volume"""
        vehicles = await self.get_vehicles(available_only=True)
        suitable = []
        
        for vehicle in vehicles:
            available_weight = vehicle.get('available_weight_capacity', 0)
            available_volume = vehicle.get('available_volume_capacity', 0)
            
            if available_weight >= required_weight and available_volume >= required_volume:
                suitable.append({
                    "vehicle_id": vehicle['vehicle_id'],
                    "vehicle_type": vehicle['vehicle_type'],
                    "license_plate": vehicle['license_plate'],
                    "available_weight_capacity": available_weight,
                    "available_volume_capacity": available_volume,
                    "utilization_weight": round((required_weight / vehicle.get('max_weight_capacity', 1)) * 100, 1),
                    "utilization_volume": round((required_volume / vehicle.get('max_volume_capacity', 1)) * 100, 1)
                })
        
        # Sort by best utilization (prefer vehicles that will be more fully utilized)
        suitable.sort(key=lambda x: -(x["utilization_weight"] + x["utilization_volume"]) / 2)
        
        return suitable
    
    def _calculate_delivery_priority(self, requests: List[Dict]) -> str:
        """Calculate overall delivery priority for a group of requests"""
        priorities = [req.get('priority', 'medium') for req in requests]
        
        if 'critical' in priorities:
            return 'critical'
        elif 'high' in priorities:
            return 'high'
        elif 'medium' in priorities:
            return 'medium'
        else:
            return 'low'
    
    # =============================================================================
    # DELIVERY PLAN EXECUTION
    # =============================================================================
    
    async def create_delivery_plan(self, plan_data: Dict[str, Any], created_by: str) -> str:
        """Create a delivery plan"""
        plan_id = f"PLAN_{uuid.uuid4().hex[:8].upper()}"
        
        plan_doc = {
            "plan_id": plan_id,
            "store_id": plan_data["store_id"],
            "vehicle_id": plan_data["vehicle_id"],
            "products": plan_data["products"],
            "total_weight": plan_data.get("total_weight", 0),
            "total_volume": plan_data.get("total_volume", 0),
            "estimated_delivery_time": plan_data.get("estimated_delivery_time"),
            "notes": plan_data.get("notes"),
            "status": "created",
            "created_by": created_by,
            "created_at": datetime.utcnow()
        }
        
        await self.db.insert_one("delivery_plans", plan_doc)
        
        # Update vehicle status
        await self.update_vehicle(plan_data["vehicle_id"], {"status": "assigned"})
        
        # Update request statuses
        for product in plan_data["products"]:
            if "request_id" in product:
                await self.update_request_status(product["request_id"], "planned", f"Added to delivery plan {plan_id}")
        
        logger.info(f"Created delivery plan: {plan_id}")
        return plan_id
    
    async def get_delivery_plans(self, status: Optional[str] = None,
                                vehicle_id: Optional[str] = None,
                                store_id: Optional[str] = None,
                                page: int = 1, size: int = 20) -> List[Dict]:
        """Get delivery plans with filtering"""
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if vehicle_id:
            filter_dict["vehicle_id"] = vehicle_id
        if store_id:
            filter_dict["store_id"] = store_id
        
        skip = (page - 1) * size
        sort = [("created_at", -1)]
        
        try:
            plans = await self.db.find_many("delivery_plans", filter_dict, limit=size, sort=sort, skip=skip)
            for plan in plans:
                if '_id' in plan:
                    plan['_id'] = str(plan['_id'])
            return plans
        except Exception as e:
            logger.error(f"Error retrieving delivery plans: {e}")
            return []
    
    async def update_delivery_plan_status(self, plan_id: str, status: str, notes: Optional[str] = None) -> bool:
        """Update delivery plan status"""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if notes:
            update_data["status_notes"] = notes
        
        # If marking as completed, update vehicle status back to available
        if status == "completed":
            plan = await self.db.find_one("delivery_plans", {"plan_id": plan_id})
            if plan and plan.get("vehicle_id"):
                await self.update_vehicle(plan["vehicle_id"], {"status": "available", "current_weight": 0, "current_volume": 0})
        
        return await self.db.update_one("delivery_plans", {"plan_id": plan_id}, update_data)
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    async def sync_store_inventory(self, store_id: str, product_id: str, 
                                 current_stock: int, change_type: str):
        """Sync store inventory state for optimization"""
        update_data = {
            "current_stock": current_stock,
            "last_updated": datetime.utcnow(),
            "change_type": change_type
        }
        
        # Use upsert to create if doesn't exist
        existing = await self.db.find_one("store_inventory_cache", {"store_id": store_id, "product_id": product_id})
        if existing:
            await self.db.update_one(
                "store_inventory_cache",
                {"store_id": store_id, "product_id": product_id},
                update_data
            )
        else:
            await self.db.insert_one("store_inventory_cache", {
                "store_id": store_id,
                "product_id": product_id,
                **update_data
            })
    
    async def create_shipment_plan(self, request: Dict[str, Any], 
                                 optimization_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed shipment plan"""
        products = [{
            "product_id": request['product_id'],
            "quantity": optimization_result.get('primary_quantity', request['requested_quantity']),
            "type": "primary"
        }]
        
        return {
            "shipment_id": f"SHIP_{uuid.uuid4().hex[:8].upper()}",
            "request_id": request['request_id'],
            "destination_store": request['store_id'],
            "products": products,
            "optimization_applied": optimization_result.get('optimization_strategy', ''),
            "estimated_weight": optimization_result.get('total_weight', 0),
            "estimated_volume": optimization_result.get('total_volume', 0),
            "created_at": datetime.utcnow()
        }
    
    async def get_fulfillment_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get fulfillment metrics for the last N days"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Count requests by status
            total_requests = await self.count_fulfillment_requests()
            pending_requests = await self.count_fulfillment_requests(status="pending")
            processing_requests = await self.count_fulfillment_requests(status="processing")
            completed_requests = await self.count_fulfillment_requests(status="allocated")
            
            # Count vehicles by status
            total_vehicles = await self.count_vehicles()
            available_vehicles = await self.count_vehicles(available_only=True)
            
            # Recent activity
            recent_requests = await self.db.find_many(
                "fulfillment_requests",
                {"created_at": {"$gte": since_date}},
                limit=10,
                sort=[("created_at", -1)]
            )
            
            return {
                "period_days": days,
                "requests": {
                    "total": total_requests,
                    "pending": pending_requests,
                    "processing": processing_requests,
                    "completed": completed_requests,
                    "recent": len(recent_requests)
                },
                "vehicles": {
                    "total": total_vehicles,
                    "available": available_vehicles,
                    "utilized": total_vehicles - available_vehicles,
                    "utilization_rate": round(((total_vehicles - available_vehicles) / max(total_vehicles, 1)) * 100, 1)
                },
                "recent_activity": [
                    {
                        "request_id": req["request_id"],
                        "store_id": req["store_id"],
                        "status": req["status"],
                        "created_at": req["created_at"].isoformat() if req.get("created_at") else None
                    }
                    for req in recent_requests
                ],
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating fulfillment metrics: {e}")
            return {"error": str(e)}