"""设置模块 Schemas 定义。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ninja import Schema
from pydantic import Field


class SettingBaseSchema(Schema):
    key: str
    name: str
    value_type: str
    category: str
    value: Optional[Any] = None
    default_value: Optional[Any] = None
    description: Optional[str] = None
    is_active: bool = True
    is_editable: bool = True
    sort_order: int = 0
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    extra_options: Dict[str, Any] = Field(default_factory=dict)


class SettingCreateSchema(SettingBaseSchema):
    """创建设置入参。"""
    pass


class SettingUpdateSchema(Schema):
    """更新设置入参。"""
    name: Optional[str] = None
    value: Optional[Any] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_editable: Optional[bool] = None
    sort_order: Optional[int] = None
    validation_rules: Optional[Dict[str, Any]] = None
    extra_options: Optional[Dict[str, Any]] = None
    default_value: Optional[Any] = None
    value_type: Optional[str] = None
    category: Optional[str] = None


class SettingOutSchema(SettingBaseSchema):
    """设置输出 Schema。"""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SettingValueUpdateSchema(Schema):
    """更新设置值 Schema。"""

    key: str = Field(..., description="设置键名")
    value: Any = Field(..., description="设置值")
    validate: bool = Field(default=True, description="是否验证值")


class BatchUpdateSettingsSchema(Schema):
    """批量更新设置 Schema。"""

    settings: List[SettingValueUpdateSchema]


class SettingValidationResultSchema(Schema):
    """设置验证结果 Schema。"""

    valid: bool
    message: str


class SettingValueOutSchema(Schema):
    """设置值输出 Schema。"""

    key: str
    name: str
    value: Any
    value_type: str
    description: Optional[str] = None


__all__ = [
    "SettingBaseSchema",
    "SettingCreateSchema",
    "SettingUpdateSchema",
    "SettingOutSchema",
    "SettingValueUpdateSchema",
    "BatchUpdateSettingsSchema",
    "SettingValidationResultSchema",
    "SettingValueOutSchema",
]
