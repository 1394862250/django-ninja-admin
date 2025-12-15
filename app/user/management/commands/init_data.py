"""初始化默认设置"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from app.setting.models import SystemSetting
from app.user.models import UserProfile, Role, UserRole
from app.utils.log_utils import log_system_action

User = get_user_model()


class SettingDataInitializer:
    """系统设置数据初始化封装"""

    def __init__(self, stdout=None, style=None):
        self.stdout = stdout
        self.style = style
        self.created_count = 0
        self.updated_count = 0

    def log(self, message: str, level: str = 'info'):
        """统一日志输出"""
        if not self.stdout:
            return
        formatter = None
        if self.style:
            if level == 'success' and hasattr(self.style, 'SUCCESS'):
                formatter = self.style.SUCCESS
            elif level == 'warning' and hasattr(self.style, 'WARNING'):
                formatter = self.style.WARNING
            elif level == 'error' and hasattr(self.style, 'ERROR'):
                formatter = self.style.ERROR

        if formatter:
            self.stdout.write(formatter(message))
        else:
            self.stdout.write(message)

    @staticmethod
    def get_default_settings():
        """返回默认设置列表"""
        return [
            {
                'key': 'system.site_name',
                'name': '站点名称',
                'value_type': 'string',
                'category': 'system',
                'value': '测试站点',
                'default_value': '测试站点',
                'description': '网站的名称，显示在页面标题和导航栏中',
                'sort_order': 1,
            },
            {
                'key': 'system.site_description',
                'name': '站点描述',
                'value_type': 'string',
                'category': 'system',
                'value': '基于Django Ninja的后台管理系统',
                'default_value': '基于Django Ninja的后台管理系统',
                'description': '网站的简短描述',
                'sort_order': 2,
            },
            {
                'key': 'ui.items_per_page',
                'name': '每页显示数量',
                'value_type': 'integer',
                'category': 'ui',
                'value': '20',
                'default_value': '20',
                'description': '列表页面每页默认显示的条目数量',
                'sort_order': 3,
                'validation_rules': {
                    'min': 10,
                    'max': 100,
                    'required': True
                }
            },
            {
                'key': 'openai.api_url',
                'name': 'OpenAI接口地址',
                'value_type': 'url',
                'category': 'api',
                'value': 'https://api.openai.com/v1/chat/completions',
                'default_value': 'https://api.openai.com/v1/chat/completions',
                'description': 'OpenAI服务的基础URL',
                'sort_order': 10,
            },
            {
                'key': 'openai.api_key',
                'name': 'OpenAI API密钥',
                'value_type': 'string',
                'category': 'api',
                'value': '',
                'default_value': '',
                'description': '调用OpenAI接口使用的API Key',
                'sort_order': 11,
                'validation_rules': {
                    'min_length': 10,
                },
                'extra_options': {
                    'placeholder': 'sk-***'
                }
            },
            {
                'key': 'openai.model',
                'name': 'OpenAI模型',
                'value_type': 'string',
                'category': 'api',
                'value': 'gpt-4o-mini',
                'default_value': 'gpt-4o-mini',
                'description': '默认使用的OpenAI模型名称',
                'sort_order': 12,
                'extra_options': {
                    'placeholder': '例如：gpt-4o-mini'
                }
            },
            {
                'key': 'ui.auth_background',
                'name': '认证页背景图',
                'value_type': 'string',
                'category': 'ui',
                'value': '',
                'default_value': '',
                'description': '登录/注册页面通用背景图地址（留空则使用默认背景）',
                'sort_order': 20,
                'extra_options': {
                    'placeholder': '/media/backgrounds/auth.jpg',
                    'allow_upload': True,
                    'upload_hint': '支持图片文件，建议尺寸1920x1080，大小不超过5MB'
                }
            },
        ]

    def initialize(self):
        """执行初始化逻辑"""
        for setting_data in self.get_default_settings():
            _, created = SystemSetting.objects.update_or_create(
                key=setting_data['key'],
                defaults=setting_data
            )
            if created:
                self.created_count += 1
                self.log(f'创建设置: {setting_data["key"]}', level='success')
            else:
                self.updated_count += 1
                self.log(f'更新设置: {setting_data["key"]}', level='warning')

        total = self.created_count + self.updated_count
        summary = (
            f'\n初始化完成！\n'
            f'创建: {self.created_count} 项\n'
            f'更新: {self.updated_count} 项\n'
            f'总计: {total} 项设置'
        )
        self.log(summary, level='success')
        self.record_init_log()
        return self.created_count, self.updated_count, total

    def record_init_log(self):
        """写入系统日志"""
        try:
            log_system_action(
                action='setting_init',
                message=f'初始化系统设置完成，创建{self.created_count}项，更新{self.updated_count}项，共{self.created_count + self.updated_count}项',
                extra_data={
                    'created_count': self.created_count,
                    'updated_count': self.updated_count,
                    'total_count': self.created_count + self.updated_count,
                }
            )
        except Exception as exc:
            self.log(f'记录系统日志失败: {exc}', level='warning')


class UserDataInitializer:
    """用户数据初始化封装"""

    def __init__(self, stdout=None, style=None):
        self.stdout = stdout
        self.style = style
        self.created_count = 0
        self.updated_count = 0

    def log(self, message: str, level: str = 'info'):
        """统一日志输出"""
        if not self.stdout:
            return
        formatter = None
        if self.style:
            if level == 'success' and hasattr(self.style, 'SUCCESS'):
                formatter = self.style.SUCCESS
            elif level == 'warning' and hasattr(self.style, 'WARNING'):
                formatter = self.style.WARNING
            elif level == 'error' and hasattr(self.style, 'ERROR'):
                formatter = self.style.ERROR

        if formatter:
            self.stdout.write(formatter(message))
        else:
            self.stdout.write(message)

    @staticmethod
    def get_default_user_data():
        """返回默认用户数据"""
        return {
            'username': 'admin',
            'password': 'admin123',
            'email': 'admin@example.com',
            'first_name': '系统',
            'last_name': '管理员',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
            'profile': {
                'nickname': '管理员',
                'phone': '13800138000',
                'gender': 'male',
            }
        }

    def ensure_default_roles(self):
        """创建或获取系统预置角色"""
        admin_role, admin_created = Role.objects.get_or_create(
            code='super_admin',
            defaults={
                'name': '管理员',
                'description': '系统管理员，拥有大部分管理权限',
                'is_active': True,
                'is_system': True,
            }
        )
        if admin_created:
            self.log(f'创建角色: {admin_role.name}', level='success')

        user_role, user_created = Role.objects.get_or_create(
            code='user',
            defaults={
                'name': '用户',
                'description': '普通用户，拥有基本权限',
                'is_active': True,
                'is_system': False,
            }
        )
        if user_created:
            self.log(f'创建角色: {user_role.name}', level='success')

        return admin_role, user_role

    def initialize(self):
        """执行用户初始化逻辑"""
        user_data = self.get_default_user_data()
        password = user_data.pop('password')
        profile_data = user_data.pop('profile', {})

        # 创建或更新用户
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults=user_data
        )

        if created:
            # 设置密码
            user.set_password(password)
            user.save()
            self.created_count += 1
            self.log(f'创建用户: {user.username}', level='success')
        else:
            # 更新用户信息（但不修改密码）
            for key, value in user_data.items():
                setattr(user, key, value)
            user.save()
            self.updated_count += 1
            self.log(f'更新用户: {user.username} (密码保持不变)', level='warning')

        # 创建或更新用户资料
        profile, profile_created = UserProfile.objects.get_or_create(
            user=user,
            defaults=profile_data
        )
        if not profile_created:
            # 更新资料
            for key, value in profile_data.items():
                setattr(profile, key, value)
            profile.save()

        # 确保系统角色存在
        admin_role, user_role = self.ensure_default_roles()

        # 创建或更新用户角色关联
        user_role, role_created = UserRole.objects.get_or_create(
            user=user,
            role=admin_role,
            defaults={'is_active': True}
        )
        if role_created:
            self.log(f'为用户 {user.username} 分配角色: {admin_role.name}', level='success')

        total = self.created_count + self.updated_count
        summary = (
            f'\n用户初始化完成！\n'
            f'创建: {self.created_count} 个用户\n'
            f'更新: {self.updated_count} 个用户\n'
            f'总计: {total} 个用户'
        )
        self.log(summary, level='success')
        self.record_init_log(user)
        return self.created_count, self.updated_count, total

    def record_init_log(self, user):
        """写入系统日志"""
        try:
            log_system_action(
                action='user_init',
                message=f'初始化用户数据完成，创建用户: {user.username}',
                user=user,
                extra_data={
                    'username': user.username,
                    'email': user.email,
                    'created_count': self.created_count,
                    'updated_count': self.updated_count,
                }
            )
        except Exception as exc:
            self.log(f'记录系统日志失败: {exc}', level='warning')


class Command(BaseCommand):
    help = '初始化默认系统设置和用户数据'

    def handle(self, *args, **options):
        # 初始化系统设置
        setting_initializer = SettingDataInitializer(
            stdout=self.stdout,
            style=self.style
        )
        setting_initializer.initialize()

        # 初始化用户数据
        user_initializer = UserDataInitializer(
            stdout=self.stdout,
            style=self.style
        )
        user_initializer.initialize()

