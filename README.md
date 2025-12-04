# AI-Powered Functional Testing for ArcGIS Velocity

This repository contains AI-first tools and resources for functional testing of ArcGIS Velocity across its multiple platform distributions: **AWS (Neo Reloaded)**, **Azure (Trinity)**, and **Enterprise (On-premises)**.

## Overview

Leveraging artificial intelligence and modern testing frameworks, this project streamlines the testing workflow for ArcGIS Velocity by providing intelligent test automation, analysis, and reporting capabilities across all deployment platforms and test types including Heimdall, ReadyAPI, Selenium BAT, Selenium E2E, Selenium FEED, and manual testing efforts.

## Available MCP Servers

This repository includes two Model Context Protocol (MCP) servers that enable AI assistants to interact with testing and development systems:

### 1. TestRail MCP Server (`testrail-mcp/`)
A comprehensive MCP server for interacting with TestRail API, enabling AI-powered test case management, test run reporting, and test result analysis.

**Key Features:**
- Test case management (CRUD operations)
- Test run creation and updates
- Test result reporting
- Project and suite management
- Automatic pagination for large datasets

**See:** [testrail-mcp/README.md](testrail-mcp/README.md)

### 2. ArcGIS Velocity MCP Server (`arcgis-velocity-mcp/`)
A Model Context Protocol server providing programmatic access to ArcGIS Velocity API endpoints for managing feeds, analytics, and services.

**Key Features:**
- Feed management (create, start, stop, monitor)
- Real-time analytics operations
- Big data analytics management
- Service management (feature, map, stream)
- Metrics and monitoring
- Configuration import/export
- System logs querying

**See:** [arcgis-velocity-mcp/README.md](arcgis-velocity-mcp/README.md)