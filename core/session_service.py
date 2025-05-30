"""
Session Service for Hyperbaric Chamber Database Operations

This service handles all database operations related to session management,
including creating sessions, logging data points, recording events, and
retrieving session history.
"""

from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc, func, and_, or_
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import uuid
import json
from statistics import mean

from .database import Session, SessionParameter, SessionDataPoint, SessionEvent, SessionLocal
from .logger import setup_logger

logger = setup_logger("session_service")

class SessionService:
    """
    Service class for managing hyperbaric chamber sessions in the database
    """
    
    def __init__(self):
        self.current_session_id: Optional[int] = None
        self.session_start_time: Optional[datetime] = None
    
    def create_session(self, 
                      treatment_mode: Optional[str] = None,
                      compression_mode: Optional[str] = None,
                      oxygen_mode: Optional[str] = None,
                      target_pressure_ata: Optional[float] = None,
                      target_temperature_c: Optional[float] = None,
                      planned_duration_minutes: Optional[int] = None,
                      patient_id: Optional[str] = None,
                      operator_notes: Optional[str] = None,
                      initial_parameters: Optional[Dict[str, Any]] = None) -> int:
        """
        Create a new session record
        
        Returns:
            int: Session ID of the created session
        """
        db = SessionLocal()
        try:
            # Get next session number
            last_session = db.query(Session).order_by(desc(Session.session_number)).first()
            next_session_number = (last_session.session_number + 1) if last_session else 1
            
            # Create new session
            session = Session(
                session_uuid=str(uuid.uuid4()),
                session_number=next_session_number,
                start_time=datetime.now(),
                status="started",
                treatment_mode=treatment_mode,
                compression_mode=compression_mode,
                oxygen_mode=oxygen_mode,
                target_pressure_ata=target_pressure_ata,
                target_temperature_c=target_temperature_c,
                planned_duration_minutes=planned_duration_minutes,
                patient_id=patient_id,
                operator_notes=operator_notes
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            # Store current session info
            self.current_session_id = session.id
            self.session_start_time = session.start_time
            
            # Log initial parameters if provided
            if initial_parameters:
                self.log_session_parameters(session.id, initial_parameters)
            
            # Log session start event
            self.log_session_event(
                session.id,
                event_type="state_change",
                event_category="session",
                event_name="session_started",
                event_description=f"Session {session.session_number} started with mode: {treatment_mode}",
                severity="info"
            )
            
            logger.info(f"Created new session {session.session_number} (ID: {session.id})")
            return session.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create session: {e}")
            raise
        finally:
            db.close()
    
    def end_session(self, 
                   session_id: Optional[int] = None,
                   completion_reason: str = "normal",
                   final_readings: Optional[Dict[str, float]] = None) -> bool:
        """
        End the current or specified session
        
        Args:
            session_id: Session ID to end (uses current session if None)
            completion_reason: Reason for session completion
            final_readings: Final sensor readings to store
            
        Returns:
            bool: True if session ended successfully
        """
        if session_id is None:
            session_id = self.current_session_id
            
        if session_id is None:
            logger.warning("No active session to end")
            return False
            
        db = SessionLocal()
        try:
            session = db.query(Session).filter(Session.id == session_id).first()
            if not session:
                logger.error(f"Session {session_id} not found")
                return False
            
            # Calculate duration
            end_time = datetime.now()
            actual_duration = int((end_time - session.start_time).total_seconds())
            
            # Update session
            session.end_time = end_time
            session.status = "completed" if completion_reason == "normal" else "aborted"
            session.completion_reason = completion_reason
            session.actual_duration_seconds = actual_duration
            
            # Calculate and store final statistics
            if final_readings:
                session.max_pressure_reached_ata = final_readings.get("max_pressure")
                session.min_pressure_reached_ata = final_readings.get("min_pressure") 
                session.avg_temperature_c = final_readings.get("avg_temperature")
                session.avg_oxygen_percent = final_readings.get("avg_oxygen")
            else:
                # Calculate from data points
                self._calculate_session_statistics(db, session)
            
            db.commit()
            
            # Log session end event
            self.log_session_event(
                session_id,
                event_type="state_change",
                event_category="session", 
                event_name="session_ended",
                event_description=f"Session ended: {completion_reason}, Duration: {actual_duration}s",
                severity="info"
            )
            
            # Clear current session
            self.current_session_id = None
            self.session_start_time = None
            
            logger.info(f"Ended session {session.session_number} (ID: {session_id})")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to end session: {e}")
            raise
        finally:
            db.close()
    
    def log_data_point(self,
                      session_id: Optional[int] = None,
                      pressure_readings: Optional[Dict[str, float]] = None,
                      environmental_readings: Optional[Dict[str, float]] = None,
                      oxygen_readings: Optional[Dict[str, float]] = None,
                      system_status: Optional[Dict[str, bool]] = None,
                      session_state: Optional[str] = None) -> bool:
        """
        Log a data point for the session
        
        Args:
            session_id: Session ID (uses current session if None)
            pressure_readings: Dict with pressure sensor values
            environmental_readings: Dict with temperature, humidity
            oxygen_readings: Dict with oxygen sensor values
            system_status: Dict with system component status
            session_state: Current session state
            
        Returns:
            bool: True if logged successfully
        """
        if session_id is None:
            session_id = self.current_session_id
            
        if session_id is None:
            logger.warning("No active session for data point logging")
            return False
            
        db = SessionLocal()
        try:
            # Calculate elapsed time
            elapsed_seconds = None
            if self.session_start_time:
                elapsed_seconds = int((datetime.now() - self.session_start_time).total_seconds())
            
            # Create data point
            data_point = SessionDataPoint(
                session_id=session_id,
                session_elapsed_seconds=elapsed_seconds,
                session_state=session_state
            )
            
            # Add pressure readings
            if pressure_readings:
                data_point.internal_pressure_1_ata = pressure_readings.get("internal_pressure_1")
                data_point.internal_pressure_2_ata = pressure_readings.get("internal_pressure_2")
                data_point.pressure_setpoint_ata = pressure_readings.get("setpoint")
            
            # Add environmental readings
            if environmental_readings:
                data_point.temperature_c = environmental_readings.get("temperature")
                data_point.humidity_percent = environmental_readings.get("humidity")
            
            # Add oxygen readings
            if oxygen_readings:
                data_point.oxygen_sensor_1_percent = oxygen_readings.get("ambient_o2")
                data_point.oxygen_sensor_2_percent = oxygen_readings.get("ambient_o2_2")
            
            # Add system status
            if system_status:
                data_point.ac_status = system_status.get("ac_state")
                data_point.ceiling_lights_status = system_status.get("ceiling_lights")
                data_point.reading_lights_status = system_status.get("reading_lights")
                data_point.intercom_status = system_status.get("intercom")
            
            db.add(data_point)
            db.commit()
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to log data point: {e}")
            return False
        finally:
            db.close()
    
    def log_session_event(self,
                         session_id: int,
                         event_type: str,
                         event_category: str,
                         event_name: str,
                         event_description: Optional[str] = None,
                         severity: str = "info",
                         event_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log an event for the session
        
        Args:
            session_id: Session ID
            event_type: Type of event (state_change, alarm, operator_action, system_event)
            event_category: Category (pressure, temperature, oxygen, safety, user)
            event_name: Event name
            event_description: Event description
            severity: Event severity (info, warning, error, critical)
            event_data: Additional event data
            
        Returns:
            bool: True if logged successfully
        """
        db = SessionLocal()
        try:
            # Calculate elapsed time
            elapsed_seconds = None
            if self.session_start_time:
                elapsed_seconds = int((datetime.now() - self.session_start_time).total_seconds())
            
            event = SessionEvent(
                session_id=session_id,
                event_type=event_type,
                event_category=event_category,
                event_name=event_name,
                event_description=event_description,
                severity=severity,
                event_data_json=json.dumps(event_data) if event_data else None,
                session_elapsed_seconds=elapsed_seconds
            )
            
            db.add(event)
            db.commit()
            
            logger.info(f"Logged event '{event_name}' for session {session_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to log event: {e}")
            return False
        finally:
            db.close()
    
    def log_session_parameters(self, session_id: int, parameters: Dict[str, Any]) -> bool:
        """
        Log session parameters
        
        Args:
            session_id: Session ID
            parameters: Dict of parameter name -> value pairs
            
        Returns:
            bool: True if logged successfully
        """
        db = SessionLocal()
        try:
            for param_name, param_value in parameters.items():
                # Determine parameter type and category
                param_type = self._get_parameter_type(param_value)
                category = self._get_parameter_category(param_name)
                
                parameter = SessionParameter(
                    session_id=session_id,
                    parameter_name=param_name,
                    parameter_value=str(param_value),
                    parameter_type=param_type,
                    category=category
                )
                
                db.add(parameter)
            
            db.commit()
            logger.info(f"Logged {len(parameters)} parameters for session {session_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to log parameters: {e}")
            return False
        finally:
            db.close()
    
    def get_session_history(self, 
                           limit: int = 50,
                           offset: int = 0,
                           status_filter: Optional[str] = None,
                           date_from: Optional[datetime] = None,
                           date_to: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get session history with optional filtering
        
        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            status_filter: Filter by session status
            date_from: Filter sessions from this date
            date_to: Filter sessions to this date
            
        Returns:
            List of session dictionaries
        """
        db = SessionLocal()
        try:
            query = db.query(Session).order_by(desc(Session.start_time))
            
            # Apply filters
            if status_filter:
                query = query.filter(Session.status == status_filter)
            if date_from:
                query = query.filter(Session.start_time >= date_from)
            if date_to:
                query = query.filter(Session.start_time <= date_to)
            
            # Apply pagination
            sessions = query.offset(offset).limit(limit).all()
            
            return [session.to_dict() for session in sessions]
            
        finally:
            db.close()
    
    def get_session_details(self, session_id: int, include_data_points: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get detailed session information
        
        Args:
            session_id: Session ID
            include_data_points: Whether to include all data points
            
        Returns:
            Session details dictionary or None if not found
        """
        db = SessionLocal()
        try:
            session = db.query(Session).filter(Session.id == session_id).first()
            if not session:
                return None
            
            result = session.to_dict()
            
            # Add related data
            result["parameters"] = [
                {
                    "name": p.parameter_name,
                    "value": p.parameter_value,
                    "type": p.parameter_type,
                    "category": p.category,
                    "recorded_at": p.recorded_at.isoformat()
                }
                for p in session.parameters
            ]
            
            result["events"] = [event.to_dict() for event in session.events]
            
            if include_data_points:
                result["data_points"] = [
                    {
                        "recorded_at": dp.recorded_at.isoformat(),
                        "elapsed_seconds": dp.session_elapsed_seconds,
                        "pressure_1": dp.internal_pressure_1_ata,
                        "pressure_2": dp.internal_pressure_2_ata,
                        "pressure_setpoint": dp.pressure_setpoint_ata,
                        "temperature": dp.temperature_c,
                        "humidity": dp.humidity_percent,
                        "oxygen_1": dp.oxygen_sensor_1_percent,
                        "oxygen_2": dp.oxygen_sensor_2_percent,
                        "session_state": dp.session_state,
                        "ac_status": dp.ac_status,
                        "ceiling_lights": dp.ceiling_lights_status,
                        "reading_lights": dp.reading_lights_status,
                        "intercom": dp.intercom_status
                    }
                    for dp in session.data_points
                ]
            else:
                # Include summary statistics
                result["data_points_count"] = len(session.data_points)
            
            return result
            
        finally:
            db.close()
    
    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """
        Get the current active session
        
        Returns:
            Current session dictionary or None if no active session
        """
        if self.current_session_id:
            return self.get_session_details(self.current_session_id)
        return None
    
    def _calculate_session_statistics(self, db: DBSession, session: Session):
        """Calculate session statistics from data points"""
        data_points = db.query(SessionDataPoint).filter(
            SessionDataPoint.session_id == session.id
        ).all()
        
        if not data_points:
            return
        
        # Calculate pressure statistics
        pressures = [dp.internal_pressure_1_ata for dp in data_points if dp.internal_pressure_1_ata is not None]
        if pressures:
            session.max_pressure_reached_ata = max(pressures)
            session.min_pressure_reached_ata = min(pressures)
        
        # Calculate temperature average
        temperatures = [dp.temperature_c for dp in data_points if dp.temperature_c is not None]
        if temperatures:
            session.avg_temperature_c = mean(temperatures)
        
        # Calculate oxygen average
        oxygen_readings = [dp.oxygen_sensor_1_percent for dp in data_points if dp.oxygen_sensor_1_percent is not None]
        if oxygen_readings:
            session.avg_oxygen_percent = mean(oxygen_readings)
    
    def _get_parameter_type(self, value: Any) -> str:
        """Determine parameter type from value"""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, (dict, list)):
            return "json"
        else:
            return "string"
    
    def _get_parameter_category(self, param_name: str) -> str:
        """Determine parameter category from name"""
        name_lower = param_name.lower()
        if "pressure" in name_lower:
            return "pressure"
        elif "temperature" in name_lower or "temp" in name_lower:
            return "temperature"
        elif "oxygen" in name_lower or "o2" in name_lower:
            return "oxygen"
        elif "mode" in name_lower:
            return "mode"
        elif any(word in name_lower for word in ["ac", "light", "intercom"]):
            return "control"
        else:
            return "general"

# Global session service instance
session_service = SessionService() 