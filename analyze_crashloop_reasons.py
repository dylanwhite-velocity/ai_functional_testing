#!/usr/bin/env python3
"""
Analyze crashlooping pods and extract failure reasons
"""
import subprocess
import json
import re

def get_crashloop_pods(namespace):
    """Get list of pods in CrashLoopBackOff"""
    result = subprocess.run(
        ['kubectl', 'get', 'pods', '-n', namespace, '-o', 'json'],
        capture_output=True, text=True
    )
    
    data = json.loads(result.stdout)
    crashloop_pods = []
    
    for pod in data['items']:
        if not pod.get('status', {}).get('containerStatuses'):
            continue
        
        for cs in pod['status']['containerStatuses']:
            if cs.get('state', {}).get('waiting', {}).get('reason') == 'CrashLoopBackOff':
                crashloop_pods.append(pod['metadata']['name'])
                break
    
    return crashloop_pods

def get_pod_logs(namespace, pod_name, lines=100):
    """Get recent logs from a pod"""
    result = subprocess.run(
        ['kubectl', 'logs', '-n', namespace, pod_name, '--tail', str(lines)],
        capture_output=True, text=True, timeout=10
    )
    return result.stdout

def extract_failure_reason(logs):
    """Extract concise failure reason from logs"""
    
    # Common error patterns to look for
    patterns = {
        'VALIDATION_ANALYTICS__FEED_ACCOUNT_RESOURCE_FILE_DOES_NOT_EXIST': 'Feed does not exist or inaccessible',
        'VALIDATION_ANALYTICS__FEATURE_LAYER_NEW_OUTPUT_PORTAL_ITEM_ID_FAILED': 'Feature layer output not accessible',
        'VALIDATION_ANALYTICS__NODES_MISSING_SCHEMAS': 'Nodes missing schemas',
        'VALIDATION_ANALYTICS__TOOL_TARGET_FEATURE_SCHEMA_UNKNOWN': 'Target feature schema unknown',
        'NullPointerException': 'Null pointer exception',
        'BAT not found': 'BAT not found',
        'Connection refused': 'Connection refused',
        'Unable to connect to Kafka': 'Kafka connection failed',
        'Failed to authenticate': 'Authentication failed',
        'OOMKilled': 'Out of memory',
        'CrashLoopBackOff': 'Container crash loop',
        'ImagePullBackOff': 'Image pull failed',
        'Error: ECONNREFUSED': 'Connection refused (network)',
        'Prometheus': 'Prometheus authentication/connection error'
    }
    
    # Search for patterns
    for pattern, description in patterns.items():
        if pattern in logs:
            return description
    
    # Look for ERROR lines
    error_lines = [line for line in logs.split('\n') if 'ERROR' in line.upper()]
    if error_lines:
        # Get first error and try to extract key info
        first_error = error_lines[0]
        if 'VALIDATION_' in first_error:
            return 'Validation error'
        elif 'Item does not exist' in first_error:
            return 'Item/resource deleted'
        elif 'does not have access' in first_error:
            return 'Access denied to resource'
        return 'Error in logs (see details)'
    
    # Check for specific startup failures
    if 'failed to start' in logs.lower():
        return 'Container failed to start'
    if 'panic:' in logs.lower():
        return 'Application panic'
    
    return 'Unknown - check logs'

def analyze_crashloop_pods(namespace):
    """Analyze all crashloop pods and extract reasons"""
    
    print(f"Getting crashloop pods in {namespace}...", flush=True)
    pods = get_crashloop_pods(namespace)
    print(f"Found {len(pods)} crashlooping pods", flush=True)
    
    results = []
    
    for i, pod in enumerate(pods, 1):
        print(f"Analyzing {i}/{len(pods)}: {pod}...", flush=True)
        try:
            logs = get_pod_logs(namespace, pod, lines=200)
            reason = extract_failure_reason(logs)
            results.append((pod, reason))
        except subprocess.TimeoutExpired:
            results.append((pod, 'Timeout getting logs'))
        except Exception as e:
            results.append((pod, f'Error: {str(e)[:50]}'))
    
    return results

if __name__ == "__main__":
    namespace = 'velocity-ksoqrenrugvqxizs-services'
    
    results = analyze_crashloop_pods(namespace)
    
    # Print results
    print("\n" + "="*100)
    print("CRASHLOOP BACKOFF FAILURE REASONS")
    print("="*100)
    
    with open('/Users/dyl13740/ai_functional_testing/crashloop_failure_reasons.txt', 'w') as f:
        f.write("="*100 + "\n")
        f.write(f"CRASHLOOP BACKOFF FAILURE REASONS - {namespace}\n")
        f.write(f"Generated: 2026-01-15\n")
        f.write(f"Total Pods: {len(results)}\n")
        f.write("="*100 + "\n\n")
        
        for pod, reason in results:
            line = f"{pod}: {reason}"
            print(line)
            f.write(line + "\n")
    
    print("\n" + "="*100)
    print(f"Results saved to: /Users/dyl13740/ai_functional_testing/crashloop_failure_reasons.txt")
    print("="*100)
