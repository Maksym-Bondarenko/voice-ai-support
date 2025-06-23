"""Very small in-memory session store for demo purposes."""
from __future__ import annotations
from enum import Enum
from datetime import datetime

class Stage(str, Enum):
    WAIT_TRACKING = "wait_tracking"
    WAIT_POSTAL   = "wait_postal"
    WAIT_SLOT     = "wait_slot"
    DONE          = "done"

class Session:
    def __init__(self, call_id: str) -> None:
        self.call_id = call_id
        self.stage = Stage.WAIT_TRACKING
        self.tracking_id: str | None = None
        self.postal_code: str | None = None
        self.slot: str | None = None
        self.created = datetime.utcnow()

_SESSIONS: dict[str, Session] = {}

def get(call_id: str) -> Session:
    return _SESSIONS.setdefault(call_id, Session(call_id))
