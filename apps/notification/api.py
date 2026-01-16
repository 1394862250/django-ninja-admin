"""
    通知API
"""
from typing import Dict, List, Optional
from uuid import UUID
from ninja import Query
from ninja_extra import (
    ModelConfig,
    ModelControllerBase,
    ModelSchemaConfig,
    api_controller,
    route,
)
from ninja_extra.pagination import PageNumberPaginationExtra

from .model import Notification
from apps.core.api.permissions import IsAuthenticated, IsStaffOrSuperuser
from apps.core.utils.serializers import to_iso
from .services import (
    get_user_notifications_flow,
    get_unread_count_flow,
    get_unread_notifications_flow,
    mark_notification_read_flow,
    mark_notifications_read_bulk_flow,
    filter_notifications_flow,
    get_admin_unread_count_flow,
    get_notification_stats_flow,
    create_notifications_flow,
    send_notification_flow,
    delete_notification_flow,
)
from .schemas import (
    NotificationCreateSchema,
    NotificationFilterSchema,
    NotificationMarkReadBulkSchema,
    NotificationOut,
    NotificationWithRecipientOut,
    NotificationSeedSchema,
)
from apps.core.api.responses import ApiResponse


def success_response(data=None, message="操作成功", status_code=200):
    return ApiResponse(data=data, message=message, success=True, status_code=status_code).to_json_response()


def error_response(message="操作失败", status_code=400, data=None):
    return ApiResponse(data=data, message=message, success=False, status_code=status_code).to_json_response()


