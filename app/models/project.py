"""
项目和去重模型

定义 Project、DedupJob 等管理相关的数据模型。
"""
import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

# 使用与 asset.py 相同的基类
from .asset import BaseModel


class Project(BaseModel):
    """项目模型 - 存储在 projects_metadata.db"""
    __tablename__ = "project"
    
    id = Column(String(128), primary_key=True, index=True)  # proj_2025_万科_01
    name = Column(String(256), nullable=False, index=True)
    client_name = Column(String(256))
    description = Column(Text)
    status = Column(String(32), default='active', index=True)  # active/completed/archived
    created_time = Column(DateTime, default=datetime.datetime.now)
    updated_time = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    image_count = Column(Integer, default=0)
    video_count = Column(Integer, default=0)
    total_size = Column(Integer, default=0)
    database_path = Column(String(1024))
    is_deleted = Column(Boolean, default=False)


class DedupJob(BaseModel):
    """去重任务模型"""
    __tablename__ = "dedup_job"
    
    id = Column(String(64), primary_key=True)
    library_type = Column(String(32), default="permanent", index=True)
    status = Column(String(32), default="pending", index=True)  # pending/running/completed/failed
    current_phase = Column(String(32))  # checksum/phash/clip
    progress_percent = Column(Float, default=0.0)
    total_duplicates = Column(Integer, default=0)
    error_message = Column(Text)
    
    # 时间戳
    created_time = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_time = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    completed_time = Column(DateTime)
    
    # 统计信息
    total_scanned = Column(Integer, default=0)
    duplicate_groups = Column(Integer, default=0)
    duplicates_marked = Column(Integer, default=0)
    space_saving = Column(Integer, default=0)  # bytes
    
    # 报告
    report = Column(Text)  # JSON
    notes = Column(Text)


class PexelsVideo(BaseModel):
    """Pexels 视频模型 - 用于外部视频搜索"""
    __tablename__ = "pexels_video"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128))
    description = Column(String(256))
    duration = Column(Integer, index=True)
    view_count = Column(Integer, index=True)
    thumbnail_loc = Column(String(256))
    content_loc = Column(String(256))
    thumbnail_feature = Column(Integer)  # BINARY in SQLite
