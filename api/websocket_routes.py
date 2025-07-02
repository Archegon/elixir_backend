"""
WebSocket Routes for Elixir Backend

This module provides WebSocket endpoints for real-time status monitoring
from the S7-200 PLC system. All status reading should use WebSocket for 
real-time updates, while HTTP endpoints handle only command operations.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Set
import asyncio
import json
from datetime import datetime
from fastapi import WebSocketState
from fastapi.websockets import ConnectionClosedError

from .shared import get_plc, logger, Addresses

# Create router
router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.logger = logger
        # Add tracking for custom addresses
        self.monitored_addresses: Set[str] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(f"WebSocket connection established. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.logger.info(f"WebSocket connection closed. Total connections: {len(self.active_connections)}")

    def has_active_connections(self) -> bool:
        """Check if there are any active WebSocket connections"""
        # Clean up any closed connections
        self.active_connections = [ws for ws in self.active_connections if ws.client_state == WebSocketState.CONNECTED]
        return len(self.active_connections) > 0

    def get_connection_count(self) -> int:
        """Get the current number of active connections"""
        # Clean up any closed connections
        self.active_connections = [ws for ws in self.active_connections if ws.client_state == WebSocketState.CONNECTED]
        return len(self.active_connections)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            self.logger.error(f"Failed to send message to WebSocket: {e}")
            # Remove failed connection
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all active connections"""
        if not self.active_connections:
            return
            
        # Clean up closed connections and broadcast to active ones
        active_connections = []
        for connection in self.active_connections:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
                    active_connections.append(connection)
                else:
                    self.logger.debug(f"Removing closed WebSocket connection")
            except ConnectionClosedError:
                self.logger.debug(f"Connection closed during broadcast")
            except Exception as e:
                self.logger.error(f"Error broadcasting to WebSocket: {e}")
        
        self.active_connections = active_connections

    def add_monitored_address(self, address: str):
        """Add an address to the monitoring list"""
        self.monitored_addresses.add(address)
        self.logger.info(f"Added address {address} to monitoring. Total: {len(self.monitored_addresses)}")

    def remove_monitored_address(self, address: str):
        """Remove an address from the monitoring list"""
        self.monitored_addresses.discard(address)
        self.logger.info(f"Removed address {address} from monitoring. Total: {len(self.monitored_addresses)}")

    def get_monitored_addresses(self) -> Set[str]:
        """Get the current set of monitored addresses"""
        return self.monitored_addresses.copy()

manager = ConnectionManager()

# Global function to check if any WebSocket clients are connected
def has_websocket_clients() -> bool:
    """
    Global function to check if any WebSocket clients are currently connected.
    This can be used by other services to determine if they should perform
    data collection operations.
    """
    return manager.has_active_connections()

def get_websocket_client_count() -> int:
    """
    Global function to get the current number of WebSocket clients.
    """
    return manager.get_connection_count()

