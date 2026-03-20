# Commit Staged Files

Commit staged files with well-structured commit messages following conventional commits format.

## When to use this skill

Use this skill when you need to:
- Commit files that are already staged (`git add`)
- Create well-formatted commit messages
- Follow conventional commit standards
- Ensure commit message quality

## Instructions

When the user invokes this skill:

### 1. Check Staged Files

Run `git status` and `git diff --cached --stat` to see what's staged:
- If nothing is staged, inform the user and suggest using `/commit-all` or staging files first
- Show the user what will be committed

### 2. Analyze Changes

Review the staged changes:
- Run `git diff --cached` to understand what changed
- Identify the type of change (feature, fix, refactor, etc.)
- Group related changes if multiple files
- Look for breaking changes or important migrations

### 3. Determine Commit Type

Choose the appropriate conventional commit type:

**Common types:**
- **feat**: New feature or functionality
- **fix**: Bug fix
- **docs**: Documentation changes only
- **style**: Formatting, whitespace, missing semicolons (no code change)
- **refactor**: Code restructuring without changing behavior
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependencies, build config
- **perf**: Performance improvements
- **ci**: CI/CD configuration changes
- **build**: Build system or external dependency changes
- **revert**: Reverting a previous commit

### 4. Generate Commit Message

Create a commit message with:

**Subject line (max 72 characters):**
```
<type>: <short description>
```

