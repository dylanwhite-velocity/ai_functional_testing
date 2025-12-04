# ArcGIS Velocity MCP Server

A Model Context Protocol (MCP) server providing programmatic access to ArcGIS Velocity API endpoints. This server enables AI assistants and other MCP clients to interact with Velocity feeds, analytics, services, and other resources.

## Features

- **Automatic Token Management**: Automatically generates and refreshes authentication tokens - no manual token management required
- **Feed Management**: Create, read, update, delete, start, stop, and monitor feeds
- **Real-Time Analytics**: Manage real-time analytics tasks
- **Big Data Analytics**: Manage big data analytics tasks
- **Services**: Manage feature, map, and stream services
- **Metrics & Monitoring**: Retrieve metrics, status, and history for feeds and analytics
- **Configuration**: Import/export configurations
- **Logs**: Query system logs
- **Retry Logic**: Automatically retries failed requests due to token expiration

## Prerequisites

- Python 3.10 or higher
- ArcGIS Velocity environment access
- Valid ArcGIS username and password

## Installation

### Using Docker

1. Clone this repository
2. Create a `.env` file with your Velocity configuration:

```env
VELOCITY_BASE_URL=https://your-velocity-instance.arcgis.com
VELOCITY_USERNAME=your_username
VELOCITY_PASSWORD=your_password
VELOCITY_PORTAL_URL=https://www.arcgis.com
```

3. Build and run:

```bash
docker-compose up --build
```

### Local Development

1. Install dependencies:

```bash
pip install -e .
```

2. Set environment variables:

```bash
export VELOCITY_BASE_URL=https://your-velocity-instance.arcgis.com
export VELOCITY_USERNAME=your_username
export VELOCITY_PASSWORD=your_password
export VELOCITY_PORTAL_URL=https://www.arcgis.com
```

3. Run the server:

```bash
python -m arcgis_velocity_mcp
```

## Configuration

The server requires the following environment variables:

- `VELOCITY_BASE_URL`: Base URL of your Velocity deployment (e.g., `https://us5-iotdev.arcgis.com/dedicated/ksoqrenrugvqxizs`)
- `VELOCITY_USERNAME`: Your ArcGIS username
- `VELOCITY_PASSWORD`: Your ArcGIS password
- `VELOCITY_PORTAL_URL`: Portal URL for token generation (e.g., `https://www.arcgis.com` for ArcGIS Online)

**Note:** The server automatically generates and refreshes authentication tokens as needed, so you don't need to worry about token expiration.

## Available Tools

### Feed Management
- `get_feeds` - List all feeds
- `get_feed` - Get a specific feed by ID
- `create_feed` - Create a new feed
- `update_feed` - Update an existing feed
- `delete_feed` - Delete a feed
- `start_feed` - Start a feed
- `stop_feed` - Stop a feed
- `get_feed_status` - Get feed status
- `get_feed_metrics` - Get feed metrics
- `clone_feed` - Clone an existing feed

### Real-Time Analytics
- `get_realtime_analytics` - List all real-time analytics
- `get_realtime_analytic` - Get a specific analytic
- `create_realtime_analytic` - Create a new analytic
- `update_realtime_analytic` - Update an analytic
- `delete_realtime_analytic` - Delete an analytic
- `start_realtime_analytic` - Start an analytic
- `stop_realtime_analytic` - Stop an analytic
- `get_realtime_analytic_status` - Get analytic status
- `get_realtime_analytic_metrics` - Get analytic metrics

### Big Data Analytics
- `get_bigdata_analytics` - List all big data analytics
- `get_bigdata_analytic` - Get a specific analytic
- `create_bigdata_analytic` - Create a new analytic
- `update_bigdata_analytic` - Update an analytic
- `delete_bigdata_analytic` - Delete an analytic
- `start_bigdata_analytic` - Start an analytic
- `stop_bigdata_analytic` - Stop an analytic
- `get_bigdata_analytic_status` - Get analytic status

### Services
- `get_feature_services` - List feature services
- `get_feature_service` - Get a specific feature service
- `get_stream_services` - List stream services
- `get_stream_service` - Get a specific stream service

### System
- `get_version` - Get Velocity API version
- `query_logs` - Query system logs
- `export_configuration` - Export configuration snapshot
- `get_tenant_metrics` - Get tenant-level metrics

## Usage with Claude Desktop

Add to your Claude Desktop configuration:

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
        "VELOCITY_BASE_URL=https://your-velocity-instance.arcgis.com",
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

## API Documentation

For complete API documentation, refer to the Swagger UI at:
`https://<your-velocity-instance>/iot/api/swagger.html`

## License

This project is licensed under the terms specified in the ArcGIS Velocity license agreement.

## Support

For issues related to:
- This MCP server: Create an issue in this repository
- ArcGIS Velocity API: Consult official Esri documentation
