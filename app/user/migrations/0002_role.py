# Generated migration for role management
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='角色标识')),
                ('display_name', models.CharField(blank=True, max_length=150, null=True, verbose_name='显示名称')),
                ('description', models.TextField(blank=True, null=True, verbose_name='角色描述')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('metadata', models.JSONField(blank=True, null=True, verbose_name='角色元数据')),
                ('permissions', models.ManyToManyField(blank=True, related_name='ninja_roles', to='auth.permission', verbose_name='标准权限')),
            ],
            options={
                'verbose_name': '角色',
                'verbose_name_plural': '角色',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='RolePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('permission_type', models.CharField(choices=[('user_management', '用户管理'), ('content_moderation', '内容管理'), ('system_admin', '系统管理'), ('api_access', 'API访问'), ('data_export', '数据导出'), ('bulk_operations', '批量操作')], max_length=30, verbose_name='权限类型')),
                ('metadata', models.JSONField(blank=True, null=True, verbose_name='权限元数据')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='custom_permission_links', to='user.role', verbose_name='角色')),
            ],
            options={
                'verbose_name': '角色自定义权限',
                'verbose_name_plural': '角色自定义权限',
            },
        ),
        migrations.AddConstraint(
            model_name='rolepermission',
            constraint=models.UniqueConstraint(fields=('role', 'permission_type'), name='user_role_permission_unique'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='roles',
            field=models.ManyToManyField(blank=True, related_name='users', to='user.role', verbose_name='用户角色'),
        ),
    ]
