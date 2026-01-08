"""
应用配置模块

支持多环境配置：development, production, testing
通过环境变量覆盖默认值
"""
import os
from typing import List


def _get_bool(key: str, default: bool = False) -> bool:
    """从环境变量获取布尔值"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def _get_list(key: str, default: str = '') -> List[str]:
    """从环境变量获取列表（逗号分隔）"""
    value = os.getenv(key, default)
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


class BaseConfig:
    """基础配置"""
    
    # === Flask 配置 ===
    SECRET_KEY = os.getenv('SECRET_KEY', 'materialsearch-secret-key')
    
    # === 服务器配置 ===
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', '5000'))
    
    # === 数据库配置 ===
    USE_SUPABASE = _get_bool('USE_SUPABASE', False)
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')
    SQLITE_DATABASE_PATH = os.getenv('SQLITE_DATABASE_PATH', './instance/permanent.db')
    
    # === 认证配置 ===
    ENABLE_LOGIN = _get_bool('ENABLE_LOGIN', False)
    # 旧版单用户模式
    USERNAME = os.getenv('USERNAME', 'admin')
    PASSWORD = os.getenv('PASSWORD', 'admin')
    # JWT 配置
    JWT_SECRET = os.getenv('JWT_SECRET', 'jwt-secret-key')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
    
    # === 素材路径配置 ===
    ASSETS_PATH = _get_list('ASSETS_PATH')
    SKIP_PATH = _get_list('SKIP_PATH')
    TEMP_PATH = os.getenv('TEMP_PATH', './tmp')
    
    # === AI 模型配置 ===
    MODEL_NAME = os.getenv('MODEL_NAME', 'OFA-Sys/chinese-clip-vit-base-patch16')
    USE_GPU = _get_bool('USE_GPU', True)
    SCAN_PROCESS_BATCH_SIZE = int(os.getenv('SCAN_PROCESS_BATCH_SIZE', '6'))
    
    # === 搜索配置 ===
    POSITIVE_THRESHOLD = float(os.getenv('POSITIVE_THRESHOLD', '0.27'))
    NEGATIVE_THRESHOLD = float(os.getenv('NEGATIVE_THRESHOLD', '0.27'))
    IMAGE_THRESHOLD = float(os.getenv('IMAGE_THRESHOLD', '0.9'))
    
    # === 扫描配置 ===
    AUTO_SCAN = _get_bool('AUTO_SCAN', True)
    SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', '3600'))
    
    # === 缓存配置 ===
    CACHE_SIZE = int(os.getenv('CACHE_SIZE', '1000'))
    
    # === 日志配置 ===
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    DEBUG = True
    FLASK_DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(BaseConfig):
    """生产环境配置"""
    DEBUG = False
    FLASK_DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    # 生产环境强制要求
    USE_SUPABASE = _get_bool('USE_SUPABASE', True)
    ENABLE_LOGIN = True


class TestingConfig(BaseConfig):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    
    # 测试使用内存数据库
    USE_SUPABASE = False
    SQLITE_DATABASE_PATH = ':memory:'
    
    # 禁用自动扫描
    AUTO_SCAN = False


# 配置映射
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
