"""用户与账号相关模型定义（自定义用户 + 关联实体）。"""
from __future__ import annotations

import os
import uuid
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from model_utils import Choices

from apps.core.models import BaseModel


def user_avatar_path(instance, filename: str) -> str:
    """头像上传路径：user_avatars/user_<id>/<filename>。"""
    user_id = instance.user.id if hasattr(instance, "user") else uuid.uuid4()
    return f"user_avatars/user_{user_id}/{filename}"


class User(BaseModel, AbstractUser):
    """自定义用户模型，使用 UUID 主键并包含软删除标记。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        "用户名",
        max_length=150,
        unique=True,
        help_text="必填。150 个字符或更少，仅包含字母、数字和@/./+/-/_。",
        validators=[username_validator],
        error_messages={
            "unique": "具有该用户名的用户已存在。",
        },
    )
    email = models.EmailField("邮箱地址", blank=True)

    objects = UserManager()

    class Meta(BaseModel.Meta):
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self) -> str:
        return self.get_username()

    def soft_delete(self, using=None):
        """用户软删除时标记并停用。"""
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=["is_deleted", "is_active", "updated_at"])


class UserProfile(BaseModel):
    """用户资料扩展。"""

    GENDER_CHOICES = [
        ("male", "男"),
        ("female", "女"),
        ("other", "其他"),
        ("prefer_not_to_say", "不愿透露"),
    ]

    STATUS_CHOICES = [
        ("active", "活跃"),
        ("inactive", "不活跃"),
        ("suspended", "被暂停"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="关联用户",
    )
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="电话号码")
    nickname = models.CharField(max_length=50, blank=True, null=True, verbose_name="昵称")
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True, verbose_name="性别")
    birth_date = models.DateField(blank=True, null=True, verbose_name="出生日期")
    avatar = models.ImageField(upload_to=user_avatar_path, blank=True, null=True, verbose_name="头像")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active", verbose_name="账户状态")
    login_count = models.IntegerField(default=0, verbose_name="登录次数")
    last_activity = models.DateTimeField(default=timezone.now, verbose_name="最后活动时间")

    class Meta(BaseModel.Meta):
        verbose_name = "用户资料"
        verbose_name_plural = "用户资料"

    def __str__(self) -> str:
        return f"资料 - {self.user.username}"

    def update_login_stats(self) -> None:
        """更新登录次数与最后活动时间。"""
        self.login_count += 1
        self.last_activity = timezone.now()
        self.save(update_fields=["login_count", "last_activity", "updated_at"])

    def delete_avatar(self) -> None:
        """删除头像文件并清空字段。"""
        if self.avatar and hasattr(self.avatar, "path") and os.path.exists(self.avatar.path):
            os.remove(self.avatar.path)
        self.avatar = None
        self.save(update_fields=["avatar", "updated_at"])


class UserActivity(BaseModel):
    """用户活动记录。"""

    ACTIVITY_TYPES = Choices(
        ("login", "登录"),
        ("logout", "登出"),
        ("register", "注册"),
        ("profile_update", "资料更新"),
        ("password_change", "修改密码"),
        ("avatar_upload", "上传头像"),
        ("admin_action", "管理操作"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activities",
        verbose_name="用户",
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, verbose_name="活动类型")
    description = models.TextField(verbose_name="活动描述")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP地址")
    user_agent = models.TextField(blank=True, null=True, verbose_name="用户代理")
    metadata = models.JSONField(blank=True, null=True, verbose_name="元数据")

    class Meta(BaseModel.Meta):
        verbose_name = "用户活动"
        verbose_name_plural = "用户活动"

    def __str__(self) -> str:
        return f"{self.user.username} - {self.get_activity_type_display()}"


class DocumentUpload(BaseModel):
    """文档上传管理。"""

    DOCUMENT_TYPES = Choices(
        ("avatar", "头像"),
        ("document", "文档"),
        ("image", "图片"),
        ("other", "其他"),
    )

    DOCUMENT_STATUS = Choices(
        ("pending", "待处理"),
        ("approved", "已批准"),
        ("rejected", "已拒绝"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_documents",
        verbose_name="上传用户",
    )
    file = models.FileField(upload_to="documents/%Y/%m/%d/", verbose_name="文件")
    file_name = models.CharField(max_length=255, verbose_name="文件名称")
    file_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default="other", verbose_name="文件类型")
    file_size = models.IntegerField(default=0, verbose_name="文件大小（字节）")
    content_type = models.CharField(max_length=100, default="application/octet-stream", verbose_name="内容类型")
    status = models.CharField(max_length=20, choices=DOCUMENT_STATUS, default="pending", verbose_name="审核状态")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_documents",
        verbose_name="审核人",
    )
    review_notes = models.TextField(blank=True, null=True, verbose_name="审核备注")

    class Meta(BaseModel.Meta):
        verbose_name = "文档上传"
        verbose_name_plural = "文档上传"

    def __str__(self) -> str:
        return f"{self.user.username} - {self.file_name}"


class Role(BaseModel):
    """角色定义。"""

    code = models.CharField(max_length=50, unique=True, verbose_name="角色标识")
    name = models.CharField(max_length=100, verbose_name="角色名称")
    description = models.TextField(blank=True, null=True, verbose_name="描述")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    is_system = models.BooleanField(default=False, verbose_name="是否系统预置")

    class Meta(BaseModel.Meta):
        verbose_name = "角色"
        verbose_name_plural = "角色"

    def __str__(self) -> str:
        return self.name


class UserRole(BaseModel):
    """用户角色关联。"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_roles", verbose_name="用户")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles", verbose_name="角色")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    class Meta(BaseModel.Meta):
        verbose_name = "用户角色"
        verbose_name_plural = "用户角色"
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="unique_user_role"),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.role}"


__all__ = ["User", "UserProfile", "UserActivity", "DocumentUpload", "Role", "UserRole"]
