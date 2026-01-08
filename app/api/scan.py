"""
扫描 API Blueprint

提供素材扫描功能，支持永久库和项目库。
"""
import logging
import threading

from flask import Blueprint, request, jsonify

from scan import scanner
from project_manager import get_project_manager

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
