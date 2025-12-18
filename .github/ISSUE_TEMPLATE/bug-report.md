---
name: 🐛 Bug Report
about: Report a bug in existing code that needs to be resolved
title: "[BUG] - [Brief Description]"
labels: "A-Bug 🐛", "T-Non-Functional Testing 🧪"
assignees: ""
---

## Bug Description

Brief description of the issue and its impact:

---

## Environment

**Reproducible In:** (check all that apply)

- [ ] Velocity SaaS Production
- [ ] Velocity SaaS Dev
- [ ] Velocity SaaS QA (Build #______)
- [ ] Velocity Enterprise (Build #______)

**Component/Feature:** Feed | Output | Tools | Layers | Real-time Analytics | Big Data Analytics | Sources | Other

---

## Steps to Reproduce

1. [First step]
2. [Second step]
3. [Third step]
4. [Additional steps as needed]

**Credentials Used:** [Specify account/credentials if relevant]

---

## Expected Behavior

What should happen:

---

## Actual Behavior

What actually happens:

---

## Configuration

<details>
<summary>Repro Configuration (if applicable)</summary>

```json
{
  "paste": "your config here"
}
```

</details>

---

## Evidence

**Screenshots/Videos:** [Attach or link]

**Network Traffic/Pod Logs:** [Paste relevant logs]

**Error Messages:** [Include specific error text]

---

## Impact & Workaround

**Impact/Risks:**
- [Describe impact on users/system]
- [List risks of not addressing]

**Workaround:** [Describe any temporary workaround, or state "None"]

---

## Acceptance Criteria

- [ ] [Specific testable criteria #1]
- [ ] [Specific testable criteria #2]
- [ ] [Specific testable criteria #3]

---

## Design & Documentation Needs

**Frontend/Backend Design Session Required?**
- [ ] Yes
- [ ] No

**Documentation Updates Required?**
- [ ] Yes - PBI #______ logged
- [ ] No

**BYS Ticket Required?**
- [ ] Yes - PBI #______ logged
- [ ] No

**Team Wiki/Content Updates Required?**
- [ ] Yes - [Specify what needs updating]
- [ ] No

---

## Related Issues

- Related to: #[issue number]
- Blocks: #[issue number]
- Blocked by: #[issue number]

---

## FOR DEV: Fix Implementation & Testing Instructions

> **Developers:** Complete this section when fixing the bug. This helps testers verify your changes.

### Changes Made

**What was changed:**
- [ ] [Specific code change #1]
- [ ] [Specific code change #2]
- [ ] [Configuration change #1]

**Files Modified:**
- `path/to/file1.py`
- `path/to/file2.ts`

**Root Cause:**
[Brief explanation of what caused the bug]

---

### How to Test This Fix

**Test Environment:** DEV | QA | Production

**Prerequisites:**
- [Required data/credentials]
- [Required configuration]
- [Any setup steps]

**Verification Steps:**
1. [Specific step to verify fix #1]
2. [Specific step to verify fix #2]
3. [Expected result]

**Test Data/Credentials:**
- Data Source: [Link or location]
- Test Account: [Specify if different from repro]

**Expected Results After Fix:**
- [ ] [Specific observable outcome #1]
- [ ] [Specific observable outcome #2]
- [ ] [Original bug no longer reproduces]

---

### Regression Testing

**Areas to Regression Test:**
- [ ] [Related feature #1 - specify test]
- [ ] [Related feature #2 - specify test]
- [ ] [Any downstream dependencies]

**Negative Testing:**
- [ ] [Edge case #1 to verify]
- [ ] [Edge case #2 to verify]

---

## Testing & Automation Updates

**Functional Automation Test Case Required?**
- [ ] Yes - TestRail Case: C______ (update existing)
- [ ] Yes - New test case needed (create PBI)
- [ ] No

**Heimdall/Backend Test Updates Required?**
- [ ] Yes - [Specify test file/location]
- [ ] No

**Certification Tests Required?**
- [ ] Yes - [Specify certification scenario]
- [ ] No

---

## Verification Sign-Off

**Developer Verification:**
- [ ] Fix implemented and unit tested
- [ ] Testing instructions provided above
- [ ] PR linked: #______

**QA/PE Verification:**
- [ ] Reproduced original bug
- [ ] Verified fix using dev's test steps
- [ ] Completed regression testing
- [ ] Verified in environment: ______

**Follow-up PBIs Created:**
- [ ] PBI #______ - [Description]
- [ ] None needed

---

## Notes

[Additional context, technical details, or considerations]
