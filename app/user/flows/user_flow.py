"""
用户管理相关的业务流程编排
每个 Flow < 300 行，包含权限检查和业务流程编排
"""
from captcha.models import CaptchaStore

from app.user.actions.user_actions import (
    get_user_by_id,
    verify_password,
    change_user_password,
    update_user_avatar,
    get_user_activities,
    create_password_change_activity,
    update_user_basic_info
)
from app.user.actions.auth_actions import (
    update_profile_nickname,
    update_profile_gender,
    update_profile_birth_date,
    update_profile_phone
)
from app.user.actions.captcha_actions import delete_captcha
from app.utils.log_utils import log_user_action
from app.log.model import Log


class ChangePasswordResult:
    """修改密码结果"""
    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message


def change_password_flow(request, old_password: str, new_password: str,
                        captcha: str = None, captcha_key: str = None) -> ChangePasswordResult:
    """
    修改密码流程
    权限检查：必须是当前登录用户
    """
    # 权限检查：必须已登录
    if not request.user.is_authenticated:
        return ChangePasswordResult(
            success=False,
            message="需要登录访问"
        )

    user = request.user

    # 验证验证码（如果提供了验证码）
    if captcha and captcha_key:
        try:
            captcha_store = CaptchaStore.objects.get(
                hashkey=captcha_key,
                response=captcha
            )
            delete_captcha(captcha_store)
        except CaptchaStore.DoesNotExist:
            log_user_action(
                action="修改密码",
                message=f"用户 {user.username} 修改密码失败：验证码错误或已过期",
                level=Log.LEVEL.WARNING,
                user=user,
                request=request,
                extra_data={"reason": "验证码错误或已过期"}
            )
            return ChangePasswordResult(
                success=False,
                message="验证码错误或已过期"
            )
    elif captcha or captcha_key:
        log_user_action(
            action="修改密码",
            message=f"用户 {user.username} 修改密码失败：请提供完整的验证码信息",
            level=Log.LEVEL.WARNING,
            user=user,
            request=request,
            extra_data={"reason": "验证码信息不完整"}
        )
        return ChangePasswordResult(
            success=False,
            message="请提供完整的验证码信息"
        )

    # 验证旧密码
    if not verify_password(user, old_password):
        log_user_action(
            action="修改密码",
            message=f"用户 {user.username} 修改密码失败：原密码错误",
            level=Log.LEVEL.WARNING,
            user=user,
            request=request,
            extra_data={"reason": "原密码错误"}
        )
        return ChangePasswordResult(
            success=False,
            message="原密码错误"
        )

    # 修改密码
    change_user_password(user, new_password)

    # 记录密码修改活动
    try:
        create_password_change_activity(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    except Exception:
        pass

    # 记录成功日志
    log_user_action(
        action="修改密码",
        message=f"用户 {user.username} 修改密码成功",
        user=user,
        request=request
    )

    return ChangePasswordResult(
        success=True,
        message="密码修改成功"
    )


class UploadAvatarResult:
    """上传头像结果"""
    def __init__(self, success: bool, message: str, avatar_url: str = None):
        self.success = success
        self.message = message
        self.avatar_url = avatar_url


def upload_avatar_flow(request, avatar_file) -> UploadAvatarResult:
    """
    上传头像流程
    权限检查：必须是当前登录用户
    """
    # 权限检查：必须已登录
    if not request.user.is_authenticated:
        return UploadAvatarResult(
            success=False,
            message="需要登录访问"
        )

    user = request.user

    # 更新头像
    update_user_avatar(user, avatar_file)

    # 记录日志
    log_user_action(
        action="上传头像",
        message=f"用户 {user.username} 上传头像成功",
        user=user,
        request=request
    )

    avatar_url = user.profile.avatar.url if user.profile and user.profile.avatar else None

    return UploadAvatarResult(
        success=True,
        message="头像上传成功",
        avatar_url=avatar_url
    )


class UpdateProfileResult:
    """更新资料结果"""
    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message


def update_profile_flow(request, nickname: str = None, gender: str = None,
                       birth_date = None, phone: str = None) -> UpdateProfileResult:
    """
    更新个人资料流程
    权限检查：必须是当前登录用户
    """
    # 权限检查：必须已登录
    if not request.user.is_authenticated:
        return UpdateProfileResult(
            success=False,
            message="需要登录访问"
        )

    user = request.user

    # 检查昵称唯一性
    if nickname and nickname.strip():
        profile = user.profile if hasattr(user, 'profile') else None
        if profile:
            from app.user.models import UserProfile
            existing_profile = UserProfile.objects.filter(
                nickname=nickname.strip()
            ).exclude(pk=profile.pk).first()
            if existing_profile:
                log_user_action(
                    action="更新个人资料",
                    message=f"用户 {user.username} 更新个人资料失败：昵称已被其他用户使用",
                    level=Log.LEVEL.WARNING,
                    user=user,
                    request=request,
                    extra_data={"nickname": nickname.strip(), "reason": "昵称已被使用"}
                )
                return UpdateProfileResult(
                    success=False,
                    message="昵称已被其他用户使用，请选择其他昵称"
                )

    # 更新资料
    profile = user.profile if hasattr(user, 'profile') else None
    if profile:
        if nickname:
            update_profile_nickname(profile, nickname)
        if gender:
            update_profile_gender(profile, gender)
        if birth_date:
            update_profile_birth_date(profile, birth_date)
        if phone:
            update_profile_phone(profile, phone)

    # 记录日志
    log_user_action(
        action="更新资料",
        message=f"用户 {user.username} 更新资料成功",
        user=user,
        request=request
    )

    return UpdateProfileResult(
        success=True,
        message="资料更新成功"
    )


class GetActivitiesResult:
    """获取活动记录结果"""
    def __init__(self, success: bool, message: str, data: dict = None):
        self.success = success
        self.message = message
        self.data = data


def get_user_activities_flow(request, page: int = 1, page_size: int = 10,
                             activity_type: str = None) -> GetActivitiesResult:
    """
    获取用户活动记录流程
    权限检查：必须是当前登录用户
    """
    # 权限检查：必须已登录
    if not request.user.is_authenticated:
        return GetActivitiesResult(
            success=False,
            message="需要登录访问"
        )

    user = request.user

    # 获取活动记录
    from django.core.paginator import Paginator
    activities = get_user_activities(user, limit=1000)  # 获取足够多的记录用于分页

    # 按类型过滤
    if activity_type:
        activities = [a for a in activities if a.activity_type == activity_type]

    # 分页
    paginator = Paginator(activities, page_size)
    activities_page = paginator.get_page(page)

    # 转换为字典列表
    activities_data = []
    for activity in activities_page:
        activities_data.append({
            'id': activity.id,
            'activity_type': activity.get_activity_type_display(),
            'description': activity.description,
            'ip_address': activity.ip_address,
            'created_at': activity.created.strftime('%Y-%m-%d %H:%M:%S'),
        })

    return GetActivitiesResult(
        success=True,
        message="获取活动记录成功",
        data={
            'activities': activities_data,
            'page': page,
            'page_size': page_size,
            'total_count': paginator.count,
            'total_pages': paginator.num_pages
        }
    )

