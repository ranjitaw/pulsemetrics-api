"""Weekly report endpoint."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_org_id
from app.services.report_service import generate_weekly_report

router = APIRouter()


@router.get("/weekly")
def get_weekly_report(
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    db: Session = Depends(get_db),
    org_id: str = Depends(get_org_id),
) -> dict:
    return generate_weekly_report(db, org_id, period_start, period_end)