**Body (optional but recommended for significant changes):**
- Explain **what** changed and **why**
- Use present tense ("add" not "added")
- Wrap at 72 characters
- Reference issues/PRs if applicable (#123)
- Note breaking changes with "BREAKING CHANGE:" prefix

**Examples:**

Simple commit:
```
feat: add user authentication with JWT
```

With body:
```
feat: add user authentication with JWT

Implements JWT-based authentication system with login, signup,
and password reset flows. Users can now securely authenticate
and maintain sessions.

- Add auth middleware for protected routes
- Implement token refresh mechanism
- Add password hashing with bcrypt

Closes #123
```

Breaking change:
```
feat: migrate to new API endpoint structure

BREAKING CHANGE: API endpoints now use /api/v2 prefix instead of /v1.
Clients must update their base URLs.

Migrates all endpoints to new versioned structure for better
API evolution support.
```

### 5. Execute Commit

Run the commit:
```bash
git commit -m "$(cat <<'EOF'
<commit message here>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

### 6. Verify Success

After committing:
- Run `git log -1` to show the commit
- Run `git status` to confirm clean state
- If commit fails (pre-commit hooks, etc.), help fix the issue and create a NEW commit (don't amend)

### 7. Push to Remote

After a successful commit, attempt to push:
```bash
git push
```

**If push is rejected** (remote has new commits), follow the Merge Conflict Protocol below
before pushing again.

---

## Merge Conflict Protocol

This protocol applies whenever `git push` is rejected because the remote has diverged.
Follow every step in order. Do not skip ahead.

> **Why this matters**: AI agents are among the most common sources of silent code loss
> in collaborative repos. A conflict "resolved" by picking one side destroys the other
> side's work with no warning. The steps below prevent that.

### Step 1 — Always merge, never rebase

```bash
git pull --no-rebase
```

**Never use `git pull --rebase`, `git rebase`, or any rebase flag.** Rebase rewrites
commit history and makes it much harder to audit what was dropped. Merge preserves
full history of both sides and produces an explicit merge commit that can be reviewed.

If the repo has `pull.rebase = true` configured globally, override it for this pull:
```bash
git -c pull.rebase=false pull
```

### Step 2 — If auto-merge succeeds (no conflicts)

Verify the merge did not accidentally drop anything:
```bash
git diff HEAD~1 HEAD        # what changed in the merge commit
git log --oneline -5        # confirm both branches are in history
```

Then push:
```bash
git push
```

### Step 3 — If conflicts arise: understand before touching anything

Before resolving a single conflict marker, gather full context:

```bash
# See what each branch actually changed
git log --oneline HEAD...MERGE_HEAD

# See the full conflict diff with base version (more context than default)
git diff --diff-filter=U

# For each conflicted file, show the three-way base version
git checkout --conflict=diff3 <file>   # adds base version between <<<< and ====
```

Read the **entire** conflicting region — not just the lines immediately around the
markers. Understanding what each side was trying to accomplish is more important than
the line-level diff. This is the distinction between a *syntactic conflict* (same lines
changed) and a *semantic conflict* (logically contradictory intent). AI tools
like Cursor, Copilot, and Claude are particularly prone to resolving syntactic conflicts
correctly while missing semantic ones.

### Step 4 — Classify each conflict before resolving it

For every conflict hunk, determine which category applies:

**A. Additive — both sides added independent things to the same area**

Examples: different import lines, different functions added near the same location,
different items added to a list or enum.

Resolution: **include both**. Order them logically (e.g., alphabetical for imports).

```
// ours
import { Foo } from './foo'
// theirs
import { Bar } from './bar'
// resolved: keep both
import { Bar } from './bar'
import { Foo } from './foo'
```

**B. Parallel edits — both sides changed the same code for independent reasons**

Examples: both sides updated a function signature, both sides modified the same config
value for different reasons.

Resolution: **merge the intent of both changes**. Read surrounding code and commit
messages to understand what each side needed. The result should satisfy both.

**C. Semantic conflict — two features that logically contradict each other**

One side adds or changes behavior X; the other removes it or implements incompatible
behavior Y. These cannot both be true at once.

→ **STOP. Do not guess. Ask the user:**

> "I found a genuine behavioral conflict in `<file>` at `<function/section>`.
>
> **Our branch**: `<describe what our code does>`
> **Remote branch**: `<describe what the remote code does>`
>
> These cannot both be active at the same time. Which should take precedence?
> Or should I combine them in a specific way?"

**D. Delete/modify conflict — one side deleted something the other modified**

One side deleted a function, component, or file; the other side made changes to it.

→ **STOP. Ask the user:**

> "The remote branch deleted `<function/component/file>` that our branch modified.
>
> **Our change**: `<describe the modification>`
> **Remote action**: deleted it
>
> Should I: (1) keep the deletion and discard our changes, (2) restore our modified
> version, or (3) something else?"

**E. Duplicate/superseded — one side is a strict subset of the other**

One side's change is entirely contained in or replaced by the other's (e.g., a function
was renamed and both now reference the new name; one side already includes the other's
additions).

Resolution: keep the more complete version, but **explicitly verify** before discarding.
State what you are dropping and why in the merge commit message.

### Step 5 — The golden rule: never silently drop code

**Never resolve a conflict by simply picking one side (`git checkout --ours` or
`--theirs`) without explicit user confirmation for that file.**

If in doubt about whether something can be dropped: keep both. Duplicate or redundant
code is far safer than silently lost behavior.

Pre-resolution checklist for every conflicted file:
- [ ] Every function/feature present in HEAD is still present in the resolved file
- [ ] Every function/feature present in MERGE_HEAD is still present (or user confirmed removal)
- [ ] No conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) remain
- [ ] The merged result is syntactically valid

Run a syntax check after resolving all conflicts:
```bash
# TypeScript projects
npx tsc --noEmit

# Or whatever the project's lint/typecheck command is
```

### Step 6 — Review the full merge diff before committing

After resolving all conflicts and before staging:

```bash
git diff                    # unstaged resolved changes
git diff --cached           # already staged changes
```

Verify:
1. **Your changes are intact** — everything from HEAD is present
2. **Remote changes are intact** — everything from MERGE_HEAD is present
3. **Nothing was accidentally dropped** — no functions, imports, or behavior went missing

Only after this review, stage and commit:
```bash
git add <resolved files>
git commit   # accept git's auto-generated merge commit message — do not rewrite it
```

The merge commit message ("Merge branch 'main' of ...") is intentional — it marks this
as a merge point in history, which is important for auditability.

### Step 7 — Push

```bash
git push
```

---

## Commit Message Guidelines

**Subject line:**
- Use imperative mood ("add feature" not "added feature")
- Don't capitalize first letter after type
- No period at the end
- Keep under 72 characters
- Be specific but concise

**Body:**
- Separate from subject with blank line
- Explain what and why, not how
- Wrap at 72 characters
- Use bullet points for multiple changes
- Reference issues with #123
- Note breaking changes prominently

**Examples of good vs bad:**

✅ Good:
```
feat: add email verification for new users

Implements email verification flow to ensure valid email addresses.
Users receive a verification link after signup and must verify
before accessing full features.

- Add verification token generation
- Implement email sending service
- Add verification UI flow

Closes #456
```

❌ Bad:
```
Added some stuff

Updated files
```

## Tips

- **Be descriptive but concise**: Subject should be clear, body adds context
- **Group related changes**: One logical change per commit
- **Use conventional commits**: Makes changelog generation easier
- **Reference issues**: Link to tickets/issues for context
- **Explain why**: The code shows what, commit message explains why
- **Check for secrets**: Don't commit API keys, passwords, or credentials

## Notes

- This skill only commits **already staged** files
- Use `/commit-all` if you want to stage and commit everything
- If commit fails due to hooks, fix the issue and create a NEW commit (never amend unless explicitly requested)
- Always add "Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>" to commits
