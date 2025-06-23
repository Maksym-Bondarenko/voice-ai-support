"""
NOT NECESSARY FOR CURRENT STAND. WAS AN APPROACH FOR RETELL CUSTOM LLM FOR HANDLING CONVERSATION.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import models
from app.services.email_service import send_reschedule_email

log = logging.getLogger("voice-test")
router = APIRouter()

# in-memory finite-state machine per call_id
_sessions: dict[str, dict] = {}


class _Webhook(BaseModel):
    event: str
    call_id: str
    transcript: Optional[str] = None
    full_transcript: Optional[str] = None


# ───────────────────────── helpers ────────────────────────────
def _schedule(pkg: models.Package, dt: datetime, db: Session):
    pkg.scheduled_at = dt
    pkg.status = "Scheduled"
    db.commit()
    send_reschedule_email(pkg)
    log.info("📧 email-confirm fired for %s", pkg.tracking_id)


# ───────────────────────── main handler ───────────────────────
@router.post("/voice-webhook")
def voice_webhook(body: _Webhook, db: Session = Depends(get_db)):
    cid = body.call_id

    # ── call started ──
    if body.event == "call_started":
        _sessions[cid] = {"stage": "await_tracking"}
        return {"response": {"text": "Hello, please say your tracking number."}}

    # ── normal speech ──
    if body.event == "transcript":
        sess = _sessions.get(cid) or {}
        stage = sess.get("stage")

        # 1) tracking ID
        if stage == "await_tracking":
            sess.update(
                stage="await_postal",
                tracking_id=body.transcript.strip().upper(),
            )
            return {"response": {"text": "Thanks! What's your 5-digit postal code?"}}

        # 2) postal code
        if stage == "await_postal":
            sess.update(stage="await_slot", postal=body.transcript.strip())
            return {
                "response": {
                    "text": "Great. Choose a slot: 1) tomorrow morning "
                    "2) tomorrow afternoon 3) Saturday morning."
                }
            }

        # 3) slot choice
        if stage == "await_slot":
            choice = body.transcript.strip()
            if choice not in {"1", "2", "3"}:
                return {"response": {"text": "Please say 1, 2 or 3."}}

            now = datetime.now(timezone.utc)
            slot_map = {
                "1": now.replace(hour=9, minute=0, second=0, microsecond=0)
                + timedelta(days=1),
                "2": now.replace(hour=15, minute=0, second=0, microsecond=0)
                + timedelta(days=1),
                "3": (
                    now
                    + timedelta(days=(5 - now.weekday()) % 7 or 7)
                ).replace(hour=9, minute=0, second=0, microsecond=0),
            }
            scheduled_dt = slot_map[choice]

            pkg = (
                db.query(models.Package)
                .filter_by(tracking_id=sess["tracking_id"])
                .first()
            )
            if pkg:
                _schedule(pkg, scheduled_dt, db)

            sess["stage"] = "done"
            return {
                "response": {
                    "text": "All set — your delivery was rescheduled. Goodbye!"
                }
            }

        # default fallback
        return {"response": {"text": "Just to confirm – was that correct? Yes or no?"}}

    # ── call ended ──
    if body.event == "call_ended":
        sess = _sessions.pop(cid, None) or {}
        db.add(
            models.CallLog(
                tracking_id=sess.get("tracking_id", "?"),
                transcript=body.full_transcript or "",
                completed=True,
                escalated=False,
            )
        )
        db.commit()
        return {"ok": True}

    raise HTTPException(400, "Unknown event")


def handle_call():
    return None