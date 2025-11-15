"""日志记录中间件"""
import time
import json
from django.utils import timezone
from django.conf import settings
from app.log.model import Log


class LogMiddleware:
    """
    日志记录中间件
    自动记录HTTP请求日志
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # 不记录日志的路径
        self.exclude_paths = getattr(settings, 'LOG_EXCLUDE_PATHS', [
            '/static/',
            '/media/',
            '/favicon.ico',
            '/api/docs/',
            '/api/openapi.json',
        ])
        
        # 不记录日志的状态码
        self.exclude_status_codes = getattr(settings, 'LOG_EXCLUDE_STATUS_CODES', [200, 201, 204])
    
    def __call__(self, request):
        # 记录请求开始时间
        start_time = time.time()
        
        # 处理请求
        response = self.get_response(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 检查是否需要记录日志
        if self.should_log(request, response):
            self.log_request(request, response, process_time)
        
        return response
    
    def should_log(self, request, response):
        """判断是否需要记录日志"""
        # 检查路径是否在排除列表中
        for path in self.exclude_paths:
            if request.path.startswith(path):
                return False
        
        # 检查状态码是否在排除列表中
        if response.status_code in self.exclude_status_codes:
            return False
        
        # 只记录API请求和管理后台请求
        if not (request.path.startswith('/api/') or request.path.startswith('/manage/')):
            return False
        
        return True
    
    def log_request(self, request, response, process_time):
        """记录请求日志"""
        try:
            # 获取用户信息
            user = getattr(request, 'user', None)
            user_id = user.id if user and user.is_authenticated else None
            
            # 获取IP地址
            ip_address = self.get_client_ip(request)
            
            # 获取请求方法
            method = request.method
            
            # 获取请求路径
            path = request.path
            
            # 获取状态码
            status_code = response.status_code
            
            # 确定日志级别
            level = self.get_log_level(status_code)
            
            # 确定日志类别
            category = self.get_log_category(request)
            
            # 确定操作动作
            action = self.get_log_action(request, response)
            
            # 构建日志消息
            message = self.get_log_message(request, response, process_time)
            
            # 获取用户代理
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # 准备额外数据
            extra_data = {
                'process_time': round(process_time, 3),
                'request_size': len(request.body) if hasattr(request, 'body') else 0,
                'response_size': len(response.content) if hasattr(response, 'content') else 0,
            }
            
            # 记录敏感参数（如密码）时进行脱敏
            if request.method in ['POST', 'PUT', 'PATCH'] and hasattr(request, 'body'):
                try:
                    body_data = json.loads(request.body.decode('utf-8'))
                    if isinstance(body_data, dict):
                        # 脱敏处理
                        sanitized_data = self.sanitize_sensitive_data(body_data)
                        extra_data['request_body'] = sanitized_data
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            
            # 创建日志记录
            Log.objects.create(
                user_id=user_id,
                level=level,
                category=category,
                action=action,
                message=message,
                ip_address=ip_address,
                user_agent=user_agent,
                path=path,
                method=method,
                status_code=status_code,
                extra_data=extra_data
            )
        except Exception as e:
            # 记录日志失败不应该影响正常业务流程
            print(f"记录日志失败: {e}")
    
    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_log_level(self, status_code):
        """根据状态码确定日志级别"""
        if status_code < 300:
            return Log.LEVEL.INFO
        elif status_code < 400:
            return Log.LEVEL.INFO
        elif status_code < 500:
            return Log.LEVEL.WARNING
        else:
            return Log.LEVEL.ERROR
    
    def get_log_category(self, request):
        """根据请求路径确定日志类别"""
        path = request.path
        
        if path.startswith('/api/auth/'):
            return Log.CATEGORY.auth
        elif path.startswith('/api/user/'):
            return Log.CATEGORY.user
        elif path.startswith('/api/notification/'):
            return Log.CATEGORY.notification
        elif path.startswith('/api/'):
            return Log.CATEGORY.api
        elif path.startswith('/manage/'):
            return Log.CATEGORY.admin
        else:
            return Log.CATEGORY.system
    
    def get_log_action(self, request, response):
        """根据请求方法和路径确定操作动作"""
        method = request.method
        path = request.path
        
        # 尝试从路径中提取资源类型
        path_parts = path.strip('/').split('/')
        if len(path_parts) >= 2:
            resource_type = path_parts[1]
        else:
            resource_type = 'unknown'
        
        # 根据HTTP方法和资源类型确定操作
        if method == 'GET':
            if path.endswith('/') or len(path_parts) <= 2:
                action = f'查看{resource_type}列表'
            else:
                action = f'查看{resource_type}详情'
        elif method == 'POST':
            action = f'创建{resource_type}'
        elif method == 'PUT' or method == 'PATCH':
            action = f'更新{resource_type}'
        elif method == 'DELETE':
            action = f'删除{resource_type}'
        else:
            action = f'{method} {resource_type}'
        
        return action
    
    def get_log_message(self, request, response, process_time):
        """构建日志消息"""
        return f"{request.method} {request.path} - {response.status_code} - {round(process_time, 3)}s"
    
    def sanitize_sensitive_data(self, data):
        """脱敏敏感数据"""
        sensitive_fields = ['password', 'token', 'secret', 'key', 'auth']
        
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if any(field in key.lower() for field in sensitive_fields):
                    sanitized[key] = '***'
                elif isinstance(value, dict):
                    sanitized[key] = self.sanitize_sensitive_data(value)
                elif isinstance(value, list):
                    sanitized[key] = [self.sanitize_sensitive_data(item) if isinstance(item, dict) else item for item in value]
                else:
                    sanitized[key] = value
            return sanitized
        else:
            return data