async def read_all_plc_status(plc) -> Dict[str, Any]:
    """
    Read all PLC status bits and values for comprehensive system monitoring.
    This replaces the need for individual HTTP status endpoints.
    """
    try:
        status_data = {
            "timestamp": datetime.now().isoformat(),
            
            # Authentication & Security Status
            "auth": {
                "show_password_screen": plc.getMem(Addresses.auth("show_password_screen")),
                "proceed_password": plc.getMem(Addresses.auth("proceed_password")),
                "back_password": plc.getMem(Addresses.auth("back_password")),
                "password_input": plc.getMem(Addresses.auth("password_input")),
                "proceed_status": plc.getMem(Addresses.auth("proceed_status")),
                "change_password_status": plc.getMem(Addresses.auth("change_password_status")),
                "admin_password": plc.getMem(Addresses.auth("admin_password")),
                "user_password": plc.getMem(Addresses.auth("user_password"))
            },
            
            # Language Settings
            "language": {
                "english_active": plc.getMem(Addresses.language("english_active")),
                "chinese_active": plc.getMem(Addresses.language("chinese_active")),
                "language_switch": plc.getMem(Addresses.language("language_switch"))
            },
            
            # Control Panel Status  
            "control_panel": {
                "ac_state": plc.getMem(Addresses.control("ac_state")),
                "shutdown_status": plc.getMem(Addresses.control("shutdown_status")),
                "ceiling_lights_state": plc.getMem(Addresses.control("ceiling_light_state")),
                "reading_lights_state": plc.getMem(Addresses.control("reading_lights")),
                "door_lights_state": plc.getMem(Addresses.control("door_light")),
                "intercom_state": plc.getMem(Addresses.control("intercom_state"))
            },
            
            # Pressure System Status
            "pressure": {
                "setpoint": plc.getMem(Addresses.pressure("pressure_setpoint")),
                "internal_pressure_1": plc.getMem(Addresses.pressure("internal_pressure_1")),
                "internal_pressure_2": plc.getMem(Addresses.pressure("internal_pressure_2"))
            },
            
            # Session Status
            "session": {
                "running_state": plc.getMem(Addresses.session("running_state")),
                "pressuring_state": plc.getMem(Addresses.session("pressuring_state")),
                "stabilising_state": plc.getMem(Addresses.session("stabilising_state")),
                "depressurise_state": plc.getMem(Addresses.session("depressurise_state")),
                "equalise_state": plc.getMem(Addresses.session("equalise_state")),
                "depressurise_confirm": plc.getMem(Addresses.session("depressurisation_confirm"))
            },
            
            # Operating Modes Status
            "modes": {
                "mode_rest": plc.getMem(Addresses.modes("mode_rest")),
                "mode_health": plc.getMem(Addresses.modes("mode_health")),
                "mode_professional": plc.getMem(Addresses.modes("mode_professional")),
                "mode_custom": plc.getMem(Addresses.modes("mode_custom")),
                "mode_o2_100": plc.getMem(Addresses.modes("mode_o2_100")),
                "mode_o2_120": plc.getMem(Addresses.modes("mode_o2_120")),
                "compression_beginner": plc.getMem(Addresses.modes("compression_beginner")),
                "compression_normal": plc.getMem(Addresses.modes("compression_normal")),
                "compression_fast": plc.getMem(Addresses.modes("compression_fast")),
                "continuous_o2_flag": plc.getMem(Addresses.modes("continuous_o2_flag")),
                "intermittent_o2_flag": plc.getMem(Addresses.modes("intermittent_o2_flag")),
                "custom_duration": plc.getMem(Addresses.modes("set_duration"))
            },
            
            # Climate Control Status
            "climate": {
                "ac_auto": plc.getMem(Addresses.temperature("ac_auto")),
                "ac_low": plc.getMem(Addresses.temperature("ac_low")),
                "ac_mid": plc.getMem(Addresses.temperature("ac_mid")),
                "ac_high": plc.getMem(Addresses.temperature("ac_high")),
                "temperature_setpoint": plc.getMem(Addresses.temperature("temperature_setpoint")),
                "heating_cooling_toggle": plc.getMem(Addresses.temperature("heating_cooling_toggle"))
            },
            
            # Sensor Readings
            "sensors": {
                "current_temperature": plc.getMem(Addresses.sensors("current_temperature")),
                "current_humidity": plc.getMem(Addresses.sensors("current_humidity")),
                "ambient_o2": plc.getMem(Addresses.sensors("ambient_o2")),
                "ambient_o2_2": plc.getMem(Addresses.sensors("ambient_o2_2")),
                "ambient_o2_check_flag": plc.getMem(Addresses.sensors("ambient_o2_check_flag"))
            },
            
            # Calibration Status
            "calibration": {
                "pressure_sensor_calibration": plc.getMem(Addresses.calibration("pressure_sensor_calibration")),
                "oxygen_sensor_calibration": plc.getMem(Addresses.calibration("oxygen_sensor_calibration"))
            },
            
            # Manual Control Status
            "manual": {
                "manual_mode": plc.getMem(Addresses.manual("manual_mode")),
                "release_solenoid_manual": plc.getMem(Addresses.manual("release_solenoid_manual")),
                "air_pump1_manual": plc.getMem(Addresses.manual("air_pump1_manual")),
                "air_pump2_manual": plc.getMem(Addresses.manual("air_pump2_manual")),
                "oxygen_supply1_manual": plc.getMem(Addresses.manual("oxygen_supply1_manual")),
                "oxygen_supply2_manual": plc.getMem(Addresses.manual("oxygen_supply2_manual"))
            },
            
            # System Timers
            "timers": {
                "run_time_remaining_sec": plc.getMem(Addresses.timers("run_time_remaining_sec")),
                "run_time_remaining_min": plc.getMem(Addresses.timers("run_time_remaining_min"))
            },
            
            # System Health
            "system": {
                "plc_connected": plc.plc.get_connected(),
                "communication_errors": 0,  # Could track communication error count
                "last_update": datetime.now().isoformat()
            }
        }
        
        return status_data
        
    except Exception as e:
        logger.error(f"Error reading comprehensive PLC status: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "system": {
                "plc_connected": False,
                "communication_errors": 1,
                "last_update": datetime.now().isoformat()
            }
        }

