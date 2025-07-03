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
        'DEMAND_FORECASTING': 'demand-forecasting',
        'ALERT_NOTIFICATIONS': 'alert-notifications'
    }
    
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.group_id = os.getenv("KAFKA_GROUP_ID", "warehouse-system")
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.running_consumers: Dict[str, bool] = {}
    
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
    
    async def stop_consumer(self, topic: str):
        """Stop consumer for a specific topic"""
        self.running_consumers[topic] = False
        if topic in self.consumers:
            await self.consumers[topic].stop()
            del self.consumers[topic]
    
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

# Global Kafka manager instance
kafka_manager = KafkaManager()

async def get_kafka_manager() -> KafkaManager:
    """Dependency injection for Kafka manager"""
    return kafka_manager

async def initialize_kafka():
    """Initialize Kafka topics and producer"""
    try:
        await kafka_manager.create_topics()
        await kafka_manager.start_producer()
        logger.info("Kafka initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka: {e}")
        raise

async def cleanup_kafka():
    """Cleanup Kafka connections"""
    await kafka_manager.stop_all_consumers()
    await kafka_manager.stop_producer()
    logger.info("Kafka cleanup completed")