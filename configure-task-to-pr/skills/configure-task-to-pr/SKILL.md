---
name: configure-task-to-pr
description: Configure a project-specific task-to-PR pipeline. Use when the user asks to set up, customize, bootstrap, adapt, or install the task-to-PR workflow for a repo, team, client project, enterprise codebase, web app, mobile app, API, desktop app, or monorepo.
argument-hint: [project/context]
---

# Configure Task to PR

Turn the generic Supatest AI task-to-PR skill suite into project-local skills that know the current repository's commands, validation gates, review rules, artifact paths, surfaces, and operational constraints.

This skill creates or updates local skills in the target project. It does not write a single central profile. Each configured skill should read like it was written for that project.

## When Not to Use

- Do not use for executing an implementation task. Use `task-to-pr`.
- Do not use for only committing current changes. Use `commit`.
- Do not use for only testing a finished feature. Use `test-feature`.
- Do not use for a one-off explanation of the workflow; explain the installed skills instead.

## Target Output

Create or update project-local skills under the first supported local skills directory:

1. `.agents/skills/<skill-name>/SKILL.md`
2. `.claude/skills/<skill-name>/SKILL.md`
3. `.codex/skills/<skill-name>/SKILL.md`

Prefer `.agents/skills` when the repo already uses it or has no established skill directory. Use the directory the project already documents if one exists.

Configure this stack by default:

- `task-to-pr`
- `test-feature`
- `automate-e2e-tests`
- `agent-browser`
- `commit`
- `review-pr`

Create surface-specific testing skills only when validation machinery truly differs:

- `test-web-feature`
- `test-mobile-feature`
- `test-ios-feature`
- `test-android-feature`
- `test-api-feature`
- `test-desktop-feature`

Split by tooling and evidence requirements, not by product labels. For example, a web app and PWA that both use Playwright can share `test-feature`; native iOS and Android apps usually deserve separate configured skills.

## Phase 1 - Inspect the Repository

Read the repo before asking questions.

Run focused discovery commands:

```bash
pwd
git status --short
rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'README*' -g 'CONTRIBUTING*' -g 'package.json' -g 'pnpm-workspace.yaml' -g 'turbo.json' -g 'nx.json' -g 'vite.config.*' -g 'next.config.*' -g 'playwright.config.*' -g 'cypress.config.*' -g 'pom.xml' -g 'build.gradle*' -g 'settings.gradle*' -g 'pyproject.toml' -g 'go.mod' -g '*.xcodeproj' -g '*.xcworkspace' -g 'Package.swift'
find . -maxdepth 3 -type d \( -name e2e -o -name tests -o -name test -o -name specs -o -name __tests__ \) 2>/dev/null | sort
```

Read the highest-signal files:

- Root agent or contributor instructions.
- Package manager scripts.
- Test configuration.
- PR template if present.
- Existing local skills if present.
- Mobile, desktop, API, or deployment docs when the repo suggests those surfaces.

Infer what is obvious before asking the team. Do not ask questions that can be answered from files.

## Phase 2 - Interview the Team

Ask only questions whose answers change the generated skills. Group questions so the user can answer in one pass.

Required questions:

1. What surfaces should this workflow support: web, PWA, API, iOS, Android, React Native, desktop, CLI, library, data pipeline, infrastructure, or monorepo?
2. Which commands prove correctness for this project: lint, format, typecheck, unit, integration, E2E, build, security scan, mobile simulator tests, contract tests, or other checks?
3. What commands are expensive, flaky, destructive, or require approval?
4. How should local feature validation work: app URL, auth path, test users, seed data, browser, device, simulator, emulator, or API client?
5. What evidence should a completed task produce: screenshots, video, HTML report, test logs, coverage, trace, accessibility output, deployment links, or ticket comments?
6. What does the PR body require: ticket link, problem, changes, tests, screenshots, risk, rollback, compatibility, security, accessibility, performance, observability, or release notes?
7. What branch, commit, and push rules apply: branch prefix, ticket ID in branch, conventional commits, signed commits, squash policy, no-push policy, or review before push?
8. What enterprise constraints apply: regulated data, client isolation, approval gates, no production access, migration guardrails, secrets policy, audit evidence, or security review?

Ask follow-up questions only for ambiguity that would make the skills unsafe or useless. If the user cannot answer, encode a runtime confirmation step in the relevant skill instead of guessing.

## Phase 3 - Choose the Skill Topology

Use this decision table:

| Situation | Configure |
|---|---|
| One primary product surface | `test-feature` only |
| Web and PWA share browser tooling | `test-feature` with surface sections |
| Web and native mobile have different tooling | `test-web-feature` plus `test-mobile-feature` or platform-specific skills |
| iOS and Android use different commands/devices | `test-ios-feature` and `test-android-feature` |
| API-only service | `test-api-feature`; keep `agent-browser` only if docs/admin UI exist |
| Library/package | no browser testing skill unless examples/docs UI exists |
| Monorepo with independent apps | `task-to-pr` routes by touched surface; split test skills when commands differ |

Keep the first configuration small enough to use. Add split skills when the team names a concrete command, tool, or evidence requirement that differs by surface.

## Phase 4 - Write Project-Local Skills

For each local skill, write a complete coherent `SKILL.md`. Do not append a vague "Project Overrides" section to a generic body.

Each skill must include:

- Frontmatter with `name`, `description`, and optional `argument-hint`.
- Clear trigger and anti-trigger behavior.
- Project contract: stack, surfaces, and assumptions.
- Exact commands and paths, with fallbacks only where needed.
- Required evidence and report location.
- Failure handling with concrete next actions.
- Self-improvement instruction: if the workflow proves stale, patch the local skill.

Use these specialization rules:

- `task-to-pr`: orchestrates requirement, planning, implementation, validation, testing evidence, commit, self-review, push, and PR.
- `test-feature`: validates finished user-facing behavior and writes a feature validation report.
- `automate-e2e-tests`: turns validated behavior into durable regression coverage using the project's E2E framework.
- `agent-browser`: teaches browser mechanics for the available browser automation tool. If the Agent Browser CLI is standard, keep it thin and call `agent-browser skills get agent-browser --full` for current instructions.
- `commit`: encodes the project's commit, branch, staging, signing, and push policy.
- `review-pr`: encodes local review dimensions, severity model, and domain risks.

## Phase 5 - Preserve Upstream Provenance

Add a short provenance section near the bottom of generated local skills:

```md
## Source

Generated from Supatest AI supa-skills `<skill-name>` v<version> by `configure-task-to-pr`.
Project-specific behavior is intentionally local to this repository.
```

When updating an existing configured skill, preserve useful local knowledge. Replace stale commands, remove contradictions, and keep the source/version current.

## Phase 6 - Validate

After writing skills:

1. Confirm every generated skill has valid frontmatter starting on line 1.
2. Confirm each `name` matches its directory.
3. Confirm descriptions are specific enough to trigger correctly and not so broad that they steal unrelated tasks.
4. Run a syntax check that fits the repository:
   ```bash
   find .agents/skills .claude/skills .codex/skills -name SKILL.md 2>/dev/null | sort
   ```
5. Read each generated skill once after writing to catch contradictions.
6. If the repo has a skill validator, run it.

Do not run destructive project commands during configuration. Only run read-only inspection and safe validation unless the user explicitly approves more.

## Final Report

Report:

- Local skill directory used.
- Skills created or updated.
- Any split testing skills created and why.
- Commands and gates configured.
- Questions left for runtime confirmation.
- Any risks, missing credentials, unavailable tooling, or project docs that should be improved.
