"""通知业务流程"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Count
from django.utils import timezone

from ..actions.notification_actions import (
    get_user_notifications_action,
    get_notification_action,
    get_all_active_users_action,
    get_staff_users_action,
    get_regular_users_action,
    get_user_by_id_action,
    create_notification_action,
    bulk_create_notifications_action,
    mark_notification_read_action,
    bulk_mark_notifications_read_action,
    update_notification_status_action,
    delete_notification_action,
    count_unread_notifications_action,
)
from ..model import Notification
from app.utils.log_utils import log_notification_action

User = get_user_model()


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
    return get_user_notifications_action(user)


def get_unread_count_flow(user) -> int:
    """获取未读通知数量流程"""
    queryset = get_user_notifications_action(user)
    return count_unread_notifications_action(queryset)


def get_unread_notifications_flow(user) -> QuerySet:
    """获取未读通知列表流程"""
    queryset = get_user_notifications_action(user)
    return queryset.filter(is_read=False)


def mark_notification_read_flow(user, notification_id: int) -> Tuple[bool, Optional[str], Optional[Notification]]:
    """标记通知为已读流程"""
    queryset = get_user_notifications_action(user)
    try:
        notification = queryset.get(id=notification_id)
    except Notification.DoesNotExist:
        return False, "通知不存在", None
    mark_notification_read_action(notification)
    return True, None, notification


def mark_notifications_read_bulk_flow(user, notification_ids: List[int]) -> Tuple[int, Optional[str]]:
    """批量标记通知为已读流程"""
    queryset = get_user_notifications_action(user)
    updated = bulk_mark_notifications_read_action(notification_ids, queryset)
    return updated, None


def filter_notifications_flow(
    category: Optional[str] = None,
    status: Optional[str] = None,
    is_read: Optional[bool] = None,
) -> QuerySet:
    """过滤通知流程"""
    queryset = Notification.objects.select_related("recipient").order_by("-created")
    if category:
        queryset = queryset.filter(category=category)
    if status:
        queryset = queryset.filter(status=status)
    if is_read is not None:
        queryset = queryset.filter(is_read=is_read)
    return queryset


def get_admin_unread_count_flow() -> int:
    """获取管理员未读通知数量流程"""
    return Notification.objects.filter(is_read=False).count()


def get_notification_stats_flow() -> Dict:
    """获取通知统计流程"""
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


def create_notifications_flow(
    user: User,
    recipient_id: Optional[int],
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
            recipients = get_all_active_users_action()
        elif recipient_role == "管理员":
            recipients = get_staff_users_action()
        elif recipient_role == "用户":
            recipients = get_regular_users_action()
        else:
            return False, "无效的接收角色", None
        if not recipients:
            return False, "没有找到符合条件的接收用户", None
    elif recipient_id:
        try:
            recipients = [get_user_by_id_action(recipient_id)]
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
    created_notifications = bulk_create_notifications_action(notifications)

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


def send_notification_flow(user: User, notification_id: int, request) -> Tuple[bool, Optional[str], Optional[Notification]]:
    """发送通知流程"""
    can_manage, error_msg = can_manage_notifications_flow(user)
    if not can_manage:
        return False, error_msg, None

    try:
        notification = get_notification_action(notification_id)
    except Notification.DoesNotExist:
        return False, "通知不存在", None

    if notification.status != Notification.STATUS.pending:
        return False, f"通知状态为 {notification.status}，只能发送待发送状态的通知", None

    if notification.scheduled_for and notification.scheduled_for > timezone.now():
        return False, "计划发送时间未到，无法发送", None

    update_notification_status_action(notification, Notification.STATUS.sent)

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


def delete_notification_flow(user: User, notification_id: int, request) -> Tuple[bool, Optional[str]]:
    """删除通知流程"""
    can_manage, error_msg = can_manage_notifications_flow(user)
    if not can_manage:
        return False, error_msg

    try:
        notification = get_notification_action(notification_id)
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

    delete_notification_action(notification)
    return True, None

