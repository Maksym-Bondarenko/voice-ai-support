"""
NOT NECESSARY FOR CURRENT STAND. WAS AN APPROACH FOR RETELL CUSTOM LLM FOR HANDLING CONVERSATION.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import models, schemas

router = APIRouter(prefix="", tags=["voice"])

# --- 1. validate -------------------------------------------------------------

@router.post("/validate", response_model=schemas.ValidateResponse)
def validate(
    payload: schemas.ValidateRequest, db: Session = Depends(get_db)
):
    pkg = (
        db.query(models.Package)
        .filter_by(tracking_id=payload.tracking_id,
                   postal_code=payload.postal_code)
        .first()
    )
    if not pkg:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Package not found or postal code mismatch."
        )

    # process if status is either of the following two
    eligible = pkg.status in {"Out for Delivery", "Scheduled"}
    return schemas.ValidateResponse(
        tracking_id=pkg.tracking_id,
        customer_name=pkg.customer_name,
        status=pkg.status,
        scheduled_at=pkg.scheduled_at,
        eligible=eligible,
    )

# --- 2. reschedule -----------------------------------------------------------

@router.post("/reschedule", response_model=schemas.GenericAck)
def reschedule(
    payload: schemas.RescheduleRequest, db: Session = Depends(get_db)
):
    pkg = db.query(models.Package).filter_by(
        tracking_id=payload.tracking_id
    ).first()
    if not pkg:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Package not found.")

    if pkg.status not in {"Out for Delivery", "Scheduled"}:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Package status ({pkg.status}) not eligible for reschedule.",
        )

    pkg.scheduled_at = payload.new_slot
    pkg.status = "Scheduled"
    pkg.updated_at = datetime.utcnow()
    db.commit()

    # send confirmation email
    from app.services.email_service import send_reschedule_email
    send_reschedule_email(pkg)

    return schemas.GenericAck(ok=True, detail="Rescheduled!")

# --- 3. voice-webhook (entry for Retell/Twilio) ------------------------------
# For now we just log; full dialog management will come next.

@router.post("/voice-webhook", response_model=schemas.GenericAck)
def voice_webhook(event: dict):
    # Retell will POST JSON with call events; store raw for now.
    print("[VOICE] incoming:", event)  # noqa: T201
    return schemas.GenericAck(ok=True)