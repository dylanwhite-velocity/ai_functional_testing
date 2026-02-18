#!/usr/bin/env python3
"""Kubernetes Pod Log Fetcher for Velocity Items with Errors.

Reads the output from get_velocity_item_logs.py and fetches corresponding
Kubernetes pod logs for items that have errors.

Usage:
    # Using environments config (recommended for multi-env):
    python get_pod_logs_for_errors.py <velocity_errors.json> --config environments.yaml

    # Single environment with explicit context/namespace:
    python get_pod_logs_for_errors.py <velocity_errors.json> --context <kube_context> --namespace <namespace>

    # Direct item IDs:
    python get_pod_logs_for_errors.py --item-ids abc123,def456 --context qa-advanced --namespace velocity-xxx-services

Arguments:
    errors_file    JSON file from get_velocity_item_logs.py
    --config       YAML config file (derives context/namespace automatically)
    --item-ids     Comma-separated list of item IDs to check (alternative to errors_file)
    --context      Kubernetes context (required without --config)
    --namespace    Velocity namespace (required without --config)
    --hours        Hours of logs to fetch (default: 6)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml

# Pod patterns by item type
POD_PATTERNS = {
    "feed": {
        "pattern": r"^feeds-{item_id}-[a-z0-9]+-[a-z0-9]+$",
        "prefix": "feeds-"
    },
    "realtime_analytic": {
        "pattern": r"^rats-{item_id}-[0-9]+$",
        "prefix": "rats-"
    },
    # BAT pods use flexible matching — see find_bat_pods()
    # Driver pattern:   cb{item_id[:15]}-{timestamp}-driver
    # Executor pattern: {char}{item_id[1:]}-{hash}-exec-{N}
    "bigdata_analytic": {
        "pattern": None,
        "prefix": None
    }
}

# Error patterns to highlight in pod logs
ERROR_PATTERNS = [
    r"\[ERROR\]",
    r"\[FATAL\]",
    r"Exception",
    r"Error:",
    r"FAILED",
    r"java\.lang\.\w*Exception",
    r"Traceback",
    r"OOMKilled",
    r"CrashLoopBackOff",
]


def run_kubectl(context: str, namespace: str, args: List[str]) -> str:
    """Run kubectl command and return output."""
    cmd = ["kubectl", "--context", context, "-n", namespace] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e.stderr}"


def get_all_pods(context: str, namespace: str) -> List[Dict]:
    """Get all pods in the namespace."""
    output = run_kubectl(context, namespace, ["get", "pods", "-o", "json"])
    
    if output.startswith("ERROR:"):
        print(f"  Warning: {output}")
        return []
    
    try:
        pods_data = json.loads(output)
        return pods_data.get("items", [])
    except json.JSONDecodeError:
        return []


def get_pod_creation_time(pod: Dict) -> str:
    """Get the creation timestamp of a pod for sorting."""
    return pod.get("metadata", {}).get("creationTimestamp", "")


def get_newest_pod(pods: List[Dict]) -> Optional[Dict]:
    """Return the newest pod by creation timestamp."""
    if not pods:
        return None
    return max(pods, key=lambda p: get_pod_creation_time(p))


def find_bat_pods(item_id: str, all_pods: List[Dict]) -> List[Dict]:
    """Find BAT (big data analytic) pods using flexible matching.
    
    BAT pods have two naming patterns:
      - Driver:   cb{item_id[:15]}-{timestamp}-driver
      - Executor: {char}{item_id[1:]}-{hash}-exec-{N}
    
    We use substring matching with the item ID and verify the pod
    has a BAT-related suffix (-driver or -exec-).
    """
    matching_pods = []
    
    # Build search keys — substrings of the item ID present in pod names
    search_keys = [
        item_id,            # full item ID (exact match, unlikely but covers edge cases)
        item_id[:15],       # truncated ID used in driver pods (cb{id[:15]}-...)
        item_id[1:],        # ID minus first char (executor pods swap first char)
    ]
    
    bat_suffixes = ("-driver", "-exec-")
    
    for pod in all_pods:
        pod_name = pod["metadata"]["name"]
        # Pod must have a BAT-related suffix
        if not any(suffix in pod_name for suffix in bat_suffixes):
            continue
        # Check if any search key substring appears in the pod name
        for key in search_keys:
            if key in pod_name:
                matching_pods.append(pod)
                break
    
    return matching_pods


def find_pods_for_item(item_id: str, item_type: str, all_pods: List[Dict]) -> List[Dict]:
    """Find pods matching an item ID and type."""
    # BATs use flexible substring matching
    if item_type == "bigdata_analytic":
        return find_bat_pods(item_id, all_pods)
    
    matching_pods = []
    
    pattern_config = POD_PATTERNS.get(item_type)
    if not pattern_config or not pattern_config.get("pattern"):
        for pod in all_pods:
            pod_name = pod["metadata"]["name"]
            if item_id in pod_name:
                matching_pods.append(pod)
        return matching_pods
    
    pattern = pattern_config["pattern"].replace("{item_id}", item_id)
    
    for pod in all_pods:
        pod_name = pod["metadata"]["name"]
        if re.match(pattern, pod_name):
            matching_pods.append(pod)
    
    return matching_pods


def get_pod_logs(context: str, namespace: str, pod_name: str, hours_back: int = 6) -> str:
    """Get logs from a pod for the last N hours."""
    output = run_kubectl(context, namespace, [
        "logs", pod_name,
        "--all-containers=true",
        f"--since={hours_back}h",
        "--timestamps"
    ])
    return output


def get_pod_events(context: str, namespace: str, pod_name: str) -> List[Dict]:
    """Get events related to a pod."""
    output = run_kubectl(context, namespace, [
        "get", "events",
        "--field-selector", f"involvedObject.name={pod_name}",
        "-o", "json"
    ])
    
    if output.startswith("ERROR:"):
        return []
    
    try:
        events_data = json.loads(output)
        return events_data.get("items", [])
    except json.JSONDecodeError:
        return []


def extract_error_lines(logs: str) -> List[str]:
    """Extract lines containing errors from logs."""
    error_lines = []
    for line in logs.split('\n'):
        for pattern in ERROR_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                error_lines.append(line.strip())
                break
    return error_lines


def get_pod_status_info(pod: Dict) -> Dict:
    """Extract status information from pod."""
    status = pod.get("status", {})
    metadata = pod.get("metadata", {})
    
    container_statuses = status.get("containerStatuses", [])
    restart_count = sum(c.get("restartCount", 0) for c in container_statuses)
    
    issues = []
    for cs in container_statuses:
        state = cs.get("state", {})
        if "waiting" in state:
            reason = state["waiting"].get("reason", "Unknown")
            issues.append(f"Container waiting: {reason}")
        if "terminated" in state:
            reason = state["terminated"].get("reason", "Unknown")
            exit_code = state["terminated"].get("exitCode", -1)
            issues.append(f"Container terminated: {reason} (exit code: {exit_code})")
    
    return {
        "phase": status.get("phase", "Unknown"),
        "restart_count": restart_count,
        "start_time": status.get("startTime"),
        "pod_ip": status.get("podIP"),
        "node": pod.get("spec", {}).get("nodeName", "Unknown"),
        "issues": issues
    }


def process_errors_file(errors_file: str) -> tuple[List[Dict], Dict]:
    """Load and parse errors file from get_velocity_item_logs.py."""
    with open(errors_file, "r") as f:
        data = json.load(f)
    
    return data.get("items_with_errors", []), {
        "sut_name": data.get("sut_name", "unknown"),
        "base_url": data.get("base_url", ""),
        "time_range": data.get("time_range", {})
    }


def process_item_ids(item_ids_str: str) -> List[Dict]:
    """Create item list from comma-separated IDs."""
    items = []
    for item_id in item_ids_str.split(","):
        item_id = item_id.strip()
        if item_id:
            items.append({
                "item_id": item_id,
                "item_name": f"Item {item_id}",
                "item_type": "unknown"
            })
    return items


def load_environments_config(config_path: str) -> tuple[List[Dict], Dict]:
    """Load environments and settings from YAML config file."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Extract settings
    settings = config.get("settings", {})
    
    environments = []
    for instance in config.get("instances", []):
        name = instance.get("name")
        org_id = instance.get("organizationId")
        
        if not name or not org_id:
            continue
        
        # Derive context and namespace from config
        # Context = instance name, Namespace = velocity-{orgId}-services
        environments.append({
            "name": name,
            "organization_id": org_id,
            "context": name,
            "namespace": f"velocity-{org_id}-services"
        })
    
    return environments, settings


