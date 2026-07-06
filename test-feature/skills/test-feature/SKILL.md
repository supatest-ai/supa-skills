---
name: test-feature
description: This skill should be used when the user asks to QA, dogfood, browser-test, mobile-test, verify, capture evidence, or create a validation report for a completed user-facing feature. Do not use for test-file authoring.
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

Use `references/report-template.html` as the starting point when the project does not already provide a validation report template.

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

Generic starter from Supatest AI supa-skills `test-feature` v1.1.1. Run `configure-task-to-pr` in each project to create a local enriched version.

## Self-Improvement

If this skill misses a required evidence type, surface, status, or report field during validation, patch this skill or the configured project-local version before closing.
