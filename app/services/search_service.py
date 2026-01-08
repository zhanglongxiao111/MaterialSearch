"""
搜索服务

封装搜索业务逻辑，协调 Repository 完成复杂搜索操作。
"""
import logging
from typing import List, Dict, Any, Optional

import numpy as np

from app.repositories.image_repo import get_image_repository
from app.repositories.video_repo import get_video_repository

logger = logging.getLogger(__name__)


class SearchService:
    """
    搜索服务类
    
    提供图片和视频的语义搜索功能。
    """
    
    def __init__(self, target: str = 'permanent'):
        """
        初始化
        
        Args:
            target: 目标库，'permanent' 或 'proj_xxx'
        """
        self.target = target
        self._image_repo = get_image_repository(target)
        self._video_repo = get_video_repository(target)
    
    def search_images_by_text(
        self,
        positive_prompt: str,
        negative_prompt: str = "",
        positive_threshold: float = 0.27,
        negative_threshold: float = 0.27,
        path_filter: str = "",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        include_duplicates: bool = False,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        文字搜索图片
        
        Args:
            positive_prompt: 正向搜索词
            negative_prompt: 反向搜索词（排除）
            positive_threshold: 正向阈值
            negative_threshold: 反向阈值
            path_filter: 路径过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            include_duplicates: 是否包含重复图片
            limit: 返回数量限制
        
        Returns:
            匹配的图片列表
        """
        # 暂时使用旧实现
        from search import search_image_by_text_path_time
        
        project_id = self.target if self.target.startswith('proj_') else None
        library_type = 'project' if project_id else 'permanent'
        
        return search_image_by_text_path_time(
            positive_prompt, negative_prompt,
            positive_threshold, negative_threshold,
            path_filter, start_time, end_time,
            library_type, project_id,
            include_duplicates=include_duplicates
        )[:limit]
    
    def search_images_by_image(
        self,
        image_source: Any,  # 可以是路径、ID 或特征向量
        threshold: float = 0.9,
        path_filter: str = "",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        include_duplicates: bool = False,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        图片搜索图片
        
        Args:
            image_source: 图片来源（路径、ID 或特征向量）
            threshold: 相似度阈值
            path_filter: 路径过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            include_duplicates: 是否包含重复图片
            limit: 返回数量限制
        
        Returns:
            相似图片列表
        """
        # 暂时使用旧实现
        from search import search_image_by_image
        
        project_id = self.target if self.target.startswith('proj_') else None
        library_type = 'project' if project_id else 'permanent'
        
        return search_image_by_image(
            image_source, threshold,
            path_filter, start_time, end_time,
            library_type, project_id,
            include_duplicates=include_duplicates
        )[:limit]
    
    def search_videos_by_text(
        self,
        positive_prompt: str,
        negative_prompt: str = "",
        positive_threshold: float = 0.27,
        negative_threshold: float = 0.27,
        path_filter: str = "",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        文字搜索视频
        
        Args:
            positive_prompt: 正向搜索词
            negative_prompt: 反向搜索词
            positive_threshold: 正向阈值
            negative_threshold: 反向阈值
            path_filter: 路径过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            limit: 返回数量限制
        
        Returns:
            匹配的视频片段列表
        """
        # 暂时使用旧实现
        from search import search_video_by_text_path_time
        
        project_id = self.target if self.target.startswith('proj_') else None
        library_type = 'project' if project_id else 'permanent'
        
        return search_video_by_text_path_time(
            positive_prompt, negative_prompt,
            positive_threshold, negative_threshold,
            path_filter, start_time, end_time,
            library_type, project_id
        )[:limit]
    
    def search_videos_by_image(
        self,
        image_source: Any,
        threshold: float = 0.9,
        path_filter: str = "",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        图片搜索视频
        
        Args:
            image_source: 图片来源
            threshold: 相似度阈值
            path_filter: 路径过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            limit: 返回数量限制
        
        Returns:
            相似视频片段列表
        """
        # 暂时使用旧实现
        from search import search_video_by_image
        
        project_id = self.target if self.target.startswith('proj_') else None
        library_type = 'project' if project_id else 'permanent'
        
        return search_video_by_image(
            image_source, threshold,
            path_filter, start_time, end_time,
            library_type, project_id
        )[:limit]
    
    def calculate_similarity(
        self,
        text: str,
        image_source: Any
    ) -> float:
        """
        计算文本和图片的相似度
        
        Args:
            text: 文本
            image_source: 图片来源
        
        Returns:
            相似度分数 (0-100)
        """
        from process_assets import match_text_and_image, process_image, process_text
        
        text_features = process_text(text)
        image_features = process_image(image_source)
        score = match_text_and_image(text_features, image_features) * 100
        return score


# 服务实例缓存
_search_service_cache = {}


def get_search_service(target: str = 'permanent') -> SearchService:
    """获取搜索服务实例"""
    if target not in _search_service_cache:
        _search_service_cache[target] = SearchService(target)
    return _search_service_cache[target]
