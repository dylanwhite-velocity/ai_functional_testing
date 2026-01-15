#!/usr/bin/env python3
"""
Deep dive into the 19 "Error in logs" pods - get actual error messages
"""

import subprocess
import re
import json

def get_pod_logs(namespace, pod_name, lines=300):
    """Get logs for a specific pod"""
    try:
        result = subprocess.run(
            ['kubectl', 'logs', '-n', namespace, pod_name, '--tail', str(lines)],
            capture_output=True,
            text=True,
            timeout=15
        )
        return result.stdout if result.returncode == 0 else ""
    except Exception as e:
        return ""

def get_pod_json(namespace, pod_name):
    """Get pod JSON for inspection"""
    try:
        result = subprocess.run(
            ['kubectl', 'get', 'pod', pod_name, '-n', namespace, '-o', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except:
        return None

def extract_meaningful_error(logs, pod_json=None):
    """Extract the ACTUAL error from logs"""
    
    # Check pod status first
    if pod_json:
        try:
            container_status = pod_json['status']['containerStatuses'][0]
            if 'lastState' in container_status and 'terminated' in container_status['lastState']:
                reason = container_status['lastState']['terminated'].get('reason', '')
                exit_code = container_status['lastState']['terminated'].get('exitCode', '')
                if reason and reason != 'Error':
                    return f"{reason} (exit code {exit_code})"
        except:
            pass
    
    # Look for specific VALIDATION errors first
    val_patterns = [
        (r'VALIDATION_ANALYTICS__FEED_ACCOUNT_RESOURCE_FILE_DOES_NOT_EXIST', 'Feed does not exist - feed was deleted'),
        (r'VALIDATION_ANALYTICS__NODES_MISSING_SCHEMAS', 'Missing schema configuration'),
        (r'VALIDATION_ANALYTICS__FEATURE_LAYER_NEW_OUTPUT_PORTAL_ITEM_ID_FAILED', 'Feature layer output failure - portal item issue'),
        (r'VALIDATION_ANALYTICS__(\w+)', lambda m: f'Validation error: {m.group(1).replace("_", " ").lower()}'),
    ]
    
    for pattern, msg in val_patterns:
        match = re.search(pattern, logs)
        if match:
            if callable(msg):
                return msg(match)
            return msg
    
    # Look for common Quarkus/Java startup failures
    if 'Failed to start application' in logs:
        # Extract the actual failure reason
        fail_match = re.search(r'Failed to start application[:\s]+([^\n]{0,200})', logs)
        if fail_match:
            return f"Startup failure: {fail_match.group(1).strip()}"
        return "Application failed to start"
    
    # Look for OOMKilled
    if 'OutOfMemoryError' in logs or 'OOMKilled' in logs:
        return "OutOfMemoryError - pod killed due to insufficient memory"
    
    # Liveness/readiness probe failures
    if 'Liveness probe failed' in logs or 'Readiness probe failed' in logs:
        return "Health check probe failures - pod not becoming ready"
    
    # Connection refused usually means MSK/Kafka or internal service
    if 'Connection refused' in logs:
        # Try to find what service
        service_match = re.search(r'Connection refused.*?(?:to|at)\s+([^\s:]+)', logs, re.IGNORECASE)
        if service_match:
            return f"Connection refused to {service_match.group(1)}"
        return "Connection refused - dependent service unavailable"
    
    # Timeout errors
    if 'TimeoutException' in logs or 'timed out' in logs.lower():
        return "Timeout connecting to dependent service"
    
    # Look for actual Java exceptions with meaningful messages
    exception_patterns = [
        r'Exception:\s*(.{10,150})',
        r'ERROR.*?:\s*(.{10,150})',
        r'FATAL.*?:\s*(.{10,150})',
        r'Caused by:\s*\w+Exception:\s*(.{10,150})',
    ]
    
    for pattern in exception_patterns:
        matches = re.findall(pattern, logs)
        if matches:
            # Get the first meaningful one
            for match in matches[:3]:
                cleaned = match.strip()
                if len(cleaned) > 20 and not cleaned.startswith('at '):
                    return cleaned[:150]
    
    # Check if pod is actually starting successfully but then crashing
    if 'Listening on:' in logs and 'started in' in logs:
        # Pod started successfully but crashed later - look for what killed it
        lines = logs.split('\n')
        started_idx = None
        for i, line in enumerate(lines):
            if 'started in' in line:
                started_idx = i
                break
        
        if started_idx and started_idx < len(lines) - 5:
            # Look at what happened after startup
            after_lines = lines[started_idx+1:]
            for line in after_lines:
                if 'ERROR' in line or 'FATAL' in line or 'Exception' in line:
                    return f"Post-startup crash: {line[:150]}"
            return "Started successfully but crashed - check liveness probes"
    
    # If we got here, look at raw log content
    log_lines = [l.strip() for l in logs.split('\n') if l.strip()]
    if len(log_lines) < 5:
        return "Pod produces minimal logs - likely crashing immediately on startup"
    
    # Last resort - return last few non-empty lines
    meaningful_lines = [l for l in log_lines if len(l) > 20 and not l.startswith('exec java')]
    if meaningful_lines:
        return f"Last log: {meaningful_lines[-1][:150]}"
    
    return "No clear error in logs - pod may be crash looping silently"

def main():
    namespace = "velocity-ksoqrenrugvqxizs-services"
    
    # Read the pods marked as "Error in logs"
    with open('crashloop_failure_reasons.txt', 'r') as f:
        lines = f.readlines()
    
    error_pods = []
    for line in lines:
        if "Error in logs (see details)" in line:
            pod_name = line.split(':')[0].strip()
            error_pods.append(pod_name)
    
    print(f"DETAILED ERROR ANALYSIS FOR 19 PODS")
    print(f"=" * 100)
    print()
    
    for i, pod_name in enumerate(error_pods, 1):
        print(f"[{i}/19] {pod_name}")
        logs = get_pod_logs(namespace, pod_name, lines=500)
        pod_json = get_pod_json(namespace, pod_name)
        error = extract_meaningful_error(logs, pod_json)
        print(f"     {error}")
        print()

if __name__ == "__main__":
    main()
