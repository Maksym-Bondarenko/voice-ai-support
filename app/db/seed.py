"""
Run once:  python -m app.db.seed
"""

from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.db import models

SAMPLE = [
    # Eligible: “Out for Delivery” so Voice AI can reschedule
    dict(
        tracking_id="ABC123456",
        customer_name="Jane Doe",
        phone="+49123456789",
        address="Example Str. 1, 80331 München",
        postal_code="80331",
        scheduled_at=datetime.utcnow() + timedelta(hours=2),
        status="Out for Delivery",
    ),
    # Ineligible: already delivered
    dict(
        tracking_id="XYZ987654",
        customer_name="John Smith",
        phone="+49123456780",
        address="Another Str. 2, 50667 Köln",
        postal_code="50667",
        scheduled_at=datetime.utcnow() - timedelta(days=1),
        status="Delivered",
    ),
]

def main() -> None:
    db = SessionLocal()
    for pkg in SAMPLE:
        if not db.query(models.Package).filter_by(
            tracking_id=pkg["tracking_id"]
        ).first():
            db.add(models.Package(**pkg))
    db.commit()
    db.close()
    print("Seeded demo packages.")

if __name__ == "__main__":
    main()