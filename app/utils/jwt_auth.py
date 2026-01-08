"""
JWT 认证工具

提供 JWT 令牌的生成、验证和解析功能。
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def get_jwt_config() -> dict:
    """获取 JWT 配置"""
    return {
        'secret': os.getenv('JWT_SECRET', 'your-secret-key-change-in-production'),
        'algorithm': 'HS256',
        'expiration_hours': int(os.getenv('JWT_EXPIRATION_HOURS', '24')),
    }


def create_token(user_id: str, email: str, role: str = 'designer') -> str:
    """
    创建 JWT 令牌
    
    Args:
        user_id: 用户 ID
        email: 用户邮箱
        role: 用户角色
    
    Returns:
        JWT 令牌字符串
    """
    try:
        from jose import jwt
    except ImportError:
        raise ImportError("python-jose 未安装，请运行: pip install python-jose[cryptography]")
    
    config = get_jwt_config()
    
    payload = {
        'sub': user_id,
        'email': email,
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=config['expiration_hours']),
    }
    
    token = jwt.encode(payload, config['secret'], algorithm=config['algorithm'])
    return token


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证并解析 JWT 令牌
    
    Args:
        token: JWT 令牌字符串
    
    Returns:
        解析后的 payload，验证失败返回 None
    """
    try:
        from jose import jwt, JWTError
    except ImportError:
        raise ImportError("python-jose 未安装，请运行: pip install python-jose[cryptography]")
    
    config = get_jwt_config()
    
    try:
        payload = jwt.decode(
            token, 
            config['secret'], 
            algorithms=[config['algorithm']]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT 验证失败: {e}")
        return None


def decode_token_without_verification(token: str) -> Optional[Dict[str, Any]]:
    """
    解码 JWT 令牌（不验证签名）
    
    用于日志和调试，不要用于认证！
    
    Args:
        token: JWT 令牌字符串
    
    Returns:
        解析后的 payload
    """
    try:
        from jose import jwt
    except ImportError:
        return None
    
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception:
        return None


def is_token_expired(token: str) -> bool:
    """
    检查令牌是否过期
    
    Args:
        token: JWT 令牌字符串
    
    Returns:
        是否已过期
    """
    payload = decode_token_without_verification(token)
    if not payload or 'exp' not in payload:
        return True
    
    exp = datetime.fromtimestamp(payload['exp'])
    return datetime.utcnow() > exp


def extract_user_from_request(request) -> Optional[Dict[str, Any]]:
    """
    从 Flask Request 中提取用户信息
    
    支持：
    - Authorization: Bearer <token>
    - X-Access-Token: <token>
    
    Args:
        request: Flask request 对象
    
    Returns:
        用户信息字典，未认证返回 None
    """
    token = None
    
    # 从 Authorization header 提取
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    
    # 从 X-Access-Token header 提取
    if not token:
        token = request.headers.get('X-Access-Token')
    
    if not token:
        return None
    
    payload = verify_token(token)
    if not payload:
        return None
    
    return {
        'id': payload.get('sub'),
        'email': payload.get('email'),
        'role': payload.get('role', 'viewer'),
    }
