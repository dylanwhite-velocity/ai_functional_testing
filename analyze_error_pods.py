#!/usr/bin/env python3
"""
Analyze the 19 pods marked as "Error in logs (see details)" and extract specific failure reasons
"""

import subprocess
import re

def get_pod_logs(namespace, pod_name, lines=200):
    """Get logs for a specific pod"""
    try:
        result = subprocess.run(
            ['kubectl', 'logs', '-n', namespace, pod_name, '--tail', str(lines)],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout if result.returncode == 0 else ""
    except Exception as e:
        return f"Error getting logs: {str(e)}"

def extract_detailed_error(logs):
    """Extract detailed error information from pod logs"""
    
    # Pattern 1: VALIDATION_ANALYTICS errors with details
    validation_match = re.search(r'VALIDATION_ANALYTICS__(\w+)', logs)
    if validation_match:
        error_type = validation_match.group(1)
        
        # Get more context around the error
        if "NODES_MISSING_SCHEMAS" in error_type:
            return "Missing schemas in analytic configuration"
        elif "FEATURE_LAYER" in error_type:
            return "Feature layer access or configuration failure"
        elif "PORTAL_ITEM" in error_type:
            return "Portal item access failure or item does not exist"
        elif "ACCOUNT_RESOURCE" in error_type:
            return "Account resource access failure"
        else:
            return f"Validation error: {error_type}"
    
    # Pattern 2: NullPointerException
    if "NullPointerException" in logs or "null pointer" in logs.lower():
        # Try to find context
        npe_match = re.search(r'at com\.esri\..*?\.(\w+)\.\w+\(', logs)
        if npe_match:
            return f"NullPointerException in {npe_match.group(1)}"
        return "NullPointerException - null value encountered"
    
    # Pattern 3: Connection errors
    if "Connection refused" in logs:
        return "Connection refused - service unavailable"
    if "ConnectException" in logs:
        return "Connection exception - cannot connect to required service"
    if "SocketTimeoutException" in logs:
        return "Socket timeout - service not responding"
    
    # Pattern 4: Authentication/Authorization errors
    if "Unauthorized" in logs or "401" in logs:
        return "Unauthorized - authentication failure"
    if "Forbidden" in logs or "403" in logs:
        return "Forbidden - insufficient permissions"
    
    # Pattern 5: Missing configuration
    if "configuration" in logs.lower() and "missing" in logs.lower():
        return "Missing configuration parameter"
    if "required" in logs.lower() and ("null" in logs.lower() or "empty" in logs.lower()):
        return "Required parameter is null or empty"
    
    # Pattern 6: Schema/parsing errors
    if "JsonParseException" in logs or "JSON" in logs and "parse" in logs.lower():
        return "JSON parsing error - invalid data format"
    if "SchemaException" in logs:
        return "Schema validation failure"
    
    # Pattern 7: Kafka/MSK errors
    if "kafka" in logs.lower() and ("timeout" in logs.lower() or "unavailable" in logs.lower()):
        return "Kafka connection timeout or unavailable"
    
    # Pattern 8: Database errors
    if "SQLException" in logs or "database" in logs.lower() and "error" in logs.lower():
        return "Database connection or query error"
    
    # Pattern 9: Look for ERROR or FATAL lines
    error_lines = [line for line in logs.split('\n') if 'ERROR' in line or 'FATAL' in line]
    if error_lines:
        # Get first error line and extract key info
        first_error = error_lines[0]
        # Try to extract meaningful part
        if len(first_error) > 100:
            return f"Error: {first_error[first_error.find('ERROR')+6:first_error.find('ERROR')+100]}..."
        return f"Error: {first_error[:100]}"
    
    # Pattern 10: Exception class names
    exception_match = re.search(r'(\w+Exception):', logs)
    if exception_match:
        return f"Exception: {exception_match.group(1)}"
    
    return "Unknown error - requires manual log review"

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
    
    print(f"Found {len(error_pods)} pods marked as 'Error in logs (see details)'")
    print("\nAnalyzing detailed errors...\n")
    print("=" * 80)
    
    for i, pod_name in enumerate(error_pods, 1):
        print(f"[{i}/{len(error_pods)}] Analyzing {pod_name}...")
        logs = get_pod_logs(namespace, pod_name)
        error_detail = extract_detailed_error(logs)
        print(f"{pod_name}: {error_detail}")
    
    print("=" * 80)
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
