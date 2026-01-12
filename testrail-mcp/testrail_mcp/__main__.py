"""
Entry point for the TestRail MCP Server
"""

import sys
import asyncio
from .mcp_server import main

def run():
    """Run the TestRail MCP server."""
    print("Starting TestRail MCP server in stdio mode", file=sys.stderr)
    asyncio.run(main())

if __name__ == "__main__":
    run()
