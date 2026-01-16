"""
系统级数据验证工具函数。
仅包含数据格式验证，不包含权限判断。
"""
import re
from django.core.exceptions import ValidationError


def validate_username(username):
    """验证用户名格式"""
    if not username:
        raise ValidationError("用户名不能为空")
    if len(username) < 3:
        raise ValidationError("用户名长度不能少于3个字符")
    if len(username) > 20:
        raise ValidationError("用户名长度不能超过20个字符")
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        raise ValidationError("用户名只能包含字母、数字和下划线")
    return True


def validate_password_strength(password):
    """验证密码强度"""
    if not password:
        raise ValidationError("密码不能为空")
    if len(password) < 8:
        raise ValidationError("密码长度不能少于8个字符")
    if not re.search(r"\d", password):
        raise ValidationError("密码必须包含至少一个数字")
    if not re.search(r"[a-zA-Z]", password):
        raise ValidationError("密码必须包含至少一个字母")
    return True


def validate_phone(phone):
    """验证手机号格式（可为空）"""
    if not phone:
        return True
    if not re.match(r"^1[3-9]\d{9}$", phone):
        raise ValidationError("请输入有效的手机号码")
    return True


def validate_email(email):
    """验证邮箱格式"""
    if not email:
        raise ValidationError("邮箱不能为空")
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise ValidationError("请输入有效的邮箱地址")
    return True


__all__ = [
    "validate_username",
    "validate_password_strength",
    "validate_phone",
    "validate_email",
]
