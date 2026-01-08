"""
归档 API Blueprint

提供项目图片归档到永久库的功能。
"""
import logging

from flask import Blueprint, request, jsonify

from app.services.archive_service import get_archive_manager

logger = logging.getLogger(__name__)

archive_bp = Blueprint('archive', __name__)


@archive_bp.route('/projects/<project_id>/archive', methods=['POST'])
def archive_images(project_id):
    """归档项目图片到永久库"""
    am = get_archive_manager()
    
    data = request.get_json()
    image_ids = data.get("image_ids", [])
    mark_archived = data.get("mark_archived", True)
    
    if not image_ids:
        return jsonify({"success": False, "error": "未指定要归档的图片"}), 400
    
    try:
        result = am.archive_images_to_permanent(
            project_id=project_id,
            image_ids=image_ids,
            mark_archived=mark_archived
        )
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"归档失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@archive_bp.route('/projects/<project_id>/archived', methods=['GET'])
def get_archived_images(project_id):
    """获取项目中已归档的图片列表"""
    am = get_archive_manager()
    
    try:
        archived_images = am.get_archived_images(project_id)
        return jsonify({
            "success": True,
            "data": archived_images
        })
    except Exception as e:
        logger.error(f"获取归档列表失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@archive_bp.route('/projects/<project_id>/unarchive', methods=['POST'])
def unarchive_images(project_id):
    """取消归档标记"""
    am = get_archive_manager()
    
    data = request.get_json()
    image_ids = data.get("image_ids", [])
    
    if not image_ids:
        return jsonify({"success": False, "error": "未指定要取消归档的图片"}), 400
    
    try:
        result = am.unarchive_images(project_id, image_ids)
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"取消归档失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
