"""
Fulfillment Service - FastAPI application
Main entry point for warehouse fulfillment and AI-powered optimization
"""
import os
import sys
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.common.database import db_manager, close_database
from services.common.kafka_client import initialize_kafka, cleanup_kafka, kafka_manager
from services.common.models import HealthCheck
from services.fulfillment_service.routes.fulfillment import router as fulfillment_router
from services.fulfillment_service.services.fulfillment_service import FulfillmentService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set service name for Kafka messages
os.environ['SERVICE_NAME'] = 'fulfillment-service'

# Global fulfillment service instance for Kafka consumers
fulfillment_service_instance = None

async def start_kafka_consumers():
    """Start Kafka consumers for restock requests and inventory updates"""
    global fulfillment_service_instance
    
    try:
        # Create fulfillment service instance
        await db_manager.connect()
        fulfillment_service_instance = FulfillmentService(db_manager)
        
        # Start consuming restock requests
        asyncio.create_task(
            kafka_manager.start_consumer(
                kafka_manager.TOPICS['RESTOCK_REQUESTS'],
                fulfillment_service_instance.handle_restock_request,
                group_id="fulfillment-restock-consumer"
            )
        )
        
        # Start consuming inventory updates
        asyncio.create_task(
            kafka_manager.start_consumer(
                kafka_manager.TOPICS['INVENTORY_UPDATES'],
                fulfillment_service_instance.handle_inventory_update,
                group_id="fulfillment-inventory-consumer"
            )
        )
        
        logger.info("Kafka consumers started for fulfillment service")
        
    except Exception as e:
        logger.error(f"Failed to start Kafka consumers: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Fulfillment Service...")
    
    try:
        # Initialize database
        if not await db_manager.connect():
            raise RuntimeError("Failed to connect to database")
        logger.info("Database connected successfully")
        
        # Initialize Kafka
        await initialize_kafka()
        logger.info("Kafka initialized successfully")
        
        # Start Kafka consumers
        await start_kafka_consumers()
        logger.info("Kafka consumers started")
        
        logger.info("Fulfillment Service started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start Fulfillment Service: {e}")
        raise
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down Fulfillment Service...")
        await cleanup_kafka()
        await close_database()
        logger.info("Fulfillment Service shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Warehouse Fulfillment Service",
    description="AI-powered microservice for warehouse fulfillment and order optimization",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": f"Validation error: {str(exc)}",
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_status = "healthy" if db_manager.database is not None else "unhealthy"
        
        # Check Kafka connection
        kafka_status = "healthy" if await kafka_manager.health_check() else "unhealthy"
        
        # Check LLM service (we'll add this)
        llm_status = "healthy"  # Will implement LLM health check
        
        overall_status = "healthy" if all([
            db_status == "healthy",
            kafka_status == "healthy",
            llm_status == "healthy"
        ]) else "unhealthy"
        
        return HealthCheck(
            service="fulfillment-service",
            status=overall_status,
            version="1.0.0",
            dependencies={
                "database": db_status,
                "kafka": kafka_status,
                "llm": llm_status
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            service="fulfillment-service",
            status="unhealthy",
            version="1.0.0",
            dependencies={
                "database": "unknown",
                "kafka": "unknown",
                "llm": "unknown"
            }
        )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "success": True,
        "message": "Warehouse Fulfillment Service is running",
        "data": {
            "service": "fulfillment-service",
            "version": "1.0.0",
            "features": [
                "AI-powered order optimization",
                "Warehouse inventory management", 
                "Restock request processing",
                "Vehicle capacity planning",
                "Product recommendation engine"
            ],
            "endpoints": [
                "/health",
                "/docs",
                "/api/v1/fulfillment",
                "/api/v1/warehouse",
                "/api/v1/optimization"
            ]
        },
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }

# Include routers
app.include_router(
    fulfillment_router,
    prefix="/api/v1",
    tags=["fulfillment"]
)

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("FULFILLMENT_SERVICE_PORT", "8003"))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    logger.info(f"Starting Fulfillment Service on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )