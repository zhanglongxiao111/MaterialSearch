"""
搜索 API Blueprint

提供图片和视频的向量相似度搜索功能。
"""
import os
import logging

from flask import Blueprint, request, jsonify, session, abort

# 导入搜索服务（暂时使用旧模块，后续迁移到 services 层）
from app.services.search_service import (
    search_image_by_image,
    search_image_by_text_path_time,
    search_video_by_image,
    search_video_by_text_path_time,
    search_pexels_video_by_text,
)
from app.services.asset_service import match_text_and_image, process_image, process_text
from app.services.project_service import get_project_manager

logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__)


def _parse_bool(value) -> bool:
    """解析布尔值参数"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _validate_library_type(library_type: str, project_id: str):
    """验证库类型参数"""
    if library_type not in {"permanent", "project"}:
        return {"error": "library_type 仅支持 'permanent' 或 'project'"}, 400
    
    if library_type == "project":
        if not project_id:
            return {"error": "library_type='project' 时必须提供 project_id"}, 400
        pm = get_project_manager()
        project = pm.get_project(project_id)
        if not project:
            return {"error": f"项目不存在: {project_id}"}, 404
    
    return None


@search_bp.route('/match', methods=['POST'])
def match():
    """
    统一搜索接口
    
    支持的 search_type:
    - 0: 文字搜图片
    - 1: 图片搜图片（上传文件）
    - 2: 文字搜视频
    - 3: 图片搜视频（上传文件）
    - 4: 计算图文相似度
    - 5: 图片搜图片（使用已有图片ID）
    - 6: 图片搜视频（使用已有图片ID）
    - 9: 搜索 Pexels 视频
    """
    data = request.get_json()
    
    # 解析参数
    try:
        top_n = int(data.get("top_n", 0))
    except (TypeError, ValueError):
        top_n = 0
    
    search_type = data.get("search_type")
    positive_threshold = data.get("positive_threshold", 0.27)
    negative_threshold = data.get("negative_threshold", 0.27)
    image_threshold = data.get("image_threshold", 0.9)
    img_id = data.get("img_id")
    path = data.get("path", "")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    
    # 库类型参数
    library_type = data.get("library_type", "permanent")
    project_id = data.get("project_id")
    
    # 验证库类型
    validation_error = _validate_library_type(library_type, project_id)
    if validation_error:
        return jsonify(validation_error[0]), validation_error[1]
    
    # 是否包含重复图片
    include_duplicates = _parse_bool(data.get("include_duplicates", False))
    if library_type != "permanent":
        include_duplicates = True
    
    # 获取上传文件路径
    upload_file_path = session.get('upload_file_path', '')
    session['upload_file_path'] = ""
    
    # 验证上传文件
    if search_type in (1, 3, 4):
        if not upload_file_path or not os.path.exists(upload_file_path):
            return jsonify({"error": "你没有上传文件！"}), 400
    
    # 检查空查询
    blank_query = False
    if search_type in (0, 2):
        blank_query = not any([
            data.get("positive"),
            data.get("negative"),
            path,
            start_time,
            end_time,
        ])
    
    if library_type == "permanent" and blank_query:
        return jsonify({"error": "永久库暂不支持空搜索，请输入关键词或路径"}), 400
    
    # 执行搜索
    logger.debug(f"搜索请求: type={search_type}, library={library_type}")
    
    if search_type == 0:
        # 文字搜图片
        results = search_image_by_text_path_time(
            data.get("positive", ""), data.get("negative", ""),
            positive_threshold, negative_threshold,
            path, start_time, end_time,
            library_type, project_id,
            include_duplicates=include_duplicates
        )
    elif search_type == 1:
        # 图片搜图片（上传文件）
        results = search_image_by_image(
            upload_file_path, image_threshold,
            path, start_time, end_time,
            library_type, project_id,
            include_duplicates=include_duplicates
        )
    elif search_type == 2:
        # 文字搜视频
        results = search_video_by_text_path_time(
            data.get("positive", ""), data.get("negative", ""),
            positive_threshold, negative_threshold,
            path, start_time, end_time,
            library_type, project_id
        )
    elif search_type == 3:
        # 图片搜视频（上传文件）
        results = search_video_by_image(
            upload_file_path, image_threshold,
            path, start_time, end_time,
            library_type, project_id
        )
    elif search_type == 4:
        # 计算图文相似度
        score = match_text_and_image(
            process_text(data.get("positive", "")),
            process_image(upload_file_path)
        ) * 100
        return jsonify({"score": "%.2f" % score})
    elif search_type == 5:
        # 图片搜图片（使用已有图片ID）
        results = search_image_by_image(
            img_id, image_threshold,
            path, start_time, end_time,
            library_type, project_id,
            include_duplicates=include_duplicates
        )
    elif search_type == 6:
        # 图片搜视频（使用已有图片ID）
        results = search_video_by_image(
            img_id, image_threshold,
            path, start_time, end_time,
            library_type, project_id
        )
    elif search_type == 9:
        # 搜索 Pexels 视频
        results = search_pexels_video_by_text(
            data.get("positive", ""),
            positive_threshold
        )
    else:
        logger.warning(f"search_type 不正确: {search_type}")
        abort(400)
    
    # 返回结果
    if isinstance(results, list):
        limit = len(results) if top_n <= 0 else top_n
        return jsonify(results[:limit])
    return jsonify(results)


@search_bp.route('/images/text', methods=['POST'])
def search_images_by_text():
    """
    文字搜图片（简化接口）
    
    Request Body:
    {
        "positive_prompt": "搜索关键词",
        "negative_prompt": "排除关键词（可选）",
        "threshold": 0.27,
        "limit": 100,
        "project_id": "proj_xxx"（可选）
    }
    """
    data = request.get_json()
    
    positive = data.get("positive_prompt", "")
    negative = data.get("negative_prompt", "")
    threshold = float(data.get("threshold", 0.27))
    limit = int(data.get("limit", 100))
    project_id = data.get("project_id")
    
    library_type = "project" if project_id else "permanent"
    
    if library_type == "project":
        validation_error = _validate_library_type(library_type, project_id)
        if validation_error:
            return jsonify(validation_error[0]), validation_error[1]
    
    results = search_image_by_text_path_time(
        positive, negative,
        threshold, threshold,
        "", None, None,
        library_type, project_id,
        include_duplicates=True
    )
    
    if isinstance(results, list):
        return jsonify(results[:limit])
    return jsonify(results)


@search_bp.route('/videos/text', methods=['POST'])
def search_videos_by_text():
    """
    文字搜视频（简化接口）
    """
    data = request.get_json()
    
    positive = data.get("positive_prompt", "")
    negative = data.get("negative_prompt", "")
    threshold = float(data.get("threshold", 0.27))
    limit = int(data.get("limit", 100))
    project_id = data.get("project_id")
    
    library_type = "project" if project_id else "permanent"
    
    if library_type == "project":
        validation_error = _validate_library_type(library_type, project_id)
        if validation_error:
            return jsonify(validation_error[0]), validation_error[1]
    
    results = search_video_by_text_path_time(
        positive, negative,
        threshold, threshold,
        "", None, None,
        library_type, project_id
    )
    
    if isinstance(results, list):
        return jsonify(results[:limit])
    return jsonify(results)
