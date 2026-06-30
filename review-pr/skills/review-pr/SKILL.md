---
name: review-pr
description: Review a pull request or set of code changes. Filters to issues introduced by this PR (not pre-existing), scores confidence, and produces a prioritized HTML report with severity tiers.
argument-hint: [PR number or branch name]
---

# Code Review

Structured pull request review. Focuses on issues *introduced* by this change, not pre-existing ones. Produces a prioritized HTML report.

## When to Use

- Reviewing a PR before merge
- Reviewing your own code before opening a PR
- Security or correctness audit of a specific diff
- Reviewing code after implementing a feature (incremental review)

## What NOT to Do

- Do not flag pre-existing issues the author didn't touch
- Do not block on style/formatting — that's what linters are for
- Do not rewrite code to a personal preference
- Do not list speculative risks without evidence

---

## Phase 1 — Context Gathering

Read the following before examining any diff:

1. **PR description** — What is this change trying to do?
2. **Linked issues** — What problem is being solved?
3. **Commit messages** — What was the author's intent at each step?
4. **CLAUDE.md / CONTRIBUTING.md** — Any project-specific conventions?

If the PR is a draft, has `WIP` in the title, or is already closed — ask the user before proceeding.

For PRs with >400 lines changed: flag this to the user and suggest splitting. Proceed only with their confirmation.

---

## Phase 2 — Filter to What This PR Introduced

Only report issues that are new in this diff. Use `git blame` to confirm an issue was introduced by this change, not inherited from existing code:

```bash
git log -p --follow -S "<suspicious code>" -- <file>
git log --all --oneline -S "<removed-code-pattern>"
```

If a suspicious pattern exists elsewhere in the codebase and is not new here, mark it as `pre-existing` and skip it.

---

## Phase 3 — Review Dimensions

Work through these categories in priority order:

### 1. Security (Highest Priority)
- **Injection:** SQL, command, LDAP, XPath, template injection
- **Authentication/Authorization:** missing auth checks, privilege escalation, JWT/session issues
- **Sensitive data:** secrets, credentials, or PII in code, logs, or error messages
- **Input validation:** unvalidated user input reaching dangerous operations
- **Cryptography:** weak algorithms, hardcoded keys, insecure random
- **Dependency risk:** new packages added — are they trustworthy, maintained, minimal?

For each finding: state the exploit scenario concretely, not just "this could be insecure."

### 2. Correctness
- Logic errors, off-by-one, null/undefined handling
- Async/await correctness, unhandled promise rejections
- Edge cases: empty input, zero, negative numbers, max values
- Error propagation — are errors being swallowed silently?
- Race conditions or shared mutable state

### 3. Performance
- N+1 queries (database calls inside loops)
- Missing indexes for new query patterns
- Unbounded operations (no pagination, no limits)
- Unnecessary blocking operations in async code
- Large payloads loaded entirely into memory

### 4. Maintainability
- Functions doing too much (>30 lines warrants scrutiny)
- Deep nesting (>3 levels)
- Magic numbers/strings without explanation
- Variable/function names that are misleading
- Dead code introduced

### 5. Test Coverage
- Does the happy path have a test?
- Are edge cases and error paths tested?
- Are the test assertions meaningful (not just "it doesn't throw")?
- Was existing test coverage inadvertently broken?

### 6. Error Handling
- Empty catch blocks that silence errors
- Missing `finally` for cleanup operations
- User-facing error messages that leak internal details

### 7. Documentation (Lowest Priority)
- Public API changes without updated docs
- Complex logic with no explanation comment
- Outdated comments that now contradict the code

---

## Phase 4 — Confidence Filtering

Before including a finding in the report, ask:
- Can I point to the exact file + line?
- Can I describe a concrete scenario where this causes a real problem?
- Is my confidence ≥ 80%?

If any answer is no → drop the finding or downgrade to a question/suggestion.

Skip findings that:
- A linter would already catch
- Require speculative future scenarios to be a problem
- Are purely stylistic with no functional impact
- Are pre-existing (not introduced by this PR)

---

## Phase 5 — Build the HTML Report

