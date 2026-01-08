from sqlalchemy import BINARY, Boolean, Column, DateTime, Integer, String

from .base import BaseModel, BaseModelProject


class PDFPage(BaseModel):
    __tablename__ = "pdf_page"

    id = Column(Integer, primary_key=True, index=True)
    source_path = Column(String(4096), index=True)
    page_no = Column(Integer, index=True)
    page_count = Column(Integer)
    is_primary = Column(Boolean, default=False, index=True)
    pages_truncated = Column(Boolean, default=False)
    modify_time = Column(DateTime, index=True)
    checksum = Column(String(40), index=True)
    features = Column(BINARY)
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)
    thumbnail_path = Column(String(4096))
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_time = Column(DateTime)


class ProjectPDFPage(BaseModelProject):
    __tablename__ = "pdf_page"

    id = Column(Integer, primary_key=True, index=True)
    source_path = Column(String(4096), index=True)
    page_no = Column(Integer, index=True)
    page_count = Column(Integer)
    is_primary = Column(Boolean, default=False, index=True)
    pages_truncated = Column(Boolean, default=False)
    modify_time = Column(DateTime, index=True)
    checksum = Column(String(40), index=True)
    features = Column(BINARY)
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)
    thumbnail_path = Column(String(4096))
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_time = Column(DateTime)