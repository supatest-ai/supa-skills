# Why These Rules Exist

## Why generated artifacts must stay generated

Drizzle couples several pieces together:
- schema/model source files
- generated SQL migrations
- `drizzle/meta/_journal.json`
- snapshot files in `drizzle/meta/`
- rows recorded in `__drizzle_migrations`

If an agent edits only one layer by hand, the repo can look correct while fresh databases, existing databases, and deployed environments behave differently.

## Common failure modes

### Hand-written SQL migrations

Agents often create `.sql` files directly because it feels faster. That creates drift between:
- the schema code
- the generated metadata
- the actual migration history Drizzle expects

Default assumption: if the repo uses Drizzle migrations, create them through the repo's Drizzle generate command.

### Editing old migrations

Changing an already-applied migration rewrites history. Some databases will have the old version, some the new version, and the filename alone will hide the mismatch.

Default assumption: once applied anywhere outside a disposable DB, an old migration is frozen.

### Manually editing journal or snapshot files

Those files are not just documentation. They are part of how Drizzle understands migration order and schema history. Manual edits can create out-of-order behavior, skipped migrations, or fresh-db failures that are hard to see in code review.

### Direct database surgery

Manually updating `__drizzle_migrations`, running arbitrary `ALTER TABLE` statements, or repairing prod by hand can be necessary during an incident, but it is not normal feature work. It should never be the default path.

## Break-Glass Recovery Posture

Use this posture only when the user explicitly wants incident recovery or production repair.

1. Stop normal feature work.
2. Document the actual current state:
   - checked-in migration files
   - journal order
   - deployed schema state
   - rows in `__drizzle_migrations`
3. Prefer a forward-only repair over rewriting history.
4. Explain the risk before touching non-disposable databases.
5. Keep repo state and database state aligned before declaring success.

## Heuristics

- If the repo has a checked-in `drizzle/` folder, treat migration generation as part of the source of truth.
- If a fix requires hand-editing generated files, assume you should pause and reassess.
- If a deploy can continue after a failed migration, treat that as a process bug.
- If runtime code references tables missing from the canonical schema, verify whether the code is stale before adding migrations.
