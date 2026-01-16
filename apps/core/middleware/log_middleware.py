"""核心日志中间件：收集请求基础数据并交由日志服务处理。"""
import time
from django.conf import settings

from apps.core.utils.request import get_client_ip
from apps.core.utils.security import sanitize_sensitive_data


class LogMiddleware:
    """
    日志记录中间件
    - 收集请求/响应信息
    - 依赖 apps.log.services.create_request_log 保存
    - 不直接执行业务逻辑，失败不影响主流程
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.exclude_paths = getattr(
            settings,
            "LOG_EXCLUDE_PATHS",
            ["/static/", "/media/", "/favicon.ico", "/api/docs/", "/api/openapi.json"],
        )
        self.exclude_status_codes = getattr(settings, "LOG_EXCLUDE_STATUS_CODES", [200, 201, 204])

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        process_time = time.time() - start_time

        if self.should_log(request, response):
            self.log_request(request, response, process_time)
        return response

    def should_log(self, request, response) -> bool:
        """判断是否需要记录日志"""
        for path in self.exclude_paths:
            if request.path.startswith(path):
                return False
        if response.status_code in self.exclude_status_codes:
            return False
        if not (request.path.startswith("/api/") or request.path.startswith("/manage/")):
            return False
        return True

    def log_request(self, request, response, process_time: float):
        """收集基础信息并交给日志服务"""
        try:
            from apps.log.services import create_request_log

            user = getattr(request, "user", None)
            user = user if user and getattr(user, "is_authenticated", False) else None

            extra_data = {
                "process_time": round(process_time, 3),
                "request_size": len(getattr(request, "body", b"") or b""),
                "response_size": len(getattr(response, "content", b"") or b""),
                "query_params": sanitize_sensitive_data(getattr(request, "GET", {})),
            }

            create_request_log(
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                path=request.path,
                method=request.method,
                status_code=response.status_code,
                extra_data=extra_data,
            )
        except Exception as exc:  # pragma: no cover - 防御性
            print(f"收集日志信息失败: {exc}")
