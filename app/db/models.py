import datetime as dt
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from app.db.base import Base

class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    tracking_id = Column(String, unique=True, index=True, nullable=False)
    customer_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    postal_code = Column(String, nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="Scheduled")

    created_at = Column(
        DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=dt.datetime.utcnow,
        onupdate=dt.datetime.utcnow)


class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True, index=True)
    tracking_id = Column(String, index=True, nullable=False)
    transcript = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    escalated = Column(Boolean, default=False)
    created_at = Column(
        DateTime, nullable=False, default=dt.datetime.utcnow
    )