@router.websocket("/ws/system-status")
async def websocket_comprehensive_status(websocket: WebSocket):
    """
    Primary WebSocket endpoint for comprehensive real-time system status.
    This endpoint provides all PLC status bits and should be used by the frontend
    for real-time monitoring instead of polling HTTP endpoints.
    
    Update frequency: 0.3 seconds for responsive UI updates and real-time interactions.
    """
    await manager.connect(websocket)
    communication_errors = 0
    
    try:
        while True:
            # Check if this connection is still active
            if websocket not in manager.active_connections:
                logger.info("WebSocket connection no longer active, stopping data stream")
                break
                
            # Pause if no clients are connected to reduce PLC load
            if not manager.has_active_connections():
                await asyncio.sleep(1.0)
                continue
                
            try:
                plc = get_plc()
                
                # Read custom addresses if any are being monitored
                custom_data = {}
                for address in manager.get_monitored_addresses():
                    try:
                        custom_data[address] = plc.getMem(address)
                    except Exception as e:
                        logger.debug(f"Failed to read custom address {address}: {e}")
                        custom_data[address] = None
                
                # Collect comprehensive status
                status_data = {
                    "timestamp": datetime.now().isoformat(),
                    "auth": {
                        "show_password_screen": plc.getMem(Addresses.auth("show_password_screen")),
                        "proceed_password": plc.getMem(Addresses.auth("proceed_password")),
                        "back_password": plc.getMem(Addresses.auth("back_password")),
                        "password_input": plc.getMem(Addresses.auth("password_input")),
                        "proceed_status": plc.getMem(Addresses.auth("proceed_status")),
                        "change_password_status": plc.getMem(Addresses.auth("change_password_status")),
                        "admin_password": plc.getMem(Addresses.auth("admin_password")),
                        "user_password": plc.getMem(Addresses.auth("user_password"))
                    },
                    "language": {
                        "current_language": plc.getMem(Addresses.language("current_language"))
                    },
                    "control_panel": {
                        "ac_state": plc.getMem(Addresses.control_panel("ac_state")),
                        "system_shutdown": plc.getMem(Addresses.control_panel("system_shutdown")),
                        "ceiling_lights_state": plc.getMem(Addresses.control_panel("ceiling_lights_state")),
                        "reading_lights_state": plc.getMem(Addresses.control_panel("reading_lights_state")),
                        "door_lights_state": plc.getMem(Addresses.control_panel("door_lights_state")),
                        "intercom_state": plc.getMem(Addresses.control_panel("intercom_state"))
                    },
                    "pressure": {
                        "setpoint": plc.getMem(Addresses.pressure("pressure_setpoint")),
                        "internal_pressure_1": plc.getMem(Addresses.pressure("internal_pressure_1")),
                        "internal_pressure_2": plc.getMem(Addresses.pressure("internal_pressure_2"))
                    },
                    "session": {
                        "equalise_state": plc.getMem(Addresses.session("equalise_state")),
                        "pressuring_state": plc.getMem(Addresses.session("pressuring_state")),
                        "stabilising_state": plc.getMem(Addresses.session("stabilising_state")),
                        "depressurise_state": plc.getMem(Addresses.session("depressurise_state")),
                        "running_state": plc.getMem(Addresses.session("running_state")),
                        "stop_state": plc.getMem(Addresses.session("stop_state")),
                        "session_ended": plc.getMem(Addresses.session("session_ended")),
                        "depressurise_confirm": plc.getMem(Addresses.session("depressurise_confirm"))
                    },
                    "modes": {
                        "mode_rest": plc.getMem(Addresses.modes("mode_rest")),
                        "mode_health": plc.getMem(Addresses.modes("mode_health")),
                        "mode_professional": plc.getMem(Addresses.modes("mode_professional")),
                        "mode_custom": plc.getMem(Addresses.modes("mode_custom")),
                        "mode_o2_100": plc.getMem(Addresses.modes("mode_o2_100")),
                        "mode_o2_120": plc.getMem(Addresses.modes("mode_o2_120")),
                        "custom_duration": plc.getMem(Addresses.modes("custom_duration")),
                        "compression_beginner": plc.getMem(Addresses.modes("compression_beginner")),
                        "compression_normal": plc.getMem(Addresses.modes("compression_normal")),
                        "compression_fast": plc.getMem(Addresses.modes("compression_fast")),
                        "continuous_o2_flag": plc.getMem(Addresses.modes("continuous_o2_flag")),
                        "intermittent_o2_flag": plc.getMem(Addresses.modes("intermittent_o2_flag"))
                    },
                    "climate": {
                        "ac_auto": plc.getMem(Addresses.climate("ac_auto")),
                        "ac_low": plc.getMem(Addresses.climate("ac_low")),
                        "ac_mid": plc.getMem(Addresses.climate("ac_mid")),
                        "ac_high": plc.getMem(Addresses.climate("ac_high")),
                        "temperature_setpoint": plc.getMem(Addresses.climate("temperature_setpoint")),
                        "heating_cooling_toggle": plc.getMem(Addresses.climate("heating_cooling_toggle"))
                    },
                    "sensors": {
                        "current_temperature": plc.getMem(Addresses.sensors("current_temperature")),
                        "current_humidity": plc.getMem(Addresses.sensors("current_humidity")),
                        "ambient_o2": plc.getMem(Addresses.sensors("ambient_o2")),
                        "ambient_o2_2": plc.getMem(Addresses.sensors("ambient_o2_2")),
                        "ambient_o2_check_flag": plc.getMem(Addresses.sensors("ambient_o2_check_flag"))
                    },
                    "calibration": {
                        "pressure_sensor_calibration": plc.getMem(Addresses.calibration("pressure_sensor_calibration")),
                        "oxygen_sensor_calibration": plc.getMem(Addresses.calibration("oxygen_sensor_calibration"))
                    },
                    "manual": {
                        "manual_mode": plc.getMem(Addresses.manual("manual_mode"))
                    },
                    "timers": {
                        "run_time_remaining_sec": plc.getMem(Addresses.timers("run_time_remaining_sec")),
                        "run_time_remaining_min": plc.getMem(Addresses.timers("run_time_remaining_min")),
                        "session_elapsed_time": plc.getMem(Addresses.timers("session_elapsed_time"))
                    },
                    "system": {
                        "plc_connected": plc.plc.get_connected() if hasattr(plc.plc, 'get_connected') else True,
                        "communication_errors": communication_errors,
                        "last_update": datetime.now().isoformat()
                    },
                    # Include custom address monitoring data
                    "custom_addresses": custom_data
                }
                
                await websocket.send_json(status_data)
                communication_errors = 0  # Reset error counter on successful read
                
            except Exception as e:
                communication_errors += 1
                logger.error(f"WebSocket communication error {communication_errors}: {e}")
                
                # Send error status
                error_data = {
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "communication_errors": communication_errors,
                    "custom_addresses": {}  # Empty custom data on error
                }
                
                try:
                    await websocket.send_json(error_data)
                except:
                    logger.error("Failed to send error data through WebSocket")
                    break
                
                # If too many errors, break the connection
                if communication_errors > 10:
                    logger.error("Too many communication errors, closing WebSocket")
                    break
            
            await asyncio.sleep(0.3)  # 300ms update rate
            
    except ConnectionClosedError:
        logger.info("WebSocket connection closed by client")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)

