---
name: task-to-pr
description: "This skill should be used when the user asks to take a task, ticket, bug, or feature end to end: understand, plan, implement, validate, commit, self-review, push, and open a PR. Do not use for pure review, commit-only, or workflow configuration."
argument-hint: [requirement-or-ticket]
---

# Task to PR

Drive a requirement from understanding to implementation, validation, commit, self-review, branch push, and pull request. This is the generic starter skill. In real projects, run `setup-task-to-pr` first so this skill can be enriched with local commands and delivery rules.

## When Not to Use

- Do not use for pure code review. Use `review-pr`.
- Do not use for committing already-finished work only. Use `commit`.
- Do not use for only browser-testing a completed feature. Use `test-feature`.
- Do not use when the user asks to set up the workflow for a repo. Use `setup-task-to-pr`.

## Delivery Contract

Before opening or marking a PR ready:

- The requirement and assumptions are captured.
- The likely files and ownership boundaries are understood.
- Non-trivial work has a short plan.
- The implementation covers the happy path, important unhappy paths, and recovery states.
- Relevant validation lanes have run, or each skipped lane has a documented reason.
- User-facing behavior has feature validation evidence when applicable.
- Durable E2E coverage was added or deliberately skipped with a reason when browser/mobile integration behavior changed.
- Only task-scoped files are staged and committed.
- The branch is suitable for review.
- The PR body names the problem, changes, testing, edge cases, compatibility, risk, and rollback.

## Phase 1 - Understand

1. Read the user requirement, linked ticket, issue, plan, or branch context.
2. Inspect repo instructions before editing:
   ```bash
   rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'CONTRIBUTING*' -g 'README*' -g 'docs/**'
   ```
3. If project-local skills exist, read the relevant local versions first:
   ```bash
   find .agents/skills .claude/skills .codex/skills -maxdepth 3 -name SKILL.md 2>/dev/null | sort
   ```
4. Inspect likely entry points with `rg`, `rg --files`, and focused file reads.
5. Record the starting point:
   ```bash
   git status --short
   git branch --show-current
   git rev-parse --short HEAD
   ```
6. If the worktree is dirty, track task-scoped touched files explicitly. Never rely on broad staging.

Ask one focused question only when ambiguity changes the implementation or creates safety risk. Otherwise state assumptions and proceed.

## Phase 2 - Plan

For non-trivial work, create a concise plan in the location the project uses for notes, task artifacts, or temporary docs. If no convention exists, keep the plan in chat or create `notes/<slug>-plan.md` only when the repo already uses `notes/`.

The plan should include:

- Requirement and assumptions.
- Files likely to change.
- Implementation order.
- Validation lanes to run: lint, format, typecheck/compile, unit, integration, E2E, build/package, security, accessibility, performance, feature validation, or project-specific checks.
- Feature validation decision.
- Durable E2E decision.
- Compatibility and risk notes.

Do not over-plan tiny edits. For tiny work, keep the plan in the PR body.

## Phase 3 - Implement

1. Follow the most specific project instructions and local skill guidance.
2. Keep the write set narrow.
3. Prefer existing patterns, helpers, test fixtures, and framework conventions.
4. Run narrow checks while editing when available.
5. Keep a touched-file list if unrelated worktree changes exist.

If implementation exposes stale instructions or missing tooling, patch the narrowest durable layer in the same change when appropriate.

## Phase 4 - Validate

Run the smallest meaningful validation for the touched surface and risk level. Treat lint, typecheck/compile, unit tests, integration tests, E2E tests, build/package checks, security checks, accessibility checks, and feature validation as separate validation lanes.

Prefer the project's configured commands. If the project has not been configured yet, discover likely commands:

```bash
npm run
pnpm run
yarn run
npm run test
npm run lint
npm run typecheck
npm run build
pnpm test
pnpm lint
yarn test
pytest
go test ./...
cargo test
mvn test
./gradlew test
```

Use this default validation matrix until a project-local `task-to-pr` skill replaces it:

