"""日志数据读取层（Selectors）。"""
from django.db.models import QuerySet

from .model import Log


def base_logs_queryset() -> QuerySet:
    """基础查询：按创建时间倒序并预取用户。"""
    return Log.objects.filter(is_deleted=False).select_related("user").order_by("-created_at")


__all__ = ["base_logs_queryset"]
