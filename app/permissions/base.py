"""
权限管理基类
"""
from abc import ABC, abstractmethod
from typing import List, Any, Optional
from django.contrib.auth.models import User
from django.http import HttpRequest


class BasePermission(ABC):
    """权限基类"""
    
    @abstractmethod
    def has_permission(self, request: HttpRequest, user: User = None) -> bool:
        """检查是否有权限"""
        pass


class AllowAll(BasePermission):
    """允许所有操作"""
    
    def has_permission(self, request: HttpRequest, user: User = None) -> bool:
        return True


class IsAuthenticated(BasePermission):
    """需要用户已认证"""
    
    def has_permission(self, request: HttpRequest, user: User = None) -> bool:
        if user is None:
            return request.user.is_authenticated
        return user.is_authenticated


class IsAdminUser(BasePermission):
    """需要管理员权限"""
    
    def has_permission(self, request: HttpRequest, user: User = None) -> bool:
        if user is None:
            return request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
        return user.is_authenticated and (user.is_staff or user.is_superuser)


class IsSelfUser(BasePermission):
    """只能操作自己的资源"""
    
    def has_permission(self, request: HttpRequest, user: User = None) -> bool:
        if user is None:
            return False
        
        # 管理员可以操作所有资源
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # 普通用户只能操作自己的资源
        return request.user.id == user.id


class PermissionChecker:
    """权限检查器"""
    
    def __init__(self):
        self.permissions: List[BasePermission] = []
    
    def add_permission(self, permission: BasePermission) -> 'PermissionChecker':
        """添加权限"""
        self.permissions.append(permission)
        return self
    
    def has_permission(self, request: HttpRequest, user: User = None) -> bool:
        """检查所有权限"""
        return all(permission.has_permission(request, user) for permission in self.permissions)