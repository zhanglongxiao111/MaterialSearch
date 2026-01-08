"""
项目 Repository

封装项目相关的数据访问操作。
"""
import logging
from typing import Optional, List

from .base import BaseRepository
from database import get_db_manager
from models import Project

logger = logging.getLogger(__name__)


class ProjectRepository(BaseRepository[Project]):
    """
    项目数据访问类
    
    提供项目的 CRUD 操作。
    """
    
    @property
    def table_name(self) -> str:
        return 'projects'
    
    def __init__(self):
        super().__init__()
        self._db_manager = get_db_manager()
    
    def _get_session(self):
        """获取项目元数据 session"""
        return self._db_manager.get_projects_metadata_session()
    
    # =========================================================================
    # SQLite 后端实现
    # =========================================================================
    
    def _sqlite_find_by_id(self, id: str) -> Optional[Project]:
        with self._get_session() as session:
            return session.query(Project).filter(Project.id == id).first()
    
    def _sqlite_find_all(self, limit: int = 100, offset: int = 0) -> List[Project]:
        with self._get_session() as session:
            return session.query(Project).offset(offset).limit(limit).all()
    
    def find_by_status(
        self, 
        status: Optional[str] = None, 
        include_deleted: bool = False
    ) -> List[Project]:
        """根据状态查找项目"""
        with self._get_session() as session:
            query = session.query(Project)
            
            if not include_deleted:
                from sqlalchemy import or_
                query = query.filter(or_(Project.is_deleted.is_(False), Project.is_deleted.is_(None)))
            
            if status:
                query = query.filter(Project.status == status)
            
            return query.order_by(Project.created_time.desc()).all()
    
    def create(self, data: dict) -> Project:
        """创建项目"""
        with self._get_session() as session:
            project = Project(**data)
            session.add(project)
            session.commit()
            session.refresh(project)
            return project
    
    def update(self, id: str, data: dict) -> Optional[Project]:
        """更新项目"""
        with self._get_session() as session:
            project = session.query(Project).filter(Project.id == id).first()
            if not project:
                return None
            
            for key, value in data.items():
                if value is not None and hasattr(project, key):
                    setattr(project, key, value)
            
            session.commit()
            session.refresh(project)
            return project
    
    def soft_delete(self, id: str) -> bool:
        """软删除项目"""
        with self._get_session() as session:
            project = session.query(Project).filter(Project.id == id).first()
            if not project:
                return False
            
            project.is_deleted = True
            session.commit()
            return True
    
    def count(self, include_deleted: bool = False) -> int:
        """统计项目数量"""
        with self._get_session() as session:
            query = session.query(Project)
            if not include_deleted:
                from sqlalchemy import or_
                query = query.filter(or_(Project.is_deleted.is_(False), Project.is_deleted.is_(None)))
            return query.count()


# 单例实例
_project_repo: Optional[ProjectRepository] = None


def get_project_repository() -> ProjectRepository:
    """获取项目 Repository 实例"""
    global _project_repo
    if _project_repo is None:
        _project_repo = ProjectRepository()
    return _project_repo
