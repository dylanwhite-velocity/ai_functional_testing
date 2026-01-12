"""
TestRail MCP Server

This module implements the MCP server for TestRail API.
"""

import asyncio
import logging
import json
from typing import Any, Optional, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from .testrail_client import TestRailClient
from .config import TESTRAIL_URL, TESTRAIL_USERNAME, TESTRAIL_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server instance
server = Server("testrail-mcp")


def create_testrail_client() -> TestRailClient:
    """Create and return a TestRail API client"""
    return TestRailClient(TESTRAIL_URL, TESTRAIL_USERNAME, TESTRAIL_API_KEY)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools"""
    return [
        # Project tools
        Tool(
            name="get_project",
            description="Get a project by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "The ID of the project"}
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="get_projects",
            description="Get all projects",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="add_project",
            description="Add a new project",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The name of the project"},
                    "announcement": {"type": "string", "description": "The announcement of the project"},
                    "show_announcement": {"type": "boolean", "description": "Whether to show the announcement"},
                    "suite_mode": {"type": "integer", "description": "Suite mode (1=single, 2=single+baselines, 3=multiple)"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="update_project",
            description="Update an existing project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "The ID of the project"},
                    "name": {"type": "string", "description": "The name of the project"},
                    "announcement": {"type": "string", "description": "The announcement of the project"},
                    "show_announcement": {"type": "boolean", "description": "Whether to show the announcement"},
                    "is_completed": {"type": "boolean", "description": "Whether the project is completed"}
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="delete_project",
            description="Delete a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "The ID of the project"}
                },
                "required": ["project_id"]
            }
        ),
        
        # Case tools
        Tool(
            name="get_case",
            description="Get a test case by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "integer", "description": "The ID of the test case"}
                },
                "required": ["case_id"]
            }
        ),
        Tool(
            name="get_cases",
            description="Get all test cases for a project/suite with automatic pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "The ID of the project"},
                    "suite_id": {"type": "integer", "description": "The ID of the test suite"},
                    "section_id": {"type": "integer", "description": "The ID of the section to filter by"}
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="add_case",
            description="Add a new test case",
            inputSchema={
                "type": "object",
                "properties": {
                    "section_id": {"type": "integer", "description": "The ID of the section"},
                    "title": {"type": "string", "description": "The title of the test case"},
                    "type_id": {"type": "integer", "description": "The ID of the case type"},
                    "priority_id": {"type": "integer", "description": "The ID of the priority"},
                    "estimate": {"type": "string", "description": "The estimate (e.g. '30s' or '1m 45s')"},
                    "milestone_id": {"type": "integer", "description": "The ID of the milestone"},
                    "refs": {"type": "string", "description": "A comma-separated list of references"},
                    "custom_steps": {"type": "string", "description": "Steps as string"},
                    "custom_expected": {"type": "string", "description": "Expected result as string"},
                    "custom_steps_separated": {"type": "array", "description": "Test steps as array of objects"},
                    "steps_separated": {"type": "array", "description": "Test steps as array of objects"}
                },
                "required": ["section_id", "title"]
            }
        ),
        Tool(
            name="update_case",
            description="Update an existing test case",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "integer", "description": "The ID of the test case"},
                    "title": {"type": "string", "description": "The title of the test case"},
                    "type_id": {"type": "integer", "description": "The ID of the case type"},
                    "priority_id": {"type": "integer", "description": "The ID of the priority"},
                    "estimate": {"type": "string", "description": "The estimate (e.g. '30s' or '1m 45s')"},
                    "milestone_id": {"type": "integer", "description": "The ID of the milestone"},
                    "refs": {"type": "string", "description": "A comma-separated list of references"},
                    "custom_steps": {"type": "string", "description": "Steps as string"},
                    "custom_expected": {"type": "string", "description": "Expected result as string"},
                    "custom_steps_separated": {"type": "array", "description": "Test steps as array of objects"},
                    "steps_separated": {"type": "array", "description": "Test steps as array of objects"}
                },
                "required": ["case_id"]
            }
        ),
        Tool(
            name="delete_case",
            description="Delete a test case",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "integer", "description": "The ID of the test case"}
                },
                "required": ["case_id"]
            }
        ),
        
        # Suite tools
        Tool(
            name="get_suites",
            description="Get all test suites for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "The ID of the project"}
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="get_suite",
            description="Get a test suite by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "suite_id": {"type": "integer", "description": "The ID of the suite"}
                },
                "required": ["suite_id"]
            }
        ),
        
        # Section tools
        Tool(
            name="get_section",
            description="Retrieves details of a specific section by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "section_id": {"type": "integer", "description": "The ID of the section"}
                },
                "required": ["section_id"]
            }
        ),
        Tool(
            name="get_sections",
            description="Retrieves all sections for a specified project and or suite",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "The ID of the project"},
                    "suite_id": {"type": "integer", "description": "The ID of the test suite"}
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="add_section",
            description="Creates a new section in a TestRail project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "The ID of the project"},
                    "name": {"type": "string", "description": "Name of the section"},
                    "description": {"type": "string", "description": "Description of the section"},
                    "suite_id": {"type": "integer", "description": "The ID of the test suite"},
                    "parent_id": {"type": "integer", "description": "The ID of the parent section"}
                },
                "required": ["project_id", "name", "description"]
            }
        ),
        Tool(
            name="update_section",
            description="Updates an existing section",
            inputSchema={
                "type": "object",
                "properties": {
                    "section_id": {"type": "integer", "description": "The ID of the section"},
                    "name": {"type": "string", "description": "Name of the section"},
                    "description": {"type": "string", "description": "Description of the section"}
                },
                "required": ["section_id"]
            }
        ),
        Tool(
            name="delete_section",
            description="Deletes a section",
            inputSchema={
                "type": "object",
                "properties": {
                    "section_id": {"type": "integer", "description": "The ID of the section"},
                    "soft": {"type": "boolean", "description": "If true, returns affected test count without deletion"}
                },
                "required": ["section_id", "soft"]
            }
        ),
        Tool(
            name="move_section",
            description="Moves a section to a new position in the test hierarchy",
            inputSchema={
                "type": "object",
                "properties": {
                    "section_id": {"type": "integer", "description": "The ID of the section"},
                    "parent_id": {"type": "integer", "description": "ID of the new parent"},
                    "after_id": {"type": "integer", "description": "ID of the section to move after"}
                },
                "required": ["section_id"]
            }
        ),
        
        # Run tools
        Tool(
            name="get_run",
            description="Get a test run by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer", "description": "The ID of the test run"}
                },
                "required": ["run_id"]
            }
        ),
        Tool(
            name="get_runs",
            description="Get all test runs for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "The ID of the project"}
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="add_run",
            description="Add a new test run",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "The ID of the project"},
                    "suite_id": {"type": "integer", "description": "The ID of the test suite"},
                    "name": {"type": "string", "description": "The name of the test run"},
                    "description": {"type": "string", "description": "The description of the test run"},
                    "milestone_id": {"type": "integer", "description": "The ID of the milestone"},
                    "assignedto_id": {"type": "integer", "description": "The ID of the user to assign to"},
                    "include_all": {"type": "boolean", "description": "Include all test cases"},
                    "case_ids": {"type": "array", "description": "Array of case IDs for custom selection"}
                },
                "required": ["project_id", "suite_id", "name"]
            }
        ),
        Tool(
            name="update_run",
            description="Update an existing test run",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer", "description": "The ID of the test run"},
                    "name": {"type": "string", "description": "The name of the test run"},
                    "description": {"type": "string", "description": "The description of the test run"},
                    "milestone_id": {"type": "integer", "description": "The ID of the milestone"},
                    "assignedto_id": {"type": "integer", "description": "The ID of the user to assign to"},
                    "include_all": {"type": "boolean", "description": "Include all test cases"},
                    "case_ids": {"type": "array", "description": "Array of case IDs for custom selection"}
                },
                "required": ["run_id"]
            }
        ),
        Tool(
            name="close_run",
            description="Close an existing test run",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer", "description": "The ID of the test run"}
                },
                "required": ["run_id"]
            }
        ),
        Tool(
            name="delete_run",
            description="Delete a test run",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer", "description": "The ID of the test run"}
                },
                "required": ["run_id"]
            }
        ),
        
        # Results tools
        Tool(
            name="get_results",
            description="Get all test results for a test",
            inputSchema={
                "type": "object",
                "properties": {
                    "test_id": {"type": "integer", "description": "The ID of the test"}
                },
                "required": ["test_id"]
            }
        ),
        Tool(
            name="add_result",
            description="Add a new test result",
            inputSchema={
                "type": "object",
                "properties": {
                    "test_id": {"type": "integer", "description": "The ID of the test"},
                    "status_id": {"type": "integer", "description": "The ID of the test status"},
                    "comment": {"type": "string", "description": "Comment for the test result"},
                    "version": {"type": "string", "description": "Version or build tested against"},
                    "elapsed": {"type": "string", "description": "Time to execute (e.g. '30s' or '1m 45s')"},
                    "defects": {"type": "string", "description": "Comma-separated list of defects"},
                    "assignedto_id": {"type": "integer", "description": "ID of user to assign to"}
                },
                "required": ["test_id", "status_id"]
            }
        ),
        
        # Dataset tools
        Tool(
            name="get_dataset",
            description="Get a dataset by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "integer", "description": "The ID of the dataset"}
                },
                "required": ["dataset_id"]
            }
        ),
        Tool(
            name="get_datasets",
            description="Get all datasets for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "The ID of the project"}
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="add_dataset",
            description="Add a new dataset",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "The ID of the project"},
                    "name": {"type": "string", "description": "The name of the dataset"},
                    "description": {"type": "string", "description": "The description of the dataset"}
                },
                "required": ["project_id", "name"]
            }
        ),
        Tool(
            name="update_dataset",
            description="Update an existing dataset",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "integer", "description": "The ID of the dataset"},
                    "name": {"type": "string", "description": "The name of the dataset"},
                    "description": {"type": "string", "description": "The description of the dataset"}
                },
                "required": ["dataset_id"]
            }
        ),
        Tool(
            name="delete_dataset",
            description="Delete a dataset",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "integer", "description": "The ID of the dataset"}
                },
                "required": ["dataset_id"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    
    client = create_testrail_client()
    try:
        result = None
        
        # Project tools
        if name == "get_project":
            result = client.get_project(arguments["project_id"])
        elif name == "get_projects":
            result = client.get_projects()
        elif name == "add_project":
            data = {"name": arguments["name"]}
            if "announcement" in arguments:
                data["announcement"] = arguments["announcement"]
            if "show_announcement" in arguments:
                data["show_announcement"] = arguments["show_announcement"]
            if "suite_mode" in arguments:
                data["suite_mode"] = arguments["suite_mode"]
            result = client.add_project(data)
        elif name == "update_project":
            data = {}
            if "name" in arguments:
                data["name"] = arguments["name"]
            if "announcement" in arguments:
                data["announcement"] = arguments["announcement"]
            if "show_announcement" in arguments:
                data["show_announcement"] = arguments["show_announcement"]
            if "is_completed" in arguments:
                data["is_completed"] = arguments["is_completed"]
            result = client.update_project(arguments["project_id"], data)
        elif name == "delete_project":
            result = client.delete_project(arguments["project_id"])
        
        # Case tools
        elif name == "get_case":
            result = client.get_case(arguments["case_id"])
        elif name == "get_cases":
            result = client.get_cases(
                arguments["project_id"],
                arguments.get("suite_id"),
                arguments.get("section_id")
            )
        elif name == "add_case":
            data = {"title": arguments["title"]}
            optional_fields = ["type_id", "priority_id", "estimate", "milestone_id", "refs",
                             "custom_steps", "custom_expected", "custom_steps_separated", "steps_separated"]
            for field in optional_fields:
                if field in arguments:
                    data[field] = arguments[field]
            result = client.add_case(arguments["section_id"], data)
        elif name == "update_case":
            data = {}
            optional_fields = ["title", "type_id", "priority_id", "estimate", "milestone_id", "refs",
                             "custom_steps", "custom_expected", "custom_steps_separated", "steps_separated"]
            for field in optional_fields:
                if field in arguments:
                    data[field] = arguments[field]
            result = client.update_case(arguments["case_id"], data)
        elif name == "delete_case":
            result = client.delete_case(arguments["case_id"])
        
        # Suite tools
        elif name == "get_suites":
            result = client.get_suites(arguments["project_id"])
        elif name == "get_suite":
            result = client.get_suite(arguments["suite_id"])
        
        # Section tools
        elif name == "get_section":
            result = client.get_section(arguments["section_id"])
        elif name == "get_sections":
            result = client.get_sections(
                arguments["project_id"],
                arguments.get("suite_id")
            )
        elif name == "add_section":
            data = {
                "name": arguments["name"],
                "description": arguments["description"]
            }
            if "suite_id" in arguments:
                data["suite_id"] = arguments["suite_id"]
            if "parent_id" in arguments:
                data["parent_id"] = arguments["parent_id"]
            result = client.add_section(arguments["project_id"], data)
        elif name == "update_section":
            data = {}
            if "name" in arguments:
                data["name"] = arguments["name"]
            if "description" in arguments:
                data["description"] = arguments["description"]
            result = client.update_section(arguments["section_id"], data)
        elif name == "delete_section":
            result = client.delete_section(arguments["section_id"], arguments["soft"])
        elif name == "move_section":
            data = {}
            if "parent_id" in arguments:
                data["parent_id"] = arguments["parent_id"]
            if "after_id" in arguments:
                data["after_id"] = arguments["after_id"]
            result = client.move_section(arguments["section_id"], data)
        
        # Run tools
        elif name == "get_run":
            result = client.get_run(arguments["run_id"])
        elif name == "get_runs":
            result = client.get_runs(arguments["project_id"])
        elif name == "add_run":
            data = {
                "suite_id": arguments["suite_id"],
                "name": arguments["name"]
            }
            optional_fields = ["description", "milestone_id", "assignedto_id", "include_all", "case_ids"]
            for field in optional_fields:
                if field in arguments:
                    data[field] = arguments[field]
            result = client.add_run(arguments["project_id"], data)
        elif name == "update_run":
            data = {}
            optional_fields = ["name", "description", "milestone_id", "assignedto_id", "include_all", "case_ids"]
            for field in optional_fields:
                if field in arguments:
                    data[field] = arguments[field]
            result = client.update_run(arguments["run_id"], data)
        elif name == "close_run":
            result = client.close_run(arguments["run_id"])
        elif name == "delete_run":
            result = client.delete_run(arguments["run_id"])
        
        # Results tools
        elif name == "get_results":
            result = client.get_results(arguments["test_id"])
        elif name == "add_result":
            data = {"status_id": arguments["status_id"]}
            optional_fields = ["comment", "version", "elapsed", "defects", "assignedto_id"]
            for field in optional_fields:
                if field in arguments:
                    data[field] = arguments[field]
            result = client.add_result(arguments["test_id"], data)
        
        # Dataset tools
        elif name == "get_dataset":
            result = client.get_dataset(arguments["dataset_id"])
        elif name == "get_datasets":
            result = client.get_datasets(arguments["project_id"])
        elif name == "add_dataset":
            data = {"name": arguments["name"]}
            if "description" in arguments:
                data["description"] = arguments["description"]
            result = client.add_dataset(arguments["project_id"], data)
        elif name == "update_dataset":
            data = {}
            if "name" in arguments:
                data["name"] = arguments["name"]
            if "description" in arguments:
                data["description"] = arguments["description"]
            result = client.update_dataset(arguments["dataset_id"], data)
        elif name == "delete_dataset":
            result = client.delete_dataset(arguments["dataset_id"])
        
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Format the response
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
