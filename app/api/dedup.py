"""
去重 API Blueprint

提供图片去重任务的创建、状态查询和报告功能。
"""
import logging

from flask import Blueprint, request, jsonify

from app.services.dedup_service import get_dedup_service
from app.integrations.sqlite_manager import get_db_manager
from app.models import DedupJob

logger = logging.getLogger(__name__)

dedup_bp = Blueprint('dedup', __name__)


@dedup_bp.route('/jobs', methods=['POST'])
def start_dedup_job():
    """
    启动去重任务
    
    Request Body:
    {
        "library_type": "permanent",  // 或 "project"
        "include_phash": true,         // 是否使用感知哈希
        "include_clip": true           // 是否使用 CLIP 相似度
    }
    """
    data = request.get_json() or {}
    library_type = data.get("library_type", "permanent")
    include_phash = data.get("include_phash", True)
    include_clip = data.get("include_clip", True)
    
    dedup_service = get_dedup_service()
    
    # 检查是否有运行中的任务
    if dedup_service.has_running_job:
        return jsonify({
            "success": False,
            "error": "已有去重任务在运行中"
        }), 409
    
    try:
        job_id = dedup_service.start_job(
            library_type=library_type,
            include_phash=include_phash,
            include_clip=include_clip
        )
        return jsonify({
            "success": True,
            "data": {"job_id": job_id}
        })
    except Exception as e:
        logger.error(f"启动去重任务失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@dedup_bp.route('/jobs', methods=['GET'])
def list_dedup_jobs():
    """获取去重任务列表"""
    limit = int(request.args.get("limit", 10))
    
    try:
        db_manager = get_db_manager()
        session = db_manager.get_permanent_session()
        
        with session:
            jobs = session.query(DedupJob).order_by(
                DedupJob.created_time.desc()
            ).limit(limit).all()
            
            return jsonify({
                "success": True,
                "data": [
                    {
                        "id": job.id,
                        "status": job.status,
                        "current_phase": job.current_phase,
                        "progress_percent": job.progress_percent,
                        "total_duplicates": job.total_duplicates,
                        "created_time": job.created_time.isoformat() if job.created_time else None,
                        "completed_time": job.completed_time.isoformat() if job.completed_time else None,
                    }
                    for job in jobs
                ]
            })
    except Exception as e:
        logger.error(f"获取去重任务列表失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@dedup_bp.route('/jobs/<job_id>', methods=['GET'])
def get_dedup_job(job_id):
    """获取去重任务详情"""
    try:
        db_manager = get_db_manager()
        session = db_manager.get_permanent_session()
        
        with session:
            job = session.query(DedupJob).filter(DedupJob.id == job_id).first()
            
            if not job:
                return jsonify({"success": False, "error": "任务不存在"}), 404
            
            return jsonify({
                "success": True,
                "data": {
                    "id": job.id,
                    "status": job.status,
                    "current_phase": job.current_phase,
                    "progress_percent": job.progress_percent,
                    "total_duplicates": job.total_duplicates,
                    "error_message": job.error_message,
                    "created_time": job.created_time.isoformat() if job.created_time else None,
                    "completed_time": job.completed_time.isoformat() if job.completed_time else None,
                }
            })
    except Exception as e:
        logger.error(f"获取去重任务详情失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@dedup_bp.route('/status', methods=['GET'])
def get_dedup_status():
    """获取当前去重服务状态"""
    dedup_service = get_dedup_service()
    
    return jsonify({
        "success": True,
        "data": {
            "has_running_job": dedup_service.has_running_job
        }
    })
