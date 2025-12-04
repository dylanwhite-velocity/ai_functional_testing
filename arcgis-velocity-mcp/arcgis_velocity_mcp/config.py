"""
Configuration module for ArcGIS Velocity MCP Server
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


@dataclass
class Config:
    """Configuration for Velocity MCP Server"""
    base_url: str
    username: str
    password: str
    portal_url: str
    
    def __post_init__(self):
        """Validate configuration"""
        if not self.base_url:
            raise ValueError("VELOCITY_BASE_URL environment variable is required")
        if not self.username:
            raise ValueError("VELOCITY_USERNAME environment variable is required")
        if not self.password:
            raise ValueError("VELOCITY_PASSWORD environment variable is required")
        if not self.portal_url:
            raise ValueError("VELOCITY_PORTAL_URL environment variable is required")
        
        # Ensure URLs don't end with a slash
        self.base_url = self.base_url.rstrip('/')
        self.portal_url = self.portal_url.rstrip('/')


def get_config() -> Config:
    """
    Get configuration from environment variables.
    
    Returns:
        Config object with Velocity settings
    
    Raises:
        ValueError: If required environment variables are missing
    """
    return Config(
        base_url=os.getenv("VELOCITY_BASE_URL", ""),
        username=os.getenv("VELOCITY_USERNAME", ""),
        password=os.getenv("VELOCITY_PASSWORD", ""),
        portal_url=os.getenv("VELOCITY_PORTAL_URL", "")
    )
