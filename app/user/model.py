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

    def get_valid_roles(self):
        """获取用户的所有有效角色"""
        from django.utils import timezone
        now = timezone.now()
        return UserRole.objects.filter(
            user=self.user,
            is_active=True
        ).select_related('role').filter(
            role__is_active=True
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        )
    
    def has_role(self, role_code):
        """检查用户是否拥有指定角色"""
        return self.get_valid_roles().filter(role__code=role_code).exists()
    
    def has_permission(self, permission_code):
        """检查用户是否拥有指定权限"""
        # 超级用户拥有所有权限
        if self.user.is_superuser:
            return True
        
        # 检查用户角色中的权限
        user_roles = self.get_valid_roles()
        for user_role in user_roles:
            if user_role.role.has_permission(permission_code):
                return True
        
        return False
    
    def get_permissions(self):
        """获取用户的所有权限代码"""
        # 超级用户拥有所有权限
        if self.user.is_superuser:
            return Permission.objects.filter(is_active=True).values_list('code', flat=True)
        
        # 获取用户角色中的所有权限
        permissions = set()
        user_roles = self.get_valid_roles()
        for user_role in user_roles:
            role_permissions = user_role.role.permissions.filter(is_active=True).values_list('code', flat=True)
            permissions.update(role_permissions)
        
        return list(permissions)
    
    def assign_role(self, role_code, assigned_by=None, expires_at=None):
        """为用户分配角色"""
        try:
            role = Role.objects.get(code=role_code, is_active=True)
            user_role, created = UserRole.objects.update_or_create(
                user=self.user,
                role=role,
                defaults={
                    'is_active': True,
                    'assigned_by': assigned_by,
                    'expires_at': expires_at
                }
            )
            return user_role, created
        except Role.DoesNotExist:
            return None, False
    
    def remove_role(self, role_code):
        """移除用户角色"""
        try:
            role = Role.objects.get(code=role_code)
            user_role = UserRole.objects.get(user=self.user, role=role)
            user_role.delete()
            return True
        except (Role.DoesNotExist, UserRole.DoesNotExist):
            return False


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


class Permission(TimeStampedModel):
    """权限模型"""
    
    # 权限类型
    PERMISSION_TYPES = Choices(
        ('view', '查看'),
        ('add', '添加'),
        ('change', '修改'),
        ('delete', '删除'),
        ('execute', '执行'),
        ('admin', '管理'),
    )
    
    # 权限范围
    PERMISSION_SCOPES = Choices(
        ('system', '系统'),
        ('user', '用户'),
        ('role', '角色'),
        ('permission', '权限'),
        ('log', '日志'),
        ('notification', '通知'),
        ('content', '内容'),
        ('other', '其他'),
    )
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="权限名称"
    )
    
    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="权限代码"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="权限描述"
    )
    
    permission_type = models.CharField(
        max_length=20,
        choices=PERMISSION_TYPES,
        verbose_name="权限类型"
    )
    
    scope = models.CharField(
        max_length=20,
        choices=PERMISSION_SCOPES,
        verbose_name="权限范围"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否激活"
    )
    
    class Meta:
        verbose_name = "权限"
        verbose_name_plural = "权限"
        ordering = ['scope', 'permission_type', 'code']
        unique_together = ['code', 'permission_type', 'scope']
    
    def __str__(self):
        return f"{self.get_scope_display()} - {self.get_permission_type_display()} - {self.name}"


class Role(TimeStampedModel):
    """角色模型"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="角色名称"
    )
    
    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="角色代码"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="角色描述"
    )
    
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='roles',
        verbose_name="权限"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否激活"
    )
    
    is_system = models.BooleanField(
        default=False,
        verbose_name="是否系统角色"
    )
    
    class Meta:
        verbose_name = "角色"
        verbose_name_plural = "角色"
        ordering = ['is_system', 'name']
    
    def __str__(self):
        return f"{self.name} ({'系统' if self.is_system else '自定义'})"
    
    def has_permission(self, permission_code):
        """检查角色是否拥有指定权限"""
        return self.permissions.filter(code=permission_code, is_active=True).exists()
    
    def add_permission(self, permission_code):
        """添加权限"""
        try:
            permission = Permission.objects.get(code=permission_code, is_active=True)
            self.permissions.add(permission)
            return True
        except Permission.DoesNotExist:
            return False
    
    def remove_permission(self, permission_code):
        """移除权限"""
        try:
            permission = Permission.objects.get(code=permission_code)
            self.permissions.remove(permission)
            return True
        except Permission.DoesNotExist:
            return False


class UserRole(TimeStampedModel):
    """用户角色关联模型"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name="用户"
    )
    
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='role_users',
        verbose_name="角色"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否激活"
    )
    
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_roles',
        verbose_name="分配人"
    )
    
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="分配时间"
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="过期时间"
    )
    
    class Meta:
        verbose_name = "用户角色"
        verbose_name_plural = "用户角色"
        unique_together = ['user', 'role']
        ordering = ['-created']
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
    
    def is_expired(self):
        """检查角色是否已过期"""
        if self.expires_at is None:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """检查角色是否有效（激活且未过期）"""
        return self.is_active and not self.is_expired()

