"""
管理员 API Blueprint

提供用户管理、审计日志等管理功能。
仅限管理员访问。
"""
import logging

from flask import Blueprint, request, jsonify

from .auth import login_required, require_role

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


# =============================================================================
# 用户管理 API (需要 admin 角色)
# =============================================================================

@admin_bp.route('/users', methods=['GET'])
@login_required
@require_role('admin')
def list_users():
    """获取用户列表"""
    from app.repositories.user_repo import get_user_repository
    
    repo = get_user_repository()
    users = repo.list_users()
    
    return jsonify({
        "success": True,
        "data": users
    })


@admin_bp.route('/users', methods=['POST'])
@login_required
@require_role('admin')
def create_user():
    """创建用户"""
    # 转发到 auth.register_user
    from .auth import register_user
    return register_user()


@admin_bp.route('/users/<user_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@require_role('admin')
def manage_user(user_id):
    """用户详情/更新/删除"""
    from app.repositories.user_repo import get_user_repository
    
    repo = get_user_repository()
    
    if request.method == 'GET':
        user = repo.find_by_id(user_id)
        if not user:
            return jsonify({"success": False, "error": "用户不存在"}), 404
        return jsonify({"success": True, "data": user})
    
    elif request.method == 'PUT':
        data = request.get_json()
        user = repo.update_user(user_id, data)
        if not user:
            return jsonify({"success": False, "error": "更新失败"}), 400
        return jsonify({"success": True, "data": user})
    
    elif request.method == 'DELETE':
        # TODO: 实现删除逻辑
        return jsonify({"success": False, "error": "暂不支持删除用户"}), 501


# =============================================================================
# 审计日志 API (需要 admin 角色)
# =============================================================================

@admin_bp.route('/audit-logs', methods=['GET'])
@login_required
@require_role('admin')
def list_audit_logs():
    """获取审计日志"""
    from app.services.audit_service import get_audit_service
    
    user_id = request.args.get('user_id')
    action = request.args.get('action')
    limit = int(request.args.get('limit', 100))
    
    service = get_audit_service()
    logs = service.query(user_id=user_id, action=action, limit=limit)
    
    return jsonify({
        "success": True,
        "data": logs
    })


# =============================================================================
# 系统信息 API
# =============================================================================

@admin_bp.route('/system/info', methods=['GET'])
def get_system_info():
    """获取系统信息"""
    import sys
    import platform
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if gpu_available else None
    except ImportError:
        gpu_available = False
        gpu_name = None
    
    return jsonify({
        "success": True,
        "data": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "gpu_available": gpu_available,
            "gpu_name": gpu_name,
            "architecture": {
                "phase": "Phase 1 - 模块化拆分",
                "use_supabase": False,  # TODO: 从配置读取
                "auth_enabled": False,  # TODO: 从配置读取
            }
        }
    })
