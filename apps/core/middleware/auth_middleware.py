"""核心认证中间件：确保 request.user 始终存在。"""
from django.contrib.auth.models import AnonymousUser


class AuthMiddleware:
    """确保 request.user 存在的轻量中间件。"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(request, "user", None) or isinstance(request.user, AnonymousUser):
            request.user = AnonymousUser()
        return self.get_response(request)


__all__ = ["AuthMiddleware"]
