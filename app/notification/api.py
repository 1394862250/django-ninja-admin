"""Notification service API endpoints."""
from typing import Dict

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.http import JsonResponse
from django.utils import timezone
from ninja import Query, Router
from ninja.security import HttpBearer

from app.notification.model import Notification
from app.notification.schema import (
    NotificationCreateSchema,
    NotificationFilterSchema,
    NotificationMarkReadBulkSchema,
)
from app.utils.log_utils import log_notification_action, log_admin_action
from app.log.model import Log

User = get_user_model()


class AuthBearer(HttpBearer):
    """Basic bearer auth relying on Django session user."""

    def authenticate(self, request, token):  # pragma: no cover - simple pass-through
        return request.user.is_authenticated


def success_response(data=None, message="操作成功", status_code=200):
    """Return a unified success JsonResponse."""
    return JsonResponse(
        {
            "success": True,
            "message": message,
            "data": data,
        },
        status=status_code,
    )


def error_response(message="操作失败", status_code=400, data=None):
    """Return a unified error JsonResponse."""
    return JsonResponse(
        {
            "success": False,
            "message": message,
            "data": data,
        },
        status=status_code,
    )


def get_user_notifications_queryset(user) -> QuerySet[Notification]:
    """Return base queryset for a user's notifications."""
    return Notification.objects.filter(recipient=user).order_by("-created")


def serialize_notification(notification: Notification) -> Dict:
    """Serialize a notification instance into a dict."""
    return {
        "id": notification.id,
        "title": notification.title,
        "body": notification.body,
        "category": notification.category,
        "priority": notification.priority,
        "status": notification.status,
        "is_read": notification.is_read,
        "read_at": notification.read_at,
        "scheduled_for": notification.scheduled_for,
        "sent_role": notification.sent_role,
        "created": notification.created,
    }


api = Router(tags=["通知管理API"])
auth = AuthBearer()


@api.get("/notifications", auth=auth)
def list_notifications(request, filters: NotificationFilterSchema = Query(...)):
    """Return paginated notification list for current user."""
    user = request.user
    if not user.is_authenticated:
        return error_response("需要登录访问", status_code=401)

    queryset = get_user_notifications_queryset(user)

    if filters.category:
        queryset = queryset.filter(category=filters.category)
    if filters.status:
        queryset = queryset.filter(status=filters.status)
    if filters.is_read is not None:
        queryset = queryset.filter(is_read=filters.is_read)

    paginator = Paginator(queryset, filters.page_size)
    page_obj = paginator.get_page(filters.page)

    results = [serialize_notification(item) for item in page_obj]

    return success_response(
        data={
            "results": results,
            "pagination": {
                "page": filters.page,
                "page_size": filters.page_size,
                "total_count": paginator.count,
                "total_pages": paginator.num_pages,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            },
        }
    )


@api.get("/notifications/unread-count", auth=auth)
def unread_count(request):
    """Return unread notification count for current user."""
    user = request.user
    if not user.is_authenticated:
        return error_response("需要登录访问", status_code=401)

    count = get_user_notifications_queryset(user).filter(is_read=False).count()
    return success_response({"count": count})


@api.get("/notifications/unread", auth=auth)
def unread_notifications(request, page: int = 1, page_size: int = 20):
    """Get unread notifications for current user."""
    user = request.user
    if not user.is_authenticated:
        return error_response("需要登录访问", status_code=401)

    queryset = get_user_notifications_queryset(user).filter(is_read=False).order_by("-created")
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)

    results = [serialize_notification(item) for item in page_obj]

    return success_response(
        data={
            "results": results,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": paginator.count,
                "total_pages": paginator.num_pages,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            },
        }
    )


@api.post("/notifications/mark-read/{notification_id}", auth=auth)
def mark_notification_read(request, notification_id: int):
    """Mark a single notification as read."""
    user = request.user
    if not user.is_authenticated:
        return error_response("需要登录访问", status_code=401)

    try:
        notification = get_user_notifications_queryset(user).get(id=notification_id)
    except Notification.DoesNotExist:
        return error_response("通知不存在", status_code=404)

    notification.mark_read()
    return success_response(message="通知已标记为已读")


