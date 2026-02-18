#!/usr/bin/env python3
"""Soak Monitoring Orchestrator.

Runs the complete soak monitoring workflow end-to-end:
  1. Fetch Velocity item logs (identifies items with errors)
  2. Fetch Kubernetes pod logs (for items with errors)
  3. Generate summary report via Azure OpenAI / OpenAI API

Usage:
    # Full workflow using environments config:
    python run_soak_monitor.py --config environments.yaml

    # Skip data collection, just regenerate report from existing JSON files:
    python run_soak_monitor.py --report-only \
        --velocity-errors logs/velocity_errors_*.json \
        --pod-logs logs/pod_logs_*.json \
        --config environments.yaml

    # Dry run (collect data but don't call OpenAI):
    python run_soak_monitor.py --config environments.yaml --dry-run
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Optional

# Ensure src/ is on the path for sibling imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Add parent paths for common package imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def step_1_fetch_velocity_logs(config_path: str, item_type: Optional[str] = None,
                                hours: Optional[int] = None) -> str:
    """Step 1: Fetch Velocity item logs and identify errors.

    Returns:
        Path to the velocity_errors JSON file.
    """
    print(f"\n{'#'*60}")
    print("# STEP 1: Fetch Velocity Item Logs")
    print(f"{'#'*60}")

    from get_velocity_item_logs import run_multi_environment

    output_file = asyncio.run(run_multi_environment(config_path, item_type, hours))
    return output_file


def step_2_fetch_pod_logs(errors_file: str, config_path: str,
                           hours: Optional[int] = None) -> Optional[str]:
    """Step 2: Fetch Kubernetes pod logs for items with errors.

    Skips if no items have errors.

    Returns:
        Path to the pod_logs JSON file, or None if skipped.
    """
    print(f"\n{'#'*60}")
    print("# STEP 2: Fetch Kubernetes Pod Logs")
    print(f"{'#'*60}")

    # Check if there are any errors to investigate
    with open(errors_file, "r") as f:
        errors_data = json.load(f)

    total_errors = errors_data.get("summary", {}).get("total_items_with_errors", 0)

    if total_errors == 0:
        print("\n  No items with errors found. Skipping pod log collection.")
        print("  All Velocity items are healthy!\n")
        return None

    print(f"\n  Found {total_errors} items with errors. Fetching pod logs...")

    from get_pod_logs_for_errors import run_multi_environment

    output_file = run_multi_environment(errors_file, config_path, hours)
    return output_file


def step_3_generate_report(velocity_errors_path: str, pod_logs_path: Optional[str],
                            config_path: str, output_path: Optional[str] = None,
                            dry_run: bool = False) -> Optional[str]:
    """Step 3: Generate summary report via OpenAI API.

    If pod_logs_path is None (no errors found), generates a healthy-environment report.

    Returns:
        Path to the generated report, or None if dry-run.
    """
    print(f"\n{'#'*60}")
    print("# STEP 3: Generate Report")
    print(f"{'#'*60}")

    from generate_report import generate_report
    from openai_config import load_openai_config

    config = load_openai_config(config_path)

    if pod_logs_path is None:
        # No errors — generate a simple healthy report
        print("\n  No pod logs to analyze (all items healthy).")
        print("  Generating healthy environment report...")

        # Create a minimal pod_logs structure so generate_report can still work
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(os.path.dirname(script_dir), "logs")
        os.makedirs(logs_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        empty_pod_logs_path = os.path.join(logs_dir, f"pod_logs_{timestamp}_empty.json")

        empty_pod_logs = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "items_processed": 0,
                "items_with_pods": 0,
                "total_pods_analyzed": 0,
                "total_pod_errors": 0,
            },
            "items": [],
        }
        with open(empty_pod_logs_path, "w") as f:
            json.dump(empty_pod_logs, f, indent=2)

        pod_logs_path = empty_pod_logs_path

    report_path = generate_report(
        velocity_errors_path=velocity_errors_path,
        pod_logs_path=pod_logs_path,
        config=config,
        output_path=output_path,
        dry_run=dry_run,
    )

    return report_path


def run_workflow(config_path: str, item_type: Optional[str] = None,
                 velocity_hours: Optional[int] = None,
                 pod_hours: Optional[int] = None,
                 output_path: Optional[str] = None,
                 dry_run: bool = False,
                 report_only: bool = False,
                 velocity_errors_path: Optional[str] = None,
                 pod_logs_path: Optional[str] = None) -> Optional[str]:
    """Run the full soak monitoring workflow.

    Args:
        config_path: Path to environments.yaml.
        item_type: Filter by item type (feeds, rats, bats). None = all.
        velocity_hours: Override hours for Velocity log fetch.
        pod_hours: Override hours for pod log fetch.
        output_path: Override report output path.
        dry_run: If True, skip OpenAI API call.
        report_only: If True, skip data collection and use existing files.
        velocity_errors_path: Existing velocity errors file (for --report-only).
        pod_logs_path: Existing pod logs file (for --report-only).

    Returns:
        Path to the generated report file.
    """
    start_time = datetime.now()

    print(f"\n{'='*60}")
    print("SOAK MONITORING WORKFLOW")
    print(f"{'='*60}")
    print(f"Config: {config_path}")
    print(f"Started: {start_time.isoformat()}")
    if report_only:
        print(f"Mode: Report-only (using existing data files)")
    else:
        print(f"Mode: Full workflow")
    if dry_run:
        print(f"Dry run: Yes (will not call OpenAI API)")
    print(f"{'='*60}")

    if report_only:
        # Report-only mode — use provided file paths
        if not velocity_errors_path:
            print("ERROR: --velocity-errors is required with --report-only")
            sys.exit(1)

        # Resolve glob patterns
        from generate_report import resolve_glob_pattern

        velocity_errors_path = resolve_glob_pattern(velocity_errors_path)
        if pod_logs_path:
            pod_logs_path = resolve_glob_pattern(pod_logs_path)

    else:
        # Full workflow — collect data
        # Step 1: Velocity logs
        velocity_errors_path = step_1_fetch_velocity_logs(
            config_path, item_type, velocity_hours
        )

        # Step 2: Pod logs
        pod_logs_path = step_2_fetch_pod_logs(
            velocity_errors_path, config_path, pod_hours
        )

    # Step 3: Generate report
    report_path = step_3_generate_report(
        velocity_errors_path, pod_logs_path, config_path,
        output_path=output_path, dry_run=dry_run
    )

    # Summary
    elapsed = datetime.now() - start_time
    print(f"\n{'='*60}")
    print("WORKFLOW COMPLETE")
    print(f"{'='*60}")
    print(f"Duration: {elapsed.total_seconds():.1f}s")
    print(f"Velocity errors: {velocity_errors_path}")
    print(f"Pod logs: {pod_logs_path or 'N/A (no errors)'}")
    if report_path:
        print(f"Report: {report_path}")
    else:
        print(f"Report: Skipped (dry run)")
    print(f"{'='*60}\n")

    return report_path


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run the complete soak monitoring workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full workflow:
  python run_soak_monitor.py --config environments.yaml

  # Just regenerate report from existing data:
  python run_soak_monitor.py --report-only \\
      --velocity-errors logs/velocity_errors_*.json \\
      --pod-logs logs/pod_logs_*.json \\
      --config environments.yaml

  # Dry run (collect data, print prompt, don't call API):
  python run_soak_monitor.py --config environments.yaml --dry-run
        """,
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to environments.yaml config file",
    )
    parser.add_argument(
        "--type",
        choices=["feeds", "rats", "bats"],
        help="Filter by item type (default: all)",
    )
    parser.add_argument(
        "--velocity-hours",
        type=int,
        help="Override hours for Velocity log fetch (default from config)",
    )
    parser.add_argument(
        "--pod-hours",
        type=int,
        help="Override hours for pod log fetch (default from config)",
    )
    parser.add_argument(
        "--output",
        help="Override report output file path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip OpenAI API call, print prompt instead",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Skip data collection, generate report from existing files",
    )
    parser.add_argument(
        "--velocity-errors",
        help="Existing velocity errors JSON (for --report-only, supports globs)",
    )
    parser.add_argument(
        "--pod-logs",
        help="Existing pod logs JSON (for --report-only, supports globs)",
    )

    args = parser.parse_args()

    # Validate
    if args.report_only and not args.velocity_errors:
        parser.error("--velocity-errors is required when using --report-only")

    report_path = run_workflow(
        config_path=args.config,
        item_type=args.type,
        velocity_hours=args.velocity_hours,
        pod_hours=args.pod_hours,
        output_path=args.output,
        dry_run=args.dry_run,
        report_only=args.report_only,
        velocity_errors_path=args.velocity_errors,
        pod_logs_path=args.pod_logs,
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
