import datetime

from sqlalchemy import BINARY, Boolean, Column, DateTime, Float, Integer, String, Text

from .base import BaseModel, BaseModelProject


class ImageMixin:
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(4096), index=True)
    modify_time = Column(DateTime, index=True)
    features = Column(BINARY)
    checksum = Column(String(40), index=True)

    width = Column(Integer)
    height = Column(Integer)
    aspect_ratio = Column(Float, index=True)
    aspect_ratio_standard = Column(String(16), index=True)
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

    phash = Column(String(64), index=True)
    duplicate_group = Column(String(64))
    master_image_id = Column(Integer)
    duplicate_type = Column(String(32))
    duplicate_confidence = Column(Float)
    is_duplicate = Column(Boolean, default=False)

    ai_description = Column(Text)
    ai_description_vector = Column(BINARY)

    is_deleted = Column(Boolean, default=False, index=True)
    deleted_time = Column(DateTime)


class Image(ImageMixin, BaseModel):
    __tablename__ = "image"


class ProjectImage(ImageMixin, BaseModelProject):
    __tablename__ = "image"

    image_type = Column(String(32), index=True)
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