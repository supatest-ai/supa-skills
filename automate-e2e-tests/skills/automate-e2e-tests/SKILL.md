---
name: automate-e2e-tests
description: This skill should be used when the user asks to add or update durable E2E, integration, contract, browser, mobile, API, routing, auth, or multi-service regression tests after a feature is validated. Do not use for manual QA only.
argument-hint: [feature-or-validation-report]
---

# Automate E2E Tests

Turn a validated behavior into durable regression coverage using the project's E2E, integration, contract, or mobile test framework. This is a generic starter skill; project teams should run `setup-task-to-pr` to enrich it with exact paths, commands, fixtures, auth, device setup, and CI rules.

## When Not to Use

- Do not use for manual QA, screenshots, video, or validation reports only. Use `test-feature`.
- Do not use for broad flaky-suite repair or skip audits unless the user asks for suite maintenance.
- Do not use when unit, component, API, parser, validator, or contract tests are the better level of coverage.
- Do not add E2E tests for docs-only or internal refactors with no user-observable behavior.

## Inputs

Before editing tests, read:

1. The requirement or ticket.
2. The implementation diff.
3. The feature validation report from `test-feature` or the configured testing skill, if present.
4. Existing E2E configs, specs, fixtures, and helpers.
5. Project test instructions.

Discover common frameworks:

```bash
rg --files -g 'playwright.config.*' -g 'cypress.config.*' -g 'wdio.conf.*' -g 'nightwatch.conf.*' -g 'detox.config.*' -g 'maestro.yaml' -g '.maestro/**' -g 'package.json' -g 'pom.xml' -g 'build.gradle*'
find . -maxdepth 4 -type d \( -name e2e -o -name cypress -o -name playwright -o -name specs -o -name tests -o -name maestro \) 2>/dev/null | sort
```

If no E2E framework exists, do not introduce one without user approval. Document the coverage gap and suggest the smallest viable framework choice.

## Coverage Decision

Add or update E2E coverage when:

- Auth, routing, browser/mobile UI, persistence, realtime behavior, payments, onboarding, checkout, permissions, or multi-service integration is the thing being protected.
- A core user journey changed.
- A bug reproduction needs a full-stack regression test.
- The project already has nearby E2E coverage for the same surface.

Prefer lower-level tests, with a documented reason, when:

- The behavior is pure calculation, parsing, validation, formatting, or data mapping.
- The E2E setup would be brittle because required test data, auth, or environments are missing.
- Equivalent E2E coverage already exists.
- The change is not user-observable.

## Authoring Flow

1. Identify the smallest durable journey from the validation report or requirement.
2. Search existing specs before creating new files:
   ```bash
   rg -n "<route|feature words|button text|test id|domain term>" .
   ```
3. Reuse existing fixtures, auth helpers, page objects, seed data, server setup, device setup, and test utilities.
4. Update an existing spec when it already owns the behavior.
5. Create a new spec only in the closest established E2E folder.
6. Prefer accessible roles, labels, and visible text. Add stable test selectors only when the UI needs a durable test contract.
7. Assert user-visible outcomes and persisted state. Do not assert private implementation details.
8. Cover the changed happy path and at least one meaningful failure, boundary, or recovery path when practical.
9. Keep the test deterministic. Avoid broad sleeps unless the existing suite has a scoped settle helper and no better signal exists.

## Surface Guidance

| Surface | Guidance |
|---|---|
| Web/PWA | Prefer existing Playwright, Cypress, WebdriverIO, or framework-specific browser tests. Reuse auth storage and fixture setup. |
| Native mobile | Prefer existing Appium, Detox, Maestro, XCUITest, Espresso, or project simulator/device harness. Do not invent device setup. |
| API | Prefer integration or contract tests over browser E2E unless a UI flow is part of the requirement. |
| Desktop | Use the project's established desktop automation harness. If none exists, document the gap before adding tooling. |
| Monorepo | Place tests beside the app or in the established cross-app E2E package. |

## Validation

Run the narrowest focused command first. Examples:

```bash
npx playwright test path/to/spec
npx cypress run --spec path/to/spec
npm run e2e -- path/to/spec
pnpm e2e path/to/spec
yarn e2e path/to/spec
./gradlew connectedAndroidTest
xcodebuild test -scheme <scheme> -destination <destination>
maestro test path/to/flow.yaml
```

Use the command the project already documents. For new or meaningfully changed browser/mobile specs, repeat the focused test when practical to catch obvious flakes.

Run broader E2E or CI-equivalent checks only when touched helpers, fixtures, setup code, or shared flows make the focused run insufficient.

## Failure Handling

- **Spec exposes a product bug:** fix the product if in scope, then rerun the focused spec.
- **Spec is flaky:** tighten selectors, setup, waits, data isolation, or assertions. If this becomes broad suite repair, stop and report that the task has changed.
- **Missing fixture/auth/device support:** add the narrowest reusable support if safe; otherwise document the blocker.
- **No approved E2E framework:** ask before introducing one.
- **Environment unavailable:** record exact command, error, and unverified risk in the PR/testing notes.

## Artifacts

Success produces one of:

- A new or updated E2E spec/flow.
- A new or updated integration or contract test when that is the right regression layer.
- A narrow fixture/helper update required by that spec.
- A documented E2E coverage exception with the alternate coverage used.

Report the exact files changed, command run, pass/fail result, and remaining risk.

## Source

Generic starter from Supatest AI supa-skills `automate-e2e-tests` v1.0.1. Run `setup-task-to-pr` in each project to create a local enriched version.

## Self-Improvement

If this skill chooses the wrong regression layer, misses a project test framework, or creates brittle tests, patch this skill or the configured project-local version before closing.
