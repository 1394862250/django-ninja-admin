"""设置原子操作函数"""
from typing import Any, Optional, List, Dict
from django.core.cache import cache
from django.db.models import QuerySet

from ..models import SystemSetting

CACHE_PREFIX = 'setting:'
CACHE_TIMEOUT = 60 * 60  # 1小时


def get_settings_queryset_action() -> QuerySet:
    """获取设置基础查询集"""
    return SystemSetting.objects.all().order_by("category", "sort_order", "key")


def get_setting_by_key_action(key: str) -> SystemSetting:
    """根据键名获取设置"""
    return SystemSetting.objects.get(key=key, is_active=True)


def get_setting_by_id_action(setting_id: int) -> SystemSetting:
    """根据ID获取设置"""
    return SystemSetting.objects.get(id=setting_id)


def get_active_settings_action() -> QuerySet:
    """获取所有启用的设置"""
    return SystemSetting.objects.filter(is_active=True).order_by("category", "sort_order", "key")


def update_setting_value_action(setting: SystemSetting, value: Any) -> None:
    """更新设置值"""
    setting.set_value(value)
    setting.save(update_fields=["value"])


def clear_setting_cache_action(key: str) -> None:
    """清除单个设置的缓存"""
    cache_key = f"{CACHE_PREFIX}{key}"
    cache.delete(cache_key)


def clear_all_settings_cache_action() -> None:
    """清除所有设置缓存"""
    cache.clear()


def get_setting_from_cache_action(key: str) -> Optional[Any]:
    """从缓存获取设置值"""
    cache_key = f"{CACHE_PREFIX}{key}"
    return cache.get(cache_key)


def set_setting_to_cache_action(key: str, value: Any) -> None:
    """将设置值存入缓存"""
    cache_key = f"{CACHE_PREFIX}{key}"
    cache.set(cache_key, value, CACHE_TIMEOUT)


def delete_setting_action(setting: SystemSetting) -> None:
    """删除设置"""
    setting.delete()


def reset_setting_to_default_action(setting: SystemSetting) -> None:
    """重置设置为默认值"""
    setting.value = setting.default_value
    setting.save(update_fields=["value"])

