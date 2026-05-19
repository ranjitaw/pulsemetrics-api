# API Reference

Base URL: `https://api.pulsemetrics.io`

All endpoints require an `X-Org-Id` header identifying the calling
organization. In production this header is set by the API gateway after
validating the caller's API key.

## POST /v1/events

Ingest a single analytics event.

### Request body

| field | type | required | notes |
|---|---|---|---|
| event_type | string | yes | alphanumeric + underscores |
| occurred_at | ISO-8601 datetime | yes | when the event happened on the client |
| payload | object | no | arbitrary JSON, max 32KB |
| source | string | no | defaults to `"api"` |

### Response

`201 Created` with the persisted event.

## GET /v1/reports/weekly

Fetch (or generate) a weekly rollup report for the calling org.

### Query params

| param | type | required |
|---|---|---|
| period_start | ISO-8601 datetime | yes |
| period_end | ISO-8601 datetime | yes |

## POST /v1/webhooks/{provider}

Receive a webhook from an upstream provider (`stripe`, `segment`, etc).
Returns `202 Accepted` immediately after durably persisting the payload;
processing happens asynchronously.

## GET /healthz, GET /readyz

Liveness and readiness probes.
