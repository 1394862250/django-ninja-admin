"""
用户模型扩展
"""
from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
from django.conf import settings
from model_utils.models import TimeStampedModel
from model_utils import Choices
from imagekit.models import ProcessedImageField, ImageSpecField
from imagekit.processors import ResizeToFill
from guardian.shortcuts import assign_perm, get_perms_for_model
import os

# 头像上传路径
def user_avatar_path(instance, filename):
    # 文件将上传到 MEDIA_ROOT/user_avatars/user_<id>/<filename>
    return f'user_avatars/user_{instance.user.id}/{filename}'

class UserProfile(TimeStampedModel):
    """用户资料扩展"""
    
    # 基本信息
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name="关联用户"
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="电话号码"
    )
    bio = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="个人简介"
    )
    location = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="位置"
    )
    website = models.URLField(
        blank=True, 
        null=True, 
        verbose_name="个人网站"
    )
    
    # 头像相关
    avatar = ProcessedImageField(
        upload_to=user_avatar_path,
        blank=True,
        null=True,
        verbose_name="头像",
        processors=[ResizeToFill(300, 300)],
        format='JPEG',
        options={'quality': 90}
    )
    
    # ImageKit 自动生成缩略图
    avatar_thumbnail = ImageSpecField(
        source='avatar',
        processors=[ResizeToFill(100, 100)],
        format='JPEG',
        options={'quality': 90}
    )
    
    # 状态和统计
    STATUS_CHOICES = [
        ('active', '活跃'),
        ('inactive', '不活跃'),
        ('suspended', '被暂停'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="账户状态"
    )
    
    login_count = models.IntegerField(
        default=0,
        verbose_name="登录次数"
    )
    
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name="最后活动时间"
    )
    
    class Meta:
        verbose_name = "用户资料"
        verbose_name_plural = "用户资料"

    def __str__(self):
        return f"资料 - {self.user.username}"
    
    def update_login_count(self):
        """更新登录次数"""
        self.login_count += 1
        self.last_activity = timezone.now()
        self.save(update_fields=['login_count', 'last_activity'])


class UserActivity(TimeStampedModel):
    """用户活动记录"""
    
    ACTIVITY_TYPES = Choices(
        'login', '登录',
        'logout', '登出',
        'register', '注册',
        'profile_update', '资料更新',
        'password_change', '修改密码',
        'avatar_upload', '上传头像',
        'admin_action', '管理操作',
    )
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='activities',
        verbose_name="用户"
    )
    
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES,
        verbose_name="活动类型"
    )
    
    description = models.TextField(
        verbose_name="活动描述"
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True, 
        null=True, 
        verbose_name="IP地址"
    )
    
    user_agent = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="用户代理"
    )
    
    metadata = models.JSONField(
        blank=True, 
        null=True, 
        verbose_name="元数据"
    )

    class Meta:
        verbose_name = "用户活动"
        verbose_name_plural = "用户活动"
        ordering = ['-created']

    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()}"


class UserPermission(TimeStampedModel):
    """用户权限扩展"""
    
    PERMISSION_TYPES = Choices(
        'user_management', '用户管理',
        'content_moderation', '内容管理',
        'system_admin', '系统管理',
        'api_access', 'API访问',
        'data_export', '数据导出',
        'bulk_operations', '批量操作',
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='custom_permissions',
        verbose_name="用户"
    )
    
    permission_type = models.CharField(
        max_length=30,
        choices=PERMISSION_TYPES,
        verbose_name="权限类型"
    )
    
    granted = models.BooleanField(
        default=True,
        verbose_name="是否已授权"
    )
    
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_permissions',
        verbose_name="授权人"
    )
    
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="过期时间"
    )
    
    metadata = models.JSONField(
        blank=True,
        null=True,
        verbose_name="权限元数据"
    )

    class Meta:
        verbose_name = "用户权限"
        verbose_name_plural = "用户权限"
        unique_together = [
            ('user', 'permission_type')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_permission_type_display()}"
    
    @property
    def is_expired(self):
        """检查权限是否已过期"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class DocumentUpload(TimeStampedModel):
    """文档上传管理"""
    
    DOCUMENT_TYPES = Choices(
        'avatar', '头像',
        'document', '文档',
        'image', '图片',
        'other', '其他',
    )
    
    DOCUMENT_STATUS = Choices(
        'pending', '待处理',
        'approved', '已批准',
        'rejected', '已拒绝',
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_documents',
        verbose_name="上传用户"
    )
    
    file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        verbose_name="文件"
    )
    
    file_name = models.CharField(
        max_length=255,
        verbose_name="文件名称"
    )
    
    file_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        default='other',
        verbose_name="文件类型"
    )
    
    file_size = models.IntegerField(
        default=0,
        verbose_name="文件大小（字节）"
    )
    
    content_type = models.CharField(
        max_length=100,
        default='application/octet-stream',
        verbose_name="内容类型"
    )
    
    status = models.CharField(
        max_length=20,
        choices=DOCUMENT_STATUS,
        default='pending',
        verbose_name="审核状态"
    )
    
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_documents',
        verbose_name="审核人"
    )
    
    review_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="审核备注"
    )

    class Meta:
        verbose_name = "文档上传"
        verbose_name_plural = "文档上传"
        ordering = ['-created']

    def __str__(self):
        return f"{self.user.username} - {self.file_name}"


# 信号处理器

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """用户创建时自动创建用户资料"""
    if created:
        try:
            UserProfile.objects.create(user=instance)
        except Exception as e:
            # 如果创建失败，记录错误但不阻止用户创建
            print(f"创建用户资料失败: {e}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """用户更新时自动保存用户资料"""
    if hasattr(instance, 'profile'):
        try:
            instance.profile.save()
        except Exception as e:
            print(f"保存用户资料失败: {e}")


# 辅助函数

def check_user_permission(user, permission_type, content_type=None, object_id=None):
    """检查用户是否具有特定权限"""
    if user.is_superuser:
        return True
    
    # 检查标准Django权限
    if user.has_perm(permission_type):
        return True
    
    # 检查自定义权限
    try:
        user_perm = UserPermission.objects.get(
            user=user,
            permission_type=permission_type,
            granted=True
        )
        
        # 检查权限是否过期
        if user_perm.is_expired:
            return False
            
        return True
    except UserPermission.DoesNotExist:
        return False


def grant_user_permission(user, permission_type, granted_by=None, expires_at=None):
    """为用户授予权限"""
    permission, created = UserPermission.objects.get_or_create(
        user=user,
        permission_type=permission_type,
        defaults={
            'granted': True,
            'granted_by': granted_by,
            'expires_at': expires_at,
        }
    )
    
    if not created:
        permission.granted = True
        permission.granted_by = granted_by
        permission.expires_at = expires_at
        permission.save()
    
    return permission


def revoke_user_permission(user, permission_type):
    """撤销用户权限"""
    try:
        permission = UserPermission.objects.get(
            user=user,
            permission_type=permission_type
        )
        permission.granted = False
        permission.save()
        return True
    except UserPermission.DoesNotExist:
        return False