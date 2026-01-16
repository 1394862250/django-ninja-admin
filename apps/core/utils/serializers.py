"""序列化辅助工具。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable


def to_iso(dt: datetime | None) -> str | None:
    """安全地将 datetime 转为 ISO 字符串。"""
    return dt.isoformat() if dt else None


def model_to_dict_iso(instance, fields: Iterable[str]) -> Dict[str, Any]:
    """
    按字段序列化模型对象，datetime 字段使用 ISO 字符串。
    仅适合简单平铺场景，复杂序列化建议使用 Schema。
    """
    result: Dict[str, Any] = {}
    for field in fields:
        value = getattr(instance, field, None)
        if isinstance(value, datetime):
            result[field] = to_iso(value)
        else:
            result[field] = value
    return result


__all__ = ["to_iso", "model_to_dict_iso"]
