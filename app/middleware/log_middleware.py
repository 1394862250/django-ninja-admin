"""日志记录中间件 - 仅收集请求信息，不操作数据库"""
import time
from django.conf import settings


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
        """收集请求信息（不操作数据库）"""
        try:
            # 从 app.log.flows 导入日志流程
            from app.log.flows.log_flows import create_request_log_flow
            
            # 获取用户信息
            user = getattr(request, 'user', None)
            user = user if user and user.is_authenticated else None
            
            # 获取IP地址
            ip_address = self.get_client_ip(request)
            
            # 获取请求方法
            method = request.method
            
            # 获取请求路径
            path = request.path
            
            # 获取状态码
            status_code = response.status_code
            
            # 获取用户代理
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # 准备额外数据
            extra_data = {
                'process_time': round(process_time, 3),
                'request_size': len(request.body) if hasattr(request, 'body') else 0,
                'response_size': len(response.content) if hasattr(response, 'content') else 0,
            }
            
            # 调用 Flow 创建日志（异步或同步，由 Flow 决定）
            create_request_log_flow(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                path=path,
                method=method,
                status_code=status_code,
                extra_data=extra_data,
            )
        except Exception as e:
            # 记录日志失败不应该影响正常业务流程
            print(f"收集日志信息失败: {e}")
    
    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
