"""
外部服务集成层

封装与外部服务的交互：Supabase、CLIP 模型、存储后端等。
"""
from .sqlite_compat import (
    get_sqlite_manager,
    use_supabase,
    get_db_session,
    SQLiteManager,
)

# Supabase 客户端（仅在需要时导入，避免强制依赖）
# from .supabase_client import get_supabase, supabase_query, supabase_rpc

__all__ = [
    'get_sqlite_manager',
    'use_supabase',
    'get_db_session',
    'SQLiteManager',
]
