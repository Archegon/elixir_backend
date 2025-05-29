"""
Main API Router for Elixir Backend

This module combines HTTP and WebSocket routes into a single router
for inclusion in the main FastAPI application.
"""

from fastapi import APIRouter

from . import http_routes
from . import websocket_routes

# Create main router
router = APIRouter()

# Include HTTP routes
router.include_router(http_routes.router, tags=["HTTP"])

# Include WebSocket routes  
router.include_router(websocket_routes.router, tags=["WebSocket"]) 