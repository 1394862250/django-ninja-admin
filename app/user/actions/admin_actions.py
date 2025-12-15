"""
管理员相关的原子操作
所有 Action 必须 < 30 行，单一职责，无流程控制
"""
from django.contrib.auth.models import User


def update_user_staff_status(user: User, is_staff: bool, is_active: bool):
    """更新用户的 staff 和 active 状态"""
    user.is_staff = is_staff
    user.is_active = is_active
    user.save(update_fields=['is_staff', 'is_active'])


def delete_user(user: User):
    """删除用户"""
    user.delete()
