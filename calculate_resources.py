#!/usr/bin/env python3
"""
Calculate resource allocation for Velocity tenants
"""
import subprocess
import json
import sys

def parse_cpu(cpu_str):
    """Convert CPU string to millicores"""
    if not cpu_str or cpu_str == "0":
        return 0
    if cpu_str.endswith('m'):
        return int(cpu_str[:-1])
    return int(float(cpu_str) * 1000)

def parse_memory(mem_str):
    """Convert memory string to MiB"""
    if not mem_str or mem_str == "0":
        return 0
    if mem_str.endswith('Gi'):
        return int(float(mem_str[:-2]) * 1024)
    elif mem_str.endswith('Mi'):
        return int(float(mem_str[:-2]))
    elif mem_str.endswith('Ki'):
        return int(float(mem_str[:-2]) / 1024)
    return int(float(mem_str) / (1024*1024))

def analyze_tenant(namespace):
    """Analyze resource allocation for a tenant"""
    
    # Get all pods
    result = subprocess.run(
        ['kubectl', 'get', 'pods', '-n', namespace, '-o', 'json'],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        print(f"Error getting pods for {namespace}: {result.stderr}")
        return None
    
    data = json.loads(result.stdout)
    
    # Calculate totals
    total_cpu_req = 0
    total_mem_req = 0
    total_cpu_lim = 0
    total_mem_lim = 0
    
    crashloop_cpu_req = 0
    crashloop_mem_req = 0
    crashloop_cpu_lim = 0
    crashloop_mem_lim = 0
    
    total_pods = 0
    crashloop_count = 0
    
    for pod in data['items']:
        if not pod.get('status', {}).get('containerStatuses'):
            continue
        
        total_pods += 1
        
        # Check if crashlooping
        is_crashloop = False
        for cs in pod['status']['containerStatuses']:
            if cs.get('state', {}).get('waiting', {}).get('reason') == 'CrashLoopBackOff':
                is_crashloop = True
                crashloop_count += 1
                break
        
        for container in pod['spec']['containers']:
            resources = container.get('resources', {})
            requests = resources.get('requests', {})
            limits = resources.get('limits', {})
            
            cpu_req = parse_cpu(requests.get('cpu', '0'))
            mem_req = parse_memory(requests.get('memory', '0'))
            cpu_lim = parse_cpu(limits.get('cpu', '0'))
            mem_lim = parse_memory(limits.get('memory', '0'))
            
            total_cpu_req += cpu_req
            total_mem_req += mem_req
            total_cpu_lim += cpu_lim
            total_mem_lim += mem_lim
            
            if is_crashloop:
                crashloop_cpu_req += cpu_req
                crashloop_mem_req += mem_req
                crashloop_cpu_lim += cpu_lim
                crashloop_mem_lim += mem_lim
    
    return {
        'namespace': namespace,
        'total_pods': total_pods,
        'crashloop_pods': crashloop_count,
        'total_cpu_req': total_cpu_req,
        'total_mem_req': total_mem_req,
        'total_cpu_lim': total_cpu_lim,
        'total_mem_lim': total_mem_lim,
        'crashloop_cpu_req': crashloop_cpu_req,
        'crashloop_mem_req': crashloop_mem_req,
        'crashloop_cpu_lim': crashloop_cpu_lim,
        'crashloop_mem_lim': crashloop_mem_lim
    }

def print_report(stats):
    """Print formatted report"""
    if not stats:
        return
    
    print("=" * 80)
    print(f"TENANT: {stats['namespace']}")
    print("=" * 80)
    
    print("\nTOTAL TENANT RESOURCES (All {} Pods)".format(stats['total_pods']))
    print("-" * 80)
    print(f"CPU Requests:    {stats['total_cpu_req']:,} millicores ({stats['total_cpu_req']/1000:.1f} cores)")
    print(f"Memory Requests: {stats['total_mem_req']:,} MiB ({stats['total_mem_req']/1024:.1f} GiB)")
    print(f"CPU Limits:      {stats['total_cpu_lim']:,} millicores ({stats['total_cpu_lim']/1000:.1f} cores)")
    print(f"Memory Limits:   {stats['total_mem_lim']:,} MiB ({stats['total_mem_lim']/1024:.1f} GiB)")
    
    print("\nCRASHLOOPING PODS RESOURCES ONLY ({} pods)".format(stats['crashloop_pods']))
    print("-" * 80)
    print(f"CPU Requests:    {stats['crashloop_cpu_req']:,} millicores ({stats['crashloop_cpu_req']/1000:.1f} cores)")
    print(f"Memory Requests: {stats['crashloop_mem_req']:,} MiB ({stats['crashloop_mem_req']/1024:.1f} GiB)")
    print(f"CPU Limits:      {stats['crashloop_cpu_lim']:,} millicores ({stats['crashloop_cpu_lim']/1000:.1f} cores)")
    print(f"Memory Limits:   {stats['crashloop_mem_lim']:,} MiB ({stats['crashloop_mem_lim']/1024:.1f} GiB)")
    
    if stats['crashloop_pods'] > 0:
        print("\nWASTED RESOURCES (Percentage)")
        print("-" * 80)
        cpu_waste_pct = (stats['crashloop_cpu_req'] / stats['total_cpu_req'] * 100) if stats['total_cpu_req'] > 0 else 0
        mem_waste_pct = (stats['crashloop_mem_req'] / stats['total_mem_req'] * 100) if stats['total_mem_req'] > 0 else 0
        pod_waste_pct = (stats['crashloop_pods'] / stats['total_pods'] * 100) if stats['total_pods'] > 0 else 0
        
        print(f"CPU Waste:       {cpu_waste_pct:.1f}% of total tenant CPU requests")
        print(f"Memory Waste:    {mem_waste_pct:.1f}% of total tenant memory requests")
        print(f"Pods Wasted:     {pod_waste_pct:.1f}% of total tenant pods")
        
        # Cost estimates (AWS EKS pricing approximations)
        # CPU: ~$0.04 per vCPU-hour
        # Memory: ~$0.005 per GB-hour
        cpu_cost_hourly = (stats['crashloop_cpu_req'] / 1000) * 0.04
        mem_cost_hourly = (stats['crashloop_mem_req'] / 1024) * 0.005
        total_cost_hourly = cpu_cost_hourly + mem_cost_hourly
        
        print("\nESTIMATED WASTE COST (AWS Pricing)")
        print("-" * 80)
        print(f"CPU Cost:        ${cpu_cost_hourly:.2f}/hour  (${cpu_cost_hourly * 24:.2f}/day)  (${cpu_cost_hourly * 24 * 365:.2f}/year)")
        print(f"Memory Cost:     ${mem_cost_hourly:.2f}/hour  (${mem_cost_hourly * 24:.2f}/day)  (${mem_cost_hourly * 24 * 365:.2f}/year)")
        print(f"Total Cost:      ${total_cost_hourly:.2f}/hour  (${total_cost_hourly * 24:.2f}/day)  (${total_cost_hourly * 24 * 365:.2f}/year)")
    
    print("\n")

if __name__ == "__main__":
    tenants = [
        'velocity-ksoqrenrugvqxizs-services',
        'velocity-idjqgiutf8vkwplv-services'
    ]
    
    for tenant in tenants:
        stats = analyze_tenant(tenant)
        if stats:
            print_report(stats)
