"""
PLC Configuration Module

This module handles loading and accessing PLC memory addresses from the configuration file.
It provides a centralized way to manage PLC addresses without hardcoding them in the API routes.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from .logger import setup_logger

class PLCConfig:
    """Manages PLC address configuration"""
    
    def __init__(self, config_path: str = None):
        self.logger = setup_logger(f"{__name__}.PLCConfig")
        
        # Default config path
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "plc_addresses.json")
        
        self.config_path = config_path
        self.addresses = {}
        self.load_config()
    
    def load_config(self):
        """Load PLC addresses from configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                self.addresses = json.load(f)
            self.logger.info(f"Loaded PLC configuration from {self.config_path}")
            self.logger.info(f"Categories loaded: {list(self.addresses.keys())}")
        except FileNotFoundError:
            self.logger.error(f"PLC configuration file not found: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in PLC configuration file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading PLC configuration: {e}")
            raise
    
    def reload_config(self):
        """Reload configuration from file"""
        self.logger.info("Reloading PLC configuration")
        self.load_config()
    
    def get_address(self, category: str, function: str) -> str:
        """
        Get PLC address for a specific category and function
        
        Args:
            category: The category (e.g., 'pressure_control', 'sensors')
            function: The function name (e.g., 'internal_pressure_1', 'current_temperature')
        
        Returns:
            The PLC memory address (e.g., 'VD504', 'M1.4')
        
        Raises:
            KeyError: If category or function not found
        """
        try:
            return self.addresses[category][function]["address"]
        except KeyError as e:
            self.logger.error(f"Address not found: category='{category}', function='{function}'")
            available_categories = list(self.addresses.keys())
            if category in self.addresses:
                available_functions = list(self.addresses[category].keys())
                self.logger.error(f"Available functions in '{category}': {available_functions}")
            else:
                self.logger.error(f"Available categories: {available_categories}")
            raise KeyError(f"PLC address not found: {category}.{function}")
    
    def get_comment(self, category: str, function: str) -> str:
        """
        Get comment for a specific category and function
        
        Args:
            category: The category
            function: The function name
        
        Returns:
            The comment/description
        """
        try:
            return self.addresses[category][function]["comment"]
        except KeyError:
            return "No comment available"
    
    def get_category(self, category: str) -> Dict[str, Dict[str, str]]:
        """
        Get all functions in a category
        
        Args:
            category: The category name
        
        Returns:
            Dictionary of functions with their addresses and comments
        """
        if category not in self.addresses:
            available = list(self.addresses.keys())
            raise KeyError(f"Category '{category}' not found. Available: {available}")
        
        return self.addresses[category]
    
    def get_all_categories(self) -> list:
        """Get list of all available categories"""
        return list(self.addresses.keys())
    
    def get_all_functions(self, category: str) -> list:
        """Get list of all functions in a category"""
        if category not in self.addresses:
            return []
        return list(self.addresses[category].keys())
    
    def validate_config(self) -> bool:
        """
        Validate the configuration structure
        
        Returns:
            True if valid, False otherwise
        """
        try:
            for category, functions in self.addresses.items():
                if not isinstance(functions, dict):
                    self.logger.error(f"Category '{category}' should contain a dictionary")
                    return False
                
                for function, config in functions.items():
                    if not isinstance(config, dict):
                        self.logger.error(f"Function '{function}' in '{category}' should be a dictionary")
                        return False
                    
                    if "address" not in config:
                        self.logger.error(f"Missing 'address' in {category}.{function}")
                        return False
                    
                    if "comment" not in config:
                        self.logger.warning(f"Missing 'comment' in {category}.{function}")
            
            self.logger.info("PLC configuration validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
    
    def search_address(self, address: str) -> list:
        """
        Search for functions that use a specific address
        
        Args:
            address: The PLC address to search for
        
        Returns:
            List of tuples (category, function, comment)
        """
        results = []
        for category, functions in self.addresses.items():
            for function, config in functions.items():
                if config["address"].upper() == address.upper():
                    results.append((category, function, config["comment"]))
        
        return results
    
    def get_addresses_by_pattern(self, pattern: str) -> Dict[str, list]:
        """
        Get all addresses matching a pattern (e.g., 'VD*', 'M1.*')
        
        Args:
            pattern: Pattern to match (basic wildcard support with *)
        
        Returns:
            Dictionary with pattern matches
        """
        import fnmatch
        
        results = {}
        for category, functions in self.addresses.items():
            category_results = []
            for function, config in functions.items():
                if fnmatch.fnmatch(config["address"].upper(), pattern.upper()):
                    category_results.append({
                        "function": function,
                        "address": config["address"],
                        "comment": config["comment"]
                    })
            
            if category_results:
                results[category] = category_results
        
        return results

# Global instance for easy access
_plc_config = None

def get_plc_config() -> PLCConfig:
    """Get the global PLC configuration instance"""
    global _plc_config
    if _plc_config is None:
        _plc_config = PLCConfig()
    return _plc_config

def get_address(category: str, function: str) -> str:
    """Convenience function to get an address"""
    return get_plc_config().get_address(category, function)

def reload_config():
    """Reload the PLC configuration"""
    global _plc_config
    if _plc_config:
        _plc_config.reload_config()

# Convenience functions for common categories
class Addresses:
    """Convenience class with static methods for accessing addresses"""
    
    @staticmethod
    def auth(function: str) -> str:
        """Get authentication addresses"""
        return get_address("authentication", function)
    
    @staticmethod
    def language(function: str) -> str:
        """Get language control addresses"""
        return get_address("language", function)
    
    @staticmethod
    def control(function: str) -> str:
        """Get control panel addresses"""
        return get_address("control_panel", function)
    
    @staticmethod
    def pressure(function: str) -> str:
        """Get pressure control addresses"""
        return get_address("pressure_control", function)
    
    @staticmethod
    def session(function: str) -> str:
        """Get session control addresses"""
        return get_address("session_control", function)
    
    @staticmethod
    def modes(function: str) -> str:
        """Get operating mode addresses"""
        return get_address("operating_modes", function)
    
    @staticmethod
    def temperature(function: str) -> str:
        """Get temperature control addresses"""
        return get_address("temperature_control", function)
    
    @staticmethod
    def sensors(function: str) -> str:
        """Get sensor addresses"""
        return get_address("sensors", function)
    
    @staticmethod
    def calibration(function: str) -> str:
        """Get calibration addresses"""
        return get_address("calibration", function)
    
    @staticmethod
    def manual(function: str) -> str:
        """Get manual control addresses"""
        return get_address("manual_controls", function)
    
    @staticmethod
    def timers(function: str) -> str:
        """Get timer addresses"""
        return get_address("timers", function) 