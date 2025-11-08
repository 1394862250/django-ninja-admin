# Generated migration
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('file', models.FileField(upload_to='documents/%Y/%m/%d/', verbose_name='文件')),
                ('file_name', models.CharField(max_length=255, verbose_name='文件名称')),
                ('file_type', models.CharField(choices=[('avatar', '头像'), ('document', '文档'), ('image', '图片'), ('other', '其他')], default='other', max_length=20, verbose_name='文件类型')),
                ('file_size', models.IntegerField(default=0, verbose_name='文件大小（字节）')),
                ('content_type', models.CharField(default='application/octet-stream', max_length=100, verbose_name='内容类型')),
                ('status', models.CharField(choices=[('pending', '待处理'), ('approved', '已批准'), ('rejected', '已拒绝')], default='pending', max_length=20, verbose_name='审核状态')),
                ('review_notes', models.TextField(blank=True, null=True, verbose_name='审核备注')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_documents', to=settings.AUTH_USER_MODEL, verbose_name='审核人')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploaded_documents', to=settings.AUTH_USER_MODEL, verbose_name='上传用户')),
            ],
            options={
                'verbose_name': '文档上传',
                'verbose_name_plural': '文档上传',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='UserActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('activity_type', models.CharField(choices=[('login', '登录'), ('logout', '登出'), ('register', '注册'), ('profile_update', '资料更新'), ('password_change', '修改密码'), ('avatar_upload', '上传头像'), ('admin_action', '管理操作')], max_length=20, verbose_name='活动类型')),
                ('description', models.TextField(verbose_name='活动描述')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP地址')),
                ('user_agent', models.TextField(blank=True, null=True, verbose_name='用户代理')),
                ('metadata', models.JSONField(blank=True, null=True, verbose_name='元数据')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '用户活动',
                'verbose_name_plural': '用户活动',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='UserPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('permission_type', models.CharField(choices=[('user_management', '用户管理'), ('content_moderation', '内容管理'), ('system_admin', '系统管理'), ('api_access', 'API访问'), ('data_export', '数据导出'), ('bulk_operations', '批量操作')], max_length=30, verbose_name='权限类型')),
                ('granted', models.BooleanField(default=True, verbose_name='是否已授权')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='过期时间')),
                ('metadata', models.JSONField(blank=True, null=True, verbose_name='权限元数据')),
                ('granted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='granted_permissions', to=settings.AUTH_USER_MODEL, verbose_name='授权人')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='custom_permissions', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '用户权限',
                'verbose_name_plural': '用户权限',
                'unique_together': {('user', 'permission_type')},
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='电话号码')),
                ('bio', models.TextField(blank=True, null=True, verbose_name='个人简介')),
                ('location', models.CharField(blank=True, max_length=100, null=True, verbose_name='位置')),
                ('website', models.URLField(blank=True, null=True, verbose_name='个人网站')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='user_avatars', verbose_name='头像')),
                ('status', models.CharField(choices=[('active', '活跃'), ('inactive', '不活跃'), ('suspended', '被暂停')], default='active', max_length=20, verbose_name='账户状态')),
                ('login_count', models.IntegerField(default=0, verbose_name='登录次数')),
                ('last_activity', models.DateTimeField(auto_now=True, verbose_name='最后活动时间')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL, verbose_name='关联用户')),
            ],
            options={
                'verbose_name': '用户资料',
                'verbose_name_plural': '用户资料',
            },
        ),
    ]