"""
管理相关的数据验证模式
用于 admin.py API
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, validator


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
