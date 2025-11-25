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

#### 2. Platform-Agnostic Testing
All test cases in TestRail are designed to be platform-agnostic and should work on any distribution (AWS, Azure, or Enterprise). Tests are designed to validate functionality regardless of the deployment platform.

When querying, creating, or reporting TestRail data:
- Test cases apply to all platforms unless explicitly stated otherwise
- Focus on functionality being tested rather than platform specifics
- Test runs may target specific environments but test cases remain universal

#### 3. Environment Specification
Distinguish between test environments when creating test runs:
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
- Include environment: `DEV`, `QA`, `Production`
- Include test type when applicable
- Include version or sprint information when relevant
- Example: `QA - Selenium E2E - Sprint 24.3` or `DEV - Heimdall Regression - v1.2.0`

#### 6. Reporting Standards
When generating reports or summaries:
- Group results by test type and environment
- Include environment context in all summaries
- Highlight failures or issues with clear descriptions
- Focus on functionality tested rather than platform specifics

## TestRail MCP Usage Examples

### Example 1: Getting Test Runs
```python
# Always filter for Velocity project (ID: 63)
get_runs(project_id=63)
```

### Example 2: Creating Test Runs
```python
# Include environment and test type in name
add_run(
    project_id=63,
    name="QA - Heimdall Regression - v1.2.0",
    description="Automated regression tests for QA environment"
)
```

### Example 3: Querying Test Cases
```python
# Test cases are platform-agnostic and work across all distributions
# Filter by suite, section, or test type as needed
get_cases(project_id=63, suite_id=7253)
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

When environment is not specified in a prompt:
1. Ask for clarification about which environment (DEV/QA/Production)
2. If context suggests a specific environment, state the assumption clearly
3. Default to QA environment for test execution if not specified

## Keywords to Watch For

Environment indicators:
- Dev, Development → DEV environment
- QA, Testing, Test → QA environment
- Prod, Production → Production environment
