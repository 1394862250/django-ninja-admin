"""通知业务流程（写/权限为主，读依赖 selectors）。"""
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from datetime import datetime
import random
from faker import Faker
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.utils import timezone

from .model import Notification
from .selectors import (
    count_unread_notifications,
    filter_notifications,
    get_admin_unread_count,
    get_all_active_users,
    get_notification_by_id,
    get_notification_stats,
    get_regular_users,
    get_staff_users,
    get_unread_notifications,
    get_user_by_id,
    get_user_notifications,
)
from apps.core.api.exceptions import ValidationException
from apps.core.api.permissions import ensure_staff_or_superuser
from apps.log.services import log_notification_action

User = get_user_model()
faker = Faker("zh_CN")


def _bulk_create_notifications(notifications: List[Notification]) -> List[Notification]:
    """批量创建通知"""
    return Notification.objects.bulk_create(notifications)


def _mark_notification_read(notification: Notification) -> None:
    """标记通知为已读"""
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save(update_fields=["is_read", "read_at"])


def _bulk_mark_notifications_read(notification_ids: List[UUID], queryset: QuerySet) -> int:
    """批量标记通知为已读"""
    return queryset.filter(id__in=notification_ids).update(is_read=True, read_at=timezone.now())


def _update_notification_status(notification: Notification, status: str) -> None:
    """更新通知状态"""
    notification.status = status
    notification.save(update_fields=["status"])


def _delete_notification(notification: Notification) -> None:
    """删除通知"""
    notification.delete()


def can_access_notification_flow(user, notification: Notification) -> Tuple[bool, Optional[str]]:
    """判断用户是否可以访问通知"""
    if not user.is_authenticated:
        return False, "需要登录访问"
    if user.is_staff or user.is_superuser:
        return True, None
    if notification.recipient.id == user.id:
        return True, None
    return False, "无权访问该通知"


def can_manage_notifications_flow(user) -> Tuple[bool, Optional[str]]:
    """判断用户是否可以管理通知"""
    if not user.is_authenticated:
        return False, "需要登录访问"
    if not (user.is_staff or user.is_superuser):
        return False, "需要管理员权限"
    return True, None


def get_user_notifications_flow(user) -> QuerySet:
    """获取用户通知列表流程"""
    return get_user_notifications(user)


def get_unread_count_flow(user) -> int:
    """获取未读通知数量流程"""
    queryset = get_user_notifications(user)
    return count_unread_notifications(queryset)


def get_unread_notifications_flow(user) -> QuerySet:
    """获取未读通知列表流程"""
    return get_unread_notifications(user)


def mark_notification_read_flow(user, notification_id: UUID) -> Tuple[bool, Optional[str], Optional[Notification]]:
    """标记通知为已读流程"""
    queryset = get_user_notifications(user)
    try:
        notification = queryset.get(id=notification_id)
    except Notification.DoesNotExist:
        return False, "通知不存在", None
    _mark_notification_read(notification)
    return True, None, notification


def mark_notifications_read_bulk_flow(user, notification_ids: List[UUID]) -> Tuple[int, Optional[str]]:
    """批量标记通知为已读流程"""
    queryset = get_user_notifications(user)
    updated = _bulk_mark_notifications_read(notification_ids, queryset)
    return updated, None


def filter_notifications_flow(
    category: Optional[str] = None,
    status: Optional[str] = None,
    is_read: Optional[bool] = None,
) -> QuerySet:
    """过滤通知流程"""
    return filter_notifications(category=category, status=status, is_read=is_read)


def get_admin_unread_count_flow() -> int:
    """获取管理员未读通知数量流程"""
    return get_admin_unread_count()


def get_notification_stats_flow() -> Dict:
    """获取通知统计流程"""
    return get_notification_stats()


def create_notifications_flow(
    user: User,
    recipient_id: Optional[UUID],
    recipient_role: Optional[str],
    title: str,
    body: str,
    category: str,
    priority: str,
    status: str,
    scheduled_for: Optional[datetime],
    request,
) -> Tuple[bool, Optional[str], Optional[List[Notification]]]:
    """创建通知流程"""
    can_manage, error_msg = can_manage_notifications_flow(user)
    if not can_manage:
        return False, error_msg, None

    if priority not in Notification.PRIORITY:
        return False, "无效的通知优先级", None
    if status not in Notification.STATUS:
        return False, "无效的通知状态", None

    recipients: List[User] = []
    if recipient_role:
        if recipient_role == "all":
            recipients = get_all_active_users()
        elif recipient_role == "管理员":
            recipients = get_staff_users()
        elif recipient_role == "用户":
            recipients = get_regular_users()
        else:
            return False, "无效的接收角色", None
        if not recipients:
            return False, "没有找到符合条件的接收用户", None
    elif recipient_id:
        try:
            recipients = [get_user_by_id(recipient_id)]
        except User.DoesNotExist:
            return False, "接收用户不存在", None
    else:
        return False, "必须指定接收用户ID或接收角色", None

    if not recipients:
        return False, "没有找到符合条件的接收用户", None

    sent_role = recipient_role if recipient_role else None
    notifications = [
        Notification(
            recipient=r,
            title=title,
            body=body,
            category=category,
            priority=priority,
            status=status,
            scheduled_for=scheduled_for,
            sent_role=sent_role,
        )
        for r in recipients
    ]
    created_notifications = _bulk_create_notifications(notifications)

    log_notification_action(
        action="创建通知",
        message=f"用户 {user.username} 创建了 {len(created_notifications)} 条通知：{title}",
        user=user,
        request=request,
        extra_data={
            "title": title,
            "category": category,
            "priority": priority,
            "recipient_role": recipient_role,
            "recipient_count": len(created_notifications),
        },
    )

    return True, None, created_notifications


