"""设置相关Schema"""
from ninja import Schema
from typing import Optional, Dict, Any
from pydantic import Field


class SystemSettingBase(Schema):
    """设置基础Schema"""
    key: str
    name: str
    value_type: str
    category: str
    value: Optional[str] = None
    default_value: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    is_editable: bool = True
    sort_order: int = 0
    validation_rules: Optional[Dict[str, Any]] = Field(default_factory=dict)
    extra_options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SystemSettingCreate(SystemSettingBase):
    """创建设置Schema"""
    pass


class SystemSettingUpdate(Schema):
    """更新设置Schema"""
    name: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    validation_rules: Optional[Dict[str, Any]] = None
    extra_options: Optional[Dict[str, Any]] = None


class SystemSettingOut(SystemSettingBase):
    """设置输出Schema"""
    id: int
    created: str
    modified: str

    class Config:
        from_attributes = True


class SystemSettingValueUpdate(Schema):
    """更新设置值Schema"""
    value: str
    do_validate: bool = True


class BatchUpdateSettings(Schema):
    """批量更新设置Schema"""
    settings: list[SystemSettingValueUpdate]


class SystemSettingGroup(Schema):
    """按分类分组的设置Schema"""
    category: str
    category_name: str
    settings: list[SystemSettingOut]


class SettingValidationResult(Schema):
    """设置验证结果Schema"""
    valid: bool
    message: str


class SettingValueOut(Schema):
    """设置值输出Schema"""
    key: str
    name: str
    value: Any
    value_type: str
    description: Optional[str] = None
