#!/usr/bin/env python3
"""Generate soak monitoring report using OpenAI API.

Reads Velocity error logs and pod logs JSON files, combines them with the
report template, and sends to OpenAI to generate a standardized markdown report.

Usage:
    # Using environments config (reads openai settings from it):
    python generate_report.py \
        --velocity-errors logs/velocity_errors_*.json \
        --pod-logs logs/pod_logs_*.json \
        --config environments.yaml

    # With explicit options:
    python generate_report.py \
        --velocity-errors logs/velocity_errors_20260218.json \
        --pod-logs logs/pod_logs_20260218.json \
        --model gpt-4o \
        --output logs/report_20260218.md

    # Dry run (print prompt without calling API):
    python generate_report.py \
        --velocity-errors logs/velocity_errors_*.json \
        --pod-logs logs/pod_logs_*.json \
        --dry-run
"""

import argparse
import glob
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add parent paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from openai_config import OpenAIConfig, load_openai_config

# Maximum characters of JSON data to include in the prompt.
# gpt-4o-mini has 128K context window (~400K chars).
# We cap at 200K chars to leave room for system prompt + response.
MAX_DATA_CHARS = 200_000


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load and return a JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def load_template(template_path: Optional[str] = None) -> str:
    """Load the report template markdown."""
    if template_path is None:
        # Default to templates/report_template.md relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(os.path.dirname(script_dir), "templates", "report_template.md")

    try:
        with open(template_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"  Warning: Template not found at {template_path}, using built-in format")
        return ""


def resolve_glob_pattern(pattern: str) -> str:
    """Resolve a glob pattern to the most recent matching file.

    If the pattern contains wildcards, find all matches and return the newest
    (by filename, which includes timestamps).
    """
    if "*" in pattern or "?" in pattern:
        matches = sorted(glob.glob(pattern))
        if not matches:
            raise FileNotFoundError(f"No files matching pattern: {pattern}")
        # Return the last (newest by timestamp in filename)
        return matches[-1]
    return pattern


def truncate_data(data: Dict[str, Any], max_chars: int) -> str:
    """Serialize JSON data, truncating if necessary.

    Truncation strategy:
    1. Try full JSON first
    2. If too large, truncate pod full_logs (biggest offender)
    3. If still too large, limit error samples per item
    """
    # First pass: truncate full_logs in pod data
    data_copy = json.loads(json.dumps(data, default=str))

    # Truncate full_logs if present (these are the largest fields)
    if "items" in data_copy:
        for item in data_copy["items"]:
            for pod in item.get("pods", []):
                full_logs = pod.get("full_logs", "")
                if len(full_logs) > 5000:
                    pod["full_logs"] = full_logs[:2500] + "\n...[truncated]...\n" + full_logs[-2500:]

    serialized = json.dumps(data_copy, indent=2, default=str)

    if len(serialized) <= max_chars:
        return serialized

    # Second pass: further reduce error samples
    for item in data_copy.get("items", data_copy.get("items_with_errors", [])):
        errors = item.get("errors", item.get("velocity_errors", []))
        if len(errors) > 5:
            if "errors" in item:
                item["errors"] = errors[:5]
                item["errors_truncated"] = True
            elif "velocity_errors" in item:
                item["velocity_errors"] = errors[:5]
                item["velocity_errors_truncated"] = True

        for pod in item.get("pods", []):
            error_lines = pod.get("error_lines", [])
            if len(error_lines) > 20:
                pod["error_lines"] = error_lines[:20]
                pod["error_lines_truncated"] = True
            pod.pop("full_logs", None)  # Remove full logs entirely

    serialized = json.dumps(data_copy, indent=2, default=str)

    if len(serialized) > max_chars:
        print(f"  Warning: Data still {len(serialized)} chars after truncation (limit: {max_chars})")
        serialized = serialized[:max_chars] + "\n...[DATA TRUNCATED]..."

    return serialized


def build_prompt(
    velocity_errors: Dict[str, Any],
    pod_logs: Dict[str, Any],
    template: str,
) -> tuple[str, str]:
    """Build the system prompt and user prompt for OpenAI.

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = """You are an expert Site Reliability Engineer analyzing ArcGIS Velocity soak environment health.
Your task is to generate a comprehensive monitoring report from structured log data.

