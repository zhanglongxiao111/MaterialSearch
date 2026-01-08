"""
审计日志模型

记录系统中的重要操作，用于安全审计和问题追踪。
"""
from sqlalchemy import Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.sql import func

from .base import BaseModel


class AuditLog(BaseModel):
    """审计日志模型"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)  # 可以是本地用户ID或Supabase UUID
    username = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False, index=True)  # login, logout, search, upload, delete, etc.
    resource_type = Column(String(50), nullable=True)  # image, video, project, user
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)  # 额外的操作详情
    ip_address = Column(String(45), nullable=True)  # 支持 IPv6
    user_agent = Column(Text, nullable=True)
    status = Column(String(20), default='success')  # success, failure, error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.action} by {self.username} at {self.created_at}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# 常用的审计动作常量
class AuditAction:
    # 认证相关
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    
    # 用户管理
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ROLE_CHANGE = "user_role_change"
    
    # 项目操作
    PROJECT_CREATE = "project_create"
    PROJECT_UPDATE = "project_update"
    PROJECT_DELETE = "project_delete"
    PROJECT_ARCHIVE = "project_archive"
    
    # 素材操作
    IMAGE_UPLOAD = "image_upload"
    IMAGE_DELETE = "image_delete"
    VIDEO_UPLOAD = "video_upload"
    VIDEO_DELETE = "video_delete"
    
    # 搜索操作
    SEARCH = "search"
    
    # 系统操作
    SCAN_START = "scan_start"
    SCAN_COMPLETE = "scan_complete"
    DEDUP_START = "dedup_start"
    DEDUP_COMPLETE = "dedup_complete"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
