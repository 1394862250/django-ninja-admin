"""设置业务流程"""
from typing import Any, Optional, List, Dict, Tuple
from collections import defaultdict
from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from ..actions.setting_actions import (
    get_settings_queryset_action,
    get_setting_by_key_action,
    get_setting_by_id_action,
    get_active_settings_action,
    update_setting_value_action,
    clear_setting_cache_action,
    clear_all_settings_cache_action,
    get_setting_from_cache_action,
    set_setting_to_cache_action,
    delete_setting_action,
    reset_setting_to_default_action,
)
from ..models import SystemSetting

User = get_user_model()

def can_manage_settings_flow(user) -> Tuple[bool, Optional[str]]:
    """判断用户是否可以管理设置"""
    if not user.is_authenticated:
        return False, "需要登录访问"
    if not (user.is_staff or user.is_superuser):
        return False, "需要管理员权限"
    return True, None

def get_settings_queryset_flow() -> QuerySet:
    """获取设置查询集流程"""
    return get_settings_queryset_action()

def get_setting_flow(key: str, default: Any = None) -> Any:
    """获取设置值流程（带缓存）"""
    # 尝试从缓存获取
    value = get_setting_from_cache_action(key)
    if value is not None:
        return value

    # 缓存未命中，从数据库获取
    try:
        setting = get_setting_by_key_action(key)
        value = setting.get_value()
        # 存入缓存
        set_setting_to_cache_action(key, value)
        return value
    except SystemSetting.DoesNotExist:
        return default

def get_setting_bool_flow(key: str, default: bool = False) -> bool:
    """获取布尔类型设置流程"""
    value = get_setting_flow(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)

def get_setting_int_flow(key: str, default: int = 0) -> int:
    """获取整数类型设置流程"""
    value = get_setting_flow(key, default)
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def get_setting_float_flow(key: str, default: float = 0.0) -> float:
    """获取浮点数类型设置流程"""
    value = get_setting_flow(key, default)
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def get_setting_str_flow(key: str, default: str = '') -> str:
    """获取字符串类型设置流程"""
    value = get_setting_flow(key, default)
    return str(value) if value is not None else default

def get_setting_dict_flow(key: str, default: dict = None) -> dict:
    """获取字典类型设置流程"""
    if default is None:
        default = {}
    value = get_setting_flow(key, default)
    if isinstance(value, dict):
        return value
    return default

def set_setting_flow(user: User, key: str, value: Any) -> Tuple[bool, Optional[str]]:
    """设置值流程"""
    can_manage, error_msg = can_manage_settings_flow(user)
    if not can_manage:
        return False, error_msg

    try:
        setting = get_setting_by_key_action(key)
        update_setting_value_action(setting, value)
        clear_setting_cache_action(key)
        return True, None
    except SystemSetting.DoesNotExist:
        return False, "设置不存在"

def get_settings_grouped_flow() -> List[Dict[str, Any]]:
    """获取按分类分组的设置流程"""
    settings = get_active_settings_action()
    grouped = defaultdict(list)
    for setting in settings:
        grouped[setting.category].append(setting)

    result = []
    category_names = dict(SystemSetting.CATEGORY)
    for category, category_settings in sorted(grouped.items()):
        result.append(
            {
                "category": category,
                "category_name": category_names.get(category, category),
                "settings": category_settings,
            }
        )
    return result

def get_setting_by_key_flow(key: str) -> SystemSetting:
    """根据键名获取设置对象流程"""
    return get_setting_by_key_action(key)


