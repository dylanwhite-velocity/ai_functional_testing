---
mode: agent
tools: ['run_in_terminal', 'read_file', 'create_file']
description: Run soak monitoring workflow and generate error report
---

# Soak Monitoring Workflow

Analyze Velocity items and Kubernetes pods for errors, then generate a standardized report.

## Configuration

Use the environments config file at `soak-monitoring-logs/environments.yaml` to define target environments and settings.
- Comment out instances you want to skip
- Adjust `velocity_hours` and `pod_hours` in the settings section as needed

## Workflow Steps

### Step 1: Fetch Velocity Item Logs

Run the Velocity log fetcher using the environments config:

```bash
cd /Users/dyl13740/ai_functional_testing/soak-monitoring-logs
/Users/dyl13740/ai_functional_testing/.venv/bin/python src/get_velocity_item_logs.py --config environments.yaml
```

This outputs to: `logs/velocity_errors_<timestamp>.json`

### Step 2: Fetch Pod Logs (if errors found)

If Velocity errors were found, fetch corresponding Kubernetes pod logs using the same config:

```bash
/Users/dyl13740/ai_functional_testing/.venv/bin/python src/get_pod_logs_for_errors.py \
    logs/velocity_errors_<timestamp>.json \
    --config environments.yaml
```

This outputs to: `logs/pod_logs_<timestamp>.json`

### Step 3: Generate Report

Read both JSON files and generate a markdown report using the template at:
`templates/report_template.md`

Save the report to: `logs/report_<timestamp>.md`

## Report Requirements

The generated report should include:

1. **Executive Summary** - 2-3 sentences summarizing environment health
2. **Health Status Table** - Counts of items, errors by category
3. **Items Requiring Attention** - For each item with errors:
   - Item details (ID, name, type, pod)
   - Error counts and sample error messages
   - Root cause analysis if determinable
   - Recommended action
4. **Healthy Items Summary** - Brief note on items without errors
5. **Recommendations** - Prioritized list of actions

## Output

After completing the workflow, provide:
1. The full markdown report 
2. A brief verbal summary highlighting critical issues
