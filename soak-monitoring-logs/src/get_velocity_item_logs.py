#!/usr/bin/env python3
"""
Velocity Item Log Fetcher

Fetches logs from the Velocity API for all items (feeds, RATs, BATs) and 
identifies errors. Outputs a JSON file with items that have errors.

Usage:
    # Single environment:
    python get_velocity_item_logs.py --sut <sut_name> --username <user> --org-id <org> [--hours 24]
    
    # Multiple environments from config:
    python get_velocity_item_logs.py --config environments.yaml [--hours 24]

Arguments:
    --sut          SUT Config name to load credentials from (e.g., "qa-advanced")
    --org-id       Org ID for SUTConfig
    --username     Username for SUTConfig  
    --config       YAML config file with multiple environments
    --type         Filter by item type: feeds, rats, bats (default: all)
    --hours        Hours to look back (default: 24)
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import httpx
import yaml

# Add parent paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Defaults
HOURS_BACK = 24
LOG_LEVEL = "WARN"
LOG_PAGE_SIZE = 500


class VelocityLogClient:
    """Simple client for fetching Velocity logs."""
    
    def __init__(self, base_url: str, username: str, password: str, portal_url: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.portal_url = portal_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=60.0)
        self._token: Optional[str] = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.client.aclose()
    
    async def _get_token(self) -> str:
        """Generate authentication token."""
        if self._token:
            return self._token
        
        token_url = f"{self.portal_url}/sharing/rest/generateToken"
        data = {
            "username": self.username,
            "password": self.password,
            "referer": self.base_url,
            "f": "json",
            "expiration": 60
        }
        
        response = await self.client.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        
        if "token" not in token_data:
            raise Exception(f"Token generation failed: {token_data}")
        
        self._token = token_data["token"]
        return self._token
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated API request."""
        token = await self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        response = await self.client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        
        if not response.content:
            return {"success": True}
        return response.json()
    
    async def get_feeds(self) -> List[Dict]:
        """Get all feeds."""
        return await self._request("GET", "/iot/feed")
    
    async def get_realtime_analytics(self) -> List[Dict]:
        """Get all real-time analytics."""
        return await self._request("GET", "/iot/analytics/realtime")
    
    async def get_bigdata_analytics(self) -> List[Dict]:
        """Get all big data analytics."""
        return await self._request("GET", "/iot/analytics/bigdata")
    
    async def get_item_logs(self, item_id: str, start_time: int, end_time: int, 
                            level: str = None, page_size: int = LOG_PAGE_SIZE) -> Dict:
        """Get logs for a specific item.
        
        Args:
            item_id: The Velocity item ID.
            start_time: Start time in epoch milliseconds.
            end_time: End time in epoch milliseconds.
            level: Minimum log level (e.g. 'WARN'). With includeHigherLevels=True,
                   'WARN' returns both WARN and ERROR entries.
            page_size: Number of log entries to return (default: LOG_PAGE_SIZE).
        """
        query_params = {
            "startTime": start_time,
            "startTimeEquals": True,
            "endTime": end_time,
            "endTimeEquals": True,
            "sortOrder": "desc",
            "from": 0,
            "size": page_size,
        }
        if level:
            query_params["level"] = level
            query_params["includeHigherLevels"] = True
            query_params["levelQueryOption"] = "term"
        
        return await self._request("POST", f"/iot/logs/{item_id}", json=query_params)


def get_credentials_from_sut(sut_name: str, org_id: Optional[str] = None, 
                              username: Optional[str] = None) -> Dict[str, str]:
    """Load credentials from SUTConfigManager."""
    try:
        from common.sut_config.sut_config_manager import SUTConfigManager
        
        manager = SUTConfigManager()
        manager.set_active_context(sut_name, org_id=org_id, username=username)
        
        config = manager.get_config()
        auth = manager.get_auth()
        
        # get_api_url() appends org ID to the base URL
        api_url = manager.get_api_url()
        
        # Determine portal URL based on distribution or auth.url
        if auth.url:
            portal_url = auth.url.rstrip('/')
        elif config.distribution == "VelocitySaaS":
            portal_url = "https://www.arcgis.com"
        else:
            # For Enterprise, try to derive from apiUrl
            portal_url = config.apiUrl.rsplit('/iot', 1)[0] if '/iot' in config.apiUrl else config.apiUrl
        
        return {
            "base_url": api_url,
            "username": auth.username,
            "password": auth.password,
            "portal_url": portal_url,
            "sut_name": config.name,
            "distribution": config.distribution
        }
    except ImportError:
        print("ERROR: SUTConfigManager not available. Ensure common package is in PYTHONPATH.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load SUT config '{sut_name}': {e}")
        sys.exit(1)