def get_setting_value_flow(key: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """获取设置值流程"""
    try:
        setting = get_setting_by_key_action(key)
        return True, None, {
            "key": setting.key,
            "name": setting.name,
            "value": setting.get_value(),
            "value_type": setting.value_type,
            "description": setting.description,
        }
    except SystemSetting.DoesNotExist:
        return False, "设置不存在", None

def update_setting_value_flow(
    user: User, key: str, value: Any, validate: bool = True
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """更新设置值流程"""
    can_manage, error_msg = can_manage_settings_flow(user)
    if not can_manage:
        return False, error_msg, None

    try:
        setting = get_setting_by_key_action(key)
        if validate:
            valid, message = setting.validate_value(value)
            if not valid:
                return False, message, None
        update_setting_value_action(setting, value)
        clear_setting_cache_action(key)
        return True, None, {
            "key": setting.key,
            "name": setting.name,
            "value": setting.get_value(),
            "value_type": setting.value_type,
            "description": setting.description,
        }
    except SystemSetting.DoesNotExist:
        return False, "设置不存在", None

def batch_update_settings_flow(
    user: User, settings_data: List[Dict[str, Any]]
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """批量更新设置流程"""
    can_manage, error_msg = can_manage_settings_flow(user)
    if not can_manage:
        return False, error_msg, {}

    updated = []
    errors = []
    for item in settings_data:
        try:
            setting = get_setting_by_key_action(item["key"])
            if item.get("validate", True):
                valid, message = setting.validate_value(item["value"])
                if not valid:
                    errors.append({"key": item["key"], "message": message})
                    continue
            update_setting_value_action(setting, item["value"])
            clear_setting_cache_action(item["key"])
            updated.append(
                {
                    "key": setting.key,
                    "name": setting.name,
                    "value": setting.get_value(),
                }
            )
        except SystemSetting.DoesNotExist:
            errors.append({"key": item["key"], "message": "设置不存在"})
        except Exception as e:
            errors.append({"key": item.get("key", "unknown"), "message": str(e)})

    return True, None, {
        "updated": updated,
        "errors": errors,
        "updated_count": len(updated),
        "error_count": len(errors),
    }

def delete_setting_by_key_flow(user: User, key: str) -> Tuple[bool, Optional[str]]:
    """根据键名删除设置流程"""
    can_manage, error_msg = can_manage_settings_flow(user)
    if not can_manage:
        return False, error_msg

    try:
        setting = get_setting_by_key_action(key)
        delete_setting_action(setting)
        clear_setting_cache_action(key)
        return True, None
    except SystemSetting.DoesNotExist:
        return False, "设置不存在"

def validate_setting_value_flow(key: str, value: str) -> Tuple[bool, bool, str]:
    """验证设置值流程"""
    try:
        setting = get_setting_by_key_action(key)
        valid, message = setting.validate_value(value)
        return True, valid, message
    except SystemSetting.DoesNotExist:
        return False, False, "设置不存在"

def get_settings_dictionary_flow() -> Dict[str, Any]:
    """获取设置字典流程"""
    settings = get_active_settings_action()
    result = {s.key: s.get_value() for s in settings}
    return result

def reset_settings_to_defaults_flow(user: User) -> Tuple[bool, Optional[str], int]:
    """重置设置为默认值流程"""
    can_manage, error_msg = can_manage_settings_flow(user)
    if not can_manage:
        return False, error_msg, 0

    settings = get_active_settings_action()
    reset_count = 0
    for setting in settings:
        if setting.default_value is not None:
            reset_setting_to_default_action(setting)
            clear_setting_cache_action(setting.key)
            reset_count += 1
    return True, None, reset_count

def get_many_settings_flow(keys: List[str]) -> Dict[str, Any]:
    """批量获取设置流程"""
    result = {}
    for key in keys:
        result[key] = get_setting_flow(key)
    return result

def is_feature_enabled_flow(feature_key: str) -> bool:
    """检查功能是否启用流程"""
    return get_setting_bool_flow(feature_key, False)

def get_site_config_flow() -> Dict[str, Any]:
    """获取站点配置流程"""
    config_keys = [
        'system.site_name',
        'system.site_description',
        'system.site_logo',
        'ui.theme',
        'ui.language',
        'ui.timezone',
    ]
    return get_many_settings_flow(config_keys)

def get_email_config_flow() -> Dict[str, Any]:
    """获取邮件配置流程"""
    config_keys = [
        'email.enabled',
        'email.host',
        'email.port',
        'email.username',
        'email.use_tls',
    ]
    return get_many_settings_flow(config_keys)

def get_security_config_flow() -> Dict[str, Any]:
    """获取安全配置流程"""
    config_keys = [
        'security.max_login_attempts',
        'security.lockout_duration',
        'security.password_min_length',
        'security.require_email_verification',
    ]
    return get_many_settings_flow(config_keys)

