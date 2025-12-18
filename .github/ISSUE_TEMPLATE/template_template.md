---
name: Test Case Fix
about: Template for tracking and fixing failing automated test cases
title: "BATs Sources [COMPONENT] - fix automated tests"
labels: testing, automation
assignees: ""
---

## Description

[Provide a one-sentence description of what needs to be done]

**Component:** [e.g., HTTP Poller, WebSocket, Kafka, etc.]

---

## Test Cases

The following test cases are failing and need to be addressed:

- [Test Case ID/Name - Link to TestRail]
- [Test Case ID/Name - Link to TestRail]
- [Test Case ID/Name - Link to TestRail]

**Grafana Dashboard:** [Link to Grafana dashboard showing failures]

---

## Acceptance Criteria

- [ ] Review test failures in TestRail and automation results
- [ ] Determine root cause of failures (reach out to other PEs if needed)
- [ ] Update test case steps in TestRail to reflect correct behavior
- [ ] Verify test case Type status is set to "Automated" in TestRail
- [ ] Update Precondition field in TestRail (what is required before test execution)
- [ ] Update Test Summary field in TestRail (bulleted list of what test accomplishes)
- [ ] Notify automation team to update steps in Dev environment as well
- [ ] Validate fix by re-running test case with updated steps

---

## Next Steps

- [ ] Update corresponding Confluence page with latest test case information
  - **Confluence Page:** [Link to relevant Confluence page]
  - Format should match [this example](https://confluence.example.com/template)
- [ ] Export updated test cases and add them to Confluence page as a table
- [ ] Create PBI in automation repo with Priority 1 if automation updates needed
  - **Regression Repo Issue Creation:** [Link to create new issue]
- [ ] If test uses deprecated data sources (e.g., wss://geoeventsample1.esri...), change Type to "Automated (future)" and note in Test Summary

---

## Additional Details

- [Include any relevant information or context]
- [Add any screenshots or error messages if applicable]

---

## Resources

- **Grafana Dashboard - Test Case Result History:** [Link to Grafana]
- **TestRail Section:** [Link to TestRail section]
- **Automation Repo:** [Link to automation repository]
- **Office Hours:** Weekly Wednesday meetings for questions and status review
