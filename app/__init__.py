"""
MaterialSearch 应用包

采用 Flask App Factory 模式，支持多环境配置。
"""
import os
import logging
from flask import Flask

from .settings import config_by_name

logger = logging.getLogger(__name__)


def create_app(config_name: str = None) -> Flask:
    """
    Flask 应用工厂函数
    
    Args:
        config_name: 配置名称 ('development', 'production', 'testing')
                     如果未指定，从环境变量 FLASK_ENV 读取
    
    Returns:
        Flask: 配置完成的 Flask 应用实例
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__, 
                static_folder='../static',
                template_folder='../templates')
    
    # 加载配置
    app.config.from_object(config_by_name[config_name])
    
    # 设置 secret key
    app.secret_key = app.config.get('SECRET_KEY', 'materialsearch-default-secret')
    
    # 注册 Blueprint
    _register_blueprints(app)
    
    # 注册错误处理
    _register_error_handlers(app)
    
    logger.info(f"MaterialSearch 应用已创建 (环境: {config_name})")
    
    return app


def _register_blueprints(app: Flask) -> None:
    """注册所有 API Blueprint"""
    from .api import register_blueprints
    register_blueprints(app)


def _register_error_handlers(app: Flask) -> None:
    """注册全局错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return {
            'error': {
                'code': 'BAD_REQUEST',
                'message': str(error.description) if hasattr(error, 'description') else '请求参数错误'
            }
        }, 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {
            'error': {
                'code': 'UNAUTHORIZED',
                'message': '需要认证'
            }
        }, 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return {
            'error': {
                'code': 'FORBIDDEN',
                'message': '无权限访问'
            }
        }, 403
    
    @app.errorhandler(404)
    def not_found(error):
        return {
            'error': {
                'code': 'NOT_FOUND',
                'message': '资源不存在'
            }
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.exception("服务器内部错误")
        return {
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': '服务器内部错误'
            }
        }, 500
