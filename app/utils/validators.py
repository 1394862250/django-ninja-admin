"""
数据验证器
"""
import re
from typing import Any, Optional, List, Dict
from pydantic import BaseModel, EmailStr, validator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from captcha.fields import CaptchaField
from captcha.models import CaptchaStore

# 导入用户相关的验证模式
from app.user.schemas import (
    UserLoginSchema,
    UserRegisterSchema,
    AdminCreateUserSchema,
    UserUpdateSchema,
    ChangePasswordSchema,
    UserProfileUpdateSchema,
    CaptchaRequestSchema,
    CaptchaVerifySchema
)

"""
验证工具函数
"""
import re
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from django.http import JsonResponse
from ninja.errors import HttpError
from django.http import HttpRequest
from app.user.models import UserProfile


def validate_username(username):
    """验证用户名格式"""
    if not username:
        raise ValidationError("用户名不能为空")
    
    if len(username) < 3:
        raise ValidationError("用户名长度不能少于3个字符")
    
    if len(username) > 20:
        raise ValidationError("用户名长度不能超过20个字符")
    
    # 只允许字母、数字和下划线
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise ValidationError("用户名只能包含字母、数字和下划线")
    
    return True


def validate_password_strength(password):
    """验证密码强度"""
    if not password:
        raise ValidationError("密码不能为空")
    
    if len(password) < 8:
        raise ValidationError("密码长度不能少于8个字符")
    
    # 检查是否包含至少一个数字
    if not re.search(r'\d', password):
        raise ValidationError("密码必须包含至少一个数字")
    
    # 检查是否包含至少一个字母
    if not re.search(r'[a-zA-Z]', password):
        raise ValidationError("密码必须包含至少一个字母")
    
    return True


def validate_phone(phone):
    """验证手机号格式"""
    if not phone:
        return True  # 手机号可以为空
    
    # 简单的手机号验证，可根据需要调整
    if not re.match(r'^1[3-9]\d{9}$', phone):
        raise ValidationError("请输入有效的手机号码")
    
    return True


def validate_email(email):
    """验证邮箱格式"""
    if not email:
        raise ValidationError("邮箱不能为空")
    
    # 简单的邮箱验证
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError("请输入有效的邮箱地址")
    
    return True


# ==================
# 权限检查装饰器和工具函数
# ==================

def _extract_request_and_call_args(args):
    """
    从装饰器参数中提取request对象，兼容函数视图和绑定到类实例的方法
    返回 (self_obj, request, remaining_args)
    """
    if not args:
        raise ValueError("装饰器使用错误，缺少参数")
    
    potential_request = args[0]
    if isinstance(potential_request, HttpRequest) or (
        hasattr(potential_request, "user") and hasattr(potential_request, "META")
    ):
        return None, potential_request, args[1:]
    
    # 兼容绑定方法：第一个参数是self，第二个参数才是request
    if len(args) < 2:
        raise ValueError("装饰器使用错误，缺少request对象")
    
    request = args[1]
    if not isinstance(request, HttpRequest) and not (
        hasattr(request, "user") and hasattr(request, "META")
    ):
        raise ValueError("装饰器使用错误，未找到HttpRequest对象")
    
    return potential_request, request, args[2:]


def permission_required(permission_code):
    """
    权限检查装饰器
    用于检查用户是否拥有指定权限
    
    使用示例:
    @permission_required('user.view')
    def my_view(request):
        pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(*args, **kwargs):
            self_obj, request, remaining_args = _extract_request_and_call_args(args)
            # 检查用户是否已登录
            if not request.user.is_authenticated:
                if hasattr(request, 'is_api_request') and request.is_api_request:
                    raise HttpError(401, "用户未登录")
                else:
                    from django.contrib.auth.decorators import login_required
                    return login_required(view_func)(request, *args, **kwargs)
            
            # 获取用户资料
            try:
                profile = request.user.profile
            except UserProfile.DoesNotExist:
                if hasattr(request, 'is_api_request') and request.is_api_request:
                    raise HttpError(403, "用户资料不存在")
                else:
                    from django.core.exceptions import PermissionDenied
                    raise PermissionDenied("用户资料不存在")
            
            # 检查权限
            if not profile.has_permission(permission_code):
                if hasattr(request, 'is_api_request') and request.is_api_request:
                    raise HttpError(403, f"权限不足，需要权限: {permission_code}")
                else:
                    from django.core.exceptions import PermissionDenied
                    raise PermissionDenied(f"权限不足，需要权限: {permission_code}")
            
            if self_obj is not None:
                return view_func(self_obj, request, *remaining_args, **kwargs)
            return view_func(request, *remaining_args, **kwargs)
        return _wrapped_view
    return decorator


def role_required(role_code):
    """
    角色检查装饰器
    用于检查用户是否拥有指定角色
    
    使用示例:
    @role_required('admin')
    def my_view(request):
        pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(*args, **kwargs):
            self_obj, request, remaining_args = _extract_request_and_call_args(args)
            # 检查用户是否已登录
            if not request.user.is_authenticated:
                if hasattr(request, 'is_api_request') and request.is_api_request:
                    raise HttpError(401, "用户未登录")
                else:
                    from django.contrib.auth.decorators import login_required
                    return login_required(view_func)(request, *args, **kwargs)
            
            # 获取用户资料
            try:
                profile = request.user.profile
            except UserProfile.DoesNotExist:
                if hasattr(request, 'is_api_request') and request.is_api_request:
                    raise HttpError(403, "用户资料不存在")
                else:
                    from django.core.exceptions import PermissionDenied
                    raise PermissionDenied("用户资料不存在")
            
            # 检查角色
            if not profile.has_role(role_code):
                if hasattr(request, 'is_api_request') and request.is_api_request:
                    raise HttpError(403, f"权限不足，需要角色: {role_code}")
                else:
                    from django.core.exceptions import PermissionDenied
                    raise PermissionDenied(f"权限不足，需要角色: {role_code}")
            
            if self_obj is not None:
                return view_func(self_obj, request, *remaining_args, **kwargs)
            return view_func(request, *remaining_args, **kwargs)
        return _wrapped_view
    return decorator


