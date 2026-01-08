"""
项目管理 API Blueprint

提供项目的 CRUD 操作和统计信息查询。
"""
import logging

from flask import Blueprint, request, jsonify

from app.services.project_service import get_project_manager
from app.services.search_service import clean_cache
from .auth import login_required, require_role

logger = logging.getLogger(__name__)

projects_bp = Blueprint('projects', __name__)


def _serialize_project(project) -> dict:
    """序列化项目对象为字典"""
    return {
        "id": project.id,
        "name": project.name,
        "client_name": project.client_name,
        "description": project.description,
        "status": project.status,
        "image_count": getattr(project, 'image_count', 0),
        "video_count": getattr(project, 'video_count', 0),
        "total_size": getattr(project, 'total_size', 0),
        "created_time": project.created_time.isoformat() if project.created_time else None,
        "updated_time": project.updated_time.isoformat() if project.updated_time else None,
    }


@projects_bp.route('/', methods=['GET'])
def list_projects():
    """获取项目列表"""
    pm = get_project_manager()
    
    status = request.args.get("status")
    include_deleted = request.args.get("include_deleted", "false").lower() == "true"
    
    try:
        projects = pm.list_projects(status=status, include_deleted=include_deleted)
        return jsonify({
            "success": True,
            "data": [_serialize_project(p) for p in projects]
        })
    except Exception as e:
        logger.error(f"获取项目列表失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@projects_bp.route('/', methods=['POST'])
def create_project():
    """创建新项目"""
    pm = get_project_manager()
    
    data = request.get_json()
    name = data.get("name")
    client_name = data.get("client_name")
    description = data.get("description")
    
    if not name:
        return jsonify({"success": False, "error": "项目名称不能为空"}), 400
    
    try:
        project = pm.create_project(
            name=name,
            client_name=client_name,
            description=description
        )
        return jsonify({
            "success": True,
            "data": _serialize_project(project)
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"创建项目失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@projects_bp.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    """获取项目详情"""
    pm = get_project_manager()
    
    try:
        project = pm.get_project(project_id)
        if not project:
            return jsonify({"success": False, "error": "项目不存在"}), 404
        
        return jsonify({
            "success": True,
            "data": _serialize_project(project)
        })
    except Exception as e:
        logger.error(f"获取项目详情失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@projects_bp.route('/<project_id>', methods=['PUT'])
def update_project(project_id):
    """更新项目"""
    pm = get_project_manager()
    
    data = request.get_json()
    try:
        project = pm.update_project(
            project_id=project_id,
            name=data.get("name"),
            client_name=data.get("client_name"),
            description=data.get("description"),
            status=data.get("status")
        )
        return jsonify({
            "success": True,
            "data": _serialize_project(project)
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"更新项目失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@projects_bp.route('/<project_id>', methods=['DELETE'])
@login_required
@require_role('admin', 'designer')
def delete_project(project_id):
    """删除项目（需要 admin 或 designer 角色）"""
    pm = get_project_manager()
    
    hard_delete = request.args.get("hard_delete", "false").lower() == "true"
    try:
        pm.delete_project(project_id, hard_delete=hard_delete)
        return jsonify({"success": True, "message": "项目已删除"})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@projects_bp.route('/<project_id>/stats', methods=['GET'])
def get_project_stats(project_id):
    """获取项目统计信息"""
    pm = get_project_manager()
    
    try:
        stats = pm.get_project_stats(project_id)
        return jsonify({"success": True, "data": stats})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        logger.error(f"获取项目统计失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@projects_bp.route('/<project_id>/update_stats', methods=['POST'])
def update_project_stats(project_id):
    """更新项目统计信息"""
    pm = get_project_manager()
    
    try:
        pm.update_project_stats(project_id)
        return jsonify({"success": True, "message": "统计信息已更新"})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        logger.error(f"更新项目统计失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@projects_bp.route('/<project_id>/images/delete', methods=['POST'])
@login_required
@require_role('admin', 'designer')
def delete_project_images(project_id):
    """删除项目库中的图片记录（需要 admin 或 designer 角色）"""
    pm = get_project_manager()
    
    data = request.get_json() or {}
    image_ids = data.get("image_ids", [])
    
    if not isinstance(image_ids, list) or not image_ids:
        return jsonify({"success": False, "error": "未指定要删除的图片"}), 400
    
    try:
        # 规范化 ID
        normalized_ids = []
        for img_id in image_ids:
            try:
                normalized_ids.append(int(img_id))
            except (TypeError, ValueError):
                continue
        
        if not normalized_ids:
            return jsonify({"success": False, "error": "图片 ID 不合法"}), 400
        
        result = pm.delete_project_images(project_id, normalized_ids)
        pm.update_project_stats(project_id)
        clean_cache()
        return jsonify({"success": True, "data": result})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"删除项目图片失败: {e}")
        return jsonify({"success": False, "error": "删除失败，请稍后重试"}), 500
