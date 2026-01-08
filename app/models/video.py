import datetime

from sqlalchemy import BINARY, Boolean, Column, DateTime, Float, Integer, String, Text

from .base import BaseModel, BaseModelProject, BaseModelPexelsVideo


class VideoMixin:
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(4096), index=True)
    frame_time = Column(Integer)
    modify_time = Column(DateTime, index=True)
    features = Column(BINARY)
    checksum = Column(String(40), index=True)

    width = Column(Integer)
    height = Column(Integer)
    aspect_ratio = Column(Float, index=True)
    duration = Column(Integer)
    file_size = Column(Integer)
    file_format = Column(String(16))

    upload_time = Column(DateTime, default=datetime.datetime.now)
    last_accessed = Column(DateTime)

    category = Column(String(64), index=True)
    sub_category = Column(String(64))
    tags = Column(Text)
    building_type = Column(String(64))
    design_style = Column(String(64), index=True)

    source_type = Column(String(32), default="local")
    source_project = Column(String(128))
    source_notes = Column(Text)

    quality_score = Column(Float)
    is_featured = Column(Boolean, default=False)

    ai_description = Column(Text)
    ai_description_vector = Column(BINARY)

    is_deleted = Column(Boolean, default=False, index=True)
    deleted_time = Column(DateTime)


class Video(VideoMixin, BaseModel):
    __tablename__ = "video"


class ProjectVideo(VideoMixin, BaseModelProject):
    __tablename__ = "video"

    video_type = Column(String(32), index=True)
    stage = Column(String(32))
    space_type = Column(String(64))

    version = Column(Integer, default=1)
    parent_id = Column(Integer)

    is_approved = Column(Boolean, default=False)
    approved_by = Column(String(128))
    approved_time = Column(DateTime)

    archived = Column(Boolean, default=False, index=True)
    archived_to_id = Column(Integer)
    archived_time = Column(DateTime)


class PexelsVideo(BaseModelPexelsVideo):
    __tablename__ = "PexelsVideo"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128))
    description = Column(String(256))
    duration = Column(Integer, index=True)
    view_count = Column(Integer, index=True)
    thumbnail_loc = Column(String(256))
    content_loc = Column(String(256))
    thumbnail_feature = Column(BINARY)