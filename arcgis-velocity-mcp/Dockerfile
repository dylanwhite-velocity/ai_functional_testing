FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy the MCP server code
COPY arcgis_velocity_mcp ./arcgis_velocity_mcp

# Run the MCP server
CMD ["python", "-m", "arcgis_velocity_mcp"]
