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
        "metadata": notification.metadata,
        "created": notification.created,
    }


api = Router(tags=["Notification API"])
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
    """Create a notification. Restricted to staff users."""
    user = request.user
    if not user.is_authenticated:
        return error_response("需要登录访问", status_code=401)
    if not (user.is_staff or user.is_superuser):
        return error_response("需要管理员权限", status_code=403)

    try:
        recipient = User.objects.get(id=payload.recipient_id)
    except User.DoesNotExist:
        return error_response("接收用户不存在", status_code=404)

    if payload.priority not in Notification.PRIORITY:
        return error_response("无效的通知优先级", status_code=400)
    if payload.status not in Notification.STATUS:
        return error_response("无效的通知状态", status_code=400)

    notification = Notification.objects.create(
        recipient=recipient,
        title=payload.title,
        body=payload.body,
        category=payload.category,
        priority=payload.priority,
        status=payload.status,
        scheduled_for=payload.scheduled_for,
        metadata=payload.metadata,
    )

    data = serialize_notification(notification)
    return success_response(data, message="通知创建成功", status_code=201)


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
