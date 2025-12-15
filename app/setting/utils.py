"""设置工具函数 - 便捷函数，内部调用 Flow"""
from typing import Any
from .flows.setting_flows import (
    get_setting_flow,
    get_setting_bool_flow,
    get_setting_int_flow,
    get_setting_float_flow,
    get_setting_str_flow,
    get_setting_dict_flow,
    is_feature_enabled_flow,
    get_site_config_flow,
    get_email_config_flow,
    get_security_config_flow,
    get_many_settings_flow,
)


def get_setting(key: str, default: Any = None) -> Any:
    """获取设置值的便捷函数（向后兼容）"""
    return get_setting_flow(key, default)


def get_bool(key: str, default: bool = False) -> bool:
    """获取布尔类型设置的便捷函数"""
    return get_setting_bool_flow(key, default)


def get_int(key: str, default: int = 0) -> int:
    """获取整数类型设置的便捷函数"""
    return get_setting_int_flow(key, default)


def get_float(key: str, default: float = 0.0) -> float:
    """获取浮点数类型设置的便捷函数"""
    return get_setting_float_flow(key, default)


def get_str(key: str, default: str = '') -> str:
    """获取字符串类型设置的便捷函数"""
    return get_setting_str_flow(key, default)


def get_dict(key: str, default: dict = None) -> dict:
    """获取字典类型设置的便捷函数"""
    return get_setting_dict_flow(key, default)


def is_feature_enabled(feature_key: str) -> bool:
    """检查功能是否启用的便捷函数（向后兼容）"""
    return is_feature_enabled_flow(feature_key)


def get_site_config() -> dict[str, Any]:
    """获取站点配置的便捷函数（向后兼容）"""
    return get_site_config_flow()


def get_email_config() -> dict[str, Any]:
    """获取邮件配置的便捷函数（向后兼容）"""
    return get_email_config_flow()


def get_security_config() -> dict[str, Any]:
    """获取安全配置的便捷函数（向后兼容）"""
    return get_security_config_flow()


def get_many(keys: list[str]) -> dict[str, Any]:
    """批量获取设置的便捷函数（向后兼容）"""
    return get_many_settings_flow(keys)
