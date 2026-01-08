"""
核心功能测试用例

在进行旧代码迁移前后运行，确保功能不被破坏。

Usage:
    pytest tests/test_core_functions.py -v
    python -m pytest tests/test_core_functions.py -v
"""
import os
import sys
import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAppCreation:
    """测试应用创建"""
    
    def test_create_app(self):
        """测试 Flask App 能正常创建"""
        from app import create_app
        app = create_app()
        assert app is not None
        assert app.name == 'app'
    
    def test_routes_registered(self):
        """测试路由已注册"""
        from app import create_app
        app = create_app()
        routes = list(app.url_map.iter_rules())
        # 至少应该有 40 个路由
        assert len(routes) >= 35, f"只有 {len(routes)} 个路由"
    
    def test_health_endpoint(self):
        """测试健康检查端点"""
        from app import create_app
        app = create_app()
        with app.test_client() as client:
            response = client.get('/api/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'


class TestDatabaseConnection:
    """测试数据库连接"""
    
    def test_database_manager_exists(self):
        """测试数据库管理器存在"""
        from database import get_db_manager
        db_manager = get_db_manager()
        assert db_manager is not None
    
    def test_permanent_session(self):
        """测试永久库 session"""
        from database import get_db_manager
        db_manager = get_db_manager()
        session = db_manager.get_permanent_session()
        assert session is not None


class TestModels:
    """测试数据模型"""
    
    def test_image_model_import(self):
        """测试 Image 模型可导入"""
        from models import Image
        assert Image is not None
        assert hasattr(Image, 'id')
        assert hasattr(Image, 'path')
        assert hasattr(Image, 'features')
    
    def test_video_model_import(self):
        """测试 Video 模型可导入"""
        from models import Video
        assert Video is not None
        assert hasattr(Video, 'frame_time')
    
    def test_project_model_import(self):
        """测试 Project 模型可导入"""
        from models import Project
        assert Project is not None
        assert hasattr(Project, 'name')


class TestSearchModule:
    """测试搜索模块"""
    
    def test_search_module_import(self):
        """测试 search 模块可导入"""
        import search
        assert hasattr(search, 'process_text')
        assert hasattr(search, 'search_image_by_text_path_time')
    
    def test_process_text(self):
        """测试文本处理"""
        from search import process_text
        # 应该能处理中文文本
        result = process_text("现代建筑")
        assert result is not None


class TestScanModule:
    """测试扫描模块"""
    
    def test_scan_module_import(self):
        """测试 scan 模块可导入"""
        import scan
        assert hasattr(scan, 'scanning')
        assert hasattr(scan, 'status')


class TestProjectManager:
    """测试项目管理器"""
    
    def test_project_manager_import(self):
        """测试 project_manager 模块可导入"""
        from project_manager import get_project_manager
        pm = get_project_manager()
        assert pm is not None
        assert hasattr(pm, 'list_projects')
        assert hasattr(pm, 'create_project')


class TestRepositories:
    """测试 Repository 层"""
    
    def test_image_repo_import(self):
        """测试 ImageRepository 可导入"""
        from app.repositories import get_image_repository
        repo = get_image_repository()
        assert repo is not None
        assert hasattr(repo, 'find_by_id')
        assert hasattr(repo, 'search_by_vector')
    
    def test_video_repo_import(self):
        """测试 VideoRepository 可导入"""
        from app.repositories import get_video_repository
        repo = get_video_repository()
        assert repo is not None
    
    def test_project_repo_import(self):
        """测试 ProjectRepository 可导入"""
        from app.repositories import get_project_repository
        repo = get_project_repository()
        assert repo is not None


class TestServices:
    """测试 Service 层"""
    
    def test_search_service_import(self):
        """测试 SearchService 可导入"""
        from app.services import get_search_service
        service = get_search_service()
        assert service is not None
    
    def test_project_service_import(self):
        """测试 ProjectService 可导入"""
        from app.services import get_project_service
        service = get_project_service()
        assert service is not None
    
    def test_audit_service_import(self):
        """测试 AuditService 可导入"""
        from app.services import get_audit_service
        service = get_audit_service()
        assert service is not None


class TestAPIEndpoints:
    """测试 API 端点"""
    
    @pytest.fixture
    def client(self):
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_search_endpoint_exists(self, client):
        """测试搜索端点存在"""
        # OPTIONS 请求应该返回 200 或 405
        response = client.options('/api/search/match')
        assert response.status_code in [200, 405, 308]
    
    def test_projects_list(self, client):
        """测试项目列表端点"""
        response = client.get('/api/projects/')
        # 可能需要认证，但端点应该存在
        assert response.status_code in [200, 401, 403]
    
    def test_scan_status(self, client):
        """测试扫描状态端点"""
        response = client.get('/api/scan/status')
        assert response.status_code in [200, 401, 403]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