| Change Type | Expected Validation Lanes |
|---|---|
| Docs-only | docs lint or link check if available; otherwise `git diff --check` |
| Formatting/config | formatter/lint check plus the narrow config validation command |
| Pure logic | lint, typecheck/compile, focused unit tests |
| Shared package/library | lint, typecheck/compile, focused unit tests, affected consumer compile/typecheck when practical |
| UI component or screen | lint, typecheck/compile, unit/component tests when available, feature validation for visible behavior |
| API route/service | lint, typecheck/compile, focused unit tests, integration or contract tests |
| Database/schema/migration | migration generation/validation, integration tests, rollback or compatibility notes |
| Auth, permissions, billing, or security | focused unit and integration tests, feature validation, security review notes, negative-path checks |
| Mobile app | lint/typecheck/compile, focused unit tests, simulator/device checks when configured |
| Desktop app | compile/package check plus the project's desktop smoke or integration check |
| Dependencies/build tooling | install/lockfile validation, lint/typecheck/build or CI-equivalent check when practical |

For each relevant lane, record:

- Command run.
- Scope: focused, package/app-specific, or full suite.
- Result: pass, fail, mixed, blocked, or skipped.
- Evidence path when the command produces artifacts.
- Reason for any skipped or blocked lane.

Do not run expensive, flaky, destructive, production-affecting, or externally visible commands unless the local skill or user explicitly permits them. When a required lane is unsafe or unavailable, document the exact blocker and remaining risk.

For user-facing behavior, use `test-feature` or the configured surface-specific testing skill. It should exercise the real flow, capture evidence, and produce a validation report.

After feature validation, use `automate-e2e-tests` when the behavior needs durable regression coverage. Skip E2E only with a documented reason such as existing coverage, lower-level tests being better, no user-visible behavior, or missing safe infrastructure.

## Phase 5 - Commit and Review

1. Review the diff:
   ```bash
   git status --short
   git diff -- <task-scoped-files>
   ```
2. Create or switch to a task branch if the project expects feature branches.
3. Use `commit` for the scoped commit. If unavailable, stage explicit task files only:
   ```bash
   git add <file-1> <file-2>
   git commit -m "feat: <summary>"
   ```
4. Use `review-pr` for self-review when the change is non-trivial, security-sensitive, or cross-cutting.

Never use `git add .`, `git add -A`, force push, destructive resets, or one-side conflict resolution unless the user explicitly authorizes the exact action.

## Phase 6 - Pull Request

Push the branch only when project policy allows it:

```bash
git push -u origin <branch>
```

Open a PR with the local tool if available, commonly:

```bash
gh pr create
```

Default PR body:

```md
## Problem

## Requirement

## Changes

## Testing

## Edge Cases

## Compatibility

## Risk and Rollback

## Self-Review
```

Include links or paths to validation reports, screenshots, video, test output, or other evidence.

## Phase 7 - CI Follow-Up

If CI access is available after opening or updating the PR:

1. Inspect required check status with the project's PR tool or CI dashboard.
2. If checks pass, record that in the closeout.
3. If checks fail, classify each failure as product, test, environment, dependency, permission, or unrelated existing failure.
4. Fix product or test failures introduced by this task, then rerun the narrowest relevant command locally before pushing an update.
5. Do not chase broad flaky-suite, infrastructure, permission, or unrelated failures without user approval. Document exact failing checks and next action.

## Closeout

Report:

- PR URL or branch name.
- Commit SHA.
- Commands run and results.
- Feature validation report path when applicable.
- E2E coverage added, updated, already covered, skipped, or blocked.
- Remaining risks.

## Source

Generic starter from Supatest AI supa-skills `task-to-pr` v1.0.2. Run `setup-task-to-pr` in each project to create a local enriched version.

## Self-Improvement

If this workflow misses a required validation gate, PR rule, CI behavior, or delivery artifact during real use, patch this skill or the configured project-local version before closing.
