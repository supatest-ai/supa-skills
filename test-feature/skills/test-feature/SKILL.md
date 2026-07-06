---
name: test-feature
description: Interactively test a completed user-facing feature. Use when the user asks to QA, dogfood, browser-test, mobile-test, verify, produce screenshots/video evidence, or create a feature validation report after implementation.
argument-hint: [feature-description]
---

# Test Feature

Validate a finished or nearly finished feature through the real product surface, capture evidence, and write a local HTML report. This is the human-facing QA workflow. Use `agent-browser` for low-level browser mechanics and `automate-e2e-tests` when the validated behavior needs durable regression coverage.

This is the generic starter skill. In real projects, run `configure-task-to-pr` first so this skill can be enriched with local URLs, auth, devices, commands, report paths, and surface-specific rules.

## When Not to Use

- Do not use before the feature is implemented enough to exercise.
- Do not use for pure API checks without user-facing behavior unless the project has no UI; configure `test-api-feature` if API validation is common.
- Do not use for authoring automated E2E tests. Use `automate-e2e-tests`.
- Do not use for low-level browser operation alone. Use `agent-browser`.
- Do not use for broad flaky-suite repair or test infrastructure cleanup.

## Inputs

Read:

1. The feature description, ticket, plan, or PR diff.
2. Project-local testing skills if present.
3. App instructions for local URLs, auth, seed data, devices, simulators, or test environments.
4. Existing validation reports or bug reproduction notes if this is a retest.

If the app URL, credentials, device, or environment is not discoverable, ask one concise question before testing.

## Surface Selection

Use the surface that matches the feature:

| Surface | Validation approach |
|---|---|
| Web/PWA | Use Agent Browser, Playwright, Chrome, or the project's browser tool. |
| Native mobile | Use the project's simulator, emulator, device, Appium, Detox, Maestro, XCUITest, Espresso, or manual/device harness. |
| Desktop | Use the project's desktop automation or manual launch/check process. |
| API-only | Exercise the API with the approved client and record request/response evidence. |
| Monorepo | Test the app or package that owns the changed behavior. |

If a repo has meaningfully different validation machinery for web, mobile, API, or desktop, recommend running `configure-task-to-pr` to split this into surface-specific local skills.

## Validation Plan

Before interacting with the app, define:

- Requirement being tested.
- Environment and URL/device/API endpoint.
- Auth/test data path.
- Happy path.
- Important edge cases.
- Error or recovery states.
- Evidence to capture.
- Pass/fail criteria.

Do not stop at a nearby page, component preview, or partial state when the requested behavior is a workflow.

## Evidence Directory

Use the project's configured report location when available. Otherwise use:

```text
reports/<feature-slug>/
```

Recommended structure:

```text
reports/<feature-slug>/
├── index.html
├── screenshots/
│   ├── 01-initial-state.png
│   └── 02-after-action.png
├── videos/
│   └── flow.webm
└── logs/
    └── commands.txt
```

Use relative links in the HTML report so the folder can be attached to a ticket or PR.

## Exercise the Feature

1. Prove the environment is reachable.
2. Establish auth using approved test credentials, seeded users, saved state, or manual sign-in. Do not invent credentials.
3. Execute the happy path first.
4. Exercise edge cases that are natural for the feature: empty states, optional fields, boundary values, permissions, repeated actions, navigation away/back, slow loading, or missing data.
5. Exercise error and recovery states when safe: invalid input, server rejection, offline/network failure if the project supports simulation, retry, cancel, undo, or validation errors.
6. Capture evidence after each meaningful state change.
7. Inspect the evidence before declaring success.
8. Record exact commands, tools, URLs, devices, and observed results.

For browser validation, invoke `agent-browser` when available. If Agent Browser is not available, use the project's browser tool or Playwright/Chrome/in-app browser integration.

Reject evidence that is blank, black, stale, wrong-route, too cropped to prove the behavior, or unplayable.

## Status Model

Use one of:

- `pass`: the validated behavior meets the requirement and evidence proves it.
- `fail`: the behavior does not meet the requirement.
- `mixed`: core behavior works but some paths, evidence, tooling, or environment coverage is incomplete.
- `blocked`: validation cannot proceed because required environment, credentials, data, tooling, or approvals are missing.

Do not mark `pass` if important evidence is missing.

## HTML Report

Create a self-contained HTML report at:

```text
reports/<feature-slug>/index.html
```

The report must include:

