"""
认证相关的数据验证模式
用于 auth.py API
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from django.contrib.auth.models import User


class UserLoginSchema(BaseModel):
    """用户登录验证模式"""
    username: str
    password: str

    @validator('username')
    def username_must_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()

    @validator('password')
    def password_must_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('密码不能为空')
        return v


class UserRegisterSchema(BaseModel):
    """用户注册验证模式"""
    username: str
    email: EmailStr
    password1: str
    password2: str
    captcha: Optional[str] = None  # 验证码
    captcha_key: Optional[str] = None  # 验证码键
    nickname: Optional[str] = None  # 昵称（可选，留空自动生成）
    gender: Optional[str] = None  # 性别（可选）
    birth_date: Optional[str] = None  # 出生日期（可选，格式：YYYY-MM-DD）
    phone: Optional[str] = None  # 电话号码（可选）

    @validator('username')
    def username_must_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()

    @validator('password1', 'password2')
    def passwords_must_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('密码不能为空')
        return v

    @validator('password2')
    def passwords_match(cls, v, values):
        if 'password1' in values and v != values['password1']:
            raise ValueError('两次输入的密码不一致')
        return v

    @validator('password1')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度不能少于8个字符')
        return v

    @validator('username')
    def username_not_exists(cls, v):
        if User.objects.filter(username=v).exists():
            raise ValueError('用户名已存在')
        return v

    @validator('email')
    def email_not_exists(cls, v):
        if User.objects.filter(email=v).exists():
            raise ValueError('邮箱已被注册')
        return v

    @validator('nickname')
    def nickname_allow_empty(cls, v):
        # 允许空字符串，表示自动生成
        if v is not None and isinstance(v, str):
            return v.strip() if v.strip() else None
        return v

    @validator('gender')
    def gender_choices(cls, v):
        if v and v not in ['male', 'female', 'other', 'prefer_not_to_say']:
            raise ValueError('性别选项无效')
        return v

    @validator('birth_date')
    def birth_date_format(cls, v):
        if v:
            from datetime import datetime
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('出生日期格式不正确，请使用 YYYY-MM-DD 格式')
        return v

    @validator('phone')
    def phone_format(cls, v):
        if v and isinstance(v, str):
            return v.strip() if v.strip() else None
        return v
