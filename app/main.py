"""FastAPI application entrypoint."""
from fastapi import FastAPI

from app.api import routes_events, routes_health, routes_reports, routes_webhooks
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="PulseMetrics API",
    description="Ingestion, reporting, and webhook API for the PulseMetrics analytics platform.",
    version="0.4.0",
)

app.include_router(routes_health.router)
app.include_router(routes_events.router, prefix="/v1/events", tags=["events"])
app.include_router(routes_reports.router, prefix="/v1/reports", tags=["reports"])
app.include_router(routes_webhooks.router, prefix="/v1/webhooks", tags=["webhooks"])


@app.on_event("startup")
async def on_startup() -> None:
    if settings.is_production:
        # Fail fast if required secrets are still defaults in prod.
        if settings.webhook_signing_secret == "change-me":
            raise RuntimeError("webhook_signing_secret must be set in production")
