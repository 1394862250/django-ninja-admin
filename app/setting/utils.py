"""设置工具类"""
from typing import Any, Optional
from django.core.cache import cache
from app.setting.models import SystemSetting


class SettingManager:
    """设置管理器"""

    # 缓存键前缀
    CACHE_PREFIX = 'setting:'
    # 缓存超时时间（秒）
    CACHE_TIMEOUT = 60 * 60  # 1小时

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """获取设置值

        Args:
            key: 设置键名，如 'system.site_name'
            default: 默认值

        Returns:
            设置值，如果不存在则返回默认值
        """
        # 尝试从缓存获取
        cache_key = f"{cls.CACHE_PREFIX}{key}"
        value = cache.get(cache_key)

        if value is not None:
            return value

        # 缓存未命中，从数据库获取
        try:
            setting = SystemSetting.objects.get(key=key, is_active=True)
            value = setting.get_value()

            # 存入缓存
            cache.set(cache_key, value, cls.CACHE_TIMEOUT)

            return value
        except SystemSetting.DoesNotExist:
            return default

    @classmethod
    def get_bool(cls, key: str, default: bool = False) -> bool:
        """获取布尔类型设置"""
        value = cls.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)

    @classmethod
    def get_int(cls, key: str, default: int = 0) -> int:
        """获取整数类型设置"""
        value = cls.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @classmethod
    def get_float(cls, key: str, default: float = 0.0) -> float:
        """获取浮点数类型设置"""
        value = cls.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @classmethod
    def get_str(cls, key: str, default: str = '') -> str:
        """获取字符串类型设置"""
        value = cls.get(key, default)
        return str(value) if value is not None else default

    @classmethod
    def get_dict(cls, key: str, default: dict = None) -> dict:
        """获取字典类型设置"""
        if default is None:
            default = {}
        value = cls.get(key, default)
        if isinstance(value, dict):
            return value
        return default

    @classmethod
    def set(cls, key: str, value: Any) -> bool:
        """设置值

        Args:
            key: 设置键名
            value: 设置值

        Returns:
            是否设置成功
        """
        try:
            setting = SystemSetting.objects.get(key=key, is_active=True)
            setting.set_value(value)
            setting.save()

            # 清除缓存
            cache_key = f"{cls.CACHE_PREFIX}{key}"
            cache.delete(cache_key)

            return True
        except SystemSetting.DoesNotExist:
            return False

    @classmethod
    def clear_cache(cls, key: str = None):
        """清除缓存

        Args:
            key: 设置键名，如果为空则清除所有设置缓存
        """
        if key:
            cache_key = f"{cls.CACHE_PREFIX}{key}"
            cache.delete(cache_key)
        else:
            # 清除所有设置相关的缓存
            cache.clear()

    @classmethod
    def get_many(cls, keys: list[str]) -> dict[str, Any]:
        """批量获取设置

        Args:
            keys: 设置键名列表

        Returns:
            字典，键为设置键名，值为设置值
        """
        result = {}

        for key in keys:
            result[key] = cls.get(key)

        return result

    @classmethod
    def is_feature_enabled(cls, feature_key: str) -> bool:
        """检查功能是否启用

        Args:
            feature_key: 功能标识，如 'notification.enabled'

        Returns:
            功能是否启用
        """
        return cls.get_bool(feature_key, False)

    @classmethod
    def get_site_config(cls) -> dict[str, Any]:
        """获取站点配置"""
        config_keys = [
            'system.site_name',
            'system.site_description',
            'system.site_logo',
            'ui.theme',
            'ui.language',
            'ui.timezone',
        ]
        return cls.get_many(config_keys)

    @classmethod
    def get_email_config(cls) -> dict[str, Any]:
        """获取邮件配置"""
        config_keys = [
            'email.enabled',
            'email.host',
            'email.port',
            'email.username',
            'email.use_tls',
        ]
        return cls.get_many(config_keys)

    @classmethod
    def get_security_config(cls) -> dict[str, Any]:
        """获取安全配置"""
        config_keys = [
            'security.max_login_attempts',
            'security.lockout_duration',
            'security.password_min_length',
            'security.require_email_verification',
        ]
        return cls.get_many(config_keys)


# 便捷函数
def get_setting(key: str, default: Any = None) -> Any:
    """获取设置值的便捷函数"""
    return SettingManager.get(key, default)


def is_feature_enabled(feature_key: str) -> bool:
    """检查功能是否启用的便捷函数"""
    return SettingManager.is_feature_enabled(feature_key)