Guidelines:
- Be precise and factual. Only reference errors/data present in the provided JSON.
- Categorize severity: CRITICAL (crash loops, OOM, service down), HIGH (persistent errors affecting functionality), LOW (warnings, intermittent issues that self-resolve).
- For each item with errors, provide: root cause analysis, error summary, and actionable recommendations.
- Include healthy items as a summary table — do not analyze them individually.
- Prioritize recommendations from most to least urgent.
- Use the report template structure provided, filling in all sections.
- Use markdown formatting with emoji severity indicators: :red_circle: CRITICAL, :orange_circle: HIGH, :yellow_circle: LOW.
- Keep the executive summary to 2-3 sentences.

The report should be ready to share with the engineering team without additional editing."""

    # Build the data section, respecting size limits
    half_budget = MAX_DATA_CHARS // 2
    velocity_json = truncate_data(velocity_errors, half_budget)
    pod_json = truncate_data(pod_logs, half_budget)

    user_prompt = f"""Generate a Velocity Soak Monitoring Report from the following data.

## Report Template
{template}

## Velocity API Error Logs
```json
{velocity_json}
```

## Kubernetes Pod Logs
```json
{pod_json}
```

Generate the complete markdown report following the template structure. Include all items with errors, healthy items summary, and prioritized recommendations."""

    return system_prompt, user_prompt


def call_openai(
    system_prompt: str,
    user_prompt: str,
    config: OpenAIConfig,
) -> str:
    """Call OpenAI API to generate the report.

    Args:
        system_prompt: System instructions for the model.
        user_prompt: User message with data and template.
        config: OpenAI configuration.

    Returns:
        Generated markdown report string.
    """
    try:
        from openai import AzureOpenAI, OpenAI
    except ImportError:
        raise RuntimeError(
            "openai package not installed. Install with: pip install openai"
        )

    if config.is_azure:
        client = AzureOpenAI(
            api_key=config.api_key,
            azure_endpoint=config.azure_endpoint,
            api_version=config.azure_api_version,
        )
        # Azure uses deployment name, not model name
        model_param = config.azure_deployment
        print(f"  Calling Azure OpenAI API...")
        print(f"    Endpoint: {config.azure_endpoint}")
        print(f"    Deployment: {config.azure_deployment}")
    else:
        client = OpenAI(api_key=config.api_key)
        model_param = config.model
        print(f"  Calling OpenAI API...")

    print(f"    Model: {config.model}")
    print(f"    Temperature: {config.temperature}")
    print(f"    Max tokens: {config.max_tokens}")
    print(f"    Prompt size: ~{len(system_prompt) + len(user_prompt):,} chars")

    # Build request kwargs — some models don't support temperature or max_completion_tokens
    request_kwargs = {
        "model": model_param,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if config.temperature is not None:
        request_kwargs["temperature"] = config.temperature
    if config.max_tokens:
        request_kwargs["max_completion_tokens"] = config.max_tokens

    response = client.chat.completions.create(**request_kwargs)

    # Extract response
    choice = response.choices[0]
    report = choice.message.content or ""

    # Check for truncation or refusal
    if choice.finish_reason == "length":
        print(f"    WARNING: Response was truncated (hit max_completion_tokens limit)")
        print(f"    Consider increasing max_tokens in environments.yaml")
    elif choice.finish_reason == "content_filter":
        print(f"    WARNING: Response was filtered by content policy")
    if hasattr(choice.message, "refusal") and choice.message.refusal:
        print(f"    WARNING: Model refused the request: {choice.message.refusal}")

    # Log usage
    usage = response.usage
    if usage:
        print(f"    Tokens used: {usage.prompt_tokens:,} prompt + {usage.completion_tokens:,} completion = {usage.total_tokens:,} total")
    print(f"    Finish reason: {choice.finish_reason}")
    print(f"    Response length: {len(report):,} chars")

    return report


def generate_report(
    velocity_errors_path: str,
    pod_logs_path: str,
    config: OpenAIConfig,
    template_path: Optional[str] = None,
    output_path: Optional[str] = None,
    dry_run: bool = False,
) -> str:
    """Full report generation pipeline.

    Args:
        velocity_errors_path: Path to velocity_errors JSON file.
        pod_logs_path: Path to pod_logs JSON file.
        config: OpenAI configuration.
        template_path: Optional path to report template.
        output_path: Optional output file path. Auto-generated if None.
        dry_run: If True, print prompt but don't call API.

    Returns:
        Path to the generated report file.
    """
    print(f"\n{'='*60}")
    print("REPORT GENERATOR")
    print(f"{'='*60}")

    # Resolve glob patterns
    velocity_errors_path = resolve_glob_pattern(velocity_errors_path)
    pod_logs_path = resolve_glob_pattern(pod_logs_path)

    print(f"Velocity errors: {velocity_errors_path}")
    print(f"Pod logs: {pod_logs_path}")
    print(f"OpenAI config: {config.to_dict()}")
    print(f"{'='*60}\n")

    # Load data
    print("Loading data files...")
    velocity_errors = load_json_file(velocity_errors_path)
    pod_logs = load_json_file(pod_logs_path)
    template = load_template(template_path)

    print(f"  Velocity errors: {velocity_errors.get('summary', {}).get('total_items_with_errors', '?')} items, "
          f"{velocity_errors.get('summary', {}).get('total_error_count', '?')} errors")
    print(f"  Pod logs: {pod_logs.get('summary', {}).get('items_processed', '?')} items, "
          f"{pod_logs.get('summary', {}).get('total_pod_errors', '?')} pod errors")

    # Build prompt
    print("\nBuilding prompt...")
    system_prompt, user_prompt = build_prompt(velocity_errors, pod_logs, template)
    print(f"  System prompt: {len(system_prompt):,} chars")
    print(f"  User prompt: {len(user_prompt):,} chars")

    if dry_run:
        print(f"\n{'='*60}")
        print("DRY RUN — Prompt content:")
        print(f"{'='*60}")
        print("\n--- SYSTEM PROMPT ---")
        print(system_prompt)
        print("\n--- USER PROMPT ---")
        print(user_prompt[:2000])
        if len(user_prompt) > 2000:
            print(f"\n... [{len(user_prompt) - 2000:,} more chars] ...")
        print(f"\n{'='*60}")
        return ""

    # Call OpenAI
    print("\nGenerating report...")
    report = call_openai(system_prompt, user_prompt, config)

    # Determine output path
    if output_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(os.path.dirname(script_dir), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(logs_dir, f"report_{timestamp}.md")

    # Write report
    with open(output_path, "w") as f:
        f.write(report)

    print(f"\n{'='*60}")
    print(f"Report written to: {output_path}")
    print(f"Report length: {len(report):,} chars")
    print(f"{'='*60}\n")

    return output_path


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate soak monitoring report using OpenAI API"
    )
    parser.add_argument(
        "--velocity-errors",
        required=True,
        help="Path to velocity_errors JSON file (supports glob patterns)",
    )
    parser.add_argument(
        "--pod-logs",
        required=True,
        help="Path to pod_logs JSON file (supports glob patterns)",
    )
    parser.add_argument(
        "--config",
        help="Path to environments.yaml (for OpenAI settings)",
    )
    parser.add_argument(
        "--template",
        help="Path to report template (default: templates/report_template.md)",
    )
    parser.add_argument(
        "--output",
        help="Output file path (default: logs/report_<timestamp>.md)",
    )
    parser.add_argument(
        "--model",
        help=f"Override OpenAI model (default from config or {OpenAIConfig.model})",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        help=f"Override temperature (default from config or {OpenAIConfig.temperature})",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        help=f"Override max tokens (default from config or {OpenAIConfig.max_tokens})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompt without calling OpenAI API",
    )

    args = parser.parse_args()

    # Load OpenAI config
    config = load_openai_config(args.config)

    # Apply CLI overrides
    if args.model:
        config.model = args.model
    if args.temperature is not None:
        config.temperature = args.temperature
    if args.max_tokens is not None:
        config.max_tokens = args.max_tokens

    # Generate report
    output_path = generate_report(
        velocity_errors_path=args.velocity_errors,
        pod_logs_path=args.pod_logs,
        config=config,
        template_path=args.template,
        output_path=args.output,
        dry_run=args.dry_run,
    )

    if output_path:
        print(f"Done. Report: {output_path}")


if __name__ == "__main__":
    main()
