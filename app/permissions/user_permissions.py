"""
用户管理权限系统
"""
from typing import Optional
from django.contrib.auth.models import User
from django.http import HttpRequest
from .base import BasePermission, PermissionChecker, IsAuthenticated, IsAdminUser, IsSelfUser


class UserManagementPermissions:
    """用户管理权限类"""
    
    def __init__(self):
        self.checker = PermissionChecker()
    
    def can_list_users(self, request: HttpRequest) -> bool:
        """检查是否可以查看用户列表"""
        self.checker.permissions = [IsAdminUser()]
        return self.checker.has_permission(request)
    
    def can_create_user(self, request: HttpRequest) -> bool:
        """检查是否可以创建用户"""
        self.checker.permissions = [IsAdminUser()]
        return self.checker.has_permission(request)
    
    def can_view_user(self, request: HttpRequest, target_user: Optional[User] = None) -> bool:
        """检查是否可以查看特定用户信息"""
        if target_user is None:
            return False
        
        # 管理员可以查看所有用户
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # 用户可以查看自己的信息
        return request.user.id == target_user.id
    
    def can_update_user(self, request: HttpRequest, target_user: Optional[User] = None) -> bool:
        """检查是否可以更新用户信息"""
        if target_user is None:
            return False
        
        # 管理员可以更新所有用户
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # 用户可以更新自己的信息
        return request.user.id == target_user.id
    
    def can_delete_user(self, request: HttpRequest, target_user: Optional[User] = None) -> bool:
        """检查是否可以删除用户"""
        if target_user is None:
            return False
        
        # 管理员可以删除非自己之外的用户
        if request.user.is_staff or request.user.is_superuser:
            return request.user.id != target_user.id
        
        return False
    
    def can_toggle_user_status(self, request: HttpRequest, target_user: Optional[User] = None) -> bool:
        """检查是否可以切换用户状态"""
        if target_user is None:
            return False
        
        # 管理员可以切换非自己之外的用户状态
        if request.user.is_staff or request.user.is_superuser:
            return request.user.id != target_user.id
        
        return False


class AuthPermissions:
    """认证相关权限类"""
    
    def can_login(self, request: HttpRequest) -> bool:
        """检查是否可以登录"""
        # 允许所有已认证用户登录
        return True
    
    def can_register(self, request: HttpRequest) -> bool:
        """检查是否可以注册"""
        # 允许所有用户注册
        return True
    
    def can_logout(self, request: HttpRequest) -> bool:
        """检查是否可以登出"""
        return request.user.is_authenticated
    
    def can_change_password(self, request: HttpRequest) -> bool:
        """检查是否可以修改密码"""
        return request.user.is_authenticated
    
    def can_view_profile(self, request: HttpRequest) -> bool:
        """检查是否可以查看个人信息"""
        return request.user.is_authenticated


# 全局权限实例
user_permissions = UserManagementPermissions()
auth_permissions = AuthPermissions()