def parse_log_entries(logs_response: Dict) -> List[Dict]:
    """Extract log entries from API response."""
    if isinstance(logs_response, list):
        return logs_response
    return logs_response.get("logs", logs_response.get("items", []))


def filter_error_logs(logs: List[Dict], levels: List[str] = None) -> List[Dict]:
    """Filter logs for error-level entries.
    
    This is a client-side safety net. The API should already filter by level
    when 'level' + 'includeHigherLevels' are set in the request body.
    """
    if not levels:
        levels = ["ERROR", "WARN"]
    
    error_logs = []
    for log in logs:
        level = log.get("level", log.get("severity", "")).upper()
        if level in levels:
            error_logs.append(log)
    return error_logs


# Fields that are redundant (already on parent or always empty/constant)
_STRIP_FIELDS = {"fullLog", "itemId", "orgId", "componentType", "componentName",
                 "componentLabel", "userId", "timestampEpoch"}


def compact_errors(errors: List[Dict]) -> List[Dict]:
    """Compact error list by deduplicating, stripping, and grouping.

    Optimizations applied:
    1. Deduplicate user/admin access pairs (same error logged twice)
    2. Drop fullLog (stringified duplicate of parsed fields)
    3. Strip redundant per-error fields (itemId, orgId, etc.)
    4. Group errors by key — collapse identical error types into one
       entry with a count and list of unique args/trackIds.
    """
    if not errors:
        return errors

    # Step 1: Deduplicate user/admin pairs.
    # Build a signature from (key, timestamp_second, englishMessage) and keep
    # only the first occurrence.
    seen_sigs = set()
    deduped = []
    for e in errors:
        sig = (
            e.get("key", ""),
            e.get("timestamp", "")[:19],  # second-level precision
            e.get("englishMessage", ""),
        )
        if sig in seen_sigs:
            continue
        seen_sigs.add(sig)
        deduped.append(e)

    # Step 2 & 3: Strip redundant fields.
    cleaned = []
    for e in deduped:
        clean = {k: v for k, v in e.items()
                 if k not in _STRIP_FIELDS and v not in ("", None, [], {})}
        cleaned.append(clean)

    # Step 4: Group by error key.
    from collections import OrderedDict
    groups: OrderedDict[str, Dict] = OrderedDict()
    for e in cleaned:
        key = e.get("key", "UNKNOWN")
        if key not in groups:
            groups[key] = {
                "key": key,
                "level": e.get("level", "error"),
                "className": e.get("className", ""),
                "englishMessage": e.get("englishMessage", ""),
                "count": 0,
                "unique_args": [],
                "first_timestamp": e.get("timestamp"),
                "last_timestamp": e.get("timestamp"),
            }
        g = groups[key]
        g["count"] += 1
        g["last_timestamp"] = e.get("timestamp", g["last_timestamp"])
        # Collect unique args (e.g. different trackIds)
        args = e.get("args")
        if args and args not in g["unique_args"]:
            # Keep at most 10 unique arg sets per group
            if len(g["unique_args"]) < 10:
                g["unique_args"].append(args)

    # Clean up: drop className if empty, drop unique_args if only one
    result = []
    for g in groups.values():
        if not g.get("className"):
            g.pop("className", None)
        if len(g["unique_args"]) <= 1:
            # Inline the single args value
            if g["unique_args"]:
                g["args"] = g["unique_args"][0]
            g.pop("unique_args")
        if g["first_timestamp"] == g["last_timestamp"]:
            g["timestamp"] = g.pop("first_timestamp")
            g.pop("last_timestamp")
        result.append(g)

    return result


async def fetch_item_logs(client: VelocityLogClient, items: List[Dict], 
                          item_type: str, start_time: int, end_time: int,
                          environment_info: Optional[Dict] = None) -> List[Dict]:
    """Fetch logs for a list of items and return those with errors."""
    items_with_errors = []
    
    for item in items:
        item_id = item.get("id", item.get("itemId", ""))
        item_name = item.get("label", item.get("name", item.get("title", "Unknown")))
        
        if not item_id:
            continue
        
        print(f"  Checking {item_type}: {item_name} ({item_id})...")
        
        try:
            logs_response = await client.get_item_logs(item_id, start_time, end_time, LOG_LEVEL)
            logs = parse_log_entries(logs_response)
            error_logs = filter_error_logs(logs)
            
            if error_logs:
                compacted = compact_errors(error_logs[:50])
                item_data = {
                    "item_id": item_id,
                    "item_name": item_name,
                    "item_type": item_type,
                    "status": item.get("status", item.get("state", "unknown")),
                    "error_count": len(error_logs),
                    "unique_error_count": sum(e.get("count", 1) for e in compacted),
                    "errors": compacted,
                }
                # Tag with environment info for multi-env mode
                if environment_info:
                    item_data["environment"] = environment_info.get("sut_name")
                    item_data["organization_id"] = environment_info.get("organization_id")
                
                items_with_errors.append(item_data)
                print(f"    ✗ Found {len(error_logs)} errors")
            else:
                print(f"    ✓ No errors")
                
        except Exception as e:
            print(f"    ! Error fetching logs: {e}")
    
    return items_with_errors


