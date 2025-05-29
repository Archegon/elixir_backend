"""
Shared dependencies and utilities for API routes.

This module contains common imports, models, and utilities used by both
HTTP and WebSocket routes.
"""

from fastapi import HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from plc.plc import S7_200
from core.logger import setup_logger, ContextLogger
from plc.plc_config import Addresses, get_plc_config, reload_config

# Initialize logger
logger = setup_logger("api.shared")

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