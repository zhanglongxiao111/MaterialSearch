"""
Repository 基类

提供数据访问层的通用接口和实现。
支持 Supabase 和 SQLite 两种后端。
"""
import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, TypeVar, Generic

logger = logging.getLogger(__name__)

T = TypeVar('T')


def get_use_supabase() -> bool:
    """获取是否使用 Supabase"""
    return os.getenv('USE_SUPABASE', 'false').lower() == 'true'


class BaseRepository(ABC, Generic[T]):
    """
    Repository 基类
    
    所有 Repository 需继承此类并实现抽象方法。
    提供两种后端支持：
    - Supabase (PostgreSQL + pgvector)
    - SQLite (兼容模式)
    """
    
    def __init__(self):
        self._use_supabase = get_use_supabase()
    
    @property
    def use_supabase(self) -> bool:
        return self._use_supabase
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """表名"""
        pass
    
    # =========================================================================
    # 通用 CRUD 操作（子类可覆盖）
    # =========================================================================
    
    def find_by_id(self, id: int) -> Optional[T]:
        """根据 ID 查找记录"""
        if self.use_supabase:
            return self._supabase_find_by_id(id)
        else:
            return self._sqlite_find_by_id(id)
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """查找所有记录"""
        if self.use_supabase:
            return self._supabase_find_all(limit, offset)
        else:
            return self._sqlite_find_all(limit, offset)
    
    def create(self, data: dict) -> T:
        """创建记录"""
        if self.use_supabase:
            return self._supabase_create(data)
        else:
            return self._sqlite_create(data)
    
    def update(self, id: int, data: dict) -> Optional[T]:
        """更新记录"""
        if self.use_supabase:
            return self._supabase_update(id, data)
        else:
            return self._sqlite_update(id, data)
    
    def delete(self, id: int) -> bool:
        """删除记录"""
        if self.use_supabase:
            return self._supabase_delete(id)
        else:
            return self._sqlite_delete(id)
    
    # =========================================================================
    # Supabase 后端实现（子类需实现）
    # =========================================================================
    
    def _supabase_find_by_id(self, id: int) -> Optional[T]:
        raise NotImplementedError("Supabase 后端未实现")
    
    def _supabase_find_all(self, limit: int, offset: int) -> List[T]:
        raise NotImplementedError("Supabase 后端未实现")
    
    def _supabase_create(self, data: dict) -> T:
        raise NotImplementedError("Supabase 后端未实现")
    
    def _supabase_update(self, id: int, data: dict) -> Optional[T]:
        raise NotImplementedError("Supabase 后端未实现")
    
    def _supabase_delete(self, id: int) -> bool:
        raise NotImplementedError("Supabase 后端未实现")
    
    # =========================================================================
    # SQLite 后端实现（子类需实现）
    # =========================================================================
    
    def _sqlite_find_by_id(self, id: int) -> Optional[T]:
        raise NotImplementedError("SQLite 后端未实现")
    
    def _sqlite_find_all(self, limit: int, offset: int) -> List[T]:
        raise NotImplementedError("SQLite 后端未实现")
    
    def _sqlite_create(self, data: dict) -> T:
        raise NotImplementedError("SQLite 后端未实现")
    
    def _sqlite_update(self, id: int, data: dict) -> Optional[T]:
        raise NotImplementedError("SQLite 后端未实现")
    
    def _sqlite_delete(self, id: int) -> bool:
        raise NotImplementedError("SQLite 后端未实现")