async def main(credentials: Dict[str, str], item_type: Optional[str], hours_back: int,
               environment_info: Optional[Dict] = None) -> Optional[str]:
    """Main execution."""
    
    # Calculate time range
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(hours=hours_back)).timestamp() * 1000)
    
    print(f"\n{'='*60}")
    print("VELOCITY ITEM LOG FETCHER")
    print(f"{'='*60}")
    print(f"SUT: {credentials['sut_name']}")
    print(f"Base URL: {credentials['base_url']}")
    print(f"Distribution: {credentials['distribution']}")
    print(f"Time Range: Last {hours_back} hours")
    print(f"Log Level: {LOG_LEVEL} (includeHigherLevels=True)")
    print(f"Item Types: {item_type or 'all'}")
    print(f"{'='*60}\n")
    
    all_errors = []
    
    async with VelocityLogClient(
        credentials['base_url'], 
        credentials['username'], 
        credentials['password'], 
        credentials['portal_url']
    ) as client:
        
        if item_type is None or item_type == "feeds":
            print("Fetching feeds...")
            try:
                feeds = await client.get_feeds()
                if isinstance(feeds, dict):
                    feeds = feeds.get("items", feeds.get("feeds", []))
                print(f"  Found {len(feeds)} feeds")
                errors = await fetch_item_logs(client, feeds, "feed", start_time, end_time, environment_info)
                all_errors.extend(errors)
            except Exception as e:
                print(f"  Error fetching feeds: {e}")
        
        if item_type is None or item_type == "rats":
            print("\nFetching real-time analytics (RATs)...")
            try:
                rats = await client.get_realtime_analytics()
                if isinstance(rats, dict):
                    rats = rats.get("items", rats.get("analytics", []))
                print(f"  Found {len(rats)} RATs")
                errors = await fetch_item_logs(client, rats, "realtime_analytic", start_time, end_time, environment_info)
                all_errors.extend(errors)
            except Exception as e:
                print(f"  Error fetching RATs: {e}")
        
        if item_type is None or item_type == "bats":
            print("\nFetching big data analytics (BATs)...")
            try:
                bats = await client.get_bigdata_analytics()
                if isinstance(bats, dict):
                    bats = bats.get("items", bats.get("analytics", []))
                print(f"  Found {len(bats)} BATs")
                errors = await fetch_item_logs(client, bats, "bigdata_analytic", start_time, end_time, environment_info)
                all_errors.extend(errors)
            except Exception as e:
                print(f"  Error fetching BATs: {e}")
    
    return all_errors, credentials


