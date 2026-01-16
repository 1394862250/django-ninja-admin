"""安全相关的通用工具。"""
from typing import Any


SENSITIVE_KEYS = ("password", "token", "secret", "key", "auth", "csrf")


def mask_value(value: str, visible: int = 2) -> str:
    """对字符串做简单脱敏，保留前后若干位。"""
    if not value or not isinstance(value, str):
        return value
    if len(value) <= visible * 2:
        return "*" * len(value)
    return f"{value[:visible]}{'*' * (len(value) - visible * 2)}{value[-visible:]}"


def sanitize_sensitive_data(data: Any):
    """递归脱敏常见敏感字段，保持结构不变。"""
    if data is None:
        return data

    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if any(field in key.lower() for field in SENSITIVE_KEYS):
                sanitized[key] = "***"
            elif isinstance(value, dict):
                sanitized[key] = sanitize_sensitive_data(value)
            elif isinstance(value, list):
                sanitized[key] = [sanitize_sensitive_data(item) for item in value]
            else:
                sanitized[key] = value
        return sanitized

    if isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]

    return data


__all__ = ["sanitize_sensitive_data", "mask_value", "SENSITIVE_KEYS"]
