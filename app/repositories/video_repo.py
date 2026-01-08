"""
视频 Repository

封装视频相关的数据访问操作。
"""
import logging
from typing import Optional, List, Tuple
import numpy as np

from .base import BaseRepository
from app.integrations.sqlite_manager import get_db_manager
from app.models import Video

logger = logging.getLogger(__name__)


class VideoRepository(BaseRepository[Video]):
    """
    视频数据访问类
    
    提供视频的 CRUD 操作和向量搜索功能。
    """
    
    @property
    def table_name(self) -> str:
        return 'videos'
    
    def __init__(self, target: str = 'permanent'):
        """
        初始化
        
        Args:
            target: 目标库，'permanent' 或 'proj_xxx'
        """
        super().__init__()
        self.target = target
        self._db_manager = get_db_manager()
    
    def _get_session(self):
        """获取数据库 session"""
        if self.target == 'permanent':
            return self._db_manager.get_permanent_session()
        elif self.target.startswith('proj_'):
            return self._db_manager.get_project_session(self.target)
        else:
            raise ValueError(f"无效的目标库: {self.target}")
    
    # =========================================================================
    # SQLite 后端实现
    # =========================================================================
    
    def _sqlite_find_by_id(self, id: int) -> Optional[Video]:
        with self._get_session() as session:
            return session.query(Video).filter(Video.id == id).first()
    
    def _sqlite_find_all(self, limit: int = 100, offset: int = 0) -> List[Video]:
        with self._get_session() as session:
            return session.query(Video).offset(offset).limit(limit).all()
    
    def find_by_path(self, path: str) -> List[Video]:
        """根据路径查找视频（可能有多帧）"""
        with self._get_session() as session:
            return session.query(Video).filter(Video.path == path).all()
    
    def count(self, include_deleted: bool = False) -> int:
        """统计视频帧数量"""
        with self._get_session() as session:
            query = session.query(Video)
            if not include_deleted:
                from sqlalchemy import or_
                query = query.filter(or_(Video.is_deleted.is_(False), Video.is_deleted.is_(None)))
            return query.count()
    
    def count_unique_videos(self, include_deleted: bool = False) -> int:
        """统计唯一视频数量"""
        with self._get_session() as session:
            from sqlalchemy import func
            query = session.query(func.count(func.distinct(Video.path)))
            if not include_deleted:
                from sqlalchemy import or_
                query = query.filter(or_(Video.is_deleted.is_(False), Video.is_deleted.is_(None)))
            return query.scalar() or 0
    
    def find_with_features(self, limit: int = 10000) -> List[Tuple[int, str, int, bytes]]:
        """
        获取带有特征向量的视频帧
        
        Returns:
            List of (id, path, frame_time, features)
        """
        with self._get_session() as session:
            results = session.query(
                Video.id, Video.path, Video.frame_time, Video.features
            ).filter(
                Video.features.isnot(None)
            ).limit(limit).all()
            return [(r.id, r.path, r.frame_time, r.features) for r in results]
    
    def search_by_vector(
        self, 
        vector: np.ndarray, 
        threshold: float = 0.3, 
        limit: int = 100
    ) -> List[dict]:
        """
        向量相似度搜索视频
        
        Args:
            vector: 查询向量 (512维 CLIP 特征)
            threshold: 相似度阈值
            limit: 返回数量限制
        
        Returns:
            按相似度排序的视频列表
        """
        if self.use_supabase:
            return self._supabase_search_by_vector(vector, threshold, limit)
        else:
            return self._sqlite_search_by_vector(vector, threshold, limit)
    
    def _sqlite_search_by_vector(
        self, 
        vector: np.ndarray, 
        threshold: float, 
        limit: int
    ) -> List[dict]:
        """SQLite + FAISS 实现向量搜索"""
        # TODO: 实现纯 Repository 版本
        logger.warning("video search_by_vector 暂时使用旧实现")
        return []
    
    def _supabase_search_by_vector(
        self, 
        vector: np.ndarray, 
        threshold: float, 
        limit: int
    ) -> List[dict]:
        """
        Supabase + pgvector 实现向量搜索
        
        调用 PostgreSQL 函数 search_videos_by_vector
        """
        from app.integrations.supabase_client import supabase_rpc
        
        vector_list = vector.tolist() if isinstance(vector, np.ndarray) else list(vector)
        
        try:
            response = supabase_rpc('search_videos_by_vector', {
                'query_vector': vector_list,
                'similarity_threshold': threshold,
                'result_limit': limit,
                'include_deleted': False
            }).execute()
            
            if response.data:
                return [
                    {
                        'id': row['id'],
                        'path': row['path'],
                        'frame_time': row['frame_time'],
                        'score': row['similarity'] * 100,
                        'duration': row.get('duration'),
                    }
                    for row in response.data
                ]
            return []
        except Exception as e:
            logger.error(f"Supabase 视频向量搜索失败: {e}")
            return []


# 单例实例缓存
_video_repo_cache = {}


def get_video_repository(target: str = 'permanent') -> VideoRepository:
    """获取视频 Repository 实例（带缓存）"""
    if target not in _video_repo_cache:
        _video_repo_cache[target] = VideoRepository(target)
    return _video_repo_cache[target]
