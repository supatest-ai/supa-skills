---
name: test-feature
description: Interactively test a completed feature using browser automation. Navigates the live app, exercises key flows, captures screenshots, and produces an HTML verification report.
argument-hint: [feature-description]
---

# Test Feature

Use this skill when you have finished implementing a feature and want to verify it works correctly through live browser testing with a visual HTML report.

## When to Use

Invoke this skill AFTER you have:
- Completed implementing a new feature
- Made code changes that need testing verification
- Want a visual walkthrough with screenshots for stakeholders

## What This Skill Does

1. **Understands the feature** from your description and any plan/spec files
2. **Navigates the live app** to locate the feature under test
3. **Exercises all key flows** — happy path, edge cases, and error states
4. **Captures screenshots** at each significant UI state
5. **Generates an HTML report** with all artifacts and a pass/fail summary

## Prerequisites

Before invoking this skill, ensure:
1. The application is running and accessible in the browser (note the URL)
2. You are logged in or test credentials are available
3. The feature you want to test is deployed/served locally

## Instructions

### Step 1 — Understand the Feature

Read the feature description provided by the user. If a plan file or spec is referenced, read it. Summarize:
- What the feature does
- The key flows to test (happy path + edge cases)
- Where in the app it lives

### Step 2 — Exercise All Flows

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

### Step 3 — Generate the HTML Report

Create a self-contained HTML report at `reports/<feature-slug>/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Feature Test Report: <Feature Name></title>
  <style>
    body { font: 14px/1.6 system-ui, sans-serif; max-width: 960px; margin: 0 auto; padding: 20px; background: #f8f9fa; color: #1a1a2e; }
    h1 { font-size: 24px; margin: 0 0 4px; }
    .meta { color: #6b7280; font-size: 13px; margin-bottom: 20px; }
    .status { display: inline-block; padding: 4px 16px; border-radius: 99px; font-weight: 700; font-size: 14px; margin-bottom: 20px; }
    .status.pass { background: #dcfce7; color: #16a34a; }
    .status.fail { background: #fef2f2; color: #dc2626; }
    .status.partial { background: #fef3c7; color: #d97706; }
    table { width: 100%; border-collapse: collapse; margin: 12px 0 20px; }
    th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }
    th { background: #f1f5f9; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #6b7280; }
    .pass-badge { color: #16a34a; font-weight: 600; }
    .fail-badge { color: #dc2626; font-weight: 600; }
    .screenshot-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; margin: 12px 0 20px; }
    .screenshot-card { background: white; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
    .screenshot-card img { width: 100%; display: block; }
    .screenshot-card .caption { padding: 8px 12px; font-size: 12px; color: #6b7280; }
    .issues { background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px 20px; margin: 12px 0 20px; }
    .section-title { font-size: 16px; font-weight: 700; margin: 24px 0 8px; padding-bottom: 6px; border-bottom: 2px solid #e5e7eb; }
  </style>
</head>
<body>

<h1>Feature Test Report: <Feature Name></h1>
<div class="meta">Date: <today> &middot; URL: <url tested></div>
<div class="status pass">PASS</div>
<!-- or <div class="status fail">FAIL</div> -->

<div class="section-title">Summary</div>
<p><1-3 sentence summary of what was tested and overall result></p>

<div class="section-title">Test Results</div>
<table>
  <tr><th>Flow</th><th>Step</th><th>Result</th></tr>
  <tr><td>Happy Path</td><td><step></td><td class="pass-badge">PASS</td></tr>
  <tr><td>Edge Case</td><td><empty state></td><td class="pass-badge">PASS</td></tr>
  <tr><td>Error State</td><td><invalid input></td><td class="fail-badge">FAIL</td></tr>
</table>

<div class="section-title">Screenshots</div>
<div class="screenshot-grid">
  <div class="screenshot-card">
    <img src="screenshots/01-initial-state.png" alt="Initial state" />
    <div class="caption">Initial state — feature loaded correctly</div>
  </div>
  <div class="screenshot-card">
    <img src="screenshots/02-action.png" alt="After action" />
    <div class="caption">After submitting form — validation shown</div>
  </div>
</div>

<div class="section-title">Issues Found</div>
<div class="issues">
  <p>No issues found.</p>
  <!-- or list bugs, UX issues, unexpected behavior -->
</div>

</body>
</html>
```

### Step 4 — Report to the User

Tell the user:
- Overall pass/fail status
- Where the report is saved
- Any issues found

## How to Describe the Feature

Include the feature name, location in the app, key flows to test, and the app URL:

```
/test-feature The new user onboarding modal — app at http://localhost:3000.
Flows: first-time user sees modal on login, can skip or complete steps,
progress is saved, modal doesn't show again after completion.
```

## Output Location

```
reports/<feature-slug>/
├── index.html                      # Main HTML report
└── screenshots/
    ├── 01-initial-state.png
    ├── 02-<step>.png
    └── ...
```
