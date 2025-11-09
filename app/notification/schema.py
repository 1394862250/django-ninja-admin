"""Schemas for notification APIs."""
from datetime import datetime
from typing import List, Optional

from ninja import Field, Schema


class NotificationFilterSchema(Schema):
    category: Optional[str] = Field(None, description="按类别过滤")
    status: Optional[str] = Field(None, description="按状态过滤")
    is_read: Optional[bool] = Field(None, description="按是否已读过滤")
    page: int = Field(1, ge=1, description="当前页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class NotificationOutSchema(Schema):
    id: int
    title: str
    body: str
    category: str
    priority: str
    status: str
    is_read: bool
    read_at: Optional[datetime]
    scheduled_for: Optional[datetime]
    metadata: Optional[dict]
    created: datetime

    model_config = {
        "from_attributes": True,
    }


class NotificationCreateSchema(Schema):
    recipient_id: int = Field(..., description="接收用户ID")
    title: str = Field(..., max_length=200, description="通知标题")
    body: str = Field(..., description="通知内容")
    category: str = Field(..., max_length=30, description="通知类别")
    priority: Optional[str] = Field("medium", description="通知优先级")
    status: Optional[str] = Field("pending", description="通知状态")
    scheduled_for: Optional[datetime] = Field(None, description="计划发送时间")
    metadata: Optional[dict] = Field(None, description="扩展数据")


class NotificationMarkReadBulkSchema(Schema):
    notification_ids: List[int] = Field(..., min_items=1, description="通知ID列表")
