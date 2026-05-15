"""Background worker that pre-generates weekly reports for active orgs."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models.user import Organization
from app.services.report_service import generate_weekly_report


def run_weekly_report_sweep() -> int:
    """Pre-warm the report cache for every org. Intended to run nightly."""
    now = datetime.now(timezone.utc)
    period_end = now
    period_start = now - timedelta(days=7)

    generated = 0
    db = SessionLocal()
    try:
        org_ids = [row.id for row in db.query(Organization.id).all()]
        for org_id in org_ids:
            generate_weekly_report(db, org_id, period_start, period_end)
            generated += 1
    finally:
        db.close()
    return generated


if __name__ == "__main__":
    count = run_weekly_report_sweep()
    print(f"Generated {count} weekly reports")
