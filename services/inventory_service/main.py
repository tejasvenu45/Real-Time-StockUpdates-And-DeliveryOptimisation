"""
Inventory Service - FastAPI application
Main entry point for the inventory management microservice
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime


from dotenv import load_dotenv
load_dotenv()
print(f"🔑 GEMINI_API_KEY loaded: {'✅ YES' if os.getenv('GEMINI_API_KEY') else '❌ NO'}")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.common.database import db_manager, close_database
from services.common.kafka_client import initialize_kafka, cleanup_kafka
from services.common.models import HealthCheck, APIResponse
from services.inventory_service.routes.inventory import router as inventory_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set service name for Kafka messages
os.environ['SERVICE_NAME'] = 'inventory-service'

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Inventory Service...")
    
    try:
        # Initialize database
        if not await db_manager.connect():
            raise RuntimeError("Failed to connect to database")
        logger.info("Database connected successfully")
        
        # Initialize Kafka
        await initialize_kafka()
        logger.info("Kafka initialized successfully")
        
        logger.info("Inventory Service started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start Inventory Service: {e}")
        raise
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down Inventory Service...")
        await cleanup_kafka()
        await close_database()
        logger.info("Inventory Service shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Warehouse Inventory Service",
    description="Microservice for managing warehouse and store inventory",
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
            "timestamp": datetime.utcnow().isoformat()
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
            "timestamp": datetime.utcnow().isoformat()
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
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_status = "healthy" if db_manager.database is not None else "unhealthy"
        
        # Check Kafka connection
        from services.common.kafka_client import kafka_manager
        kafka_status = "healthy" if await kafka_manager.health_check() else "unhealthy"
        
        overall_status = "healthy" if all([
            db_status == "healthy",
            kafka_status == "healthy"
        ]) else "unhealthy"
        
        return HealthCheck(
            service="inventory-service",
            status=overall_status,
            version="1.0.0",
            dependencies={
                "database": db_status,
                "kafka": kafka_status
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            service="inventory-service",
            status="unhealthy",
            version="1.0.0",
            dependencies={
                "database": "unknown",
                "kafka": "unknown"
            }
        )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "success": True,
        "message": "Warehouse Inventory Service is running",
        "data": {
            "service": "inventory-service",
            "version": "1.0.0",
            "endpoints": [
                "/health",
                "/docs",
                "/inventory",
                "/stores",
                "/products"
            ]
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# Include routers
app.include_router(
    inventory_router,
    prefix="/api/v1",
    tags=["inventory"]
)

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("INVENTORY_SERVICE_PORT", "8001"))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    logger.info(f"Starting Inventory Service on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )