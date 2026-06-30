---
name: work-summary
description: Generate a summary of work done based on git commit history across one or more repositories. Use for standups, timesheets, retrospectives, or any time you need a structured overview of what was accomplished in a time period.
argument-hint: <author> <start_datetime> <end_datetime> <repo1> [repo2...]
---

# Work Summary Generator

Generate a summary of work done based on git commit history.

## Arguments

`<author> <start_datetime> <end_datetime> <repo1> [repo2] [repo3]...`

### Examples
- `/work-summary Alice "2026-01-08 09:00" "2026-01-09 18:00" frontend backend`
- `/work-summary "Alice Smith" "2026-01-07 09:00" "2026-01-07 18:00" .`

## When to use this skill

Use this skill when you need to:
- Generate work summaries for standup or status reports
- Create summaries for timesheets or billing
- Review what was accomplished in a time period
- Prepare for retrospectives or reviews
- Track work across multiple repositories

## Instructions

### 1. Parse Arguments

If no arguments provided, ask the user for:
1. **Author name** - Git author to filter by
2. **Start date/time** - Format: `YYYY-MM-DD HH:MM` (in local timezone)
3. **End date/time** - Format: `YYYY-MM-DD HH:MM` (in local timezone)
4. **Repository paths** - Space-separated, relative to current directory or absolute paths

Example prompts:
```
Please provide:
- Author name: (e.g., "Alice" or "Alice Smith")
- Start time: (e.g., "2026-01-08 09:00")
- End time: (e.g., "2026-01-08 18:00")
- Repositories: (e.g., "frontend backend" or "." for current)
```

### 2. Collect Git Data

For each repository:

**Get commits:**
```bash
cd <repo> && git log --author="<author>" --since="<start>" --until="<end>" --pretty=format:"%h|%s"
```

**Get stats:**
```bash
cd <repo> && git log --author="<author>" --since="<start>" --until="<end>" --shortstat --pretty=format:"%h"
```

**Notes:**
- Assume the user's local timezone unless otherwise specified
- Handle relative paths (convert to absolute if needed)
- If repo doesn't exist, warn and skip it

### 3. Group and Categorize Commits

**Group related commits** into logical tasks:
- Same feature across multiple commits
- Related bug fixes
- Single refactoring effort
- Use commit message prefixes to help (feat, fix, refactor, chore, docs, test)

**Categorize by size:**

**Large Tasks:**
- New packages or major modules
- Significant new functionality with multiple components
- Major architectural changes
- Complex features spanning many files
- Examples: "Add authentication system", "Implement payment processing"

**Medium Tasks:**
- Feature additions to existing modules
- Substantial refactoring efforts
- Multi-file changes with moderate complexity
- API endpoint additions
- Examples: "Add user profile editing", "Refactor API error handling"

**Small Tasks:**
- Bug fixes
- UI tweaks and styling
- Single-file changes
- Cleanup and formatting
- Documentation updates
- Minor refactors
- Examples: "Fix typo", "Update button color", "Add JSDoc"

### 4. Calculate Totals

- Total commit count across all repos
- Total lines added (sum from git stats)
- Total lines deleted (sum from git stats)
- Total distinct tasks

### 5. Generate HTML Output

