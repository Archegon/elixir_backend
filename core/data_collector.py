"""
Data Collection Service for Real-time Session Monitoring

This service runs in the background to collect and log sensor data
during active hyperbaric chamber sessions.
"""

import asyncio
import time
from datetime import datetime
from typing import Optional, Dict, Any
from threading import Thread

from .session_service import session_service
from .logger import setup_logger

logger = setup_logger("data_collector")

class DataCollectionService:
    """
    Background service for collecting and logging sensor data during sessions
    """
    
    def __init__(self, collection_interval: int = 30):
        """
        Initialize data collection service
        
        Args:
            collection_interval: Time in seconds between data collections
        """
        self.collection_interval = collection_interval
        self.is_running = False
        self.collection_thread: Optional[Thread] = None
        self._plc_instance = None
        self._addresses = None
        
    def start(self, plc_instance, addresses):
        """
        Start the data collection service
        
        Args:
            plc_instance: PLC instance for reading data
            addresses: Address mapping instance
        """
        if self.is_running:
            logger.warning("Data collection service is already running")
            return
            
        self._plc_instance = plc_instance
        self._addresses = addresses
        self.is_running = True
        
        # Start collection thread
        self.collection_thread = Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        
        logger.info(f"Data collection service started with {self.collection_interval}s interval")
    
    def stop(self):
        """Stop the data collection service"""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
            
        logger.info("Data collection service stopped")
    
    def _collection_loop(self):
        """Main collection loop running in background thread"""
        logger.info("Data collection loop started")
        
        while self.is_running:
            try:
                # Check if there's an active session
                current_session = session_service.get_current_session()
                
                if current_session:
                    # Collect and log data
                    self._collect_and_log_data()
                else:
                    # No active session, just wait
                    pass
                    
            except Exception as e:
                logger.error(f"Error in data collection loop: {e}")
            
            # Wait for next collection interval
            time.sleep(self.collection_interval)
        
        logger.info("Data collection loop ended")
    
    def _collect_and_log_data(self):
        """Collect sensor data and log to database"""
        if not self._plc_instance or not self._addresses:
            logger.warning("PLC instance or addresses not available for data collection")
            return
        
        try:
            # Collect pressure readings
            pressure_readings = {}
            try:
                pressure_readings = {
                    "internal_pressure_1": self._plc_instance.getMem(self._addresses.pressure("internal_pressure_1")),
                    "internal_pressure_2": self._plc_instance.getMem(self._addresses.pressure("internal_pressure_2")),
                    "setpoint": self._plc_instance.getMem(self._addresses.pressure("pressure_setpoint"))
                }
            except Exception as e:
                logger.warning(f"Failed to read pressure data: {e}")
            
            # Collect environmental readings
            environmental_readings = {}
            try:
                environmental_readings = {
                    "temperature": self._plc_instance.getMem(self._addresses.sensors("current_temperature")),
                    "humidity": self._plc_instance.getMem(self._addresses.sensors("current_humidity"))
                }
            except Exception as e:
                logger.warning(f"Failed to read environmental data: {e}")
            
            # Collect oxygen readings
            oxygen_readings = {}
            try:
                oxygen_readings = {
                    "ambient_o2": self._plc_instance.getMem(self._addresses.sensors("ambient_o2")),
                    "ambient_o2_2": self._plc_instance.getMem(self._addresses.sensors("ambient_o2_2"))
                }
            except Exception as e:
                logger.warning(f"Failed to read oxygen data: {e}")
            
            # Collect system status
            system_status = {}
            try:
                system_status = {
                    "ac_state": self._plc_instance.getMem(self._addresses.control("ac_state")),
                    "ceiling_lights": self._plc_instance.getMem(self._addresses.control("ceiling_light_state")),
                    "reading_lights": self._plc_instance.getMem(self._addresses.control("reading_lights")),
                    "intercom": self._plc_instance.getMem(self._addresses.control("intercom_state"))
                }
            except Exception as e:
                logger.warning(f"Failed to read system status: {e}")
            
            # Get session state
            session_state = None
            try:
                # Try to determine session state from PLC
                running_state = self._plc_instance.getMem(self._addresses.session("running_state"))
                pressuring_state = self._plc_instance.getMem(self._addresses.session("pressuring_state"))
                stabilising_state = self._plc_instance.getMem(self._addresses.session("stabilising_state"))
                depressurise_state = self._plc_instance.getMem(self._addresses.session("depressurise_state"))
                equalise_state = self._plc_instance.getMem(self._addresses.session("equalise_state"))
                
                if depressurise_state:
                    session_state = "depressurising"
                elif running_state:
                    session_state = "running"
                elif stabilising_state:
                    session_state = "stabilising"
                elif pressuring_state:
                    session_state = "pressuring"
                elif equalise_state:
                    session_state = "equalising"
                else:
                    session_state = "unknown"
                    
            except Exception as e:
                logger.warning(f"Failed to read session state: {e}")
                session_state = "unknown"
            
            # Log the data point
            success = session_service.log_data_point(
                pressure_readings=pressure_readings if pressure_readings else None,
                environmental_readings=environmental_readings if environmental_readings else None,
                oxygen_readings=oxygen_readings if oxygen_readings else None,
                system_status=system_status if system_status else None,
                session_state=session_state
            )
            
            if success:
                logger.debug("Data point logged successfully")
            else:
                logger.warning("Failed to log data point")
                
        except Exception as e:
            logger.error(f"Failed to collect and log data: {e}")
    
    def log_event(self, event_type: str, event_category: str, event_name: str, 
                  event_description: Optional[str] = None, severity: str = "info",
                  event_data: Optional[Dict[str, Any]] = None):
        """
        Log an event for the current session
        
        Args:
            event_type: Type of event
            event_category: Event category
            event_name: Event name
            event_description: Event description
            severity: Event severity
            event_data: Additional event data
        """
        try:
            current_session = session_service.get_current_session()
            if current_session:
                session_service.log_session_event(
                    session_id=current_session["id"],
                    event_type=event_type,
                    event_category=event_category,
                    event_name=event_name,
                    event_description=event_description,
                    severity=severity,
                    event_data=event_data
                )
                logger.info(f"Event '{event_name}' logged for session {current_session['id']}")
            else:
                logger.warning("No active session for event logging")
        except Exception as e:
            logger.error(f"Failed to log event: {e}")

# Global data collection service instance
data_collector = DataCollectionService(collection_interval=30)  # Collect data every 30 seconds 