"""
SQLite 兼容层

当 USE_SUPABASE=false 时，提供与 Supabase 接口兼容的 SQLite 实现。
用于开发环境和单机部署。
"""
import os
import logging
from typing import Optional, List, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)


class SQLiteManager:
    """
    SQLite 数据库管理器
    
    管理多个 SQLite 数据库连接：
    - permanent.db: 永久库
    - projects_metadata.db: 项目元信息
    - proj_*.db: 各项目数据库
    """
    
    def __init__(self):
        self._engines = {}
        self._sessions = {}
        
        # 默认路径
        self.permanent_db_path = os.getenv('PERMANENT_DATABASE_PATH', './instance/permanent.db')
        self.metadata_db_path = os.getenv('METADATA_DATABASE_PATH', './instance/projects_metadata.db')
        self.project_db_dir = os.getenv('PROJECT_DATABASE_DIR', './instance/projects')
        
        # 确保目录存在
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """确保数据库目录存在"""
        for path in [self.permanent_db_path, self.metadata_db_path]:
            dir_path = os.path.dirname(path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)
        
        if not os.path.exists(self.project_db_dir):
            os.makedirs(self.project_db_dir)
    
    def _get_engine(self, db_path: str):
        """获取或创建数据库引擎"""
        if db_path not in self._engines:
            url = f'sqlite:///{db_path}'
            self._engines[db_path] = create_engine(
                url,
                connect_args={"check_same_thread": False}
            )
        return self._engines[db_path]
    
    def get_permanent_session(self) -> Session:
        """获取永久库 Session"""
        engine = self._get_engine(self.permanent_db_path)
        SessionClass = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionClass()
    
    def get_metadata_session(self) -> Session:
        """获取项目元信息库 Session"""
        engine = self._get_engine(self.metadata_db_path)
        SessionClass = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionClass()
    
    def get_project_session(self, project_id: str) -> Session:
        """获取项目数据库 Session"""
        db_path = os.path.join(self.project_db_dir, f'{project_id}.db')
        engine = self._get_engine(db_path)
        SessionClass = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionClass()
    
    def create_project_database(self, project_id: str) -> str:
        """
        创建项目数据库
        
        Args:
            project_id: 项目 ID
        
        Returns:
            数据库文件路径
        """
        from app.models import BaseModelProject
        
        db_path = os.path.join(self.project_db_dir, f'{project_id}.db')
        engine = self._get_engine(db_path)
        
        # 创建表
        BaseModelProject.metadata.create_all(bind=engine)
        
        logger.info(f"已创建项目数据库: {db_path}")
        return db_path
    
    def delete_project_database(self, project_id: str) -> bool:
        """
        删除项目数据库
        
        Args:
            project_id: 项目 ID
        
        Returns:
            是否成功删除
        """
        db_path = os.path.join(self.project_db_dir, f'{project_id}.db')
        
        # 关闭连接
        if db_path in self._engines:
            self._engines[db_path].dispose()
            del self._engines[db_path]
        
        # 删除文件
        if os.path.exists(db_path):
            os.remove(db_path)
            logger.info(f"已删除项目数据库: {db_path}")
            return True
        
        return False
    
    def init_databases(self):
        """初始化所有数据库表"""
        from app.models import BaseModel, BaseModelProject
        from app.models import Project, DedupJob
        
        # 初始化永久库
        engine = self._get_engine(self.permanent_db_path)
        BaseModel.metadata.create_all(bind=engine)
        
        # 初始化元信息库
        engine = self._get_engine(self.metadata_db_path)
        BaseModel.metadata.create_all(bind=engine)
        
        logger.info("数据库初始化完成")


# 单例实例
_sqlite_manager: Optional[SQLiteManager] = None


def get_sqlite_manager() -> SQLiteManager:
    """获取 SQLite 管理器实例"""
    global _sqlite_manager
    if _sqlite_manager is None:
        _sqlite_manager = SQLiteManager()
    return _sqlite_manager


def use_supabase() -> bool:
    """检查是否使用 Supabase"""
    return os.getenv('USE_SUPABASE', 'false').lower() == 'true'


def get_db_session(target: str = 'permanent') -> Session:
    """
    获取数据库 Session（自动选择后端）
    
    Args:
        target: 目标库类型
            - 'permanent': 永久库
            - 'metadata': 项目元信息库
            - 'proj_xxx': 项目数据库
    
    Returns:
        数据库 Session
    """
    if use_supabase():
        # Supabase 模式：返回 Supabase 客户端的查询接口
        # 这里需要适配，因为 Supabase 不使用 SQLAlchemy Session
        raise NotImplementedError("Supabase Session 适配待 Phase 2 完成")
    else:
        manager = get_sqlite_manager()
        if target == 'permanent':
            return manager.get_permanent_session()
        elif target == 'metadata':
            return manager.get_metadata_session()
        elif target.startswith('proj_'):
            return manager.get_project_session(target)
        else:
            raise ValueError(f"未知的目标库: {target}")
