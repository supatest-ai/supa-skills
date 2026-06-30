---
name: test-feature
description: Interactively test a completed feature using browser automation. Navigates the live app, exercises all key flows, captures a GIF video of the happy path, and produces a visual verification report. Use after implementing a new feature or making code changes that need testing verification.
argument-hint: [feature-description]
---

# Test Feature

Use this skill when you have finished implementing a feature and want to verify it works correctly through live browser testing with a recorded video report.

## When to Use

Invoke this skill AFTER you have:
- Completed implementing a new feature
- Made code changes that need testing verification
- Want a visual walkthrough with screenshots and a recorded GIF for stakeholders

## What This Skill Does

This skill uses the **agent-browser** skill to drive a real browser session against your running application:

1. **Understands the feature** from your description and any plan/spec files
2. **Navigates the live app** to locate the feature under test
3. **Exercises all key flows** — happy path, edge cases, and error states
4. **Records a GIF** of the complete happy-path walkthrough
5. **Captures screenshots** at each significant UI state
6. **Generates a REPORT.md** with all artifacts and a pass/fail summary

## Prerequisites

Before invoking this skill, ensure:
1. The application is running and accessible in the browser (note the URL)
2. You are logged in or test credentials are available
3. The feature you want to test is deployed/served locally

## Your Task

When this skill is invoked, follow these steps:

### Step 1 — Understand the Feature

Read the feature description provided by the user. If a plan file or spec is referenced, read it. Summarize:
- What the feature does
- The key flows to test (happy path + edge cases)
- Where in the app it lives (URL, page, component)

### Step 2 — Start the Browser Session

Invoke the **agent-browser** skill to open the application and navigate to the feature:

```
Use agent-browser to:
- Open the app at <URL>
- Navigate to the page/section containing the feature
- Take an initial screenshot to confirm the starting state
```

### Step 3 — Start GIF Recording

Before exercising any flows, start recording a GIF that will capture the full walkthrough:

```
Use agent-browser to start a GIF recording named "<feature-slug>-walkthrough.gif"
```

Keep recording throughout all steps below. Capture extra frames before and after each interaction for smooth playback.

### Step 4 — Exercise All Flows

Work through each flow systematically, taking a screenshot after each significant state change:

**Happy Path (always first):**
- Walk through the primary intended user flow from start to finish
- Verify all expected UI states, data, and feedback appear correctly

**Edge Cases:**
- Empty states, boundary values, optional fields left blank
- Actions in unexpected order (if applicable)

**Error States:**
- Invalid inputs, missing required fields
- Network-level errors if you can simulate them

For each flow, note: what was tested, what was observed, pass or fail.

### Step 5 — Stop GIF Recording

After completing the happy-path walkthrough, stop the GIF recording and save the file.

### Step 6 — Generate the Report

Create a `REPORT.md` in the project root or a `reports/` directory:

```markdown
# Feature Test Report: <Feature Name>

**Date:** <today's date>
**App URL:** <url tested>
**Status:** PASS / FAIL / PARTIAL

## Summary

<1-3 sentence summary of what was tested and overall result>

## Feature Description

<what the feature does>

## Test Results

### Happy Path
- [ ] <flow step 1> — PASS/FAIL
- [ ] <flow step 2> — PASS/FAIL
...

### Edge Cases
- [ ] <edge case> — PASS/FAIL
...

### Error States
- [ ] <error state> — PASS/FAIL
...

## Screenshots

| Step | Screenshot | Notes |
|------|-----------|-------|
| <step name> | ![step](<path>) | <observation> |
...

## Happy Path Video

![Walkthrough](<feature-slug>-walkthrough.gif)

## Issues Found

<List any bugs, UX issues, or unexpected behavior. If none, state "No issues found.">

## Files Changed

<List the key files that implement this feature, if known>
```

### Step 7 — Report to the User

Tell the user:
- Overall pass/fail status
- Where the report is saved
- Any issues found
- A direct path to the GIF recording

## How to Describe the Feature

Give the skill a rich, contextual description. Include:

### 1. Feature Name and Location
```
"The date range picker on the Test Runs page"
```

### 2. Key Flows to Test
```
- Default 7-day range is pre-selected
- Preset buttons: Today, Yesterday, Last 7 days, Last 30 days
- Custom date range via calendar picker
- Table and stats update when date range changes
```

### 3. App URL
```
"App is running at http://localhost:3000"
```

### 4. Files Changed (optional, for context)
```
- frontend/src/pages/runs.tsx
- api/src/controllers/runs.controller.ts
```

## Example Invocations

```
/test-feature The new user onboarding modal — app at http://localhost:3000.
Flows: first-time user sees modal on login, can skip or complete steps,
progress is saved, modal doesn't show again after completion.
```

```
/test-feature Stripe checkout — http://localhost:3000/checkout.
Happy path: add item, enter card 4242 4242 4242 4242, complete purchase,
see confirmation. Edge cases: declined card, empty cart checkout attempt.
```

## Output Location

Reports are saved to:
```
reports/<feature-slug>/
├── REPORT.md                        # Main report
├── screenshots/
│   ├── 01-initial-state.png
│   ├── 02-<step>.png
│   └── ...
└── <feature-slug>-walkthrough.gif   # Happy path video
```

## Integration with Development Workflow

```
1. Plan the feature
2. Implement the feature
3. Commit the changes
4. [INVOKE THIS SKILL] → Browser automation tests the live feature
5. Review the generated report and GIF
6. Share report with team as a verification artifact
```
