# API Reference

Base URL: `https://api.pulsemetrics.io`

All endpoints require an `X-Org-Id` header identifying the calling
organization. In production this header is set by the API gateway after
validating the caller's API key.

## Rate limits

| plan | requests/minute (events) | requests/minute (reports) |
|---|---|---|
| free | 60 | 10 |
| pro | 600 | 60 |
| enterprise | negotiated | negotiated |

Responses that are rate limited return `429` with a `Retry-After` header
(seconds). Rate limits are enforced per org, not per API key.

## POST /v1/events

Ingest a single analytics event.

### Request body

| field | type | required | notes |
|---|---|---|---|
| event_type | string | yes | alphanumeric + underscores |
| occurred_at | ISO-8601 datetime | yes | must not be more than ~2 minutes ahead of server time |
| payload | object | no | arbitrary JSON, max 32KB |
| source | string | no | defaults to `"api"` |

`occurred_at` too far in the future returns a `422` with the measured clock
skew in the error detail - this usually means the sending client's clock is
wrong, not that our validation is broken.

### Response

`201 Created` with the persisted event.

### Example

```bash
curl -X POST https://api.pulsemetrics.io/v1/events \
  -H "X-Org-Id: org_123" \
  -H "Content-Type: application/json" \
  -d '{"event_type": "signup", "occurred_at": "2026-06-20T18:04:00Z", "payload": {"plan": "pro"}}'
```

## GET /v1/reports/weekly

Fetch (or generate) a weekly rollup report for the calling org.

### Query params

| param | type | required |
|---|---|---|
| period_start | ISO-8601 datetime | yes |
| period_end | ISO-8601 datetime | yes |

Reports are cached for 5 minutes per org/period; a write to that org
invalidates the cache immediately, so you'll never read data that's older
than your own most recent write.

## Pagination

Endpoints that can return large result sets (currently none of the
endpoints below - flagged here in advance of the upcoming `GET /v1/events`
list endpoint) will use cursor-based pagination: a `cursor` query param in
the response's `next_cursor` field, not a `page` number. Page-number
pagination breaks under concurrent writes because rows can shift between
pages; a cursor doesn't have that problem.

## POST /v1/webhooks/{provider}

Receive a webhook from an upstream provider (`stripe`, `segment`, etc).
Returns `202 Accepted` immediately after durably persisting the payload;
processing happens asynchronously.

### Delivery guarantees

We de-duplicate on `(provider, external_id)`. If you redeliver the same
event (e.g. after a timeout on your end), we return
`{"status": "duplicate_ignored"}` with a `202` rather than an error - treat
this as a successful delivery. We do not currently expose a way to look up
whether a given `external_id` was previously received other than via this
response.

### Example: subscribing to Stripe events

1. In the Stripe dashboard, add an endpoint pointing at
   `https://api.pulsemetrics.io/v1/webhooks/stripe`.
2. Select the events you care about (we recommend starting with
   `invoice.paid` and `customer.subscription.updated`).
3. We recommend configuring a generous timeout on Stripe's side (10s+) -
   webhook receipt is synchronous and fast, but a slow network hop
   shouldn't cause Stripe to consider the delivery failed and retry
   unnecessarily.

## GET /healthz, GET /readyz

Liveness and readiness probes.
