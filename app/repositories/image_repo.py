"""
图片 Repository

封装图片相关的数据访问操作。
"""
import logging
from typing import Optional, List, Tuple
import numpy as np

from .base import BaseRepository
from app.integrations.sqlite_manager import get_db_manager
from app.models import Image

logger = logging.getLogger(__name__)


class ImageRepository(BaseRepository[Image]):
    """
    图片数据访问类
    
    提供图片的 CRUD 操作和向量搜索功能。
    """
    
    @property
    def table_name(self) -> str:
        return 'images'
    
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
    
    def _sqlite_find_by_id(self, id: int) -> Optional[Image]:
        with self._get_session() as session:
            return session.query(Image).filter(Image.id == id).first()
    
    def _sqlite_find_all(self, limit: int = 100, offset: int = 0) -> List[Image]:
        with self._get_session() as session:
            return session.query(Image).offset(offset).limit(limit).all()
    
    def find_by_path(self, path: str) -> Optional[Image]:
        """根据路径查找图片"""
        with self._get_session() as session:
            return session.query(Image).filter(Image.path == path).first()
    
    def count(self, include_deleted: bool = False) -> int:
        """统计图片数量"""
        with self._get_session() as session:
            query = session.query(Image)
            if not include_deleted:
                from sqlalchemy import or_
                query = query.filter(or_(Image.is_deleted.is_(False), Image.is_deleted.is_(None)))
            return query.count()
    
    def find_with_features(self, limit: int = 10000) -> List[Tuple[int, str, bytes]]:
        """
        获取带有特征向量的图片
        
        Returns:
            List of (id, path, features)
        """
        with self._get_session() as session:
            results = session.query(
                Image.id, Image.path, Image.features
            ).filter(
                Image.features.isnot(None)
            ).limit(limit).all()
            return [(r.id, r.path, r.features) for r in results]
    
    def search_by_vector(
        self, 
        vector: np.ndarray, 
        threshold: float = 0.3, 
        limit: int = 100,
        include_duplicates: bool = False
    ) -> List[dict]:
        """
        向量相似度搜索
        
        Args:
            vector: 查询向量 (512维 CLIP 特征)
            threshold: 相似度阈值
            limit: 返回数量限制
            include_duplicates: 是否包含重复图片
        
        Returns:
            按相似度排序的图片列表
        """
        if self.use_supabase:
            return self._supabase_search_by_vector(vector, threshold, limit)
        else:
            return self._sqlite_search_by_vector(vector, threshold, limit, include_duplicates)
    
    def _sqlite_search_by_vector(
        self, 
        vector: np.ndarray, 
        threshold: float, 
        limit: int,
        include_duplicates: bool
    ) -> List[dict]:
        """SQLite + FAISS 实现向量搜索"""
        # 暂时使用旧实现
        from app.services.search_service import search_image_by_text_path_time
        # TODO: 实现纯 Repository 版本
        logger.warning("search_by_vector 暂时使用旧实现")
        return []
    
    def _supabase_search_by_vector(
        self, 
        vector: np.ndarray, 
        threshold: float, 
        limit: int
    ) -> List[dict]:
        """
        Supabase + pgvector 实现向量搜索
        
        调用 PostgreSQL 函数 search_images_by_vector
        """
        from app.integrations.supabase_client import supabase_rpc
        
        # 将 numpy 数组转换为列表
        vector_list = vector.tolist() if isinstance(vector, np.ndarray) else list(vector)
        
        try:
            response = supabase_rpc('search_images_by_vector', {
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
                        'score': row['similarity'] * 100,  # 转换为百分制
                        'category': row.get('category'),
                        'design_style': row.get('design_style'),
                        'width': row.get('width'),
                        'height': row.get('height'),
                    }
                    for row in response.data
                ]
            return []
        except Exception as e:
            logger.error(f"Supabase 向量搜索失败: {e}")
            return []


# 单例实例
_image_repo_cache = {}


def get_image_repository(target: str = 'permanent') -> ImageRepository:
    """获取图片 Repository 实例（带缓存）"""
    if target not in _image_repo_cache:
        _image_repo_cache[target] = ImageRepository(target)
    return _image_repo_cache[target]
