"""
数据模型层

定义数据库表结构和数据传输对象。
"""
from .asset import (
    BaseModel,
    BaseModelProject,
    Image,
    Video,
    PDFPage,
    ProjectImage,
    ProjectVideo,
    ProjectPDFPage,
    ImageMixin,
    VideoMixin,
)
from .project import (
    Project,
    DedupJob,
    PexelsVideo,
)

__all__ = [
    # 基类
    'BaseModel',
    'BaseModelProject',
    # 永久库模型
    'Image',
    'Video',
    'PDFPage',
    # 项目库模型
    'ProjectImage',
    'ProjectVideo',
    'ProjectPDFPage',
    # 管理模型
    'Project',
    'DedupJob',
    'PexelsVideo',
    # Mixins
    'ImageMixin',
    'VideoMixin',
]