def seed_notifications_service(
    operator: User,
    *,
    count: int = 10,
    recipient_role: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """批量生成测试通知（仅 staff/superuser）。"""
    ensure_staff_or_superuser(operator)

    if count < 1 or count > 50:
        raise ValidationException("单次生成数量需在 1~50 之间")

    recipients = list(get_all_active_users())
    if not recipients:
        raise ValidationException("没有可用的接收用户，请先创建用户")

    def pick_priority():
        return priority if priority else random.choice([p for p, _ in Notification.PRIORITY])

    def pick_status():
        return status if status else random.choice([s for s, _ in Notification.STATUS])

    notifications: List[Notification] = []
    for _ in range(count):
        if recipient_role:
            if recipient_role == "all":
                target_users = recipients
            elif recipient_role == "管理员":
                target_users = [u for u in recipients if u.is_staff or u.is_superuser]
            elif recipient_role == "用户":
                target_users = [u for u in recipients if not (u.is_staff or u.is_superuser)]
            else:
                raise ValidationException("无效的接收角色")
            if not target_users:
                raise ValidationException("指定角色下没有可用用户")
            target_user = random.choice(target_users)
        else:
            target_user = random.choice(recipients)

        notifications.append(
            Notification(
                recipient=target_user,
                title=faker.sentence(nb_words=6),
                body=faker.paragraph(nb_sentences=3),
                category=random.choice(["系统", "活动", "营销", "提醒"]),
                priority=pick_priority(),
                status=pick_status(),
                is_read=False,
                scheduled_for=None,
                sent_role=recipient_role or None,
            )
        )

    created_notifications = _bulk_create_notifications(notifications)

    log_notification_action(
        action="批量生成通知",
        message=f"管理员 {operator.username} 生成通知 {len(created_notifications)} 条",
        user=operator,
        request=None,
        extra_data={"count": len(created_notifications), "recipient_role": recipient_role, "priority": priority, "status": status},
    )

    return {
        "created": len(created_notifications),
        "recipient_role": recipient_role,
        "priority": priority,
        "status": status,
    }


def send_notification_flow(user: User, notification_id: UUID, request) -> Tuple[bool, Optional[str], Optional[Notification]]:
    """发送通知流程"""
    can_manage, error_msg = can_manage_notifications_flow(user)
    if not can_manage:
        return False, error_msg, None

    try:
        notification = get_notification_by_id(notification_id)
    except Notification.DoesNotExist:
        return False, "通知不存在", None

    if notification.status != Notification.STATUS.pending:
        return False, f"通知状态为 {notification.status}，只能发送待发送状态的通知", None

    if notification.scheduled_for and notification.scheduled_for > timezone.now():
        return False, "计划发送时间未到，无法发送", None

    _update_notification_status(notification, Notification.STATUS.sent)

    log_notification_action(
        action="发送通知",
        message=f"用户 {user.username} 发送了通知：{notification.title}",
        user=user,
        request=request,
        extra_data={
            "notification_id": notification.id,
            "title": notification.title,
            "recipient": notification.recipient.username if notification.recipient else None,
            "recipient_role": notification.sent_role,
        },
    )

    return True, None, notification


def delete_notification_flow(user: User, notification_id: UUID, request) -> Tuple[bool, Optional[str]]:
    """删除通知流程"""
    can_manage, error_msg = can_manage_notifications_flow(user)
    if not can_manage:
        return False, error_msg

    try:
        notification = get_notification_by_id(notification_id)
    except Notification.DoesNotExist:
        return False, "通知不存在"

    log_notification_action(
        action="删除通知",
        message=f"用户 {user.username} 删除了通知：{notification.title}",
        user=user,
        request=request,
        extra_data={
            "notification_id": notification.id,
            "title": notification.title,
            "recipient": notification.recipient.username if notification.recipient else None,
            "status": notification.status,
        },
    )

    _delete_notification(notification)
    return True, None


__all__ = [
    "get_user_notifications_flow",
    "get_unread_count_flow",
    "get_unread_notifications_flow",
    "mark_notification_read_flow",
    "mark_notifications_read_bulk_flow",
    "filter_notifications_flow",
    "get_admin_unread_count_flow",
    "get_notification_stats_flow",
    "create_notifications_flow",
    "send_notification_flow",
    "delete_notification_flow",
    "can_manage_notifications_flow",
    "can_access_notification_flow",
]
