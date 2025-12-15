"""
认证相关的业务流程编排
每个 Flow < 300 行，包含权限检查和业务流程编排
"""
from django.contrib.auth import login, logout
from datetime import datetime

from app.user.actions.auth_actions import (
    authenticate_user,
    check_user_exists_by_username,
    check_user_exists_by_email,
    create_user,
    update_login_count,
    create_user_activity,
    update_profile_nickname,
    update_profile_gender,
    update_profile_birth_date,
    update_profile_phone
)
from app.utils.log_utils import log_auth_action
from app.log.model import Log


class LoginResult:
    """登录结果"""
    def __init__(self, success: bool, message: str, user=None, data=None):
        self.success = success
        self.message = message
        self.user = user
        self.data = data


def login_user_flow(request, username: str, password: str) -> LoginResult:
    """
    用户登录流程
    不需要权限检查（登录前无用户身份）
    """
    # 认证用户
    user = authenticate_user(username, password)

    if user is None:
        log_auth_action(
            action="用户登录",
            message=f"用户 {username} 登录失败：用户名或密码错误",
            level=Log.LEVEL.WARNING,
            request=request,
            extra_data={"username": username, "reason": "用户名或密码错误"}
        )
        return LoginResult(
            success=False,
            message="用户名或密码错误"
        )

    # 检查账户是否被禁用
    if not user.is_active:
        log_auth_action(
            action="用户登录",
            message=f"用户 {username} 登录失败：账户已被禁用",
            level=Log.LEVEL.WARNING,
            user=user,
            request=request,
            extra_data={"username": username, "reason": "账户已禁用"}
        )
        return LoginResult(
            success=False,
            message="用户账户已被禁用"
        )

    # 执行登录
    login(request, user)

    # 更新登录次数
    if hasattr(user, 'profile') and user.profile:
        try:
            update_login_count(user.profile)
        except Exception:
            pass

    # 记录登录活动
    try:
        create_user_activity(
            user=user,
            activity_type='login',
            description=f'用户 {user.username} 登录成功',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    except Exception:
        pass

    # 记录登录成功日志
    log_auth_action(
        action="用户登录",
        message=f"用户 {user.username} 登录成功",
        user=user,
        request=request,
        extra_data={"username": username}
    )

    # 构建返回数据
    profile_data = {}
    if hasattr(user, 'profile') and user.profile:
        profile_data = {
            'phone': user.profile.phone,
            'nickname': user.profile.nickname,
            'gender': user.profile.gender,
            'birth_date': user.profile.birth_date.strftime('%Y-%m-%d') if user.profile.birth_date else None,
            'status': user.profile.status,
            'login_count': user.profile.login_count,
        }

    return LoginResult(
        success=True,
        message="登录成功",
        user=user,
        data={
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
            'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            'profile': profile_data,
        }
    )


class RegisterResult:
    """注册结果"""
    def __init__(self, success: bool, message: str, user=None, data=None):
        self.success = success
        self.message = message
        self.user = user
        self.data = data


def register_user_flow(request, username: str, email: str, password: str,
                      nickname: str = None, gender: str = None,
                      birth_date: str = None, phone: str = None) -> RegisterResult:
    """
    用户注册流程
    不需要权限检查（注册前无用户身份）
    """
    # 检查用户名是否已存在
    if check_user_exists_by_username(username):
        log_auth_action(
            action="用户注册",
            message=f"用户 {username} 注册失败：用户名已存在",
            level=Log.LEVEL.WARNING,
            request=request,
            extra_data={"username": username, "email": email, "reason": "用户名已存在"}
        )
        return RegisterResult(
            success=False,
            message="用户名已存在"
        )

    # 检查邮箱是否已存在
    if check_user_exists_by_email(email):
        log_auth_action(
            action="用户注册",
            message=f"用户 {username} 注册失败：邮箱已被注册",
            level=Log.LEVEL.WARNING,
            request=request,
            extra_data={"username": username, "email": email, "reason": "邮箱已被注册"}
        )
        return RegisterResult(
            success=False,
            message="邮箱已被注册"
        )

    # 创建用户（UserProfile会通过信号处理器自动创建）
    user = create_user(username, email, password)

    # 刷新用户对象以确保 profile 已创建
    user.refresh_from_db()

    # 更新用户资料
    if nickname or gender or birth_date or phone:
        profile = user.profile if hasattr(user, 'profile') else None
        if profile:
            if nickname:
                update_profile_nickname(profile, nickname)
            if gender:
                update_profile_gender(profile, gender)
            if birth_date:
                birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d').date()
                update_profile_birth_date(profile, birth_date_obj)
            if phone:
                update_profile_phone(profile, phone)

    # 记录注册活动
    try:
        create_user_activity(
            user=user,
            activity_type='register',
            description=f'用户 {user.username} 注册成功',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    except Exception:
        pass

    # 记录注册成功日志
    log_auth_action(
        action="用户注册",
        message=f"用户 {user.username} 注册成功",
        user=user,
        request=request,
        extra_data={"username": user.username, "email": user.email}
    )

    return RegisterResult(
        success=True,
        message="注册成功",
        user=user,
        data={
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            'profile': {
                'nickname': user.profile.nickname if hasattr(user, 'profile') else None,
            },
        }
    )


class LogoutResult:
    """登出结果"""
    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message


def logout_user_flow(request) -> LogoutResult:
    """
    用户登出流程
    权限检查：必须已登录
    """
    # 权限检查：必须已登录
    if not request.user.is_authenticated:
        log_auth_action(
            action="用户登出",
            message="用户登出失败：用户未登录",
            level=Log.LEVEL.WARNING,
            request=request
        )
        return LogoutResult(
            success=False,
            message="用户未登录"
        )

    # 记录登出活动
    try:
        create_user_activity(
            user=request.user,
            activity_type='logout',
            description=f'用户 {request.user.username} 登出',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    except Exception:
        pass

    # 记录登出成功日志
    log_auth_action(
        action="用户登出",
        message=f"用户 {request.user.username} 登出成功",
        user=request.user,
        request=request
    )

    # 执行登出
    try:
        if hasattr(request, 'session'):
            logout(request)
    except Exception:
        pass

    return LogoutResult(
        success=True,
        message="登出成功"
    )
