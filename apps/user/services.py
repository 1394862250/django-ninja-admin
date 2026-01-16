"""用户模块服务层：认证、个人中心、管理写操作与权限校验。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from captcha.models import CaptchaStore
from django.contrib.auth import get_user_model, login, logout
from faker import Faker

from apps.core.api.exceptions import BusinessException, NotFoundException, ValidationException
from apps.core.api.permissions import ensure_authenticated, ensure_staff_or_superuser, ensure_superuser
from apps.core.utils.serializers import to_iso
from apps.log.model import Log
from apps.log.services import log_admin_action, log_auth_action, log_user_action
from .model import Role, UserActivity, UserProfile, UserRole
from .selectors import (
    authenticate_user,
    check_user_exists_by_email,
    check_user_exists_by_username,
    filter_users,
    get_admin_dashboard_metrics,
    get_dashboard_chart_series,
    get_dashboard_plotly_data,
    get_user_activities,
    get_user_by_id,
    get_user_with_profile,
    is_nickname_taken,
    paginate_queryset,
    serialize_user,
    verify_password,
)

User = get_user_model()
faker = Faker("zh_CN")


# ====== 认证 ======
def login_user(request, username: str, password: str) -> Dict[str, Any]:
    user = authenticate_user(username, password)
    if user is None:
        log_auth_action(
            action="用户登录",
            message=f"用户 {username} 登录失败：用户名或密码错误",
            level=Log.LEVEL.WARNING,
            request=request,
            extra_data={"username": username, "reason": "用户名或密码错误"},
        )
        raise ValidationException("用户名或密码错误")

    if not user.is_active:
        log_auth_action(
            action="用户登录",
            message=f"用户 {username} 登录失败：账户已被禁用",
            level=Log.LEVEL.WARNING,
            user=user,
            request=request,
            extra_data={"username": username, "reason": "账户已禁用"},
        )
        raise PermissionException("用户账户已被禁用")

    login(request, user)

    profile = getattr(user, "profile", None)
    if profile:
        profile.update_login_stats()

    UserActivity.objects.create(
        user=user,
        activity_type="login",
        description=f"用户 {user.username} 登录成功",
        ip_address=request.META.get("REMOTE_ADDR", ""),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )

    log_auth_action(
        action="用户登录",
        message=f"用户 {user.username} 登录成功",
        user=user,
        request=request,
        extra_data={"username": username},
    )

    return serialize_user(user)


def register_user(
    request,
    *,
    username: str,
    email: str,
    password: str,
    nickname: Optional[str] = None,
    gender: Optional[str] = None,
    birth_date: Optional[str] = None,
    phone: Optional[str] = None,
) -> Dict[str, Any]:
    if check_user_exists_by_username(username):
        raise ValidationException("用户名已存在")
    if check_user_exists_by_email(email):
        raise ValidationException("邮箱已被注册")

    user = User.objects.create_user(username=username, email=email, password=password)

    profile = getattr(user, "profile", None)
    if profile:
        if nickname:
            profile.nickname = nickname
        if gender:
            profile.gender = gender
        if birth_date:
            try:
                birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
                profile.birth_date = birth_date_obj
            except ValueError:
                raise ValidationException("出生日期格式不正确，请使用 YYYY-MM-DD 格式")
        if phone:
            profile.phone = phone
        profile.save()

    UserActivity.objects.create(
        user=user,
        activity_type="register",
        description=f"用户 {user.username} 注册成功",
        ip_address=request.META.get("REMOTE_ADDR", ""),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )

    log_auth_action(
        action="用户注册",
        message=f"用户 {user.username} 注册成功",
        user=user,
        request=request,
        extra_data={"username": user.username, "email": user.email},
    )

    return serialize_user(user)


def logout_user(request):
    ensure_authenticated(request.user)

    UserActivity.objects.create(
        user=request.user,
        activity_type="logout",
        description=f"用户 {request.user.username} 登出",
        ip_address=request.META.get("REMOTE_ADDR", ""),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )

    log_auth_action(
        action="用户登出",
        message=f"用户 {request.user.username} 登出成功",
        user=request.user,
        request=request,
    )

    if hasattr(request, "session"):
        logout(request)


# ====== 个人中心 ======
def get_profile(user) -> Dict[str, Any]:
    ensure_authenticated(user)
    return serialize_user(user)


def change_password(
    request,
    *,
    user,
    old_password: str,
    new_password: str,
    captcha: Optional[str] = None,
    captcha_key: Optional[str] = None,
):
    ensure_authenticated(user)

    if captcha or captcha_key:
        if not (captcha and captcha_key):
            raise ValidationException("请提供完整的验证码信息")
        try:
            captcha_store = CaptchaStore.objects.get(hashkey=captcha_key, response=captcha)
            captcha_store.delete()
        except CaptchaStore.DoesNotExist:
            log_user_action(
                action="修改密码",
                message=f"用户 {user.username} 修改密码失败：验证码错误或已过期",
                level=Log.LEVEL.WARNING,
                user=user,
                request=request,
                extra_data={"reason": "验证码错误或已过期"},
            )
            raise ValidationException("验证码错误或已过期")

    if not verify_password(user, old_password):
        log_user_action(
            action="修改密码",
            message=f"用户 {user.username} 修改密码失败：原密码错误",
            level=Log.LEVEL.WARNING,
            user=user,
            request=request,
            extra_data={"reason": "原密码错误"},
        )
        raise ValidationException("原密码错误")

    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])

    UserActivity.objects.create(
        user=user,
        activity_type="password_change",
        description=f"用户 {user.username} 修改了密码",
        ip_address=request.META.get("REMOTE_ADDR", ""),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )

    log_user_action(
        action="修改密码",
        message=f"用户 {user.username} 修改密码成功",
        user=user,
        request=request,
    )


def upload_avatar(user, avatar_file):
    ensure_authenticated(user)

    if not avatar_file.content_type.startswith("image/"):
        raise ValidationException("只能上传图片文件")
    if avatar_file.size > 5 * 1024 * 1024:
        raise ValidationException("文件大小不能超过5MB")

    profile = getattr(user, "profile", None)
    if profile:
        profile.avatar = avatar_file
        profile.save(update_fields=["avatar", "updated_at"])

    log_user_action(
        action="上传头像",
        message=f"用户 {user.username} 上传头像成功",
        user=user,
        request=None,
    )

    return profile.avatar.url if profile and profile.avatar else None


def update_profile(user, *, nickname: Optional[str], gender: Optional[str], birth_date=None, phone: Optional[str]):
    ensure_authenticated(user)

    profile = getattr(user, "profile", None)
    if not profile:
        raise NotFoundException("用户资料不存在")

    if nickname:
        if is_nickname_taken(nickname.strip(), exclude_user_id=user.id):
            raise ValidationException("昵称已被其他用户使用，请选择其他昵称")
        profile.nickname = nickname.strip()

    if gender:
        profile.gender = gender
    if birth_date:
        profile.birth_date = birth_date
    if phone:
        profile.phone = phone

    profile.save()

    log_user_action(
        action="更新资料",
        message=f"用户 {user.username} 更新资料成功",
        user=user,
        request=None,
    )


def list_user_activities(user, page: int = 1, page_size: int = 10, activity_type: Optional[str] = None) -> Dict[str, Any]:
    ensure_authenticated(user)

    activities_qs = get_user_activities(user, activity_type=activity_type)
    page_objects, total_count, total_pages = paginate_queryset(activities_qs, page, page_size)

    activities_data = []
    for activity in page_objects:
        activities_data.append(
            {
                "id": activity.id,
                "activity_type": activity.get_activity_type_display(),
                "description": activity.description,
                "ip_address": activity.ip_address,
                "created_at": to_iso(activity.created_at),
            }
        )

    return {
        "activities": activities_data,
        "page": page,
        "page_size": page_size,
        "total": total_count,
        "total_pages": total_pages,
    }


# ====== 管理 ======
def list_users(user, page: int = 1, page_size: int = 10, search: Optional[str] = None) -> Dict[str, Any]:
    ensure_staff_or_superuser(user)

    queryset = filter_users(search)
    page_objects, total_count, total_pages = paginate_queryset(queryset, page, page_size)

    users_data = []
    for item in page_objects:
        profile = getattr(item, "profile", None)
        users_data.append(
            {
                "id": item.id,
                "username": item.username,
                "email": item.email,
                "is_active": item.is_active,
                "is_staff": item.is_staff,
                "date_joined": to_iso(getattr(item, "date_joined", None)),
                "nickname": getattr(profile, "nickname", None),
                "login_count": getattr(profile, "login_count", 0),
            }
        )

    return {
        "users": users_data,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def create_user_admin(
    user,
    *,
    username: str,
    email: str,
    password: str,
    is_staff: bool = False,
    is_active: bool = True,
    nickname: Optional[str] = None,
) -> Dict[str, Any]:
    ensure_staff_or_superuser(user)

    if check_user_exists_by_username(username):
        raise ValidationException("用户名已存在")
    if check_user_exists_by_email(email):
        raise ValidationException("邮箱已被使用")

    new_user = User.objects.create_user(username=username, email=email, password=password)
    new_user.is_staff = is_staff
    new_user.is_active = is_active
    new_user.save(update_fields=["is_staff", "is_active", "updated_at"])

    profile = getattr(new_user, "profile", None)
    if profile and nickname:
        profile.nickname = nickname
        profile.save(update_fields=["nickname", "updated_at"])

    log_admin_action(
        action="创建用户",
        message=f"管理员 {user.username} 创建用户 {username}",
        user=user,
        request=None,
        extra_data={"new_user_id": new_user.id, "username": username},
    )

    return {"user_id": new_user.id, "username": new_user.username}


def toggle_user_status(user, target_user_id: UUID) -> Dict[str, Any]:
    ensure_staff_or_superuser(user)

    if str(user.id) == str(target_user_id):
        raise BusinessException("不能禁用自己的账户")

    target = get_user_by_id(target_user_id)
    if not target:
        raise NotFoundException("用户不存在")

    target.is_active = not target.is_active
    target.save(update_fields=["is_active", "updated_at"])

    log_admin_action(
        action="切换用户状态",
        message=f"管理员 {user.username} 将用户 {target.username} 状态设置为 {'激活' if target.is_active else '禁用'}",
        user=user,
        request=None,
        extra_data={"target_user_id": str(target_user_id), "new_status": target.is_active},
    )

    return {"is_active": target.is_active}


def get_user_detail(user, target_user_id: UUID) -> Dict[str, Any]:
    ensure_staff_or_superuser(user)

    target = get_user_with_profile(target_user_id)
    if not target:
        raise NotFoundException("用户不存在")
    return serialize_user(target)


def update_user_admin(user, target_user_id: UUID, *, email: Optional[str] = None, is_staff: Optional[bool] = None):
    ensure_staff_or_superuser(user)

    target = get_user_by_id(target_user_id)
    if not target:
        raise NotFoundException("用户不存在")

    if email:
        target.email = email
    if is_staff is not None:
        target.is_staff = is_staff
    target.save()


def get_dashboard_data(user) -> Dict[str, Any]:
    ensure_staff_or_superuser(user)
    return get_admin_dashboard_metrics()


def get_dashboard_chart_data(user, days: int = 30) -> Dict[str, Any]:
    ensure_staff_or_superuser(user)
    return get_dashboard_plotly_data(days=days)


def delete_user_admin(user, target_user_id: UUID):
    ensure_superuser(user)

    if str(user.id) == str(target_user_id):
        raise BusinessException("不能删除自己的账户")

    target = get_user_by_id(target_user_id)
    if not target:
        raise NotFoundException("用户不存在")

    username = target.username
    target.soft_delete()

    log_admin_action(
        action="删除用户",
        message=f"管理员 {user.username} 删除用户 {username}",
        user=user,
        request=None,
        extra_data={"deleted_user_id": str(target_user_id), "username": username},
    )


# ====== 数据工厂 ======
def _generate_unique_username(faker_obj) -> str:
    for _ in range(5):
        candidate = faker_obj.user_name()
        if not check_user_exists_by_username(candidate):
            return candidate
    return f"user_{uuid4().hex[:8]}"


def _generate_unique_email(faker_obj) -> str:
    for _ in range(5):
        candidate = faker_obj.email()
        if not check_user_exists_by_email(candidate):
            return candidate
    return f"user_{uuid4().hex[:8]}@example.com"


def seed_users_service(
    operator,
    *,
    count: int,
    default_password: str = "123456",
    role_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """批量生成测试用户（仅超级管理员）。"""
    ensure_superuser(operator)

    if count < 1 or count > 50:
        raise ValidationException("单次生成数量需在 1~50 之间")
    if not default_password or not default_password.strip():
        raise ValidationException("默认密码不能为空")

    target_role = None
    if role_id:
        target_role = Role.objects.filter(id=role_id, is_deleted=False, is_active=True).first()
        if not target_role:
            raise NotFoundException("角色不存在或已禁用")

    created_users = []
    for _ in range(count):
        username = _generate_unique_username(faker)
        email = _generate_unique_email(faker)

        new_user = User.objects.create_user(username=username, email=email, password=default_password)
        new_user.is_active = True
        new_user.save(update_fields=["is_active", "updated_at"])

        profile = getattr(new_user, "profile", None)
        if profile:
            profile.nickname = profile.nickname or faker.name()
            profile.phone = profile.phone or faker.phone_number()
            profile.save(update_fields=["nickname", "phone", "updated_at"])

        if target_role:
            UserRole.objects.get_or_create(user=new_user, role=target_role, defaults={"is_active": True})

        created_users.append(
            {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "role": target_role.name if target_role else None,
            }
        )

    log_admin_action(
        action="批量生成用户",
        message=f"管理员 {operator.username} 批量生成用户：{len(created_users)} 个",
        user=operator,
        request=None,
        extra_data={
            "count": len(created_users),
            "role": getattr(target_role, "code", None),
        },
    )

    return {
        "created": len(created_users),
        "role_assigned": getattr(target_role, "name", None),
        "default_password": default_password,
        "users": created_users,
    }


__all__ = [
    "login_user",
    "register_user",
    "logout_user",
    "get_profile",
    "change_password",
    "upload_avatar",
    "update_profile",
    "list_user_activities",
    "list_users",
    "create_user_admin",
    "toggle_user_status",
    "get_user_detail",
    "update_user_admin",
    "get_dashboard_data",
    "get_dashboard_chart_data",
    "delete_user_admin",
    "seed_users_service",
]
