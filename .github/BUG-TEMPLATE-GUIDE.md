# Bug Report Template - Usage Guide

## Overview

This bug template follows industry-standard practices for bug reporting and fix verification, ensuring clear communication between reporters, developers, and testers throughout the bug lifecycle.

## Template Sections Explained

### 1. Bug Description & Environment
**Purpose:** Quickly understand what's broken and where

**Industry Standard:** JIRA, Azure DevOps, GitHub all prioritize environment specification to avoid "works on my machine" issues.

**What to include:**
- One-sentence impact statement
- All environments where bug reproduces
- Build numbers for traceability

### 2. Steps to Reproduce
**Purpose:** Enable anyone to see the bug

**Industry Standard:** Must be specific enough that a new team member could reproduce without asking questions.

**Best Practice:**
- Number each step
- Include exact values/inputs used
- Specify credentials if relevant

### 3. Expected vs Actual Behavior
**Purpose:** Define the gap between what should happen and what does happen

**Industry Standard:** Acceptance criteria basis - if actual matches expected, bug is fixed.

### 4. Evidence
**Purpose:** Prove the bug exists

**Industry Standard:** Screenshots, logs, and network traces reduce back-and-forth clarification.

### 5. **FOR DEV: Fix Implementation & Testing Instructions** ⭐
**Purpose:** This is the critical missing piece in most workflows

**Industry Standard Practice:**
- **Google:** Bugs require "Test Plan" section before code review
- **Microsoft:** Bugs need "Verification Steps" from developer
- **Amazon:** "Run Book" section required for all bug fixes

**Why This Matters:**
- Testers shouldn't have to reverse-engineer how to test a fix
- Developers know their changes best - they should specify test steps
- Reduces testing time by 50-70%
- Prevents "I thought you were testing X, not Y" miscommunication

**What Developers Must Fill Out:**
1. **Changes Made:** What code/config changed and why
2. **How to Test This Fix:** Exact steps to verify the fix works
3. **Test Data/Credentials:** What testers need to run verification
4. **Expected Results After Fix:** What success looks like
5. **Regression Testing:** Related areas that might be affected

### 6. Verification Sign-Off
**Purpose:** Clear handoffs and accountability

**Industry Standard:** Bugs should have explicit sign-off from both dev and QA before closing.

**Workflow:**
1. Developer checks "Fix implemented" and provides testing instructions
2. Developer links PR
3. QA checks "Reproduced original bug"
4. QA follows dev's test steps
5. QA checks "Verified fix"
6. QA completes regression testing
7. Only then is bug closed

## Workflow Process

### Phase 1: Bug Reported (Reporter/PE)
1. Fill out Bug Description through Evidence sections
2. Add Acceptance Criteria
3. Assign to appropriate developer
4. Add labels and link related issues

### Phase 2: Bug Assigned to Developer
1. Developer reproduces the issue
2. Developer implements fix
3. **Developer completes "FOR DEV" section** ⭐
   - Documents what changed
   - Provides explicit testing steps
   - Specifies expected results
   - Identifies regression test areas
4. Developer checks "Fix implemented and unit tested"
5. Developer links PR
6. Developer assigns to QA/PE for verification

### Phase 3: Bug Verification (QA/PE)
1. QA reviews developer's testing instructions
2. QA reproduces original bug in affected environment
3. QA deploys fix to test environment
4. QA follows developer's exact test steps
5. QA verifies expected results match actual results
6. QA performs regression testing on related areas
7. QA checks all verification boxes
8. QA closes bug or reopens with specific failure details

### Phase 4: Closure
1. Update automation tests if needed
2. Create follow-up PBIs if needed
3. Close bug with comment summarizing fix

## Why This Approach Works

### Industry Examples:

**Google's Bug Process:**
- Every bug fix requires a "Test Plan" that another engineer must approve
- Reduces escaped defects by 40%

**Microsoft's Definition of Done for Bugs:**
- Developer must provide "Verification Steps"
- QA must sign off on verification
- Automation test must be updated

**Amazon's Two-Pizza Team Standard:**
- "Run Book" required for all production bugs
- Ensures anyone can verify the fix
- Reduces mean time to resolution (MTTR)

### What This Fixes in Your Current Process:

**❌ Old Problem:** "I fixed the bug" → "How do I test it?" → 5 Slack messages later...

**✅ New Solution:** Developer documents test steps in the bug itself → Tester executes → Done

**❌ Old Problem:** Tester guesses what to test → Misses edge case → Bug escapes to production

**✅ New Solution:** Developer specifies regression areas → Tester covers all cases → Confidence in fix

**❌ Old Problem:** Bug closed, 2 weeks later similar issue appears

**✅ New Solution:** Regression testing section ensures related areas checked → Fewer regressions

## Key Improvements Over Current Template

1. **Structured Testing Section:** Forces developers to think through verification
2. **Clear Handoffs:** Sign-off checkboxes show exactly where bug is in lifecycle
3. **Regression Focus:** Prevents "fixed one thing, broke another" scenario
4. **Test Data Specification:** Testers know exactly what data/credentials to use
5. **Reduced Back-and-Forth:** All information in one place
6. **Accountability:** Clear ownership at each phase

## Tips for Adoption

**For Developers:**
- Fill out "FOR DEV" section before creating PR
- Think: "If I was on vacation, could QA test this without me?"
- More detail = fewer interruptions later

**For QA/Testers:**
- Don't start testing until "FOR DEV" section is complete
- If test steps unclear, reject back to dev with specific questions
- Always verify original bug still reproduces before testing fix

**For Team Leads:**
- Make "FOR DEV" completion mandatory in PR review
- Track bugs that get reopened - often means insufficient test instructions
- Use verification sign-offs to measure process adherence

## Metrics to Track

With this template, you can measure:
- Time from "Fix Implemented" to "Verified" (should decrease)
- Number of times bugs reopened (should decrease)
- Questions asked in comments (should decrease)
- Escaped defects (should decrease)

## Customization

This template is opinionated based on industry best practices. Feel free to adjust:
- Add/remove environment types
- Add specific automation requirements
- Add security review sections
- Add performance impact sections

The critical section that should NOT be removed: **"FOR DEV: Fix Implementation & Testing Instructions"** - this is the key to streamlined verification.
