# Architecture

## Overview

PulseMetrics API is the ingestion and reporting backend for the PulseMetrics
analytics platform. Customers send events either directly via the `/v1/events`
API or indirectly via provider webhooks (Stripe, Segment, custom) at
`/v1/webhooks/{provider}`. We aggregate those events into weekly reports that
power the customer-facing dashboard.

## Components

- **API layer** (`app/api/`) - FastAPI routers for events, reports, webhooks,
  and health checks. Thin - validation and business logic live in `services/`.
- **Services** (`app/services/`) - core business logic: validation, caching,
  report generation, webhook processing.
- **Models** (`app/models/`) - SQLAlchemy 2.0 declarative models, one table
  per module.
- **Workers** (`app/workers/`) - background jobs invoked by a scheduler
  (cron in staging, a k8s CronJob in production). Not run in-process with the
  API.
- **migrations/** - Alembic migrations, one per schema change.

## Data flow

1. Events arrive via the ingestion API or a provider webhook.
2. Webhook payloads are persisted as raw `WebhookEvent` rows and processed
   asynchronously; the ingestion API persists `Event` rows synchronously.
3. `report_worker` pre-generates weekly reports on a schedule; the reports
   endpoint also generates on demand and caches the result in Redis.
4. `cache_invalidation_worker` sweeps for orgs with new events and evicts
   their cached report so the next read picks up fresh data.

## Datastore

PostgreSQL is the system of record. Redis is used only as a cache - nothing
in Redis is authoritative, and losing the cache should never lose data, only
cause a slower next read.

## Tradeoffs worth knowing

- We use polling-based cache invalidation (a periodic worker) rather than a
  pub/sub push model, because most orgs don't need sub-minute freshness and
  polling is much simpler to operate. Time-sensitive paths (see the cache
  invalidation fix in PR #101) invalidate synchronously on write instead of
  waiting for the sweep.
- Webhook processing is split into "receive and persist" (synchronous, fast,
  always durable) and "process" (async, can retry) so that a slow downstream
  dependency never causes us to drop a webhook or make a provider retry
  unnecessarily.
