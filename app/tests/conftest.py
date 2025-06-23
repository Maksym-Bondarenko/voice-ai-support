from __future__ import annotations

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db import models
from app.db.session import get_db
from app.main import app

# ── mount the REAL Voice-AI router, replacing the stub  ──────────────────
from app.routers import voice_ai        # the file with _speak()

# drop any earlier POST /voice-webhook route (added by routers/voice.py)
app.router.routes = [
    r for r in app.router.routes
    if not (isinstance(r, APIRoute)
            and r.path == "/voice-webhook"
            and "POST" in r.methods)
]

# now include the full dialog router
app.include_router(voice_ai.router)

# ───────────────────────────────────────────────────────── In-memory DB
TEST_DB_URL = "sqlite:///:memory:"
# create engine *after* tables exist
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base.metadata.create_all(bind=engine)

# seed one eligible + one ineligible package
with TestSessionLocal() as db:
    db.add(
        models.Package(
            tracking_id="ABC123456",
            postal_code="80331",
            customer_name="Jane Doe",
            phone="000",
            address="X",
            status="Out for Delivery",
        )
    )
    db.add(
        models.Package(
            tracking_id="XYZ999999",
            postal_code="80331",
            customer_name="John",
            phone="000",
            address="X",
            status="Delivered",
        )
    )
    db.commit()

# ───────────────────────────────────────── override dependency
def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# ───────────────────────────────────────── mute outbound webhooks
@pytest.fixture(autouse=True)
def mute_webhooks(monkeypatch):
    calls = []

    def fake_post(url, payload):
        calls.append((url, payload))

    from app.services import email_service

    monkeypatch.setattr(email_service, "_post", fake_post)
    yield calls  # tests can inspect this list


# ───────────────────────────────────────── pytest client
@pytest.fixture(name="client")
def _client():
    # disable secret validation for tests
    settings = get_settings()
    settings.VOICE_WEBHOOK_SECRET = ""
    with TestClient(app) as c:
        yield c