"""
Session History API Routes

This module provides API endpoints for managing and retrieving hyperbaric chamber
session history from the database.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from core.session_service import session_service
from core.database import get_db, init_database, get_database_info
from .shared import logger, PLCResponse

# Create router
router = APIRouter()

# Pydantic models for request/response
class SessionCreateRequest(BaseModel):
    treatment_mode: Optional[str] = Field(None, description="Treatment mode (rest, health, professional, custom, o2_100, o2_120)")
    compression_mode: Optional[str] = Field(None, description="Compression mode (beginner, normal, fast)")
    oxygen_mode: Optional[str] = Field(None, description="Oxygen delivery mode (continuous, intermittent)")
    target_pressure_ata: Optional[float] = Field(None, ge=1.0, le=5.0, description="Target pressure in ATA")
    target_temperature_c: Optional[float] = Field(None, ge=15.0, le=35.0, description="Target temperature in Celsius")
    planned_duration_minutes: Optional[int] = Field(None, ge=1, le=1440, description="Planned duration in minutes")
    patient_id: Optional[str] = Field(None, max_length=50, description="Optional patient identifier")
    operator_notes: Optional[str] = Field(None, max_length=1000, description="Operator notes")

class SessionEndRequest(BaseModel):
    completion_reason: str = Field("normal", description="Reason for session completion")
    operator_notes: Optional[str] = Field(None, max_length=1000, description="Final operator notes")

class SessionHistoryResponse(BaseModel):
    sessions: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int
    has_more: bool

# === DATABASE MANAGEMENT ROUTES ===
@router.post(
    "/api/database/init",
    response_model=PLCResponse,
    tags=["Database Management"],
    summary="Initialize Database",
    description="""
    Initialize the session history database tables.
    
    This endpoint creates all necessary database tables for storing session
    history, parameters, data points, and events. Safe to call multiple times.
    
    **Use Cases:**
    - Initial system setup
    - Database recovery
    - Schema updates
    
    **Note:** This operation is idempotent and will not affect existing data.
    """,
    responses={
        200: {"description": "Database initialized successfully"},
        500: {"description": "Failed to initialize database"}
    }
)
async def initialize_database():
    """Initialize database tables"""
    try:
        init_database()
        db_info = get_database_info()
        logger.info("Database initialized successfully")
        return PLCResponse(
            success=True,
            data=db_info,
            message="Database initialized successfully"
        )
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/api/database/info",
    response_model=PLCResponse,
    tags=["Database Management"],
    summary="Get Database Information",
    description="""
    Retrieve information about the database connection and schema.
    
    Returns details about:
    - Database connection URL
    - Database engine information
    - Available tables
    - Connection status
    """,
    responses={
        200: {"description": "Database information retrieved successfully"},
        500: {"description": "Failed to retrieve database information"}
    }
)
async def get_database_information():
    """Get database connection information"""
    try:
        db_info = get_database_info()
        return PLCResponse(
            success=True,
            data=db_info,
            message="Database information retrieved"
        )
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === SESSION MANAGEMENT ROUTES ===
@router.post(
    "/api/sessions/create",
    response_model=PLCResponse,
    tags=["Session History"],
    summary="Create New Session Record",
    description="""
    Create a new session record in the database with initial parameters.
    
    This endpoint creates a session record that can be used to track the
    complete lifecycle of a hyperbaric treatment session including:
    
    **Session Information:**
    - Treatment and compression modes
    - Target parameters (pressure, temperature)
    - Patient identification (optional)
    - Operator notes and metadata
    
    **Automatic Features:**
    - Unique session UUID generation
    - Sequential session numbering
    - Session start timestamp
    - Initial event logging
    
    **Note:** This is separate from the PLC session start and can be used
    for pre-session planning and documentation.
    """,
    responses={
        200: {"description": "Session created successfully"},
        400: {"description": "Invalid session parameters"},
        500: {"description": "Failed to create session"}
    }
)
async def create_session_record(request: SessionCreateRequest):
    """Create a new session record"""
    try:
        session_id = session_service.create_session(
            treatment_mode=request.treatment_mode,
            compression_mode=request.compression_mode,
            oxygen_mode=request.oxygen_mode,
            target_pressure_ata=request.target_pressure_ata,
            target_temperature_c=request.target_temperature_c,
            planned_duration_minutes=request.planned_duration_minutes,
            patient_id=request.patient_id,
            operator_notes=request.operator_notes
        )
        
        logger.info(f"Created session record {session_id}")
        return PLCResponse(
            success=True,
            data={"session_id": session_id},
            message="Session record created successfully"
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/api/sessions/end",
    response_model=PLCResponse,
    tags=["Session History"],
    summary="End Current Session",
    description="""
    End the current active session with completion details.
    
    This endpoint finalizes the current session record by:
    - Setting the end timestamp
    - Recording completion reason
    - Calculating final statistics
    - Logging session end event
    
    **Completion Reasons:**
    - `normal`: Planned completion
    - `emergency_stop`: Emergency termination
    - `manual_abort`: Operator-initiated abort
    - `error`: System error termination
    
    **Final Statistics:**
    Session statistics are automatically calculated from recorded data points
    including pressure ranges, temperature averages, and oxygen levels.
    """,
    responses={
        200: {"description": "Session ended successfully"},
        404: {"description": "No active session to end"},
        500: {"description": "Failed to end session"}
    }
)
async def end_current_session(request: SessionEndRequest):
    """End the current session"""
    try:
        success = session_service.end_session(
            completion_reason=request.completion_reason
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="No active session to end")
        
        logger.info("Session ended successfully")
        return PLCResponse(
            success=True,
            message="Session ended successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/api/sessions/current",
    response_model=PLCResponse,
    tags=["Session History"],
    summary="Get Current Active Session",
    description="""
    Retrieve information about the currently active session.
    
    Returns complete session details including:
    - Session identification and timing
    - Treatment parameters and modes
    - Current status and progress
    - Recorded events and parameters
    - Data points summary
    
    **Use Cases:**
    - Real-time session monitoring
    - Progress tracking
    - Status verification
    """,
    responses={
        200: {"description": "Current session retrieved successfully"},
        404: {"description": "No active session"},
        500: {"description": "Failed to retrieve current session"}
    }
)
async def get_current_session():
    """Get the current active session"""
    try:
        current_session = session_service.get_current_session()
        
        if not current_session:
            raise HTTPException(status_code=404, detail="No active session")
        
        return PLCResponse(
            success=True,
            data=current_session,
            message="Current session retrieved"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === SESSION HISTORY ROUTES ===
@router.get(
    "/api/sessions/history",
    response_model=PLCResponse,
    tags=["Session History"],
    summary="Get Session History",
    description="""
    Retrieve paginated session history with optional filtering.
    
    This endpoint provides comprehensive session history with support for:
    
    **Filtering Options:**
    - **Status**: Filter by session status (started, running, completed, aborted)
    - **Date Range**: Filter sessions within specific date ranges
    - **Pagination**: Limit and offset for large datasets
    
    **Sorting:**
    - Sessions are returned in reverse chronological order (newest first)
    
    **Response Format:**
    - Paginated results with metadata
    - Session summaries (detailed view available separately)
    - Total count and pagination information
    
    **Use Cases:**
    - Session history review
    - Treatment tracking
    - Compliance reporting
    - Statistical analysis
    """,
    responses={
        200: {"description": "Session history retrieved successfully"},
        400: {"description": "Invalid query parameters"},
        500: {"description": "Failed to retrieve session history"}
    }
)
async def get_session_history(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    status: Optional[str] = Query(None, description="Filter by session status"),
    date_from: Optional[datetime] = Query(None, description="Filter sessions from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter sessions to this date")
):
    """Get session history with filtering and pagination"""
    try:
        sessions = session_service.get_session_history(
            limit=limit,
            offset=offset,
            status_filter=status,
            date_from=date_from,
            date_to=date_to
        )
        
        # Calculate pagination info
        has_more = len(sessions) == limit
        page = (offset // limit) + 1
        
        response_data = {
            "sessions": sessions,
            "total_count": len(sessions),  # Note: This is the current page count
            "page": page,
            "page_size": limit,
            "has_more": has_more,
            "filters": {
                "status": status,
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None
            }
        }
        
        return PLCResponse(
            success=True,
            data=response_data,
            message="Session history retrieved"
        )
    except Exception as e:
        logger.error(f"Failed to get session history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/api/sessions/{session_id}",
    response_model=PLCResponse,
    tags=["Session History"],
    summary="Get Detailed Session Information",
    description="""
    Retrieve comprehensive details for a specific session.
    
    This endpoint provides complete session information including:
    
    **Session Overview:**
    - Session identification and timing
    - Treatment parameters and final statistics
    - Completion status and reason
    
    **Session Parameters:**
    - All recorded session parameters
    - Parameter categories and types
    - Recording timestamps
    
    **Session Events:**
    - State changes and operator actions
    - System events and alarms
    - Event severity and descriptions
    
    **Data Points (Optional):**
    - Real-time sensor readings throughout session
    - System status at each recording
    - Pressure, temperature, and oxygen trends
    
    **Use Cases:**
    - Detailed session review
    - Clinical documentation
    - Troubleshooting and analysis
    - Compliance and audit trails
    """,
    responses={
        200: {"description": "Session details retrieved successfully"},
        404: {"description": "Session not found"},
        500: {"description": "Failed to retrieve session details"}
    }
)
async def get_session_details(
    session_id: int,
    include_data_points: bool = Query(False, description="Include all data points in response")
):
    """Get detailed information for a specific session"""
    try:
        session_details = session_service.get_session_details(
            session_id=session_id,
            include_data_points=include_data_points
        )
        
        if not session_details:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return PLCResponse(
            success=True,
            data=session_details,
            message="Session details retrieved"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/api/sessions/{session_id}/events",
    response_model=PLCResponse,
    tags=["Session History"],
    summary="Get Session Events",
    description="""
    Retrieve all events for a specific session.
    
    Events include:
    - State changes (pressurizing, running, depressurizing)
    - Operator actions (mode changes, manual controls)
    - System alerts and alarms
    - Safety-related events
    
    **Event Categories:**
    - `state_change`: Session phase transitions
    - `operator_action`: User-initiated actions
    - `system_event`: Automated system events
    - `alarm`: Safety alerts and warnings
    
    **Severity Levels:**
    - `info`: Informational events
    - `warning`: Important notifications
    - `error`: Error conditions
    - `critical`: Critical safety events
    """,
    responses={
        200: {"description": "Session events retrieved successfully"},
        404: {"description": "Session not found"},
        500: {"description": "Failed to retrieve session events"}
    }
)
async def get_session_events(session_id: int):
    """Get all events for a specific session"""
    try:
        session_details = session_service.get_session_details(session_id)
        
        if not session_details:
            raise HTTPException(status_code=404, detail="Session not found")
        
        events = session_details.get("events", [])
        
        return PLCResponse(
            success=True,
            data={
                "session_id": session_id,
                "events": events,
                "event_count": len(events)
            },
            message="Session events retrieved"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/api/sessions/statistics/summary",
    response_model=PLCResponse,
    tags=["Session History"],
    summary="Get Session Statistics Summary",
    description="""
    Retrieve summary statistics for session history.
    
    Provides aggregated statistics including:
    - Total number of sessions
    - Sessions by status
    - Sessions by treatment mode
    - Average session durations
    - Recent activity summary
    
    **Time Periods:**
    - All time totals
    - Last 30 days summary
    - Current month statistics
    
    **Use Cases:**
    - Dashboard statistics
    - Usage reporting
    - Performance metrics
    - Trend analysis
    """,
    responses={
        200: {"description": "Statistics retrieved successfully"},
        500: {"description": "Failed to retrieve statistics"}
    }
)
async def get_session_statistics():
    """Get summary statistics for session history"""
    try:
        # Get sessions from last 30 days for recent statistics
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_sessions = session_service.get_session_history(
            limit=1000,  # Large limit to get most recent sessions
            date_from=thirty_days_ago
        )
        
        # Get all sessions for total statistics (summary only)
        all_sessions = session_service.get_session_history(limit=1000)
        
        # Calculate statistics
        total_sessions = len(all_sessions)
        recent_sessions_count = len(recent_sessions)
        
        # Status distribution
        status_counts = {}
        mode_counts = {}
        
        for session in all_sessions:
            status = session.get("status", "unknown")
            mode = session.get("treatment_mode", "unknown")
            
            status_counts[status] = status_counts.get(status, 0) + 1
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        # Calculate average durations
        completed_sessions = [s for s in all_sessions if s.get("actual_duration_seconds")]
        avg_duration_seconds = 0
        if completed_sessions:
            total_duration = sum(s["actual_duration_seconds"] for s in completed_sessions)
            avg_duration_seconds = total_duration / len(completed_sessions)
        
        statistics = {
            "total_sessions": total_sessions,
            "recent_sessions_30_days": recent_sessions_count,
            "status_distribution": status_counts,
            "mode_distribution": mode_counts,
            "average_duration_seconds": round(avg_duration_seconds),
            "average_duration_minutes": round(avg_duration_seconds / 60, 1),
            "completed_sessions": len(completed_sessions),
            "completion_rate": round(len(completed_sessions) / total_sessions * 100, 1) if total_sessions > 0 else 0
        }
        
        return PLCResponse(
            success=True,
            data=statistics,
            message="Session statistics retrieved"
        )
    except Exception as e:
        logger.error(f"Failed to get session statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 