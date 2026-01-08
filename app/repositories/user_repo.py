"""
用户 Repository

封装用户相关的数据访问操作。
"""
import logging
from typing import Optional, List

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """
    用户数据访问类
    
    Supabase 模式：通过 Supabase Auth + user_profiles 表
    SQLite 模式：使用本地配置的用户（单用户）
    """
    
    @property
    def table_name(self) -> str:
        return 'user_profiles'
    
    def find_by_id(self, user_id: str) -> Optional[dict]:
        """根据 ID 查找用户"""
        if self.use_supabase:
            return self._supabase_find_by_id(user_id)
        else:
            # SQLite 模式：返回默认管理员
            import os
            return {
                'id': 'local_admin',
                'email': os.getenv('USERNAME', 'admin'),
                'role': 'admin',
                'display_name': 'Administrator',
            }
    
    def find_by_email(self, email: str) -> Optional[dict]:
        """根据邮箱查找用户"""
        if self.use_supabase:
            return self._supabase_find_by_email(email)
        else:
            import os
            if email == os.getenv('USERNAME', 'admin'):
                return self.find_by_id('local_admin')
            return None
    
    def list_users(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """获取用户列表"""
        if self.use_supabase:
            return self._supabase_list_users(limit, offset)
        else:
            # SQLite 模式：只返回默认管理员
            return [self.find_by_id('local_admin')]
    
    def update_user(self, user_id: str, data: dict) -> Optional[dict]:
        """更新用户信息"""
        if self.use_supabase:
            return self._supabase_update_user(user_id, data)
        else:
            logger.warning("SQLite 模式不支持更新用户")
            return None
    
    # =========================================================================
    # Supabase 实现
    # =========================================================================
    
    def _supabase_find_by_id(self, user_id: str) -> Optional[dict]:
        from app.integrations.supabase_client import get_supabase
        
        response = get_supabase().table('user_profiles').select('*').eq('id', user_id).single().execute()
        return response.data if response.data else None
    
    def _supabase_find_by_email(self, email: str) -> Optional[dict]:
        from app.integrations.supabase_client import get_supabase
        
        response = get_supabase().table('user_profiles').select('*').eq('email', email).single().execute()
        return response.data if response.data else None
    
    def _supabase_list_users(self, limit: int, offset: int) -> List[dict]:
        from app.integrations.supabase_client import get_supabase
        
        response = get_supabase().table('user_profiles').select('*').range(offset, offset + limit - 1).execute()
        return response.data if response.data else []
    
    def _supabase_update_user(self, user_id: str, data: dict) -> Optional[dict]:
        from app.integrations.supabase_client import get_supabase
        
        response = get_supabase().table('user_profiles').update(data).eq('id', user_id).execute()
        return response.data[0] if response.data else None


# 单例实例
_user_repo: Optional[UserRepository] = None


def get_user_repository() -> UserRepository:
    """获取用户 Repository 实例"""
    global _user_repo
    if _user_repo is None:
        _user_repo = UserRepository()
    return _user_repo
