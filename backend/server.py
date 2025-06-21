from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
from pathlib import Path
import asyncio

# Import database and services
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import connect_to_mongo, close_mongo_connection, db_manager
from auth import create_default_admin
from services.system_monitor import system_monitor

# Import routers
from routers.auth_router import router as auth_router
from routers.dashboard_router import router as dashboard_router
from routers.files_router import router as files_router
from routers.rdp_router import router as rdp_router
from routers.sessions_router import router as sessions_router
from routers.logs_router import router as logs_router
from routers.settings_router import router as settings_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    # Startup
    logger.info("Starting RDP Stealth application...")
    
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        
        # Create default admin user
        await create_default_admin()
        
        # Start system monitoring
        await system_monitor.start_monitoring(interval=30)  # Monitor every 30 seconds
        
        # Schedule periodic cleanup
        asyncio.create_task(periodic_cleanup())
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down RDP Stealth application...")
    
    try:
        # Stop system monitoring
        await system_monitor.stop_monitoring()
        
        # Close database connection
        await close_mongo_connection()
        
        logger.info("Application shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="RDP Stealth",
    description="Secure Remote Desktop Access Panel",
    version="2.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],  # In production, specify exact origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")

# Health check endpoint
@api_router.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "RDP Stealth API is running",
        "version": "2.1.0",
        "status": "healthy"
    }

@api_router.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check database connection
        db_stats = await db_manager.get_database_stats()
        
        # Check system monitoring
        monitoring_status = system_monitor.monitoring
        
        return {
            "status": "healthy",
            "database": "connected",
            "monitoring": "active" if monitoring_status else "inactive",
            "database_stats": db_stats,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(files_router)
api_router.include_router(rdp_router)
api_router.include_router(sessions_router)
api_router.include_router(logs_router)
api_router.include_router(settings_router)

# Include the API router in the main app
app.include_router(api_router)

# Periodic cleanup task
async def periodic_cleanup():
    """Periodic cleanup of old data"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            await db_manager.cleanup_old_data()
            logger.info("Periodic cleanup completed")
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Not Found",
        "message": "The requested resource was not found",
        "status_code": 404
    }

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return {
        "error": "Internal Server Error",
        "message": "An internal server error occurred",
        "status_code": 500
    }

# Startup message
@app.on_event("startup")
async def startup_message():
    logger.info("RDP Stealth API Server Started")
    logger.info("Available endpoints:")
    logger.info("  - Health Check: GET /api/")
    logger.info("  - Authentication: /api/auth/*")
    logger.info("  - Dashboard: /api/dashboard/*")
    logger.info("  - File Management: /api/files/*")
    logger.info("  - RDP Management: /api/rdp/*")
    logger.info("  - Session Management: /api/sessions/*")
    logger.info("  - Logs: /api/logs/*")
    logger.info("  - Settings: /api/settings/*")

if __name__ == "__main__":
    import uvicorn
    
    # This is for development only
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )