"""
数据验证器
"""
from typing import Any, Optional, List, Dict
from pydantic import BaseModel, EmailStr, validator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from captcha.fields import CaptchaField
from captcha.models import CaptchaStore

# 导入用户相关的验证模式
from app.user.schemas import (
    UserLoginSchema,
    UserRegisterSchema,
    AdminCreateUserSchema,
    UserUpdateSchema,
    ChangePasswordSchema,
    UserProfileUpdateSchema,
    CaptchaRequestSchema,
    CaptchaVerifySchema
)


