"""
认证相关的原子操作
所有 Action 必须 < 30 行，单一职责，无流程控制
"""
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import User
from app.user.models import UserProfile, UserActivity


def authenticate_user(username: str, password: str) -> User | None:
    """认证用户"""
    user = authenticate(username=username, password=password)
    return user


def check_user_exists_by_username(username: str) -> bool:
    """检查用户名是否已存在"""
    User = get_user_model()
    return User.objects.filter(username=username).exists()


def check_user_exists_by_email(email: str) -> bool:
    """检查邮箱是否已存在"""
    User = get_user_model()
    return User.objects.filter(email=email).exists()


def create_user(username: str, email: str, password: str) -> User:
    """创建用户"""
    User = get_user_model()
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    return user


def update_login_count(profile: UserProfile):
    """更新登录次数"""
    profile.login_count += 1
    profile.save(update_fields=['login_count'])


def create_user_activity(user: User, activity_type: str, description: str, ip_address: str, user_agent: str):
    """创建用户活动记录"""
    UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent
    )


def update_profile_nickname(profile: UserProfile, nickname: str):
    """更新用户昵称"""
    profile.nickname = nickname
    profile.save(update_fields=['nickname'])


def update_profile_gender(profile: UserProfile, gender: str):
    """更新用户性别"""
    profile.gender = gender
    profile.save(update_fields=['gender'])


def update_profile_birth_date(profile: UserProfile, birth_date):
    """更新用户生日"""
    profile.birth_date = birth_date
    profile.save(update_fields=['birth_date'])


def update_profile_phone(profile: UserProfile, phone: str):
    """更新用户手机号"""
    profile.phone = phone
    profile.save(update_fields=['phone'])

