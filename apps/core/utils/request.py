"""请求相关的纯工具函数。"""
from typing import Optional
from django.http import HttpRequest


def get_client_ip(request: HttpRequest) -> Optional[str]:
    """获取客户端 IP（无业务语义）。"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


__all__ = ["get_client_ip"]
