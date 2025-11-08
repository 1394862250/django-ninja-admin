"""
CORS中间件 - 处理跨域请求
"""
from django.http import JsonResponse
from ninja import HttpRequest
import json


class CORSApiMiddleware:
    """Django Ninja CORS中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest):
        # 处理OPTIONS预检请求
        if request.method == "OPTIONS":
            response = JsonResponse({})
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        # 处理正常请求
        response = self.get_response(request)
        
        # 添加CORS头
        if hasattr(response, 'headers'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response