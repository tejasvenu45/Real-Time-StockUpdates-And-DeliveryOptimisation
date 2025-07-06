"""
Database connection and operations for MongoDB
"""
import os
import asyncio
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages MongoDB connections and operations"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.url = os.getenv("MONGODB_URL", "mongodb://admin:password@localhost:27017/warehouse_db?authSource=admin")
        self.database_name = os.getenv("MONGODB_DATABASE", "warehouse_db")
        
    async def connect(self) -> bool:
        """Establish connection to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.url)
            # Test the connection
            await self.client.admin.command('ping')
            self.database = self.client[self.database_name]
            logger.info(f"Connected to MongoDB: {self.database_name}")
            
            # Create indexes
            await self._create_indexes()
            return True
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client is not None:
            self.client.close()
            self.client = None
            self.database = None
            logger.info("Disconnected from MongoDB")
    
    async def _create_indexes(self):
        """Create necessary indexes for optimal performance"""
        try:
            # Stores collection indexes
            stores_collection = self.database.stores
            await stores_collection.create_index("store_id", unique=True)
            await stores_collection.create_index("location.coordinates", "2dsphere")
            
            # Products collection indexes
            products_collection = self.database.products
            await products_collection.create_index("product_id", unique=True)
            await products_collection.create_index("category")
            
            # Inventory collection indexes
            inventory_collection = self.database.inventory
            await inventory_collection.create_index([("store_id", 1), ("product_id", 1)], unique=True)
            await inventory_collection.create_index("last_updated")
            
            # Sales collection indexes
            sales_collection = self.database.sales
            await sales_collection.create_index([("store_id", 1), ("timestamp", -1)])
            await sales_collection.create_index("product_id")
            
            # Restock requests collection indexes
            restock_requests_collection = self.database.restock_requests
            await restock_requests_collection.create_index([("store_id", 1), ("status", 1)])
            await restock_requests_collection.create_index("priority")
            await restock_requests_collection.create_index("created_at")
            
            # Vehicles collection indexes
            vehicles_collection = self.database.vehicles
            await vehicles_collection.create_index("vehicle_id", unique=True)
            await vehicles_collection.create_index("status")
            
            # Deliveries collection indexes
            deliveries_collection = self.database.deliveries
            await deliveries_collection.create_index("delivery_id", unique=True)
            await deliveries_collection.create_index([("vehicle_id", 1), ("status", 1)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get a collection from the database"""
        if self.database is None:
            raise RuntimeError("Database not connected")
        return self.database[collection_name]
    
    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert a single document"""
        try:
            collection = self.get_collection(collection_name)
            document["created_at"] = datetime.utcnow()
            
            # Serialize document for MongoDB
            serialized_doc = self._serialize_document(document)
            
            result = await collection.insert_one(serialized_doc)
            return str(result.inserted_id)
        except DuplicateKeyError:
            raise ValueError(f"Document already exists in {collection_name}")
        except Exception as e:
            logger.error(f"Error inserting document in {collection_name}: {e}")
            raise
    
    async def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents"""
        try:
            collection = self.get_collection(collection_name)
            for doc in documents:
                doc["created_at"] = datetime.utcnow()
            
            # Serialize documents for MongoDB
            serialized_docs = [self._serialize_document(doc) for doc in documents]
            
            result = await collection.insert_many(serialized_docs)
            return [str(id) for id in result.inserted_ids]
        except Exception as e:
            logger.error(f"Error inserting documents in {collection_name}: {e}")
            raise
    
    async def find_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document"""
        try:
            collection = self.get_collection(collection_name)
            return await collection.find_one(filter_dict)
        except Exception as e:
            logger.error(f"Error finding document in {collection_name}: {e}")
            raise
    
    async def find_many(self, collection_name: str, filter_dict: Dict[str, Any] = None, 
                       limit: int = None, sort: List[tuple] = None, skip: int = None) -> List[Dict[str, Any]]:
        """Find multiple documents"""
        try:
            collection = self.get_collection(collection_name)
            cursor = collection.find(filter_dict or {})
            
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
                
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error finding documents in {collection_name}: {e}")
            raise
    
    async def update_one(self, collection_name: str, filter_dict: Dict[str, Any], 
                        update_dict: Dict[str, Any]) -> bool:
        """Update a single document"""
        try:
            collection = self.get_collection(collection_name)
            update_dict["updated_at"] = datetime.utcnow()
            
            # Serialize update document
            serialized_update = self._serialize_document(update_dict)
            
            result = await collection.update_one(filter_dict, {"$set": serialized_update})
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating document in {collection_name}: {e}")
            raise
    
    async def update_many(self, collection_name: str, filter_dict: Dict[str, Any], 
                         update_dict: Dict[str, Any]) -> int:
        """Update multiple documents"""
        try:
            collection = self.get_collection(collection_name)
            update_dict["updated_at"] = datetime.utcnow()
            
            # Serialize update document
            serialized_update = self._serialize_document(update_dict)
            
            result = await collection.update_many(filter_dict, {"$set": serialized_update})
            return result.modified_count
        except Exception as e:
            logger.error(f"Error updating documents in {collection_name}: {e}")
            raise
    
    async def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        """Delete a single document"""
        try:
            collection = self.get_collection(collection_name)
            result = await collection.delete_one(filter_dict)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document in {collection_name}: {e}")
            raise
    
    async def count_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> int:
        """Count documents in collection"""
        try:
            collection = self.get_collection(collection_name)
            return await collection.count_documents(filter_dict or {})
        except Exception as e:
            logger.error(f"Error counting documents in {collection_name}: {e}")
            raise
    
    async def aggregate(self, collection_name: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute aggregation pipeline"""
        try:
            collection = self.get_collection(collection_name)
            cursor = collection.aggregate(pipeline)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error executing aggregation in {collection_name}: {e}")
            raise
    
    def _serialize_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize document for MongoDB storage"""
        import decimal
        import enum
        from datetime import datetime
        from bson import ObjectId
        
        def serialize_value(value):
            if isinstance(value, decimal.Decimal):
                return float(value)
            elif isinstance(value, enum.Enum):
                return value.value
            elif isinstance(value, datetime):
                return value
            elif isinstance(value, ObjectId):
                return value  # Keep ObjectId as-is for MongoDB storage
            elif isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [serialize_value(item) for item in value]
            else:
                return value
        
        return {key: serialize_value(value) for key, value in document.items()}

# Global database manager instance
db_manager = DatabaseManager()

async def get_database() -> DatabaseManager:
    """Dependency injection for database"""
    if db_manager.database is None:
        await db_manager.connect()
    return db_manager

async def close_database():
    """Close database connection"""
    await db_manager.disconnect()