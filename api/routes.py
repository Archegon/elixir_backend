"""
Main API Router for Elixir Backend

This module combines HTTP, WebSocket, and Session History routes into a single router
for inclusion in the main FastAPI application.
"""

from fastapi import APIRouter

from . import http_routes
from . import websocket_routes
from . import session_routes

# Create main router
router = APIRouter()

# Include HTTP routes
router.include_router(http_routes.router, tags=["HTTP"])

# Include WebSocket routes  
router.include_router(websocket_routes.router, tags=["WebSocket"])

# Include Session History routes
router.include_router(session_routes.router, tags=["Session History"]) 