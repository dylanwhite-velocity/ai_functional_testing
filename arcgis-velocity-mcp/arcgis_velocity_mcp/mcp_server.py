"""
ArcGIS Velocity MCP Server

This module implements the MCP server for ArcGIS Velocity API.
"""

import asyncio
import logging
from typing import Any, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from .velocity_client import VelocityClient
from .config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server instance
server = Server("arcgis-velocity-mcp")


def create_velocity_client() -> VelocityClient:
    """Create and return a Velocity API client"""
    config = get_config()
    return VelocityClient(
        config.base_url,
        config.username,
        config.password,
        config.portal_url
    )


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools"""
    return [
        # Feed Management
        Tool(
            name="get_feeds",
            description="Get all feeds in the Velocity environment",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_feed",
            description="Get details of a specific feed by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "feed_id": {
                        "type": "string",
                        "description": "The ID of the feed"
                    }
                },
                "required": ["feed_id"]
            }
        ),
        Tool(
            name="create_feed",
            description="Create a new feed",
            inputSchema={
                "type": "object",
                "properties": {
                    "feed_data": {
                        "type": "object",
                        "description": "The feed configuration object"
                    }
                },
                "required": ["feed_data"]
            }
        ),
        Tool(
            name="update_feed",
            description="Update an existing feed",
            inputSchema={
                "type": "object",
                "properties": {
                    "feed_id": {
                        "type": "string",
                        "description": "The ID of the feed to update"
                    },
                    "feed_data": {
                        "type": "object",
                        "description": "The updated feed configuration"
                    }
                },
                "required": ["feed_id", "feed_data"]
            }
        ),
        Tool(
            name="delete_feed",
            description="Delete a feed",
            inputSchema={
                "type": "object",
                "properties": {
                    "feed_id": {
                        "type": "string",
                        "description": "The ID of the feed to delete"
                    }
                },
                "required": ["feed_id"]
            }
        ),
        Tool(
            name="start_feed",
            description="Start a feed",
            inputSchema={
                "type": "object",
                "properties": {
                    "feed_id": {
                        "type": "string",
                        "description": "The ID of the feed to start"
                    }
                },
                "required": ["feed_id"]
            }
        ),
        Tool(
            name="stop_feed",
            description="Stop a running feed",
            inputSchema={
                "type": "object",
                "properties": {
                    "feed_id": {
                        "type": "string",
                        "description": "The ID of the feed to stop"
                    }
                },
                "required": ["feed_id"]
            }
        ),
        Tool(
            name="get_feed_status",
            description="Get the status of a specific feed",
            inputSchema={
                "type": "object",
                "properties": {
                    "feed_id": {
                        "type": "string",
                        "description": "The ID of the feed"
                    }
                },
                "required": ["feed_id"]
            }
        ),
        Tool(
            name="get_feed_metrics",
            description="Get metrics for a feed",
            inputSchema={
                "type": "object",
                "properties": {
                    "feed_id": {
                        "type": "string",
                        "description": "The ID of the feed"
                    },
                    "time_interval": {
                        "type": "string",
                        "description": "Time interval for metrics (e.g., '300s', '5m')"
                    }
                },
                "required": ["feed_id"]
            }
        ),
        Tool(
            name="clone_feed",
            description="Clone an existing feed",
            inputSchema={
                "type": "object",
                "properties": {
                    "feed_id": {
                        "type": "string",
                        "description": "The ID of the feed to clone"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name for the cloned feed"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description for the cloned feed"
                    }
                },
                "required": ["feed_id", "name"]
            }
        ),
        
        # Real-Time Analytics
        Tool(
            name="get_realtime_analytics",
            description="Get all real-time analytics",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_realtime_analytic",
            description="Get details of a specific real-time analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic"
                    }
                },
                "required": ["analytic_id"]
            }
        ),
        Tool(
            name="create_realtime_analytic",
            description="Create a new real-time analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_data": {
                        "type": "object",
                        "description": "The analytic configuration object"
                    }
                },
                "required": ["analytic_data"]
            }
        ),
        Tool(
            name="update_realtime_analytic",
            description="Update an existing real-time analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic to update"
                    },
                    "analytic_data": {
                        "type": "object",
                        "description": "The updated analytic configuration"
                    }
                },
                "required": ["analytic_id", "analytic_data"]
            }
        ),
        Tool(
            name="delete_realtime_analytic",
            description="Delete a real-time analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic to delete"
                    }
                },
                "required": ["analytic_id"]
            }
        ),
        Tool(
            name="start_realtime_analytic",
            description="Start a real-time analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic to start"
                    }
                },
                "required": ["analytic_id"]
            }
        ),
        Tool(
            name="stop_realtime_analytic",
            description="Stop a real-time analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic to stop"
                    }
                },
                "required": ["analytic_id"]
            }
        ),
        Tool(
            name="get_realtime_analytic_status",
            description="Get the status of a real-time analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic"
                    }
                },
                "required": ["analytic_id"]
            }
        ),
        Tool(
            name="get_realtime_analytic_metrics",
            description="Get metrics for a real-time analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic"
                    },
                    "time_interval": {
                        "type": "string",
                        "description": "Time interval for metrics"
                    }
                },
                "required": ["analytic_id"]
            }
        ),
        
        # Big Data Analytics
        Tool(
            name="get_bigdata_analytics",
            description="Get all big data analytics",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_bigdata_analytic",
            description="Get details of a specific big data analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic"
                    }
                },
                "required": ["analytic_id"]
            }
        ),
        Tool(
            name="create_bigdata_analytic",
            description="Create a new big data analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_data": {
                        "type": "object",
                        "description": "The analytic configuration object"
                    }
                },
                "required": ["analytic_data"]
            }
        ),
        Tool(
            name="update_bigdata_analytic",
            description="Update an existing big data analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic to update"
                    },
                    "analytic_data": {
                        "type": "object",
                        "description": "The updated analytic configuration"
                    }
                },
                "required": ["analytic_id", "analytic_data"]
            }
        ),
        Tool(
            name="delete_bigdata_analytic",
            description="Delete a big data analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic to delete"
                    }
                },
                "required": ["analytic_id"]
            }
        ),
        Tool(
            name="start_bigdata_analytic",
            description="Start a big data analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic to start"
                    }
                },
                "required": ["analytic_id"]
            }
        ),
        Tool(
            name="stop_bigdata_analytic",
            description="Stop a big data analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic to stop"
                    }
                },
                "required": ["analytic_id"]
            }
        ),
        Tool(
            name="get_bigdata_analytic_status",
            description="Get the status of a big data analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic"
                    }
                },
                "required": ["analytic_id"]
            }
        ),
        Tool(
            name="clone_bigdata_analytic",
            description="Clone an existing big data analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic to clone"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name for the cloned analytic"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description for the cloned analytic"
                    }
                },
                "required": ["analytic_id", "name"]
            }
        ),
        Tool(
            name="scale_bigdata_analytic",
            description="Scale a running big data analytic",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic to scale"
                    },
                    "cpu": {
                        "type": "number",
                        "description": "CPU allocation"
                    },
                    "memory": {
                        "type": "number",
                        "description": "Memory allocation in GB"
                    },
                    "instances": {
                        "type": "integer",
                        "description": "Number of instances"
                    }
                },
                "required": ["analytic_id", "cpu", "memory", "instances"]
            }
        ),
        Tool(
            name="validate_bigdata_analytic",
            description="Validate a big data analytic configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_data": {
                        "type": "object",
                        "description": "The analytic configuration to validate"
                    }
                },
                "required": ["analytic_data"]
            }
        ),
        Tool(
            name="validate_bigdata_analytic_by_id",
            description="Validate a big data analytic by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "analytic_id": {
                        "type": "string",
                        "description": "The ID of the analytic to validate"
                    }
                },
                "required": ["analytic_id"]
            }
        ),
        
        # Services
        Tool(
            name="get_feature_services",
            description="Get all feature services",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_feature_service",
            description="Get details of a specific feature service",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "The ID of the feature service"
                    }
                },
                "required": ["service_id"]
            }
        ),
        Tool(
            name="get_stream_services",
            description="Get all stream services",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_stream_service",
            description="Get details of a specific stream service",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "The ID of the stream service"
                    }
                },
                "required": ["service_id"]
            }
        ),
        
        # Definitions
        Tool(
            name="get_feed_types",
            description="Get all available feed type definitions",
            inputSchema={
                "type": "object",
                "properties": {
                    "locale": {
                        "type": "string",
                        "description": "Locale for localized labels (e.g., 'en_US')"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_tool_definitions",
            description="Get all available tool definitions for analytics",
            inputSchema={
                "type": "object",
                "properties": {
                    "locale": {
                        "type": "string",
                        "description": "Locale for localized labels"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_output_definitions",
            description="Get all available output definitions",
            inputSchema={
                "type": "object",
                "properties": {
                    "locale": {
                        "type": "string",
                        "description": "Locale for localized labels"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_source_definitions",
            description="Get all available source definitions",
            inputSchema={
                "type": "object",
                "properties": {
                    "locale": {
                        "type": "string",
                        "description": "Locale for localized labels"
                    }
                },
                "required": []
            }
        ),
        
        # System
        Tool(
            name="get_version",
            description="Get the Velocity API version",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="query_logs",
            description="Query system logs with various filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "query_params": {
                        "type": "object",
                        "description": "Query parameters for filtering logs"
                    }
                },
                "required": ["query_params"]
            }
        ),
        Tool(
            name="export_configuration",
            description="Export a snapshot of the current configuration",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_tenant_metrics",
            description="Get tenant-level metrics summary",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    
    async with create_velocity_client() as client:
        try:
            result = None
            
            # Feed Management
            if name == "get_feeds":
                result = await client.get_feeds()
            elif name == "get_feed":
                result = await client.get_feed(arguments["feed_id"])
            elif name == "create_feed":
                result = await client.create_feed(arguments["feed_data"])
            elif name == "update_feed":
                result = await client.update_feed(arguments["feed_id"], arguments["feed_data"])
            elif name == "delete_feed":
                result = await client.delete_feed(arguments["feed_id"])
            elif name == "start_feed":
                result = await client.start_feed(arguments["feed_id"])
            elif name == "stop_feed":
                result = await client.stop_feed(arguments["feed_id"])
            elif name == "get_feed_status":
                result = await client.get_feed_status(arguments["feed_id"])
            elif name == "get_feed_metrics":
                result = await client.get_feed_metrics(
                    arguments["feed_id"],
                    arguments.get("time_interval")
                )
            elif name == "clone_feed":
                result = await client.clone_feed(
                    arguments["feed_id"],
                    arguments["name"],
                    arguments.get("description")
                )
            
            # Real-Time Analytics
            elif name == "get_realtime_analytics":
                result = await client.get_realtime_analytics()
            elif name == "get_realtime_analytic":
                result = await client.get_realtime_analytic(arguments["analytic_id"])
            elif name == "create_realtime_analytic":
                result = await client.create_realtime_analytic(arguments["analytic_data"])
            elif name == "update_realtime_analytic":
                result = await client.update_realtime_analytic(
                    arguments["analytic_id"],
                    arguments["analytic_data"]
                )
            elif name == "delete_realtime_analytic":
                result = await client.delete_realtime_analytic(arguments["analytic_id"])
            elif name == "start_realtime_analytic":
                result = await client.start_realtime_analytic(arguments["analytic_id"])
            elif name == "stop_realtime_analytic":
                result = await client.stop_realtime_analytic(arguments["analytic_id"])
            elif name == "get_realtime_analytic_status":
                result = await client.get_realtime_analytic_status(arguments["analytic_id"])
            elif name == "get_realtime_analytic_metrics":
                result = await client.get_realtime_analytic_metrics(
                    arguments["analytic_id"],
                    arguments.get("time_interval")
                )
            
            # Big Data Analytics
            elif name == "get_bigdata_analytics":
                result = await client.get_bigdata_analytics()
            elif name == "get_bigdata_analytic":
                result = await client.get_bigdata_analytic(arguments["analytic_id"])
            elif name == "create_bigdata_analytic":
                result = await client.create_bigdata_analytic(arguments["analytic_data"])
            elif name == "update_bigdata_analytic":
                result = await client.update_bigdata_analytic(
                    arguments["analytic_id"],
                    arguments["analytic_data"]
                )
            elif name == "delete_bigdata_analytic":
                result = await client.delete_bigdata_analytic(arguments["analytic_id"])
            elif name == "start_bigdata_analytic":
                result = await client.start_bigdata_analytic(arguments["analytic_id"])
            elif name == "stop_bigdata_analytic":
                result = await client.stop_bigdata_analytic(arguments["analytic_id"])
            elif name == "get_bigdata_analytic_status":
                result = await client.get_bigdata_analytic_status(arguments["analytic_id"])
            elif name == "clone_bigdata_analytic":
                result = await client.clone_bigdata_analytic(
                    arguments["analytic_id"],
                    arguments["name"],
                    arguments.get("description")
                )
            elif name == "scale_bigdata_analytic":
                result = await client.scale_bigdata_analytic(
                    arguments["analytic_id"],
                    arguments["cpu"],
                    arguments["memory"],
                    arguments["instances"]
                )
            elif name == "validate_bigdata_analytic":
                result = await client.validate_bigdata_analytic(arguments["analytic_data"])
            elif name == "validate_bigdata_analytic_by_id":
                result = await client.validate_bigdata_analytic_by_id(arguments["analytic_id"])
            
            # Services
            elif name == "get_feature_services":
                result = await client.get_feature_services()
            elif name == "get_feature_service":
                result = await client.get_feature_service(arguments["service_id"])
            elif name == "get_stream_services":
                result = await client.get_stream_services()
            elif name == "get_stream_service":
                result = await client.get_stream_service(arguments["service_id"])
            
            # Definitions
            elif name == "get_feed_types":
                result = await client.get_feed_types(arguments.get("locale"))
            elif name == "get_tool_definitions":
                result = await client.get_tool_definitions(arguments.get("locale"))
            elif name == "get_output_definitions":
                result = await client.get_output_definitions(arguments.get("locale"))
            elif name == "get_source_definitions":
                result = await client.get_source_definitions(arguments.get("locale"))
            
            # System
            elif name == "get_version":
                result = await client.get_version()
            elif name == "query_logs":
                result = await client.query_logs(arguments["query_params"])
            elif name == "export_configuration":
                result = await client.export_configuration()
            elif name == "get_tenant_metrics":
                result = await client.get_tenant_metrics_summary()
            
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            # Format the response
            import json
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error executing tool {name}: {str(e)}")
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]


async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
