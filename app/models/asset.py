"""
素材模型

定义 Image、Video、PDFPage 等素材相关的数据模型。
"""
import datetime

from sqlalchemy import BINARY, Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

# 永久库基类
BaseModel = declarative_base()

# 项目库基类
BaseModelProject = declarative_base()


class ImageMixin:
    """图片模型的公共字段 Mixin"""
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(4096), index=True)  # 文件路径
    modify_time = Column(DateTime, index=True)  # 文件修改时间
    features = Column(BINARY)  # CLIP 特征向量
    checksum = Column(String(40), index=True)  # 文件 SHA1
    
    # 文件属性
    width = Column(Integer)
    height = Column(Integer)
    aspect_ratio = Column(Float, index=True)
    aspect_ratio_standard = Column(String(16), index=True)
    file_size = Column(Integer)
    file_format = Column(String(16))
    
    # 时间戳
    upload_time = Column(DateTime, default=datetime.datetime.now)
    last_accessed = Column(DateTime)
    
    # 分类标签
    category = Column(String(64), index=True)
    sub_category = Column(String(64))
    tags = Column(Text)
    building_type = Column(String(64))
    design_style = Column(String(64), index=True)
    
    # 来源信息
    source_type = Column(String(32), default='local')
    source_project = Column(String(128))
    source_notes = Column(Text)
    
    # 质量管理
    quality_score = Column(Float)
    is_featured = Column(Boolean, default=False)
    
    # 去重
    phash = Column(String(64), index=True)
    duplicate_group = Column(String(64))
    master_image_id = Column(Integer)
    duplicate_type = Column(String(32))
    duplicate_confidence = Column(Float)
    is_duplicate = Column(Boolean, default=False)
    
    # AI 增强
    ai_description = Column(Text)
    ai_description_vector = Column(BINARY)
    
    # 软删除
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_time = Column(DateTime)


class VideoMixin:
    """视频模型的公共字段 Mixin"""
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(4096), index=True)
    frame_time = Column(Integer)  # 帧时间（秒）
    modify_time = Column(DateTime, index=True)
    features = Column(BINARY)
    checksum = Column(String(40), index=True)
    
    # 文件属性
    width = Column(Integer)
    height = Column(Integer)
    aspect_ratio = Column(Float, index=True)
    duration = Column(Integer)
    file_size = Column(Integer)
    file_format = Column(String(16))
    
    # 时间戳
    upload_time = Column(DateTime, default=datetime.datetime.now)
    last_accessed = Column(DateTime)
    
    # 分类标签
    category = Column(String(64), index=True)
    sub_category = Column(String(64))
    tags = Column(Text)
    building_type = Column(String(64))
    design_style = Column(String(64), index=True)
    
    # 来源信息
    source_type = Column(String(32), default='local')
    source_project = Column(String(128))
    source_notes = Column(Text)
    
    # 质量管理
    quality_score = Column(Float)
    is_featured = Column(Boolean, default=False)
    
    # AI 增强
    ai_description = Column(Text)
    ai_description_vector = Column(BINARY)
    
    # 软删除
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_time = Column(DateTime)


class Image(ImageMixin, BaseModel):
    """永久库图片模型"""
    __tablename__ = "image"


class Video(VideoMixin, BaseModel):
    """永久库视频模型"""
    __tablename__ = "video"


class PDFPage(BaseModel):
    """PDF 页面模型"""
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


class ProjectImage(ImageMixin, BaseModelProject):
    """项目库图片模型 - 存储在 proj_*.db"""
    __tablename__ = "image"
    
    # 项目特有字段
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


class ProjectVideo(VideoMixin, BaseModelProject):
    """项目库视频模型 - 存储在 proj_*.db"""
    __tablename__ = "video"
    
    # 项目特有字段
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


class ProjectPDFPage(BaseModelProject):
    """项目 PDF 页面模型"""
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
