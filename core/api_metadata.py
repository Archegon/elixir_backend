"""
API Documentation Metadata

This module contains all the API documentation metadata including tag descriptions
and enhanced documentation for the FastAPI application.
"""

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


def get_swagger_ui_parameters():
    """Get Swagger UI parameters configuration"""
    return {
        "deepLinking": True,
        "displayRequestDuration": True,
        "docExpansion": "none",
        "operationsSorter": "alpha",
        "filter": True,
        "tagsSorter": "alpha",
    }


def get_redoc_ui_parameters():
    """Get ReDoc UI parameters configuration"""
    return {
        "expandResponses": "200,201",
        "hideDownloadButton": False,
        "pathInMiddlePanel": True,
        "scrollYOffset": 0,
    }


def get_enhanced_fastapi_config(base_config: dict) -> dict:
    """
    Get enhanced FastAPI configuration with comprehensive metadata
    
    Args:
        base_config: Base FastAPI configuration from app_config
        
    Returns:
        Enhanced configuration dictionary
    """
    return {
        **base_config,
        "openapi_tags": tags_metadata,
        "openapi_url": "/openapi.json",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_prefix": "",
        "swagger_ui_parameters": get_swagger_ui_parameters(),
        "redoc_ui_parameters": get_redoc_ui_parameters(),
    } 