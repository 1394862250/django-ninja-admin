"""
用户相关的数据验证模式
用于 user.py API
"""
from typing import Optional
from pydantic import BaseModel, validator


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
