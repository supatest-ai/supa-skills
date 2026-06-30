---
name: agent-readiness
description: Evaluate how ready a codebase is for autonomous AI agent work. Generates a scored report across 11 dimensions with a maturity level and prioritized action plan.
---

# Agent Readiness Assessment

Evaluate whether a repository gives an autonomous coding agent enough structure to take a task from spec to implementation to local verification without human hand-holding.

## Automated analysis (default)

This skill ships with analysis scripts in the `scripts/` directory. If Python 3 is available, use the **combined runner** for the full assessment including session-log pattern analysis:

```bash
# Full assessment (with session log analysis)
python3 scripts/run_readiness_check.py \
  --sessions-dir ~/.claude/projects/PROJECT-NAME \
  --repo .

# Static audit only (no session logs needed — fastest)
python3 scripts/run_readiness_check.py \
  --repo . \
  --skip-sessions \
  --output /tmp/agent-readiness-report.html
```

The output is an HTML report at `/tmp/agent-readiness-report.html` with maturity level, dimension scores, failure patterns, critical gaps, and a prioritized action plan.

### Session log analysis

When session logs are available (`.jsonl` files from Claude Code, Codex, Cursor, etc. in `~/.claude/projects/`), the analyzer detects:

- Classification distribution (research-only, validation-only, blocked, task-finisher, etc.)
- Top failed tools and commands
- Recurring failure patterns (browser auth, test failures, MCP schema issues, etc.)
- Post-edit validation rate
- Compact qualitative summaries of selected sessions

Pass `--max-sessions N` for a smaller sample while iterating. The analyzer caches parsed results by file hash so re-runs are near-instant.

### Scoring checklist

When scoring manually (or to validate the automated output), use this rubric:

| Dim | Subject | Check | Impact if missing |
|-----|---------|-------|-------------------|
| 1 | Spec clarity | Structured templates with AC, edge cases, non-goals | No template → cap at 3 |
| 2 | Agent instructions | Root AGENTS.md with stack, paths, commands | None → cap at 2 |
| 2 | Agent instructions | High-risk invariants documented (migrations, secrets, etc.) | Missing → −1 |
| 3 | Code clarity | Strict TypeScript or equivalent static types | None → cap at 2 |
| 3 | Code clarity | Business logic separated from framework glue | Mixed → −1 |
| 4 | Searchability | Feature flows discoverable by name/route | Hidden → −1 |
| 4 | Searchability | Generated/vendored code clearly marked | Mixed → −0.5 |
| 5 | Local env | Dependency lockfile committed | No lockfile → cap at 2 |
| 5 | Local env | One-command setup script | Manual → −1 |
| 6 | Tests | Unit + integration + E2E tests exist | None → cap at 1 |
| 6 | Tests | Focused test commands per surface | Only blanket → −0.5 |
| 7 | Static validation | Linter configured and documented | None → cap at 2 |
| 7 | Static validation | Pre-commit or CI hook enforces lint | Missing → −0.5 |
| 8 | Build feedback | Package-scoped build commands exist | Only root → −0.5 |
| 8 | Build feedback | Dev mode with HMR documented | Missing → −1 |
| 9 | Debuggability | Tests produce diagnostic artifacts (screenshots, traces) | None → −1 |
| 9 | Debuggability | Structured error types | Silent errors → −1 |
| 10 | Safety | Destructive migration workflow explicit | Implicit → cap at 3 |
| 10 | Safety | Secret/env files in .gitignore | Not ignored → cap at 2 |
| 11 | Browser automation | Auth bypass avoids login page | Manual login → cap at 2 |
| 11 | Browser automation | Stable selectors (data-testid or a11y roles) | CSS classes → −1 |

Start each dimension at 3, adjust up/down per the checklist, max 5, min 1.

### What it assesses

| # | Dimension |
|---|-----------|
| 1 | Code Comprehensibility — strong types, clear names, predictable structure |
| 2 | Context & Documentation — AGENTS.md, README, ADRs, inline WHY |
| 3 | Verifiability & Testing — test pyramid, type checker, linter, CI gates |
| 4 | Dev Environment Reproducibility — one-command setup, locked deps, containerized services |
| 5 | Style & Validation Tooling — strict linter, formatter, pre-commit hooks |
| 6 | Build System — deterministic builds, fast feedback, HMR |
| 7 | Observability & Debuggability — structured logs, health checks, actionable errors |
| 8 | Security & Governance — branch protection, secret scanning, CODEOWNERS |
| 9 | Task Discovery & Scoping — issue templates, acceptance criteria, definition of done |
| 10 | Spec & Planning Quality — structured PRDs, API contracts, measurable success criteria |
| 11 | CI/CD & Deployment Pipeline — automated gates, staging, rollback docs |

### Maturity levels

| Level | Score | What agents can do |
|-------|-------|-------------------|
| Fragile | <2.0 | Explore only; heavy supervision needed |
| Documented | 2.0–2.9 | Small changes with close review |
| Standardized | 3.0–3.9 | Well-scoped tasks with local verification |
| Optimized | 4.0–4.4 | Complex multi-file tasks with light review |
| Autonomous | 4.5+ | Spec to tested implementation with strategic oversight |

### Manual mode (no Python)

When Python 3 is not available, score each dimension 1–5 manually using the checklist above. Produce a report with: overall level, dimension table, critical gaps, action plan, and coverage table. See the automated report for output format reference.

### Report delivery

Persist the report as an HTML document artifact when team artifact/document tools are available. Otherwise display the summary in chat and note the full HTML path at `/tmp/agent-readiness-report.html`.

### Updates

This skill ships from the [supatest-ai/supa-skills](https://github.com/supatest-ai/supa-skills) marketplace. The source of truth for the scripts is the [supatest-ai/aiden](https://github.com/supatest-ai/aiden) repo under `.agents/skills/agent-readiness/scripts/`.
