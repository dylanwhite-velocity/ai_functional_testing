# Soak Monitoring Logs

Automated error monitoring for ArcGIS Velocity soak environments. Fetches and correlates Velocity item logs with Kubernetes pod logs to identify issues.

## Project Structure

```
soak-monitoring-logs/
├── src/
│   ├── get_velocity_item_logs.py   # Fetch Velocity API logs
│   └── get_pod_logs_for_errors.py  # Fetch K8s pod logs
├── templates/
│   └── report_template.md          # Report template (editable)
├── environments.yaml               # Target environments config
├── logs/                           # Output directory (gitignored)
└── README.md

.github/prompts/
└── soak-monitoring.prompt.md       # VS Code Copilot prompt
```

## Prerequisites

- Python 3.11+
- kubectl configured with cluster contexts
- Access to SUTConfig via AWS Secrets Manager (common package)

## Installation

From the project root:
```bash
pip install -e ".[soak-monitoring]"
```

## Usage

### Option 1: Use VS Code Copilot Prompt (Recommended)

1. Edit `environments.yaml` - uncomment/comment environments you want to process
2. Open VS Code with Copilot
3. In Copilot Chat, type `/` and select `soak-monitoring`
4. Run the prompt - Copilot will execute the workflow and generate a report

### Option 2: Manual Execution

**Multi-Environment Mode (using config file):**
```bash
cd soak-monitoring-logs

# Step 1: Fetch Velocity item logs (uses velocity_hours from config)
python src/get_velocity_item_logs.py --config environments.yaml

# Step 2: Fetch pod logs for items with errors (uses pod_hours from config)
python src/get_pod_logs_for_errors.py logs/velocity_errors_*.json --config environments.yaml
```

**Single-Environment Mode:**
```bash
cd soak-monitoring-logs

# Step 1: Fetch Velocity item logs
python src/get_velocity_item_logs.py \
    --sut "qa-advanced" \
    --username "neo_admin_soak_dog" \
    --org-id "rzbirc1krb814pev" \
    --hours 24

# Step 2: Fetch pod logs for items with errors
python src/get_pod_logs_for_errors.py logs/velocity_errors_*.json \
    --context "qa-advanced" \
    --namespace "velocity-rzbirc1krb814pev-services"
```

## Environment Configuration

Edit `environments.yaml` to configure target environments and settings:

```yaml
# Log fetch settings
settings:
  velocity_hours: 24    # Hours to look back for Velocity API logs
  pod_hours: 6          # Hours to look back for K8s pod logs

instances:
  - name: qa-advanced           # SUT config name
    organizationId: rzbirc1krb814pev
    usernames:
      - neo_admin_soak_dog

  # Comment out to skip:
  # - name: qa-basic
  #   organizationId: nc7yvw8shwjniihe
  #   usernames:
  #     - neo_admin_soak_cat
```

## Script Arguments

### get_velocity_item_logs.py

| Argument | Required | Description |
|----------|----------|-------------|
| `--config` | Either | YAML config file for multi-environment mode |
| `--sut` | Either | SUT Config name (single-environment mode) |
| `--org-id` | With --sut | Org ID for SUTConfig |
| `--username` | With --sut | Username for SUTConfig |
| `--type` | No | Filter: `feeds`, `rats`, or `bats` |
| `--hours` | No | Hours to look back (from config `velocity_hours` or default 24) |

Use either `--config` OR (`--sut`, `--org-id`, `--username`) together.

### get_pod_logs_for_errors.py

| Argument | Required | Description |
|----------|----------|-------------|
| `errors_file` | Yes | JSON file from get_velocity_item_logs.py |
| `--config` | Either | YAML config file (derives context/namespace automatically) |
| `--context` | Either | Kubernetes context (required without --config) |
| `--namespace` | Either | Kubernetes namespace (required without --config) |
| `--item-ids` | No | Alternative to errors_file: comma-separated item IDs |
| `--hours` | No | Hours of logs to fetch (from config `pod_hours` or default 6) |

Use either `--config` OR (`--context`, `--namespace`) together.

## SUTConfig Integration

This project uses the `common.sut_config.SUTConfigManager` to load Velocity API credentials from AWS Secrets Manager. The SUT config provides:

- `apiUrl` - Velocity API base URL
- `auth.username` - Username for authentication
- `auth.password` - Password for authentication
- `auth.url` - Portal URL for token generation (optional)
- `distribution` - VelocitySaaS, VelocityEnterprise, or GeoEvent

**Note:** Kubernetes context and namespace are derived from `environments.yaml`:
- Context = instance name
- Namespace = `velocity-{organizationId}-services`

## Available SUTConfigs

List available configs:
```python
from common.sut_config.sut_config_manager import SUTConfigManager
manager = SUTConfigManager()
print(manager.list_available_configs())
```

## Output Files

Scripts output JSON files to the `logs/` directory:

| File | Contents |
|------|----------|
| `velocity_errors_<timestamp>.json` | Velocity API error logs |
| `pod_logs_<timestamp>.json` | Kubernetes pod logs |
| `report_<timestamp>.md` | Generated report (via Copilot) |

## Report Template

Edit `templates/report_template.md` to customize the report format. The template uses placeholder syntax that Copilot interprets when generating reports.

## Known Environments

| SUT Name | Description | K8s Context | K8s Namespace |
|----------|-------------|-------------|---------------|
| qa-advanced | DOG Soak Environment | qa-advanced | velocity-rzbirc1krb814pev-services |
| qa-dedicated | Solutions Soak Environment | qa-dedicated | velocity-8q6rrqvpilhwr3sc-services |
| qa-advanced | CAT Soak Environment | qa-advanced | velocity-nc7yvw8shwjniihe-services |

## Related

- `common/sut_config/` - SUTConfigManager for credential management
- `arcgis-velocity-mcp/` - Velocity API MCP server
