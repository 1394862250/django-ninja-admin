"""日志记录工具函数和装饰器"""
import functools
import traceback
from django.conf import settings
from django.utils import timezone
from app.log.model import Log


def log_action(
    level=Log.LEVEL.INFO,
    category=Log.CATEGORY.system,
    action=None,
    message=None,
    include_user=True,
    include_request=True,
    extra_data=None
):
    """
    日志记录装饰器
    
    Args:
        level: 日志级别
        category: 日志类别
        action: 操作动作，如果为None则使用函数名
        message: 日志消息，如果为None则使用函数名和参数
        include_user: 是否包含用户信息
        include_request: 是否包含请求信息
        extra_data: 额外数据
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取请求对象（通常是第一个参数）
            request = None
            if args and hasattr(args[0], 'META'):
                request = args[0]
            
            # 获取用户信息
            user = None
            if request and hasattr(request, 'user'):
                user = request.user if request.user.is_authenticated else None
            
            # 确定操作动作
            act = action or func.__name__
            
            # 确定日志消息
            msg = message or f"执行操作: {act}"
            
            # 准备额外数据
            extra = extra_data or {}
            if 'function_args' not in extra:
                # 记录函数参数（脱敏处理）
                safe_kwargs = sanitize_sensitive_data(kwargs)
                extra['function_args'] = safe_kwargs
            
            try:
                # 执行原函数
                result = func(*args, **kwargs)
                
                # 记录成功日志
                create_log(
                    level=level,
                    category=category,
                    action=act,
                    message=f"{msg} - 成功",
                    user=user if include_user else None,
                    request=request if include_request else None,
                    extra_data=extra
                )
                
                return result
            except Exception as e:
                # 记录错误日志
                create_log(
                    level=Log.LEVEL.ERROR,
                    category=category,
                    action=act,
                    message=f"{msg} - 失败: {str(e)}",
                    user=user if include_user else None,
                    request=request if include_request else None,
                    extra_data={
                        **extra,
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    }
                )
                raise
        
        return wrapper
    return decorator


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
    创建日志记录
    
    Args:
        level: 日志级别
        category: 日志类别
        action: 操作动作
        message: 日志消息
        user: 用户对象
        request: 请求对象
        ip_address: IP地址
        user_agent: 用户代理
        path: 请求路径
        method: 请求方法
        status_code: 状态码
        extra_data: 额外数据
    """
    try:
        # 从请求对象中提取信息
        if request:
            ip_address = ip_address or get_client_ip(request)
            user_agent = user_agent or request.META.get('HTTP_USER_AGENT', '')
            path = path or request.path
            method = method or request.method
            user = user or (request.user if hasattr(request, 'user') and request.user.is_authenticated else None)
        
        # 确保 user_agent 不为 None（管理命令等场景）
        if user_agent is None:
            user_agent = ''
        
        # 确保其他字段也不为 None
        if path is None:
            path = ''
        if method is None:
            method = ''
        
        # 创建日志记录
        Log.objects.create(
            user=user,
            level=level,
            category=category,
            action=action or 'unknown',
            message=message or '',
            ip_address=ip_address,
            user_agent=user_agent,
            path=path,
            method=method,
            status_code=status_code,
            extra_data=extra_data or {}
        )
    except Exception as e:
        # 记录日志失败不应该影响正常业务流程
        print(f"创建日志失败: {e}")


def log_user_action(action, message, level=Log.LEVEL.INFO, user=None, request=None, extra_data=None):
    """
    记录用户操作日志的便捷函数
    
    Args:
        action: 操作动作
        message: 日志消息
        level: 日志级别
        user: 用户对象
        request: 请求对象
        extra_data: 额外数据
    """
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
    """
    记录认证操作日志的便捷函数
    
    Args:
        action: 操作动作
        message: 日志消息
        level: 日志级别
        user: 用户对象
        request: 请求对象
        extra_data: 额外数据
    """
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
    """
    记录系统操作日志的便捷函数
    
    Args:
        action: 操作动作
        message: 日志消息
        level: 日志级别
        user: 用户对象
        request: 请求对象
        extra_data: 额外数据
    """
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
    """
    记录API操作日志的便捷函数
    
    Args:
        action: 操作动作
        message: 日志消息
        level: 日志级别
        user: 用户对象
        request: 请求对象
        status_code: 状态码
        extra_data: 额外数据
    """
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
    """
    记录管理操作日志的便捷函数
    
    Args:
        action: 操作动作
        message: 日志消息
        level: 日志级别
        user: 用户对象
        request: 请求对象
        extra_data: 额外数据
    """
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
    """
    记录通知操作日志的便捷函数
    
    Args:
        action: 操作动作
        message: 日志消息
        level: 日志级别
        user: 用户对象
        request: 请求对象
        extra_data: 额外数据
    """
    create_log(
        level=level,
        category=Log.CATEGORY.notification,
        action=action,
        message=message,
        user=user,
        request=request,
        extra_data=extra_data
    )


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
