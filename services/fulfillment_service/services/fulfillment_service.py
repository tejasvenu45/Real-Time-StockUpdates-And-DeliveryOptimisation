"""
Fulfillment Service Business Logic
AI-powered warehouse fulfillment and order optimization
"""
import os
import json
import uuid
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import google.generativeai as genai
from decimal import Decimal

from services.common.database import DatabaseManager
from services.common.kafka_client import kafka_manager
from services.common.models import Priority

logger = logging.getLogger(__name__)

class FulfillmentService:
    """AI-powered fulfillment and warehouse management service"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.setup_llm()
    
    def setup_llm(self):
        """Initialize LLM (Gemini) for AI-powered optimization"""
        try:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if gemini_api_key:
                genai.configure(api_key=gemini_api_key)
                self.llm_model = genai.GenerativeModel('gemini-pro')
                self.llm_available = True
                logger.info("Gemini LLM initialized successfully")
            else:
                self.llm_available = False
                logger.warning("GEMINI_API_KEY not found, AI features will use fallback logic")
        except Exception as e:
            self.llm_available = False
            logger.error(f"Failed to initialize LLM: {e}")
    
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
                                     priority: Optional[Priority] = None,
                                     store_id: Optional[str] = None,
                                     page: int = 1, size: int = 20) -> List[Dict]:
        """Get fulfillment requests with filtering"""
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if priority:
            # Handle Priority enum properly
            if hasattr(priority, 'value'):
                filter_dict["priority"] = priority.value
            else:
                filter_dict["priority"] = str(priority)
        if store_id:
            filter_dict["store_id"] = store_id
        
        skip = (page - 1) * size
        sort = [("created_at", -1)]
        
        try:
            requests = await self.db.find_many("fulfillment_requests", filter_dict, limit=size, sort=sort)
            # Convert ObjectId and other non-serializable objects
            serialized_requests = []
            for request in requests:
                if isinstance(request, dict):
                    # Remove or convert ObjectId
                    if '_id' in request:
                        request['_id'] = str(request['_id'])
                    serialized_requests.append(request)
            
            return serialized_requests[skip:skip + size] if len(serialized_requests) > skip else []
        except Exception as e:
            logger.error(f"Error retrieving fulfillment requests: {e}")
            return []
    
    async def count_fulfillment_requests(self, status: Optional[str] = None,
                                       priority: Optional[Priority] = None,
                                       store_id: Optional[str] = None) -> int:
        """Count fulfillment requests"""
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if priority:
            # Handle Priority enum properly
            if hasattr(priority, 'value'):
                filter_dict["priority"] = priority.value
            else:
                filter_dict["priority"] = str(priority)
        if store_id:
            filter_dict["store_id"] = store_id
        
        try:
            return await self.db.count_documents("fulfillment_requests", filter_dict)
        except Exception as e:
            logger.error(f"Error counting fulfillment requests: {e}")
            return 0
    
    async def process_fulfillment_request(self, request_id: str) -> Dict[str, Any]:
        """Process a fulfillment request with AI optimization"""
        try:
            # Get request details
            request = await self.db.find_one("fulfillment_requests", {"request_id": request_id})
            if not request:
                raise ValueError(f"Fulfillment request {request_id} not found")
            
            # Update status to processing
            await self.update_request_status(request_id, "processing", "Started AI-powered processing")
            
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
            
            # Use AI to optimize the fulfillment
            optimization_result = await self.optimize_fulfillment_with_ai(request)
            
            # Create shipment plan
            shipment_plan = await self.create_shipment_plan(request, optimization_result)
            
            # Allocate stock
            allocation_result = await self.allocate_warehouse_stock({
                "request_id": request_id,
                "products": shipment_plan['products'],
                "destination_store": request['store_id']
            })
            
            # Update request status
            await self.update_request_status(
                request_id, 
                "allocated", 
                f"Stock allocated successfully. Shipment planned with {len(shipment_plan['products'])} products."
            )
            
            # Send fulfillment event
            await kafka_manager.send_fulfillment_event(
                request_id=request_id,
                store_id=request['store_id'],
                status="allocated",
                products=shipment_plan['products']
            )
            
            return {
                "request_id": request_id,
                "status": "allocated",
                "shipment_plan": shipment_plan,
                "allocation": allocation_result,
                "ai_optimization": optimization_result
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
    # AI-POWERED OPTIMIZATION
    # =============================================================================
    
    async def optimize_fulfillment_with_ai(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to optimize fulfillment with additional product recommendations"""
        try:
            if not self.llm_available:
                return await self.fallback_optimization(request)
            
            # Get context data for AI
            context = await self.gather_optimization_context(request)
            
            # Create AI prompt
            prompt = self.create_optimization_prompt(request, context)
            
            # Call LLM
            response = await self.call_llm_async(prompt)
            
            # Parse and validate AI response
            optimization_result = self.parse_ai_optimization_response(response, context)
            
            logger.info(f"AI optimization completed for request {request['request_id']}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"AI optimization failed, using fallback: {e}")
            return await self.fallback_optimization(request)
    
    async def gather_optimization_context(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Gather context data for AI optimization"""
        store_id = request['store_id']
        product_id = request['product_id']
        
        # Get store information
        store = await self.db.find_one("stores", {"store_id": store_id})
        
        # Get product information
        product = await self.db.find_one("products", {"product_id": product_id})
        
        # Get store's recent sales history
        recent_sales = await self.db.find_many(
            "sales", 
            {"store_id": store_id}, 
            limit=50, 
            sort=[("timestamp", -1)]
        )
        
        # Get current store inventory levels
        store_inventory = await self.db.find_many(
            "inventory",
            {"store_id": store_id}
        )
        
        # Get nearby stores (for potential consolidated delivery)
        nearby_stores = await self.find_nearby_stores(store, max_distance_km=25.0)
        
        # Get warehouse inventory
        warehouse_inventory = await self.db.find_many("warehouse_inventory", {})
        
        return {
            "store": store,
            "product": product,
            "recent_sales": recent_sales[:10],  # Last 10 sales for context
            "store_inventory": store_inventory,
            "nearby_stores": nearby_stores,
            "warehouse_inventory": warehouse_inventory,
            "request_priority": request.get('priority', 'medium')
        }
    
    def create_optimization_prompt(self, request: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Create prompt for AI optimization"""
        store = context['store']
        product = context['product']
        recent_sales = context['recent_sales']
        
        prompt = f"""
        You are an intelligent warehouse fulfillment optimization system. Your task is to optimize a delivery to maximize efficiency and store performance.
        
        FULFILLMENT REQUEST:
        - Store: {store.get('name', 'Unknown')} (ID: {request['store_id']})
        - Product Requested: {product.get('name', 'Unknown')} (ID: {request['product_id']})
        - Quantity Requested: {request['requested_quantity']}
        - Priority: {request.get('priority', 'medium')}
        - Store Location: {store.get('address', {}).get('city', 'Unknown')}
        
        STORE CONTEXT:
        - Store Category: {product.get('category', 'Unknown')}
        - Recent Sales Pattern: {len(recent_sales)} recent transactions
        - Store Capacity: {store.get('capacity', {})}
        
        OPTIMIZATION GOALS:
        1. Fulfill the primary request efficiently
        2. Recommend additional products that would benefit this store
        3. Consider products that complement the requested item
        4. Optimize vehicle space utilization
        5. Include slow-moving inventory if it makes sense for this store
        
        Please provide recommendations in this JSON format:
        {{
            "primary_fulfillment": {{
                "product_id": "{request['product_id']}",
                "recommended_quantity": <quantity>,
                "reasoning": "<explanation>"
            }},
            "additional_products": [
                {{
                    "product_id": "<product_id>",
                    "recommended_quantity": <quantity>,
                    "reasoning": "<why this product makes sense>",
                    "priority": "<high|medium|low>"
                }}
            ],
            "optimization_notes": "<overall strategy explanation>",
            "estimated_value_add": "<expected benefit>"
        }}
        
        Focus on practical, business-smart recommendations that will help the store serve customers better.
        """
        
        return prompt
    
    async def call_llm_async(self, prompt: str) -> str:
        """Call LLM asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.llm_model.generate_content(prompt).text
        )
    
    def parse_ai_optimization_response(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate AI optimization response"""
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            json_str = response[start_idx:end_idx]
            
            ai_result = json.loads(json_str)
            
            # Validate and sanitize the response
            return {
                "ai_recommendations": ai_result,
                "primary_quantity": ai_result.get("primary_fulfillment", {}).get("recommended_quantity"),
                "additional_products": ai_result.get("additional_products", []),
                "optimization_strategy": ai_result.get("optimization_notes", ""),
                "ai_confidence": "high",
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse AI response, using fallback: {e}")
            return {
                "ai_recommendations": None,
                "primary_quantity": None,
                "additional_products": [],
                "optimization_strategy": "Fallback optimization used",
                "ai_confidence": "low",
                "error": str(e)
            }
    
    async def fallback_optimization(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback optimization when AI is unavailable"""
        return {
            "ai_recommendations": None,
            "primary_quantity": request['requested_quantity'],
            "additional_products": [],
            "optimization_strategy": "Basic fulfillment without AI optimization",
            "ai_confidence": "fallback",
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
                            "available_stock": availability['current_stock'] - quantity,
                            "reserved_stock": {"$inc": quantity},
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
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    async def sync_store_inventory(self, store_id: str, product_id: str, 
                                 current_stock: int, change_type: str):
        """Sync store inventory state for optimization"""
        # Update store inventory cache in warehouse system
        update_data = {
            "current_stock": current_stock,
            "last_updated": datetime.utcnow(),
            "change_type": change_type
        }
        
        await self.db.update_one(
            "store_inventory_cache",
            {"store_id": store_id, "product_id": product_id},
            update_data
        )
    
    async def find_nearby_stores(self, store: Dict[str, Any], max_distance_km: float = 25.0) -> List[Dict]:
        """Find stores within delivery radius for potential consolidation"""
        # This would implement geospatial queries in a real system
        # For now, return empty list as placeholder
        return []
    
    async def create_shipment_plan(self, request: Dict[str, Any], 
                                 optimization_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed shipment plan"""
        products = [{
            "product_id": request['product_id'],
            "quantity": optimization_result.get('primary_quantity', request['requested_quantity']),
            "type": "primary"
        }]
        
        # Add AI-recommended additional products
        for additional in optimization_result.get('additional_products', []):
            products.append({
                "product_id": additional['product_id'],
                "quantity": additional['recommended_quantity'],
                "type": "additional",
                "reasoning": additional.get('reasoning', '')
            })
        
        return {
            "shipment_id": f"SHIP_{uuid.uuid4().hex[:8].upper()}",
            "request_id": request['request_id'],
            "destination_store": request['store_id'],
            "products": products,
            "optimization_applied": optimization_result.get('optimization_strategy', ''),
            "estimated_weight": sum(p.get('quantity', 0) * 2.5 for p in products),  # Rough estimate
            "created_at": datetime.utcnow()
        }
    
    # Placeholder methods for additional functionality
    async def get_warehouse_inventory(self, **kwargs) -> List[Dict]:
        """Get warehouse inventory (placeholder)"""
        return []
    
    async def count_warehouse_inventory(self, **kwargs) -> int:
        """Count warehouse inventory (placeholder)"""
        return 0
    
    async def update_warehouse_inventory(self, product_id: str, update_data: Dict) -> bool:
        """Update warehouse inventory (placeholder)"""
        return True
    
    async def optimize_shipment_with_ai(self, shipment_data: Dict, use_ai: bool = True) -> Dict:
        """Optimize shipment with AI (placeholder)"""
        return {"optimization": "placeholder"}
    
    async def get_ai_product_recommendations(self, request_data: Dict) -> Dict:
        """Get AI product recommendations (placeholder)"""
        return {"recommendations": []}
    
    async def consolidate_nearby_orders(self, store_ids: List[str], max_distance_km: float) -> Dict:
        """Consolidate nearby orders (placeholder)"""
        return {"consolidation": "placeholder"}
    
    async def get_fulfillment_metrics(self, **kwargs) -> Dict:
        """Get fulfillment metrics (placeholder)"""
        return {"metrics": "placeholder"}
    
    async def get_warehouse_utilization(self) -> Dict:
        """Get warehouse utilization (placeholder)"""
        return {"utilization": "placeholder"}
    
    async def get_ai_performance_metrics(self, days: int) -> Dict:
        """Get AI performance metrics (placeholder)"""
        return {"ai_metrics": "placeholder"}