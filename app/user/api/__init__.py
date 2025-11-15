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
from ninja import Router

def create_user_api_router():
    """创建用户API路由器并注册所有模块"""
    api = Router(tags=['User API'])
    
    # 创建各个API模块实例
    CaptchaAPI(api)
    AuthAPI(api)
    UserAPI(api)
    UserFeatureAPI(api)
    AdminAPI(api)
    
    return api
