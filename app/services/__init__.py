"""
Service 层

封装业务逻辑，协调 Repository 完成复杂操作。
"""
from .search_service import SearchService, get_search_service
from .project_service import ProjectService, get_project_service
from .asset_service import AssetService, get_asset_service
from .scan_service import ScanService, get_scan_service
from .audit_service import AuditService, get_audit_service

__all__ = [
    # 搜索
    'SearchService',
    'get_search_service',
    # 项目
    'ProjectService',
    'get_project_service',
    # 素材
    'AssetService',
    'get_asset_service',
    # 扫描
    'ScanService',
    'get_scan_service',
    # 审计
    'AuditService',
    'get_audit_service',
]
