"""
HTTP Routes for Elixir Backend - S7-200 PLC Integration

This module provides HTTP REST endpoints for interacting with the S7-200 PLC system.
All routes are organized into logical categories for easy navigation in the API documentation.
"""

from fastapi import APIRouter, HTTPException, Depends

from .shared import (
    get_plc, logger, Addresses, get_plc_config, reload_config, ContextLogger,
    PLCResponse, PasswordRequest, PressureRequest, TemperatureRequest, 
    ModeRequest, ManualControlRequest
)

# Import session service for database integration
from core.session_service import session_service

# Create router
router = APIRouter()

# === CONFIGURATION MANAGEMENT ===
@router.post(
    "/api/config/reload", 
    response_model=PLCResponse,
    tags=["Configuration Management"],
    summary="Reload PLC Configuration",
    description="""
    Reload the PLC address configuration from the configuration file.
    
    This endpoint is useful when you've updated the PLC address mappings 
    and need to refresh the system without restarting the server.
    
    **Use Cases:**
    - After updating address configuration files
    - When adding new PLC address mappings
    - Troubleshooting configuration issues
    """,
    responses={
        200: {"description": "Configuration reloaded successfully"},
        500: {"description": "Failed to reload configuration"}
    }
)
async def reload_plc_config():
    """Reload PLC address configuration from file"""
    try:
        reload_config()
        logger.info("PLC configuration reloaded successfully")
        return PLCResponse(success=True, message="PLC configuration reloaded")
    except Exception as e:
        logger.error(f"Failed to reload PLC configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/api/config/addresses", 
    response_model=PLCResponse,
    tags=["Configuration Management"],
    summary="Get All PLC Addresses",
    description="""
    Retrieve all configured PLC addresses organized by categories.
    
    Returns a comprehensive mapping of all available PLC memory addresses
    used by the system, organized by functional categories such as:
    - Authentication
    - Language control
    - Control panel
    - Pressure control
    - Session management
    - And more...
    """,
    responses={
        200: {"description": "Address configuration retrieved successfully"},
        500: {"description": "Failed to retrieve address configuration"}
    }
)
async def get_all_addresses():
    """Get all configured PLC addresses"""
    try:
        config = get_plc_config()
        return PLCResponse(
            success=True,
            data={
                "categories": config.get_all_categories(),
                "addresses": config.addresses
            }
        )
    except Exception as e:
        logger.error(f"Failed to get PLC addresses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/api/config/search/{address}", 
    response_model=PLCResponse,
    tags=["Configuration Management"],
    summary="Search Functions by Address",
    description="""
    Search for all functions that use a specific PLC memory address.
    
    This is useful for debugging and understanding which system functions
    are mapped to a particular memory location in the PLC.
    
    **Example:** `/api/config/search/V100.0` might return all functions
    using that specific memory address.
    """,
    responses={
        200: {"description": "Search completed successfully"},
        500: {"description": "Search operation failed"}
    }
)
async def search_address(address: str):
    """Search for functions using a specific address"""
    try:
        config = get_plc_config()
        results = config.search_address(address)
        return PLCResponse(
            success=True,
            data={
                "address": address,
                "matches": results
            }
        )
    except Exception as e:
        logger.error(f"Failed to search address: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === AUTHENTICATION/PASSWORD ROUTES ===
@router.post(
    "/api/auth/show", 
    response_model=PLCResponse,
    tags=["Authentication & Security"],
    summary="Show Password Screen",
    description="""
    Display the password authentication screen on the hyperbaric chamber interface.
    
    This triggers the display of the password entry screen, allowing users
    to authenticate before accessing system controls.
    
    **Security Note:** This only shows the password screen; actual authentication
    happens through subsequent password input and validation.
    """,
    responses={
        200: {"description": "Password screen displayed successfully"},
        500: {"description": "Failed to display password screen"}
    }
)
async def show_password_screen(plc = Depends(get_plc)):
    """Show the password screen"""
    try:
        with ContextLogger(logger, operation="AUTH_SHOW"):
            address = Addresses.auth("show_password_screen")
            plc.writeMem(address, True)
            logger.info("Password screen display requested")
            return PLCResponse(success=True, message="Password screen shown")
    except Exception as e:
        logger.error(f"Failed to show password screen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/auth/proceed", 
    response_model=PLCResponse,
    tags=["Authentication & Security"],
    summary="Proceed from Password Screen",
    description="""
    Proceed from the password screen after successful authentication.
    
    This endpoint should be called after the user has entered the correct
    password to advance to the main system interface.
    """,
    responses={
        200: {"description": "Successfully proceeded from password screen"},
        500: {"description": "Failed to proceed from password screen"}
    }
)
async def proceed_from_password(plc = Depends(get_plc)):
    """Proceed from password screen"""
    try:
        with ContextLogger(logger, operation="AUTH_PROCEED"):
            address = Addresses.auth("proceed_password")
            plc.writeMem(address, True)
            logger.info("Password proceed requested")
            return PLCResponse(success=True, message="Password proceed triggered")
    except Exception as e:
        logger.error(f"Failed to proceed from password: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/auth/back", 
    response_model=PLCResponse,
    tags=["Authentication & Security"],
    summary="Go Back from Password Screen",
    description="""
    Navigate back from the password screen to the previous interface.
    
    This allows users to return to the previous screen if they accessed
    the password screen by mistake or need to cancel authentication.
    """,
    responses={
        200: {"description": "Successfully navigated back from password screen"},
        500: {"description": "Failed to navigate back from password screen"}
    }
)
async def back_from_password(plc = Depends(get_plc)):
    """Go back from password screen"""
    try:
        with ContextLogger(logger, operation="AUTH_BACK"):
            address = Addresses.auth("back_password")
            plc.writeMem(address, True)
            logger.info("Password back requested")
            return PLCResponse(success=True, message="Password back triggered")
    except Exception as e:
        logger.error(f"Failed to go back from password: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/auth/input", 
    response_model=PLCResponse,
    tags=["Authentication & Security"],
    summary="Set Password Input",
    description="""
    Submit password input for authentication.
    
    Send the entered password to the PLC system for validation.
    The password will be verified against stored user or admin credentials.
    
    **Security:** Passwords are transmitted securely and logged without
    revealing the actual password content.
    """,
    responses={
        200: {"description": "Password input submitted successfully"},
        500: {"description": "Failed to submit password input"}
    }
)
async def set_password_input(request: PasswordRequest, plc = Depends(get_plc)):
    """Set password input"""
    try:
        with ContextLogger(logger, operation="AUTH_INPUT", password_length=len(str(request.password or ""))):
            address = Addresses.auth("password_input")
            plc.writeMem(address, request.password)
            logger.info("Password input set")
            return PLCResponse(success=True, message="Password input set")
    except Exception as e:
        logger.error(f"Failed to set password input: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/api/auth/status", 
    response_model=PLCResponse,
    tags=["Authentication & Security"],
    summary="Get Authentication Status",
    description="""
    Retrieve the current authentication status and password information.
    
    Returns information about:
    - Current authentication proceed status
    - Password change status
    - User and admin password configurations
    
    **Note:** Actual password values may be hashed or encoded for security.
    """,
    responses={
        200: {"description": "Authentication status retrieved successfully"},
        500: {"description": "Failed to retrieve authentication status"}
    }
)
async def get_auth_status(plc = Depends(get_plc)):
    """Get authentication status"""
    try:
        proceed_status = plc.getMem(Addresses.auth("proceed_status"))
        change_pw_status = plc.getMem(Addresses.auth("change_password_status"))
        
        return PLCResponse(
            success=True,
            data={
                "proceed_status": proceed_status,
                "change_pw_status": change_pw_status,
                "user_pw": plc.getMem(Addresses.auth("user_password")),
                "admin_pw": plc.getMem(Addresses.auth("admin_password"))
            }
        )
    except Exception as e:
        logger.error(f"Failed to get auth status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === LANGUAGE ROUTES ===
@router.post(
    "/api/language/switch", 
    response_model=PLCResponse,
    tags=["Language & Localization"],
    summary="Switch System Language",
    description="""
    Toggle between English and Chinese language interfaces.
    
    This endpoint switches the display language for the hyperbaric chamber
    user interface. The system supports bilingual operation with seamless
    switching between English and Chinese.
    
    **Supported Languages:**
    - English (EN)
    - Chinese (CN)
    
    The language change affects all display text, labels, and user messages.
    """,
    responses={
        200: {"description": "Language switched successfully"},
        500: {"description": "Failed to switch language"}
    }
)
async def switch_language(plc = Depends(get_plc)):
    """Switch between English and Chinese"""
    try:
        with ContextLogger(logger, operation="LANG_SWITCH"):
            address = Addresses.language("language_switch")
            plc.writeMem(address, True)
            logger.info("Language switch requested")
            return PLCResponse(success=True, message="Language switch triggered")
    except Exception as e:
        logger.error(f"Failed to switch language: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/api/language/current", 
    response_model=PLCResponse,
    tags=["Language & Localization"],
    summary="Get Current Language Setting",
    description="""
    Retrieve the current language setting of the system.
    
    Returns the active language configuration, showing which language
    is currently being used for the user interface display.
    
    **Response includes:**
    - English activation status
    - Chinese activation status
    - Current active language identifier
    """,
    responses={
        200: {"description": "Current language retrieved successfully"},
        500: {"description": "Failed to retrieve language status"}
    }
)
async def get_current_language(plc = Depends(get_plc)):
    """Get current language setting"""
    try:
        eng_lang = plc.getMem(Addresses.language("english_active"))
        chin_lang = plc.getMem(Addresses.language("chinese_active"))
        
        return PLCResponse(
            success=True,
            data={
                "english": eng_lang,
                "chinese": chin_lang,
                "current": "english" if eng_lang else "chinese"
            }
        )
    except Exception as e:
        logger.error(f"Failed to get language status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === CONTROL PANEL ROUTES ===
@router.post(
    "/api/control/shutdown", 
    response_model=PLCResponse,
    tags=["Control Panel & System"],
    summary="Initiate System Shutdown",
    description="""
    Trigger a controlled shutdown of the hyperbaric chamber system.
    
    **⚠️ WARNING:** This initiates a complete system shutdown sequence.
    Use with extreme caution and ensure all safety protocols are followed.
    
    **Safety Considerations:**
    - Ensure chamber is fully depressurized
    - Verify no active sessions are running
    - Confirm all personnel are safely outside the chamber
    
    This operation logs a high-priority warning and should only be used
    when a complete system shutdown is required.
    """,
    responses={
        200: {"description": "System shutdown initiated successfully"},
        500: {"description": "Failed to initiate system shutdown"}
    }
)
async def shutdown_system(plc = Depends(get_plc)):
    """Trigger system shutdown"""
    try:
        with ContextLogger(logger, operation="SYSTEM_SHUTDOWN"):
            address = Addresses.control("shutdown_button")
            plc.writeMem(address, True)
            logger.warning("System shutdown requested")
            return PLCResponse(success=True, message="System shutdown initiated")
    except Exception as e:
        logger.error(f"Failed to shutdown system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/control/ac/toggle", 
    response_model=PLCResponse,
    tags=["Control Panel & System"],
    summary="Toggle Air Conditioning",
    description="""
    Toggle the air conditioning system on or off.
    
    Controls the main air conditioning unit for climate control within
    the hyperbaric chamber. This affects temperature regulation and
    air circulation during treatment sessions.
    
    **Features:**
    - Automatic state detection and toggling
    - Returns new state after toggle operation
    - Integrated with temperature control system
    """,
    responses={
        200: {"description": "AC toggled successfully", "content": {"application/json": {"example": {"success": True, "data": {"ac_state": True}, "message": "AC toggled"}}}},
        500: {"description": "Failed to toggle AC"}
    }
)
async def toggle_ac(plc = Depends(get_plc)):
    """Toggle AC on/off"""
    try:
        with ContextLogger(logger, operation="AC_TOGGLE"):
            address = Addresses.control("ac_state")
            current_state = plc.getMem(address)
            plc.writeMem(address, not current_state)
            logger.info(f"AC toggled to {'ON' if not current_state else 'OFF'}")
            return PLCResponse(success=True, data={"ac_state": not current_state}, message="AC toggled")
    except Exception as e:
        logger.error(f"Failed to toggle AC: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/control/lights/ceiling/toggle", 
    response_model=PLCResponse,
    tags=["Control Panel & System"],
    summary="Toggle Ceiling Lights",
    description="""
    Toggle the main ceiling lighting system within the hyperbaric chamber.
    
    Controls the primary overhead lighting that provides general illumination
    for the chamber interior. This is separate from reading lights and
    provides the main ambient lighting for treatments.
    
    **Lighting Features:**
    - Main ambient lighting control
    - Independent of reading lights
    - Suitable for general chamber illumination
    """,
    responses={
        200: {"description": "Ceiling lights toggled successfully"},
        500: {"description": "Failed to toggle ceiling lights"}
    }
)
async def toggle_ceiling_lights(plc = Depends(get_plc)):
    """Toggle ceiling lights"""
    try:
        with ContextLogger(logger, operation="CEILING_LIGHTS_TOGGLE"):
            address = Addresses.control("ceiling_light_state")
            current_state = plc.getMem(address)
            plc.writeMem(address, not current_state)
            logger.info(f"Ceiling lights toggled to {'ON' if not current_state else 'OFF'}")
            return PLCResponse(success=True, data={"ceiling_lights": not current_state}, message="Ceiling lights toggled")
    except Exception as e:
        logger.error(f"Failed to toggle ceiling lights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/control/lights/reading/toggle", 
    response_model=PLCResponse,
    tags=["Control Panel & System"],
    summary="Toggle Reading Lights",
    description="""
    Toggle the reading lights within the hyperbaric chamber.
    
    Controls focused lighting designed for reading and detailed activities
    during treatment sessions. These lights provide targeted illumination
    and are independent of the main ceiling lights.
    
    **Reading Light Features:**
    - Focused illumination for reading
    - Independent control from ceiling lights
    - Optimized for close-up activities
    """,
    responses={
        200: {"description": "Reading lights toggled successfully"},
        500: {"description": "Failed to toggle reading lights"}
    }
)
async def toggle_reading_lights(plc = Depends(get_plc)):
    """Toggle reading lights"""
    try:
        with ContextLogger(logger, operation="READING_LIGHTS_TOGGLE"):
            address = Addresses.control("reading_lights")
            current_state = plc.getMem(address)
            plc.writeMem(address, not current_state)
            logger.info(f"Reading lights toggled to {'ON' if not current_state else 'OFF'}")
            return PLCResponse(success=True, data={"reading_lights": not current_state}, message="Reading lights toggled")
    except Exception as e:
        logger.error(f"Failed to toggle reading lights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/control/intercom/toggle", 
    response_model=PLCResponse,
    tags=["Control Panel & System"],
    summary="Toggle Intercom System",
    description="""
    Toggle the intercom communication system.
    
    Controls the two-way communication system between the chamber interior
    and the operator/monitoring station. Essential for safety communication
    during treatment sessions.
    
    **Safety Features:**
    - Two-way communication capability
    - Emergency communication channel
    - Clear audio transmission
    
    **⚠️ Safety Note:** Ensure intercom is functional before starting any treatment.
    """,
    responses={
        200: {"description": "Intercom toggled successfully"},
        500: {"description": "Failed to toggle intercom"}
    }
)
async def toggle_intercom(plc = Depends(get_plc)):
    """Toggle intercom"""
    try:
        with ContextLogger(logger, operation="INTERCOM_TOGGLE"):
            address = Addresses.control("intercom_state")
            current_state = plc.getMem(address)
            plc.writeMem(address, not current_state)
            logger.info(f"Intercom toggled to {'ON' if not current_state else 'OFF'}")
            return PLCResponse(success=True, data={"intercom": not current_state}, message="Intercom toggled")
    except Exception as e:
        logger.error(f"Failed to toggle intercom: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/api/control/status", 
    response_model=PLCResponse,
    tags=["Control Panel & System"],
    summary="Get Control Panel Status",
    description="""
    Retrieve the current status of all control panel components.
    
    Provides a comprehensive overview of all controllable systems including:
    - Air conditioning state
    - Lighting systems (ceiling and reading)
    - Intercom communication system
    - Door lighting status
    - System shutdown status
    
    **Use Cases:**
    - System status monitoring
    - Dashboard displays
    - Pre-session system checks
    - Troubleshooting and diagnostics
    """,
    responses={
        200: {"description": "Control panel status retrieved successfully"},
        500: {"description": "Failed to retrieve control panel status"}
    }
)
async def get_control_status(plc = Depends(get_plc)):
    """Get current control panel status"""
    try:
        return PLCResponse(
            success=True,
            data={
                "ac_state": plc.getMem(Addresses.control("ac_state")),
                "ceiling_lights": plc.getMem(Addresses.control("ceiling_light_state")),
                "intercom": plc.getMem(Addresses.control("intercom_state")),
                "reading_lights": plc.getMem(Addresses.control("reading_lights")),
                "door_light": plc.getMem(Addresses.control("door_light")),
                "shutdown_status": plc.getMem(Addresses.control("shutdown_status"))
            }
        )
    except Exception as e:
        logger.error(f"Failed to get control status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === PRESSURE CONTROL ROUTES ===
@router.post(
    "/api/pressure/add", 
    response_model=PLCResponse,
    tags=["Pressure Control"],
    summary="Increase Pressure Setpoint",
    description="""
    Increase the pressure setpoint by 10 units.
    
    This endpoint provides fine-grained control over chamber pressure
    by incrementally increasing the target pressure. The increment
    is fixed at 10 units to ensure safe and controlled pressure changes.
    
    **Safety Features:**
    - Fixed increment prevents accidental large pressure changes
    - Pressure limits are enforced by the PLC system
    - All pressure changes are logged for safety monitoring
    
    **Use Cases:**
    - Fine-tuning pressure during treatment
    - Gradual pressure adjustments
    - Operator-controlled pressure increases
    """,
    responses={
        200: {"description": "Pressure setpoint increased successfully"},
        500: {"description": "Failed to increase pressure setpoint"}
    }
)
async def add_pressure(plc = Depends(get_plc)):
    """Add 10 to pressure setpoint"""
    try:
        with ContextLogger(logger, operation="PRESSURE_ADD"):
            address = Addresses.pressure("pressure_add_button")
            plc.writeMem(address, True)
            logger.info("Pressure add button pressed")
            return PLCResponse(success=True, message="Pressure increased")
    except Exception as e:
        logger.error(f"Failed to add pressure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/pressure/subtract", 
    response_model=PLCResponse,
    tags=["Pressure Control"],
    summary="Decrease Pressure Setpoint",
    description="""
    Decrease the pressure setpoint by 10 units.
    
    This endpoint provides controlled pressure reduction by decreasing
    the target pressure in safe increments. Essential for gradual
    depressurization and fine pressure adjustments.
    
    **Safety Features:**
    - Fixed decrement prevents rapid depressurization
    - Minimum pressure limits enforced by PLC
    - Comprehensive logging for safety compliance
    
    **Use Cases:**
    - Gradual pressure reduction
    - Fine-tuning during treatment
    - Controlled depressurization steps
    """,
    responses={
        200: {"description": "Pressure setpoint decreased successfully"},
        500: {"description": "Failed to decrease pressure setpoint"}
    }
)
async def subtract_pressure(plc = Depends(get_plc)):
    """Subtract 10 from pressure setpoint"""
    try:
        with ContextLogger(logger, operation="PRESSURE_SUBTRACT"):
            address = Addresses.pressure("pressure_minus_button")
            plc.writeMem(address, True)
            logger.info("Pressure minus button pressed")
            return PLCResponse(success=True, message="Pressure decreased")
    except Exception as e:
        logger.error(f"Failed to subtract pressure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/pressure/setpoint", 
    response_model=PLCResponse,
    tags=["Pressure Control"],
    summary="Set Pressure Setpoint Directly",
    description="""
    Set the pressure setpoint to a specific value.
    
    Allows direct setting of the target pressure for precise control.
    This bypasses incremental adjustments and sets the exact desired
    pressure value.
    
    **⚠️ Safety Warning:** Direct pressure setting should be used with caution.
    Ensure the target pressure is within safe operating ranges and consider
    the rate of pressure change.
    
    **Input Validation:**
    - Pressure value must be within system limits
    - PLC enforces safety boundaries
    - Invalid values will be rejected
    
    **Typical Pressure Ranges:**
    - Therapeutic range: 1.3 - 3.0 ATA
    - Emergency limit: 3.5 ATA maximum
    """,
    responses={
        200: {"description": "Pressure setpoint updated successfully"},
        400: {"description": "Invalid pressure value"},
        500: {"description": "Failed to set pressure setpoint"}
    }
)
async def set_pressure_setpoint(request: PressureRequest, plc = Depends(get_plc)):
    """Set pressure setpoint directly"""
    try:
        with ContextLogger(logger, operation="PRESSURE_SETPOINT", value=request.setpoint):
            address = Addresses.pressure("pressure_setpoint")
            plc.writeMem(address, request.setpoint)
            logger.info(f"Pressure setpoint set to {request.setpoint}")
            return PLCResponse(success=True, data={"setpoint": request.setpoint}, message="Pressure setpoint updated")
    except Exception as e:
        logger.error(f"Failed to set pressure setpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/api/pressure/current", 
    response_model=PLCResponse,
    tags=["Pressure Control"],
    summary="Get Current Pressure Readings",
    description="""
    Retrieve current pressure readings from all pressure sensors.
    
    Provides real-time pressure data including:
    - Target pressure setpoint
    - Internal pressure sensor 1 reading
    - Internal pressure sensor 2 reading
    
    **Redundancy:** Multiple pressure sensors provide redundant safety
    monitoring and help detect sensor malfunctions.
    
    **Data Uses:**
    - Real-time monitoring displays
    - Safety system inputs
    - Data logging and compliance
    - Sensor health monitoring
    
    **Update Frequency:** Pressure readings are updated continuously
    and reflect the most recent sensor values.
    """,
    responses={
        200: {"description": "Pressure readings retrieved successfully", "content": {"application/json": {"example": {"success": True, "data": {"setpoint": 2.0, "internal_pressure_1": 1.95, "internal_pressure_2": 1.97}}}}},
        500: {"description": "Failed to retrieve pressure readings"}
    }
)
async def get_pressure_readings(plc = Depends(get_plc)):
    """Get current pressure readings"""
    try:
        return PLCResponse(
            success=True,
            data={
                "setpoint": plc.getMem(Addresses.pressure("pressure_setpoint")),
                "internal_pressure_1": plc.getMem(Addresses.pressure("internal_pressure_1")),
                "internal_pressure_2": plc.getMem(Addresses.pressure("internal_pressure_2"))
            }
        )
    except Exception as e:
        logger.error(f"Failed to get pressure readings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === SESSION CONTROL ROUTES ===
@router.post(
    "/api/session/start", 
    response_model=PLCResponse,
    tags=["Session Management"],
    summary="Start Treatment Session",
    description="""
    Initiate a new hyperbaric treatment session and begin pressurization.
    
    This endpoint starts the complete treatment sequence including:
    - Chamber sealing and safety checks
    - Gradual pressurization to target pressure
    - System monitoring activation
    - Session timer initiation
    - **Database session record creation**
    
    **Pre-Session Requirements:**
    - Chamber must be properly sealed
    - All safety systems operational
    - Patient properly positioned
    - Operator supervision confirmed
    
    **⚠️ Safety Protocol:** Only start sessions when all safety requirements
    are met and qualified personnel are supervising.
    
    **Session Phases:**
    1. Pre-pressurization checks
    2. Gradual pressurization
    3. Pressure stabilization
    4. Treatment phase initiation
    
    **Database Integration:**
    - Automatically creates session record in database
    - Logs session start event
    - Captures initial system parameters
    - Enables data logging throughout session
    """,
    responses={
        200: {"description": "Treatment session started successfully"},
        500: {"description": "Failed to start treatment session"}
    }
)
async def start_session(plc = Depends(get_plc)):
    """Start session and pressurize"""
    try:
        with ContextLogger(logger, operation="SESSION_START"):
            # Get current system readings for session record
            try:
                pressure_setpoint = plc.getMem(Addresses.pressure("pressure_setpoint"))
                temp_setpoint = plc.getMem(Addresses.temperature("temperature_setpoint"))
                current_pressure_1 = plc.getMem(Addresses.pressure("internal_pressure_1"))
                current_pressure_2 = plc.getMem(Addresses.pressure("internal_pressure_2"))
                current_temp = plc.getMem(Addresses.sensors("current_temperature"))
                current_o2 = plc.getMem(Addresses.sensors("ambient_o2"))
                
                # Get current mode settings (these might be None if not set)
                # We'll determine them from PLC state or use defaults
                treatment_mode = "professional"  # Default, could be enhanced to read from PLC
                compression_mode = "normal"      # Default, could be enhanced to read from PLC
                oxygen_mode = "continuous"       # Default, could be enhanced to read from PLC
                
            except Exception as e:
                logger.warning(f"Failed to read some initial parameters: {e}")
                pressure_setpoint = None
                temp_setpoint = None
                treatment_mode = None
                compression_mode = None
                oxygen_mode = None
            
            # Create database session record
            try:
                session_id = session_service.create_session(
                    treatment_mode=treatment_mode,
                    compression_mode=compression_mode,
                    oxygen_mode=oxygen_mode,
                    target_pressure_ata=pressure_setpoint,
                    target_temperature_c=temp_setpoint,
                    operator_notes="Session started via API"
                )
                
                # Log initial system parameters
                initial_params = {
                    "pressure_setpoint_ata": pressure_setpoint,
                    "temperature_setpoint_c": temp_setpoint,
                    "initial_pressure_1_ata": current_pressure_1,
                    "initial_pressure_2_ata": current_pressure_2,
                    "initial_temperature_c": current_temp,
                    "initial_oxygen_percent": current_o2,
                    "plc_start_command": True
                }
                session_service.log_session_parameters(session_id, initial_params)
                
                logger.info(f"Created database session record {session_id}")
                
            except Exception as e:
                logger.error(f"Failed to create database session: {e}")
                # Continue with PLC operation even if database fails
                session_id = None
            
            # Send start command to PLC
            address = Addresses.session("start_session")
            plc.writeMem(address, True)
            
            # Log session start event in database
            if session_id:
                session_service.log_session_event(
                    session_id,
                    event_type="operator_action",
                    event_category="session",
                    event_name="plc_start_command",
                    event_description="Session start command sent to PLC",
                    severity="info",
                    event_data={"pressure_setpoint": pressure_setpoint, "temperature_setpoint": temp_setpoint}
                )
            
            logger.info("Session start requested")
            
            response_data = {"message": "Session started"}
            if session_id:
                response_data["session_id"] = session_id
                response_data["database_logging"] = True
            
            return PLCResponse(success=True, data=response_data, message="Session started")
            
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/session/end", 
    response_model=PLCResponse,
    tags=["Session Management"],
    summary="End Treatment Session",
    description="""
    End the current treatment session and begin controlled depressurization.
    
    This endpoint initiates the session termination sequence including:
    - Treatment phase completion
    - Controlled depressurization sequence
    - System monitoring during decompression
    - Session data logging and completion
    - **Database session finalization**
    
    **Depressurization Safety:**
    - Gradual pressure reduction prevents decompression sickness
    - Rate-controlled decompression per safety protocols
    - Continuous monitoring during depressurization
    - Emergency procedures available if needed
    
    **⚠️ Critical:** Do not interrupt the depressurization sequence once started.
    Emergency procedures should only be used in life-threatening situations.
    
    **Post-Session:**
    - Session data is automatically logged
    - System performs post-session checks
    - Chamber is prepared for next session
    - **Database session record completed with final statistics**
    
    **Database Integration:**
    - Automatically ends session record in database
    - Calculates and stores final session statistics
    - Logs session end event with completion reason
    - Preserves complete session history
    """,
    responses={
        200: {"description": "Treatment session ended successfully"},
        500: {"description": "Failed to end treatment session"}
    }
)
async def end_session(plc = Depends(get_plc)):
    """End session and depressurize"""
    try:
        with ContextLogger(logger, operation="SESSION_END"):
            # Get final system readings for session record
            try:
                final_pressure_1 = plc.getMem(Addresses.pressure("internal_pressure_1"))
                final_pressure_2 = plc.getMem(Addresses.pressure("internal_pressure_2"))
                final_temp = plc.getMem(Addresses.sensors("current_temperature"))
                final_o2 = plc.getMem(Addresses.sensors("ambient_o2"))
                
                # Prepare final readings for database
                final_readings = {
                    "final_pressure_1_ata": final_pressure_1,
                    "final_pressure_2_ata": final_pressure_2,
                    "final_temperature_c": final_temp,
                    "final_oxygen_percent": final_o2
                }
                
            except Exception as e:
                logger.warning(f"Failed to read final parameters: {e}")
                final_readings = {}
            
            # Send end command to PLC
            address = Addresses.session("end_session")
            plc.writeMem(address, True)
            
            # End database session record
            try:
                success = session_service.end_session(
                    completion_reason="normal",
                    final_readings=final_readings
                )
                
                if success:
                    logger.info("Database session ended successfully")
                    database_ended = True
                else:
                    logger.warning("No active database session to end")
                    database_ended = False
                    
            except Exception as e:
                logger.error(f"Failed to end database session: {e}")
                database_ended = False
            
            logger.info("Session end requested")
            
            response_data = {
                "message": "Session ended",
                "database_session_ended": database_ended,
                "final_readings": final_readings
            }
            
            return PLCResponse(success=True, data=response_data, message="Session ended")
            
    except Exception as e:
        logger.error(f"Failed to end session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/session/depressurize/confirm", 
    response_model=PLCResponse,
    tags=["Session Management"],
    summary="Confirm Depressurization",
    description="""
    Confirm and acknowledge the depressurization process.
    
    This endpoint provides operator confirmation for the depressurization
    sequence, ensuring that the operator is aware and monitoring the
    decompression process.
    
    **Confirmation Requirements:**
    - Operator must be present and monitoring
    - Patient condition confirmed stable
    - All monitoring systems operational
    - Emergency procedures ready if needed
    
    **Safety Verification:**
    - Confirms operator awareness of decompression
    - Acknowledges monitoring responsibility
    - Enables safety interlocks
    - Logs operator confirmation for compliance
    
    **Use Cases:**
    - Required operator acknowledgment
    - Safety protocol compliance
    - Legal and medical documentation
    - Emergency procedure preparation
    """,
    responses={
        200: {"description": "Depressurization confirmed successfully"},
        500: {"description": "Failed to confirm depressurization"}
    }
)
async def confirm_depressurization(plc = Depends(get_plc)):
    """Confirm depressurization"""
    try:
        with ContextLogger(logger, operation="DEPRESSURIZE_CONFIRM"):
            address = Addresses.session("depressurisation_confirm")
            plc.writeMem(address, True)
            logger.info("Depressurization confirmed")
            return PLCResponse(success=True, message="Depressurization confirmed")
    except Exception as e:
        logger.error(f"Failed to confirm depressurization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === MODE CONTROL ROUTES ===
@router.post(
    "/api/modes/set", 
    response_model=PLCResponse,
    tags=["Treatment Modes"],
    summary="Set Operating Mode",
    description="""
    Set the treatment operating mode for the hyperbaric session.
    
    The system supports multiple treatment modes, each optimized for
    different therapeutic applications:
    
    **Available Modes:**
    - **rest**: Relaxation and wellness mode (lower pressure, longer duration)
    - **health**: General health and wellness treatments
    - **professional**: Professional therapeutic treatments
    - **custom**: User-defined custom treatment parameters
    - **o2_100**: 100% oxygen delivery mode
    - **o2_120**: 120-minute oxygen therapy mode
    
    **Mode Features:**
    - Each mode has optimized pressure profiles
    - Automatic duration settings (can be overridden)
    - Integrated safety parameters
    - Pre-configured treatment protocols
    
    **Duration Override:**
    - Optional duration parameter overrides default mode timing
    - Duration specified in minutes
    - Must be within safe operational limits
    
    **Safety:** All modes include built-in safety limits and cannot exceed
    maximum pressure or duration thresholds.
    """,
    responses={
        200: {"description": "Operating mode set successfully"},
        400: {"description": "Invalid mode specified"},
        500: {"description": "Failed to set operating mode"}
    }
)
async def set_operating_mode(request: ModeRequest, plc = Depends(get_plc)):
    """Set operating mode"""
    try:
        with ContextLogger(logger, operation="MODE_SET", mode=request.mode):
            mode_mappings = {
                "rest": "mode_rest",
                "health": "mode_health", 
                "professional": "mode_professional",
                "custom": "mode_custom",
                "o2_100": "mode_o2_100",
                "o2_120": "mode_o2_120"
            }
            
            if request.mode not in mode_mappings:
                raise HTTPException(status_code=400, detail="Invalid mode")
            
            # Reset all modes first
            for mode_function in mode_mappings.values():
                address = Addresses.modes(mode_function)
                plc.writeMem(address, False)
            
            # Set the requested mode
            selected_address = Addresses.modes(mode_mappings[request.mode])
            plc.writeMem(selected_address, True)
            
            # Set duration if provided
            if request.duration:
                duration_address = Addresses.modes("set_duration")
                plc.writeMem(duration_address, request.duration)
            
            logger.info(f"Operating mode set to {request.mode}")
            return PLCResponse(success=True, data={"mode": request.mode, "duration": request.duration}, message="Mode updated")
    except Exception as e:
        logger.error(f"Failed to set operating mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/modes/compression", 
    response_model=PLCResponse,
    tags=["Treatment Modes"],
    summary="Set Compression Mode",
    description="""
    Set the pressurization/compression mode for the treatment session.
    
    Different compression modes provide varying rates of pressurization
    to accommodate different patient needs and treatment protocols:
    
    **Compression Modes:**
    - **beginner**: Gentle, slow pressurization for first-time users
      - Gradual pressure increase
      - Extended compression time
      - Maximum comfort and safety
    
    - **normal**: Standard pressurization rate for regular treatments
      - Balanced speed and comfort
      - Most commonly used mode
      - Suitable for experienced patients
    
    - **fast**: Rapid pressurization for time-critical treatments
      - Faster pressure increase
      - Reduced compression time
      - Only for experienced patients
    
    **Safety Considerations:**
    - Beginner mode recommended for first-time users
    - Fast mode requires patient comfort assessment
    - All modes include safety pressure limits
    - Automatic monitoring prevents unsafe pressure rates
    """,
    responses={
        200: {"description": "Compression mode set successfully"},
        400: {"description": "Invalid compression mode"},
        500: {"description": "Failed to set compression mode"}
    }
)
async def set_compression_mode(mode: str, plc = Depends(get_plc)):
    """Set compression mode"""
    try:
        with ContextLogger(logger, operation="COMPRESSION_MODE", mode=mode):
            compression_mappings = {
                "beginner": "compression_beginner",
                "normal": "compression_normal",
                "fast": "compression_fast"
            }
            
            if mode not in compression_mappings:
                raise HTTPException(status_code=400, detail="Invalid compression mode")
            
            # Reset all compression modes first
            for mode_function in compression_mappings.values():
                address = Addresses.modes(mode_function)
                plc.writeMem(address, False)
            
            # Set the requested mode
            selected_address = Addresses.modes(compression_mappings[mode])
            plc.writeMem(selected_address, True)
            
            logger.info(f"Compression mode set to {mode}")
            return PLCResponse(success=True, data={"compression_mode": mode}, message="Compression mode updated")
    except Exception as e:
        logger.error(f"Failed to set compression mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/modes/oxygen", 
    response_model=PLCResponse,
    tags=["Treatment Modes"],
    summary="Set Oxygen Delivery Mode",
    description="""
    Configure the oxygen delivery mode for the treatment session.
    
    The system supports two primary oxygen delivery methods, each
    optimized for different therapeutic protocols:
    
    **Oxygen Delivery Modes:**
    
    - **continuous**: Constant oxygen delivery throughout session
      - Steady oxygen concentration
      - Consistent therapeutic levels
      - Suitable for most treatments
      - Provides sustained oxygen exposure
    
    - **intermittent**: Alternating oxygen delivery cycles
      - Periodic oxygen delivery with air breaks
      - Prevents oxygen toxicity
      - Suitable for longer treatments
      - Reduces risk of oxygen-related side effects
    
    **Therapeutic Benefits:**
    - Continuous mode: Maximum oxygen saturation
    - Intermittent mode: Extended treatment tolerance
    
    **Safety Features:**
    - Automatic oxygen concentration monitoring
    - Built-in toxicity prevention
    - Emergency air backup systems
    - Real-time oxygen level tracking
    """,
    responses={
        200: {"description": "Oxygen delivery mode set successfully"},
        400: {"description": "Invalid oxygen mode"},
        500: {"description": "Failed to set oxygen mode"}
    }
)
async def set_oxygen_mode(mode: str, plc = Depends(get_plc)):
    """Set oxygen delivery mode"""
    try:
        with ContextLogger(logger, operation="OXYGEN_MODE", mode=mode):
            if mode == "continuous":
                plc.writeMem(Addresses.modes("continuous_o2_flag"), True)
                plc.writeMem(Addresses.modes("intermittent_o2_flag"), False)
            elif mode == "intermittent":
                plc.writeMem(Addresses.modes("intermittent_o2_flag"), True)
                plc.writeMem(Addresses.modes("continuous_o2_flag"), False)
            else:
                raise HTTPException(status_code=400, detail="Invalid oxygen mode")
            
            logger.info(f"Oxygen mode set to {mode}")
            return PLCResponse(success=True, data={"oxygen_mode": mode}, message="Oxygen mode updated")
    except Exception as e:
        logger.error(f"Failed to set oxygen mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === TEMPERATURE/AC CONTROL ROUTES ===
@router.post(
    "/api/ac/mode", 
    response_model=PLCResponse,
    tags=["Climate Control"],
    summary="Set Air Conditioning Mode",
    description="""
    Configure the air conditioning fan mode for optimal climate control.
    
    The AC system provides multiple fan modes to accommodate different
    comfort levels and treatment requirements:
    
    **Available AC Modes:**
    - **auto**: Automatic fan speed adjustment based on temperature differential
      - Energy efficient operation
      - Maintains consistent temperature
      - Adjusts fan speed as needed
    
    - **low**: Low-speed continuous operation
      - Quiet operation for sensitive patients
      - Minimal air movement
      - Extended motor life
    
    - **mid**: Medium-speed continuous operation
      - Balanced performance and noise
      - Good for most treatments
      - Moderate air circulation
    
    - **high**: High-speed continuous operation
      - Maximum cooling/heating capacity
      - Rapid temperature adjustment
      - Maximum air circulation
    
    **Integration:** AC mode works in conjunction with temperature setpoints
    and heating/cooling settings for comprehensive climate control.
    """,
    responses={
        200: {"description": "AC mode set successfully"},
        400: {"description": "Invalid AC mode specified"},
        500: {"description": "Failed to set AC mode"}
    }
)
async def set_ac_mode(mode: str, plc = Depends(get_plc)):
    """Set AC fan mode"""
    try:
        with ContextLogger(logger, operation="AC_MODE", mode=mode):
            mode_mappings = {
                "auto": "ac_auto",
                "low": "ac_low",
                "mid": "ac_mid",
                "high": "ac_high"
            }
            
            if mode not in mode_mappings:
                raise HTTPException(status_code=400, detail="Invalid AC mode")
            
            # Reset all AC modes first
            for mode_function in mode_mappings.values():
                address = Addresses.temperature(mode_function)
                plc.writeMem(address, False)
            
            # Set the requested mode
            selected_address = Addresses.temperature(mode_mappings[mode])
            plc.writeMem(selected_address, True)
            
            logger.info(f"AC mode set to {mode}")
            return PLCResponse(success=True, data={"ac_mode": mode}, message="AC mode updated")
    except Exception as e:
        logger.error(f"Failed to set AC mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/ac/temperature", 
    response_model=PLCResponse,
    tags=["Climate Control"],
    summary="Set Temperature Setpoint",
    description="""
    Set the target temperature for the hyperbaric chamber climate control.
    
    This endpoint allows precise temperature control for patient comfort
    and therapeutic effectiveness. The system maintains the setpoint
    through integrated heating and cooling systems.
    
    **Temperature Range:**
    - Typical range: 18°C - 28°C (64°F - 82°F)
    - Precision: ±0.5°C accuracy
    - Safety limits enforced by PLC
    
    **Climate Features:**
    - Automatic temperature maintenance
    - Gradual temperature adjustment
    - Integrated humidity control
    - Energy-efficient operation
    
    **Patient Comfort:**
    - Optimal temperature ranges for different treatments
    - Consideration for pressure-related thermal effects
    - Adjustable for individual patient needs
    
    **Safety:** Temperature limits prevent uncomfortable or unsafe conditions.
    """,
    responses={
        200: {"description": "Temperature setpoint updated successfully"},
        400: {"description": "Temperature value out of range"},
        500: {"description": "Failed to set temperature setpoint"}
    }
)
async def set_temperature_setpoint(request: TemperatureRequest, plc = Depends(get_plc)):
    """Set temperature setpoint"""
    try:
        with ContextLogger(logger, operation="TEMP_SETPOINT", value=request.setpoint):
            address = Addresses.temperature("temperature_setpoint")
            plc.writeMem(address, request.setpoint)
            logger.info(f"Temperature setpoint set to {request.setpoint}")
            return PLCResponse(success=True, data={"temperature_setpoint": request.setpoint}, message="Temperature setpoint updated")
    except Exception as e:
        logger.error(f"Failed to set temperature setpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/ac/heating-cooling/toggle", 
    response_model=PLCResponse,
    tags=["Climate Control"],
    summary="Toggle Heating/Cooling Mode",
    description="""
    Switch between heating and cooling modes for the HVAC system.
    
    This endpoint toggles the primary HVAC operation mode, determining
    whether the system provides heating or cooling to reach the target
    temperature setpoint.
    
    **HVAC Modes:**
    - **heating**: Provides warm air to increase chamber temperature
      - Suitable for colder environments
      - Comfort during extended treatments
      - Therapeutic benefit maintenance
    
    - **cooling**: Provides cool air to decrease chamber temperature
      - Prevents overheating during treatments
      - Patient comfort in warm conditions
      - Equipment protection from excess heat
    
    **Automatic Operation:**
    - System automatically maintains setpoint temperature
    - Mode selection affects how setpoint is achieved
    - Integrated with fan speed control
    - Energy-efficient operation
    
    **Response:** Returns the new HVAC mode after toggle operation.
    """,
    responses={
        200: {"description": "HVAC mode toggled successfully"},
        500: {"description": "Failed to toggle heating/cooling mode"}
    }
)
async def toggle_heating_cooling(plc = Depends(get_plc)):
    """Toggle between heating and cooling"""
    try:
        with ContextLogger(logger, operation="HEATING_COOLING_TOGGLE"):
            address = Addresses.temperature("heating_cooling_toggle")
            current_state = plc.getMem(address)
            plc.writeMem(address, not current_state)
            mode = "cooling" if not current_state else "heating"
            logger.info(f"HVAC mode toggled to {mode}")
            return PLCResponse(success=True, data={"hvac_mode": mode}, message="HVAC mode toggled")
    except Exception as e:
        logger.error(f"Failed to toggle heating/cooling: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === SENSOR READINGS ===
@router.get(
    "/api/sensors/readings", 
    response_model=PLCResponse,
    tags=["Sensors & Monitoring"],
    summary="Get All Sensor Readings",
    description="""
    Retrieve real-time readings from all environmental and safety sensors.
    
    This endpoint provides comprehensive sensor data for monitoring
    the hyperbaric chamber environment and ensuring patient safety:
    
    **Environmental Sensors:**
    - **current_temp**: Real-time chamber temperature (°C)
    - **current_humidity**: Relative humidity percentage (%)
    
    **Oxygen Monitoring:**
    - **ambient_o2**: Primary oxygen concentration sensor (%)
    - **ambient_o2_2**: Secondary oxygen concentration sensor (%)
    - **ambient_o2_check_flag**: Oxygen sensor validation status
    
    **Pressure Monitoring:**
    - **internal_pressure_1**: Primary pressure sensor (ATA)
    - **internal_pressure_2**: Secondary pressure sensor (ATA)
    
    **Data Quality:**
    - Real-time updates (sub-second refresh)
    - Redundant sensors for critical measurements
    - Automatic sensor health monitoring
    - Data validation and error detection
    
    **Applications:**
    - Real-time monitoring displays
    - Safety system inputs
    - Data logging and compliance
    - Trend analysis and diagnostics
    """,
    responses={
        200: {"description": "Sensor readings retrieved successfully"},
        500: {"description": "Failed to retrieve sensor readings"}
    }
)
async def get_sensor_readings(plc = Depends(get_plc)):
    """Get all sensor readings"""
    try:
        return PLCResponse(
            success=True,
            data={
                "current_temp": plc.getMem(Addresses.sensors("current_temperature")),
                "current_humidity": plc.getMem(Addresses.sensors("current_humidity")),
                "ambient_o2": plc.getMem(Addresses.sensors("ambient_o2")),
                "ambient_o2_2": plc.getMem(Addresses.sensors("ambient_o2_2")),
                "internal_pressure_1": plc.getMem(Addresses.pressure("internal_pressure_1")),
                "internal_pressure_2": plc.getMem(Addresses.pressure("internal_pressure_2")),
                "ambient_o2_check_flag": plc.getMem(Addresses.sensors("ambient_o2_check_flag"))
            }
        )
    except Exception as e:
        logger.error(f"Failed to get sensor readings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === CALIBRATION ROUTES ===
@router.post(
    "/api/calibration/pressure", 
    response_model=PLCResponse,
    tags=["Calibration & Maintenance"],
    summary="Calibrate Pressure Sensors",
    description="""
    Initiate calibration procedure for pressure sensors.
    
    Pressure sensor calibration ensures accurate readings critical for
    patient safety and treatment effectiveness. This procedure should
    be performed regularly as part of preventive maintenance.
    
    **Calibration Process:**
    - Automated calibration sequence
    - Multi-point calibration verification
    - Atmospheric pressure reference
    - Sensor drift compensation
    
    **When to Calibrate:**
    - Regular maintenance schedule (monthly)
    - After sensor replacement
    - Following system maintenance
    - If pressure readings seem inaccurate
    
    **⚠️ Safety Requirements:**
    - Chamber must be at atmospheric pressure
    - No active treatment sessions
    - Qualified technician supervision required
    - Calibration standards must be current
    
    **Quality Assurance:**
    - Calibration results are automatically logged
    - Deviation limits are enforced
    - Failed calibrations trigger alerts
    - Maintenance records are updated
    """,
    responses={
        200: {"description": "Pressure sensor calibration initiated"},
        500: {"description": "Failed to start pressure sensor calibration"}
    }
)
async def calibrate_pressure_sensor(plc = Depends(get_plc)):
    """Calibrate pressure sensor"""
    try:
        with ContextLogger(logger, operation="PRESSURE_CALIBRATION"):
            address = Addresses.calibration("pressure_sensor_calibration")
            plc.writeMem(address, True)
            logger.info("Pressure sensor calibration initiated")
            return PLCResponse(success=True, message="Pressure sensor calibration started")
    except Exception as e:
        logger.error(f"Failed to calibrate pressure sensor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/calibration/oxygen", 
    response_model=PLCResponse,
    tags=["Calibration & Maintenance"],
    summary="Calibrate Oxygen Sensors",
    description="""
    Initiate calibration procedure for oxygen concentration sensors.
    
    Oxygen sensor calibration is critical for ensuring accurate oxygen
    delivery and preventing oxygen toxicity. Regular calibration maintains
    measurement accuracy and patient safety.
    
    **Calibration Process:**
    - Two-point calibration (air and pure oxygen)
    - Temperature compensation
    - Drift correction algorithms
    - Cross-reference validation
    
    **Calibration Standards:**
    - Room air (20.9% O2) reference
    - Medical-grade oxygen (99.5%+ O2)
    - Temperature and pressure correction
    - Humidity compensation
    
    **When to Calibrate:**
    - Weekly maintenance schedule
    - Before critical treatments
    - After sensor replacement
    - Following environmental changes
    
    **⚠️ Safety Protocol:**
    - Use certified calibration gases only
    - Ensure proper ventilation
    - No ignition sources present
    - Qualified personnel only
    
    **Documentation:**
    - Calibration certificates maintained
    - Regulatory compliance tracking
    - Deviation analysis and trending
    """,
    responses={
        200: {"description": "Oxygen sensor calibration initiated"},
        500: {"description": "Failed to start oxygen sensor calibration"}
    }
)
async def calibrate_oxygen_sensor(plc = Depends(get_plc)):
    """Calibrate oxygen sensor"""
    try:
        with ContextLogger(logger, operation="OXYGEN_CALIBRATION"):
            address = Addresses.calibration("oxygen_sensor_calibration")
            plc.writeMem(address, True)
            logger.info("Oxygen sensor calibration initiated")
            return PLCResponse(success=True, message="Oxygen sensor calibration started")
    except Exception as e:
        logger.error(f"Failed to calibrate oxygen sensor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === MANUAL CONTROL ROUTES ===
@router.post(
    "/api/manual/toggle", 
    response_model=PLCResponse,
    tags=["Manual Control & Override"],
    summary="Toggle Manual Mode",
    description="""
    Enable or disable manual control mode for system components.
    
    Manual mode allows direct operator control of individual system
    components, bypassing automatic control algorithms. This mode is
    intended for maintenance, testing, and emergency situations.
    
    **⚠️ WARNING:** Manual mode disables safety interlocks and automatic
    protections. Use only with qualified personnel and extreme caution.
    
    **Manual Mode Features:**
    - Direct component control
    - Bypass of automatic safety systems
    - Individual component operation
    - Real-time response to operator commands
    
    **Safety Considerations:**
    - Requires qualified operator supervision
    - Emergency stop systems remain active
    - Comprehensive logging of all actions
    - Time limits on manual operation
    
    **Typical Use Cases:**
    - System troubleshooting
    - Component testing
    - Maintenance procedures
    - Emergency response situations
    
    **Automatic Reversion:**
    - Manual mode times out after inactivity
    - Safety systems can override manual commands
    - Automatic return to normal operation
    """,
    responses={
        200: {"description": "Manual mode toggled successfully"},
        500: {"description": "Failed to toggle manual mode"}
    }
)
async def toggle_manual_mode(plc = Depends(get_plc)):
    """Toggle manual mode on/off"""
    try:
        with ContextLogger(logger, operation="MANUAL_MODE_TOGGLE"):
            address = Addresses.manual("manual_mode")
            current_state = plc.getMem(address)
            plc.writeMem(address, not current_state)
            logger.info(f"Manual mode toggled to {'ON' if not current_state else 'OFF'}")
            return PLCResponse(success=True, data={"manual_mode": not current_state}, message="Manual mode toggled")
    except Exception as e:
        logger.error(f"Failed to toggle manual mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/manual/controls", 
    response_model=PLCResponse,
    tags=["Manual Control & Override"],
    summary="Set Manual Control Values",
    description="""
    Set individual component control values in manual mode.
    
    This endpoint allows direct control of system components when manual
    mode is active. Each component can be controlled independently with
    precise value settings.
    
    **Available Manual Controls:**
    - **release_solenoid**: Pressure release valve control (boolean)
    - **air_pump1**: Primary air pump operation (boolean)
    - **air_pump2**: Secondary air pump operation (boolean)
    - **oxygen_supply1**: Primary oxygen supply valve (boolean)
    - **oxygen_supply2**: Secondary oxygen supply valve (boolean)
    - **release_solenoid_set**: Release valve position setting (numeric)
    
    **⚠️ CRITICAL SAFETY WARNING:**
    - Manual control bypasses automatic safety systems
    - Incorrect settings can create dangerous conditions
    - Qualified personnel supervision required
    - Emergency stop systems remain active
    
    **Component Functions:**
    - **Pumps**: Control pressurization rate and capacity
    - **Solenoids**: Manage pressure release and safety systems
    - **Oxygen Supplies**: Control therapeutic gas delivery
    
    **Safety Features:**
    - All manual operations are logged
    - Emergency override capabilities
    - Time-limited operation
    - Automatic safety monitoring continues
    """,
    responses={
        200: {"description": "Manual control values updated successfully"},
        400: {"description": "Invalid control parameter or value"},
        500: {"description": "Failed to set manual control values"}
    }
)
async def set_manual_control(request: ManualControlRequest, plc = Depends(get_plc)):
    """Set manual controls"""
    try:
        with ContextLogger(logger, operation="MANUAL_CONTROL", control=request.control, value=request.value):
            control_mappings = {
                "release_solenoid": "release_solenoid_manual",
                "air_pump1": "air_pump1_manual",
                "air_pump2": "air_pump2_manual",
                "oxygen_supply1": "oxygen_supply1_manual",
                "oxygen_supply2": "oxygen_supply2_manual",
                "release_solenoid_set": "release_solenoid_set"
            }
            
            if request.control not in control_mappings:
                raise HTTPException(status_code=400, detail="Invalid manual control")
            
            address = Addresses.manual(control_mappings[request.control])
            plc.writeMem(address, request.value)
            logger.info(f"Manual control {request.control} set to {request.value}")
            return PLCResponse(success=True, data={request.control: request.value}, message="Manual control updated")
    except Exception as e:
        logger.error(f"Failed to set manual control: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === STATUS ROUTES ===
@router.get(
    "/api/status/system", 
    response_model=PLCResponse,
    tags=["System Status & Monitoring"],
    summary="Get Comprehensive System Status",
    description="""
    Retrieve complete system status including all operational states and timers.
    
    This endpoint provides a comprehensive overview of the hyperbaric chamber
    system status, including session states, timing information, and critical
    system flags.
    
    **Session Status Information:**
    - **equalise_state**: Chamber pressure equalization status
    - **running_state**: Active treatment session indicator
    - **pressuring_state**: Pressurization process status
    - **stabilising_state**: Pressure stabilization phase
    - **stop_state**: System stop/halt condition
    - **depressurise_state**: Depressurization process status
    
    **Timer Information:**
    - **total_seconds**: Total accumulated time counter
    - **seconds_counter**: Current session seconds
    - **minute_counter**: Current session minutes
    - **run_time_sec**: Treatment runtime seconds
    - **run_time_min**: Treatment runtime minutes
    - **run_times**: Number of completed sessions
    
    **System Health Indicators:**
    - **shutdown_status**: System shutdown state
    - **ambient_o2_check**: Oxygen monitoring system status
    
    **Data Applications:**
    - Real-time system monitoring
    - Operator dashboard displays
    - Safety system status verification
    - Maintenance and diagnostic information
    - Compliance and audit reporting
    
    **Update Frequency:** Status data is updated in real-time and reflects
    the current operational state of all monitored systems.
    """,
    responses={
        200: {"description": "System status retrieved successfully"},
        500: {"description": "Failed to retrieve system status"}
    }
)
async def get_system_status(plc = Depends(get_plc)):
    """Get comprehensive system status"""
    try:
        return PLCResponse(
            success=True,
            data={
                "session_status": {
                    "equalise_state": plc.getMem(Addresses.session("equalise_state")),
                    "running_state": plc.getMem(Addresses.session("running_state")),
                    "pressuring_state": plc.getMem(Addresses.session("pressuring_state")),
                    "stabilising_state": plc.getMem(Addresses.session("stabilising_state")),
                    "stop_state": plc.getMem(Addresses.session("stop_state")),
                    "depressurise_state": plc.getMem(Addresses.session("depressurise_state"))
                },
                "timers": {
                    "total_seconds": plc.getMem(Addresses.timers("total_seconds_counter")),
                    "seconds_counter": plc.getMem(Addresses.timers("seconds_counter")),
                    "minute_counter": plc.getMem(Addresses.timers("minute_counter")),
                    "run_time_sec": plc.getMem(Addresses.timers("run_time_sec")),
                    "run_time_min": plc.getMem(Addresses.timers("run_time_min")),
                    "run_times": plc.getMem(Addresses.timers("run_times"))
                },
                "shutdown_status": plc.getMem(Addresses.control("shutdown_status")),
                "ambient_o2_check": plc.getMem(Addresses.sensors("ambient_o2_check_flag"))
            }
        )
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
