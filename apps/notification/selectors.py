"""通知只读查询与统计。"""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db.models import Count, QuerySet

from .model import Notification

User = get_user_model()


def get_notifications_queryset() -> QuerySet:
    """基础查询集：按创建时间倒序，预取接收者。"""
    return Notification.objects.filter(is_deleted=False).select_related("recipient").order_by("-created_at")


def get_user_notifications(user) -> QuerySet:
    """获取用户通知列表（含权限过滤）。"""
    queryset = get_notifications_queryset()
    if not user.is_authenticated:
        return queryset.none()
    if user.is_staff or user.is_superuser:
        return queryset
    return queryset.filter(recipient=user)


def get_unread_notifications(user) -> QuerySet:
    """获取用户未读通知列表。"""
    return get_user_notifications(user).filter(is_read=False)


def get_notification_by_id(notification_id: UUID) -> Notification:
    """获取单条通知"""
    return Notification.objects.select_related("recipient").get(id=notification_id)


def count_unread_notifications(queryset: QuerySet) -> int:
    """统计未读数量"""
    return queryset.filter(is_read=False).count()


def filter_notifications(
    category: Optional[str] = None,
    status: Optional[str] = None,
    is_read: Optional[bool] = None,
) -> QuerySet:
    """按条件过滤通知列表"""
    queryset = get_notifications_queryset()
    if category:
        queryset = queryset.filter(category=category)
    if status:
        queryset = queryset.filter(status=status)
    if is_read is not None:
        queryset = queryset.filter(is_read=is_read)
    return queryset


def get_admin_unread_count() -> int:
    """管理员未读数量"""
    return Notification.objects.filter(is_read=False).count()


def get_notification_stats() -> Dict:
    """通知统计"""
    status_stats = {code: Notification.objects.filter(status=code).count() for code, _ in Notification.STATUS}
    category_stats = (
        Notification.objects.values("category")
        .order_by("category")
        .annotate(total=Count("id"))
    )
    priority_stats = {code: Notification.objects.filter(priority=code).count() for code, _ in Notification.PRIORITY}
    return {
        "status": status_stats,
        "priority": priority_stats,
        "category": list(category_stats),
        "unread_total": Notification.objects.filter(is_read=False).count(),
        "total": Notification.objects.count(),
    }


def get_all_active_users() -> List[User]:
    """获取活跃用户"""
    return list(User.objects.filter(is_active=True))


def get_staff_users() -> List[User]:
    """获取管理员用户"""
    return list(User.objects.filter(is_active=True, is_staff=True))


def get_regular_users() -> List[User]:
    """获取普通用户"""
    return list(User.objects.filter(is_active=True, is_staff=False))


def get_user_by_id(user_id: UUID) -> User:
    """根据ID获取用户"""
    return User.objects.get(id=user_id)


__all__ = [
    "get_notifications_queryset",
    "get_user_notifications",
    "get_unread_notifications",
    "get_notification_by_id",
    "count_unread_notifications",
    "filter_notifications",
    "get_admin_unread_count",
    "get_notification_stats",
    "get_all_active_users",
    "get_staff_users",
    "get_regular_users",
    "get_user_by_id",
]
