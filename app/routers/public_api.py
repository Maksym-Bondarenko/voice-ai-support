"""
Simple JSON endpoints used by the tests.
They wrap the richer /retell/* logic so the production agent
API stays untouched while pytest can talk to a tiny surface.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, constr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import models
from app.services.email_service import send_reschedule_email

router = APIRouter(tags=["test-helpers"])


# ───────────────────────── /validate ─────────────────────────
class _ValidateIn(BaseModel):
    tracking_id: str = Field(..., min_length=4, max_length=20)
    postal_code: constr(pattern=r"^\d{5}$")


class _ValidateOut(BaseModel):
    eligible: bool
    status: Optional[str] = None


@router.post("/validate", response_model=_ValidateOut)
def validate(body: _ValidateIn, db: Annotated[Session, Depends(get_db)]):
    pkg = (
        db.query(models.Package)
        .filter_by(tracking_id=body.tracking_id.upper())
        .first()
    )
    if not pkg or pkg.postal_code != body.postal_code:
        raise HTTPException(404, "Package not found")

    eligible = pkg.status in {"Out for Delivery", "Scheduled"}
    return _ValidateOut(eligible=eligible, status=pkg.status)


# ───────────────────────── /reschedule ───────────────────────
class _RescheduleIn(BaseModel):
    tracking_id: str = Field(..., min_length=4, max_length=20)
    new_slot: str  # ISO-8601 – may end with “Z”


class _RescheduleOut(BaseModel):
    ok: bool = True


@router.post("/reschedule", response_model=_RescheduleOut)
def reschedule(body: _RescheduleIn, db: Annotated[Session, Depends(get_db)]):
    pkg = (
        db.query(models.Package)
        .filter_by(tracking_id=body.tracking_id.upper())
        .first()
    )
    if not pkg:
        raise HTTPException(404, "Package not found")

    try:
        # allow “Z” suffix
        scheduled_dt = datetime.fromisoformat(
            body.new_slot.replace("Z", "+00:00")
        ).astimezone(timezone.utc)
    except ValueError as exc:
        raise HTTPException(400, "new_slot must be ISO-8601") from exc

    pkg.scheduled_at = scheduled_dt
    pkg.status = "Scheduled"
    db.commit()

    send_reschedule_email(pkg)  # hits n8n email-confirm hook
    return _RescheduleOut()