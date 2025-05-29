"""
API Routes for Elixir Backend - S7-200 PLC Integration

This module provides HTTP REST endpoints and WebSocket connections
for interacting with the S7-200 PLC system.
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import asyncio
import json
from datetime import datetime

from modules.plc import S7_200
from modules.logger import setup_logger, ContextLogger
from modules.plc_config import Addresses, get_plc_config, reload_config

# Initialize logger
logger = setup_logger("api.routes")

# Initialize PLC instance (this should be managed as a singleton in production)
plc_instance = None

def get_plc():
    """Dependency to get PLC instance"""
    global plc_instance
    if plc_instance is None:
        try:
            plc_instance = S7_200()
            logger.info("PLC instance created successfully")
        except Exception as e:
            logger.error(f"Failed to create PLC instance: {e}")
            raise HTTPException(status_code=503, detail="PLC connection unavailable")
    return plc_instance

# Create router
router = APIRouter()

# Pydantic models for request/response
class PLCResponse(BaseModel):
    success: bool
    data: Any = None
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)

class PasswordRequest(BaseModel):
    password: Optional[int] = None

class PressureRequest(BaseModel):
    setpoint: Optional[float] = None

class TemperatureRequest(BaseModel):
    setpoint: Optional[float] = None

class ModeRequest(BaseModel):
    mode: str
    duration: Optional[int] = None

class ManualControlRequest(BaseModel):
    control: str
    value: Any

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.logger = setup_logger("api.websocket")

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(f"WebSocket connection established. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.logger.info(f"WebSocket connection closed. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            self.logger.error(f"Failed to send message to WebSocket: {e}")

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

# === CONFIGURATION MANAGEMENT ===
@router.post("/api/config/reload", response_model=PLCResponse)
async def reload_plc_config():
    """Reload PLC address configuration from file"""
    try:
        reload_config()
        logger.info("PLC configuration reloaded successfully")
        return PLCResponse(success=True, message="PLC configuration reloaded")
    except Exception as e:
        logger.error(f"Failed to reload PLC configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/config/addresses", response_model=PLCResponse)
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

@router.get("/api/config/search/{address}", response_model=PLCResponse)
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
@router.post("/api/auth/show", response_model=PLCResponse)
async def show_password_screen(plc: S7_200 = Depends(get_plc)):
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

@router.post("/api/auth/proceed", response_model=PLCResponse)
async def proceed_from_password(plc: S7_200 = Depends(get_plc)):
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

@router.post("/api/auth/back", response_model=PLCResponse)
async def back_from_password(plc: S7_200 = Depends(get_plc)):
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

@router.post("/api/auth/input", response_model=PLCResponse)
async def set_password_input(request: PasswordRequest, plc: S7_200 = Depends(get_plc)):
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

@router.get("/api/auth/status", response_model=PLCResponse)
async def get_auth_status(plc: S7_200 = Depends(get_plc)):
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
@router.post("/api/language/switch", response_model=PLCResponse)
async def switch_language(plc: S7_200 = Depends(get_plc)):
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

@router.get("/api/language/current", response_model=PLCResponse)
async def get_current_language(plc: S7_200 = Depends(get_plc)):
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
@router.post("/api/control/shutdown", response_model=PLCResponse)
async def shutdown_system(plc: S7_200 = Depends(get_plc)):
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

@router.post("/api/control/ac/toggle", response_model=PLCResponse)
async def toggle_ac(plc: S7_200 = Depends(get_plc)):
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

@router.post("/api/control/lights/ceiling/toggle", response_model=PLCResponse)
async def toggle_ceiling_lights(plc: S7_200 = Depends(get_plc)):
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

@router.post("/api/control/lights/reading/toggle", response_model=PLCResponse)
async def toggle_reading_lights(plc: S7_200 = Depends(get_plc)):
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

@router.post("/api/control/intercom/toggle", response_model=PLCResponse)
async def toggle_intercom(plc: S7_200 = Depends(get_plc)):
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

@router.get("/api/control/status", response_model=PLCResponse)
async def get_control_status(plc: S7_200 = Depends(get_plc)):
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
@router.post("/api/pressure/add", response_model=PLCResponse)
async def add_pressure(plc: S7_200 = Depends(get_plc)):
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

@router.post("/api/pressure/subtract", response_model=PLCResponse)
async def subtract_pressure(plc: S7_200 = Depends(get_plc)):
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

@router.post("/api/pressure/setpoint", response_model=PLCResponse)
async def set_pressure_setpoint(request: PressureRequest, plc: S7_200 = Depends(get_plc)):
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

@router.get("/api/pressure/current", response_model=PLCResponse)
async def get_pressure_readings(plc: S7_200 = Depends(get_plc)):
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
@router.post("/api/session/start", response_model=PLCResponse)
async def start_session(plc: S7_200 = Depends(get_plc)):
    """Start session and pressurize"""
    try:
        with ContextLogger(logger, operation="SESSION_START"):
            address = Addresses.session("start_session")
            plc.writeMem(address, True)
            logger.info("Session start requested")
            return PLCResponse(success=True, message="Session started")
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/session/end", response_model=PLCResponse)
async def end_session(plc: S7_200 = Depends(get_plc)):
    """End session and depressurize"""
    try:
        with ContextLogger(logger, operation="SESSION_END"):
            address = Addresses.session("end_session")
            plc.writeMem(address, True)
            logger.info("Session end requested")
            return PLCResponse(success=True, message="Session ended")
    except Exception as e:
        logger.error(f"Failed to end session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/session/depressurize/confirm", response_model=PLCResponse)
async def confirm_depressurization(plc: S7_200 = Depends(get_plc)):
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
@router.post("/api/modes/set", response_model=PLCResponse)
async def set_operating_mode(request: ModeRequest, plc: S7_200 = Depends(get_plc)):
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

@router.post("/api/modes/compression", response_model=PLCResponse)
async def set_compression_mode(mode: str, plc: S7_200 = Depends(get_plc)):
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

@router.post("/api/modes/oxygen", response_model=PLCResponse)
async def set_oxygen_mode(mode: str, plc: S7_200 = Depends(get_plc)):
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
@router.post("/api/ac/mode", response_model=PLCResponse)
async def set_ac_mode(mode: str, plc: S7_200 = Depends(get_plc)):
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

@router.post("/api/ac/temperature", response_model=PLCResponse)
async def set_temperature_setpoint(request: TemperatureRequest, plc: S7_200 = Depends(get_plc)):
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

@router.post("/api/ac/heating-cooling/toggle", response_model=PLCResponse)
async def toggle_heating_cooling(plc: S7_200 = Depends(get_plc)):
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
@router.get("/api/sensors/readings", response_model=PLCResponse)
async def get_sensor_readings(plc: S7_200 = Depends(get_plc)):
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
@router.post("/api/calibration/pressure", response_model=PLCResponse)
async def calibrate_pressure_sensor(plc: S7_200 = Depends(get_plc)):
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

@router.post("/api/calibration/oxygen", response_model=PLCResponse)
async def calibrate_oxygen_sensor(plc: S7_200 = Depends(get_plc)):
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
@router.post("/api/manual/toggle", response_model=PLCResponse)
async def toggle_manual_mode(plc: S7_200 = Depends(get_plc)):
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

@router.post("/api/manual/controls", response_model=PLCResponse)
async def set_manual_control(request: ManualControlRequest, plc: S7_200 = Depends(get_plc)):
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
@router.get("/api/status/system", response_model=PLCResponse)
async def get_system_status(plc: S7_200 = Depends(get_plc)):
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

# === WEBSOCKET ENDPOINTS ===
@router.websocket("/ws/live-data")
async def websocket_live_data(websocket: WebSocket):
    """WebSocket endpoint for live data streaming"""
    await manager.connect(websocket)
    try:
        while True:
            # Read all live data from PLC
            try:
                plc = get_plc()
                live_data = {
                    "timestamp": datetime.now().isoformat(),
                    "sensors": {
                        "current_temp": plc.getMem(Addresses.sensors("current_temperature")),
                        "current_humidity": plc.getMem(Addresses.sensors("current_humidity")),
                        "ambient_o2": plc.getMem(Addresses.sensors("ambient_o2")),
                        "ambient_o2_2": plc.getMem(Addresses.sensors("ambient_o2_2")),
                        "internal_pressure_1": plc.getMem(Addresses.pressure("internal_pressure_1")),
                        "internal_pressure_2": plc.getMem(Addresses.pressure("internal_pressure_2"))
                    },
                    "status": {
                        "session_running": plc.getMem(Addresses.session("running_state")),
                        "pressuring": plc.getMem(Addresses.session("pressuring_state")),
                        "stabilising": plc.getMem(Addresses.session("stabilising_state")),
                        "depressurising": plc.getMem(Addresses.session("depressurise_state")),
                        "ac_state": plc.getMem(Addresses.control("ac_state")),
                        "ambient_o2_check": plc.getMem(Addresses.sensors("ambient_o2_check_flag"))
                    },
                    "timers": {
                        "run_time_sec": plc.getMem(Addresses.timers("run_time_sec")),
                        "run_time_min": plc.getMem(Addresses.timers("run_time_min")),
                        "total_seconds": plc.getMem(Addresses.timers("total_seconds_counter"))
                    },
                    "setpoints": {
                        "pressure": plc.getMem(Addresses.pressure("pressure_setpoint")),
                        "temperature": plc.getMem(Addresses.temperature("temperature_setpoint"))
                    }
                }
                
                await manager.send_personal_message(json.dumps(live_data), websocket)
                await asyncio.sleep(1)  # Send updates every second
                
            except Exception as e:
                logger.error(f"Error reading live data: {e}")
                await asyncio.sleep(5)  # Wait longer on error
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.websocket("/ws/pressure")
async def websocket_pressure_data(websocket: WebSocket):
    """WebSocket endpoint specifically for pressure data"""
    await manager.connect(websocket)
    try:
        while True:
            try:
                plc = get_plc()
                pressure_data = {
                    "timestamp": datetime.now().isoformat(),
                    "setpoint": plc.getMem(Addresses.pressure("pressure_setpoint")),
                    "internal_pressure_1": plc.getMem(Addresses.pressure("internal_pressure_1")),
                    "internal_pressure_2": plc.getMem(Addresses.pressure("internal_pressure_2")),
                    "pressuring_state": plc.getMem(Addresses.session("pressuring_state")),
                    "stabilising_state": plc.getMem(Addresses.session("stabilising_state")),
                    "depressurise_state": plc.getMem(Addresses.session("depressurise_state"))
                }
                
                await manager.send_personal_message(json.dumps(pressure_data), websocket)
                await asyncio.sleep(0.5)  # Faster updates for pressure
                
            except Exception as e:
                logger.error(f"Error reading pressure data: {e}")
                await asyncio.sleep(2)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.websocket("/ws/sensors")
async def websocket_sensor_data(websocket: WebSocket):
    """WebSocket endpoint specifically for sensor readings"""
    await manager.connect(websocket)
    try:
        while True:
            try:
                plc = get_plc()
                sensor_data = {
                    "timestamp": datetime.now().isoformat(),
                    "temperature": plc.getMem(Addresses.sensors("current_temperature")),
                    "humidity": plc.getMem(Addresses.sensors("current_humidity")),
                    "ambient_o2": plc.getMem(Addresses.sensors("ambient_o2")),
                    "ambient_o2_2": plc.getMem(Addresses.sensors("ambient_o2_2")),
                    "ambient_o2_check": plc.getMem(Addresses.sensors("ambient_o2_check_flag"))
                }
                
                await manager.send_personal_message(json.dumps(sensor_data), websocket)
                await asyncio.sleep(2)  # Updates every 2 seconds for sensors
                
            except Exception as e:
                logger.error(f"Error reading sensor data: {e}")
                await asyncio.sleep(5)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket) 