"""
用户相关的数据验证模式
"""
from typing import Any, Optional, List, Dict
from pydantic import BaseModel, EmailStr, validator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from captcha.fields import CaptchaField
from captcha.models import CaptchaStore


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


class AdminCreateUserSchema(BaseModel):
    """管理员创建用户验证模式"""
    username: str
    email: EmailStr  # 使用EmailStr类型进行验证
    password: str
    nickname: Optional[str] = None
    is_active: Optional[bool] = True
    is_staff: Optional[bool] = False
    
    @validator('username')
    def username_must_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()
    
    @validator('password')
    def password_strength(cls, v):
        if not v or len(v) < 8:
            raise ValueError('密码长度不能少于8个字符')
        return v
    
    @validator('nickname')
    def nickname_allow_empty(cls, v):
        # 允许空字符串，表示自动生成
        if v is not None and isinstance(v, str):
            return v.strip() if v.strip() else None
        return v


class UserUpdateSchema(BaseModel):
    """用户更新验证模式"""
    username: Optional[str] = None
    email: Optional[str] = None  # 改为 str，在 API 中验证邮箱格式
    nickname: Optional[str] = None
    is_active: Optional[bool] = None
    is_staff: Optional[bool] = None
    password: Optional[str] = None
    captcha: Optional[str] = None  # 验证码
    captcha_key: Optional[str] = None  # 验证码键
    
    @validator('password')
    def password_strength(cls, v):
        if v and len(v) < 8:
            raise ValueError('密码长度不能少于8个字符')
        return v
    
    @validator('nickname')
    def nickname_allow_empty(cls, v):
        # 允许空字符串，表示自动生成
        if v is not None and isinstance(v, str):
            return v.strip() if v.strip() else None
        return v


class ChangePasswordSchema(BaseModel):
    """修改密码验证模式"""
    old_password: str
    new_password1: str
    new_password2: str
    captcha: Optional[str] = None  # 验证码
    captcha_key: Optional[str] = None  # 验证码键
    
    @validator('old_password')
    def old_password_must_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('当前密码不能为空')
        return v
    
    @validator('new_password1', 'new_password2')
    def passwords_must_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('新密码不能为空')
        return v
    
    @validator('new_password2')
    def passwords_match(cls, v, values):
        if 'new_password1' in values and v != values['new_password1']:
            raise ValueError('两次输入的新密码不一致')
        return v
    
    @validator('new_password1')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('新密码长度不能少于8个字符')
        return v


class UserProfileUpdateSchema(BaseModel):
    """用户个人资料更新验证模式"""
    phone: Optional[str] = None
    nickname: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None  # 保持字符串格式，由validator转换为date对象
    
    @validator('phone')
    def phone_format(cls, v):
        if v and isinstance(v, str):
            return v.strip() if v.strip() else None
        return v
    
    @validator('nickname')
    def nickname_allow_empty(cls, v):
        # 允许空字符串，表示不更新或自动生成
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
            from datetime import datetime, date
            if isinstance(v, str):
                try:
                    parsed_date = datetime.strptime(v, '%Y-%m-%d').date()
                    # 确保是date对象而不是datetime
                    return parsed_date
                except ValueError:
                    raise ValueError('出生日期格式不正确，请使用 YYYY-MM-DD 格式')
            elif isinstance(v, date):
                return v
            else:
                raise ValueError('出生日期格式不正确，请使用 YYYY-MM-DD 格式')
        return None


class CaptchaRequestSchema(BaseModel):
    """验证码请求模式"""
    pass


class CaptchaVerifySchema(BaseModel):
    """验证码验证模式"""
    captcha: str
    captcha_key: str
    
    @validator('captcha')
    def captcha_must_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('验证码不能为空')
        return v.strip()
    
    @validator('captcha_key')
    def captcha_key_must_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('验证码键不能为空')
        return v.strip()
