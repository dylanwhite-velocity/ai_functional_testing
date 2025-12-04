# Quick Start Guide - ArcGIS Velocity MCP Server

## Setup

1. **Copy the environment template:**
   ```bash
   cd arcgis-velocity-mcp
   cp .env.example .env
   ```

2. **Configure your environment:**
   Edit `.env` and set your Velocity credentials:
   ```env
   VELOCITY_BASE_URL=https://us5-iotdev.arcgis.com/dedicated/ksoqrenrugvqxizs
   VELOCITY_USERNAME=your_username
   VELOCITY_PASSWORD=your_password
   VELOCITY_PORTAL_URL=https://www.arcgis.com
   ```
   
   **Note:** The server automatically generates and refreshes tokens, so you don't need to manage tokens manually.

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```

## Testing the Server

### Run locally:
```bash
python -m arcgis_velocity_mcp
```

### Using Docker:
```bash
docker-compose up --build
```

## Common Use Cases

### 1. List All Feeds
```json
{
  "tool": "get_feeds",
  "arguments": {}
}
```

### 2. Get Feed Status
```json
{
  "tool": "get_feed_status",
  "arguments": {
    "feed_id": "ae8c39de11b645d397b7e4bb548ab088"
  }
}
```

### 3. Start a Feed
```json
{
  "tool": "start_feed",
  "arguments": {
    "feed_id": "ae8c39de11b645d397b7e4bb548ab088"
  }
}
```

### 4. Get Real-Time Analytics
```json
{
  "tool": "get_realtime_analytics",
  "arguments": {}
}
```

### 5. Query Logs
```json
{
  "tool": "query_logs",
  "arguments": {
    "query_params": {
      "itemId": "ae8c39de11b645d397b7e4bb548ab088",
      "level": "ERROR",
      "size": 50
    }
  }
}
```

### 6. Get Feed Metrics
```json
{
  "tool": "get_feed_metrics",
  "arguments": {
    "feed_id": "ae8c39de11b645d397b7e4bb548ab088",
    "time_interval": "300s"
  }
}
```

### 7. Clone a Feed
```json
{
  "tool": "clone_feed",
  "arguments": {
    "feed_id": "ae8c39de11b645d397b7e4bb548ab088",
    "name": "Cloned Feed Name",
    "description": "Description of the cloned feed"
  }
}
```

## Integration with Claude Desktop

Add this to your Claude Desktop MCP settings file:

### macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
### Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "arcgis-velocity": {
      "command": "python",
      "args": [
        "-m",
        "arcgis_velocity_mcp"
      ],
      "env": {
        "VELOCITY_BASE_URL": "https://us5-iotdev.arcgis.com/dedicated/ksoqrenrugvqxizs",
        "VELOCITY_USERNAME": "your_username",
        "VELOCITY_PASSWORD": "your_password",
        "VELOCITY_PORTAL_URL": "https://www.arcgis.com"
      }
    }
  }
}
```

Or using Docker:

```json
{
  "mcpServers": {
    "arcgis-velocity": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "VELOCITY_BASE_URL=https://us5-iotdev.arcgis.com/dedicated/ksoqrenrugvqxizs",
        "-e",
        "VELOCITY_USERNAME=your_username",
        "-e",
        "VELOCITY_PASSWORD=your_password",
        "-e",
        "VELOCITY_PORTAL_URL=https://www.arcgis.com",
        "arcgis-velocity-mcp"
      ]
    }
  }
}
```

## Example Prompts for Claude

Once configured, you can ask Claude:

- "List all feeds in Velocity"
- "Show me the status of feed [feed_id]"
- "Start the feed with ID [feed_id]"
- "Get metrics for feed [feed_id] over the last 5 minutes"
- "What real-time analytics are currently running?"
- "Show me error logs from the last hour for item [item_id]"
- "Clone the feed [feed_id] with the name 'Test Feed Clone'"
- "What's the current version of the Velocity API?"
- "Get all available feed types"
- "Show me tenant-level metrics"

## Authentication

### Username and Password

The MCP server uses your ArcGIS username and password to automatically generate and refresh authentication tokens. This means:

- **No manual token management** - tokens are generated automatically
- **Automatic refresh** - tokens are refreshed 5 minutes before expiration
- **Retry logic** - if a token becomes invalid, the server will generate a new one automatically

### Portal URLs

- **ArcGIS Online:** `https://www.arcgis.com`
- **ArcGIS Enterprise:** `https://your-portal.domain.com/portal`

## Troubleshooting

### "Authentication failed" or "Token generation failed"
- Verify your `VELOCITY_USERNAME` and `VELOCITY_PASSWORD` are correct
- Ensure your account has access to the Velocity instance
- Check that `VELOCITY_PORTAL_URL` is correct (e.g., `https://www.arcgis.com` for ArcGIS Online)
- Verify your account has the necessary permissions

### "Connection refused"
- Check that `VELOCITY_BASE_URL` is correct
- Verify network connectivity to the Velocity instance
- Ensure the Velocity service is running

### "Tool not found"
- Restart Claude Desktop after updating the configuration
- Check that the MCP server is properly installed

### Docker issues
- Ensure Docker is running
- Check that the image built successfully: `docker images | grep velocity`
- View logs: `docker-compose logs`

## API Documentation

For complete API reference, visit the Swagger UI at:
```
https://your-velocity-instance/iot/api/swagger.html
```

Replace `your-velocity-instance` with your actual Velocity deployment URL.
