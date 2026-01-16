"""系统设置业务服务层：写操作、权限校验、缓存维护。"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from apps.core.api.exceptions import BusinessException, NotFoundException, ValidationException
from apps.core.api.permissions import ensure_staff_or_superuser

from .model import SystemSetting
from .selectors import (
    clear_setting_cache,
    get_active_settings,
    get_setting_by_id,
    get_setting_by_key,
    get_setting_from_cache,
    group_settings,
    serialize_setting,
    set_setting_to_cache,
    settings_dictionary,
)

User = get_user_model()


# 读取与缓存
def get_setting_value(key: str, default: Any = None) -> Any:
    """获取设置值（带缓存）。"""
    cached = get_setting_from_cache(key)
    if cached is not None:
        return cached
    try:
        setting = get_setting_by_key(key)
    except SystemSetting.DoesNotExist:
        return default
    value = setting.get_value()
    set_setting_to_cache(key, value)
    return value


def get_setting_bool(key: str, default: bool = False) -> bool:
    value = get_setting_value(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


def get_setting_int(key: str, default: int = 0) -> int:
    value = get_setting_value(key, default)
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def get_setting_float(key: str, default: float = 0.0) -> float:
    value = get_setting_value(key, default)
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def get_setting_str(key: str, default: str = "") -> str:
    value = get_setting_value(key, default)
    return str(value) if value is not None else default


def get_setting_dict(key: str, default: dict | None = None) -> dict:
    default = default or {}
    value = get_setting_value(key, default)
    if isinstance(value, dict):
        return value
    return default


# 写操作
def set_setting_value(user: User, key: str, value: Any, *, validate: bool = True) -> Dict[str, Any]:
    """更新单个设置值。"""
    ensure_staff_or_superuser(user)
    try:
        setting = get_setting_by_key(key, active_only=False)
    except SystemSetting.DoesNotExist:
        raise NotFoundException("设置不存在")

    if not setting.is_editable:
        raise BusinessException("该设置不可编辑")

    if validate:
        valid, message = setting.validate_value(value)
        if not valid:
            raise ValidationException(message)

    setting.set_value(value)
    setting.save(update_fields=["value", "updated_at"])
    clear_setting_cache(key)
    return serialize_setting(setting, typed_value=True)


def batch_update_settings(user: User, settings_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """批量更新设置值，逐项验证。"""
    ensure_staff_or_superuser(user)

    updated: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for item in settings_data:
        key = item.get("key")
        if not key:
            errors.append({"key": None, "message": "缺少设置键名"})
            continue
        try:
            setting = get_setting_by_key(key, active_only=False)
        except SystemSetting.DoesNotExist:
            errors.append({"key": key, "message": "设置不存在"})
            continue

        if not setting.is_editable:
            errors.append({"key": key, "message": "该设置不可编辑"})
            continue

        if item.get("validate", True):
            valid, message = setting.validate_value(item.get("value"))
            if not valid:
                errors.append({"key": key, "message": message})
                continue

        setting.set_value(item.get("value"))
        setting.save(update_fields=["value", "updated_at"])
        clear_setting_cache(key)
        updated.append({"key": setting.key, "name": setting.name, "value": setting.get_value()})

    return {
        "updated": updated,
        "errors": errors,
        "updated_count": len(updated),
        "error_count": len(errors),
    }


def delete_setting_by_key(user: User, key: str) -> None:
    """根据键名删除设置（软删除）。"""
    ensure_staff_or_superuser(user)
    try:
        setting = get_setting_by_key(key, active_only=False)
    except SystemSetting.DoesNotExist:
        raise NotFoundException("设置不存在")

    setting.soft_delete()
    clear_setting_cache(key)


def validate_setting_value(key: str, value: Any) -> Tuple[bool, str]:
    """校验设置值。"""
    try:
        setting = get_setting_by_key(key, active_only=False)
    except SystemSetting.DoesNotExist:
        raise NotFoundException("设置不存在")
    return setting.validate_value(value)


def get_settings_dictionary() -> Dict[str, Any]:
    """获取所有启用设置的字典。"""
    return settings_dictionary()


def reset_settings_to_defaults(user: User) -> int:
    """重置启用设置到默认值。"""
    ensure_staff_or_superuser(user)
    settings = get_active_settings()
    reset_count = 0
    for setting in settings:
        setting.set_value(setting.default_value)
        setting.save(update_fields=["value", "updated_at"])
        clear_setting_cache(setting.key)
        reset_count += 1
    return reset_count


def create_setting(user: User, data: Dict[str, Any]) -> SystemSetting:
    """创建新设置。"""
    ensure_staff_or_superuser(user)
    try:
        setting = SystemSetting.objects.create(**data)
    except Exception as exc:
        raise BusinessException(str(exc))
    clear_setting_cache(setting.key)
    return setting


def update_setting(user: User, setting_id: str, data: Dict[str, Any]) -> SystemSetting:
    """更新设置元信息。"""
    ensure_staff_or_superuser(user)
    try:
        setting = get_setting_by_id(setting_id)
    except SystemSetting.DoesNotExist:
        raise NotFoundException("设置不存在")

    if "key" in data:
        raise BusinessException("不支持修改设置键名")

    for field, value in data.items():
        if field == "value":
            setting.set_value(value)
        else:
            setattr(setting, field, value)
    setting.save()
    clear_setting_cache(setting.key)
    return setting


def delete_setting(user: User, setting_id: str) -> None:
    """根据ID删除设置（软删除）。"""
    ensure_staff_or_superuser(user)
    try:
        setting = get_setting_by_id(setting_id)
    except SystemSetting.DoesNotExist:
        raise NotFoundException("设置不存在")
    cache_key = setting.key
    setting.soft_delete()
    clear_setting_cache(cache_key)


def get_setting_value_detail(key: str) -> Dict[str, Any]:
    """获取设置值详情（序列化后的数据）。"""
    try:
        setting = get_setting_by_key(key)
    except SystemSetting.DoesNotExist:
        raise NotFoundException("设置不存在")
    return {
        "key": setting.key,
        "name": setting.name,
        "value": setting.get_value(),
        "value_type": setting.value_type,
        "description": setting.description,
    }


def get_settings_grouped() -> List[Dict[str, Any]]:
    """按分类分组的序列化设置列表。"""
    return group_settings()


def upload_setting_asset(user: User, *, file, max_size: int = 5 * 1024 * 1024) -> Dict[str, Any]:
    """上传设置相关资源文件。"""
    from ninja.files import UploadedFile  # 延迟导入以避免循环

    ensure_staff_or_superuser(user)
    if not isinstance(file, UploadedFile):
        raise ValidationException("无效的上传文件")

    if not file.content_type.startswith(("image/", "video/", "application/")):
        raise ValidationException("不支持的文件类型")

    if file.size > max_size:
        raise ValidationException("文件大小不能超过 5MB")

    extension = os.path.splitext(file.name)[1] or ""
    filename = f"settings/{uuid4().hex}{extension}"
    saved_path = default_storage.save(filename, ContentFile(file.read()))
    file_url = default_storage.url(saved_path)

    return {
        "url": file_url,
        "path": saved_path,
        "size": file.size,
        "content_type": file.content_type,
    }


def initialize_system_settings(user: Optional[User] = None) -> int:
    """初始化基础系统设置。"""
    if user:
        ensure_staff_or_superuser(user)

    initial_settings = [
        # 系统配置
        {
            "key": "system.site_name",
            "name": "站点名称",
            "value": "Django Ninja Admin",
            "default_value": "Django Ninja Admin",
            "value_type": SystemSetting.VALUE_TYPE.string,
            "category": SystemSetting.CATEGORY.system,
            "description": "网站的名称，显示在标题栏和侧边栏",
            "sort_order": 1,
        },
        {
            "key": "system.site_logo",
            "name": "站点 Logo",
            "value": "/static/img/logo.png",
            "default_value": "/static/img/logo.png",
            "value_type": SystemSetting.VALUE_TYPE.url,
            "category": SystemSetting.CATEGORY.system,
            "description": "网站 Logo 图片地址",
            "sort_order": 2,
        },
        # 界面配置
        {
            "key": "ui.pagination_size",
            "name": "分页数量",
            "value": "20",
            "default_value": "20",
            "value_type": SystemSetting.VALUE_TYPE.integer,
            "category": SystemSetting.CATEGORY.ui,
            "description": "后台列表页默认每页显示的条数",
            "sort_order": 10,
            "validation_rules": {"min": 5, "max": 100},
        },
        {
            "key": "ui.theme",
            "name": "默认主题",
            "value": "light",
            "default_value": "light",
            "value_type": SystemSetting.VALUE_TYPE.string,
            "category": SystemSetting.CATEGORY.ui,
            "description": "系统默认配色方案",
            "sort_order": 11,
            "extra_options": {
                "choices": [
                    {"label": "浅色", "value": "light"},
                    {"label": "深色", "value": "dark"},
                    {"label": "系统", "value": "system"},
                ]
            },
        },
        # 安全配置
        {
            "key": "security.enable_captcha",
            "name": "登录验证码",
            "value": "true",
            "default_value": "true",
            "value_type": SystemSetting.VALUE_TYPE.boolean,
            "category": SystemSetting.CATEGORY.security,
            "description": "是否开启登录页面的验证码校验",
            "sort_order": 20,
        },
    ]

    created_count = 0
    for data in initial_settings:
        if not SystemSetting.objects.filter(key=data["key"]).exists():
            SystemSetting.objects.create(**data)
            created_count += 1
    
    return created_count


__all__ = [
    "initialize_system_settings",
    "get_setting_value",
    "get_setting_bool",
    "get_setting_int",
    "get_setting_float",
    "get_setting_str",
    "get_setting_dict",
    "set_setting_value",
    "batch_update_settings",
    "delete_setting_by_key",
    "validate_setting_value",
    "get_settings_dictionary",
    "reset_settings_to_defaults",
    "create_setting",
    "update_setting",
    "delete_setting",
    "get_setting_value_detail",
    "get_settings_grouped",
    "upload_setting_asset",
]
