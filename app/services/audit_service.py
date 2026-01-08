"""
审计日志服务

记录用户操作，支持合规审计和问题追溯。
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from flask import request, g

logger = logging.getLogger(__name__)


class AuditService:
    """
    审计日志服务
    
    记录关键操作：登录、数据修改、管理操作等。
    """
    
    def __init__(self):
        from app.integrations.sqlite_compat import use_supabase
        self._use_supabase = use_supabase()
    
    def log(
        self,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """
        记录审计日志
        
        Args:
            action: 操作类型 (LOGIN, CREATE, UPDATE, DELETE, etc.)
            resource_type: 资源类型 (image, video, project, etc.)
            resource_id: 资源 ID
            details: 详细信息
            user_id: 用户 ID（如未提供则从 g.user 获取）
        """
        # 获取用户信息
        if user_id is None and hasattr(g, 'user') and g.user:
            user_id = g.user.get('id')
        
        # 获取请求信息
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')[:255]
        
        log_entry = {
            'action': action,
            'resource_type': resource_type,
            'resource_id': str(resource_id) if resource_id else None,
            'details': details,
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'created_at': datetime.utcnow().isoformat(),
        }
        
        if self._use_supabase:
            self._save_to_supabase(log_entry)
        else:
            self._save_to_local(log_entry)
    
    def _save_to_supabase(self, entry: dict) -> None:
        """保存到 Supabase"""
        try:
            from app.integrations.supabase_client import get_supabase
            get_supabase().table('audit_logs').insert(entry).execute()
        except Exception as e:
            logger.error(f"保存审计日志到 Supabase 失败: {e}")
    
    def _save_to_local(self, entry: dict) -> None:
        """保存到本地日志"""
        logger.info(f"[AUDIT] {entry['action']} - {entry['resource_type']}/{entry['resource_id']} by {entry['user_id']}")
    
    def query(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        查询审计日志
        
        Args:
            user_id: 按用户过滤
            action: 按操作类型过滤
            resource_type: 按资源类型过滤
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
        
        Returns:
            审计日志列表
        """
        if not self._use_supabase:
            logger.warning("本地模式不支持审计日志查询")
            return []
        
        try:
            from app.integrations.supabase_client import get_supabase
            
            query = get_supabase().table('audit_logs').select('*')
            
            if user_id:
                query = query.eq('user_id', user_id)
            if action:
                query = query.eq('action', action)
            if resource_type:
                query = query.eq('resource_type', resource_type)
            if start_time:
                query = query.gte('created_at', start_time.isoformat())
            if end_time:
                query = query.lte('created_at', end_time.isoformat())
            
            response = query.order('created_at', desc=True).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"查询审计日志失败: {e}")
            return []
    
    # =========================================================================
    # 便捷方法
    # =========================================================================
    
    def log_login(self, user_id: str, email: str, success: bool = True):
        """记录登录"""
        self.log(
            action='LOGIN_SUCCESS' if success else 'LOGIN_FAILED',
            resource_type='user',
            resource_id=user_id,
            details={'email': email}
        )
    
    def log_logout(self, user_id: str):
        """记录登出"""
        self.log(action='LOGOUT', resource_type='user', resource_id=user_id)
    
    def log_create(self, resource_type: str, resource_id: str, details: dict = None):
        """记录创建操作"""
        self.log(action='CREATE', resource_type=resource_type, resource_id=resource_id, details=details)
    
    def log_update(self, resource_type: str, resource_id: str, details: dict = None):
        """记录更新操作"""
        self.log(action='UPDATE', resource_type=resource_type, resource_id=resource_id, details=details)
    
    def log_delete(self, resource_type: str, resource_id: str, details: dict = None):
        """记录删除操作"""
        self.log(action='DELETE', resource_type=resource_type, resource_id=resource_id, details=details)
    
    def log_archive(self, project_id: str, image_count: int):
        """记录归档操作"""
        self.log(
            action='ARCHIVE',
            resource_type='project',
            resource_id=project_id,
            details={'image_count': image_count}
        )


# 单例实例
_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """获取审计服务实例"""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
