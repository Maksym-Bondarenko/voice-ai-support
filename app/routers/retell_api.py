"""
MOST IMPORTANT FILE FOR CURRENT STAND (RETELL PART).
"""

# app/routers/retell.py
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, constr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import models
from app.services.email_service import send_reschedule_email

log = logging.getLogger("retell")
router = APIRouter(prefix="/retell", tags=["retell-flow"])


# ──────────────────── helper ────────────────────
def _get_pkg(db: Session, tid: str) -> models.Package | None:
    """Return package row by tracking-ID (case-insensitive)."""
    return db.query(models.Package).filter_by(tracking_id=tid.upper()).first()


# ──────────────────── Pydantic models ────────────────────
class _CheckArgs(BaseModel):
    tracking_id: constr(min_length=4, max_length=20)


class CheckOrderIn(BaseModel):
    call: dict
    name: str
    args: _CheckArgs


class CheckOrderOut(BaseModel):
    found: bool
    delivered: Optional[bool] = None
    status: Optional[str] = None
    customer_name: Optional[str] = None


class DeliverySlot(str, Enum):
    tomorrow_am = "tomorrow_am"
    tomorrow_pm = "tomorrow_pm"
    saturday_am = "saturday_am"


class RescheduleArgs(BaseModel):
    tracking_id: constr(min_length=4, max_length=20)
    postal_code: constr(pattern=r"^\d{5}$")          # simple 5-digit ZIP check
    delivery_slot: DeliverySlot


class RescheduleBody(BaseModel):
    call: dict
    name: str
    args: RescheduleArgs


class RescheduleOut(BaseModel):
    label: str                                        # e.g. "tomorrow morning"
    scheduled: str                                    # ISO-8601 string


# ──────────────────── slot mapping ────────────────────
def _next_saturday_morning(now: datetime) -> datetime:
    """Return next Saturday 09:00 in UTC (≥ 7 days ahead if today is Sat)."""
    days_ahead = (5 - now.weekday()) % 7 or 7        # weekday(): Mon=0 … Sun=6
    target = (now + timedelta(days=days_ahead)).replace(
        hour=9, minute=0, second=0, microsecond=0
    )
    return target


SLOT_MAP = {
    DeliverySlot.tomorrow_am: (
        "tomorrow morning",
        lambda n: (n + timedelta(days=1)).replace(
            hour=9, minute=0, second=0, microsecond=0
        ),
    ),
    DeliverySlot.tomorrow_pm: (
        "tomorrow afternoon",
        lambda n: (n + timedelta(days=1)).replace(
            hour=15, minute=0, second=0, microsecond=0
        ),
    ),
    DeliverySlot.saturday_am: ("Saturday morning", _next_saturday_morning),
}


# ──────────────────── routes ────────────────────
@router.post("/check-order", response_model=CheckOrderOut)
def check_order(
    body: CheckOrderIn, request: Request, db: Session = Depends(get_db)
):
    tid = body.args.tracking_id.upper()
    log.info("🔍 /check-order  tid=%s  headers=%s", tid, dict(request.headers))

    pkg = _get_pkg(db, tid)
    if not pkg:
        return CheckOrderOut(found=False)

    return CheckOrderOut(
        found=True,
        delivered=pkg.status.lower() == "delivered",
        status=pkg.status,
        customer_name=pkg.customer_name,
    )


@router.post("/reschedule-order", response_model=RescheduleOut)
def reschedule_order(
    body: RescheduleBody, request: Request, db: Session = Depends(get_db)
):
    log.info("📅 /reschedule-order  headers=%s", dict(request.headers))

    tid = body.args.tracking_id.upper()
    slot_key = body.args.delivery_slot

    label, ts_fn = SLOT_MAP[slot_key]
    scheduled_dt = ts_fn(datetime.now(timezone.utc))

    pkg = _get_pkg(db, tid)
    if not pkg:
        raise HTTPException(404, "tracking id not found")

    # update DB
    pkg.scheduled_at = scheduled_dt
    pkg.status = "Scheduled"
    db.commit()

    send_reschedule_email(pkg)

    db.add(
        models.CallLog(
            tracking_id=tid,
            transcript=f"Rescheduled to {label}",
            completed=True,
            escalated=False,
        )
    )
    db.commit()

    return RescheduleOut(label=label, scheduled=scheduled_dt.isoformat())


# Retell heartbeat
@router.post("")
def ping(request: Request):
    log.info("💓  /retell  ping  headers=%s", dict(request.headers))
    return {"ok": "retell up"}