"""
HTTP Routes for Elixir Backend - S7-200 PLC Integration

This module provides HTTP REST endpoints for interacting with the S7-200 PLC system.
"""

from fastapi import APIRouter, HTTPException, Depends

from .shared import (
    get_plc, logger, Addresses, get_plc_config, reload_config, ContextLogger,
    PLCResponse, PasswordRequest, PressureRequest, TemperatureRequest, 
    ModeRequest, ManualControlRequest
)

# Create router
router = APIRouter()

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

# === AUTHENTICATION/PASSWORD ROUTES ===
@router.post("/api/auth/show", response_model=PLCResponse)
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

# === PRESSURE CONTROL ROUTES ===
@router.post("/api/pressure/add", response_model=PLCResponse)
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

# Additional routes would continue here...
# (This is a shortened version for demo purposes)
