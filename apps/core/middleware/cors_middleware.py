"""核心 CORS 中间件：为未覆盖的接口补充跨域头。"""
from django.conf import settings


class CORSApiMiddleware:
    """简单的 CORS 处理（如已使用 corsheaders，可按需关闭本中间件）。"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
        self.allow_all = getattr(settings, "CORS_ALLOW_ALL_ORIGINS", True)

    def __call__(self, request):
        if request.method == "OPTIONS":
            return self._build_preflight_response()

        response = self.get_response(request)
        self._apply_headers(response)
        return response

    def _apply_headers(self, response):
        origin = "*" if self.allow_all or not self.allowed_origins else ", ".join(self.allowed_origins)
        response["Access-Control-Allow-Origin"] = origin
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    def _build_preflight_response(self):
        from django.http import JsonResponse

        response = JsonResponse({})
        return self._apply_headers(response)


__all__ = ["CORSApiMiddleware"]
