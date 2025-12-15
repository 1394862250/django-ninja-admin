"""
用户模型扩展
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from model_utils.models import TimeStampedModel
from model_utils import Choices
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
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
    nickname = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="昵称"
    )
    GENDER_CHOICES = [
        ('male', '男'),
        ('female', '女'),
        ('other', '其他'),
        ('prefer_not_to_say', '不愿透露'),
    ]
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        verbose_name="性别"
    )
    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="出生日期"
    )
    
    # 头像字段 - 使用标准Django ImageField
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        blank=True,
        null=True,
        verbose_name="头像"
    )
    
    # 头像缩略图 - 不存储在数据库，只在访问时动态生成
    @property
    def avatar_thumbnail(self):
        """动态生成头像缩略图"""
        if not self.avatar:
            return None
        
        try:
            # 打开原始图片
            img = Image.open(self.avatar)
            
            # 转换为RGB模式（如果需要）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 创建缩略图 (100x100)
            img.thumbnail((100, 100), Image.Resampling.LANCZOS)
            
            # 保存到内存
            thumb_io = BytesIO()
            img.save(thumb_io, format='JPEG', quality=90, optimize=True)
            thumb_io.seek(0)
    
            # 创建新的图片文件
            thumb_name = f"thumb_{self.avatar.name.split('/')[-1]}"
            thumb_file = InMemoryUploadedFile(
                thumb_io,
                None,
                thumb_name,
                'image/jpeg',
                thumb_io.tell(),
                None
            )
            
            return thumb_file
        except Exception as e:
            print(f"缩略图生成失败: {e}")
            return None
    
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
    
    def generate_nickname(self):
        """生成随机昵称：用户{随机五位数字}"""
        import random
        random_number = random.randint(10000, 99999)
        return f"用户{random_number}"
    
    def save(self, *args, **kwargs):
        """保存时自动生成昵称（如果未设置）"""
        if not self.nickname or (isinstance(self.nickname, str) and not self.nickname.strip()):
            # 确保昵称唯一
            while True:
                nickname = self.generate_nickname()
                if not UserProfile.objects.filter(nickname=nickname).exclude(pk=self.pk if self.pk else None).exists():
                    self.nickname = nickname
                    break
        super().save(*args, **kwargs)
    
    def update_login_count(self):
        """更新登录次数"""
        self.login_count += 1
        self.last_activity = timezone.now()
        self.save(update_fields=['login_count', 'last_activity'])

    def delete_avatar(self):
        """删除头像文件"""
        if self.avatar:
            # 删除物理文件
            if os.path.exists(self.avatar.path):
                os.remove(self.avatar.path)
            self.avatar = None
            self.save()


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
