from typing import TYPE_CHECKING

from .apps import UserConfig

__all__ = ["UserConfig", "User", "UserProfile", "UserActivity", "DocumentUpload", "Role", "UserRole"]

if TYPE_CHECKING:  # 仅用于类型提示，避免 AppRegistryNotReady
    from .model import User, UserProfile, UserActivity, DocumentUpload, Role, UserRole


def __getattr__(name):
    """惰性导出模型，避免在应用加载前触发 Django AppRegistry。"""
    if name in {"User", "UserProfile", "UserActivity", "DocumentUpload", "Role", "UserRole"}:
        from . import model

        return getattr(model, name)
    raise AttributeError(f"module 'apps.user' has no attribute '{name}'")