def write_output(all_results: List[Dict], output_suffix: str = "") -> Optional[str]:
    """Write results to JSON file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(os.path.dirname(script_dir), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{output_suffix}" if output_suffix else ""
    output_file = os.path.join(logs_dir, f"velocity_errors_{timestamp}{suffix}.json")
    
    # Flatten all errors from all environments
    all_errors = []
    environments = []
    for result in all_results:
        all_errors.extend(result["items_with_errors"])
        environments.append({
            "sut_name": result["sut_name"],
            "username": result["username"],
            "organization_id": result["organization_id"],
            "base_url": result["base_url"],
            "items_with_errors": len(result["items_with_errors"]),
            "total_errors": sum(e["error_count"] for e in result["items_with_errors"])
        })
    
    output = {
        "generated_at": datetime.now().isoformat(),
        "environments": environments,
        "time_range": all_results[0]["time_range"] if all_results else {},
        "summary": {
            "total_environments": len(environments),
            "total_items_with_errors": len(all_errors),
            "total_error_count": sum(e["error_count"] for e in all_errors),
            "by_type": {}
        },
        "items_with_errors": all_errors
    }
    
    for item in all_errors:
        item_type_name = item["item_type"]
        if item_type_name not in output["summary"]["by_type"]:
            output["summary"]["by_type"][item_type_name] = {"count": 0, "errors": 0}
        output["summary"]["by_type"][item_type_name]["count"] += 1
        output["summary"]["by_type"][item_type_name]["errors"] += item["error_count"]
    
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    return output_file, output


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
        usernames = instance.get("usernames", [])
        
        if not name or not org_id or not usernames:
            continue
        
        for username in usernames:
            environments.append({
                "sut_name": name,
                "organization_id": org_id,
                "username": username
            })
    
    return environments, settings


async def run_single_environment(sut_name: str, org_id: str, username: str, 
                                  item_type: Optional[str], hours_back: int) -> Dict:
    """Run log fetch for a single environment."""
    credentials = get_credentials_from_sut(sut_name, org_id, username)
    
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(hours=hours_back)).timestamp() * 1000)
    
    # Pass environment info so items get tagged with org_id
    environment_info = {
        "sut_name": sut_name,
        "organization_id": org_id
    }
    
    errors, creds = await main(credentials, item_type, hours_back, environment_info)
    
    return {
        "sut_name": sut_name,
        "username": username,
        "organization_id": org_id,
        "base_url": creds["base_url"],
        "distribution": creds["distribution"],
        "time_range": {
            "start": datetime.fromtimestamp(start_time/1000).isoformat(),
            "end": datetime.fromtimestamp(end_time/1000).isoformat(),
            "hours_back": hours_back
        },
        "items_with_errors": errors
    }


async def run_multi_environment(config_path: str, item_type: Optional[str], hours_back: Optional[int] = None):
    """Run log fetch for multiple environments from config."""
    environments, settings = load_environments_config(config_path)
    
    if not environments:
        print("ERROR: No valid environments found in config file")
        sys.exit(1)
    
    # Use hours from config if not provided via CLI
    if hours_back is None:
        hours_back = settings.get("velocity_hours", 24)
    
    print(f"\n{'='*60}")
    print("VELOCITY MULTI-ENVIRONMENT LOG FETCHER")
    print(f"{'='*60}")
    print(f"Config: {config_path}")
    print(f"Environments: {len(environments)}")
    print(f"Time Range: Last {hours_back} hours")
    print(f"{'='*60}\n")
    
    all_results = []
    
    for env in environments:
        print(f"\n{'─'*60}")
        print(f"Environment: {env['sut_name']} / {env['username']}")
        print(f"{'─'*60}")
        
        try:
            result = await run_single_environment(
                env["sut_name"], 
                env["organization_id"], 
                env["username"],
                item_type, 
                hours_back
            )
            all_results.append(result)
        except Exception as e:
            print(f"ERROR: Failed to process {env['sut_name']}: {e}")
    
    if not all_results:
        print("ERROR: No environments processed successfully")
        sys.exit(1)
    
    output_file, output = write_output(all_results)
    
    print(f"\n{'='*60}")
    print("COMBINED SUMMARY")
    print(f"{'='*60}")
    print(f"Environments processed: {len(all_results)}")
    print(f"Items with errors: {output['summary']['total_items_with_errors']}")
    print(f"Total errors: {output['summary']['total_error_count']}")
    
    if output["summary"]["by_type"]:
        print(f"\nBy type:")
        for type_name, stats in output["summary"]["by_type"].items():
            print(f"  {type_name}: {stats['count']} items, {stats['errors']} errors")
    
    print(f"\nOutput written to: {output_file}")
    print(f"{'='*60}\n")
    
    return output_file


async def run_single_with_output(sut_name: str, org_id: str, username: str,
                                  item_type: Optional[str], hours_back: int):
    """Run for single environment and write output."""
    result = await run_single_environment(sut_name, org_id, username, item_type, hours_back)
    output_file, output = write_output([result])
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Items with errors: {len(result['items_with_errors'])}")
    print(f"Total errors: {sum(e['error_count'] for e in result['items_with_errors'])}")
    
    if result['items_with_errors']:
        print(f"\nBy type:")
        for type_name, stats in output["summary"]["by_type"].items():
            print(f"  {type_name}: {stats['count']} items, {stats['errors']} errors")
        
        print(f"\nItems requiring attention:")
        for item in sorted(result['items_with_errors'], key=lambda x: x["error_count"], reverse=True)[:10]:
            print(f"  - {item['item_name']} ({item['item_type']}): {item['error_count']} errors")
    
    print(f"\nOutput written to: {output_file}")
    print(f"{'='*60}\n")
    
    return output_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Velocity item logs and identify errors")
    parser.add_argument("--sut", help="SUT Config name (e.g., 'qa-advanced')")
    parser.add_argument("--org-id", help="Org ID for SUTConfig")
    parser.add_argument("--username", help="Username for SUTConfig")
    parser.add_argument("--config", help="YAML config file with multiple environments")
    parser.add_argument("--type", choices=["feeds", "rats", "bats"], 
                        help="Filter by item type (default: all)")
    parser.add_argument("--hours", type=int, default=None,
                        help=f"Hours to look back (default: from config or {HOURS_BACK})")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.config:
        # Multi-environment mode - hours from config if not specified
        result = asyncio.run(run_multi_environment(args.config, args.type, args.hours))
    elif args.sut and args.org_id and args.username:
        # Single environment mode - use default if not specified
        hours = args.hours if args.hours is not None else HOURS_BACK
        result = asyncio.run(run_single_with_output(args.sut, args.org_id, args.username, args.type, hours))
    else:
        parser.error("Either --config OR (--sut, --org-id, --username) are required")
    
    sys.exit(0)