@router.websocket("/ws/critical-status")
async def websocket_critical_status(websocket: WebSocket):
    """
    Ultra-high-frequency WebSocket endpoint for critical safety status.
    Updates every 200ms for pressure, session state, and safety-critical data.
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Check if this connection is still active
            if websocket not in manager.active_connections:
                logger.info("Critical status WebSocket connection no longer active, stopping data stream")
                break
                
            try:
                plc = get_plc()
                critical_data = {
                    "timestamp": datetime.now().isoformat(),
                    "pressure": {
                        "setpoint": plc.getMem(Addresses.pressure("pressure_setpoint")),
                        "internal_pressure_1": plc.getMem(Addresses.pressure("internal_pressure_1")),
                        "internal_pressure_2": plc.getMem(Addresses.pressure("internal_pressure_2"))
                    },
                    "session": {
                        "running_state": plc.getMem(Addresses.session("running_state")),
                        "pressuring_state": plc.getMem(Addresses.session("pressuring_state")),
                        "stabilising_state": plc.getMem(Addresses.session("stabilising_state")),
                        "depressurise_state": plc.getMem(Addresses.session("depressurise_state")),
                        "equalise_state": plc.getMem(Addresses.session("equalise_state"))
                    },
                    "safety": {
                        "ambient_o2": plc.getMem(Addresses.sensors("ambient_o2")),
                        "ambient_o2_2": plc.getMem(Addresses.sensors("ambient_o2_2")),
                        "ambient_o2_check_flag": plc.getMem(Addresses.sensors("ambient_o2_check_flag"))
                    },
                    "timers": {
                        "run_time_remaining_sec": plc.getMem(Addresses.timers("run_time_remaining_sec")),
                        "run_time_remaining_min": plc.getMem(Addresses.timers("run_time_remaining_min"))
                    }
                }
                
                await manager.send_personal_message(json.dumps(critical_data), websocket)
                
                # Ultra-high frequency updates for critical safety data
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error in critical status WebSocket: {e}")
                await asyncio.sleep(2)
                
    except WebSocketDisconnect:
        pass  # Normal disconnection
    finally:
        manager.disconnect(websocket)
        logger.info(f"Critical status WebSocket stream ended. Remaining connections: {manager.get_connection_count()}")

# Keep existing specialized endpoints for backward compatibility
@router.websocket("/ws/live-data")
async def websocket_live_data(websocket: WebSocket):
    """Legacy endpoint - consider using /ws/system-status instead"""
    await manager.connect(websocket)
    try:
        while True:
            # Check if this connection is still active
            if websocket not in manager.active_connections:
                logger.info("Live data WebSocket connection no longer active, stopping data stream")
                break
                
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
                        "equalising": plc.getMem(Addresses.session("equalise_state")),
                        "ac_state": plc.getMem(Addresses.control("ac_state")),
                        "ambient_o2_check": plc.getMem(Addresses.sensors("ambient_o2_check_flag"))
                    },
                    "timers": {
                        "run_time_remaining_sec": plc.getMem(Addresses.timers("run_time_remaining_sec")),
                        "run_time_remaining_min": plc.getMem(Addresses.timers("run_time_remaining_min"))
                    },
                    "setpoints": {
                        "pressure": plc.getMem(Addresses.pressure("pressure_setpoint")),
                        "temperature": plc.getMem(Addresses.temperature("temperature_setpoint"))
                    }
                }
                
                await manager.send_personal_message(json.dumps(live_data), websocket)
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error reading live data: {e}")
                await asyncio.sleep(5)
                
    except WebSocketDisconnect:
        pass  # Normal disconnection
    finally:
        manager.disconnect(websocket)
        logger.info(f"Live data WebSocket stream ended. Remaining connections: {manager.get_connection_count()}")

@router.websocket("/ws/pressure")
async def websocket_pressure_data(websocket: WebSocket):
    """WebSocket endpoint specifically for pressure data"""
    await manager.connect(websocket)
    try:
        while True:
            # Check if this connection is still active
            if websocket not in manager.active_connections:
                logger.info("Pressure WebSocket connection no longer active, stopping data stream")
                break
                
            try:
                plc = get_plc()
                pressure_data = {
                    "timestamp": datetime.now().isoformat(),
                    "setpoint": plc.getMem(Addresses.pressure("pressure_setpoint")),
                    "internal_pressure_1": plc.getMem(Addresses.pressure("internal_pressure_1")),
                    "internal_pressure_2": plc.getMem(Addresses.pressure("internal_pressure_2")),
                    "pressuring_state": plc.getMem(Addresses.session("pressuring_state")),
                    "stabilising_state": plc.getMem(Addresses.session("stabilising_state")),
                    "depressurise_state": plc.getMem(Addresses.session("depressurise_state")),
                    "equalise_state": plc.getMem(Addresses.session("equalise_state"))
                }
                
                await manager.send_personal_message(json.dumps(pressure_data), websocket)
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error reading pressure data: {e}")
                await asyncio.sleep(2)
                
    except WebSocketDisconnect:
        pass  # Normal disconnection
    finally:
        manager.disconnect(websocket)
        logger.info(f"Pressure WebSocket stream ended. Remaining connections: {manager.get_connection_count()}")

@router.websocket("/ws/sensors")
async def websocket_sensor_data(websocket: WebSocket):
    """WebSocket endpoint specifically for sensor readings"""
    await manager.connect(websocket)
    try:
        while True:
            # Check if this connection is still active
            if websocket not in manager.active_connections:
                logger.info("Sensors WebSocket connection no longer active, stopping data stream")
                break
                
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
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error reading sensor data: {e}")
                await asyncio.sleep(5)
                
    except WebSocketDisconnect:
        pass  # Normal disconnection
    finally:
        manager.disconnect(websocket)
        logger.info(f"Sensors WebSocket stream ended. Remaining connections: {manager.get_connection_count()}") 