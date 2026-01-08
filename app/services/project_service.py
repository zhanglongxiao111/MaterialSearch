"""
项目服务

封装项目管理业务逻辑。
"""
import logging
from typing import List, Dict, Any, Optional

from app.repositories.project_repo import get_project_repository
from app.repositories.image_repo import get_image_repository

logger = logging.getLogger(__name__)


class ProjectService:
    """
    项目服务类
    
    提供项目管理功能。
    """
    
    def __init__(self):
        self._project_repo = get_project_repository()
    
    def list_projects(
        self,
        status: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取项目列表
        
        Args:
            status: 状态过滤
            include_deleted: 是否包含已删除项目
        
        Returns:
            项目列表
        """
        # 暂时使用旧实现
        from project_manager import get_project_manager
        pm = get_project_manager()
        return pm.list_projects(status=status, include_deleted=include_deleted)
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        获取项目详情
        
        Args:
            project_id: 项目 ID
        
        Returns:
            项目信息
        """
        from project_manager import get_project_manager
        pm = get_project_manager()
        return pm.get_project(project_id)
    
    def create_project(
        self,
        name: str,
        client_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建项目
        
        Args:
            name: 项目名称
            client_name: 客户名称
            description: 项目描述
        
        Returns:
            创建的项目信息
        """
        from project_manager import get_project_manager
        pm = get_project_manager()
        return pm.create_project(
            name=name,
            client_name=client_name,
            description=description
        )
    
    def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        client_name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新项目
        
        Args:
            project_id: 项目 ID
            name: 项目名称
            client_name: 客户名称
            description: 项目描述
            status: 项目状态
        
        Returns:
            更新后的项目信息
        """
        from project_manager import get_project_manager
        pm = get_project_manager()
        return pm.update_project(
            project_id=project_id,
            name=name,
            client_name=client_name,
            description=description,
            status=status
        )
    
    def delete_project(self, project_id: str, hard_delete: bool = False) -> None:
        """
        删除项目
        
        Args:
            project_id: 项目 ID
            hard_delete: 是否硬删除
        """
        from project_manager import get_project_manager
        pm = get_project_manager()
        pm.delete_project(project_id, hard_delete=hard_delete)
    
    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """
        获取项目统计信息
        
        Args:
            project_id: 项目 ID
        
        Returns:
            统计信息
        """
        from project_manager import get_project_manager
        pm = get_project_manager()
        return pm.get_project_stats(project_id)
    
    def update_project_stats(self, project_id: str) -> None:
        """
        更新项目统计信息
        
        Args:
            project_id: 项目 ID
        """
        from project_manager import get_project_manager
        pm = get_project_manager()
        pm.update_project_stats(project_id)
    
    def delete_project_images(
        self,
        project_id: str,
        image_ids: List[int]
    ) -> Dict[str, Any]:
        """
        删除项目图片
        
        Args:
            project_id: 项目 ID
            image_ids: 图片 ID 列表
        
        Returns:
            删除结果
        """
        from project_manager import get_project_manager
        from search import clean_cache
        
        pm = get_project_manager()
        result = pm.delete_project_images(project_id, image_ids)
        pm.update_project_stats(project_id)
        clean_cache()
        return result


# 单例实例
_project_service: Optional[ProjectService] = None


def get_project_service() -> ProjectService:
    """获取项目服务实例"""
    global _project_service
    if _project_service is None:
        _project_service = ProjectService()
    return _project_service