def any_permission_required(*permission_codes):
    """
    多权限检查装饰器（满足其一即可）
    用于检查用户是否拥有指定权限中的任意一个
    
    使用示例:
    @any_permission_required('user.view', 'user.admin')
    def my_view(request):
        pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(*args, **kwargs):
            self_obj, request, remaining_args = _extract_request_and_call_args(args)
            # 检查用户是否已登录
            if not request.user.is_authenticated:
                if hasattr(request, 'is_api_request') and request.is_api_request:
                    raise HttpError(401, "用户未登录")
                else:
                    from django.contrib.auth.decorators import login_required
                    return login_required(view_func)(request, *args, **kwargs)
            
            # 获取用户资料
            try:
                profile = request.user.profile
            except UserProfile.DoesNotExist:
                if hasattr(request, 'is_api_request') and request.is_api_request:
                    raise HttpError(403, "用户资料不存在")
                else:
                    from django.core.exceptions import PermissionDenied
                    raise PermissionDenied("用户资料不存在")
            
            # 检查权限
            has_permission = False
            for permission_code in permission_codes:
                if profile.has_permission(permission_code):
                    has_permission = True
                    break
            
            if not has_permission:
                if hasattr(request, 'is_api_request') and request.is_api_request:
                    raise HttpError(403, f"权限不足，需要以下权限之一: {', '.join(permission_codes)}")
                else:
                    from django.core.exceptions import PermissionDenied
                    raise PermissionDenied(f"权限不足，需要以下权限之一: {', '.join(permission_codes)}")
            
            if self_obj is not None:
                return view_func(self_obj, request, *remaining_args, **kwargs)
            return view_func(request, *remaining_args, **kwargs)
        return _wrapped_view
    return decorator


def any_role_required(*role_codes):
    """
    多角色检查装饰器（满足其一即可）
    用于检查用户是否拥有指定角色中的任意一个
    
    使用示例:
    @any_role_required('admin', 'manager')
    def my_view(request):
        pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(*args, **kwargs):
            self_obj, request, remaining_args = _extract_request_and_call_args(args)
            # 检查用户是否已登录
            if not request.user.is_authenticated:
                if hasattr(request, 'is_api_request') and request.is_api_request:
                    raise HttpError(401, "用户未登录")
                else:
                    from django.contrib.auth.decorators import login_required
                    return login_required(view_func)(request, *args, **kwargs)
            
            # 获取用户资料
            try:
                profile = request.user.profile
            except UserProfile.DoesNotExist:
                if hasattr(request, 'is_api_request') and request.is_api_request:
                    raise HttpError(403, "用户资料不存在")
                else:
                    from django.core.exceptions import PermissionDenied
                    raise PermissionDenied("用户资料不存在")
            
            # 检查角色
            has_role = False
            for role_code in role_codes:
                if profile.has_role(role_code):
                    has_role = True
                    break
            
            if not has_role:
                if hasattr(request, 'is_api_request') and request.is_api_request:
                    raise HttpError(403, f"权限不足，需要以下角色之一: {', '.join(role_codes)}")
                else:
                    from django.core.exceptions import PermissionDenied
                    raise PermissionDenied(f"权限不足，需要以下角色之一: {', '.join(role_codes)}")
            
            if self_obj is not None:
                return view_func(self_obj, request, *remaining_args, **kwargs)
            return view_func(request, *remaining_args, **kwargs)
        return _wrapped_view
    return decorator


def check_user_permission(user, permission_code):
    """
    检查用户是否拥有指定权限的工具函数
    
    参数:
        user: User对象
        permission_code: 权限代码
    
    返回:
        bool: 是否拥有权限
    """
    if not user.is_authenticated:
        return False
    
    try:
        profile = user.profile
        return profile.has_permission(permission_code)
    except UserProfile.DoesNotExist:
        return False


def check_user_role(user, role_code):
    """
    检查用户是否拥有指定角色的工具函数
    
    参数:
        user: User对象
        role_code: 角色代码
    
    返回:
        bool: 是否拥有角色
    """
    if not user.is_authenticated:
        return False
    
    try:
        profile = user.profile
        return profile.has_role(role_code)
    except UserProfile.DoesNotExist:
        return False


def get_user_permissions(user):
    """
    获取用户的所有权限代码
    
    参数:
        user: User对象
    
    返回:
        list: 权限代码列表
    """
    if not user.is_authenticated:
        return []
    
    try:
        profile = user.profile
        return profile.get_permissions()
    except UserProfile.DoesNotExist:
        return []


def get_user_roles(user):
    """
    获取用户的所有有效角色
    
    参数:
        user: User对象
    
    返回:
        QuerySet: 用户角色查询集
    """
    if not user.is_authenticated:
        return []
    
    try:
        profile = user.profile
        return profile.get_valid_roles()
    except UserProfile.DoesNotExist:
        return []


