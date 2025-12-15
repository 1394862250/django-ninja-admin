"""
验证码相关的数据验证模式
用于 captcha.py API
"""
from pydantic import BaseModel, validator


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
