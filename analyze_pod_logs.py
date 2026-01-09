#!/usr/bin/env python3
"""
Kubernetes Pod Log Analyzer for Velocity
Analyzes logs from feeds, rats, and bats (spark driver) pods for errors in the last 12 hours.
"""

import subprocess
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict


# Configuration
KUBE_CONTEXT = "qa-advanced"  # Edit this to change the cluster context
#NAMESPACE = "velocity-rzbirc1krb814pev-services"  # Soak DOG
NAMESPACE = "velocity-nc7yvw8shwjniihe-services"  # Soak Cat
HOURS_BACK = 2  # Number of hours to look back

# Pod name patterns
POD_PATTERNS = {
    "feeds": r"^feeds-[a-f0-9]+-[a-z0-9]+-[a-z0-9]+$",
    "rats": r"^rats-[a-f0-9]+-[0-9]+$",
    "bats": r"^cb[a-f0-9]+-[0-9]+-driver$"  # BAT driver pods only
}

# Error patterns to search for in logs
ERROR_PATTERNS = [
    r"\[ERROR\]",
    r"\[FATAL\]",
    r"Exception",
    r"Error:",
    r"Failed",
    r"FAILED",
    r"java\.lang\.\w*Exception",
    r"Traceback \(most recent call last\)",
]


def run_kubectl(args: List[str]) -> str:
    """Run kubectl command and return output."""
    cmd = ["kubectl", "--context", KUBE_CONTEXT] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running kubectl: {e.stderr}")
        return ""


def get_pods_by_pattern() -> Dict[str, List[str]]:
    """Get all pods matching our patterns."""
    pods_by_type = defaultdict(list)
    
    # Get all pods in namespace
    output = run_kubectl(["-n", NAMESPACE, "get", "pods", "-o", "json"])
    if not output:
        return pods_by_type
    
    try:
        pods_data = json.loads(output)
        for pod in pods_data.get("items", []):
            pod_name = pod["metadata"]["name"]
            
            # Match against patterns
            for pod_type, pattern in POD_PATTERNS.items():
                if re.match(pattern, pod_name):
                    pods_by_type[pod_type].append(pod_name)
                    break
    except json.JSONDecodeError as e:
        print(f"Error parsing kubectl output: {e}")
    
    # For BATs, only keep the newest pod for each unique BAT ID
    if "bats" in pods_by_type:
        pods_by_type["bats"] = filter_latest_bat_pods(pods_by_type["bats"])
    
    return pods_by_type


def filter_latest_bat_pods(bat_pods: List[str]) -> List[str]:
    """
    Filter BAT pods to only keep the newest pod for each unique BAT.
    BAT pod names follow pattern: cb[bat_id]-[timestamp]-driver
    We group by BAT ID and keep only the pod with the highest timestamp.
    """
    bat_groups = defaultdict(list)
    
    for pod_name in bat_pods:
        # Extract BAT ID from pattern: cb[hash]-[timestamp]-driver
        match = re.match(r'^cb([a-f0-9]+)-(\d+)-driver$', pod_name)
        if match:
            bat_id = match.group(1)  # Just the hash without 'cb' prefix
            timestamp = int(match.group(2))
            bat_groups[bat_id].append((timestamp, pod_name))
    
    # Keep only the newest pod for each BAT
    latest_pods = []
    for bat_id, pods in bat_groups.items():
        # Sort by timestamp descending and take the first (newest)
        pods.sort(reverse=True)
        latest_pod = pods[0][1]  # Get pod name from (timestamp, pod_name) tuple
        latest_pods.append(latest_pod)
    
    return latest_pods


def extract_item_id(pod_name: str, pod_type: str) -> str:
    """
    Extract the item ID from a pod name based on pod type.
    """
    if pod_type == "feeds":
        # feeds-[item_id]-[random]-[random]
        match = re.match(r'^feeds-([a-f0-9]+)-', pod_name)
        if match:
            return match.group(1)
    elif pod_type == "rats":
        # rats-[item_id]-[timestamp]
        match = re.match(r'^rats-([a-f0-9]+)-', pod_name)
        if match:
            return match.group(1)
    elif pod_type == "bats":
        # cb[item_id]-[timestamp]-driver
        match = re.match(r'^cb([a-f0-9]+)-', pod_name)
        if match:
            return match.group(1)
    
    return "unknown"


