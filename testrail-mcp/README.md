# TestRail MCP Server

A Model Context Protocol (MCP) server for TestRail integration, maintained by the Real-Time Team. This server enables AI assistants like GitHub Copilot, Claude, Cursor, and Windsurf to interact with TestRail for test management and automation.

**Version:** 0.2.0

Based on: https://github.com/sker65/testrail-mcp

## Features
- Authentication with TestRail API
- Access to TestRail entities:
  - **Projects** - Create, read, update, and delete projects
  - **Test Cases** - Manage test cases with full CRUD operations
  - **Test Suites** - View and organize test suites
  - **Sections** - Create and manage test sections/folders
  - **Test Runs** - Create, update, close, and delete test runs
  - **Test Results** - Add and view test execution results
  - **Datasets** - Manage data-driven testing datasets
- Stdio-based communication for seamless integration
- Automatic pagination for large result sets
- Built with official MCP SDK for stability and compatibility

---

## Installation & Setup

### Prerequisites
Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))

### Step 1: Clone the Repository

```bash
git clone https://devtopia.esri.com/dyl13740/functional-testing-admin
cd ai_functional_testing/testrail-mcp
```

### Step 2: Configure TestRail Credentials

Create a `.env` file in the `testrail-mcp/` directory:

```bash
cat > .env << 'EOF'
TESTRAIL_URL=https://esri.testrail.com
TESTRAIL_USERNAME=your-email@esri.com
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
Build the Docker Image

Build and test the MCP server using Docker:

```bash
# Build the Docker image
docker compose build

# Test the server (optional - for verification)
docker compose run --rm testrail-mcp
```

You should see: `Starting TestRail MCP server in stdio mode`

The server will wait for MCP protocol messages. Press `Ctrl+C` to stop the test run.

> **Note:** The server runs in stdio mode and communicates via standard input/output. It's not meant to run standalone - it integrates with MCP clients like VS Code

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
```

This opens a browser interface where you can:
- View all 29 available tools (projects, cases, runs, results, sections, datasets)
- Test API calls interactively
- Verify your TestRail credentials
- Explore the full API schema
### Test in VS Code
 with GitHub Copilot

1. **Completely quit and restart VS Code** (⌘Q on Mac, not just reload window)
2. Wait 10-15 seconds for MCP servers to initialize
3. Open GitHub Copilot Chat
4. Test the connection:
   ```
   List all TestRail projects
   ```
   
You should see all projects from your TestRail instance, including ArcGIS Velocity (ID: 63).

**Example queries to try:**
- `Get test runs for ArcGIS Velocity project`
- `Show me test cases in suite 7253`
- `Get the status of test run 12345`
---

## Troubleshooting

### "Command not found" or "Module not found"

**Docker users:**
- Ensure Docker Desktop is running
- Run `docker compose build` to rebuild the image

### "Authentication failed"

- Verify your `.env` file has correct or "Tools not available"

**This is the most common issue.** The server may be running but not registered with VS Code yet.

**Solution:**
1. **Completely quit VS Code** (⌘Q on Mac, not reload window)
2. Wait 10-15 seconds
3. Restart VS Code
4. Wait for MCP servers to initialize (10-15 seconds)
5. Start a **new chat session**

**Verify configuration:**
- Check the **full absolute path** in `mcp.json`
- Ensure path uses forward slashes: `/Users/...`
- No typos in the JSON configuration

## Available Tools

The server provides **29 tools** for comprehensive TestRail integration:

**Projects:** `get_project`, `get_projects`, `add_project`, `update_project`, `delete_project`

**Test Cases:** `get_case`, `get_cases`, `add_case`, `update_case`, `delete_case`

**Test Suites:** `get_suite`, `get_suites`

**Sections:** `get_section`, `get_sections`, `add_section`, `update_section`, `delete_section`, `move_section`

**Test Runs:** `get_run`, `get_runs`, `add_run`, `update_run`, `close_run`, `delete_run`

**Test Results:** `get_results`, `add_result`

**Datasets:** `get_dataset`, `get_datasets`, `add_dataset`, `update_dataset`, `delete_dataset`

---

## Development & Architecture

This server is built using:

- **[MCP SDK](https://github.com/modelcontextprotocol)** - Official Model Context Protocol SDK (v1.0.0+)
- **[Requests](https://requests.readthedocs.io/)** - HTTP communication with TestRail API
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** - Environment variable management
- **Python 3.10+** - Modern Python features and type hints


---

## Team Resources

**Primary TestRail Project:** ArcGIS Velocity (ID: 63)
- URL: https://esri.testrail.com/index.php?/projects/overview/63
- Multiple test suite mode
- Default role: Real-Time PE

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review server logs: `docker logs $(docker ps -q --filter "name=testrail-mcp")`
3. Contact Real-Time Team
4. File an issue in the repository
**View server logs:**
```bash
docker logs $(docker ps -q --filter "name=testrail-mcp")
```

- Verify the **full absolute path** in your configuration
- Restart your editor completely
- Check for typos in the JSON configuration
