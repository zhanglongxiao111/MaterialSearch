"""
扫描 API Blueprint

提供素材扫描功能，支持永久库和项目库。
"""
import logging
import threading

from flask import Blueprint, request, jsonify

from app.services.scan_service import scanner
from app.services.project_service import get_project_manager

logger = logging.getLogger(__name__)

scan_bp = Blueprint('scan', __name__)


@scan_bp.route('/start', methods=['GET', 'POST'])
def start_scan():
    """
    启动扫描任务
    
    Query Parameters (GET) / Body (POST):
        target (str): 目标库，'permanent' 或 'proj_xxx'，默认 'permanent'
        path (str/list): 自定义扫描路径
    """
    if request.method == 'POST':
        data = request.get_json() or {}
        target = data.get('target', 'permanent')
        scan_paths = data.get('paths', [])
    else:
        target = request.args.get('target', 'permanent')
        scan_paths = request.args.getlist('path')
    
    logger.info(f"接收到扫描请求: target={target}")
    
    # 项目库必须指定路径
    if target != 'permanent':
        if not scan_paths:
            return jsonify({
                "success": False,
                "error": "项目库扫描必须指定路径参数（path）"
            }), 400
        logger.info(f"使用自定义扫描路径: {scan_paths}")
    
    # 验证项目是否存在
    if target.startswith('proj_'):
        try:
            pm = get_project_manager()
            project = pm.get_project(target)
            if not project:
                return jsonify({"success": False, "error": f"项目不存在: {target}"}), 404
        except Exception as e:
            logger.error(f"验证项目失败: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    # 检查是否正在扫描
    if scanner.is_scanning:
        return jsonify({"success": False, "error": "扫描进行中，请稍后再试"}), 409
    
    # 启动扫描
    try:
        if target != 'permanent':
            scan_thread = threading.Thread(
                target=scanner.scan,
                args=(False, target, scan_paths)
            )
        else:
            scan_thread = threading.Thread(
                target=scanner.scan,
                args=(False, target)
            )
        scan_thread.start()
        
        message = f"开始扫描到 {target}"
        if scan_paths:
            paths_preview = ', '.join(scan_paths[:2])
            if len(scan_paths) > 2:
                paths_preview += '...'
            message += f" (路径: {paths_preview})"
        
        return jsonify({"success": True, "message": message})
    except Exception as e:
        logger.error(f"启动扫描失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@scan_bp.route('/status', methods=['GET'])
def get_status():
    """获取扫描状态"""
    return jsonify(scanner.get_status())


@scan_bp.route('/stop', methods=['POST'])
def stop_scan():
    """停止扫描任务"""
    try:
        scanner.stop_scan()
        return jsonify({"success": True, "message": "扫描已停止"})
    except Exception as e:
        logger.error(f"停止扫描失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# 批量索引 API
# =============================================================================
import uuid
import os

# 存储批量索引任务状态
_batch_index_tasks = {}


@scan_bp.route('/batch_index', methods=['POST'])
def start_batch_index():
    """
    启动批量索引任务
    
    Request Body:
    {
        "files": [{"path": "/path/to/file", "filename": "xxx.jpg"}, ...],
        "target": "permanent" or "proj_xxx",
        "duplicate_strategy": "ask" | "skip" | "overwrite"
    }
    """
    data = request.get_json() or {}
    files = data.get('files', [])
    target = data.get('target', 'permanent')
    duplicate_strategy = data.get('duplicate_strategy', 'ask')
    
    if not files:
        return jsonify({"error": "未提供文件列表"}), 400
    
    # 提取文件路径
    file_paths = []
    for f in files:
        path = f.get('path') if isinstance(f, dict) else f
        if path and os.path.exists(path):
            file_paths.append(path)
    
    if not file_paths:
        return jsonify({"error": "没有有效的文件路径"}), 400
    
    # 验证项目是否存在
    if target.startswith('proj_'):
        try:
            pm = get_project_manager()
            project = pm.get_project(target)
            if not project:
                return jsonify({"error": f"项目不存在: {target}"}), 404
        except Exception as e:
            logger.error(f"验证项目失败: {e}")
            return jsonify({"error": str(e)}), 500
    
    # 创建任务
    task_id = str(uuid.uuid4())
    task_info = {
        "task_id": task_id,
        "status": "running",
        "total": len(file_paths),
        "processed": 0,
        "success": 0,
        "failed": [],
        "duplicates": [],
        "truncated": [],
        "current_file": "",
        "progress": 0,
        "target": target,
        "pending_duplicate": None,
    }
    _batch_index_tasks[task_id] = task_info
    
    # 启动异步处理
    def process_batch():
        try:
            for i, path in enumerate(file_paths):
                if task_info["status"] == "cancelled":
                    break
                
                task_info["current_file"] = os.path.basename(path)
                task_info["processed"] = i
                task_info["progress"] = i / len(file_paths)
                
                try:
                    # 使用扫描服务处理单个文件
                    scanner.scan_single_file(path, target)
                    task_info["success"] += 1
                except Exception as e:
                    logger.error(f"索引文件失败: {path}, {e}")
                    task_info["failed"].append({
                        "path": path,
                        "error": str(e)
                    })
            
            task_info["processed"] = len(file_paths)
            task_info["progress"] = 1.0
            task_info["status"] = "completed"
            task_info["current_file"] = ""
        except Exception as e:
            logger.error(f"批量索引任务异常: {e}")
            task_info["status"] = "failed"
            task_info["error"] = str(e)
    
    index_thread = threading.Thread(target=process_batch)
    index_thread.start()
    
    return jsonify({"task_id": task_id, "success": True})


@scan_bp.route('/batch_index/<task_id>/status', methods=['GET'])
def get_batch_index_status(task_id):
    """获取批量索引任务状态"""
    task_info = _batch_index_tasks.get(task_id)
    if not task_info:
        return jsonify({"error": "任务不存在"}), 404
    return jsonify(task_info)


@scan_bp.route('/batch_index/<task_id>/cancel', methods=['POST'])
def cancel_batch_index(task_id):
    """取消批量索引任务"""
    task_info = _batch_index_tasks.get(task_id)
    if not task_info:
        return jsonify({"error": "任务不存在"}), 404
    
    task_info["status"] = "cancelled"
    return jsonify({"success": True, "message": "任务已取消"})
