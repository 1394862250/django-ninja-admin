"""
用户相关的原子操作
所有 Action 必须 < 30 行，单一职责，无流程控制
"""
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from app.user.models import UserProfile, UserActivity


def get_user_by_id(user_id: int) -> User | None:
    """根据ID获取用户"""
    return User.objects.filter(id=user_id).first()


def verify_password(user: User, password: str) -> bool:
    """验证密码"""
    return check_password(password, user.password)


def change_user_password(user: User, new_password: str):
    """修改用户密码"""
    user.set_password(new_password)
    user.save(update_fields=['password'])


def update_user_avatar(user: User, avatar_file):
    """更新用户头像"""
    if hasattr(user, 'profile') and user.profile:
        user.profile.avatar = avatar_file
        user.profile.save(update_fields=['avatar'])


def get_user_activities(user: User, limit: int = 10):
    """获取用户活动记录"""
    return UserActivity.objects.filter(user=user).order_by('-created')[:limit]


def create_password_change_activity(user: User, ip_address: str, user_agent: str):
    """创建密码修改活动记录"""
    UserActivity.objects.create(
        user=user,
        activity_type='password_change',
        description=f'用户 {user.username} 修改了密码',
        ip_address=ip_address,
        user_agent=user_agent
    )


def toggle_user_active_status(user: User) -> bool:
    """切换用户激活状态"""
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    return user.is_active


def update_user_basic_info(user: User, email: str = None, is_staff: bool = None):
    """更新用户基本信息"""
    if email:
        user.email = email
    if is_staff is not None:
        user.is_staff = is_staff
    user.save()