@api.post("/notifications/mark-read-bulk", auth=auth)
def mark_notifications_read_bulk(request, payload: NotificationMarkReadBulkSchema):
    """Bulk mark notifications as read."""
    user = request.user
    if not user.is_authenticated:
        return error_response("需要登录访问", status_code=401)

    queryset = get_user_notifications_queryset(user).filter(id__in=payload.notification_ids)
    updated = queryset.update(is_read=True, read_at=timezone.now())
    return success_response({"updated": updated}, message="批量标记成功")


@api.post("/notifications", auth=auth)
def create_notification(request, payload: NotificationCreateSchema):
    """Create a notification. Restricted to staff users. Supports role-based bulk creation."""
    user = request.user
    if not user.is_authenticated:
        return error_response("需要登录访问", status_code=401)
    if not (user.is_staff or user.is_superuser):
        log_notification_action(
            action="创建通知",
            message=f"用户 {user.username} 尝试创建通知失败：权限不足",
            level=Log.LEVEL.WARNING,
            user=user,
            request=request
        )
        return error_response("需要管理员权限", status_code=403)

    if payload.priority not in Notification.PRIORITY:
        return error_response("无效的通知优先级", status_code=400)
    if payload.status not in Notification.STATUS:
        return error_response("无效的通知状态", status_code=400)

    # 确定接收用户列表
    recipients = []
    
    if payload.recipient_role:
        # 按角色批量创建
        if payload.recipient_role == "all":
            # 全局：所有用户
            recipients = list(User.objects.filter(is_active=True))
        elif payload.recipient_role == "管理员":
            # 管理员：所有staff用户
            recipients = list(User.objects.filter(is_active=True, is_staff=True))
        elif payload.recipient_role == "用户":
            # 普通用户：非staff用户
            recipients = list(User.objects.filter(is_active=True, is_staff=False))
        else:
            return error_response("无效的接收角色", status_code=400)
    elif payload.recipient_id:
        # 单个用户
        try:
            recipient = User.objects.get(id=payload.recipient_id)
            recipients = [recipient]
        except User.DoesNotExist:
            return error_response("接收用户不存在", status_code=404)
    else:
        return error_response("必须指定接收用户ID或接收角色", status_code=400)

    if not recipients:
        return error_response("没有找到符合条件的接收用户", status_code=400)

    # 批量创建通知
    notifications = []
    sent_role = payload.recipient_role if payload.recipient_role else None
    
    for recipient in recipients:
        notification = Notification.objects.create(
            recipient=recipient,
            title=payload.title,
            body=payload.body,
            category=payload.category,
            priority=payload.priority,
            status=payload.status,
            scheduled_for=payload.scheduled_for,
            sent_role=sent_role,  # 存储发送角色
        )
        notifications.append(notification)

    # 记录创建通知日志
    log_notification_action(
        action="创建通知",
        message=f"用户 {user.username} 创建了 {len(notifications)} 条通知：{payload.title}",
        user=user,
        request=request,
        extra_data={
            "title": payload.title,
            "category": payload.category,
            "priority": payload.priority,
            "recipient_role": payload.recipient_role,
            "recipient_count": len(notifications)
        }
    )

    # 返回创建的通知列表
    data = [serialize_notification(n) for n in notifications]
    return success_response(
        data={"notifications": data, "count": len(notifications)},
        message=f"成功创建 {len(notifications)} 条通知",
        status_code=201
    )


@api.delete("/notifications/{notification_id}", auth=auth)
def delete_notification(request, notification_id: int):
    """Delete a notification belonging to the current user."""
    user = request.user
    if not user.is_authenticated:
        return error_response("需要登录访问", status_code=401)

    try:
        notification = get_user_notifications_queryset(user).get(id=notification_id)
    except Notification.DoesNotExist:
        return error_response("通知不存在", status_code=404)

    notification.delete()
    return success_response(message="通知已删除")


