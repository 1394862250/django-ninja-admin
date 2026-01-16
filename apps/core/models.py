"""核心数据模型基类，提供统一主键与审计字段。"""
import uuid
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """
    抽象基类：
    - 使用 UUID 作为主键，便于分布式与日志追踪
    - 统一的创建/更新时间
    - 软删除标记
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True
        ordering = ("-created_at",)

    def soft_delete(self, using=None):
        """软删除标记，不物理删除。"""
        self.is_deleted = True
        self.save(update_fields=["is_deleted", "updated_at"])


__all__ = ["BaseModel"]
