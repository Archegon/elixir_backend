"""
WebSocket Routes for Elixir Backend

This module provides WebSocket endpoints for real-time data streaming
from the S7-200 PLC system.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import json
from datetime import datetime

from .shared import get_plc, logger, Addresses

# Create router
router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.logger = logger

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