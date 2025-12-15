"""日志工具函数 - 仅包含工具函数，不包含业务逻辑"""
from app.log.actions.log_actions import create_log_action
from app.log.model import Log


def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def sanitize_sensitive_data(data):
    """脱敏敏感数据"""
    if not data:
        return data
        
    sensitive_fields = ['password', 'token', 'secret', 'key', 'auth', 'csrf']
    
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if any(field in key.lower() for field in sensitive_fields):
                sanitized[key] = '***'
            elif isinstance(value, dict):
                sanitized[key] = sanitize_sensitive_data(value)
            elif isinstance(value, list):
                sanitized[key] = [sanitize_sensitive_data(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value
        return sanitized
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) if isinstance(item, dict) else item for item in data]
    else:
        return data


# 以下函数保留为便捷函数，但内部调用 Action
def create_log(
    level=Log.LEVEL.INFO,
    category=Log.CATEGORY.system,
    action=None,
    message=None,
    user=None,
    request=None,
    ip_address=None,
    user_agent=None,
    path=None,
    method=None,
    status_code=None,
    extra_data=None
):
    """
    创建日志记录（便捷函数，内部调用 Action）
    
    注意：此函数保留是为了向后兼容，实际业务逻辑在 Action 中
    """
    
    # 从请求对象中提取信息
    if request:
        ip_address = ip_address or get_client_ip(request)
        user_agent = user_agent or request.META.get('HTTP_USER_AGENT', '')
        path = path or request.path
        method = method or request.method
        user = user or (request.user if hasattr(request, 'user') and request.user.is_authenticated else None)
    
    # 确保字段不为 None
    if user_agent is None:
        user_agent = ''
    if path is None:
        path = ''
    if method is None:
        method = ''
    
    try:
        create_log_action(
            level=level,
            category=category,
            action=action or 'unknown',
            message=message or '',
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            path=path,
            method=method,
            status_code=status_code,
            extra_data=extra_data or {},
        )
    except Exception as e:
        # 记录日志失败不应该影响正常业务流程
        print(f"创建日志失败: {e}")


def log_user_action(action, message, level=Log.LEVEL.INFO, user=None, request=None, extra_data=None):
    """记录用户操作日志的便捷函数"""
    create_log(
        level=level,
        category=Log.CATEGORY.user,
        action=action,
        message=message,
        user=user,
        request=request,
        extra_data=extra_data
    )


def log_auth_action(action, message, level=Log.LEVEL.INFO, user=None, request=None, extra_data=None):
    """记录认证操作日志的便捷函数"""
    create_log(
        level=level,
        category=Log.CATEGORY.auth,
        action=action,
        message=message,
        user=user,
        request=request,
        extra_data=extra_data
    )


def log_system_action(action, message, level=Log.LEVEL.INFO, user=None, request=None, extra_data=None):
    """记录系统操作日志的便捷函数"""
    create_log(
        level=level,
        category=Log.CATEGORY.system,
        action=action,
        message=message,
        user=user,
        request=request,
        extra_data=extra_data
    )


def log_api_action(action, message, level=Log.LEVEL.INFO, user=None, request=None, status_code=None, extra_data=None):
    """记录API操作日志的便捷函数"""
    create_log(
        level=level,
        category=Log.CATEGORY.api,
        action=action,
        message=message,
        user=user,
        request=request,
        status_code=status_code,
        extra_data=extra_data
    )


def log_admin_action(action, message, level=Log.LEVEL.INFO, user=None, request=None, extra_data=None):
    """记录管理操作日志的便捷函数"""
    create_log(
        level=level,
        category=Log.CATEGORY.admin,
        action=action,
        message=message,
        user=user,
        request=request,
        extra_data=extra_data
    )


def log_notification_action(action, message, level=Log.LEVEL.INFO, user=None, request=None, extra_data=None):
    """记录通知操作日志的便捷函数"""
    create_log(
        level=level,
        category=Log.CATEGORY.notification,
        action=action,
        message=message,
        user=user,
        request=request,
        extra_data=extra_data
    )
