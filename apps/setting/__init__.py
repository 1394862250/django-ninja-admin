"""设置管理模块。"""
from typing import TYPE_CHECKING

__all__ = ["SystemSetting", "SettingCategory"]

if TYPE_CHECKING:
    from .model import SettingCategory, SystemSetting


def __getattr__(name):
    """惰性导出模型，避免在应用加载前触发 AppRegistryNotReady。"""
    if name in {"SystemSetting", "SettingCategory"}:
        from . import model

        return getattr(model, name)
    raise AttributeError(f"module 'apps.setting' has no attribute '{name}'")
