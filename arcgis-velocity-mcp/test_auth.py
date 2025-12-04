#!/usr/bin/env python3
"""
Test script for ArcGIS Velocity MCP Server authentication

This script verifies that the token generation and API access work correctly.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent))

from arcgis_velocity_mcp import VelocityClient, get_config


async def test_authentication():
    """Test authentication and basic API access"""
    
    print("Testing ArcGIS Velocity MCP Server Authentication")
    print("=" * 50)
    
    try:
        # Load configuration
        print("\n1. Loading configuration...")
        config = get_config()
        print(f"   ✓ Base URL: {config.base_url}")
        print(f"   ✓ Username: {config.username}")
        print(f"   ✓ Portal URL: {config.portal_url}")
        
        # Create client
        print("\n2. Creating Velocity client...")
        async with VelocityClient(
            config.base_url,
            config.username,
            config.password,
            config.portal_url
        ) as client:
            print("   ✓ Client created successfully")
            
            # Test token generation
            print("\n3. Testing token generation...")
            token = await client._ensure_valid_token()
            print(f"   ✓ Token generated: {token[:20]}...")
            print(f"   ✓ Token expiry: {client._token_expiry}")
            
            # Test API call - get version
            print("\n4. Testing API call (get version)...")
            version = await client.get_version()
            print(f"   ✓ API Version: {version.get('version', 'Unknown')}")
            
            # Test another API call - list feeds
            print("\n5. Testing API call (list feeds)...")
            feeds = await client.get_feeds()
            print(f"   ✓ Found {len(feeds)} feeds")
            
            if feeds:
                print(f"   ✓ Sample feed: {feeds[0].get('label', 'Unknown')}")
            
            print("\n" + "=" * 50)
            print("✓ All tests passed successfully!")
            print("=" * 50)
            
    except ValueError as e:
        print(f"\n✗ Configuration Error: {e}")
        print("\nPlease ensure all required environment variables are set:")
        print("  - VELOCITY_BASE_URL")
        print("  - VELOCITY_USERNAME")
        print("  - VELOCITY_PASSWORD")
        print("  - VELOCITY_PORTAL_URL")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_authentication())
