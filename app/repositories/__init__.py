"""
Repository 层

封装数据访问逻辑，支持 Supabase 和 SQLite 双后端。
"""
from .base import BaseRepository, get_use_supabase
from .image_repo import ImageRepository, get_image_repository
from .video_repo import VideoRepository, get_video_repository
from .project_repo import ProjectRepository, get_project_repository
from .user_repo import UserRepository, get_user_repository

__all__ = [
    # 基类
    'BaseRepository',
    'get_use_supabase',
    # 图片
    'ImageRepository',
    'get_image_repository',
    # 视频
    'VideoRepository',
    'get_video_repository',
    # 项目
    'ProjectRepository',
    'get_project_repository',
    # 用户
    'UserRepository',
    'get_user_repository',
]
