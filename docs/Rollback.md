# Deployment Rollback Runbook

## When to roll back

Roll back if, after a deploy:

- error rate on `/v1/events` or `/v1/webhooks/*` exceeds 2% for more than 5
  minutes, or
- `/readyz` starts failing on more than one pod, or
- a migration fails partway and leaves the schema in a state the running
  app version doesn't expect.

## Application rollback

1. Identify the last known-good release tag (`git tag --sort=-creatordate | head -5`).
2. Redeploy that tag through the normal deploy pipeline (do **not** hotfix
   forward under pressure - roll back first, fix on a branch after).
3. Confirm `/readyz` is green on all pods before declaring the incident
   resolved.
4. Post a summary in `#pulsemetrics-incidents` with the tag rolled back to
   and a link to the triggering deploy.

## Database rollback

Most releases are additive (new columns, new tables) and do not require a
DB rollback - rolling back the application is enough, since older app code
simply ignores new columns it doesn't know about.

If a migration must be reverted:

```bash
alembic downgrade -1
```

**Warning:** `alembic downgrade` is only safe for schema changes that don't
drop data. If a migration dropped a column or table, downgrading recreates
the column/table but the original data is gone - a downgrade is not a
substitute for a backup restore. Check the migration's `downgrade()` body
before running it in production; if it contains `drop_column` or
`drop_table` in the `upgrade()`, treat the migration as irreversible and
restore from the pre-migration snapshot instead.

## Customer communication

If the rollback affected report data that customers may have already seen
(e.g. a reporting bug produced incorrect numbers for a window before the
fix/rollback):

1. Identify affected orgs via the `reports.generated_at` range that
   overlaps the bad deploy window.
2. Use the status page template below - do not send an ad hoc message,
   the template has already been reviewed by support and legal.

> **Status page template**
> We identified an issue between [start time] and [end time] UTC that
> caused [metric name] in weekly reports to be [inaccurate/delayed]. The
> issue has been resolved and affected reports have been regenerated. No
> underlying event data was lost. If you have questions, reach out to
> support@pulsemetrics.io.

3. For Enterprise accounts, the account's CSM should also send a direct
   note referencing the status page - don't rely on the status page alone
   for our largest accounts.

## Post-incident

File a postmortem within 2 business days using the standard template.
Rollbacks triggered by a failed migration should always include an action
item to add a pre-deploy migration dry-run against a prod snapshot.
