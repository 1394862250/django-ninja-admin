"""
User API模块
导出所有API路由创建函数
"""

# 导入新的路由创建函数
from .auth import create_auth_api_router
from .user import create_user_api_router as create_user_api_router_new
from .user_feature import create_user_feature_api_router as create_user_feature_api_router_new
from .admin import create_admin_api_router as create_admin_api_router_new

# 暂时保留旧的 API 类导入
from .base import BaseUserAPI, success_response, error_response
from .captcha import CaptchaAPI
from ninja import Router


def create_user_api_router():
    """创建用户API路由器（主路由，包含所有子路由）"""
    api = Router(tags=['用户API'])
    CaptchaAPI(api)
    # 注册用户相关路由
    user_router = create_user_api_router_new()
    api.add_router("", user_router)
    return api

def create_captcha_api_router():
    """创建验证码API路由器"""
    api = Router(tags=['验证码API'])
    CaptchaAPI(api)
    return api

# create_auth_api_router 已在 auth.py 中定义
# create_user_api_router_new 已在 user.py 中定义
# create_user_feature_api_router_new 已在 user_feature.py 中定义
# create_admin_api_router_new 已在 admin.py 中定义

def create_user_feature_api_router():
    """创建用户特征API路由器"""
    return create_user_feature_api_router_new()

def create_admin_api_router():
    """创建管理API路由器"""
    return create_admin_api_router_new()

def create_role_api_router():
    """创建角色API路由器（已删除）"""
    # Role/Permission 相关功能已删除，返回空路由
    return Router(tags=['角色API'])