@api.get("/notifications/unread-count", auth=auth)
def admin_unread_count(request):
    """Return unread notification count for all users (any authenticated user can access)."""
    user = request.user
    if not user.is_authenticated:
        return error_response("需要登录访问", status_code=401)

    count = Notification.objects.filter(is_read=False).count()
    return success_response({"count": count})


@api.post("/manage/notifications/{notification_id}/send", auth=auth)
def send_notification(request, notification_id: int):
    """Send a pending notification (change status to sent)."""
    user = request.user
    if not user.is_authenticated:
        return error_response("需要登录访问", status_code=401)
    if not (user.is_staff or user.is_superuser):
        log_notification_action(
            action="发送通知",
            message=f"用户 {user.username} 尝试发送通知失败：权限不足",
            level=Log.LEVEL.WARNING,
            user=user,
            request=request
        )
        return error_response("需要管理员权限", status_code=403)

    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return error_response("通知不存在", status_code=404)

    if notification.status != Notification.STATUS.pending:
        return error_response(f"通知状态为 {notification.status}，只能发送待发送状态的通知", status_code=400)

    # 检查计划发送时间
    if notification.scheduled_for and notification.scheduled_for > timezone.now():
        return error_response("计划发送时间未到，无法发送", status_code=400)

    # 更新状态为已发送
    notification.status = Notification.STATUS.sent
    notification.save(update_fields=['status'])

    # 记录发送通知日志
    log_notification_action(
        action="发送通知",
        message=f"用户 {user.username} 发送了通知：{notification.title}",
        user=user,
        request=request,
        extra_data={
            "notification_id": notification.id,
            "title": notification.title,
            "recipient": notification.recipient.username if notification.recipient else None,
            "recipient_role": notification.sent_role
        }
    )

    data = serialize_notification(notification)
    return success_response(data, message="通知已发送")


@api.delete("/manage/notifications/{notification_id}", auth=auth)
def delete_notification_admin(request, notification_id: int):
    """Delete any notification (admin only)."""
    user = request.user
    if not user.is_authenticated:
        return error_response("需要登录访问", status_code=401)
    if not (user.is_staff or user.is_superuser):
        log_notification_action(
            action="删除通知",
            message=f"用户 {user.username} 尝试删除通知失败：权限不足",
            level=Log.LEVEL.WARNING,
            user=user,
            request=request
        )
        return error_response("需要管理员权限", status_code=403)

    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return error_response("通知不存在", status_code=404)

    # 记录删除通知日志
    log_notification_action(
        action="删除通知",
        message=f"用户 {user.username} 删除了通知：{notification.title}",
        user=user,
        request=request,
        extra_data={
            "notification_id": notification.id,
            "title": notification.title,
            "recipient": notification.recipient.username if notification.recipient else None,
            "status": notification.status
        }
    )

    notification.delete()
    return success_response(message="通知已删除")


@api.get("/manage/notifications", auth=auth)
def list_all_notifications(request, filters: NotificationFilterSchema = Query(...)):
    """Return all notifications for admin users."""
    user = request.user
    if not user.is_authenticated:
        return error_response("需要登录访问", status_code=401)
    if not (user.is_staff or user.is_superuser):
        return error_response("需要管理员权限", status_code=403)

    # 管理员可以查看所有通知
    queryset = Notification.objects.all().order_by("-created")

    if filters.category:
        queryset = queryset.filter(category=filters.category)
    if filters.status:
        queryset = queryset.filter(status=filters.status)
    if filters.is_read is not None:
        queryset = queryset.filter(is_read=filters.is_read)

    paginator = Paginator(queryset, filters.page_size)
    page_obj = paginator.get_page(filters.page)

    # 扩展序列化以包含接收用户信息
    results = []
    for item in page_obj:
        notification_data = serialize_notification(item)
        notification_data['recipient'] = {
            'id': item.recipient.id,
            'username': item.recipient.username,
            'email': item.recipient.email
        }
        results.append(notification_data)

    return success_response(
        data={
            "results": results,
            "pagination": {
                "page": filters.page,
                "page_size": filters.page_size,
                "total_count": paginator.count,
                "total_pages": paginator.num_pages,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            },
        }
    )