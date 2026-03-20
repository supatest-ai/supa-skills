# Commit All Changes

Stage all changes and commit with well-structured commit messages following conventional commits format.

## When to use this skill

Use this skill when you need to:
- Stage and commit all changes in one step
- Quickly commit everything without manually staging
- Create well-formatted commit messages for all changes
- Follow conventional commit standards

## Instructions

When the user invokes this skill:

### 1. Check Repository Status

Run `git status` to see all changes:
- Show untracked files
- Show modified files
- Show deleted files
- Warn if there are sensitive files (.env, credentials, etc.)

### 2. Review All Changes

Before staging anything:
- Run `git diff` to see unstaged changes
- Run `git diff --cached` to see any already staged changes
- Identify all files that will be affected
- **Critical**: Check for files that should NOT be committed:
  - `.env` files
  - `credentials.json` or similar
  - API keys or secrets
  - Large binary files
  - Build artifacts (`dist/`, `node_modules/`, etc.)

### 3. Stage All Files

If safe to proceed:
```bash
git add -A
```

Or for more control, list specific files:
```bash
git add file1 file2 file3
```

**Never stage:**
- Files with secrets or credentials
- Files that should be in .gitignore
- Large binaries (warn user first)

### 4. Analyze Changes

Review what's now staged:
- Run `git diff --cached --stat` to see stats
- Identify the type of change (feature, fix, refactor, etc.)
- Group related changes if multiple areas affected
- Look for breaking changes or important migrations

### 5. Determine Commit Type

Choose the appropriate conventional commit type:

**Common types:**
- **feat**: New feature or functionality
- **fix**: Bug fix
- **docs**: Documentation changes only
- **style**: Formatting, whitespace (no code change)
- **refactor**: Code restructuring without changing behavior
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependencies, build config
- **perf**: Performance improvements
- **ci**: CI/CD configuration changes
- **build**: Build system or external dependency changes

### 6. Generate Commit Message

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

Multiple file types:
```
chore: update dependencies and fix linting issues

Updates all npm packages to latest versions and fixes
eslint warnings across the codebase.

- Update package.json dependencies
- Fix linting issues in components
- Update Jest configuration
```

Mixed changes:
```
feat: add dark mode and update documentation

Implements dark mode toggle with persistent user preference.
Updates docs to reflect new theming system.

- Add ThemeProvider with light/dark themes
- Implement theme toggle component
- Add theme persistence to localStorage
- Update README with theme usage examples
```

### 7. Execute Commit

Run the commit:
```bash
git commit -m "$(cat <<'EOF'
<commit message here>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

### 8. Verify Success

After committing:
- Run `git log -1` to show the commit
- Run `git status` to confirm clean state
- If commit fails (pre-commit hooks, etc.), help fix the issue and create a NEW commit (don't amend)

### 9. Push to Remote

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
was renamed and both now reference the new name).

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

### Step 7 — Push

```bash
git push
```

---

## Safety Checks

Before staging with `git add -A`, verify:

1. **No sensitive files:**
   - Check for `.env`, `.env.local`, etc.
   - Check for `*credentials*`, `*secrets*`, `*keys*`
   - Check for `config/production.json` with secrets

2. **No build artifacts:**
   - `node_modules/`, `dist/`, `build/`
   - `.next/`, `.nuxt/`
   - `target/`, `out/`

3. **No large files:**
   - Warn if files > 10MB
   - Suggest using Git LFS for large assets

4. **Check .gitignore:**
   - If files should be ignored, suggest adding to .gitignore first

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

## Examples

### Example 1: Simple Feature
```
User: "/commit-all"

You:
1. git status (shows new components and tests)
2. git diff (reviews changes)
3. git add -A
4. Generate message:

feat: add user profile component

Implements new user profile page with avatar upload
and bio editing functionality.

- Add ProfilePage component
- Add AvatarUpload component
- Add profile API endpoints
- Add profile page tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

5. git commit
6. Confirm success
```

### Example 2: Multiple Changes
```
User: "/commit-all"

You:
1. git status (shows code changes, docs, and config)
2. Check for sensitive files (none found)
3. git add -A
4. Generate message:

chore: update build config and improve documentation

Updates webpack config for better performance and adds
comprehensive API documentation.

- Optimize webpack bundle splitting
- Add compression plugins
- Update API documentation with examples
- Add contribution guidelines

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

### Example 3: Sensitive Files Detected
```
User: "/commit-all"

You:
1. git status
2. Detect .env file

⚠️ Warning: Sensitive files detected

Found files that should not be committed:
- .env (contains API keys)

Options:
1. Add .env to .gitignore (recommended)
2. Stage only safe files manually
3. Cancel commit

What would you like to do?
```

## Tips

- **Review before staging**: Always check what's being committed
- **Use .gitignore**: Keep it updated for your project
- **Be descriptive**: Subject + body for non-trivial changes
- **Group logically**: One logical change per commit (even if multiple files)
- **Check secrets**: Never commit credentials or API keys
- **Consider scope**: Very large commits might need to be split

## Notes

- This skill stages **everything** - use `/commit` for selective commits
- Always reviews files before staging to prevent committing secrets
- If commit fails due to hooks, fix the issue and create a NEW commit (never amend unless explicitly requested)
- Always add "Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>" to commits
