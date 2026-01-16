"""通知相关 API Schemas。"""
from typing import List, Optional, Literal
from uuid import UUID
from datetime import datetime

from ninja import Field, Schema, ModelSchema

from .model import Notification


class NotificationOut(ModelSchema):
    """通知输出 Schema"""

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
            "created_at",
            "updated_at",
        ]


class NotificationWithRecipientOut(NotificationOut):
    """带接收者信息的通知输出"""

    recipient_id: UUID
    recipient_username: str
    recipient_email: str


class NotificationFilterSchema(Schema):
    """通知过滤条件"""

    category: Optional[str] = Field(None, description="按类别过滤")
    status: Optional[str] = Field(None, description="按状态过滤")
    is_read: Optional[bool] = Field(None, description="按是否已读过滤")


class NotificationCreateSchema(Schema):
    """创建通知 Schema"""

    recipient_id: Optional[UUID] = Field(None, description="接收用户ID（单个用户时使用）")
    recipient_role: Optional[str] = Field(None, description="接收角色（all/管理员/用户）")
    title: str = Field(..., max_length=200, description="通知标题")
    body: str = Field(..., description="通知内容")
    category: str = Field(..., max_length=30, description="通知类别")
    priority: Optional[Literal["low", "medium", "high"]] = Field("medium", description="通知优先级")
    status: Optional[Literal["pending", "sent", "failed"]] = Field("pending", description="通知状态")
    scheduled_for: Optional[datetime] = Field(None, description="计划发送时间（可为空）")


class NotificationMarkReadBulkSchema(Schema):
    """批量标记已读 Schema"""

    notification_ids: List[UUID] = Field(..., min_items=1, description="通知ID列表")


class NotificationSeedSchema(Schema):
    """批量生成通知 Schema"""

    count: int = Field(10, ge=1, le=50, description="生成条数，最大 50")
    recipient_role: Optional[Literal["all", "管理员", "用户"]] = Field(
        None, description="接收角色；为空则随机选择单个用户"
    )
    priority: Optional[Literal["low", "medium", "high"]] = Field(
        None, description="指定优先级，不填则随机"
    )
    status: Optional[Literal["pending", "sent", "failed"]] = Field(
        None, description="指定状态，不填则随机"
    )


__all__ = [
    "NotificationOut",
    "NotificationWithRecipientOut",
    "NotificationFilterSchema",
    "NotificationCreateSchema",
    "NotificationMarkReadBulkSchema",
    "NotificationSeedSchema",
]
