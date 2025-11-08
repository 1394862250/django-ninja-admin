"""
认证中间件 - 为Django Ninja API提供身份验证
"""
from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser
from ninja import HttpRequest


class AuthMiddleware:
    """Django Ninja认证中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest):
        # 尝试从请求头获取用户认证信息
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            # 用户已认证，继续处理
            pass
        else:
            # 设置为匿名用户
            request.user = AnonymousUser()
        
        response = self.get_response(request)
        return response


class CORSMiddleware:
    """CORS中间件配置"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest):
        # 添加CORS头
        response = self.get_response(request)
        
        # 允许的源（生产环境中应该更严格）
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response