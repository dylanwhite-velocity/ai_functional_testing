# Test Case Fix Process - Simplified Workflow

## Overview

This streamlined workflow replaces the manual, multi-system process with a single GitHub issue that contains all necessary information and automates administrative tasks.

## New Simplified Process

### 1. Identify Failure in Grafana
- Open [Test Case Result History by Section](your-grafana-url)
- Select feature area (Feed/Output/Tools/etc.)
- Click failed test → "Open Test Case Results"

### 2. Create GitHub Issue
- Go to PS-Regression repo
- Click "New Issue" → Select **"🔧 Test Case Fix"** template
- Fill in the markdown template with:
  - TestRail Case ID (replace C12345)
  - Grafana link
  - TestRail link
  - Allure report link (from TestRail Results & Comments)
  - Test type (delete options that don't apply, leave one)
  - Environment (delete options that don't apply, leave one)
  - Component/Feature (delete options that don't apply, leave one)
  - Brief failure description

### 3. Fix Test Case in TestRail
Update the test case with:
- Preconditions (linked test cases or required data)
- Test Case Summary (what the test validates)
- Rewritten steps (clear, no shared steps)
- Expected results (only necessary fields)
- Type changed to "Automated"
- Owner changed to you
- References field includes GitHub issue link

### 4. Document Changes in GitHub
- Return to GitHub issue
- Fill in "Changes Made in TestRail" section (add your bullet points)
- Check off completed items in TestRail Checklist (change `[ ]` to `[x]`)
- Check the action required box (usually "Update automation in DEV and QA")

### 5. Automation Handles the Rest
The CI/CD workflow automatically:
- Adds appropriate labels (`QC–ReadyAPI`, `QC–Selenium`, etc.)
- Adds watchers (Yini, Eric, Manish)
- Adds to project board
- Posts comment requesting automation team updates
- No manual tagging or label management needed!

## What Changed

### ❌ Old Process Pain Points
- Navigate 4+ systems (Grafana → TestRail → PS Repo → Confluence)
- Manual label application
- Manual Excel exports and Confluence table updates
- Instructions scattered across multiple Confluence pages
- Manual tagging of team members
- Separate PBI creation for simple updates
- Multiple escalation rules and decision trees

### ✅ New Streamlined Benefits
- **Single source of truth**: GitHub issue contains all links and context
- **Zero manual admin**: Labels, watchers, project assignment automated
- **No Confluence updates needed**: For test case fixes
- **Clear next steps**: Built into issue template
- **Reduced cognitive load**: No need to remember multi-page instructions
- **Faster turnaround**: Reduced from 15+ steps to 4 key steps

## Configuration Required

### Update GitHub Usernames
In `.github/workflows/test-case-fix-automation.yml`, replace placeholder usernames:
```yaml
const watchers = [
  'yini-username',    // Replace with Yini's GitHub username
  'eric-username',    // Replace with Eric's GitHub username  
  'manish-username'   // Replace with Manish's GitHub username
];
```

### Update Project Board Number
If using GitHub Projects, update the project number:
```yaml
const projectNumber = 1; // Update with your PS Regression project number
```

### Create Component Labels (Optional)
Create these labels in your repo for better organization:
- `component:feed`
- `component:output`
- `component:tools`
- `component:layers`
- `component:analytics`
- `component:bigdata`
- `component:sources`

## When to Still Use Confluence

Confluence updates are now **only needed** for:
- Major feature documentation updates
- Adding new preconditions that affect multiple tests
- Known limitations or testing gaps
- Quarterly/release summaries

**Not needed for**: Individual test case fixes (handled in GitHub)

## Proposal Summary for Manager

**Current state**: 15+ manual steps across 4 systems, ~2-3 hours per test case fix

**Proposed state**: 4 key steps, single GitHub issue, ~30-45 minutes per test case fix

**Time savings**: ~60-70% reduction in administrative overhead

**Quality improvements**: 
- Reduced errors from manual processes
- Better tracking and visibility
- Standardized documentation
- Faster communication with automation team

**Implementation effort**: ~1 hour to configure workflow, test with 2-3 issues

**ROI**: With 50+ test cases to fix, saves ~75-100 hours of PE time
