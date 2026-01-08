"""
Supabase 客户端

封装与 Supabase 的所有交互。
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Supabase 客户端单例
_supabase_client = None


def get_supabase_config() -> dict:
    """获取 Supabase 配置"""
    return {
        'url': os.getenv('SUPABASE_URL', ''),
        'anon_key': os.getenv('SUPABASE_ANON_KEY', ''),
        'service_key': os.getenv('SUPABASE_SERVICE_KEY', ''),
    }


def is_supabase_configured() -> bool:
    """检查 Supabase 是否已配置"""
    config = get_supabase_config()
    return bool(config['url'] and config['anon_key'])


def get_supabase():
    """
    获取 Supabase 客户端实例
    
    Returns:
        Supabase 客户端，如果未配置则返回 None
    
    Raises:
        ImportError: 如果 supabase 包未安装
        ValueError: 如果配置不完整
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    config = get_supabase_config()
    
    if not config['url'] or not config['anon_key']:
        raise ValueError(
            "Supabase 配置不完整。请设置环境变量:\n"
            "  - SUPABASE_URL\n"
            "  - SUPABASE_ANON_KEY"
        )
    
    try:
        from supabase import create_client, Client
    except ImportError:
        raise ImportError(
            "supabase 包未安装。请运行: pip install supabase>=2.0.0"
        )
    
    logger.info(f"正在连接 Supabase: {config['url']}")
    _supabase_client = create_client(config['url'], config['anon_key'])
    logger.info("Supabase 客户端已创建")
    
    return _supabase_client


def get_supabase_admin():
    """
    获取使用 service_key 的 Supabase 管理客户端
    
    用于绕过 RLS 进行管理操作。
    
    Returns:
        Supabase 管理客户端
    """
    config = get_supabase_config()
    
    if not config['service_key']:
        raise ValueError(
            "Supabase 服务密钥未配置。请设置环境变量:\n"
            "  - SUPABASE_SERVICE_KEY"
        )
    
    from supabase import create_client
    return create_client(config['url'], config['service_key'])


class SupabaseStorage:
    """
    Supabase Storage 封装
    
    用于文件存储（可选功能，Phase 3+ 实现）
    """
    
    def __init__(self, bucket: str = 'assets'):
        self.bucket = bucket
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase()
        return self._client
    
    def upload(self, path: str, file_data: bytes, content_type: str = 'image/jpeg') -> str:
        """
        上传文件
        
        Args:
            path: 存储路径
            file_data: 文件数据
            content_type: MIME 类型
        
        Returns:
            公开访问 URL
        """
        response = self.client.storage.from_(self.bucket).upload(
            path, file_data, {'content-type': content_type}
        )
        return self.get_public_url(path)
    
    def download(self, path: str) -> bytes:
        """下载文件"""
        response = self.client.storage.from_(self.bucket).download(path)
        return response
    
    def delete(self, path: str) -> bool:
        """删除文件"""
        self.client.storage.from_(self.bucket).remove([path])
        return True
    
    def get_public_url(self, path: str) -> str:
        """获取公开访问 URL"""
        return self.client.storage.from_(self.bucket).get_public_url(path)


class SupabaseAuth:
    """
    Supabase Auth 封装
    
    用于用户认证
    """
    
    def __init__(self):
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase()
        return self._client
    
    def sign_up(self, email: str, password: str) -> dict:
        """注册新用户"""
        response = self.client.auth.sign_up({
            'email': email,
            'password': password
        })
        return response
    
    def sign_in(self, email: str, password: str) -> dict:
        """用户登录"""
        response = self.client.auth.sign_in_with_password({
            'email': email,
            'password': password
        })
        return response
    
    def sign_out(self) -> None:
        """用户登出"""
        self.client.auth.sign_out()
    
    def get_user(self, jwt: str) -> Optional[dict]:
        """通过 JWT 获取用户信息"""
        response = self.client.auth.get_user(jwt)
        return response.user if response else None
    
    def refresh_session(self, refresh_token: str) -> dict:
        """刷新会话"""
        response = self.client.auth.refresh_session(refresh_token)
        return response


# 便捷函数
def supabase_query(table: str):
    """
    快捷查询函数
    
    Usage:
        result = supabase_query('images').select('*').limit(10).execute()
    """
    return get_supabase().table(table)


def supabase_rpc(function_name: str, params: dict = None):
    """
    调用 PostgreSQL 函数
    
    Usage:
        result = supabase_rpc('search_images_by_vector', {'query_vector': [...], 'threshold': 0.3})
    """
    return get_supabase().rpc(function_name, params or {})
