"""
素材处理 API Blueprint

提供图片、视频的获取、上传和缩略图功能。
"""
import base64
import os
import logging
from io import BytesIO

from flask import Blueprint, request, jsonify, session, send_file, abort

from app.integrations.sqlite_manager import get_db_manager, is_video_exist
from app.models import Image
from models import DatabaseSession
from app.utils.common import get_hash, crop_video, resize_image_with_aspect_ratio
from app.utils.image import extract_rhino_preview

logger = logging.getLogger(__name__)

assets_bp = Blueprint('assets', __name__)

# 临时路径（从配置读取）
TEMP_PATH = os.getenv('TEMP_PATH', './tmp')
VIDEO_EXTENSION_LENGTH = int(os.getenv('VIDEO_EXTENSION_LENGTH', '2'))


@assets_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    上传文件（用于以图搜图）
    
    上传的文件保存到临时目录，路径存储在 session 中供后续搜索使用。
    """
    logger.debug(f"上传请求: {request.files}")
    
    # 清理之前的上传文件
    upload_file_path = session.get('upload_file_path', '')
    if upload_file_path and os.path.exists(upload_file_path):
        try:
            os.remove(upload_file_path)
        except Exception as e:
            logger.warning(f"清理旧上传文件失败: {e}")
    
    # 保存新文件
    if 'file' not in request.files:
        return jsonify({"error": "未提供文件"}), 400
    
    f = request.files["file"]
    filehash = get_hash(f.stream)
    upload_file_path = f"{TEMP_PATH}/upload/{filehash}"
    
    # 确保目录存在
    os.makedirs(os.path.dirname(upload_file_path), exist_ok=True)
    
    f.save(upload_file_path)
    session['upload_file_path'] = upload_file_path
    
    return jsonify({"success": True, "message": "文件上传成功"})


@assets_bp.route('/images/<int:image_id>', methods=['GET'])
def get_image(image_id):
    """
    获取图片
    
    Query Parameters:
        target (str): 'permanent' 或 'proj_xxx'，默认 'permanent'
        thumbnail (bool): 是否返回缩略图
    """
    target = request.args.get('target', 'permanent')
    
    # 获取正确的 session
    if target == 'permanent':
        db_session = get_db_manager().get_permanent_session()
    elif target.startswith('proj_'):
        db_session = get_db_manager().get_project_session(target)
    else:
        db_session = DatabaseSession()
    
    with db_session:
        image = db_session.query(Image).filter(Image.id == image_id).first()
        if not image:
            abort(404)
        
        # 缩略图
        if request.args.get('thumbnail'):
            img = resize_image_with_aspect_ratio(image.path, (640, 480), convert_rgb=True)
            img_io = BytesIO()
            img.save(img_io, 'JPEG', quality=60)
            img_io.seek(0)
            return send_file(img_io, mimetype='image/jpeg')
        
        # Rhino 3dm 文件：返回提取的预览图
        if image.path.lower().endswith('.3dm'):
            img = extract_rhino_preview(image.path)
            if img:
                img_io = BytesIO()
                img.save(img_io, 'JPEG', quality=95)
                img_io.seek(0)
                return send_file(img_io, mimetype='image/jpeg')
        
        # 返回原始文件
        return send_file(image.path)


@assets_bp.route('/videos/<path:video_path>', methods=['GET'])
def get_video(video_path):
    """
    获取视频
    
    video_path 是 base64 编码的视频路径
    """
    decoded_path = base64.urlsafe_b64decode(video_path).decode()
    
    if not os.path.exists(decoded_path):
        abort(404)
    
    return send_file(decoded_path)


@assets_bp.route('/videos/<path:video_path>/clip', methods=['GET'])
def download_video_clip(video_path):
    """
    下载视频片段
    
    Query Parameters:
        start_time (int): 开始时间（秒）
        end_time (int): 结束时间（秒）
    """
    decoded_path = base64.urlsafe_b64decode(video_path).decode()
    
    try:
        start_time = int(request.args.get('start_time', 0))
        end_time = int(request.args.get('end_time', 0))
    except (TypeError, ValueError):
        return jsonify({"error": "start_time 和 end_time 必须是整数"}), 400
    
    if end_time <= start_time:
        return jsonify({"error": "end_time 必须大于 start_time"}), 400
    
    with DatabaseSession() as session_db:
        if not is_video_exist(session_db, decoded_path):
            abort(404)
    
    # 扩展时间范围
    start_time = max(0, start_time - VIDEO_EXTENSION_LENGTH)
    end_time += VIDEO_EXTENSION_LENGTH
    
    # 生成输出路径
    output_dir = f"{TEMP_PATH}/video_clips"
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/{start_time}_{end_time}_{os.path.basename(decoded_path)}"
    
    # 裁剪视频
    if not os.path.exists(output_path):
        crop_video(decoded_path, output_path, start_time, end_time)
    
    return send_file(output_path)
