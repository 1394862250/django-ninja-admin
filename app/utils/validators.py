"""
数据验证器
"""
from typing import Any, Optional
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


class UserUpdateSchema(BaseModel):
    """用户更新验证模式"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_staff: Optional[bool] = None
    password: Optional[str] = None
    captcha: Optional[str] = None  # 验证码
    captcha_key: Optional[str] = None  # 验证码键
    
    @validator('username')
    def username_not_exists(cls, v, values):
        if v and User.objects.filter(username=v).exclude(id=values.get('id')).exists():
            raise ValueError('用户名已存在')
        return v
    
    @validator('email')
    def email_not_exists(cls, v, values):
        if v and User.objects.filter(email=v).exclude(id=values.get('id')).exists():
            raise ValueError('邮箱已被注册')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        if v and len(v) < 8:
            raise ValueError('密码长度不能少于8个字符')
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