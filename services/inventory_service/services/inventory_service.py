"""
Inventory Service Business Logic
Core business logic for inventory management
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal

from services.common.database import DatabaseManager
from services.common.kafka_client import kafka_manager
from services.common.models import (
    Store, Product, InventoryItem, InventoryItemCreate, SaleTransaction, RestockRequest,
    StoreCreateRequest, ProductCreateRequest, InventoryUpdateRequest, SaleRequest,
    Priority, RequestStatus, ProductCategory
)

logger = logging.getLogger(__name__)

class InventoryService:
    """Business logic for inventory management"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    # =============================================================================
    # STORE MANAGEMENT
    # =============================================================================
    
    async def create_store(self, store_data: StoreCreateRequest) -> str:
        """Create a new store"""
        # Check if store already exists
        existing = await self.db.find_one("stores", {"store_id": store_data.store_id})
        if existing:
            raise ValueError(f"Store with ID {store_data.store_id} already exists")
        
        # Create store document
        store_doc = store_data.dict()
        store_doc["status"] = "active"
        
        # Insert into database
        await self.db.insert_one("stores", store_doc)
        
        logger.info(f"Created store: {store_data.store_id}")
        return store_data.store_id
    
    async def get_stores(self, page: int = 1, size: int = 10, status: Optional[str] = None) -> List[Dict]:
        """Get stores with pagination and filtering"""
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        
        skip = (page - 1) * size
        sort = [("created_at", -1)]
        
        stores = await self.db.find_many("stores", filter_dict, limit=size, sort=sort, skip=skip)
        return stores
    
    async def get_store(self, store_id: str) -> Optional[Dict]:
        """Get a specific store"""
        return await self.db.find_one("stores", {"store_id": store_id})
    
    async def update_store(self, store_id: str, store_data: StoreCreateRequest) -> bool:
        """Update a store"""
        update_data = store_data.dict()
        return await self.db.update_one("stores", {"store_id": store_id}, update_data)
    
    async def count_stores(self, status: Optional[str] = None) -> int:
        """Count stores"""
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        return await self.db.count_documents("stores", filter_dict)
    
    # =============================================================================
    # PRODUCT MANAGEMENT
    # =============================================================================
    
    async def create_product(self, product_data: ProductCreateRequest) -> str:
        """Create a new product"""
        # Check if product already exists
        existing = await self.db.find_one("products", {"product_id": product_data.product_id})
        if existing:
            raise ValueError(f"Product with ID {product_data.product_id} already exists")
        
        # Create product document
        product_doc = product_data.dict()
        product_doc["is_active"] = True
        
        # Insert into database
        await self.db.insert_one("products", product_doc)
        
        logger.info(f"Created product: {product_data.product_id}")
        return product_data.product_id
    
    async def get_products(self, page: int = 1, size: int = 10, 
                          category: Optional[str] = None, active_only: bool = True) -> List[Dict]:
        """Get products with pagination and filtering"""
        filter_dict = {}
        if category:
            filter_dict["category"] = category
        if active_only:
            filter_dict["is_active"] = True
        
        skip = (page - 1) * size
        sort = [("created_at", -1)]
        
        products = await self.db.find_many("products", filter_dict, limit=size, sort=sort, skip=skip)
        return products
    
    async def get_product(self, product_id: str) -> Optional[Dict]:
        """Get a specific product"""
        return await self.db.find_one("products", {"product_id": product_id})
    
    async def count_products(self, category: Optional[str] = None, active_only: bool = True) -> int:
        """Count products"""
        filter_dict = {}
        if category:
            filter_dict["category"] = category
        if active_only:
            filter_dict["is_active"] = True
        return await self.db.count_documents("products", filter_dict)
    
    # =============================================================================
    # INVENTORY MANAGEMENT
    # =============================================================================
    
    async def create_inventory_item(self, inventory_data: InventoryItemCreate) -> str:
        """Create a new inventory item"""
        # Validate store and product exist
        store = await self.get_store(inventory_data.store_id)
        if not store:
            raise ValueError(f"Store {inventory_data.store_id} not found")
        
        product = await self.get_product(inventory_data.product_id)
        if not product:
            raise ValueError(f"Product {inventory_data.product_id} not found")
        
        # Check if inventory item already exists
        existing = await self.db.find_one("inventory", {
            "store_id": inventory_data.store_id,
            "product_id": inventory_data.product_id
        })
        if existing:
            raise ValueError(f"Inventory item already exists for store {inventory_data.store_id} and product {inventory_data.product_id}")
        
        # Create full inventory item with calculated available_stock
        inventory_item = InventoryItem(
            store_id=inventory_data.store_id,
            product_id=inventory_data.product_id,
            current_stock=inventory_data.current_stock,
            reserved_stock=inventory_data.reserved_stock,
            available_stock=inventory_data.current_stock - inventory_data.reserved_stock,  # Calculate it
            reorder_threshold=inventory_data.reorder_threshold,
            warning_threshold=inventory_data.warning_threshold,
            critical_threshold=inventory_data.critical_threshold,
            max_capacity=inventory_data.max_capacity,
            location=inventory_data.location
        )
        
        # Create inventory document
        inventory_doc = inventory_item.model_dump()
        
        # Insert into database
        doc_id = await self.db.insert_one("inventory", inventory_doc)
        
        # Send inventory update event
        await kafka_manager.send_inventory_update(
            store_id=inventory_data.store_id,
            product_id=inventory_data.product_id,
            current_stock=inventory_data.current_stock,
            previous_stock=0,
            change_type="initial_stock"
        )
        
        logger.info(f"Created inventory item: {inventory_data.store_id}/{inventory_data.product_id}")
        return doc_id
    
    async def get_inventory_items(self, store_id: Optional[str] = None, 
                                product_id: Optional[str] = None,
                                low_stock_only: bool = False,
                                page: int = 1, size: int = 20) -> List[Dict]:
        """Get inventory items with filtering"""
        filter_dict = {}
        if store_id:
            filter_dict["store_id"] = store_id
        if product_id:
            filter_dict["product_id"] = product_id
        
        skip = (page - 1) * size
        
        # Use aggregation for low stock filtering
        if low_stock_only:
            pipeline = [
                {"$match": filter_dict},
                {"$addFields": {
                    "is_low_stock": {
                        "$lte": ["$current_stock", "$warning_threshold"]
                    }
                }},
                {"$match": {"is_low_stock": True}},
                {"$sort": {"updated_at": -1}},
                {"$skip": skip},
                {"$limit": size}
            ]
            return await self.db.aggregate("inventory", pipeline)
        else:
            sort = [("updated_at", -1)]
            inventory_items = await self.db.find_many("inventory", filter_dict, limit=size, sort=sort, skip=skip)
            return inventory_items
    
    async def get_inventory_item(self, store_id: str, product_id: str) -> Optional[Dict]:
        """Get specific inventory item"""
        return await self.db.find_one("inventory", {
            "store_id": store_id,
            "product_id": product_id
        })
    
    async def update_inventory(self, store_id: str, product_id: str, 
                             update_data: InventoryUpdateRequest) -> bool:
        """Update inventory levels"""
        # Get current inventory
        current_inventory = await self.get_inventory_item(store_id, product_id)
        if not current_inventory:
            raise ValueError(f"Inventory item not found for store {store_id} and product {product_id}")
        
        # Calculate new stock level
        current_stock = current_inventory["current_stock"]
        new_stock = current_stock + update_data.quantity_change
        
        if new_stock < 0:
            raise ValueError("Insufficient stock for the requested operation")
        
        # Update inventory
        update_doc = {
            "current_stock": new_stock,
            "available_stock": max(0, new_stock - current_inventory.get("reserved_stock", 0))
        }
        
        # Update last restock date if adding stock
        if update_data.quantity_change > 0 and update_data.change_type == "restock":
            update_doc["last_restock_date"] = datetime.utcnow()
        
        # Update last sale date if reducing stock due to sale
        if update_data.quantity_change < 0 and update_data.change_type == "sale":
            update_doc["last_sale_date"] = datetime.utcnow()
        
        success = await self.db.update_one("inventory", {
            "store_id": store_id,
            "product_id": product_id
        }, update_doc)
        
        if success:
            # Send inventory update event
            await kafka_manager.send_inventory_update(
                store_id=store_id,
                product_id=product_id,
                current_stock=new_stock,
                previous_stock=current_stock,
                change_type=update_data.change_type
            )
            
            # Check if restock is needed
            await self._check_restock_threshold(store_id, product_id, new_stock, current_inventory)
            
            logger.info(f"Updated inventory: {store_id}/{product_id} by {update_data.quantity_change}")
        
        return success
    
    async def count_inventory_items(self, store_id: Optional[str] = None,
                                  product_id: Optional[str] = None,
                                  low_stock_only: bool = False) -> int:
        """Count inventory items"""
        filter_dict = {}
        if store_id:
            filter_dict["store_id"] = store_id
        if product_id:
            filter_dict["product_id"] = product_id
        
        if low_stock_only:
            pipeline = [
                {"$match": filter_dict},
                {"$addFields": {
                    "is_low_stock": {
                        "$lte": ["$current_stock", "$warning_threshold"]
                    }
                }},
                {"$match": {"is_low_stock": True}},
                {"$count": "total"}
            ]
            result = await self.db.aggregate("inventory", pipeline)
            return result[0]["total"] if result else 0
        else:
            return await self.db.count_documents("inventory", filter_dict)
    
    # =============================================================================
    # SALES MANAGEMENT
    # =============================================================================
    
    async def record_sale(self, sale_data: SaleRequest) -> str:
        """Record a sale transaction"""
        # Validate inventory availability
        inventory = await self.get_inventory_item(sale_data.store_id, sale_data.product_id)
        if not inventory:
            raise ValueError(f"Product {sale_data.product_id} not found in store {sale_data.store_id}")
        
        if inventory["available_stock"] < sale_data.quantity:
            raise ValueError(f"Insufficient stock. Available: {inventory['available_stock']}, Requested: {sale_data.quantity}")
        
        # Generate transaction ID
        transaction_id = f"TXN_{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate total amount
        total_amount = (sale_data.quantity * sale_data.unit_price) - sale_data.discount + sale_data.tax
        
        # Create sale transaction
        sale_doc = {
            "transaction_id": transaction_id,
            **sale_data.dict(),
            "total_amount": float(total_amount),
            "timestamp": datetime.utcnow()
        }
        
        # Insert sale transaction
        await self.db.insert_one("sales", sale_doc)
        
        # Update inventory
        inventory_update = InventoryUpdateRequest(
            store_id=sale_data.store_id,
            product_id=sale_data.product_id,
            quantity_change=-sale_data.quantity,
            change_type="sale",
            reference_id=transaction_id,
            notes=f"Sale transaction {transaction_id}"
        )
        
        await self.update_inventory(sale_data.store_id, sale_data.product_id, inventory_update)
        
        # Send sales event
        await kafka_manager.send_sales_event(
            store_id=sale_data.store_id,
            product_id=sale_data.product_id,
            quantity=sale_data.quantity,
            price=float(sale_data.unit_price)
        )
        
        logger.info(f"Recorded sale: {transaction_id}")
        return transaction_id
    
    async def get_sales(self, store_id: Optional[str] = None,
                       product_id: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       page: int = 1, size: int = 20) -> List[Dict]:
        """Get sales transactions with filtering"""
        filter_dict = {}
        if store_id:
            filter_dict["store_id"] = store_id
        if product_id:
            filter_dict["product_id"] = product_id
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            filter_dict["timestamp"] = date_filter
        
        skip = (page - 1) * size
        sort = [("timestamp", -1)]
        
        sales = await self.db.find_many("sales", filter_dict, limit=size, sort=sort, skip=skip)
        return sales
    
    async def count_sales(self, store_id: Optional[str] = None,
                         product_id: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> int:
        """Count sales transactions"""
        filter_dict = {}
        if store_id:
            filter_dict["store_id"] = store_id
        if product_id:
            filter_dict["product_id"] = product_id
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            filter_dict["timestamp"] = date_filter
        
        return await self.db.count_documents("sales", filter_dict)
    
    # =============================================================================
    # RESTOCK MANAGEMENT
    # =============================================================================
    
    async def create_restock_request(self, store_id: str, product_id: str,
                                   quantity: int, priority: Priority,
                                   reason: str, requested_by: Optional[str] = None) -> str:
        """Create a restock request"""
        # Validate store and product exist
        store = await self.get_store(store_id)
        if not store:
            raise ValueError(f"Store {store_id} not found")
        
        product = await self.get_product(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        # Generate request ID
        request_id = f"REQ_{uuid.uuid4().hex[:8].upper()}"
        
        # Create restock request
        request_doc = {
            "request_id": request_id,
            "store_id": store_id,
            "product_id": product_id,
            "requested_quantity": quantity,
            "priority": priority.value,
            "reason": reason,
            "status": RequestStatus.PENDING.value,
            "requested_by": requested_by,
            "created_at": datetime.utcnow()
        }
        
        # Insert request
        await self.db.insert_one("restock_requests", request_doc)
        
        # Send restock request event
        await kafka_manager.send_restock_request(
            store_id=store_id,
            product_id=product_id,
            requested_quantity=quantity,
            priority=priority.value,
            reason=reason
        )
        
        logger.info(f"Created restock request: {request_id}")
        return request_id
    
    async def get_restock_requests(self, store_id: Optional[str] = None,
                                 status: Optional[str] = None,
                                 priority: Optional[Priority] = None,
                                 page: int = 1, size: int = 20) -> List[Dict]:
        """Get restock requests with filtering"""
        filter_dict = {}
        if store_id:
            filter_dict["store_id"] = store_id
        if status:
            filter_dict["status"] = status
        if priority:
            filter_dict["priority"] = priority.value
        
        skip = (page - 1) * size
        sort = [("created_at", -1)]
        
        requests = await self.db.find_many("restock_requests", filter_dict, limit=size, sort=sort, skip=skip)
        return requests
    
    async def count_restock_requests(self, store_id: Optional[str] = None,
                                   status: Optional[str] = None,
                                   priority: Optional[Priority] = None) -> int:
        """Count restock requests"""
        filter_dict = {}
        if store_id:
            filter_dict["store_id"] = store_id
        if status:
            filter_dict["status"] = status
        if priority:
            filter_dict["priority"] = priority.value
        
        return await self.db.count_documents("restock_requests", filter_dict)
    
    # =============================================================================
    # ANALYTICS
    # =============================================================================
    
    async def get_inventory_summary(self, store_id: Optional[str] = None) -> Dict[str, Any]:
        """Get inventory summary analytics"""
        match_stage = {}
        if store_id:
            match_stage["store_id"] = store_id
        
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": None,
                "total_products": {"$sum": 1},
                "total_stock": {"$sum": "$current_stock"},
                "total_value": {"$sum": {"$multiply": ["$current_stock", "$price"]}},
                "low_stock_items": {
                    "$sum": {
                        "$cond": [
                            {"$lte": ["$current_stock", "$warning_threshold"]},
                            1,
                            0
                        ]
                    }
                },
                "out_of_stock_items": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$current_stock", 0]},
                            1,
                            0
                        ]
                    }
                }
            }}
        ]
        
        result = await self.db.aggregate("inventory", pipeline)
        
        if result:
            summary = result[0]
            summary.pop("_id", None)
            return summary
        else:
            return {
                "total_products": 0,
                "total_stock": 0,
                "total_value": 0,
                "low_stock_items": 0,
                "out_of_stock_items": 0
            }
    
    async def get_low_stock_alerts(self, store_id: Optional[str] = None) -> List[Dict]:
        """Get low stock alerts"""
        match_stage = {}
        if store_id:
            match_stage["store_id"] = store_id
        
        pipeline = [
            {"$match": match_stage},
            {"$addFields": {
                "stock_level": {
                    "$cond": [
                        {"$lte": ["$current_stock", "$critical_threshold"]}, "critical",
                        {"$cond": [
                            {"$lte": ["$current_stock", "$warning_threshold"]}, "warning",
                            "normal"
                        ]}
                    ]
                }
            }},
            {"$match": {"stock_level": {"$in": ["critical", "warning"]}}},
            {"$sort": {"stock_level": 1, "current_stock": 1}}
        ]
        
        return await self.db.aggregate("inventory", pipeline)
    
    # =============================================================================
    # PRIVATE METHODS
    # =============================================================================
    
    async def _check_restock_threshold(self, store_id: str, product_id: str, 
                                     current_stock: int, inventory_data: Dict):
        """Check if restock is needed and create automatic request"""
        reorder_threshold = inventory_data.get("reorder_threshold", 0)
        warning_threshold = inventory_data.get("warning_threshold", 0)
        critical_threshold = inventory_data.get("critical_threshold", 0)
        
        if current_stock <= critical_threshold:
            # Create critical restock request
            await self.create_restock_request(
                store_id=store_id,
                product_id=product_id,
                quantity=reorder_threshold * 2,  # Order double the reorder threshold
                priority=Priority.CRITICAL,
                reason="Automatic critical stock replenishment",
                requested_by="system"
            )
        elif current_stock <= reorder_threshold:
            # Create normal restock request
            await self.create_restock_request(
                store_id=store_id,
                product_id=product_id,
                quantity=reorder_threshold,
                priority=Priority.HIGH,
                reason="Automatic stock replenishment",
                requested_by="system"
            )