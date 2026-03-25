---
name: drizzle-migration-guardrails
description: Safe workflow for Drizzle ORM schema changes, migration generation, migration review, and schema-drift investigation. Use when Codex is modifying Drizzle models or schema files, generating or applying migrations, reviewing `drizzle/` artifacts, diagnosing out-of-order migrations or schema drift, or planning DB-related deploys in repos that use Drizzle Kit.
---

# Drizzle Migration Guardrails

## Overview

Keep Drizzle migrations forward-only, generated, and verifiable. This skill exists to stop agents from "fixing" migration problems by hand-editing SQL, journals, snapshots, or database state when the repo already has a canonical Drizzle workflow.

## Non-Negotiable Rules

1. Change Drizzle source-of-truth schema code first.
   Edit the repo's Drizzle models/schema files, not generated migration artifacts.

2. Generate migrations with the repo's own Drizzle command.
   Prefer package scripts like `db:generate`, `db:migrate`, or documented wrappers over ad hoc commands.

3. Never hand-write or hand-edit normal Drizzle migration artifacts.
   Do not manually create or edit:
   - `drizzle/*.sql`
   - `drizzle/meta/_journal.json`
   - `drizzle/meta/*_snapshot.json`

   Exception: for data-only migrations, use `drizzle-kit generate --custom` to create the file, then fill in the SQL. See "Data-Only Migrations" section below.

4. Never rewrite migration history that may already be applied anywhere.
   Once a migration might exist in another developer DB, staging, CI, or production, treat it as immutable. Add a new forward migration instead.

5. Never patch `__drizzle_migrations` or mutate production schema state unless the user explicitly asks for incident recovery.
   Even then, pause and inspect before acting. Read [references/why-and-break-glass.md](./references/why-and-break-glass.md).

6. Never use `drizzle-kit push` in a repo that versions migrations.
   If the repo has a committed `drizzle/` folder and migration scripts, assume `generate + migrate` is the intended workflow.

## Safe Workflow

### 1. Inspect the repo's migration contract

Check:
- package scripts for `db:generate`, `db:migrate`, type-check, and test commands
- `drizzle.config.*`
- schema entrypoints and model barrel files
- deployment hooks that run migrations

Use the repo's wrapper commands when they exist. Do not invent a new workflow because it seems simpler.

### 2. Make the schema change in source code

Update the Drizzle schema/models that define the desired DB shape.

Do not start by writing SQL.

### 3. Generate the migration

Run the repo's canonical generate command.

Typical examples:
- `pnpm db:generate`
- `pnpm -F api db:generate`
- `npm run db:generate`

If the generated SQL looks wrong, fix the schema inputs and regenerate. Do not "clean up" generated files by hand during normal feature work.

### 4. Review the generated artifacts

Verify that the generated migration is:
- additive or forward-only when appropriate
- consistent with the schema change you intended
- free of accidental table drops, renames, or constraint churn

Review is required. Manual editing is not the default fix.

### 5. Apply and verify

Run the repo's canonical migrate command on a disposable or local development database.

Then verify:
- the migration applies cleanly from scratch
- the app/type-check/tests that depend on the schema still work
- the generated artifacts are fully committed together

### 6. Check deployment safety

If deploy hooks or CI swallow migration failures, flag or fix that. A migration failure should block deployment in normal operation.

## Data-Only Migrations (Backfills, Seeding, Data Conversions)

Sometimes you need a migration that changes data but not schema — for example, backfilling a new column, seeding lookup data, or converting values (slugs to UUIDs). Drizzle has a built-in mechanism for this.

### How to create a data-only migration

Use `drizzle-kit generate --custom`:

```bash
pnpm -F api exec drizzle-kit generate --custom --name=descriptive-name
```

This generates:
- An empty SQL file at `drizzle/NNNN_descriptive_name.sql` with a placeholder comment
- A proper snapshot file at `drizzle/meta/NNNN_snapshot.json` (copies the current schema state)
- A journal entry in `drizzle/meta/_journal.json`

Then fill the generated SQL file with your data migration SQL.

### Rules for data migrations

1. **Always use `--custom` flag** — never hand-create SQL files or manually edit `_journal.json` or snapshot files.
2. **Make data migrations idempotent** — use WHERE clauses, NOT EXISTS, or join conditions that naturally skip already-migrated rows. This prevents double-application.
3. **Keep data migrations separate from schema migrations** — don't mix DDL (ALTER TABLE) and data backfill (UPDATE) in the same migration. Generate the schema migration first with `db:generate`, then create a separate `--custom` migration for the data backfill.
4. **Order matters** — if a data migration depends on a schema migration (e.g., backfilling a column that was just added), the `--custom` migration must come after the schema migration in the journal sequence. Generate the schema migration first, then run the `--custom` command.

### Example: Backfilling a new column

```bash
# Step 1: Add column in schema code, then generate DDL migration
pnpm -F api db:generate

# Step 2: Generate empty custom migration for the backfill
pnpm -F api exec drizzle-kit generate --custom --name=backfill-project-ids

# Step 3: Fill in the generated SQL file with backfill logic
# e.g., UPDATE tests SET project_id = ... FROM runs WHERE ...

# Step 4: Run both migrations
pnpm -F api db:migrate
```

### Common data migration patterns

- **Backfill from join**: `UPDATE target SET col = source.col FROM source WHERE target.fk = source.id AND target.col IS NULL`
- **Backfill with fallback**: First try precise backfill, then assign remaining NULLs to a default value
- **Value conversion**: `UPDATE table SET col = lookup.new_value FROM lookup WHERE lookup.old_value = table.col` (naturally idempotent if old values don't exist in lookup after conversion)

## Decision Rules

### If a migration number or ordering looks wrong

Do not renumber, rename, reorder, or edit journal timestamps to make the sequence prettier.

Instead:
- inspect the current journal, checked-in SQL files, and deploy scripts
- determine whether the issue is cosmetic, generated drift, or already-applied history
- prefer a new forward migration or a documented recovery plan

### If multiple branches generated migrations in parallel

Rebase or merge onto the latest main branch and regenerate from the latest schema state. Do not blindly keep both generated histories without reconciling them.

### If a repo has runtime code for a table that is not in the canonical schema

Do not assume the migration is missing. First determine whether the code is stale or the schema is stale. Remove dead code when the feature path is no longer canonical.

## What to Say Out Loud

When working in this area, explicitly state:
- which schema files are source of truth
- which command you are using to generate migrations
- how you verified the migration path
- whether this is normal feature work or break-glass recovery

## When to Escalate

Escalate before acting if any of these are true:
- production or shared environments may already have divergent migration history
- you think editing old migration files would be the easiest fix
- you are tempted to update `drizzle/meta` manually
- you are considering direct SQL against a non-disposable database

Read [references/why-and-break-glass.md](./references/why-and-break-glass.md) for the rationale and incident-recovery posture.
