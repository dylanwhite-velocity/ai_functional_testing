# TestRail MCP Server

A Model Context Protocol (MCP) server for TestRail integration, maintained by the Real-Time Team. This server enables AI assistants like GitHub Copilot, Claude, Cursor, and Windsurf to interact with TestRail for test management and automation.

Source: https://github.com/sker65/testrail-mcp

## Features
- Authentication with TestRail API
- Access to TestRail entities:
  - Projects
  - Cases
  - Runs
  - Results
  - Datasets
- Full support for the Model Context Protocol

## See it in action together with Octomind MCP

[![Video Title](https://img.youtube.com/vi/I7lc9I0S62Y/0.jpg)](https://www.youtube.com/watch?v=I7lc9I0S62Y)

---

## Installation & Setup

### Prerequisites
Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))

### Step 1: Clone the Repository

```bash
git clone https://devtopia.esri.com/dyl13740/functional-testing-admin
cd ai_functional_testing
```

### Step 2: Configure TestRail Credentials

Create a `.env` file in the `testrail-mcp/` directory:

```bash
cd testrail-mcp
cat > .env << 'EOF'
TESTRAIL_URL=https://your-instance.testrail.io
TESTRAIL_USERNAME=your-email@example.com
TESTRAIL_API_KEY=your-api-key-here
EOF
```

**How to get your TestRail API key:**
1. Log in to your TestRail instance
2. Click your profile → **My Settings**
3. Navigate to **API Keys** tab
4. Click **Add Key** and copy the generated key

⚠️ **Important:** Never commit the `.env` file to version control (it's already in `.gitignore`)

### Step 3: Choose Your Installation Method

#### Docker (Recommended)**

Build and run the MCP server using Docker:

```bash
# Build the Docker image
docker compose build

# Run the server (for testing)
docker compose run --rm testrail-mcp
```

You should see: `Starting TestRail MCP server in stdio mode`

Press `Ctrl+C` to stop the test run.


## Integrating with MCP Clients

The MCP server runs in **stdio mode**, which means it communicates via standard input/output. Configure your preferred client below.

### VS Code (GitHub Copilot)

1. Locate your MCP configuration file:
   ```
   ~/Library/Application Support/Code/User/mcp.json    # macOS
   %APPDATA%/Code/User/mcp.json                        # Windows
   ~/.config/Code/User/mcp.json                        # Linux
   ```

2. Add the TestRail MCP server configuration:

   **For Docker:**
   ```json
   {
     "servers": {
       "real-time/testrail-mcp": {
         "type": "stdio",
         "command": "docker",
         "args": [
           "compose",
           "-f",
           "/FULL/PATH/TO/testrail-mcp/docker-compose.yml",
           "run",
           "--rm",
           "testrail-mcp"
         ]
       }
     }
   }
   ```


3. **Restart VS Code** to load the configuration


## Verifying Installation

### Test with MCP Inspector

The MCP Inspector provides a web UI to test your server:

```bash
cd testrail-mcp

# For Docker:
npx @modelcontextprotocol/inspector docker compose run --rm testrail-mcp

# For Python:
source .venv/bin/activate
npx @modelcontextprotocol/inspector python -m testrail_mcp
```

This opens a browser interface where you can:
- View available tools (projects, cases, runs, results)
- Test API calls interactively
- Verify your TestRail credentials

### Test in VS Code

1. Open any file in VS Code
2. Open GitHub Copilot Chat
3. Type: `@real-time/testrail-mcp list all projects`
4. You should see your TestRail projects listed

---

## Troubleshooting

### "Command not found" or "Module not found"

**Docker users:**
- Ensure Docker Desktop is running
- Run `docker compose build` to rebuild the image

### "Authentication failed"

- Verify your `.env` file has correct credentials
- Check that `TESTRAIL_URL` uses HTTPS: `https://`
- Regenerate your API key in TestRail if needed

### "Server not appearing in VS Code"

- Verify the **full absolute path** in your configuration
- Restart your editor completely
- Check for typos in the JSON configuration

### Docker permission errors

On Linux, you may need to run Docker commands with `sudo` or add your user to the `docker` group:
```bash
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

---
## Development

This server is built using:

- [FastMCP](https://github.com/jlowin/fastmcp) - A Python framework for building MCP servers
- [Requests](https://requests.readthedocs.io/) - For HTTP communication with TestRail API
- [python-dotenv](https://github.com/theskumar/python-dotenv) - For environment variable management