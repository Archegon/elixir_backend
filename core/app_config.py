"""
Application Configuration Module

This module handles loading and accessing application metadata from pyproject.toml.
Provides a simplified configuration system using only the standard Python project metadata.
"""

import os
import toml
from typing import Dict, Any, List
from datetime import datetime

from .logger import setup_logger

class AppConfig:
    """Manages application metadata from pyproject.toml"""
    
    def __init__(self, pyproject_path: str = None):
        self.logger = setup_logger(f"{__name__}.AppConfig")
        
        # Default pyproject.toml path
        if pyproject_path is None:
            pyproject_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pyproject.toml")
        
        self.pyproject_path = pyproject_path
        self.data = {}
        self.load_config()
    
    def load_config(self):
        """Load application metadata from pyproject.toml"""
        try:
            with open(self.pyproject_path, 'r') as f:
                self.data = toml.load(f)
            self.logger.info(f"Loaded configuration from {self.pyproject_path}")
            self.logger.info(f"App: {self.get_name()} v{self.get_version()}")
        except FileNotFoundError:
            self.logger.error(f"pyproject.toml not found: {self.pyproject_path}")
            self.data = self._get_default_data()
        except Exception as e:
            self.logger.error(f"Error loading pyproject.toml: {e}")
            self.data = self._get_default_data()
    
    def _get_default_data(self) -> Dict[str, Any]:
        """Get default data if pyproject.toml is not available"""
        return {
            "project": {
                "name": "elixir-backend",
                "version": "1.0.0",
                "description": "Backend API for Elixir Hyperbaric Chamber System"
            }
        }
    
    def reload_config(self):
        """Reload configuration from pyproject.toml"""
        self.logger.info("Reloading configuration")
        self.load_config()
    
    @property
    def project(self) -> Dict[str, Any]:
        """Get project section from pyproject.toml"""
        return self.data.get("project", {})
    
    # Basic Information
    def get_name(self) -> str:
        """Get project name"""
        return self.project.get("name", "elixir-backend")
    
    def get_version(self) -> str:
        """Get project version"""
        return self.project.get("version", "1.0.0")
    
    def get_description(self) -> str:
        """Get project description"""
        return self.project.get("description", "Backend API for Elixir Hyperbaric Chamber System")
    
    def get_authors(self) -> List[Dict[str, str]]:
        """Get list of authors"""
        return self.project.get("authors", [])
    
    def get_maintainers(self) -> List[Dict[str, str]]:
        """Get list of maintainers"""
        return self.project.get("maintainers", [])
    
    def get_license(self) -> str:
        """Get license information"""
        license_info = self.project.get("license", {})
        if isinstance(license_info, dict):
            return license_info.get("text", "MIT")
        return str(license_info) if license_info else "MIT"
    
    def get_keywords(self) -> List[str]:
        """Get project keywords"""
        return self.project.get("keywords", [])
    
    def get_urls(self) -> Dict[str, str]:
        """Get project URLs"""
        return self.data.get("project", {}).get("urls", {})
    
    def get_python_version(self) -> str:
        """Get required Python version"""
        return self.project.get("requires-python", ">=3.8")
    
    # FastAPI Configuration
    def get_fastapi_config(self) -> Dict[str, Any]:
        """Get simplified configuration for FastAPI app initialization"""
        authors = self.get_authors()
        contact = {}
        if authors:
            first_author = authors[0]
            contact = {
                "name": first_author.get("name", ""),
                "email": first_author.get("email", "")
            }
        
        config = {
            "title": self.get_name().replace("-", " ").title() + " API",
            "description": self.get_description(),
            "version": self.get_version(),
            "contact": contact,
            "license_info": {"name": self.get_license()}
        }
        
        return config
    
    # Root Endpoint Response (Simplified)
    def get_root_response(self) -> Dict[str, Any]:
        """Get simplified response data for root endpoint"""
        authors = self.get_authors()
        maintainers = self.get_maintainers()
        urls = self.get_urls()
        
        response = {
            "name": self.get_name(),
            "version": self.get_version(),
            "description": self.get_description(),
            "status": "operational",
            "python_version": self.get_python_version(),
            "license": self.get_license(),
            "api_docs": "/docs",
            "timestamp": datetime.now().isoformat()
        }
        
        # Add authors if available
        if authors:
            response["authors"] = authors
        
        # Add maintainers if available  
        if maintainers:
            response["maintainers"] = maintainers
        
        # Add keywords if available
        keywords = self.get_keywords()
        if keywords:
            response["keywords"] = keywords
        
        # Add URLs if available
        if urls:
            response["urls"] = urls
        
        return response
    
    # Health Check Response
    def get_health_response(self) -> Dict[str, Any]:
        """Get basic health check response"""
        return {
            "status": "healthy",
            "service": self.get_name(),
            "version": self.get_version(),
            "timestamp": datetime.now().isoformat()
        }

# Global instance for easy access
_app_config = None

def get_app_config() -> AppConfig:
    """Get the global app configuration instance"""
    global _app_config
    if _app_config is None:
        _app_config = AppConfig()
    return _app_config

def reload_app_config():
    """Reload the app configuration"""
    global _app_config
    if _app_config:
        _app_config.reload_config()

# Convenience functions
def get_version() -> str:
    """Get application version"""
    return get_app_config().get_version()

def get_name() -> str:
    """Get application name"""
    return get_app_config().get_name()

def get_fastapi_config() -> Dict[str, Any]:
    """Get FastAPI configuration"""
    return get_app_config().get_fastapi_config()

def get_root_response() -> Dict[str, Any]:
    """Get root endpoint response"""
    return get_app_config().get_root_response()

def get_health_response() -> Dict[str, Any]:
    """Get health check response"""
    return get_app_config().get_health_response() 