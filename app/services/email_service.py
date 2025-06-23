import json
import httpx
from datetime import datetime
from typing import Literal

from app.core.config import get_settings
from app.db.models import Package

settings = get_settings()

def _post(url: str, payload: dict) -> None:
    headers = {}
    if settings.N8N_API_KEY:
        headers["X-N8N-API-KEY"] = settings.N8N_API_KEY
    try:
        r = httpx.post(url, json=payload, headers=headers, timeout=5)
        r.raise_for_status()
    except Exception as exc:
        print(f"[WEBHOOK] call failed: {exc}")


def send_reschedule_email(pkg: Package) -> None:
    """Notify customer of new delivery slot."""
    if not settings.EMAIL_WEBHOOK_URL:
        print("[EMAIL-WEBHOOK] skipped (no URL set)")
        return

    payload = {
        "type": "delivery_rescheduled",
        "recipient": pkg.customer_name,
        "email": pkg.phone,
        "tracking_id": pkg.tracking_id,
        "new_slot": pkg.scheduled_at.isoformat() if pkg.scheduled_at else None,
        "timestamp": datetime.utcnow().isoformat(),
    }
    _post(settings.EMAIL_WEBHOOK_URL, payload)


def escalate_to_support(pkg: Package, reason: str) -> None:
    """Route customer to human agent via support webhook in n8n."""
    if not settings.SUPPORT_WEBHOOK_URL:
        print("[SUPPORT-WEBHOOK] skipped (no URL set)")
        return

    payload = {
        "type": "escalation",
        "tracking_id": pkg.tracking_id,
        "customer_name": pkg.customer_name,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
    }
    _post(settings.SUPPORT_WEBHOOK_URL, payload)