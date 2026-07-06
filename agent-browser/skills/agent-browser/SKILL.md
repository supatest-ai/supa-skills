---
name: agent-browser
description: Use Agent Browser for browser automation. Trigger when the user asks to open a website, click, type, fill a form, take screenshots, record video, scrape page data, test a web app, verify UI behavior, log in to a site, or automate browser actions.
argument-hint: [browser-task]
---

# Agent Browser

Use the Agent Browser CLI for browser automation. Agent Browser ships its own current skill content, so this discovery skill should stay thin and delegate to the installed CLI whenever possible.

## When Not to Use

- Do not use for pure HTTP/API calls that can be done with `curl` or a project SDK.
- Do not use for unit, integration, or E2E test authoring without live browser interaction. Use `automate-e2e-tests` for test files.
- Do not use to bypass authentication, terms, permissions, or access controls.

## Load Current Instructions

First check whether the CLI is available:

```bash
agent-browser --version
```

If it is available, retrieve the current core instructions from the installed CLI:

```bash
agent-browser skills get core --full
```

If the command above is unsupported, use:

```bash
agent-browser skills list
agent-browser skills get core
```

Follow the CLI-served instructions for command syntax, references, templates, sessions, screenshots, video, selectors, and troubleshooting.

## Install or Repair

If Agent Browser is missing and installing tools is allowed in the environment, use the official install path:

```bash
npm i -g agent-browser
agent-browser install
```

If global installs are not allowed, use the project's documented toolchain or ask the user for the approved installation method. Do not install global tooling inside restricted enterprise environments without approval.

## Generic Workflow

When CLI-served instructions are unavailable, use this minimal workflow:

1. Open the target URL.
2. Wait for load or a specific UI condition.
3. Inspect the page with an accessibility/tree snapshot.
4. Prefer stable element refs, accessible roles, labels, and visible text over brittle CSS selectors.
5. Click, fill, type, scroll, or evaluate page state as needed.
6. Capture screenshots or video for user-facing validation.
7. Save and reuse named sessions when auth state matters.
8. Close or reset sessions when done.

Example:

```bash
agent-browser open http://localhost:3000
agent-browser wait --load networkidle
agent-browser snapshot -i
agent-browser click @e1
agent-browser fill @e2 "example"
agent-browser screenshot --annotate reports/agent-browser/step.png
```

Use a named session for longer flows:

```bash
agent-browser --session feature-test open http://localhost:3000
agent-browser --session feature-test snapshot -i
agent-browser --session feature-test screenshot reports/feature/step.png
```

## Evidence Rules

For testing and verification work:

- Capture evidence after meaningful state changes.
- Inspect screenshots and recordings before reporting success.
- Reject blank, black, wrong-route, stale-state, or unplayable evidence.
- Prefer video for multi-step flows, animations, auth, modal/sheet interactions, and navigation.
- Record exact commands and observed results in the calling workflow's report.

## Failure Handling

- **CLI missing:** install only when permitted; otherwise ask for the approved tool path.
- **Command syntax differs:** run `agent-browser skills get core --full` and follow the installed version.
- **Auth required:** use approved test credentials, saved state, seeded users, or ask the user to sign in. Do not invent credentials.
- **Stale refs:** take a fresh snapshot and use semantic locators when possible.
- **Screenshots or recordings fail:** retry once with a fresh named session, then document the blocker in the validation report.
- **Page behaves unexpectedly:** capture the URL, screenshot, console/network evidence if available, and hand findings back to `test-feature`.

## Source

Generic starter from Supatest AI supa-skills `agent-browser` v1.0.0. It intentionally keeps the familiar skill name while delegating detailed instructions to the installed Agent Browser CLI `core` skill so usage stays aligned with the local CLI version.
