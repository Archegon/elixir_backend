"""
HTTP Routes for Elixir Backend - S7-200 PLC Integration

This module provides HTTP REST endpoints for COMMAND OPERATIONS ONLY.
All status reading should use WebSocket endpoints for real-time updates.

ARCHITECTURAL PRINCIPLE:
- HTTP endpoints: Commands and control operations (writing to PLC)
- WebSocket endpoints: Status monitoring and data reading (reading from PLC)

All routes send simple commands to the PLC and let the PLC handle the actual logic.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

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
    description="Reload PLC address configuration from file. Useful after updating address mappings without restarting the server.",
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
    description="Retrieve all configured PLC addresses organized by functional categories (authentication, control panel, pressure control, etc.).",
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
    description="Search for all functions that use a specific PLC memory address. Useful for debugging and understanding address mappings.",
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
    description="Display the password authentication screen on the hyperbaric chamber interface.",
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
    description="Proceed from the password screen after successful authentication.",
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
    description="Navigate back from the password screen to the previous interface.",
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
    description="Submit password input for authentication. The password will be verified against stored credentials.",
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
    description="Retrieve current authentication status including proceed status, password change status, and stored passwords.",
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
    description="Toggle between English and Chinese language interfaces for the hyperbaric chamber display.",
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
    description="Retrieve the current language setting showing which language is active (English or Chinese).",
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
    description="⚠️ WARNING: Trigger a controlled shutdown of the hyperbaric chamber system. Use with extreme caution.",
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
    description="Toggle the air conditioning system on or off. Controls climate control within the chamber.",
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
    description="Toggle the main ceiling lighting system within the hyperbaric chamber.",
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
    description="Toggle the reading lights for focused illumination during treatment sessions.",
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
    "/api/control/lights/door/toggle", 
    response_model=PLCResponse,
    tags=["Control Panel & System"],
    summary="Toggle Door Lights",
    description="Toggle the door lighting system for entry and exit illumination.",
    responses={
        200: {"description": "Door lights toggled successfully"},
        500: {"description": "Failed to toggle door lights"}
    }
)
async def toggle_door_lights(plc = Depends(get_plc)):
    """Toggle door lights"""
    try:
        with ContextLogger(logger, operation="DOOR_LIGHTS_TOGGLE"):
            address = Addresses.control("door_light")
            current_state = plc.getMem(address)
            plc.writeMem(address, not current_state)
            logger.info(f"Door lights toggled to {'ON' if not current_state else 'OFF'}")
            return PLCResponse(success=True, data={"door_lights": not current_state}, message="Door lights toggled")
    except Exception as e:
        logger.error(f"Failed to toggle door lights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/control/intercom/toggle", 
    response_model=PLCResponse,
    tags=["Control Panel & System"],
    summary="Toggle Intercom System",
    description="Toggle the intercom communication system between chamber and operator station. ⚠️ Ensure functional before treatment.",
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
    description="Retrieve current status of all control panel components (AC, lights, intercom, shutdown status).",
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
    description="Increase the pressure setpoint by 10 units with safety limits enforced by PLC.",
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
    description="Decrease the pressure setpoint by 10 units for controlled pressure reduction.",
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
    description="Set pressure setpoint to a specific value. ⚠️ Use with caution - ensure target is within safe operating ranges (1.3-3.0 ATA).",
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
    description="Retrieve real-time pressure readings from all sensors including setpoint and dual internal pressure sensors.",
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
    description="Start hyperbaric treatment session with pressurization, safety checks, and database logging. ⚠️ Ensure all safety requirements met.",
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
    description="End treatment session with controlled depressurization and database finalization. ⚠️ Do not interrupt depressurization once started.",
    responses={
        200: {"description": "Treatment session ended successfully"},
        500: {"description": "Failed to end treatment session"}
    }
)
async def end_session(plc = Depends(get_plc)):
    """End treatment session with controlled depressurization"""
    try:
        with ContextLogger(logger, operation="SESSION_END"):
            # Write to PLC to end session
            address = Addresses.session("end_session")
            plc.writeMem(address, True)
            
            # Try to end current session in database
            try:
                session_service.end_current_session("manual_end")
                logger.info("Session ended in database")
            except Exception as db_error:
                logger.warning(f"Database session end failed: {db_error}")
            
            logger.info("Session end command sent to PLC")
            return PLCResponse(
                success=True, 
                message="Session end initiated - depressurization will begin"
            )
    except Exception as e:
        logger.error(f"Failed to end session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/session/equalise", 
    response_model=PLCResponse,
    tags=["Session Management"],
    summary="Toggle Session Equalise State",
    description="Toggle the equalise/pause state during treatment session. Use to pause treatment for patient comfort or safety assessments.",
    responses={
        200: {"description": "Session equalise state toggled successfully"},
        500: {"description": "Failed to toggle equalise state"}
    }
)
async def toggle_equalise(plc = Depends(get_plc)):
    """Toggle session equalise/pause state"""
    try:
        with ContextLogger(logger, operation="SESSION_EQUALISE"):
            # Read current equalise state
            equalise_address = Addresses.session("equalise_state")
            current_state = plc.readMem(equalise_address)
            
            # Toggle the equalise state
            new_state = not current_state
            plc.writeMem(equalise_address, new_state)
            
            # Log the event in database if possible
            try:
                action = "equalise_enabled" if new_state else "equalise_disabled"
                session_service.log_session_event(action, {"equalise_state": new_state})
                logger.info(f"Session equalise event logged: {action}")
            except Exception as db_error:
                logger.warning(f"Database event logging failed: {db_error}")
            
            logger.info(f"Session equalise toggled to: {new_state}")
            return PLCResponse(
                success=True,
                data={"equalise_state": new_state},
                message=f"Session {'equalised' if new_state else 'resumed'}"
            )
    except Exception as e:
        logger.error(f"Failed to toggle equalise state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/session/depressurize/confirm", 
    response_model=PLCResponse,
    tags=["Session Management"],
    summary="Confirm Depressurization",
    description="Confirm and acknowledge the depressurization process for operator verification and safety compliance.",
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
    description="Set treatment operating mode (rest, health, professional, custom, o2_100, o2_120) with optional duration override.",
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
    description="Set compression mode for pressurization rate: beginner (slow), normal (standard), or fast (rapid).",
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
    description="Set oxygen delivery mode: continuous (constant delivery) or intermittent (alternating cycles with air breaks).",
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
    description="Configure AC fan mode: auto (temperature-based), low, mid, or high speed for optimal climate control.",
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
    description="Set target temperature for chamber climate control. Range: 18°C-28°C with ±0.5°C accuracy.",
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
    description="Toggle between heating and cooling modes for the HVAC system to reach target temperature.",
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
    description="Retrieve real-time readings from all environmental and safety sensors (temperature, humidity, oxygen, pressure).",
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
    description="Initiate pressure sensor calibration procedure. ⚠️ Requires atmospheric pressure, no active sessions, and qualified technician.",
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
    description="Initiate oxygen sensor calibration using air and pure oxygen references. ⚠️ Use certified gases only with proper ventilation.",
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
    description="⚠️ WARNING: Enable/disable manual control mode bypassing automatic safety systems. Use only with qualified supervision.",
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
    description="⚠️ CRITICAL: Set individual component controls in manual mode. Bypasses safety systems - qualified personnel only.",
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
    description="Retrieve comprehensive system status including session states, timers, and system health indicators for monitoring.",
    responses={
        200: {"description": "System status retrieved successfully"},
        500: {"description": "Failed to retrieve system status"}
    }
)
async def get_system_status(plc = Depends(get_plc)):
    """Get comprehensive system status for monitoring"""
    try:
        with ContextLogger(logger, operation="SYSTEM_STATUS"):
            # Read core system status
            status_data = {
                "session": {
                    "running_state": plc.getMem(Addresses.session("running_state")),
                    "pressuring_state": plc.getMem(Addresses.session("pressuring_state")),
                    "stabilising_state": plc.getMem(Addresses.session("stabilising_state")),
                    "depressurise_state": plc.getMem(Addresses.session("depressurise_state")),
                    "equalise_state": plc.getMem(Addresses.session("equalise_state"))
                },
                "pressure": {
                    "setpoint": plc.getMem(Addresses.pressure("pressure_setpoint")),
                    "internal_pressure_1": plc.getMem(Addresses.pressure("internal_pressure_1")),
                    "internal_pressure_2": plc.getMem(Addresses.pressure("internal_pressure_2"))
                },
                "safety": {
                    "ambient_o2": plc.getMem(Addresses.sensors("ambient_o2")),
                    "temperature": plc.getMem(Addresses.sensors("current_temperature"))
                },
                "system": {
                    "plc_connected": plc.plc.get_connected() if hasattr(plc.plc, 'get_connected') else True
                }
            }
            
            return PLCResponse(
                success=True,
                data=status_data,
                message="System status retrieved"
            )
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/api/status/websocket-connections", 
    response_model=PLCResponse,
    tags=["System Status & Monitoring"],
    summary="Get WebSocket Connection Status",
    description="Retrieve current WebSocket connection status for debugging and monitoring purposes.",
    responses={
        200: {"description": "WebSocket connection status retrieved successfully"},
        500: {"description": "Failed to retrieve WebSocket connection status"}
    }
)
async def get_websocket_status():
    """Get current WebSocket connection status"""
    try:
        # Import WebSocket functions
        from .websocket_routes import get_websocket_client_count, has_websocket_clients
        
        connection_count = get_websocket_client_count()
        has_clients = has_websocket_clients()
        
        status_data = {
            "websocket_connections": {
                "active_connections": connection_count,
                "has_active_clients": has_clients,
                "data_streaming_active": has_clients,
                "status": "active" if has_clients else "idle"
            },
            "performance_optimization": {
                "plc_polling_active": has_clients,
                "description": "Backend reduces PLC polling when no WebSocket clients are connected"
            }
        }
        
        logger.info(f"WebSocket status requested - Active connections: {connection_count}")
        
        return PLCResponse(
            success=True,
            data=status_data,
            message=f"WebSocket status: {connection_count} active connection(s)"
        )
    except Exception as e:
        logger.error(f"Failed to get WebSocket status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === CUSTOM PLC ADDRESS MONITORING ===
@router.get(
    "/api/plc/read/{address}",
    response_model=PLCResponse,
    tags=["Development & Debugging"],
    summary="Read Custom PLC Address",
    description="Read a value from a custom PLC memory address for development and debugging purposes.",
    responses={
        200: {"description": "PLC address read successfully"},
        400: {"description": "Invalid address format"},
        500: {"description": "Failed to read PLC address"}
    }
)
async def read_custom_plc_address(address: str, plc = Depends(get_plc)):
    """Read value from a custom PLC address"""
    try:
        with ContextLogger(logger, operation="CUSTOM_READ", address=address):
            # Validate address format (basic validation)
            if not address or len(address) < 2:
                raise HTTPException(status_code=400, detail="Invalid address format")
            
            # Read the address
            value = plc.readMem(address)
            
            logger.info(f"Read custom address {address}: {value}")
            return PLCResponse(
                success=True,
                data={
                    "address": address,
                    "value": value,
                    "type": type(value).__name__
                },
                message=f"Address {address} read successfully"
            )
    except Exception as e:
        logger.error(f"Failed to read custom address {address}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class CustomWriteRequest(BaseModel):
    value: float | int | bool

@router.post(
    "/api/plc/write/{address}",
    response_model=PLCResponse,
    tags=["Development & Debugging"],
    summary="Write to Custom PLC Address",
    description="⚠️ WARNING: Write a value to a custom PLC memory address. Use with extreme caution in development only.",
    responses={
        200: {"description": "PLC address written successfully"},
        400: {"description": "Invalid address format or value"},
        500: {"description": "Failed to write to PLC address"}
    }
)
async def write_custom_plc_address(address: str, request: CustomWriteRequest, plc = Depends(get_plc)):
    """Write value to a custom PLC address"""
    try:
        with ContextLogger(logger, operation="CUSTOM_WRITE", address=address, value=request.value):
            # Validate address format (basic validation)
            if not address or len(address) < 2:
                raise HTTPException(status_code=400, detail="Invalid address format")
            
            # Read current value for logging
            try:
                old_value = plc.readMem(address)
            except:
                old_value = "unknown"
            
            # Write the new value
            plc.writeMem(address, request.value)
            
            # Verify the write by reading back
            try:
                new_value = plc.readMem(address)
            except:
                new_value = "unknown"
            
            logger.warning(f"Custom write to {address}: {old_value} → {request.value} (verified: {new_value})")
            return PLCResponse(
                success=True,
                data={
                    "address": address,
                    "old_value": old_value,
                    "written_value": request.value,
                    "verified_value": new_value
                },
                message=f"Address {address} written successfully"
            )
    except Exception as e:
        logger.error(f"Failed to write custom address {address}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
