"""全局通用权限与校验工具。"""
from ninja_extra.permissions import BasePermission

from .exceptions import AuthenticationException, PermissionException


class IsAuthenticated(BasePermission):
    """必须已登录"""

    def has_permission(self, request, controller) -> bool:
        return bool(getattr(request, "user", None) and request.user.is_authenticated)


class IsStaffOrSuperuser(BasePermission):
    """必须是 staff 或 superuser"""

    def has_permission(self, request, controller) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


class IsSuperuser(BasePermission):
    """必须是超级管理员"""

    def has_permission(self, request, controller) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_superuser)


def ensure_authenticated(user):
    """确保用户已登录，否则抛 AuthenticationException。"""
    if not user or not getattr(user, "is_authenticated", False):
        raise AuthenticationException("需要登录访问")


def ensure_staff_or_superuser(user):
    """确保用户为 staff 或 superuser，否则抛 PermissionException。"""
    ensure_authenticated(user)
    if not (user.is_staff or user.is_superuser):
        raise PermissionException("需要管理员权限")


def ensure_superuser(user):
    """确保用户为超级管理员，否则抛 PermissionException。"""
    ensure_authenticated(user)
    if not user.is_superuser:
        raise PermissionException("需要超级管理员权限")


__all__ = [
    "IsAuthenticated",
    "IsStaffOrSuperuser",
    "IsSuperuser",
    "ensure_authenticated",
    "ensure_staff_or_superuser",
    "ensure_superuser",
]
