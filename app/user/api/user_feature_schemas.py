"""
用户功能相关的数据验证模式
用于 user_feature.py API
"""
from typing import Optional
from pydantic import BaseModel, validator


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
