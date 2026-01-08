"""
API Blueprint 模块

包含所有 REST API 端点，按功能域拆分为独立 Blueprint。
每个 Blueprint 负责单一功能域，保持文件 ≤200 行。
"""
from flask import Flask

from .search import search_bp
from .projects import projects_bp
from .assets import assets_bp
from .archive import archive_bp
from .dedup import dedup_bp
from .scan import scan_bp
from .auth import auth_bp
from .admin import admin_bp


def register_blueprints(app: Flask) -> None:
    """
    注册所有 API Blueprint
    
    Blueprint 路由前缀：
    - /api/search   - 搜索功能
    - /api/projects - 项目管理
    - /api/assets   - 素材处理
    - /api/archive  - 归档功能
    - /api/dedup    - 去重功能
    - /api/scan     - 扫描功能
    - /api/admin    - 管理功能
    
    - /api/auth     - 认证相关
    """
    app.register_blueprint(search_bp, url_prefix='/api/search')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(assets_bp, url_prefix='/api/assets')
    app.register_blueprint(archive_bp, url_prefix='/api/archive')
    app.register_blueprint(dedup_bp, url_prefix='/api/dedup')
    app.register_blueprint(scan_bp, url_prefix='/api/scan')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    
    # 健康检查端点（不需要认证）
    @app.route('/api/health')
    def health_check():
        return {'status': 'ok', 'message': 'MaterialSearch API is running'}
    
    # 兼容旧版 API 路径
    # 旧版 /api/match -> 新版 /api/search/match
    @app.route('/api/match', methods=['POST'])
    def legacy_match():
        """兼容旧版搜索接口"""
        from .search import match
        return match()
    
    # 旧版 /api/projects -> 直接映射到新版
    # 由于路由前缀已设置，无需额外兼容
    
    # 旧版 /api/scan -> 新版 /api/scan/start
    @app.route('/api/scan', methods=['GET'])
    def legacy_scan():
        """兼容旧版扫描接口"""
        from .scan import start_scan
        return start_scan()
    
    # 旧版 /api/status -> 新版 /api/scan/status
    @app.route('/api/status', methods=['GET'])
    def legacy_status():
        """兼容旧版状态接口"""
        from .scan import get_status
        return get_status()
