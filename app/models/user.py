"""
用户模型

定义用户相关的数据库模型。
"""
from sqlalchemy import Column, DateTime, Integer, String, Boolean, Text
from sqlalchemy.sql import func

from .base import BaseModel


class User(BaseModel):
    """用户模型 - 本地认证使用"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    role = Column(String(50), default='user', nullable=False)  # admin, user, viewer
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }


class UserProfile(BaseModel):
    """用户配置文件 - Supabase 兼容"""
    __tablename__ = "user_profiles"
    
    id = Column(String(36), primary_key=True)  # UUID from Supabase Auth
    username = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    role = Column(String(50), default='user', nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<UserProfile {self.username}>"
