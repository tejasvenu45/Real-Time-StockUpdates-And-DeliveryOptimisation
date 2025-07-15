"""
Kafka client for event streaming and message processing
"""
import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError, KafkaTimeoutError
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
from collections import defaultdict
from services.common.database import db_manager
import uuid
logger = logging.getLogger(__name__)

class KafkaManager:
    """Manages Kafka connections, producers, and consumers"""
    
    # Define topic names
    TOPICS = {
        'SALES_EVENTS': 'sales-events',
        'INVENTORY_UPDATES': 'inventory-updates',
        'RESTOCK_REQUESTS': 'restock-requests',
        'FULFILLMENT_EVENTS': 'fulfillment-events',
        'DELIVERY_TRACKING': 'delivery-tracking',
        'demandsense-data':'demandsense-data',
        'DEMAND_FORECASTING': 'demand-forecasting',
        'ALERT_NOTIFICATIONS': 'alert-notifications'
    }
    
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.group_id = os.getenv("KAFKA_GROUP_ID", "warehouse-system")
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.running_consumers: Dict[str, bool] = {}
        self.restock_messages: List[Dict[str, Any]] = []
        self.fulfillment_messages: List[Dict[str, Any]] = []

    async def start_producer(self):
        """Initialize and start Kafka producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retry_backoff_ms=100,
                request_timeout_ms=30000,
                acks='all'  # Wait for all replicas to acknowledge
            )
            await self.producer.start()
            logger.info("Kafka producer started successfully")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise
    
    async def stop_producer(self):
        """Stop Kafka producer"""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")
    
    async def create_topics(self):
        """Create all required Kafka topics"""
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id='warehouse_admin'
            )
            
            topics_to_create = []
            for topic_name in self.TOPICS.values():
                topic = NewTopic(
                    name=topic_name,
                    num_partitions=3,
                    replication_factor=1
                )
                topics_to_create.append(topic)
            
            try:
                admin_client.create_topics(topics_to_create, validate_only=False)
                logger.info(f"Created Kafka topics: {list(self.TOPICS.values())}")
            except TopicAlreadyExistsError:
                logger.info("Kafka topics already exist")
            
            admin_client.close()
            
        except Exception as e:
            logger.error(f"Error creating Kafka topics: {e}")
            raise
    
    async def send_message(self, topic: str, message: Dict[str, Any], key: str = None):
        """Send a message to Kafka topic"""
        if not self.producer:
            await self.start_producer()
        
        try:
            # Add metadata to message
            enriched_message = {
                **message,
                'timestamp': datetime.utcnow().isoformat(),
                'source_service': os.getenv('SERVICE_NAME', 'unknown')
            }
            
            future = await self.producer.send(topic, enriched_message, key=key)
            record_metadata = await future
            
            logger.debug(f"Message sent to {topic}: partition {record_metadata.partition}, offset {record_metadata.offset}")
            return record_metadata
            
        except KafkaTimeoutError:
            logger.error(f"Timeout sending message to topic {topic}")
            raise
        except Exception as e:
            logger.error(f"Error sending message to topic {topic}: {e}")
            raise
    
    async def send_sales_event(self, store_id: str, product_id: str, quantity: int, price: float):
        """Send a sales event"""
        message = {
            'event_type': 'sale',
            'store_id': store_id,
            'product_id': product_id,
            'quantity': quantity,
            'price': price,
            'total_amount': quantity * price
        }
        await self.send_message(self.TOPICS['SALES_EVENTS'], message, key=store_id)
    
    async def send_inventory_update(self, store_id: str, product_id: str, current_stock: int, 
                                  previous_stock: int, change_type: str):
        """Send inventory update event"""
        message = {
            'event_type': 'inventory_update',
            'store_id': store_id,
            'product_id': product_id,
            'current_stock': current_stock,
            'previous_stock': previous_stock,
            'change_quantity': current_stock - previous_stock,
            'change_type': change_type  # 'sale', 'restock', 'adjustment'
        }
        await self.send_message(self.TOPICS['INVENTORY_UPDATES'], message, key=f"{store_id}:{product_id}")
    
    async def send_restock_request(self, store_id: str, product_id: str, requested_quantity: int, 
                                 priority: str, reason: str):
        """Send restock request event"""
        message = {
            'event_type': 'restock_request',
            'store_id': store_id,
            'product_id': product_id,
            'requested_quantity': requested_quantity,
            'priority': priority,  # 'low', 'medium', 'high', 'critical'
            'reason': reason
        }
        await self.send_message(self.TOPICS['RESTOCK_REQUESTS'], message, key=store_id)
    
    async def send_fulfillment_event(self, request_id: str, store_id: str, status: str, 
                                   products: List[Dict], vehicle_id: str = None):
        """Send fulfillment event"""
        message = {
            'event_type': 'fulfillment_update',
            'request_id': request_id,
            'store_id': store_id,
            'status': status,  # 'processing', 'packed', 'shipped', 'delivered'
            'products': products,
            'vehicle_id': vehicle_id
        }
        await self.send_message(self.TOPICS['FULFILLMENT_EVENTS'], message, key=request_id)
    
    async def create_consumer(self, topic: str, group_id: str = None) -> AIOKafkaConsumer:
        """Create a Kafka consumer for a specific topic"""
        consumer_group = group_id or f"{self.group_id}-{topic}"
        
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=consumer_group,
            auto_offset_reset='latest',
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
            key_deserializer=lambda k: k.decode('utf-8') if k else None
        )
        
        self.consumers[topic] = consumer
        return consumer
    
    async def start_consumer(self, topic: str, message_handler: Callable, group_id: str = None):
        """Start consuming messages from a topic"""
        consumer = await self.create_consumer(topic, group_id)
        
        try:
            await consumer.start()
            self.running_consumers[topic] = True
            logger.info(f"Started consumer for topic: {topic}")
            
            async for message in consumer:
                if not self.running_consumers.get(topic, False):
                    break
                
                try:
                    await message_handler(message.value, message.key, message.offset, message.partition)
                except Exception as e:
                    logger.error(f"Error processing message from {topic}: {e}")
                    # Continue processing other messages
                    continue
                    
        except Exception as e:
            logger.error(f"Error in consumer for topic {topic}: {e}")
            raise
        finally:
            await consumer.stop()
            logger.info(f"Stopped consumer for topic: {topic}")
    
    
    async def get_all_restock_messages(self) -> List[Dict[str, Any]]:
        """Fetch all messages from the restock-requests topic"""
        topic = self.TOPICS['RESTOCK_REQUESTS']
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            group_id=None  # Read without group tracking
        )

        await consumer.start()
        messages = []

        try:
            partitions = consumer.assignment()
            if not partitions:
                # Need to wait for partition assignment
                await consumer.seek_to_beginning()
                await asyncio.sleep(1)
                partitions = consumer.assignment()

            # Get beginning and end offsets for each partition
            end_offsets = await consumer.end_offsets(partitions)
            for tp in partitions:
                await consumer.seek_to_beginning(tp)

            while True:
                msg_batch = await consumer.getmany(timeout_ms=1000)
                empty = True

                for tp, batch in msg_batch.items():
                    for msg in batch:
                        empty = False
                        messages.append({
                            "key": msg.key,
                            "offset": msg.offset,
                            "partition": msg.partition,
                            "timestamp": msg.timestamp,
                            "message": msg.value
                        })

                if empty:
                    break

        finally:
            await consumer.stop()

        return messages


    async def start_restock_consumer(self):
        """Start consumer for restock-requests topic"""
        await self.start_consumer(self.TOPICS['RESTOCK_REQUESTS'], self.handle_restock_message)

    async def stop_consumer(self, topic: str):
        """Stop consumer for a specific topic"""
        self.running_consumers[topic] = False
        if topic in self.consumers:
            await self.consumers[topic].stop()
            del self.consumers[topic]

    async def handle_restock_message(self, value: Dict[str, Any], key: str, offset: int, partition: int):
        """Handle messages from restock-requests topic"""
        logger.info(f"Consumed restock request message from partition {partition}, offset {offset}: {value}")
        self.restock_messages.append({
            "key": key,
            "offset": offset,
            "partition": partition,
            "message": value
        })

    
    async def stop_all_consumers(self):
        """Stop all running consumers"""
        for topic in list(self.running_consumers.keys()):
            await self.stop_consumer(topic)
    
    async def health_check(self) -> bool:
        """Check if Kafka connection is healthy"""
        try:
            if not self.producer:
                await self.start_producer()
            
            # Try to send a simple health check message
            test_message = {'health_check': True, 'timestamp': datetime.utcnow().isoformat()}
            await self.send_message('health-check', test_message)
            return True
            
        except Exception as e:
            logger.error(f"Kafka health check failed: {e}")
            return False
    
    async def process_restock_requests_and_generate_fulfillments(self):
        """Aggregate restock requests and send fulfillment events"""
        restock_messages = await self.get_all_restock_messages()

        store_requests = defaultdict(list)

        for msg in restock_messages:
            data = msg['message']
            store_id = data['store_id']
            product_id = data['product_id']

            # 🔍 Inline product fetch + volume calculation
            product = await db_manager.find_one("products", {"product_id": product_id})
            if not product:
                logger.warning(f"⚠️ Product {product_id} not found. Skipping.")
                continue

            dimensions = product.get("dimensions", {})
            length = dimensions.get("length", 0)
            width = dimensions.get("width", 0)
            height = dimensions.get("height", 0)
            volume = length * width * height

            product_entry = {
                "product_id": product_id,
                "requested_quantity": data['requested_quantity'],
                "priority": data['priority'],
                "reason": data['reason'],
                "volume": volume  # ✅ Volume in place of placeholder
            }
            store_requests[store_id].append(product_entry)

        # Clear old list if re-used
        self.fulfillment_messages = []

        for store_id, products in store_requests.items():
            fulfillment_id = f"FUL_{uuid.uuid4().hex[:8].upper()}"
            fulfillment_event = {
                "event_type": "fulfillment_request",
                "request_id": fulfillment_id,
                "store_id": store_id,
                "status": "allocated",
                "products": products,
                "created_at": datetime.utcnow().isoformat()
            }

            self.fulfillment_messages.append(fulfillment_event)

            await self.send_message(
                self.TOPICS["FULFILLMENT_EVENTS"],
                fulfillment_event,
                key=store_id
            )

            print(f"✅ Fulfillment event sent for {store_id} with {len(products)} items")

        # Simulate clearing processed restocks
        self.restock_messages = []
kafka_manager = KafkaManager()

async def get_kafka_manager() -> KafkaManager:
    """Dependency injection for Kafka manager"""
    return kafka_manager

async def initialize_kafka():
    """Initialize Kafka topics and producer"""
    try:
        await kafka_manager.create_topics()
        await kafka_manager.start_producer()
        # ✅ Run consumer in background
        asyncio.create_task(kafka_manager.start_restock_consumer())
        logger.info("Kafka initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka: {e}")
        raise

async def cleanup_kafka():
    """Cleanup Kafka connections"""
    await kafka_manager.stop_all_consumers()
    await kafka_manager.stop_producer()
    logger.info("Kafka cleanup completed")