Generate a self-contained HTML report at `/tmp/code-review-report.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Code Review: <PR title> (#<number>)</title>
  <style>
    body { font: 14px/1.6 system-ui, sans-serif; max-width: 960px; margin: 0 auto; padding: 20px; color: #1a1a2e; background: #f8f9fa; }
    h1 { font-size: 22px; margin: 0 0 4px; }
    .meta { color: #6b7280; font-size: 13px; margin-bottom: 20px; }
    .summary { display: flex; gap: 12px; margin-bottom: 24px; }
    .summary-item { background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px 18px; text-align: center; flex: 1; }
    .summary-item .count { font-size: 28px; font-weight: 700; display: block; }
    .summary-item .label { font-size: 11px; text-transform: uppercase; color: #6b7280; letter-spacing: 0.05em; }
    .finding { background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px 20px; margin-bottom: 12px; }
    .finding h3 { margin: 0 0 6px; font-size: 15px; }
    .finding .file { font-family: monospace; font-size: 12px; color: #6b7280; margin-bottom: 8px; }
    .finding .desc { font-size: 13px; margin-bottom: 8px; }
    .finding .confidence { font-size: 11px; color: #6b7280; }
    .blocking { border-left: 4px solid #dc2626; }
    .blocking h3 { color: #dc2626; }
    .important { border-left: 4px solid #d97706; }
    .important h3 { color: #d97706; }
    .nit { border-left: 4px solid #6b7280; }
    .nit h3 { color: #6b7280; }
    .suggestion { border-left: 4px solid #2563eb; }
    .suggestion h3 { color: #2563eb; }
    .positive { border-left: 4px solid #16a34a; }
    .positive h3 { color: #16a34a; }
    pre { background: #f1f5f9; border-radius: 4px; padding: 8px 12px; font-size: 12px; overflow-x: auto; }
    .findings-section { margin-bottom: 24px; }
    .findings-section h2 { font-size: 16px; margin: 0 0 10px; padding-bottom: 6px; border-bottom: 2px solid #e5e7eb; }
    .verdict { text-align: center; padding: 16px; font-size: 18px; font-weight: 700; border-radius: 8px; margin-top: 24px; }
    .verdict.approve { background: #dcfce7; color: #16a34a; }
    .verdict.changes { background: #fef3c7; color: #d97706; }
  </style>
</head>
<body>

<h1>Code Review: <PR title> (#<number>)</h1>
<div class="meta">
  <strong>Branch:</strong> `<branch>` → `main` &middot;
  <strong>Files:</strong> N &middot;
  <strong>Lines:</strong> +X / -Y
</div>

<div class="summary">
  <div class="summary-item"><span class="count" style="color:#dc2626">N</span><span class="label">Blocking</span></div>
  <div class="summary-item"><span class="count" style="color:#d97706">N</span><span class="label">Important</span></div>
  <div class="summary-item"><span class="count" style="color:#6b7280">N</span><span class="label">Nits</span></div>
  <div class="summary-item"><span class="count" style="color:#2563eb">N</span><span class="label">Suggestions</span></div>
</div>

<!-- Blocking -->
<div class="findings-section">
<h2>🔴 Blocking — Must fix before merge</h2>
<div class="finding blocking">
  <h3>[Security] SQL injection in user search</h3>
  <div class="file">src/api/users.ts:47</div>
  <div class="desc">Raw user input interpolated into query string. Attacker can extract any table.</div>
  <pre>// Current
db.query(`SELECT * FROM users WHERE name = '${req.query.name}'`)
// Fix
db.query('SELECT * FROM users WHERE name = $1', [req.query.name])</pre>
  <div class="confidence">Confidence: 95%</div>
</div>
</div>

<!-- Important -->
<div class="findings-section">
<h2>🟡 Important — Should fix before merge</h2>
<div class="finding important">
  <h3>[Correctness] Unhandled promise rejection</h3>
  <div class="file">src/jobs/sync.ts:23</div>
  <div class="desc">...</div>
  <div class="confidence">Confidence: 85%</div>
</div>
</div>

<!-- Nits -->
<div class="findings-section">
<h2>🔵 Nits</h2>
<div class="finding nit">
  <h3>[Maintainability] Magic number</h3>
  <div class="file">src/config.ts:8</div>
  <div class="desc">...</div>
</div>
</div>

<!-- Suggestions -->
<div class="findings-section">
<h2>💡 Suggestions</h2>
<div class="finding suggestion">
  <h3>Suggestion title</h3>
  <div class="desc">Optional improvement worth considering.</div>
</div>
</div>

<!-- Positive Observations -->
<div class="findings-section">
<h2>✅ Positive Observations</h2>
<div class="finding positive">
  <h3>Well-structured error handling</h3>
  <div class="desc">New error boundary covers all API call sites.</div>
</div>
</div>

<div class="verdict approve">✅ Approve</div>
<!-- or <div class="verdict changes">🔄 Request Changes</div> -->

</body>
</html>
```

Save the file and report the path to the user.

## Severity Reference

| Tier | Label | Meaning |
|---|---|---|
| 🔴 | **Blocking** | Security vulnerability, data loss risk, broken functionality — fix before merge |
| 🟡 | **Important** | Real bug or risk, should fix but not emergency |
| 🔵 | **Nit** | Minor quality issue, fix if trivial |
| 💡 | **Suggestion** | Optional improvement |
| ✅ | **Praise** | Good work worth acknowledging |
| 👻 | **Pre-existing** | Issue exists but was not introduced by this PR |
