"""
Database Models and Configuration for Session History

This module provides SQLAlchemy models and database configuration for storing
hyperbaric chamber session history, parameters, and real-time data.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os
from typing import Optional, List, Dict, Any
import json

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hyperbaric_sessions.db")

# Create engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("DB_ECHO", "false").lower() == "true"
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

class Session(Base):
    """
    Main session record storing overall session information
    """
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Session identification
    session_uuid = Column(String(36), unique=True, index=True)  # UUID for unique identification
    session_number = Column(Integer)  # Sequential session number
    
    # Timing information
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    planned_duration_minutes = Column(Integer, nullable=True)
    actual_duration_seconds = Column(Integer, nullable=True)
    
    # Session status
    status = Column(String(50), nullable=False, default="started")  # started, running, completed, aborted, error
    completion_reason = Column(String(100), nullable=True)  # normal, emergency_stop, error, manual_abort
    
    # Treatment information
    treatment_mode = Column(String(50), nullable=True)  # rest, health, professional, custom, o2_100, o2_120
    compression_mode = Column(String(20), nullable=True)  # beginner, normal, fast
    oxygen_mode = Column(String(20), nullable=True)  # continuous, intermittent
    
    # Target parameters
    target_pressure_ata = Column(Float, nullable=True)
    target_temperature_c = Column(Float, nullable=True)
    
    # Final readings
    max_pressure_reached_ata = Column(Float, nullable=True)
    min_pressure_reached_ata = Column(Float, nullable=True)
    avg_temperature_c = Column(Float, nullable=True)
    avg_oxygen_percent = Column(Float, nullable=True)
    
    # Session notes and metadata
    operator_notes = Column(Text, nullable=True)
    patient_id = Column(String(50), nullable=True)  # Optional patient identifier
    metadata_json = Column(Text, nullable=True)  # Additional metadata as JSON
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    parameters = relationship("SessionParameter", back_populates="session", cascade="all, delete-orphan")
    data_points = relationship("SessionDataPoint", back_populates="session", cascade="all, delete-orphan")
    events = relationship("SessionEvent", back_populates="session", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "id": self.id,
            "session_uuid": self.session_uuid,
            "session_number": self.session_number,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "planned_duration_minutes": self.planned_duration_minutes,
            "actual_duration_seconds": self.actual_duration_seconds,
            "status": self.status,
            "completion_reason": self.completion_reason,
            "treatment_mode": self.treatment_mode,
            "compression_mode": self.compression_mode,
            "oxygen_mode": self.oxygen_mode,
            "target_pressure_ata": self.target_pressure_ata,
            "target_temperature_c": self.target_temperature_c,
            "max_pressure_reached_ata": self.max_pressure_reached_ata,
            "min_pressure_reached_ata": self.min_pressure_reached_ata,
            "avg_temperature_c": self.avg_temperature_c,
            "avg_oxygen_percent": self.avg_oxygen_percent,
            "operator_notes": self.operator_notes,
            "patient_id": self.patient_id,
            "metadata": json.loads(self.metadata_json) if self.metadata_json else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class SessionParameter(Base):
    """
    Session parameters and settings at the time of session start
    """
    __tablename__ = "session_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    
    # Parameter information
    parameter_name = Column(String(100), nullable=False)
    parameter_value = Column(String(500), nullable=True)
    parameter_type = Column(String(50), nullable=False)  # string, integer, float, boolean, json
    category = Column(String(50), nullable=True)  # pressure, temperature, oxygen, control, etc.
    
    # Timestamps
    recorded_at = Column(DateTime, default=func.now())
    
    # Relationships
    session = relationship("Session", back_populates="parameters")

class SessionDataPoint(Base):
    """
    Real-time sensor data points recorded during the session
    """
    __tablename__ = "session_data_points"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    
    # Timing
    recorded_at = Column(DateTime, nullable=False, default=func.now())
    session_elapsed_seconds = Column(Integer, nullable=True)  # Seconds since session start
    
    # Pressure readings
    internal_pressure_1_ata = Column(Float, nullable=True)
    internal_pressure_2_ata = Column(Float, nullable=True)
    pressure_setpoint_ata = Column(Float, nullable=True)
    
    # Environmental readings
    temperature_c = Column(Float, nullable=True)
    humidity_percent = Column(Float, nullable=True)
    
    # Oxygen readings
    oxygen_sensor_1_percent = Column(Float, nullable=True)
    oxygen_sensor_2_percent = Column(Float, nullable=True)
    
    # Session state
    session_state = Column(String(50), nullable=True)  # equalising, pressuring, running, stabilising, depressurising
    
    # System status flags
    ac_status = Column(Boolean, nullable=True)
    ceiling_lights_status = Column(Boolean, nullable=True)
    reading_lights_status = Column(Boolean, nullable=True)
    intercom_status = Column(Boolean, nullable=True)
    
    # Relationships
    session = relationship("Session", back_populates="data_points")

class SessionEvent(Base):
    """
    Important events and state changes during the session
    """
    __tablename__ = "session_events"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    
    # Event information
    event_type = Column(String(50), nullable=False)  # state_change, alarm, operator_action, system_event
    event_category = Column(String(50), nullable=True)  # pressure, temperature, oxygen, safety, user
    event_name = Column(String(100), nullable=False)
    event_description = Column(Text, nullable=True)
    
    # Event severity
    severity = Column(String(20), nullable=False, default="info")  # info, warning, error, critical
    
    # Event data
    event_data_json = Column(Text, nullable=True)  # Additional event data as JSON
    
    # Timing
    occurred_at = Column(DateTime, nullable=False, default=func.now())
    session_elapsed_seconds = Column(Integer, nullable=True)
    
    # Relationships
    session = relationship("Session", back_populates="events")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "event_category": self.event_category,
            "event_name": self.event_name,
            "event_description": self.event_description,
            "severity": self.severity,
            "event_data": json.loads(self.event_data_json) if self.event_data_json else None,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "session_elapsed_seconds": self.session_elapsed_seconds
        }

# Database utility functions
def get_db():
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """
    Initialize database tables
    """
    Base.metadata.create_all(bind=engine)

def get_database_info():
    """
    Get database connection information
    """
    return {
        "database_url": DATABASE_URL,
        "engine": str(engine),
        "tables": [table.name for table in Base.metadata.tables.values()]
    } 