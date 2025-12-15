"""
权限类 - 用于 ninja-extra 控制器
仅包含协议级权限判断,不包含业务逻辑
"""
from ninja_extra.permissions import BasePermission


class IsAuthenticated(BasePermission):
    """必须已登录"""

    def has_permission(self, request, controller) -> bool:
        return request.user.is_authenticated


class IsStaffOrSuperuser(BasePermission):
    """必须是 staff 或 superuser"""

    def has_permission(self, request, controller) -> bool:
        return (
            request.user.is_authenticated and
            (request.user.is_staff or request.user.is_superuser)
        )
