import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from .base import BaseModel


class DedupJob(BaseModel):
    __tablename__ = "dedup_job"

    id = Column(String(64), primary_key=True)
    library_type = Column(String(32), default="permanent", index=True)
    status = Column(String(32), default="pending", index=True)
    phase = Column(String(32))
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    completed_at = Column(DateTime)
    created_by = Column(String(128))
    total_scanned = Column(Integer, default=0)
    duplicate_groups = Column(Integer, default=0)
    duplicates_marked = Column(Integer, default=0)
    space_saving = Column(Integer, default=0)
    report = Column(Text)
    notes = Column(Text)
    error = Column(Text)


class DedupResult(BaseModel):
    __tablename__ = "dedup_result"

    id = Column(String(64), primary_key=True)
    job_id = Column(String(64), index=True)
    image_id = Column(Integer, index=True)
    duplicate_group = Column(String(64), index=True)
    duplicate_type = Column(String(32))
    duplicate_confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)