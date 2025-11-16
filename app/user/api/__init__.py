"""
User API模块
导出所有API类
"""

from .base import BaseUserAPI, success_response, error_response
from .captcha import CaptchaAPI
from .auth import AuthAPI
from .user import UserAPI
from .user_feature import UserFeatureAPI
from .admin import AdminAPI
from .role_permission import RolePermissionAPI
from ninja import Router


def create_user_api_router():
    """创建用户API路由器并注册所有模块"""
    api = Router(tags=['用户API'])
    
    # 创建各个API模块实例
    CaptchaAPI(api)
    AuthAPI(api)
    UserAPI(api)
    UserFeatureAPI(api)
    AdminAPI(api)
    
    return api

def create_captcha_api_router():
    """创建验证码API路由器"""
    api = Router(tags=['验证码API'])
    
    # 创建验证码API模块实例
    CaptchaAPI(api)
    
    return api

def create_auth_api_router():
    """创建认证API路由器"""
    api = Router(tags=['认证API'])
    
    # 创建认证API模块实例
    AuthAPI(api)
    
    return api

def create_user_feature_api_router():
    """创建用户特征API路由器"""
    api = Router(tags=['用户特征API'])
    
    # 创建用户特征API模块实例
    UserFeatureAPI(api)
    
    return api

def create_admin_api_router():
    """创建管理API路由器"""
    api = Router(tags=['用户管理API'])
    
    # 创建管理API模块实例
    AdminAPI(api)
    
    return api

def create_role_api_router():
    """创建角色API路由器"""
    api = Router(tags=['角色API'])
    
    # 创建角色API模块实例
    RolePermissionAPI(api)
    
    return api
