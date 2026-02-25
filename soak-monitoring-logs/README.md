# Soak Monitoring Logs

Automated daily health monitoring for ArcGIS Velocity soak environments. The pipeline fetches Velocity item logs, correlates them with Kubernetes pod logs, and generates an AI-powered summary report via Azure OpenAI — delivered as a GitHub Actions artifact and an optional Microsoft Teams notification.

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. Fetch        │     │  2. Fetch K8s   │     │  3. Generate    │
│  Velocity Logs   │────▶│  Pod Logs       │────▶│  AI Report      │
│  (API errors)    │     │  (for errors)   │     │  (Azure OpenAI) │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                                              ┌───────────┴───────────┐
                                              │                       │
                                        ┌─────▼─────┐         ┌──────▼──────┐
                                        │  GitHub    │         │  Teams      │
                                        │  Artifact  │         │  Card       │
                                        └───────────┘         └─────────────┘
```

1. **Fetch Velocity Logs** — Queries the Velocity API for each configured environment/user and identifies items (feeds, RATs, BATs) with errors.
2. **Fetch Pod Logs** — For items with errors, fetches Kubernetes pod logs from the corresponding EKS cluster to provide deeper diagnostic context.
3. **Generate Report** — Sends the combined data to Azure OpenAI with a system prompt and report template, producing a structured Markdown report with stoplight ratings (GREEN/YELLOW/RED), severity classifications, and actionable recommendations. A Teams adaptive card is also generated.

## Project Structure

```
soak-monitoring-logs/
├── src/
│   ├── get_velocity_item_logs.py   # Step 1: Fetch Velocity API error logs
│   ├── get_pod_logs_for_errors.py  # Step 2: Fetch K8s pod logs for erroring items
│   ├── generate_report.py          # Step 3: Generate AI report via OpenAI
│   ├── run_soak_monitor.py         # Orchestrator: runs all 3 steps end-to-end
│   └── openai_config.py            # OpenAI/Azure OpenAI configuration loader
├── templates/
│   ├── report_template.md          # Report structure template (editable)
│   ├── system_prompt.md            # LLM system prompt (editable)
│   └── teams_card_template.json    # Teams adaptive card template
├── environments.yaml               # Target environments + OpenAI settings
├── severity_overrides.yaml         # Override LLM severity for known patterns
├── logs/                           # Output directory (gitignored)
├── Dockerfile                      # Multi-stage Docker image
└── README.md
```

## GitHub Actions Workflow

The pipeline runs automatically via `.github/workflows/soak-monitoring.yml` with two jobs:

| Job | Purpose | Triggers |
|-----|---------|----------|
| **soak-monitor** | Collect logs + generate report + upload artifact | schedule, push, workflow_dispatch |
| **notify-teams** | Download report artifact + post Teams card | schedule, workflow_dispatch only (**skipped on push**) |

### Triggers

| Trigger | Behavior |
|---------|----------|
| **Scheduled** (weekdays 1 PM UTC / 8 AM EST) | Full pipeline with default lookback from config |
| **Push** (changes to `soak-monitoring-logs/**`) | Smoke-test run with **1-hour lookback** to reduce time/tokens; Teams notification skipped |
| **Manual** (`workflow_dispatch`) | Full pipeline with optional overrides: `velocity_hours`, `pod_hours`, `item_type`, `dry_run` |

### Required Secrets

| Secret | Purpose |
|--------|---------|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | AWS Secrets Manager access (Velocity creds + OpenAI API key) |
| `AWS_EKS_ACCESS_KEY_ID` / `AWS_EKS_SECRET_ACCESS_KEY` | EKS cluster access for pod logs |
| `TEAMS_WEBHOOK_URL` | _(Optional)_ Microsoft Teams incoming webhook for notifications |

## Prerequisites

- Python 3.11+
- kubectl configured with EKS cluster contexts
- AWS credentials with access to Secrets Manager and EKS
- Azure OpenAI API key (stored in AWS Secrets Manager)

## Installation

From the repository root:
```bash
pip install -e ".[soak-monitoring]"
```

## Usage

### Option 1: GitHub Actions (Recommended)

The workflow runs daily on schedule. For ad-hoc runs, trigger manually via **Actions → Soak Monitoring → Run workflow** with optional overrides.

### Option 2: Local Orchestrator

Run the full pipeline locally with a single command:
```bash
cd soak-monitoring-logs

# Full workflow
python src/run_soak_monitor.py --config environments.yaml

# Dry run (skip OpenAI API call)
python src/run_soak_monitor.py --config environments.yaml --dry-run

# Report-only mode (regenerate from existing JSON files)
python src/run_soak_monitor.py --report-only \
    --velocity-errors logs/velocity_errors_*.json \
    --pod-logs logs/pod_logs_*.json \
    --config environments.yaml
```

### Option 3: Individual Scripts

**Multi-Environment Mode (using config file):**
```bash
cd soak-monitoring-logs

# Step 1: Fetch Velocity item logs
python src/get_velocity_item_logs.py --config environments.yaml

# Step 2: Fetch pod logs for items with errors
python src/get_pod_logs_for_errors.py logs/velocity_errors_*.json --config environments.yaml

# Step 3: Generate AI report
python src/generate_report.py --pod-logs logs/pod_logs_*.json --config environments.yaml
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

## Configuration

### environments.yaml

Central configuration for target environments, lookback windows, and OpenAI settings:

```yaml
settings:
  velocity_hours: 24    # Hours to look back for Velocity API logs
  pod_hours: 24         # Hours to look back for K8s pod logs

openai:
  provider: azure
  secret_name: RASP/openai/dylan      # AWS Secrets Manager secret
  secret_key_field: AZUREOPENAI_API_KEY
  model: gpt-5
  max_tokens: 16384
  azure_endpoint: "https://..."
  azure_api_version: "2024-10-21"
  azure_deployment: gpt-5

instances:
  - name: qa-advanced
    cluster_name: qaus1-advanced
    organizationId: rzbirc1krb814pev
    usernames:
      - neo_admin_soak_dog
    nickname: "Soak Dog"
```

### severity_overrides.yaml

Override the LLM's default severity classification for known error patterns. The LLM checks these **before** applying its own judgment:

```yaml
overrides:
  - pattern: "504"
    severity: LOW
    note: "Gateway timeouts are transient and self-resolve"
```

Severity levels: `CRITICAL`, `HIGH`, `LOW`.

### Templates

| File | Purpose |
|------|---------|
| `templates/report_template.md` | Report structure with `{{variable}}` placeholders |
| `templates/system_prompt.md` | LLM system prompt defining analysis behavior |
| `templates/teams_card_template.json` | Teams adaptive card with `{{variable}}` placeholders |

All templates are editable to customize report output without changing code.


## Output Files

All output goes to the `logs/` directory (gitignored):

| File | Contents |
|------|----------|
| `velocity_errors_<timestamp>.json` | Velocity API error logs per item |
| `pod_logs_<timestamp>.json` | Kubernetes pod logs with error context |
| `report_<timestamp>.md` | AI-generated Markdown report |
| `report_<timestamp>_teams_card.json` | Teams adaptive card JSON |

## SUTConfig Integration

This project uses `common.sut_config.SUTConfigManager` to load Velocity API credentials from AWS Secrets Manager. The SUT config provides:

- `apiUrl` — Velocity API base URL
- `auth.username` / `auth.password` — Credentials
- `auth.url` — Portal URL for token generation
- `distribution` — VelocitySaaS, VelocityEnterprise, or GeoEvent

Kubernetes context and namespace are derived from `environments.yaml`:
- Context = instance `name`
- Namespace = `velocity-{organizationId}-services`

## Related

- `common/sut_config/` — SUTConfigManager for credential management
- `arcgis-velocity-mcp/` — Velocity API MCP server
- `.github/workflows/soak-monitoring.yml` — GitHub Actions workflow
