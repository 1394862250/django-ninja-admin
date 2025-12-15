"""通知API - 重构版
符合架构约束：
1. API 层只负责参数解析与返回
2. 权限判断在 Flow 中
3. 使用 Schema 替代手写序列化
4. 分页逻辑使用 ninja-extra 内置
"""
from typing import Dict, List, Optional, Literal
from datetime import datetime
from ninja import Field, Query, Schema, ModelSchema
from ninja_extra import (
    ModelConfig,
    ModelControllerBase,
    ModelSchemaConfig,
    api_controller,
    route,
)
from ninja_extra.pagination import PageNumberPaginationExtra

from .model import Notification
from .permissions import IsAuthenticated, IsStaffOrSuperuser
from .flows.notification_flows import (
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
from app.utils.responses import ApiResponse


def success_response(data=None, message="操作成功", status_code=200):
    return ApiResponse(data=data, message=message, success=True, status_code=status_code).to_json_response()


def error_response(message="操作失败", status_code=400, data=None):
    return ApiResponse(data=data, message=message, success=False, status_code=status_code).to_json_response()


# Schema 定义
class NotificationOut(ModelSchema):
    """通知输出Schema"""
    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "body",
            "category",
            "priority",
            "status",
            "is_read",
            "read_at",
            "scheduled_for",
            "sent_role",
            "created",
        ]


class NotificationWithRecipientOut(NotificationOut):
    """带接收者信息的通知输出"""
    recipient_id: int
    recipient_username: str
    recipient_email: str


class NotificationFilterSchema(Schema):
    """通知过滤条件"""
    category: Optional[str] = Field(None, description="按类别过滤")
    status: Optional[str] = Field(None, description="按状态过滤")
    is_read: Optional[bool] = Field(None, description="按是否已读过滤")


class NotificationCreateSchema(Schema):
    """创建通知Schema"""
    recipient_id: Optional[int] = Field(None, description="接收用户ID（单个用户时使用）")
    recipient_role: Optional[str] = Field(None, description="接收角色（all/管理员/用户）")
    title: str = Field(..., max_length=200, description="通知标题")
    body: str = Field(..., description="通知内容")
    category: str = Field(..., max_length=30, description="通知类别")
    priority: Optional[Literal["low", "medium", "high"]] = Field("medium", description="通知优先级")
    status: Optional[Literal["pending", "sent", "failed"]] = Field("pending", description="通知状态")
    scheduled_for: Optional[datetime] = Field(None, description="计划发送时间（可为空）")


class NotificationMarkReadBulkSchema(Schema):
    """批量标记已读Schema"""
    notification_ids: List[int] = Field(..., min_items=1, description="通知ID列表")


@api_controller("/notifications", tags=["通知管理"], permissions=[IsAuthenticated])
class NotificationController(ModelControllerBase):
    """通知控制器 - 重构版"""

    model_config = ModelConfig(
        model=Notification,
        schema_config=ModelSchemaConfig(read_only_fields=["id", "created", "modified", "read_at"]),
        pagination_class=PageNumberPaginationExtra,
    )

    def get_queryset(self):
        """默认查询集：调用 Flow 获取"""
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
    def mark_notification_read(self, notification_id: int):
        """标记通知为已读 - Flow 内部处理权限和业务逻辑"""
        user = self.context.request.user
        if not user.is_authenticated:
            return error_response("需要登录访问", status_code=401)
        success, error_msg, notification = mark_notification_read_flow(user, notification_id)
        if not success:
            return error_response(error_msg, status_code=404 if "不存在" in error_msg else 400)
        return success_response(message="通知已标记为已读")

    @route.post("/mark-read-bulk")
    def mark_notifications_read_bulk(self, payload: NotificationMarkReadBulkSchema):
        """批量标记通知为已读 - Flow 内部处理权限和业务逻辑"""
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
                "read_at": notification.read_at.isoformat() if notification.read_at else None,
                "scheduled_for": notification.scheduled_for.isoformat() if notification.scheduled_for else None,
                "sent_role": notification.sent_role,
                "created": notification.created.isoformat() if notification.created else None,
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

    @route.post("", response=Dict)
    def create(self, payload: NotificationCreateSchema):
        """创建通知 - Flow 内部处理权限判断"""
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
    def send_notification(self, notification_id: int):
        """发送通知 - Flow 内部处理权限判断"""
        user = self.context.request.user
        success, error_msg, notification = send_notification_flow(user, notification_id, self.context.request)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 404 if "不存在" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(message="通知已发送")

    @route.delete("/manage/{notification_id}", permissions=[IsStaffOrSuperuser])
    def delete(self, notification_id: int):
        """删除通知 - Flow 内部处理权限判断"""
        user = self.context.request.user
        success, error_msg = delete_notification_flow(user, notification_id, self.context.request)
        if not success:
            status_code = 401 if "需要登录访问" in error_msg else (403 if "需要管理员权限" in error_msg else 404 if "不存在" in error_msg else 400)
            return error_response(error_msg, status_code=status_code)
        return success_response(message="通知已删除")
