"""
ArcGIS Velocity MCP Server Package
"""

__version__ = "0.1.0"
__all__ = ["VelocityClient", "get_config"]

from .velocity_client import VelocityClient
from .config import get_config
