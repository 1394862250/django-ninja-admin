"""Notification models."""
from django.conf import settings
from django.db import models
from model_utils import Choices

from apps.core.models import BaseModel


class Notification(BaseModel):
    """Represents a notification for a user."""

    STATUS = Choices(
        ("pending", "待发送"),
        ("sent", "已发送"),
        ("failed", "发送失败"),
    )

    PRIORITY = Choices(
        ("low", "低"),
        ("medium", "中"),
        ("high", "高"),
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="接收用户",
    )
    title = models.CharField("标题", max_length=200)
    body = models.TextField("内容")
    category = models.CharField("类别", max_length=30)
    priority = models.CharField(
        "优先级",
        max_length=10,
        choices=PRIORITY,
        default=PRIORITY.medium,
    )
    status = models.CharField(
        "状态",
        max_length=10,
        choices=STATUS,
        default=STATUS.pending,
    )
    is_read = models.BooleanField("是否已读", default=False)
    read_at = models.DateTimeField("阅读时间", blank=True, null=True)
    scheduled_for = models.DateTimeField("计划发送时间", blank=True, null=True)
    sent_role = models.CharField("发送角色", max_length=20, blank=True, null=True, help_text="按角色发送时的角色标识（all/管理员/用户）")

    class Meta:
        verbose_name = "通知"
        verbose_name_plural = "通知"
        ordering = ("-created_at",)

    def mark_read(self):
        """Mark notification as read."""
        if not self.is_read:
            from django.utils import timezone

            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    def __str__(self) -> str:  # pragma: no cover - human readable repr
        return f"通知: {self.title} -> {self.recipient}"
