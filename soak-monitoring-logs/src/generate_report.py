#!/usr/bin/env python3
"""Generate soak monitoring report using OpenAI API.

Reads the combined pod-logs JSON file (which includes Velocity error context
per item) and the report template, then sends a compact prompt to OpenAI to
generate a standardized markdown report.

The pod-logs file is the *sole* data source for the report.  Velocity API
errors are used upstream only to identify which items to investigate; the
compact error summaries are embedded in the pod-logs output so the report
still has context when no Kubernetes pods are found.

Usage:
    # Using environments config (reads openai settings from it):
    python generate_report.py \
        --pod-logs logs/pod_logs_*.json \
        --config environments.yaml

    # Dry run (print prompt without calling API):
    python generate_report.py \
        --pod-logs logs/pod_logs_*.json \
        --config environments.yaml \
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

# Maximum characters of combined data to include in the prompt.
# gpt-4o-mini has 128K context window (~400K chars).
# We target compact summaries; this limit is a safety cap.
MAX_DATA_CHARS = 60_000


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


def load_system_prompt(prompt_path: Optional[str] = None) -> str:
    """Load the system prompt from templates/system_prompt.md.

    The file uses a front-matter style format: everything above the first
    '---' separator is treated as comments, everything below is the prompt.
    If no separator is found, the entire file content is used.
    """
    if prompt_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(os.path.dirname(script_dir), "templates", "system_prompt.md")

    try:
        with open(prompt_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"  Warning: System prompt not found at {prompt_path}, using built-in default")
        return _DEFAULT_SYSTEM_PROMPT

    # Split on the first '---' separator — content after it is the prompt
    parts = content.split("---", 1)
    prompt = parts[1].strip() if len(parts) > 1 else content.strip()

    if not prompt:
        print("  Warning: System prompt file is empty, using built-in default")
        return _DEFAULT_SYSTEM_PROMPT

    return prompt


# Fallback in case the file is missing or empty
_DEFAULT_SYSTEM_PROMPT = """You are an expert Site Reliability Engineer analyzing ArcGIS Velocity soak environment health.
Your task is to generate a comprehensive monitoring report from structured log data.
Be precise and factual. Only reference errors/data present in the provided data.
The report should be ready to share with the engineering team without additional editing."""


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


def summarize_pod_logs(data: Dict[str, Any]) -> str:
    """Build a compact text summary of the combined pod log data for the LLM.

    The pod-logs file is the sole data source for the report.  Each item
    contains:
      - Kubernetes pod log data (primary diagnostic source)
      - Compact Velocity API error summaries (fallback context when no pods
        are found, or supplementary info when pods exist)

    Produces structured plain text that preserves all analytical value while
    drastically reducing token count vs. raw JSON.
    """
    lines: List[str] = []

    summary = data.get("summary", {})
    lines.append("=== Soak Monitoring Data ===")
    lines.append(f"Generated: {data.get('generated_at', 'N/A')}")
    lines.append(f"Hours back: {data.get('hours_back', '?')}")
    lines.append(f"Environments processed: {summary.get('environments_processed', '?')}")
    lines.append(f"Items processed: {summary.get('items_processed', 0)}")
    lines.append(f"Items with pods: {summary.get('items_with_pods', 0)}")
    lines.append(f"Total pods analyzed: {summary.get('total_pods_analyzed', 0)}")
    lines.append(f"Total pod errors: {summary.get('total_pod_errors', 0)}")
    lines.append("")

    for item in data.get("items", []):
        lines.append(f"--- Item: {item.get('item_name', '?')} ---")
        lines.append(f"  ID: {item.get('item_id', '?')}")
        lines.append(f"  Type: {item.get('item_type', '?')}")
        lines.append(f"  Status: {item.get('status', 'unknown')}")
        lines.append(f"  Environment: {item.get('environment', 'N/A')}")
        lines.append(f"  Velocity error count: {item.get('velocity_error_count', 0)}")
        lines.append(f"  Pods found: {item.get('pod_count', 0)}")

        # ── Pod log details (primary) ──
        for pod in item.get("pods", []):
            pod_status = pod.get("status", {})
            lines.append(f"  Pod: {pod.get('pod_name', '?')}")
            lines.append(f"    Phase: {pod_status.get('phase', '?')}")
            lines.append(f"    Restarts: {pod_status.get('restart_count', 0)}")
            lines.append(f"    Node: {pod_status.get('node', '?')}")
            if pod_status.get("issues"):
                lines.append(f"    Issues: {'; '.join(pod_status['issues'])}")
            lines.append(f"    Log lines: {pod.get('log_lines_total', 0)}")
            lines.append(f"    Error lines: {pod.get('error_lines_count', 0)}")

            error_lines = pod.get("error_lines", [])
            if error_lines:
                for el in error_lines[:20]:
                    el_str = str(el).strip()
                    if len(el_str) > 300:
                        el_str = el_str[:300] + "..."
                    lines.append(f"    > {el_str}")
                if len(error_lines) > 20:
                    lines.append(f"    > ...+{len(error_lines)-20} more error lines")

            events = pod.get("warning_events", [])
            if events:
                for ev in events[:10]:
                    lines.append(f"    EVENT: {ev.get('reason','?')} (x{ev.get('count',1)}): {ev.get('message','')[:200]}")

        # ── Velocity API error context (fallback / supplementary) ──
        velocity_errors = item.get("velocity_errors", [])
        if velocity_errors:
            pod_count = item.get("pod_count", 0)
            label = "Velocity API errors (primary — no pods found)" if pod_count == 0 else "Velocity API errors (supplementary)"
            lines.append(f"  {label}:")
            for e in velocity_errors:
                count = e.get("count", 1)
                key = e.get("key", "UNKNOWN")
                msg = e.get("englishMessage", "").strip()
                if len(msg) > 300:
                    msg = msg[:300] + "..."
                ts_info = ""
                if e.get("first_timestamp") and e.get("last_timestamp"):
                    ts_info = f" | first={e['first_timestamp']} last={e['last_timestamp']}"
                elif e.get("timestamp"):
                    ts_info = f" | at={e['timestamp']}"
                args_info = ""
                if e.get("unique_args"):
                    args_strs = [str(a) for a in e["unique_args"][:5]]
                    if len(e["unique_args"]) > 5:
                        args_strs.append(f"...+{len(e['unique_args'])-5} more")
                    args_info = f" | args_samples={args_strs}"
                elif e.get("args"):
                    args_info = f" | args={e['args']}"

                lines.append(f"    [{count}x] {key}{ts_info}{args_info}")
                lines.append(f"      Message: {msg}")

        lines.append("")

    return "\n".join(lines)


def build_prompt(
    pod_logs: Dict[str, Any],
    template: str,
) -> tuple[str, str]:
    """Build the system prompt and user prompt for OpenAI.

    The pod-logs data is the sole input.  It contains per-item pod log
    details (primary) and compact Velocity API error summaries (fallback
    when no pods are found).

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = load_system_prompt()

    # Build compact text summary
    data_summary = summarize_pod_logs(pod_logs)

    # Safety cap
    if len(data_summary) > MAX_DATA_CHARS:
        data_summary = data_summary[:MAX_DATA_CHARS] + "\n...[TRUNCATED]..."

    user_prompt = f"""Generate a Velocity Soak Monitoring Report from the following data.

## Report Template
{template}

## Monitoring Data
{data_summary}

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
    pod_logs_path: str,
    config: OpenAIConfig,
    template_path: Optional[str] = None,
    output_path: Optional[str] = None,
    dry_run: bool = False,
) -> str:
    """Full report generation pipeline.

    Args:
        pod_logs_path: Path to pod_logs JSON file (sole data source).
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
    pod_logs_path = resolve_glob_pattern(pod_logs_path)

    print(f"Pod logs: {pod_logs_path}")
    print(f"OpenAI config: {config.to_dict()}")
    print(f"{'='*60}\n")

    # Load data
    print("Loading data...")
    pod_logs = load_json_file(pod_logs_path)
    template = load_template(template_path)

    summary = pod_logs.get('summary', {})
    print(f"  Items processed: {summary.get('items_processed', '?')}")
    print(f"  Items with pods: {summary.get('items_with_pods', '?')}")
    print(f"  Total pod errors: {summary.get('total_pod_errors', '?')}")

    # Build prompt
    print("\nBuilding prompt...")
    system_prompt, user_prompt = build_prompt(pod_logs, template)
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
