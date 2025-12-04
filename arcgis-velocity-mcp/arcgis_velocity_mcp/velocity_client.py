"""
ArcGIS Velocity API Client

This module provides a client for interacting with the ArcGIS Velocity REST API.
"""

import httpx
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class VelocityClient:
    """Client for interacting with ArcGIS Velocity API with automatic token management"""
    
    def __init__(self, base_url: str, username: str, password: str, portal_url: str):
        """
        Initialize the Velocity API client.
        
        Args:
            base_url: Base URL of the Velocity instance (e.g., https://your-instance.arcgis.com)
            username: ArcGIS username
            password: ArcGIS password
            portal_url: Portal URL for token generation (e.g., https://www.arcgis.com)
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.portal_url = portal_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _generate_token(self) -> Dict[str, Any]:
        """
        Generate a new token from the portal.
        
        Returns:
            Token response with token and expiration time
        """
        token_url = f"{self.portal_url}/sharing/rest/generateToken"
        
        data = {
            "username": self.username,
            "password": self.password,
            "referer": self.base_url,
            "f": "json",
            "expiration": 60  # 60 minutes
        }
        
        try:
            response = await self.client.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            if "token" not in token_data:
                error_msg = token_data.get("error", {}).get("message", "Unknown error generating token")
                raise Exception(f"Token generation failed: {error_msg}")
            
            logger.info("Successfully generated new token")
            return token_data
            
        except Exception as e:
            logger.error(f"Error generating token: {str(e)}")
            raise
    
    async def _ensure_valid_token(self) -> str:
        """
        Ensure we have a valid token, generating a new one if needed.
        
        Returns:
            Valid authentication token
        """
        # Check if we need a new token
        if self._token is None or self._token_expiry is None or datetime.now() >= self._token_expiry:
            logger.info("Token expired or missing, generating new token...")
            token_data = await self._generate_token()
            self._token = token_data["token"]
            
            # Token expiry is in milliseconds from epoch
            expiry_ms = token_data.get("expires", 0)
            if expiry_ms:
                self._token_expiry = datetime.fromtimestamp(expiry_ms / 1000)
                # Refresh 5 minutes before actual expiry
                self._token_expiry = self._token_expiry - timedelta(minutes=5)
            else:
                # Default to 55 minutes from now if no expiry provided
                self._token_expiry = datetime.now() + timedelta(minutes=55)
            
            logger.info(f"Token will be refreshed at {self._token_expiry}")
        
        return self._token
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests (without auth, will be added per request)"""
        return {
            "Content-Type": "application/json"
        }
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an API request with automatic token management.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            json: JSON body data
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        
        # Ensure we have a valid token
        token = await self._ensure_valid_token()
        
        # Add token to headers
        headers = self._get_headers()
        headers["Authorization"] = f"Bearer {token}"
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json
            )
            response.raise_for_status()
            
            # Some endpoints return empty responses
            if response.status_code == 204 or not response.content:
                return {"success": True}
                
            return response.json()
            
        except httpx.HTTPStatusError as e:
            # If we get a 401, the token might be invalid - try regenerating once
            if e.response.status_code == 401:
                logger.warning("Received 401, attempting to regenerate token...")
                self._token = None  # Force token regeneration
                token = await self._ensure_valid_token()
                headers["Authorization"] = f"Bearer {token}"
                
                # Retry the request
                response = await self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json
                )
                response.raise_for_status()
                
                if response.status_code == 204 or not response.content:
                    return {"success": True}
                    
                return response.json()
            
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            raise
    
    # ========== Feed Management ==========
    
    async def get_feeds(self) -> List[Dict[str, Any]]:
        """Get all feeds"""
        return await self._request("GET", "/iot/feed")
    
    async def get_feed(self, feed_id: str) -> Dict[str, Any]:
        """Get a specific feed by ID"""
        return await self._request("GET", f"/iot/feed/{feed_id}")
    
    async def create_feed(self, feed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new feed"""
        return await self._request("POST", "/iot/feed", json=feed_data)
    
    async def update_feed(self, feed_id: str, feed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing feed"""
        return await self._request("PUT", f"/iot/feed/{feed_id}", json=feed_data)
    
    async def delete_feed(self, feed_id: str) -> Dict[str, Any]:
        """Delete a feed"""
        return await self._request("DELETE", f"/iot/feed/{feed_id}")
    
    async def start_feed(self, feed_id: str) -> Dict[str, Any]:
        """Start a feed"""
        return await self._request("GET", f"/iot/feed/{feed_id}/start")
    
    async def stop_feed(self, feed_id: str) -> Dict[str, Any]:
        """Stop a feed"""
        return await self._request("GET", f"/iot/feed/{feed_id}/stop")
    
    async def get_feed_status(self, feed_id: str) -> Dict[str, Any]:
        """Get feed status"""
        return await self._request("GET", f"/iot/feed/{feed_id}/status")
    
    async def get_all_feed_status(self, item_ids: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get status of all feeds, optionally filtered by item IDs"""
        params = {"itemIds": item_ids} if item_ids else None
        return await self._request("GET", "/iot/feed/status", params=params)
    
    async def get_feed_metrics(self, feed_id: str, time_interval: Optional[str] = None) -> Dict[str, Any]:
        """Get feed metrics"""
        body = {}
        if time_interval:
            body["timeInterval"] = time_interval
        return await self._request("POST", f"/iot/feed/metrics/{feed_id}", json=body)
    
    async def get_feed_history(
        self, 
        feed_id: str, 
        start_time: int, 
        end_time: int,
        time_interval: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get feed history metrics"""
        body = {
            "startTime": start_time,
            "endTime": end_time
        }
        if time_interval:
            body["timeInterval"] = time_interval
        return await self._request("POST", f"/iot/feed/metrics/{feed_id}/history", json=body)
    
    async def clone_feed(self, feed_id: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Clone a feed"""
        body = {"name": name}
        if description:
            body["description"] = description
        return await self._request("POST", f"/iot/feed/{feed_id}/clone", json=body)
    
    async def validate_feed(self, feed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a feed configuration"""
        return await self._request("POST", "/iot/feed/validate", json=feed_data)
    
    async def validate_feed_by_id(self, feed_id: str) -> Dict[str, Any]:
        """Validate a feed by ID"""
        return await self._request("GET", f"/iot/feed/validate/{feed_id}")
    
    async def scale_feed(self, feed_id: str, cpu: float, memory: float, instances: int) -> Dict[str, Any]:
        """Scale a running feed"""
        body = {
            "cpu": cpu,
            "memory": memory,
            "instances": instances
        }
        return await self._request("PUT", f"/iot/feed/{feed_id}/scale", json=body)
    
    # ========== Real-Time Analytics ==========
    
    async def get_realtime_analytics(self) -> List[Dict[str, Any]]:
        """Get all real-time analytics"""
        return await self._request("GET", "/iot/analytics/realtime")
    
    async def get_realtime_analytic(self, analytic_id: str) -> Dict[str, Any]:
        """Get a specific real-time analytic"""
        return await self._request("GET", f"/iot/analytics/realtime/{analytic_id}")
    
    async def create_realtime_analytic(self, analytic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new real-time analytic"""
        return await self._request("POST", "/iot/analytics/realtime", json=analytic_data)
    
    async def update_realtime_analytic(self, analytic_id: str, analytic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing real-time analytic"""
        return await self._request("PUT", f"/iot/analytics/realtime/{analytic_id}", json=analytic_data)
    
    async def delete_realtime_analytic(self, analytic_id: str) -> Dict[str, Any]:
        """Delete a real-time analytic"""
        return await self._request("DELETE", f"/iot/analytics/realtime/{analytic_id}")
    
    async def start_realtime_analytic(self, analytic_id: str) -> Dict[str, Any]:
        """Start a real-time analytic"""
        return await self._request("GET", f"/iot/analytics/realtime/{analytic_id}/start")
    
    async def stop_realtime_analytic(self, analytic_id: str) -> Dict[str, Any]:
        """Stop a real-time analytic"""
        return await self._request("GET", f"/iot/analytics/realtime/{analytic_id}/stop")
    
    async def get_realtime_analytic_status(self, analytic_id: str) -> Dict[str, Any]:
        """Get real-time analytic status"""
        return await self._request("GET", f"/iot/analytics/realtime/{analytic_id}/status")
    
    async def get_all_realtime_analytics_status(self) -> Dict[str, Any]:
        """Get status of all real-time analytics"""
        return await self._request("GET", "/iot/analytics/realtime/status")
    
    async def get_realtime_analytic_metrics(
        self, 
        analytic_id: str, 
        time_interval: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get real-time analytic metrics"""
        body = {}
        if time_interval:
            body["timeInterval"] = time_interval
        return await self._request("POST", f"/iot/analytics/realtime/metrics/{analytic_id}", json=body)
    
    async def clone_realtime_analytic(
        self, 
        analytic_id: str, 
        name: str, 
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Clone a real-time analytic"""
        body = {"name": name}
        if description:
            body["description"] = description
        return await self._request("POST", f"/iot/analytics/realtime/{analytic_id}/clone", json=body)
    
    async def scale_realtime_analytic(
        self, 
        analytic_id: str, 
        cpu: float, 
        memory: float, 
        instances: int
    ) -> Dict[str, Any]:
        """Scale a running real-time analytic"""
        body = {
            "cpu": cpu,
            "memory": memory,
            "instances": instances
        }
        return await self._request("PUT", f"/iot/analytics/realtime/{analytic_id}/scale", json=body)
    
    async def validate_realtime_analytic(self, analytic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a real-time analytic configuration"""
        return await self._request("POST", "/iot/analytics/realtime/validate", json=analytic_data)
    
    async def validate_realtime_analytic_by_id(self, analytic_id: str) -> Dict[str, Any]:
        """Validate a real-time analytic by ID"""
        return await self._request("GET", f"/iot/analytics/realtime/validate/{analytic_id}")
    
    # ========== Big Data Analytics ==========
    
    async def get_bigdata_analytics(self) -> List[Dict[str, Any]]:
        """Get all big data analytics"""
        return await self._request("GET", "/iot/analytics/bigdata")
    
    async def get_bigdata_analytic(self, analytic_id: str) -> Dict[str, Any]:
        """Get a specific big data analytic"""
        return await self._request("GET", f"/iot/analytics/bigdata/{analytic_id}")
    
    async def create_bigdata_analytic(self, analytic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new big data analytic"""
        return await self._request("POST", "/iot/analytics/bigdata", json=analytic_data)
    
    async def update_bigdata_analytic(self, analytic_id: str, analytic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing big data analytic"""
        return await self._request("PUT", f"/iot/analytics/bigdata/{analytic_id}", json=analytic_data)
    
    async def delete_bigdata_analytic(self, analytic_id: str) -> Dict[str, Any]:
        """Delete a big data analytic"""
        return await self._request("DELETE", f"/iot/analytics/bigdata/{analytic_id}")
    
    async def start_bigdata_analytic(self, analytic_id: str) -> Dict[str, Any]:
        """Start a big data analytic"""
        return await self._request("GET", f"/iot/analytics/bigdata/{analytic_id}/start")
    
    async def stop_bigdata_analytic(self, analytic_id: str) -> Dict[str, Any]:
        """Stop a big data analytic"""
        return await self._request("GET", f"/iot/analytics/bigdata/{analytic_id}/stop")
    
    async def get_bigdata_analytic_status(self, analytic_id: str, watch: Optional[bool] = None) -> Dict[str, Any]:
        """Get big data analytic status"""
        params = {"watch": str(watch).lower()} if watch is not None else None
        return await self._request("GET", f"/iot/analytics/bigdata/{analytic_id}/status", params=params)
    
    async def get_all_bigdata_analytics_status(self) -> Dict[str, Any]:
        """Get status of all big data analytics"""
        return await self._request("GET", "/iot/analytics/bigdata/status")
    
    async def clone_bigdata_analytic(
        self, 
        analytic_id: str, 
        name: str, 
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Clone a big data analytic"""
        body = {"name": name}
        if description:
            body["description"] = description
        return await self._request("POST", f"/iot/analytics/bigdata/{analytic_id}/clone", json=body)
    
    async def scale_bigdata_analytic(
        self, 
        analytic_id: str, 
        cpu: float, 
        memory: float, 
        instances: int
    ) -> Dict[str, Any]:
        """Scale a running big data analytic"""
        body = {
            "cpu": cpu,
            "memory": memory,
            "instances": instances
        }
        return await self._request("PUT", f"/iot/analytics/bigdata/{analytic_id}/scale", json=body)
    
    async def validate_bigdata_analytic(self, analytic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a big data analytic configuration"""
        return await self._request("POST", "/iot/analytics/bigdata/validate", json=analytic_data)
    
    async def validate_bigdata_analytic_by_id(self, analytic_id: str) -> Dict[str, Any]:
        """Validate a big data analytic by ID"""
        return await self._request("GET", f"/iot/analytics/bigdata/validate/{analytic_id}")
    
    # ========== Services ==========
    
    async def get_all_services(self) -> Dict[str, Any]:
        """Get all services (feature, map, and stream)"""
        return await self._request("GET", "/iot/services")
    
    async def get_feature_services(self) -> Dict[str, Any]:
        """Get all feature services"""
        return await self._request("GET", "/iot/services/feature")
    
    async def get_feature_service(self, service_id: str) -> Dict[str, Any]:
        """Get a specific feature service"""
        return await self._request("GET", f"/iot/services/feature/{service_id}")
    
    async def create_feature_service(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new feature service"""
        return await self._request("POST", "/iot/services/feature", json=service_data)
    
    async def update_feature_service(self, service_id: str, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a feature service"""
        return await self._request("PUT", f"/iot/services/feature/{service_id}", json=service_data)
    
    async def delete_feature_service(self, service_id: str) -> Dict[str, Any]:
        """Delete a feature service"""
        return await self._request("DELETE", f"/iot/services/feature/{service_id}")
    
    async def get_stream_services(self) -> List[Dict[str, Any]]:
        """Get all stream services"""
        return await self._request("GET", "/iot/services/stream")
    
    async def get_stream_service(self, service_id: str) -> Dict[str, Any]:
        """Get a specific stream service"""
        return await self._request("GET", f"/iot/services/stream/{service_id}")
    
    async def update_stream_service(self, service_id: str, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a stream service"""
        return await self._request("PUT", f"/iot/services/stream/{service_id}", json=service_data)
    
    async def delete_stream_service(self, service_id: str) -> Dict[str, Any]:
        """Delete a stream service"""
        return await self._request("DELETE", f"/iot/services/stream/{service_id}")
    
    async def get_service_dependencies(self, portal_item_id: str) -> List[Dict[str, Any]]:
        """Get list of items that depend on a portal item"""
        return await self._request("GET", f"/iot/services/dependencies/{portal_item_id}")
    
    # ========== Definitions ==========
    
    async def get_feed_types(self, locale: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all feed type definitions"""
        params = {"locale": locale} if locale else None
        return await self._request("GET", "/iot/feed/types", params=params)
    
    async def get_feed_type(self, name: str, locale: Optional[str] = None) -> Dict[str, Any]:
        """Get a specific feed type definition"""
        params = {"locale": locale} if locale else None
        return await self._request("GET", f"/iot/feed/type/{name}", params=params)
    
    async def get_tool_definitions(self, locale: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all tool definitions"""
        params = {"locale": locale} if locale else None
        return await self._request("GET", "/iot/analytics/tools", params=params)
    
    async def get_tool_definition(self, name: str, locale: Optional[str] = None) -> Dict[str, Any]:
        """Get a specific tool definition"""
        params = {"locale": locale} if locale else None
        return await self._request("GET", f"/iot/analytics/tools/{name}", params=params)
    
    async def get_output_definitions(self, locale: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all output definitions"""
        params = {"locale": locale} if locale else None
        return await self._request("GET", "/iot/outputs", params=params)
    
    async def get_output_definition(self, name: str, locale: Optional[str] = None) -> Dict[str, Any]:
        """Get a specific output definition"""
        params = {"locale": locale} if locale else None
        return await self._request("GET", f"/iot/outputs/{name}", params=params)
    
    async def get_source_definitions(self, locale: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all source definitions"""
        params = {"locale": locale} if locale else None
        return await self._request("GET", "/iot/sources", params=params)
    
    async def get_source_definition(self, name: str, locale: Optional[str] = None) -> Dict[str, Any]:
        """Get a specific source definition"""
        params = {"locale": locale} if locale else None
        return await self._request("GET", f"/iot/sources/{name}", params=params)
    
    async def get_format_definitions(self, locale: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all format definitions"""
        params = {"locale": locale} if locale else None
        return await self._request("GET", "/iot/formats", params=params)
    
    # ========== Logs ==========
    
    async def query_logs(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Query system logs"""
        return await self._request("POST", "/iot/logs", json=query_params)
    
    async def query_logs_by_item(self, item_id: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Query logs for a specific item"""
        return await self._request("POST", f"/iot/logs/{item_id}", json=query_params)
    
    # ========== Configuration ==========
    
    async def export_configuration(self) -> Dict[str, Any]:
        """Export configuration snapshot"""
        return await self._request("GET", "/iot/configuration/export")
    
    async def import_configuration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import configuration from snapshot"""
        return await self._request("POST", "/iot/configuration/import", json=config_data)
    
    async def reset_configuration(self) -> Dict[str, Any]:
        """Reset site - delete all item configurations"""
        return await self._request("DELETE", "/iot/configuration/reset")
    
    # ========== Tenant & Metrics ==========
    
    async def get_tenant_settings(self) -> Dict[str, Any]:
        """Get tenant settings"""
        return await self._request("GET", "/iot/tenant/settings")
    
    async def update_tenant_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update tenant settings"""
        return await self._request("PUT", "/iot/tenant/settings", json=settings)
    
    async def get_tenant_metrics_summary(self) -> Dict[str, Any]:
        """Get tenant metrics summary"""
        return await self._request("GET", "/iot/tenant/metrics/status")
    
    async def get_tenant_metrics_history(
        self, 
        start_time: int, 
        end_time: int,
        time_interval: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get tenant metrics history"""
        body = {
            "startTime": start_time,
            "endTime": end_time
        }
        if time_interval:
            body["timeInterval"] = time_interval
        return await self._request("POST", "/iot/tenant/metrics/history", json=body)
    
    # ========== System ==========
    
    async def get_version(self) -> Dict[str, Any]:
        """Get Velocity API version"""
        return await self._request("GET", "/iot/api/version")