def match_items_to_environment(items: List[Dict], env_org_id: str, errors_data: Dict) -> List[Dict]:
    """Filter items that belong to a specific environment based on org ID in URL."""
    # Check if the errors file has environment info
    environments = errors_data.get("environments", [])
    
    # Find the base_url for this org_id
    target_base_url = None
    for env in environments:
        if env.get("organization_id") == env_org_id:
            target_base_url = env.get("base_url")
            break
    
    if not target_base_url:
        # Single environment mode - return all items
        return items
    
    # Multi-environment mode - we need to track which items came from which env
    # Since items don't have env info directly, we use the environments list
    # and match by checking if this env had any items with errors
    env_info = next((e for e in environments if e.get("organization_id") == env_org_id), None)
    if env_info and env_info.get("items_with_errors", 0) > 0:
        # This environment has errors - but we need to identify which items
        # The org_id appears in the base_url, so check if item came from this env
        # For now, if single env - all items, if multi env - check URL contains org_id
        matching_items = []
        for item in items:
            # Items from velocity errors file should have raw_item or we match all 
            matching_items.append(item)
        return matching_items
    
    return items


def main(errors_file: Optional[str], item_ids: Optional[str], 
         context: str, namespace: str, hours_back: int,
         items_override: Optional[List[Dict]] = None) -> tuple[str, Dict]:
    """Main execution."""
    
    print(f"\n{'='*60}")
    print("KUBERNETES POD LOG FETCHER")
    print(f"{'='*60}")
    print(f"Cluster: {context}")
    print(f"Namespace: {namespace}")
    print(f"Log window: {hours_back} hours")
    print(f"{'='*60}\n")
    
    metadata = {}
    
    if items_override is not None:
        # Items provided directly (multi-env mode)
        items = items_override
        print(f"Processing {len(items)} items (from multi-env mode)...")
    elif errors_file:
        print(f"Loading errors from: {errors_file}")
        items, metadata = process_errors_file(errors_file)
        if metadata.get("sut_name"):
            print(f"SUT: {metadata['sut_name']}")
    elif item_ids:
        print(f"Processing item IDs: {item_ids}")
        items = process_item_ids(item_ids)
    else:
        print("ERROR: Provide either an errors file or --item-ids")
        sys.exit(1)
    
    if not items:
        print("No items to process.")
        # Return empty result instead of exit for multi-env mode
        return "", {
            "summary": {
                "items_processed": 0,
                "items_with_pods": 0,
                "total_pods_analyzed": 0,
                "total_pod_errors": 0
            },
            "items": []
        }
    
    print(f"Processing {len(items)} items...\n")
    
    print("Fetching pod list...")
    all_pods = get_all_pods(context, namespace)
    print(f"Found {len(all_pods)} total pods in namespace\n")
    
    results = []
    
    for item in items:
        item_id = item["item_id"]
        item_name = item["item_name"]
        item_type = item["item_type"]
        
        print(f"{'─'*60}")
        print(f"Item: {item_name}")
        print(f"ID: {item_id}")
        print(f"Type: {item_type}")
        
        matching_pods = find_pods_for_item(item_id, item_type, all_pods)
        
        if not matching_pods and item_type == "unknown":
            for check_type in POD_PATTERNS.keys():
                matching_pods = find_pods_for_item(item_id, check_type, all_pods)
                if matching_pods:
                    item_type = check_type
                    break
        
        if not matching_pods:
            print(f"  ⚠ No pods found for item")
            results.append({
                "item_id": item_id,
                "item_name": item_name,
                "item_type": item_type,
                "velocity_errors": item.get("errors", []),
                "velocity_error_count": item.get("error_count", 0),
                "pods": [],
                "pod_count": 0,
                "status": "no_pods_found"
            })
            continue
        
        # For BATs, only analyze the newest pod (latest Spark run)
        if item_type == "bigdata_analytic" and len(matching_pods) > 1:
            newest = get_newest_pod(matching_pods)
            print(f"  Found {len(matching_pods)} BAT pod(s), selecting newest only")
            matching_pods = [newest] if newest else matching_pods
        else:
            print(f"  Found {len(matching_pods)} pod(s)")
        
        pod_results = []
        
        for pod in matching_pods:
            pod_name = pod["metadata"]["name"]
            print(f"\n  Pod: {pod_name}")
            
            status_info = get_pod_status_info(pod)
            print(f"    Phase: {status_info['phase']}")
            print(f"    Restarts: {status_info['restart_count']}")
            
            if status_info["issues"]:
                print(f"    Issues: {', '.join(status_info['issues'])}")
            
            print(f"    Fetching logs...")
            logs = get_pod_logs(context, namespace, pod_name, hours_back)
            error_lines = extract_error_lines(logs)
            
            print(f"    Log lines: {len(logs.split(chr(10)))}")
            print(f"    Error lines: {len(error_lines)}")
            
            events = get_pod_events(context, namespace, pod_name)
            warning_events = [e for e in events if e.get("type") == "Warning"]
            
            if warning_events:
                print(f"    Warning events: {len(warning_events)}")
            
            pod_results.append({
                "pod_name": pod_name,
                "status": status_info,
                "log_lines_total": len(logs.split('\n')),
                "error_lines_count": len(error_lines),
                "error_lines": error_lines[:100],
                "full_logs": logs[-50000:] if len(logs) > 50000 else logs,
                "warning_events": [{
                    "reason": e.get("reason"),
                    "message": e.get("message"),
                    "count": e.get("count", 1),
                    "last_timestamp": e.get("lastTimestamp")
                } for e in warning_events]
            })
        
        results.append({
            "item_id": item_id,
            "item_name": item_name,
            "item_type": item_type,
            "velocity_errors": item.get("errors", [])[:20],
            "velocity_error_count": item.get("error_count", 0),
            "pods": pod_results,
            "pod_count": len(pod_results),
            "status": "analyzed"
        })
    
    # Output results
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(os.path.dirname(script_dir), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(logs_dir, f"pod_logs_{timestamp}.json")
    
    output = {
        "generated_at": datetime.now().isoformat(),
        "cluster": context,
        "namespace": namespace,
        "hours_back": hours_back,
        "source_file": errors_file,
        "sut_name": metadata.get("sut_name", "unknown"),
        "summary": {
            "items_processed": len(items),
            "items_with_pods": len([r for r in results if r["pod_count"] > 0]),
            "total_pods_analyzed": sum(r["pod_count"] for r in results),
            "total_pod_errors": sum(
                sum(p["error_lines_count"] for p in r["pods"]) 
                for r in results
            )
        },
        "items": results
    }
    
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Items processed: {output['summary']['items_processed']}")
    print(f"Items with pods: {output['summary']['items_with_pods']}")
    print(f"Total pods analyzed: {output['summary']['total_pods_analyzed']}")
    print(f"Total pod error lines: {output['summary']['total_pod_errors']}")
    
    high_error_items = [
        r for r in results 
        if sum(p["error_lines_count"] for p in r["pods"]) > 10
    ]
    
    if high_error_items:
        print(f"\nHigh-error items (>10 pod errors):")
        for item in high_error_items:
            pod_errors = sum(p["error_lines_count"] for p in item["pods"])
            print(f"  - {item['item_name']}: {item['velocity_error_count']} velocity + {pod_errors} pod errors")
    
    print(f"\nOutput written to: {output_file}")
    print(f"{'='*60}\n")
    
    return output_file, output


def run_multi_environment(errors_file: str, config_path: str, hours_back: Optional[int] = None) -> str:
    """Run pod log fetching for multiple environments from config."""
    environments, settings = load_environments_config(config_path)
    
    if not environments:
        print("ERROR: No valid environments found in config file")
        sys.exit(1)
    
    # Use hours from config if not provided via CLI
    if hours_back is None:
        hours_back = settings.get("pod_hours", 6)
    
    # Load the errors file to get items
    with open(errors_file, "r") as f:
        errors_data = json.load(f)
    
    all_items = errors_data.get("items_with_errors", [])
    env_list = errors_data.get("environments", [])
    
    print(f"\n{'='*60}")
    print("KUBERNETES MULTI-ENVIRONMENT POD LOG FETCHER")
    print(f"{'='*60}")
    print(f"Config: {config_path}")
    print(f"Errors file: {errors_file}")
    print(f"Environments in config: {len(environments)}")
    print(f"Total items with errors: {len(all_items)}")
    print(f"Log window: {hours_back} hours")
    print(f"{'='*60}\n")
    
    all_results = []
    
    for env in environments:
        context = env["context"]
        namespace = env["namespace"]
        org_id = env["organization_id"]
        
        # Filter items that belong to this environment by organization_id
        env_items = [item for item in all_items if item.get("organization_id") == org_id]
        
        if not env_items:
            print(f"\n{'─'*60}")
            print(f"Environment: {env['name']} - No items with errors, skipping")
            continue
        
        print(f"\n{'─'*60}")
        print(f"Environment: {env['name']}")
        print(f"Context: {context}")
        print(f"Namespace: {namespace}")
        print(f"Items with errors: {len(env_items)}")
        print(f"{'─'*60}")
        
        _, result = main(None, None, context, namespace, hours_back, items_override=env_items)
        result["environment"] = env["name"]
        result["organization_id"] = org_id
        all_results.append(result)
    
    # Write combined output
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(os.path.dirname(script_dir), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(logs_dir, f"pod_logs_{timestamp}.json")
    
    # Flatten results
    all_items_results = []
    for result in all_results:
        for item in result.get("items", []):
            item["environment"] = result.get("environment")
            all_items_results.append(item)
    
    output = {
        "generated_at": datetime.now().isoformat(),
        "config_file": config_path,
        "source_file": errors_file,
        "hours_back": hours_back,
        "environments_processed": [r.get("environment") for r in all_results],
        "summary": {
            "environments_processed": len(all_results),
            "items_processed": sum(r["summary"]["items_processed"] for r in all_results),
            "items_with_pods": sum(r["summary"]["items_with_pods"] for r in all_results),
            "total_pods_analyzed": sum(r["summary"]["total_pods_analyzed"] for r in all_results),
            "total_pod_errors": sum(r["summary"]["total_pod_errors"] for r in all_results)
        },
        "items": all_items_results
    }
    
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n{'='*60}")
    print("COMBINED SUMMARY")
    print(f"{'='*60}")
    print(f"Environments processed: {output['summary']['environments_processed']}")
    print(f"Items processed: {output['summary']['items_processed']}")
    print(f"Items with pods: {output['summary']['items_with_pods']}")
    print(f"Total pods analyzed: {output['summary']['total_pods_analyzed']}")
    print(f"Total pod error lines: {output['summary']['total_pod_errors']}")
    print(f"\nOutput written to: {output_file}")
    print(f"{'='*60}\n")
    
    return output_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch K8s pod logs for Velocity items with errors"
    )
    parser.add_argument(
        "errors_file", 
        nargs="?",
        help="JSON file from get_velocity_item_logs.py"
    )
    parser.add_argument(
        "--config",
        help="YAML config file (derives context/namespace from instance name and org ID)"
    )
    parser.add_argument(
        "--item-ids",
        help="Comma-separated list of item IDs to check"
    )
    parser.add_argument(
        "--context",
        help="Kubernetes context (required without --config)"
    )
    parser.add_argument(
        "--namespace",
        help="Kubernetes namespace (required without --config)"
    )
    parser.add_argument(
        "--hours", 
        type=int, 
        default=None,
        help="Hours of logs to fetch (default: from config or 6)"
    )
    
    args = parser.parse_args()
    
    if args.config:
        # Multi-environment mode using config file - hours from config if not specified
        if not args.errors_file:
            parser.error("errors_file is required with --config")
        run_multi_environment(args.errors_file, args.config, args.hours)
    elif args.context and args.namespace:
        # Single environment mode - use default if not specified
        hours = args.hours if args.hours is not None else 6
        if not args.errors_file and not args.item_ids:
            parser.error("Provide either an errors file or --item-ids")
        main(args.errors_file, args.item_ids, args.context, args.namespace, hours)
    else:
        parser.error("Either --config OR (--context and --namespace) are required")
