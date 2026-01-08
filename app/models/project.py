import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from .base import BaseModel


class Project(BaseModel):
    __tablename__ = "project"

    id = Column(String(128), primary_key=True, index=True)
    name = Column(String(256), nullable=False, index=True)
    client_name = Column(String(256))
    description = Column(Text)
    status = Column(String(32), default="active", index=True)
    created_time = Column(DateTime, default=datetime.datetime.now)
    updated_time = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    image_count = Column(Integer, default=0)
    video_count = Column(Integer, default=0)
    total_size = Column(Integer, default=0)
    database_path = Column(String(1024))
    is_deleted = Column(Boolean, default=False)