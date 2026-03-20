# supa-skills

> Claude Code plugin marketplace for the Supatest AI team.

This repo is a [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces). Install skills with `/plugin install`, get updates with `/plugin update`.

## Setup (one-time per machine)

```
/plugin marketplace add supatest-ai/supa-skills
```

Then install the skills you want:

```
/plugin install commit
/plugin install commit-all
/plugin install deploy
/plugin install work-summary
/plugin install review-pr
/plugin install debug-prod
/plugin install bug
/plugin install test-feature
/plugin install signoz-health-check
/plugin install agent-readiness
```

Skills are installed globally and available across all your projects.

## Updating

```
/plugin update
```

This updates all installed plugins from all marketplaces at once.

Claude Code checks for updates automatically at every startup — no action needed on your end.

## Available Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **commit** | `/commit` | Commit already-staged files with conventional commit messages. Includes full merge conflict protocol. |
| **commit-all** | `/commit-all` | Stage all changes and commit. Includes safety checks for secrets/build artifacts and merge conflict protocol. |
| **deploy** | `/deploy [staging\|prod] [services]` | Deploy to staging or production via GitHub Actions. Auto-detects changed services, streams live workflow progress. |
| **work-summary** | `/work-summary <author> "<start>" "<end>" <repos...>` | Generate work summaries from git commits with task categorization. |
| **review-pr** | `/review-pr [PR number or branch]` | Review a PR. Filters to issues introduced by the PR, scores confidence, requires approval before posting. |
| **debug-prod** | `/debug-prod [issue description]` | Investigate production incidents. Uses metrics → traces → logs funnel, produces structured findings report. |
| **bug** | `/bug [description]` | Structured bug investigation: capture → reproduce → root cause → failing test → fix → verify. |
| **test-feature** | `/test-feature [description]` | Interactively test a feature via browser automation. Captures a GIF walkthrough and verification report. |
| **signoz-health-check** | `/signoz-health-check [timeRange]` | Comprehensive SigNoz observability health check across services, logs, metrics, traces, and alerts. |
| **agent-readiness** | `/agent-readiness` | Evaluate codebase readiness for autonomous AI agent work. Scored report across 11 dimensions. |

## Contributing

1. Create a new directory at the repo root for your skill
2. Add `.claude-plugin/plugin.json` (name, description, version)
3. Add `skills/<skill-name>/SKILL.md`
4. Add the plugin entry to `.claude-plugin/marketplace.json`
5. Submit a PR

### Plugin structure

```
my-skill/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── my-skill/
        └── SKILL.md
```

### plugin.json template

```json
{
  "name": "my-skill",
  "description": "One-line description of what this skill does.",
  "version": "1.0.0",
  "author": { "name": "Supatest AI" },
  "license": "MIT"
}
```

### Releasing updates

**Always bump `version` in `plugin.json` when you change a skill.** Claude Code compares version strings to decide whether to auto-update. If the version stays the same, installed clients will not receive the new content even after the marketplace refreshes.

Use [semantic versioning](https://semver.org): `1.0.0` → `1.0.1` for patches, `1.1.0` for new behaviour, `2.0.0` for breaking changes.

## Resources

- [Claude Code Skills docs](https://code.claude.com/docs/en/skills)
- [Plugin Marketplaces docs](https://code.claude.com/docs/en/plugin-marketplaces)
