"""通知原子操作函数"""
from typing import List
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.utils import timezone

from ..model import Notification

User = get_user_model()


def get_notifications_queryset_action() -> QuerySet:
    """获取通知基础查询集"""
    return Notification.objects.select_related("recipient").order_by("-created")


def get_user_notifications_action(user) -> QuerySet:
    """获取用户的通知查询集"""
    queryset = get_notifications_queryset_action()
    if user.is_authenticated and not (user.is_staff or user.is_superuser):
        return queryset.filter(recipient=user)
    return queryset


def get_notification_action(notification_id: int) -> Notification:
    """获取单个通知"""
    return Notification.objects.get(id=notification_id)


def get_all_active_users_action() -> List[User]:
    """获取所有活跃用户"""
    return list(User.objects.filter(is_active=True))


def get_staff_users_action() -> List[User]:
    """获取管理员用户"""
    return list(User.objects.filter(is_active=True, is_staff=True))


def get_regular_users_action() -> List[User]:
    """获取普通用户"""
    return list(User.objects.filter(is_active=True, is_staff=False))


def get_user_by_id_action(user_id: int) -> User:
    """根据ID获取用户"""
    return User.objects.get(id=user_id)


def create_notification_action(
    recipient: User,
    title: str,
    body: str,
    category: str,
    priority: str,
    status: str,
    scheduled_for=None,
    sent_role=None,
) -> Notification:
    """创建单个通知"""
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        body=body,
        category=category,
        priority=priority,
        status=status,
        scheduled_for=scheduled_for,
        sent_role=sent_role,
    )


def bulk_create_notifications_action(notifications: List[Notification]) -> List[Notification]:
    """批量创建通知"""
    return Notification.objects.bulk_create(notifications)


def mark_notification_read_action(notification: Notification) -> None:
    """标记通知为已读"""
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save(update_fields=["is_read", "read_at"])


def bulk_mark_notifications_read_action(notification_ids: List[int], queryset: QuerySet) -> int:
    """批量标记通知为已读"""
    return queryset.filter(id__in=notification_ids).update(is_read=True, read_at=timezone.now())


def update_notification_status_action(notification: Notification, status: str) -> None:
    """更新通知状态"""
    notification.status = status
    notification.save(update_fields=["status"])


def delete_notification_action(notification: Notification) -> None:
    """删除通知"""
    notification.delete()


def count_unread_notifications_action(queryset: QuerySet) -> int:
    """统计未读通知数量"""
    return queryset.filter(is_read=False).count()

