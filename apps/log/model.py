"""日志模型"""
from django.conf import settings
from django.db import models
from model_utils import Choices

from apps.core.models import BaseModel


class Log(BaseModel):
    """系统操作日志模型"""

    LEVEL = Choices(
        ("DEBUG", "调试"),
        ("INFO", "信息"),
        ("WARNING", "警告"),
        ("ERROR", "错误"),
        ("CRITICAL", "严重"),
    )

    CATEGORY = Choices(
        ("auth", "认证"),
        ("user", "用户"),
        ("system", "系统"),
        ("api", "API"),
        ("admin", "管理"),
        ("notification", "通知"),
        ("other", "其他"),
    )

    level = models.CharField(
        "日志级别",
        max_length=10,
        choices=LEVEL,
        default=LEVEL.INFO,
        help_text="日志的严重程度"
    )
    category = models.CharField(
        "日志类别",
        max_length=20,
        choices=CATEGORY,
        default=CATEGORY.system,
        help_text="日志所属的功能模块"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="logs",
        verbose_name="操作用户",
        null=True,
        blank=True,
        help_text="执行操作的用户，可为空表示系统操作"
    )
    action = models.CharField(
        "操作动作",
        max_length=100,
        help_text="执行的具体操作，如登录、创建、删除等"
    )
    message = models.TextField(
        "日志消息",
        help_text="详细的日志描述信息"
    )
    ip_address = models.GenericIPAddressField(
        "IP地址",
        null=True,
        blank=True,
        help_text="操作来源的IP地址"
    )
    user_agent = models.TextField(
        "用户代理",
        blank=True,
        help_text="浏览器或客户端信息"
    )
    path = models.CharField(
        "请求路径",
        max_length=255,
        blank=True,
        help_text="请求的URL路径"
    )
    method = models.CharField(
        "请求方法",
        max_length=10,
        blank=True,
        help_text="HTTP请求方法，如GET、POST等"
    )
    status_code = models.IntegerField(
        "状态码",
        null=True,
        blank=True,
        help_text="HTTP响应状态码"
    )
    extra_data = models.JSONField(
        "额外数据",
        default=dict,
        blank=True,
        help_text="额外的结构化数据，如请求参数、响应数据等"
    )

    class Meta:
        verbose_name = "系统日志"
        verbose_name_plural = "系统日志"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["level", "created_at"]),
            models.Index(fields=["category", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"[{self.level}] {self.category} - {self.action} - {self.created_at}"
