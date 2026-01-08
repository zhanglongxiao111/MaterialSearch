"""
认证 API Blueprint

提供用户登录、登出、注册和会话管理功能。
支持 Supabase Auth (JWT) 和本地 Session 两种模式。
"""
import os
import logging
from functools import wraps

from flask import Blueprint, request, jsonify, session, g

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


def use_supabase_auth() -> bool:
    """检查是否使用 Supabase Auth"""
    return os.getenv('USE_SUPABASE', 'false').lower() == 'true'


def login_required(f):
    """
    登录验证装饰器
    
    支持两种模式：
    - Supabase: 验证 Bearer Token (JWT)
    - 本地: 验证 Flask Session
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 检查是否启用登录
        if not os.getenv('ENABLE_LOGIN', 'false').lower() == 'true':
            return f(*args, **kwargs)
        
        if use_supabase_auth():
            # Supabase JWT 验证
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return jsonify({
                    'error': {'code': 'UNAUTHORIZED', 'message': '需要认证'}
                }), 401
            
            token = auth_header[7:]  # 去掉 'Bearer '
            try:
                from app.integrations.supabase_client import get_supabase
                client = get_supabase()
                user = client.auth.get_user(token)
                if not user:
                    raise ValueError("无效的 Token")
                g.user = user.user
                g.token = token
            except Exception as e:
                logger.warning(f"Token 验证失败: {e}")
                return jsonify({
                    'error': {'code': 'UNAUTHORIZED', 'message': 'Token 无效或已过期'}
                }), 401
        else:
            # 本地 Session 验证
            if 'username' not in session:
                return jsonify({
                    'error': {'code': 'UNAUTHORIZED', 'message': '需要登录'}
                }), 401
            g.user = {'email': session.get('username'), 'role': 'admin'}
        
        return f(*args, **kwargs)
    return decorated


def require_role(*roles):
    """
    角色验证装饰器
    
    Usage:
        @require_role('admin')
        @require_role('admin', 'designer')
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'user') or not g.user:
                return jsonify({
                    'error': {'code': 'UNAUTHORIZED', 'message': '需要认证'}
                }), 401
            
            # 获取用户角色
            user_role = g.user.get('role', 'viewer')
            if use_supabase_auth():
                # 从 user_profiles 获取角色
                # TODO: 实现 Supabase 角色查询
                user_role = 'designer'  # 临时默认
            
            if user_role not in roles:
                return jsonify({
                    'error': {'code': 'FORBIDDEN', 'message': f'需要 {roles} 角色'}
                }), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator


# =============================================================================
# 登录/登出 API
# =============================================================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    
    Request Body:
    {
        "email": "user@example.com",
        "password": "password"
    }
    
    Response:
    {
        "success": true,
        "data": {
            "access_token": "...",
            "refresh_token": "...",
            "user": {...}
        }
    }
    """
    data = request.get_json()
    email = data.get('email', '')
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({
            'success': False,
            'error': '邮箱和密码不能为空'
        }), 400
    
    if use_supabase_auth():
        # Supabase 登录
        try:
            from app.integrations.supabase_client import SupabaseAuth
            auth = SupabaseAuth()
            response = auth.sign_in(email, password)
            
            return jsonify({
                'success': True,
                'data': {
                    'access_token': response.session.access_token,
                    'refresh_token': response.session.refresh_token,
                    'user': {
                        'id': response.user.id,
                        'email': response.user.email,
                    }
                }
            })
        except Exception as e:
            # 记录登录失败
            try:
                from app.services.audit_service import get_audit_service
                get_audit_service().log_login(None, email, success=False)
            except:
                pass
            logger.warning(f"Supabase 登录失败: {e}")
            return jsonify({
                'success': False,
                'error': '邮箱或密码错误'
            }), 401
    else:
        # 本地登录（兼容模式）
        username = os.getenv('USERNAME', 'admin')
        password_env = os.getenv('PASSWORD', 'admin')
        
        if email == username and password == password_env:
            session['username'] = email
            logger.info(f"用户登录成功: {email}")
            # 记录登录成功
            try:
                from app.services.audit_service import get_audit_service
                get_audit_service().log_login('local_admin', email, success=True)
            except:
                pass
            return jsonify({
                'success': True,
                'data': {
                    'user': {'email': email, 'role': 'admin'}
                }
            })
        else:
            logger.warning(f"用户登录失败: {email}")
            # 记录登录失败
            try:
                from app.services.audit_service import get_audit_service
                get_audit_service().log_login(None, email, success=False)
            except:
                pass
            return jsonify({
                'success': False,
                'error': '用户名或密码错误'
            }), 401


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    if use_supabase_auth():
        try:
            from app.integrations.supabase_client import SupabaseAuth
            auth = SupabaseAuth()
            auth.sign_out()
        except Exception as e:
            logger.warning(f"Supabase 登出失败: {e}")
    else:
        session.clear()
    
    return jsonify({'success': True, 'message': '已登出'})


@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """刷新 Token"""
    if not use_supabase_auth():
        return jsonify({
            'success': False,
            'error': '本地模式不支持 Token 刷新'
        }), 400
    
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({
            'success': False,
            'error': 'refresh_token 不能为空'
        }), 400
    
    try:
        from app.integrations.supabase_client import SupabaseAuth
        auth = SupabaseAuth()
        response = auth.refresh_session(refresh_token)
        
        return jsonify({
            'success': True,
            'data': {
                'access_token': response.session.access_token,
            }
        })
    except Exception as e:
        logger.warning(f"Token 刷新失败: {e}")
        return jsonify({
            'success': False,
            'error': 'refresh_token 无效或已过期'
        }), 401


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """获取当前用户信息"""
    user = g.user
    
    return jsonify({
        'success': True,
        'data': {
            'id': user.get('id'),
            'email': user.get('email'),
            'role': user.get('role', 'viewer'),
        }
    })


# =============================================================================
# 用户注册（仅管理员）
# =============================================================================

@auth_bp.route('/register', methods=['POST'])
@login_required
@require_role('admin')
def register_user():
    """
    注册新用户（仅管理员）
    
    Request Body:
    {
        "email": "newuser@example.com",
        "password": "password",
        "role": "designer"
    }
    """
    if not use_supabase_auth():
        return jsonify({
            'success': False,
            'error': '本地模式不支持用户注册'
        }), 400
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'designer')
    
    if not email or not password:
        return jsonify({
            'success': False,
            'error': '邮箱和密码不能为空'
        }), 400
    
    if role not in ('admin', 'designer', 'viewer'):
        return jsonify({
            'success': False,
            'error': '无效的角色'
        }), 400
    
    try:
        from app.integrations.supabase_client import SupabaseAuth, get_supabase
        auth = SupabaseAuth()
        response = auth.sign_up(email, password)
        
        # 创建 user_profile
        if response.user:
            get_supabase().table('user_profiles').insert({
                'id': response.user.id,
                'email': email,
                'role': role
            }).execute()
        
        return jsonify({
            'success': True,
            'data': {'user_id': response.user.id if response.user else None}
        })
    except Exception as e:
        logger.error(f"用户注册失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
