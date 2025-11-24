# GitHub Copilot Instructions for ArcGIS Velocity TestRail Integration

## TestRail Project Context

### Primary Project Information
- **Project Name:** ArcGIS Velocity
- **Project ID:** 63
- **Project URL:** https://esri.testrail.com/index.php?/projects/overview/63
- **Suite Mode:** Multiple test suites (mode 3)

### Important Guidelines

#### 1. Default Project Context
All TestRail MCP operations should target the ArcGIS Velocity project (ID: 63) unless explicitly specified otherwise. When using TestRail MCP tools, always use project_id: 63.

#### 2. Platform Distribution Awareness
ArcGIS Velocity is deployed across multiple platforms. Always identify and distinguish which platform distribution test results, test cases, or test runs are associated with:

- **AWS (Neo Reloaded)** - Amazon Web Services deployment
- **Azure (Trinity)** - Microsoft Azure deployment  
- **Enterprise** - On-premises ArcGIS Enterprise deployment

When querying, creating, or reporting TestRail data:
- Always specify the platform (AWS/Azure/Enterprise) in test run names, descriptions, and filters
- Use platform-specific tags or labels when available
- Clearly indicate the platform context in any summaries or reports

#### 3. Environment Specification
Within each platform, distinguish between environments:
- **DEV** - Development environment
- **QA** - Quality Assurance environment
- **Production** - Production environment (if applicable)

#### 4. Test Types
Recognize and categorize different test types:
- **Heimdall** - Non-GUI automated tests
- **ReadyAPI** - API testing
- **Selenium BAT** - Build Acceptance Tests (GUI)
- **Selenium E2E** - End-to-End tests (GUI)
- **Selenium FEED** - Feed processing tests (GUI)
- **Manual** - Manual testing

#### 5. Naming Conventions
When creating or filtering test runs, cases, or results:
- Include platform identifier: `[AWS]`, `[Azure]`, or `[Enterprise]`
- Include environment: `DEV`, `QA`, `Production`
- Include test type when applicable
- Example: `[Azure] QA - Selenium E2E - Sprint 24.3`

#### 6. Reporting Standards
When generating reports or summaries:
- Group results by platform first, then by test type
- Clearly separate AWS, Azure, and Enterprise results
- Include environment context in all summaries
- Highlight platform-specific failures or issues

## TestRail MCP Usage Examples

### Example 1: Getting Test Runs
```python
# Always filter for Velocity project (ID: 63)
# and specify platform in the query
get_runs(project_id=63)  # Then filter by platform in results
```

### Example 2: Creating Test Runs
```python
# Include platform and environment in name
add_run(
    project_id=63,
    name="[Azure] QA - Heimdall Regression - v1.2.0",
    description="Automated regression tests for Azure QA environment"
)
```

### Example 3: Querying Test Cases
```python
# When searching test cases, consider platform-specific cases
# Use sections or custom fields to filter by platform
```

## Additional Resources

### GitHub Repositories
- **Velocity Online:** https://devtopia.esri.com/WebGIS/arcgis-velocity-online
- **PS Automation Regression:** https://github.com/EsriPS/PS-Regression/tree/main/Velocity
- **PS Accessibility Tests:** https://github.com/EsriPS/PS-Products-Accessibility
- **Real-time Testing (Heimdall):** https://devtopia.esri.com/WebGIS/real-time-gis-testing

### Jenkins Automation
- **Main Jenkins View:** http://mcstest87:8080/view/QA_Velocity/

### Confluence Documentation
- **Release Testing Wiki:** https://confluencewikidev.esri.com/display/RTQA/Release+Testing

## Default Behavior

When no platform is specified in a prompt:
1. Ask for clarification about which platform (AWS/Azure/Enterprise)
2. If context suggests a specific platform, state the assumption clearly
3. When listing results from all platforms, clearly separate and label each section

## Keywords to Watch For

Platform indicators in prompts:
- AWS, Neo, "Neo Reloaded" → AWS platform
- Azure, Trinity → Azure platform
- Enterprise, On-prem, On-premises → Enterprise platform

Environment indicators:
- Dev, Development → DEV environment
- QA, Testing, Test → QA environment
- Prod, Production → Production environment
