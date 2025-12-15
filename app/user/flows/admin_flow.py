"""
管理后台相关的业务流程编排
每个 Flow < 300 行，包含权限检查和业务流程编排
"""
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict

from app.user.models import UserActivity, UserProfile
from app.user.actions.auth_actions import create_user
from app.user.actions.user_actions import (
    get_user_by_id,
    toggle_user_active_status,
    update_user_basic_info
)
from app.user.actions.admin_actions import update_user_staff_status, delete_user
from app.utils.log_utils import log_admin_action
from app.log.model import Log


def can_access_admin(user) -> bool:
    """检查用户是否有管理员权限"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


class AdminDashboardResult:
    """管理后台数据结果"""
    def __init__(self, success: bool, message: str, data=None):
        self.success = success
        self.message = message
        self.data = data


def get_admin_dashboard_flow(request) -> AdminDashboardResult:
    """
    获取管理后台首页数据流程
    权限检查：必须是 staff 或 superuser
    """
    # 权限检查：必须是管理员
    if not can_access_admin(request.user):
        return AdminDashboardResult(
            success=False,
            message="需要管理员权限"
        )

    User = get_user_model()
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    new_users_today = User.objects.filter(date_joined__date=timezone.now().date()).count()

    activities_today = UserActivity.objects.filter(created__date=timezone.now().date()).count()
    logins_today = UserActivity.objects.filter(
        activity_type='login',
        created__date=timezone.now().date()
    ).count()

    return AdminDashboardResult(
        success=True,
        message="获取管理数据成功",
        data={
            'total_users': total_users,
            'active_users': active_users,
            'staff_users': staff_users,
            'new_users_today': new_users_today,
            'activities_today': activities_today,
            'logins_today': logins_today,
            'regular_users': total_users - staff_users
        }
    )


class ListUsersResult:
    """用户列表结果"""
    def __init__(self, success: bool, message: str, data=None):
        self.success = success
        self.message = message
        self.data = data


def list_users_flow(request, page: int = 1, page_size: int = 10, search: str = None) -> ListUsersResult:
    """
    获取用户列表流程
    权限检查：必须是 staff 或 superuser
    """
    # 权限检查：必须是管理员
    if not can_access_admin(request.user):
        return ListUsersResult(
            success=False,
            message="需要管理员权限"
        )

    User = get_user_model()
    queryset = User.objects.all().select_related('profile')

    if search:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(profile__nickname__icontains=search)
        )

    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)

    users_data = []
    for user in page_obj:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            'nickname': user.profile.nickname if hasattr(user, 'profile') else None,
            'login_count': user.profile.login_count if hasattr(user, 'profile') else 0,
        })

    return ListUsersResult(
        success=True,
        message="获取用户列表成功",
        data={
            'users': users_data,
            'total': paginator.count,
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages
        }
    )


class CreateUserResult:
    """创建用户结果"""
    def __init__(self, success: bool, message: str, user=None):
        self.success = success
        self.message = message
        self.user = user


def create_user_flow(request, username: str, email: str, password: str,
                    is_staff: bool = False, is_active: bool = True) -> CreateUserResult:
    """
    创建用户流程（管理员）
    权限检查：必须是 staff 或 superuser
    """
    # 权限检查：必须是管理员
    if not can_access_admin(request.user):
        return CreateUserResult(
            success=False,
            message="需要管理员权限"
        )

    User = get_user_model()

    # 检查用户名是否已存在
    if User.objects.filter(username=username).exists():
        return CreateUserResult(
            success=False,
            message="用户名已存在"
        )

    # 检查邮箱是否已存在
    if User.objects.filter(email=email).exists():
        return CreateUserResult(
            success=False,
            message="邮箱已被使用"
        )

    # 创建用户
    user = create_user(username, email, password)

    # 更新用户状态
    update_user_staff_status(user, is_staff, is_active)

    # 记录日志
    log_admin_action(
        action="创建用户",
        message=f"管理员 {request.user.username} 创建用户 {username}",
        user=request.user,
        request=request,
        extra_data={"new_user_id": user.id, "username": username}
    )

    return CreateUserResult(
        success=True,
        message="用户创建成功",
        user=user
    )


class ToggleUserStatusResult:
    """切换用户状态结果"""
    def __init__(self, success: bool, message: str, is_active: bool = None):
        self.success = success
        self.message = message
        self.is_active = is_active


def toggle_user_status_flow(request, user_id: int) -> ToggleUserStatusResult:
    """
    切换用户激活状态流程
    权限检查：必须是 staff 或 superuser，且不能禁用自己
    """
    # 权限检查：必须是管理员
    if not can_access_admin(request.user):
        return ToggleUserStatusResult(
            success=False,
            message="需要管理员权限"
        )

    # 权限检查：不能禁用自己
    if request.user.id == user_id:
        return ToggleUserStatusResult(
            success=False,
            message="不能禁用自己的账户"
        )

    user = get_user_by_id(user_id)
    if not user:
        return ToggleUserStatusResult(
            success=False,
            message="用户不存在"
        )

    # 切换状态
    is_active = toggle_user_active_status(user)

    # 记录日志
    log_admin_action(
        action="切换用户状态",
        message=f"管理员 {request.user.username} 将用户 {user.username} 状态设置为 {'激活' if is_active else '禁用'}",
        user=request.user,
        request=request,
        extra_data={"target_user_id": user_id, "new_status": is_active}
    )

    return ToggleUserStatusResult(
        success=True,
        message=f"用户已{'激活' if is_active else '禁用'}",
        is_active=is_active
    )


class DeleteUserResult:
    """删除用户结果"""
    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message


def delete_user_flow(request, user_id: int) -> DeleteUserResult:
    """
    删除用户流程
    权限检查：必须是 superuser，且不能删除自己
    """
    # 权限检查：必须是超级管理员
    if not request.user.is_superuser:
        return DeleteUserResult(
            success=False,
            message="需要超级管理员权限"
        )

    # 权限检查：不能删除自己
    if request.user.id == user_id:
        return DeleteUserResult(
            success=False,
            message="不能删除自己的账户"
        )

    user = get_user_by_id(user_id)
    if not user:
        return DeleteUserResult(
            success=False,
            message="用户不存在"
        )

    username = user.username

    # 删除用户（调用 Action）
    delete_user(user)

    # 记录日志
    log_admin_action(
        action="删除用户",
        message=f"管理员 {request.user.username} 删除用户 {username}",
        user=request.user,
        request=request,
        extra_data={"deleted_user_id": user_id, "username": username}
    )

    return DeleteUserResult(
        success=True,
        message="用户已删除"
    )
