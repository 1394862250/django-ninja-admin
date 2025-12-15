"""
基础API类和通用工具
"""

from typing import Optional, Any
from django.http import JsonResponse
from ninja import Router
from app.utils.responses import success_response, error_response


class BaseUserAPI:
    """用户API基础类"""

    def __init__(self, router: Router):
        self.router = router
        self._setup_routes()

    def _setup_routes(self):
        """设置路由，由子类实现"""
        pass

    def check_authentication(self, request):
        """检查用户认证状态"""
        if not request.user.is_authenticated:
            return error_response("需要登录访问", status_code=401)
        return None

    def check_admin_permission(self, request):
        """检查管理员权限"""
        if not request.user.is_authenticated:
            return error_response("需要登录访问", status_code=401)
        if not (request.user.is_staff or request.user.is_superuser):
            return error_response("需要管理员权限", status_code=403)
        return None