@api_controller("/notifications", tags=["通知管理"], permissions=[IsAuthenticated])
class NotificationController(ModelControllerBase):
    """通知控制器 - 重构版"""

    model_config = ModelConfig(
        model=Notification,
        allowed_routes=[],  # 使用自定义路由，关闭自动生成的 CRUD
        schema_config=ModelSchemaConfig(read_only_fields=["id", "created_at", "updated_at", "read_at"]),
    )

    def get_queryset(self):
        """默认查询集：调用 获取"""
        user = self.context.request.user if hasattr(self, 'context') and self.context.request.user.is_authenticated else None
        return get_user_notifications_flow(user) if user else Notification.objects.none()

    def update(self, *args, **kwargs):
        """禁用直接更新"""
        return error_response("不支持直接更新通知", status_code=405)

    def partial_update(self, *args, **kwargs):
        """禁用直接更新"""
        return error_response("不支持直接更新通知", status_code=405)

    # ==================== 用户接口 ====================

    @route.get("/unread-count")
    def unread_count(self):
        """获取未读通知数量"""
        user = self.context.request.user
        if not user.is_authenticated:
            return error_response("需要登录访问", status_code=401)
        count = get_unread_count_flow(user)
        return success_response({"count": count})

    @route.get("/unread")
    def unread_notifications(self, page: int = 1, page_size: int = 20):
        """获取未读通知列表"""
        user = self.context.request.user
        if not user.is_authenticated:
            return error_response("需要登录访问", status_code=401)
        queryset = get_unread_notifications_flow(user)

        # 使用 ninja-extra 内置分页
        paginator = PageNumberPaginationExtra(page_size)
        return paginator.paginate_queryset(queryset, self.context.request)

    @route.post("/mark-read/{notification_id}")
    def mark_notification_read(self, notification_id: UUID):
        """标记通知为已读 - 内部处理权限和业务逻辑"""
        user = self.context.request.user
        if not user.is_authenticated:
            return error_response("需要登录访问", status_code=401)
        success, error_msg, notification = mark_notification_read_flow(user, notification_id)
        if not success:
            return error_response(error_msg, status_code=404 if "不存在" in error_msg else 400)
        return success_response(message="通知已标记为已读")

    @route.post("/mark-read-bulk")
    def mark_notifications_read_bulk(self, payload: NotificationMarkReadBulkSchema):
        """批量标记通知为已读 - 内部处理权限和业务逻辑"""
        user = self.context.request.user
        if not user.is_authenticated:
            return error_response("需要登录访问", status_code=401)
        updated, error_msg = mark_notifications_read_bulk_flow(user, payload.notification_ids)
        if error_msg:
            return error_response(error_msg, status_code=400)
        return success_response({"updated": updated}, message="批量标记成功")

    # ==================== 管理员接口 ====================

    @route.get("/manage", permissions=[IsStaffOrSuperuser])
    def list_all_notifications(
        self,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        category: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        is_read: Optional[bool] = Query(None)
    ):
        """管理员:获取所有通知列表（带过滤）"""
        queryset = filter_notifications_flow(
            category=category,
            status=status,
            is_read=is_read,
        ).select_related('recipient')

        # 手动分页
        from django.core.paginator import Paginator
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        # 序列化数据
        items = []
        for notification in page_obj:
            items.append({
                "id": notification.id,
                "title": notification.title,
                "body": notification.body,
                "category": notification.category,
                "priority": notification.priority,
                "status": notification.status,
                "is_read": notification.is_read,
                "read_at": to_iso(notification.read_at),
                "scheduled_for": to_iso(notification.scheduled_for),
                "sent_role": notification.sent_role,
                "created": to_iso(notification.created_at) if hasattr(notification, "created_at") else to_iso(getattr(notification, "created", None)),
                "recipient_id": notification.recipient.id if notification.recipient else None,
                "recipient_username": notification.recipient.username if notification.recipient else None,
                "recipient_email": notification.recipient.email if notification.recipient else None,
            })

        return success_response({
            "results": items,
            "pagination": {
                "count": paginator.count,
                "page": page,
                "page_size": page_size,
                "total_pages": paginator.num_pages,
            }
        })

    @route.get("/manage/unread-count", permissions=[IsStaffOrSuperuser])
    def admin_unread_count(self):
        """管理员：获取未读通知数量"""
        count = get_admin_unread_count_flow()
        return success_response({"count": count})

    @route.get("/manage/stats", permissions=[IsStaffOrSuperuser])
    def admin_stats(self):
        """管理员：通知统计"""
        stats = get_notification_stats_flow()
        return success_response(stats)

    @route.post("/seed", permissions=[IsStaffOrSuperuser])
    def seed_notifications(self, payload: NotificationSeedSchema):
        """批量生成测试通知"""
        from .services import seed_notifications_service

        result = seed_notifications_service(
            self.context.request.user,
            count=payload.count,
            recipient_role=payload.recipient_role,
            priority=payload.priority,
            status=payload.status,
        )
        return success_response(result, message=f"已生成 {result.get('created', 0)} 条通知")

    @route.post("", response=Dict)
    def create(self, payload: NotificationCreateSchema):
        """创建通知 - 内部处理权限判断"""
        user = self.context.request.user
        if not user.is_authenticated:
            return error_response("需要登录访问", status_code=401)
        success, error_msg, notifications = create_notifications_flow(
            user=user,
            recipient_id=payload.recipient_id,
            recipient_role=payload.recipient_role,
            title=payload.title,
            body=payload.body,
            category=payload.category,
            priority=payload.priority,
            status=payload.status,
            scheduled_for=payload.scheduled_for,
            request=self.context.request,
        )
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 404 if "不存在" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)

        # 使用 Schema 序列化
        return success_response(
            data={"count": len(notifications)},
            message=f"成功创建 {len(notifications)} 条通知",
            status_code=201,
        )

    @route.post("/manage/{notification_id}/send", permissions=[IsStaffOrSuperuser])
    def send_notification(self, notification_id: UUID):
        """发送通知 - 内部处理权限判断"""
        user = self.context.request.user
        success, error_msg, notification = send_notification_flow(user, notification_id, self.context.request)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 404 if "不存在" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(message="通知已发送")

    @route.delete("/manage/{notification_id}", permissions=[IsStaffOrSuperuser])
    def delete(self, notification_id: UUID):
        """删除通知 - 内部处理权限判断"""
        user = self.context.request.user
        success, error_msg = delete_notification_flow(user, notification_id, self.context.request)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 404 if "不存在" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(message="通知已删除")
