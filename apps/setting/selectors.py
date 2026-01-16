"""系统设置只读查询与缓存操作。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import QuerySet

from apps.core.utils.serializers import to_iso
from .model import SystemSetting

CACHE_PREFIX = "setting:"
CACHE_TIMEOUT = 60 * 60  # 1小时


def base_settings_queryset() -> QuerySet:
    """基础查询，自动过滤软删除。"""
    return SystemSetting.objects.filter(is_deleted=False)


def list_settings(active_only: bool = False, category: Optional[str] = None) -> QuerySet:
    """获取设置基础查询集。"""
    queryset = base_settings_queryset()
    if active_only:
        queryset = queryset.filter(is_active=True)
    if category:
        queryset = queryset.filter(category=category)
    return queryset.order_by("category", "sort_order", "key")


def paginate_settings(page: int, page_size: int, *, active_only: bool = False, category: Optional[str] = None) -> Dict[str, Any]:
    """分页获取设置列表。"""
    queryset = list_settings(active_only=active_only, category=category)
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    items = [serialize_setting(setting) for setting in page_obj]
    return {
        "results": items,
        "pagination": {
            "count": paginator.count,
            "page": page,
            "page_size": page_size,
            "pages": paginator.num_pages,
        },
    }


def get_setting_by_key(key: str, *, active_only: bool = True) -> SystemSetting:
    """根据键名获取设置。"""
    queryset = base_settings_queryset().filter(key=key)
    if active_only:
        queryset = queryset.filter(is_active=True)
    return queryset.get()


def get_setting_by_id(setting_id: UUID) -> SystemSetting:
    """根据ID获取设置。"""
    return base_settings_queryset().get(id=setting_id)


def get_active_settings() -> QuerySet:
    """获取所有启用的设置。"""
    return list_settings(active_only=True)


def group_settings() -> List[Dict[str, Any]]:
    """按分类分组设置并序列化。"""
    grouped: Dict[str, List[SystemSetting]] = {}
    for setting in get_active_settings():
        grouped.setdefault(setting.category, []).append(setting)

    category_names = dict(SystemSetting.CATEGORY)
    result: List[Dict[str, Any]] = []
    for category, category_settings in sorted(grouped.items()):
        result.append(
            {
                "category": category,
                "category_name": category_names.get(category, category),
                "settings": [serialize_setting(item, typed_value=True) for item in category_settings],
            }
        )
    return result


def settings_dictionary() -> Dict[str, Any]:
    """获取启用设置的键值字典。"""
    return {setting.key: setting.get_value() for setting in get_active_settings()}


def serialize_setting(setting: SystemSetting, *, typed_value: bool = False) -> Dict[str, Any]:
    """序列化设置对象。"""
    value = setting.get_value() if typed_value else setting.value
    default_value = setting._convert_value(setting.default_value) if typed_value else setting.default_value
    return {
        "id": setting.id,
        "key": setting.key,
        "name": setting.name,
        "value_type": setting.value_type,
        "category": setting.category,
        "value": value,
        "default_value": default_value,
        "description": setting.description,
        "is_active": setting.is_active,
        "is_editable": setting.is_editable,
        "sort_order": setting.sort_order,
        "validation_rules": setting.validation_rules or {},
        "extra_options": setting.extra_options or {},
        "created_at": to_iso(setting.created_at),
        "updated_at": to_iso(setting.updated_at),
    }


def clear_setting_cache(key: str) -> None:
    """清除单个设置的缓存。"""
    cache_key = f"{CACHE_PREFIX}{key}"
    cache.delete(cache_key)


def clear_all_settings_cache() -> None:
    """清除所有设置缓存。"""
    cache.clear()


def get_setting_from_cache(key: str) -> Optional[Any]:
    """从缓存获取设置值。"""
    cache_key = f"{CACHE_PREFIX}{key}"
    return cache.get(cache_key)


def set_setting_to_cache(key: str, value: Any) -> None:
    """将设置值存入缓存。"""
    cache_key = f"{CACHE_PREFIX}{key}"
    cache.set(cache_key, value, CACHE_TIMEOUT)


__all__ = [
    "base_settings_queryset",
    "list_settings",
    "paginate_settings",
    "get_setting_by_key",
    "get_setting_by_id",
    "get_active_settings",
    "group_settings",
    "settings_dictionary",
    "serialize_setting",
    "clear_setting_cache",
    "clear_all_settings_cache",
    "get_setting_from_cache",
    "set_setting_to_cache",
]
