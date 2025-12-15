"""日志原子操作函数"""
from typing import Optional, Dict, Any
from django.db.models import QuerySet
from django.contrib.auth import get_user_model

from ..model import Log

User = get_user_model()


def get_logs_queryset_action() -> QuerySet:
    """获取日志基础查询集"""
    return Log.objects.select_related("user").order_by("-created")


def create_log_action(
    level: str = Log.LEVEL.INFO,
    category: str = Log.CATEGORY.system,
    action: str = "unknown",
    message: str = "",
    user: Optional[User] = None,
    ip_address: Optional[str] = None,
    user_agent: str = "",
    path: str = "",
    method: str = "",
    status_code: Optional[int] = None,
    extra_data: Optional[Dict[str, Any]] = None,
) -> Log:
    """创建日志记录"""
    return Log.objects.create(
        user=user,
        level=level,
        category=category,
        action=action,
        message=message,
        ip_address=ip_address,
        user_agent=user_agent,
        path=path,
        method=method,
        status_code=status_code,
        extra_data=extra_data or {},
    )

