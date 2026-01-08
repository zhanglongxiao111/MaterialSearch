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
    
    # 旧版 /api/batch_index -> 新版 /api/scan/batch_index
    @app.route('/api/batch_index', methods=['POST'])
    def legacy_batch_index():
        """兼容旧版批量索引接口"""
        from .scan import start_batch_index
        return start_batch_index()
    
    @app.route('/api/batch_index/<task_id>/status', methods=['GET'])
    def legacy_batch_index_status(task_id):
        """兼容旧版批量索引状态接口"""
        from .scan import get_batch_index_status
        return get_batch_index_status(task_id)
    
    @app.route('/api/batch_index/<task_id>/cancel', methods=['POST'])
    def legacy_batch_index_cancel(task_id):
        """兼容旧版取消批量索引接口"""
        from .scan import cancel_batch_index
        return cancel_batch_index(task_id)
    
    # 预览文件 API
    @app.route('/api/preview_files', methods=['POST'])
    def preview_files():
        """预览待索引文件"""
        from flask import jsonify, request as flask_request
        import os
        import urllib.parse
        from pathlib import Path
        from config import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, PDF_EXTENSIONS
        from app.integrations.sqlite_manager import get_db_manager
        from app.models import Image, ProjectImage
        
        data = flask_request.get_json() or {}
        paths = data.get('paths', [])
        target = data.get('target', 'permanent')
        
        if not paths:
            return jsonify([])
        
        result = []
        
        # 根据 target 选择正确的模型和 session
        db_session = None
        ImageModel = Image
        try:
            if target == 'permanent':
                db_session = get_db_manager().get_permanent_session()
                ImageModel = Image
            elif target.startswith('proj_'):
                db_session = get_db_manager().get_project_session(target)
                ImageModel = ProjectImage
            else:
                from models import DatabaseSession
                db_session = DatabaseSession()
                ImageModel = Image
        except Exception as e:
            # 如果获取 session 失败，使用空的 indexed_paths
            db_session = None
        
        # 获取已索引的文件路径
        indexed_paths = set()
        if db_session is not None:
            try:
                with db_session:
                    images = db_session.query(ImageModel.path).all()
                    indexed_paths = {img.path for img in images if img.path}
            except Exception as e:
                # 如果项目数据库不存在或查询失败，忽略错误
                pass
        
        def add_file(file_path):
            """添加单个文件到结果列表"""
            ext = Path(file_path).suffix.lower()
            if ext not in IMAGE_EXTENSIONS and ext not in PDF_EXTENSIONS:
                return
            
            is_indexed = file_path in indexed_paths
            encoded_path = urllib.parse.quote(file_path, safe='')
            thumbnail_url = f"/api/thumbnail?path={encoded_path}&size=256"
            
            result.append({
                'path': file_path,
                'filename': os.path.basename(file_path),
                'is_indexed': is_indexed,
                'size': os.path.getsize(file_path),
                'type': 'pdf' if ext in PDF_EXTENSIONS else 'image',
                'thumbnailUrl': thumbnail_url
            })
        
        for path in paths:
            if os.path.isfile(path):
                # 单个文件
                add_file(path)
            elif os.path.isdir(path):
                # 目录：遍历所有文件
                for root, dirs, files in os.walk(path):
                    for filename in files:
                        file_path = os.path.join(root, filename)
                        add_file(file_path)
        
        return jsonify(result)
    
    # 去重任务状态 API
    @app.route('/api/dedup/jobs/latest', methods=['GET'])
    def get_latest_dedup_job():
        """获取最新去重任务"""
        from flask import jsonify
        # 暂时返回空，因为没有正在运行的任务
        return jsonify(None)
    
    # 旧版 /api/upload -> 新版 /api/assets/upload
    @app.route('/api/upload', methods=['POST'])
    def legacy_upload():
        """兼容旧版上传接口"""
        from .assets import upload_file
        return upload_file()
    
    # 旧版 /api/pdf/pages -> 注册到根路由
    @app.route('/api/pdf/pages', methods=['GET'])
    def legacy_pdf_pages():
        """兼容旧版 PDF 页面接口"""
        from flask import request as flask_request, jsonify
        from app.models import PDFPage
        from app.models.pdf import ProjectPDFPage
        from app.integrations.sqlite_manager import get_db_manager
        import os
        
        doc_id = flask_request.args.get('doc_id')
        target = flask_request.args.get('target', 'permanent')
        
        if not doc_id:
            return jsonify({"error": "缺少 doc_id 参数"}), 400
        
        # 根据 target 选择正确的模型和 session
        if target == 'permanent':
            db_session = get_db_manager().get_permanent_session()
            PageModel = PDFPage
        elif target.startswith('proj_'):
            db_session = get_db_manager().get_project_session(target)
            PageModel = ProjectPDFPage
        else:
            from models import DatabaseSession
            db_session = DatabaseSession()
            PageModel = PDFPage
        
        with db_session:
            page = db_session.query(PageModel).filter(PageModel.id == int(doc_id)).first()
            if not page:
                return jsonify({"error": "页面不存在"}), 404
            
            source_path = page.source_path
            pages = db_session.query(PageModel).filter(
                PageModel.source_path == source_path
            ).order_by(PageModel.page_no).all()
            
            result = []
            for p in pages:
                result.append({
                    "id": p.id,
                    "page_no": p.page_no,
                    "image": f"/api/pdf/page/{p.id}?target={target}",
                    "thumbnail": f"/api/pdf/page/{p.id}?target={target}&size=256"
                })
            
            return jsonify({
                "pages": result,
                "page_count": len(result),
                "pages_truncated": page.pages_truncated if hasattr(page, 'pages_truncated') else False
            })
    
    # =============================================================================
    # 旧版图片/视频 API 兼容路由 (前端依赖)
    # =============================================================================
    from flask import send_file
    from io import BytesIO
    import base64
    
    @app.route('/api/thumbnail', methods=['GET'])
    def legacy_thumbnail():
        """旧版缩略图API - 前端 index.html 使用"""
        from flask import request, abort
        from models import Image, DatabaseSession
        from app.utils.common import resize_image_with_aspect_ratio
        from app.utils.image import extract_rhino_preview
        
        path = request.args.get('path', '')
        size = int(request.args.get('size', 128))
        
        if not path or not os.path.exists(path):
            abort(404)
        
        try:
            # Rhino 3dm 文件特殊处理
            if path.lower().endswith('.3dm'):
                img = extract_rhino_preview(path)
            else:
                img = resize_image_with_aspect_ratio(path, (size, size), convert_rgb=True)
            
            if img:
                img_io = BytesIO()
                img.save(img_io, 'JPEG', quality=60)
                img_io.seek(0)
                return send_file(img_io, mimetype='image/jpeg')
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"生成缩略图失败: {path}, {e}")
        
        abort(404)
    
    @app.route('/api/get_image', methods=['GET'])
    def legacy_get_image():
        """旧版获取图片API"""
        from flask import request, abort
        
        path = request.args.get('path', '')
        if not path:
            # 尝试 base64 解码
            encoded = request.args.get('p', '')
            if encoded:
                try:
                    path = base64.urlsafe_b64decode(encoded).decode()
                except:
                    abort(404)
        
        if not path or not os.path.exists(path):
            abort(404)
        
        return send_file(path)
    
    @app.route('/api/get_video', methods=['GET'])
    def legacy_get_video():
        """旧版获取视频API"""
        from flask import request, abort
        
        path = request.args.get('path', '')
        if not path or not os.path.exists(path):
            abort(404)
        
        return send_file(path)
    
    @app.route('/api/get_image/<int:image_id>', methods=['GET'])
    def legacy_get_image_by_id(image_id):
        """旧版按ID获取图片API - 搜索结果使用"""
        from flask import request, abort
        from models import Image
        from app.integrations.sqlite_manager import get_db_manager
        from app.utils.image import extract_rhino_preview
        
        target = request.args.get('target', 'permanent')
        
        # 获取正确的 session
        if target == 'permanent':
            db_session = get_db_manager().get_permanent_session()
        elif target.startswith('proj_'):
            db_session = get_db_manager().get_project_session(target)
        else:
            from models import DatabaseSession
            db_session = DatabaseSession()
        
        with db_session:
            image = db_session.query(Image).filter(Image.id == image_id).first()
            if not image:
                abort(404)
            
            path = image.path
            if not path or not os.path.exists(path):
                abort(404)
            
            # 3dm 文件：返回提取的预览图
            if path.lower().endswith('.3dm'):
                try:
                    img = extract_rhino_preview(path)
                    if img:
                        img_io = BytesIO()
                        img.save(img_io, 'JPEG', quality=95)
                        img_io.seek(0)
                        return send_file(img_io, mimetype='image/jpeg')
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"提取 3dm 预览失败: {path}, {e}")
            
            return send_file(path)
    
    @app.route('/api/pdf/page/<int:page_id>', methods=['GET'])
    def legacy_get_pdf_page(page_id):
        """获取 PDF 页面缩略图"""
        from flask import request, abort
        from app.models import PDFPage
        from app.models.pdf import ProjectPDFPage
        from app.integrations.sqlite_manager import get_db_manager
        
        target = request.args.get('target', 'permanent')
        size = int(request.args.get('size', 512))
        
        # 根据 target 选择正确的模型和 session
        if target == 'permanent':
            db_session = get_db_manager().get_permanent_session()
            PageModel = PDFPage
        elif target.startswith('proj_'):
            db_session = get_db_manager().get_project_session(target)
            PageModel = ProjectPDFPage
        else:
            from models import DatabaseSession
            db_session = DatabaseSession()
            PageModel = PDFPage
        
        with db_session:
            page = db_session.query(PageModel).filter(PageModel.id == page_id).first()
            if not page:
                abort(404)
            
            # 优先使用 thumbnail_path
            if page.thumbnail_path and os.path.exists(page.thumbnail_path):
                return send_file(page.thumbnail_path)
            
            # 否则返回 404
            abort(404)
    
    # =============================================================================
    # 前端页面路由
    # =============================================================================
    from flask import send_from_directory, redirect
    import os
    
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'static')
    
    @app.route('/')
    def index():
        """主页 - 重定向到 workspace"""
        return redirect('/workspace')
    
    @app.route('/workspace')
    def workspace():
        """工作区界面"""
        return send_from_directory(static_dir, 'index_workspace.html')
    
    @app.route('/classic')
    def classic():
        """经典界面"""
        return send_from_directory(static_dir, 'index_classic.html')
    
    @app.route('/index')
    def index_page():
        """默认界面"""
        return send_from_directory(static_dir, 'index.html')
    
    @app.route('/login')
    def login_page():
        """登录页面"""
        return send_from_directory(static_dir, 'login.html')
