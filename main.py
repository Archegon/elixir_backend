"""
Elixir Backend - Main FastAPI Application

This is the main entry point for the Elixir Backend API server
that interfaces with the S7-200 PLC system.
"""

from fastapi import FastAPI, Request, Response
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
        from api.routes import plc_instance
        if plc_instance:
            plc_instance.disconnect()
            logger.info("PLC connection closed")
    except Exception as e:
        logger.error(f"Error during PLC cleanup: {e}")

# Get FastAPI configuration from centralized config
fastapi_config = get_fastapi_config()

# Enhanced API metadata and tag descriptions for better documentation
tags_metadata = [
    {
        "name": "Configuration Management",
        "description": """
        **System Configuration Control**
        
        Manage PLC address mappings and system configuration. These endpoints allow 
        dynamic reloading of configuration without server restart and provide 
        inspection capabilities for troubleshooting.
        
        - Reload configuration files
        - Browse address mappings
        - Search for specific addresses
        """,
    },
    {
        "name": "Authentication & Security",
        "description": """
        **User Authentication System**
        
        Secure access control for the hyperbaric chamber system. Provides password-based
        authentication with multiple access levels and secure session management.
        
        - Password screen management
        - User and admin authentication
        - Security status monitoring
        """,
    },
    {
        "name": "Language & Localization", 
        "description": """
        **Multi-Language Interface Control**
        
        Support for bilingual operation with seamless language switching between
        English and Chinese interfaces. Essential for international deployment
        and multilingual clinical environments.
        
        - Language switching
        - Current language status
        - Localized user interfaces
        """,
    },
    {
        "name": "Control Panel & System",
        "description": """
        **Primary System Controls**
        
        Core system control panel functions including environmental controls,
        lighting, communication systems, and emergency shutdown capabilities.
        Essential for day-to-day operation and safety management.
        
        - Air conditioning control
        - Lighting systems (ceiling & reading)
        - Intercom communication
        - Emergency shutdown
        """,
    },
    {
        "name": "Pressure Control",
        "description": """
        **Pressure Management System**
        
        Precise control of chamber pressure for safe and effective hyperbaric treatments.
        Includes both incremental adjustments and direct setpoint control with
        comprehensive safety monitoring.
        
        - Incremental pressure adjustments
        - Direct pressure setpoint control
        - Real-time pressure monitoring
        - Safety limit enforcement
        """,
    },
    {
        "name": "Session Management",
        "description": """
        **Treatment Session Control**
        
        Complete treatment session lifecycle management from start to finish.
        Handles pressurization, treatment phases, and controlled depressurization
        with full safety protocol compliance.
        
        - Session start/end control
        - Pressurization management
        - Depressurization confirmation
        - Safety protocol enforcement
        """,
    },
    {
        "name": "Treatment Modes",
        "description": """
        **Therapeutic Protocol Configuration**
        
        Advanced treatment mode selection and configuration for different therapeutic
        applications. Includes operating modes, compression profiles, and oxygen
        delivery options optimized for various medical protocols.
        
        - Treatment mode selection
        - Compression rate control
        - Oxygen delivery modes
        - Duration management
        """,
    },
    {
        "name": "Climate Control",
        "description": """
        **Environmental Control System**
        
        Comprehensive climate control for patient comfort and treatment effectiveness.
        Manages temperature, humidity, and air circulation with precise control
        and energy-efficient operation.
        
        - Temperature setpoint control
        - AC mode selection
        - Heating/cooling management
        - Climate monitoring
        """,
    },
    {
        "name": "Sensors & Monitoring",
        "description": """
        **Real-Time Sensor Data**
        
        Continuous monitoring of all environmental and safety sensors providing
        real-time data for system monitoring, safety verification, and treatment
        optimization. Includes redundant sensors for critical measurements.
        
        - Environmental sensors
        - Oxygen concentration monitoring
        - Pressure sensor readings
        - Sensor health monitoring
        """,
    },
    {
        "name": "Calibration & Maintenance",
        "description": """
        **Sensor Calibration System**
        
        Professional-grade calibration procedures for pressure and oxygen sensors.
        Ensures measurement accuracy, regulatory compliance, and patient safety
        through regular calibration protocols.
        
        - Pressure sensor calibration
        - Oxygen sensor calibration
        - Calibration documentation
        - Quality assurance
        """,
    },
    {
        "name": "Manual Control & Override",
        "description": """
        **⚠️ Advanced Manual Control**
        
        **WARNING: Advanced feature for qualified personnel only**
        
        Direct manual control of system components bypassing automatic safety systems.
        Intended for maintenance, testing, and emergency situations only.
        Requires qualified supervision and extreme caution.
        
        - Manual mode activation
        - Individual component control
        - Safety override capabilities
        - Emergency procedures
        """,
    },
    {
        "name": "System Status & Monitoring",
        "description": """
        **Comprehensive System Monitoring**
        
        Complete system status overview including operational states, timing
        information, and health indicators. Essential for monitoring system
        performance, troubleshooting, and compliance reporting.
        
        - Session status monitoring
        - Timer information
        - System health indicators
        - Performance metrics
        """,
    },
    {
        "name": "Session History",
        "description": """
        **Session Database & History Management**
        
        Comprehensive session history database with detailed tracking of all
        hyperbaric treatment sessions. Provides complete audit trails, statistical
        analysis, and compliance documentation.
        
        **Database Features:**
        - Complete session lifecycle tracking
        - Real-time data point logging
        - Event and state change recording
        - Statistical analysis and reporting
        
        **Data Captured:**
        - Session parameters and settings
        - Continuous sensor readings
        - System status throughout treatment
        - Operator actions and events
        - Final session statistics
        
        **Use Cases:**
        - Clinical documentation
        - Compliance reporting
        - Performance analysis
        - Troubleshooting and diagnostics
        - Quality assurance
        """,
    },
    {
        "name": "Database Management",
        "description": """
        **Database Administration & Maintenance**
        
        Administrative functions for managing the session history database
        including initialization, configuration, and system information.
        
        - Database initialization
        - Schema management
        - Connection monitoring
        - System information
        """,
    },
]

# Enhanced FastAPI configuration with comprehensive metadata
enhanced_config = {
    **fastapi_config,
    "openapi_tags": tags_metadata,
    "openapi_url": "/openapi.json",
    "docs_url": "/docs",
    "redoc_url": "/redoc",
    "openapi_prefix": "",
    "swagger_ui_parameters": {
        "deepLinking": True,
        "displayRequestDuration": True,
        "docExpansion": "none",
        "operationsSorter": "alpha",
        "filter": True,
        "tagsSorter": "alpha",
    },
    "redoc_ui_parameters": {
        "expandResponses": "200,201",
        "hideDownloadButton": False,
        "pathInMiddlePanel": True,
        "scrollYOffset": 0,
    }
}

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