- Title and date.
- Requirement or bug summary.
- Git branch and commit SHA if available.
- Status: `pass`, `fail`, `mixed`, or `blocked`.
- Environment: URL, app, API, device, simulator, browser/tool, auth path.
- Commands run and results.
- Step-by-step journey with expected and actual outcomes.
- Screenshots, video, logs, traces, or request/response evidence using relative links.
- Issues found.
- Fixes applied during validation, if any.
- Remaining risks and untested paths.
- E2E coverage decision: created, updated, already covered, not applicable, or blocked.

Minimal report template:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Feature Validation: FEATURE</title>
  <style>
    body { font: 14px/1.6 system-ui, sans-serif; max-width: 960px; margin: 0 auto; padding: 24px; color: #172033; background: #f7f8fb; }
    h1 { font-size: 24px; margin: 0 0 4px; }
    h2 { font-size: 16px; margin-top: 28px; border-bottom: 1px solid #d9deea; padding-bottom: 6px; }
    .meta { color: #5e6a7d; font-size: 13px; margin-bottom: 16px; }
    .status { display: inline-block; border-radius: 999px; padding: 4px 12px; font-weight: 700; }
    .pass { background: #dcfce7; color: #166534; }
    .fail { background: #fee2e2; color: #991b1b; }
    .mixed { background: #fef3c7; color: #92400e; }
    .blocked { background: #e5e7eb; color: #374151; }
    table { width: 100%; border-collapse: collapse; background: white; border: 1px solid #d9deea; }
    th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #e8ecf3; vertical-align: top; }
    th { font-size: 12px; text-transform: uppercase; color: #5e6a7d; background: #eef2f7; }
    img, video { max-width: 100%; border: 1px solid #d9deea; border-radius: 6px; background: white; }
    .evidence { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }
    .card { background: white; border: 1px solid #d9deea; border-radius: 8px; padding: 12px; }
    code { background: #eef2f7; padding: 1px 4px; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Feature Validation: FEATURE</h1>
  <div class="meta">Date: DATE | Branch: BRANCH | Commit: SHA</div>
  <div class="status pass">PASS</div>

  <h2>Summary</h2>
  <p>SUMMARY</p>

  <h2>Environment</h2>
  <table>
    <tr><th>Item</th><th>Value</th></tr>
    <tr><td>URL / Device</td><td>VALUE</td></tr>
    <tr><td>Tool</td><td>VALUE</td></tr>
    <tr><td>Auth</td><td>VALUE</td></tr>
  </table>

  <h2>Journey</h2>
  <table>
    <tr><th>Flow</th><th>Expected</th><th>Observed</th><th>Status</th></tr>
    <tr><td>Happy path</td><td>EXPECTED</td><td>OBSERVED</td><td>pass</td></tr>
  </table>

  <h2>Evidence</h2>
  <div class="evidence">
    <div class="card">
      <a href="screenshots/01-initial-state.png"><img src="screenshots/01-initial-state.png" alt="Initial state"></a>
      <p>Initial state.</p>
    </div>
  </div>

  <h2>Commands</h2>
  <pre><code>COMMANDS</code></pre>

  <h2>Issues and Risks</h2>
  <p>ISSUES_OR_NONE</p>

  <h2>E2E Coverage Decision</h2>
  <p>DECISION</p>
</body>
</html>
```

## Handoff to E2E

After the report is written, invoke `automate-e2e-tests` when:

- The feature is a core user journey.
- The bug fix needs regression protection.
- Auth, routing, persistence, mobile/browser behavior, or multi-service integration is the risk.
- The project already has a suitable E2E framework.

Skip E2E with a documented reason when lower-level tests are better, equivalent coverage exists, no user-visible behavior changed, or the environment is not safe/available.

## Failure Handling

- **Environment unavailable:** record exact URL/device/command and mark `blocked`.
- **Auth unavailable:** ask for approved credentials or manual sign-in; do not invent credentials.
- **Tooling unavailable:** use an approved fallback or mark `blocked` with setup instructions.
- **Bug found:** capture evidence, fix if in scope, rerun the failed path, and record before/after.
- **Evidence capture fails:** retry once with a fresh session/tool, then mark `mixed` unless the behavior can be proven another way.
- **Unsafe test path:** do not perform destructive, paid, production, or externally visible actions unless explicitly approved.

## Final Response

Report:

- Overall status.
- Report path.
- Evidence captured.
- Issues found.
- E2E coverage decision.
- Remaining risk.

## Source

Generic starter from Supatest AI supa-skills `test-feature` v1.1.0. Run `configure-task-to-pr` in each project to create a local enriched version.