def get_pod_logs(pod_name: str, hours: int = 12) -> str:
    """Get logs from a pod for the last N hours."""
    since = f"{hours}h"
    
    # Try to get logs with --since flag
    output = run_kubectl([
        "-n", NAMESPACE,
        "logs",
        pod_name,
        "--all-containers=true",
        f"--since={since}",
        "--timestamps"
    ])
    
    return output


def analyze_logs(logs: str, pod_name: str) -> Dict[str, Any]:
    """Analyze logs for errors and return findings."""
    findings = {
        "pod_name": pod_name,
        "total_lines": 0,
        "error_lines": [],
        "error_count": 0,
        "error_types": defaultdict(int)
    }
    
    if not logs:
        return findings
    
    lines = logs.split('\n')
    findings["total_lines"] = len(lines)
    
    for line in lines:
        for pattern in ERROR_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                findings["error_lines"].append(line.strip())
                findings["error_count"] += 1
                findings["error_types"][pattern] += 1
                break  # Only count each line once
    
    return findings


def print_summary(results: Dict[str, List[Dict[str, Any]]]):
    """Print analysis summary."""
    print("\n" + "=" * 80)
    print(f"POD LOG ANALYSIS SUMMARY")
    print(f"Cluster: {KUBE_CONTEXT}")
    print(f"Namespace: {NAMESPACE}")
    print(f"Time Range: Last {HOURS_BACK} hours")
    print("=" * 80 + "\n")
    
    total_errors = 0
    total_pods = 0
    
    for pod_type, findings_list in results.items():
        print(f"\n{'─' * 80}")
        print(f"{pod_type.upper()} PODS ({len(findings_list)} pods analyzed)")
        print('─' * 80)
        
        if not findings_list:
            print("  No pods found matching pattern")
            continue
        
        for findings in findings_list:
            total_pods += 1
            pod_name = findings["pod_name"]
            error_count = findings["error_count"]
            total_errors += error_count
            
            status = "✓ OK" if error_count == 0 else f"✗ {error_count} errors"
            print(f"\n  Pod: {pod_name}")
            print(f"  Status: {status}")
            print(f"  Total lines: {findings['total_lines']}")
            
            if error_count > 0:
                print(f"\n  Error breakdown:")
                for pattern, count in findings["error_types"].items():
                    print(f"    - {pattern}: {count}")
                
                # Show all error lines with full content
                print(f"\n  All errors ({len(findings['error_lines'])} total):")
                for i, error_line in enumerate(findings["error_lines"], 1):
                    print(f"    [{i}] {error_line}")
    
    print("\n" + "=" * 80)
    print(f"TOTAL SUMMARY")
    print(f"  Pods analyzed: {total_pods}")
    print(f"  Total errors found: {total_errors}")
    print("=" * 80 + "\n")


def main():
    """Main execution function."""
    print(f"\nConnecting to cluster '{KUBE_CONTEXT}'...")
    print(f"Analyzing namespace '{NAMESPACE}'...")
    print(f"Looking back {HOURS_BACK} hours...\n")
    
    # Get pods by type
    print("Discovering pods...")
    pods_by_type = get_pods_by_pattern()
    
    if not any(pods_by_type.values()):
        print("No matching pods found!")
        return
    
    for pod_type, pod_list in pods_by_type.items():
        print(f"  Found {len(pod_list)} {pod_type} pod(s)")
    
    # Analyze logs for each pod type
    results = {}
    
    for pod_type, pod_list in pods_by_type.items():
        print(f"\nAnalyzing {pod_type} pods...")
        findings_list = []
        
        for pod_name in pod_list:
            print(f"  Fetching logs from {pod_name}...")
            logs = get_pod_logs(pod_name, HOURS_BACK)
            findings = analyze_logs(logs, pod_name)
            findings_list.append(findings)
        
        results[pod_type] = findings_list
    
    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()
