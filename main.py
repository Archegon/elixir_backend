"""
Elixir Backend - Main FastAPI Application

This is the main entry point for the Elixir Backend API server
that interfaces with the S7-200 PLC system.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import time
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Import our routes and configuration
from api.routes import router as api_router
from core.logger import setup_logger, ContextLogger
from core.app_config import get_fastapi_config, get_root_response, get_health_response, get_version, get_name
from core.database import init_database
from core.api_metadata import get_enhanced_fastapi_config

# Load environment variables
load_dotenv()

# Initialize logger
logger = setup_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app_name = get_name()
    version = get_version()
    
    logger.info(f"Starting {app_name} v{version}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"PLC IP: {os.getenv('PLC_IP', 'not configured')}")
    
    # Initialize database
    init_database()
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {app_name}")
    
    # Clean up PLC connections if needed
    try:
        from api.shared import plc_instance
        if plc_instance:
            plc_instance.disconnect()
            logger.info("PLC connection closed")
    except Exception as e:
        logger.error(f"Error during PLC cleanup: {e}")

# Get FastAPI configuration from centralized config
fastapi_config = get_fastapi_config()

# Get enhanced FastAPI configuration with metadata
enhanced_config = get_enhanced_fastapi_config(fastapi_config)

# Create FastAPI app with enhanced configuration and lifespan
app = FastAPI(**enhanced_config, lifespan=lifespan)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware - configure based on your frontend needs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    with ContextLogger(logger, 
                      operation="HTTP_REQUEST", 
                      method=request.method, 
                      path=request.url.path,
                      client=request.client.host if request.client else "unknown"):
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

# Include API routes
app.include_router(api_router, prefix="", tags=["api"])

# Root endpoint - uses centralized configuration
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return get_root_response()

# Health check endpoint - uses centralized configuration
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # You could add PLC connectivity check here
        return get_health_response()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "service": get_name().lower().replace(" ", "-"),
                "version": get_version(),
                "timestamp": time.time()
            }
        )

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception in {request.method} {request.url.path}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "Internal error",
            "version": get_version()
        }
    )

if __name__ == "__main__":
    # Development server
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting development server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
