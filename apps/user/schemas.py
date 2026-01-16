"""用户模块 Schemas（认证/个人/管理/验证码）。"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


# ==== 认证 ====
class UserLoginSchema(BaseModel):
    username: str
    password: str

    @validator("username", "password")
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("字段不能为空")
        return v.strip()


class UserRegisterSchema(BaseModel):
    username: str
    email: EmailStr
    password1: str
    password2: str
    captcha: Optional[str] = None
    captcha_key: Optional[str] = None
    nickname: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    phone: Optional[str] = None

    @validator("username", "password1", "password2")
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("字段不能为空")
        return v.strip()

    @validator("password2")
    def passwords_match(cls, v: str, values):
        if "password1" in values and v != values["password1"]:
            raise ValueError("两次输入的密码不一致")
        return v

    @validator("password1")
    def password_strength(cls, v: str):
        if len(v) < 8:
            raise ValueError("密码长度不能少于8个字符")
        return v

    @validator("nickname", "phone", pre=True)
    def strip_optional(cls, v):
        if v is None:
            return v
        return v.strip() or None

    @validator("gender")
    def gender_choices(cls, v):
        if v and v not in ["male", "female", "other", "prefer_not_to_say"]:
            raise ValueError("性别选项无效")
        return v

    @validator("birth_date")
    def birth_date_format(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("出生日期格式不正确，请使用 YYYY-MM-DD 格式")
        return v


# ==== 个人 ====
class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password1: str
    new_password2: str
    captcha: Optional[str] = None
    captcha_key: Optional[str] = None

    @validator("old_password", "new_password1", "new_password2")
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("密码不能为空")
        return v

    @validator("new_password2")
    def new_passwords_match(cls, v: str, values):
        if "new_password1" in values and v != values["new_password1"]:
            raise ValueError("两次输入的新密码不一致")
        return v

    @validator("new_password1")
    def password_strength(cls, v: str):
        if len(v) < 8:
            raise ValueError("新密码长度不能少于8个字符")
        return v


class UserProfileUpdateSchema(BaseModel):
    phone: Optional[str] = None
    nickname: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None

    @validator("phone", "nickname", pre=True)
    def strip_optional(cls, v):
        if v is None:
            return v
        return v.strip() or None

    @validator("gender")
    def gender_choices(cls, v):
        if v and v not in ["male", "female", "other", "prefer_not_to_say"]:
            raise ValueError("性别选项无效")
        return v


# ==== 管理 ====
class AdminCreateUserSchema(BaseModel):
    username: str
    email: EmailStr
    password: str
    nickname: Optional[str] = None
    is_active: Optional[bool] = True
    is_staff: Optional[bool] = False

    @validator("username")
    def username_not_empty(cls, v: str):
        if not v or not v.strip():
            raise ValueError("用户名不能为空")
        return v.strip()

    @validator("password")
    def password_strength(cls, v: str):
        if not v or len(v) < 8:
            raise ValueError("密码长度不能少于8个字符")
        return v

    @validator("nickname", pre=True)
    def strip_nickname(cls, v):
        if v is None:
            return v
        return v.strip() or None


class UserUpdateSchema(BaseModel):
    email: Optional[EmailStr] = None
    nickname: Optional[str] = None
    is_active: Optional[bool] = None
    is_staff: Optional[bool] = None
    password: Optional[str] = None

    @validator("password")
    def password_strength(cls, v: Optional[str]):
        if v and len(v) < 8:
            raise ValueError("密码长度不能少于8个字符")
        return v

    @validator("nickname", pre=True)
    def strip_nickname(cls, v):
        if v is None:
            return v
        return v.strip() or None


# ==== 验证码 ====
class CaptchaVerifySchema(BaseModel):
    captcha: str
    captcha_key: str

    @validator("captcha", "captcha_key")
    def not_empty(cls, v: str):
        if not v or not v.strip():
            raise ValueError("字段不能为空")
        return v.strip()


# ==== 数据工厂 ====
class SeedUserSchema(BaseModel):
    count: int = Field(10, ge=1, le=50, description="单次生成数量，最大 50")
    default_password: str = Field("123456", min_length=1, description="生成用户的默认密码")
    role_id: Optional[UUID] = Field(None, description="可选角色ID，为生成用户分配角色")

    @validator("default_password")
    def password_not_blank(cls, v: str):
        if not v or not v.strip():
            raise ValueError("默认密码不能为空")
        return v


__all__ = [
    "UserLoginSchema",
    "UserRegisterSchema",
    "ChangePasswordSchema",
    "UserProfileUpdateSchema",
    "AdminCreateUserSchema",
    "UserUpdateSchema",
    "CaptchaVerifySchema",
    "SeedUserSchema",
]
