---
name: 🔧 Test Case Fix
about: Fix failing automated test cases identified in Grafana
title: "Maintenance: [TEST_ID] - [Test Title]"
labels: "QC–Automation (Maintenance)", "QC–Priority 1", "QC–ArcGIS Velocity"
assignees: ""
---

## Quick Links

**TestRail Case ID:** C12345

**Grafana Dashboard:** [Link to failing test in Grafana](http://grafana.example.com/...)

**TestRail Case:** [Link to test case](https://esri.testrail.com/index.php?/cases/view/12345)

**Allure Report:** [Link to latest failure](https://allure.example.com/...)

---

## Test Information

**Test Type:** ReadyAPI | Selenium BAT | Selenium E2E | Selenium FEED | Heimdall

**Environment:** DEV | QA | Both DEV and QA | Production

**Component/Feature:** Feed | Output | Tools | Layers | Real-time Analytics | Big Data Analytics | Sources | Other

---

## Failure Description

Brief description of what's failing (from Allure/Grafana):

```
Example: Test fails at step 3 - Expected 10 features but found 0 in output layer
```

---

## Preconditions

List any datasets, feeds, or test cases that must run before this one:

- C12340: Create sample dataset
- Requires HTTP Poller feed "test_feed_001"

---

## Changes Made in TestRail

Document what you updated in the test case:

- [ ] Updated test steps to use new data source
- [ ] Added precondition link to C12340
- [ ] Updated expected result to verify feature count
- [ ] Changed Type from "Automated - Future" to "Automated"
- [ ] Added Test Case Summary

---

## TestRail Checklist

- [ ] Test Case Type set to "Automated"
- [ ] Owner changed to yourself
- [ ] Preconditions field updated
- [ ] Test Case Summary added
- [ ] Steps rewritten for clarity (no shared steps)
- [ ] Expected Results include only necessary fields
- [ ] References field includes this GitHub issue
- [ ] Label "Precondition" added (if applicable)

---

## Action Required

**Select one:**
- [ ] Update automation in DEV and QA
- [ ] Skip test - missing resources
- [ ] Skip test - deprecated data source
- [ ] Product bug identified (link to PBI below)
- [ ] Needs Automation Team investigation

---

## Additional Context

Any other relevant information, screenshots, error logs, or related PBIs:

```
- Related PBIs or bugs
- Known limitations
- Special requirements
```

---

## What Happens Next

**Automation Team** will update test steps in both DEV and QA environments based on your TestRail changes.

**Watchers** (Yini, Eric, Manish) will be automatically added by workflow.

**Labels** for test type will be automatically added based on your selection.