Create a self-contained HTML report at `/tmp/work-summary.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Work Summary: <start> - <end></title>
  <style>
    body { font: 14px/1.6 system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #1a1a2e; background: #f8f9fa; }
    h1 { font-size: 22px; margin: 0 0 4px; }
    .meta { color: #6b7280; font-size: 13px; margin-bottom: 20px; }
    .summary-bar { background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px; display: flex; gap: 20px; }
    .summary-bar .stat { text-align: center; flex: 1; }
    .summary-bar .stat .num { font-size: 28px; font-weight: 700; display: block; }
    .summary-bar .stat .label { font-size: 11px; text-transform: uppercase; color: #6b7280; letter-spacing: 0.05em; }
    .task-group { background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px 20px; margin-bottom: 16px; }
    .task-group h2 { font-size: 16px; margin: 0 0 8px; padding-bottom: 6px; border-bottom: 2px solid #e5e7eb; }
    .task-group h2 span { color: #6b7280; font-weight: 400; }
    .task { padding: 6px 0; border-bottom: 1px solid #f1f5f9; font-size: 14px; }
    .task:last-child { border-bottom: 0; }
    .task .repo { color: #6b7280; font-size: 12px; }
    .inline-task { display: inline; }
    ul { padding-left: 20px; margin: 4px 0; }
    li { font-size: 14px; margin: 4px 0; }
  </style>
</head>
<body>

<h1>Work Summary: <start> - <end></h1>
<div class="meta">Author: <name></div>

<div class="summary-bar">
  <div class="stat"><span class="num">N</span><span class="label">Commits</span></div>
  <div class="stat"><span class="num">~Xk</span><span class="label">Lines added</span></div>
  <div class="stat"><span class="num">~Yk</span><span class="label">Lines deleted</span></div>
  <div class="stat"><span class="num">N</span><span class="label">Tasks</span></div>
</div>

<div class="task-group">
  <h2>Large Tasks <span>(N)</span></h2>
  <div class="task"><strong>Task Name</strong> <span class="repo">(repo)</span> — Brief description</div>
</div>

<div class="task-group">
  <h2>Medium Tasks <span>(N)</span></h2>
  <div class="task"><strong>Task Name</strong> <span class="repo">(repo)</span> — Brief description</div>
</div>

<div class="task-group">
  <h2>Small Tasks <span>(N)</span></h2>
  <ul>
    <li>Fix login validation error <span class="repo">(repo)</span></li>
  </ul>
</div>

</body>
</html>
```

Save the file and report the path to the user.

## Examples

### Example 1: With Arguments
```
User: "/work-summary Alice '2026-02-13 09:00' '2026-02-13 18:00' frontend"

You:
1. cd frontend
2. Run git log commands
3. Analyze commits
4. Generate HTML report at /tmp/work-summary.html

Summary: 15 commits, ~2k lines added, ~500 lines deleted across 8 distinct tasks
```

### Example 2: Multiple Repos
```
User: "/work-summary 'Alice Smith' '2026-02-01 00:00' '2026-02-07 23:59' frontend backend docs"

You analyze commits across all three repos, group by task, and generate /tmp/work-summary.html.

Summary: 42 commits, ~5k lines added, ~2k lines deleted across 13 distinct tasks
```

### Example 3: No Arguments - Interactive
```
User: "/work-summary"

You: "Please provide the following information:
- Author name: (e.g., 'Alice' or 'Alice Smith')
- Start date/time: (format: YYYY-MM-DD HH:MM, e.g., '2026-02-13 09:00')
- End date/time: (format: YYYY-MM-DD HH:MM, e.g., '2026-02-13 18:00')
- Repository paths: (space-separated, e.g., 'frontend backend' or '.' for current directory)"

User: "Alice, 2026-02-13 09:00, 2026-02-13 18:00, ."

You: [Process current directory as repository and generate summary]
```

## Tips

- **Smart grouping**: Combine commits like "Add feature X", "Fix feature X bug", "Update feature X tests" into one task
- **Use commit messages**: Look for conventional commit prefixes (feat:, fix:, refactor:, etc.)
- **Context matters**: A 10-line change to a critical file might be "Medium", while a 100-line new test file might be "Small"
- **Repo names**: Only show repo names if analyzing multiple repos
- **Time zones**: Default to local timezone but respect user's timezone if specified
- **Clarity**: Make task descriptions clear and business-value focused
- **Accuracy**: Count lines accurately from git stats

## Notes

- This skill works best with clean, descriptive commit messages
- For very large time ranges, consider summarizing by day or week
- If no commits found, clearly state that and verify the author name and date range
- Handle errors gracefully (missing repos, invalid dates, git errors)
