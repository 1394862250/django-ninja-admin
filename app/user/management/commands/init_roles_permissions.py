"""
初始化角色和权限管理命令
用于创建系统基本角色和权限
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from app.user.model import Permission, Role, UserRole
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = '初始化系统基本角色和权限'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新创建所有角色和权限',
        )
    
    def handle(self, *args, **options):
        force = options.get('force', False)
        
        with transaction.atomic():
            # 创建基本权限
            self.create_permissions(force)
            
            # 创建基本角色
            self.create_roles(force)
            
            # 为超级用户分配管理员角色
            self.assign_admin_role_to_superusers()
            
            self.stdout.write(self.style.SUCCESS('成功初始化角色和权限'))
    
    def create_permissions(self, force=False):
        """创建基本权限"""
        permissions_data = [
            # 系统权限
            {'name': '查看系统', 'code': 'system.view', 'permission_type': 'view', 'scope': 'system'},
            {'name': '管理系统', 'code': 'system.admin', 'permission_type': 'admin', 'scope': 'system'},
            
            # 用户权限
            {'name': '查看用户', 'code': 'user.view', 'permission_type': 'view', 'scope': 'user'},
            {'name': '添加用户', 'code': 'user.add', 'permission_type': 'add', 'scope': 'user'},
            {'name': '修改用户', 'code': 'user.change', 'permission_type': 'change', 'scope': 'user'},
            {'name': '删除用户', 'code': 'user.delete', 'permission_type': 'delete', 'scope': 'user'},
            {'name': '管理用户', 'code': 'user.admin', 'permission_type': 'admin', 'scope': 'user'},
            
            # 角色权限
            {'name': '查看角色', 'code': 'role.view', 'permission_type': 'view', 'scope': 'role'},
            {'name': '添加角色', 'code': 'role.add', 'permission_type': 'add', 'scope': 'role'},
            {'name': '修改角色', 'code': 'role.change', 'permission_type': 'change', 'scope': 'role'},
            {'name': '删除角色', 'code': 'role.delete', 'permission_type': 'delete', 'scope': 'role'},
            {'name': '管理角色', 'code': 'role.admin', 'permission_type': 'admin', 'scope': 'role'},
            
            # 权限权限
            {'name': '查看权限', 'code': 'permission.view', 'permission_type': 'view', 'scope': 'permission'},
            {'name': '添加权限', 'code': 'permission.add', 'permission_type': 'add', 'scope': 'permission'},
            {'name': '修改权限', 'code': 'permission.change', 'permission_type': 'change', 'scope': 'permission'},
            {'name': '删除权限', 'code': 'permission.delete', 'permission_type': 'delete', 'scope': 'permission'},
            {'name': '管理权限', 'code': 'permission.admin', 'permission_type': 'admin', 'scope': 'permission'},
            
            # 用户角色权限
            {'name': '查看用户角色', 'code': 'user_role.view', 'permission_type': 'view', 'scope': 'user'},
            {'name': '分配用户角色', 'code': 'user_role.add', 'permission_type': 'add', 'scope': 'user'},
            {'name': '修改用户角色', 'code': 'user_role.change', 'permission_type': 'change', 'scope': 'user'},
            {'name': '移除用户角色', 'code': 'user_role.delete', 'permission_type': 'delete', 'scope': 'user'},
            
            # 日志权限
            {'name': '查看日志', 'code': 'log.view', 'permission_type': 'view', 'scope': 'log'},
            {'name': '删除日志', 'code': 'log.delete', 'permission_type': 'delete', 'scope': 'log'},
            {'name': '管理日志', 'code': 'log.admin', 'permission_type': 'admin', 'scope': 'log'},
            
            # 通知权限
            {'name': '查看通知', 'code': 'notification.view', 'permission_type': 'view', 'scope': 'notification'},
            {'name': '发送通知', 'code': 'notification.add', 'permission_type': 'add', 'scope': 'notification'},
            {'name': '修改通知', 'code': 'notification.change', 'permission_type': 'change', 'scope': 'notification'},
            {'name': '删除通知', 'code': 'notification.delete', 'permission_type': 'delete', 'scope': 'notification'},
            {'name': '管理通知', 'code': 'notification.admin', 'permission_type': 'admin', 'scope': 'notification'},
        ]
        
        for perm_data in permissions_data:
            permission, created = Permission.objects.get_or_create(
                code=perm_data['code'],
                defaults=perm_data
            )
            
            if created:
                self.stdout.write(f'创建权限: {permission.name}')
            elif force:
                # 更新现有权限
                for key, value in perm_data.items():
                    if key != 'code':  # 不更新代码
                        setattr(permission, key, value)
                permission.save()
                self.stdout.write(f'更新权限: {permission.name}')
    
    def create_roles(self, force=False):
        """创建基本角色"""
        roles_data = [
            {
                'name': '超级管理员',
                'code': 'super_admin',
                'description': '系统超级管理员，拥有所有权限',
                'is_system': True,
                'permission_codes': [
                    'system.view', 'system.admin',
                    'user.view', 'user.add', 'user.change', 'user.delete', 'user.admin',
                    'role.view', 'role.add', 'role.change', 'role.delete', 'role.admin',
                    'permission.view', 'permission.add', 'permission.change', 'permission.delete', 'permission.admin',
                    'user_role.view', 'user_role.add', 'user_role.change', 'user_role.delete',
                    'log.view', 'log.delete', 'log.admin',
                    'notification.view', 'notification.add', 'notification.change', 'notification.delete', 'notification.admin',
                ]
            },
            {
                'name': '管理员',
                'code': 'admin',
                'description': '系统管理员，拥有大部分管理权限',
                'is_system': True,
                'permission_codes': [
                    'system.view',
                    'user.view', 'user.add', 'user.change',
                    'role.view',
                    'permission.view',
                    'user_role.view', 'user_role.add', 'user_role.change',
                    'log.view',
                    'notification.view', 'notification.add', 'notification.change',
                ]
            },
            {
                'name': '用户管理员',
                'code': 'user_manager',
                'description': '用户管理员，负责用户管理',
                'is_system': True,
                'permission_codes': [
                    'user.view', 'user.add', 'user.change',
                    'user_role.view', 'user_role.add', 'user_role.change',
                ]
            },
            {
                'name': '内容管理员',
                'code': 'content_manager',
                'description': '内容管理员，负责内容管理',
                'is_system': True,
                'permission_codes': [
                    'notification.view', 'notification.add', 'notification.change',
                ]
            },
            {
                'name': '审计员',
                'code': 'auditor',
                'description': '审计员，负责查看日志和审计',
                'is_system': True,
                'permission_codes': [
                    'system.view',
                    'user.view',
                    'role.view',
                    'permission.view',
                    'user_role.view',
                    'log.view', 'log.admin',
                    'notification.view',
                ]
            },
            {
                'name': '普通用户',
                'code': 'user',
                'description': '普通用户，拥有基本权限',
                'is_system': True,
                'permission_codes': [
                    'notification.view',
                ]
            },
        ]
        
        for role_data in roles_data:
            permission_codes = role_data.pop('permission_codes', [])
            
            role, created = Role.objects.get_or_create(
                code=role_data['code'],
                defaults=role_data
            )
            
            if created:
                # 添加权限
                permissions = Permission.objects.filter(code__in=permission_codes, is_active=True)
                role.permissions.add(*permissions)
                self.stdout.write(f'创建角色: {role.name}')
            elif force:
                # 更新现有角色
                for key, value in role_data.items():
                    if key != 'code':  # 不更新代码
                        setattr(role, key, value)
                role.save()
                
                # 更新权限
                role.permissions.clear()
                permissions = Permission.objects.filter(code__in=permission_codes, is_active=True)
                role.permissions.add(*permissions)
                self.stdout.write(f'更新角色: {role.name}')
    
    def assign_admin_role_to_superusers(self):
        """为超级用户分配管理员角色"""
        superusers = User.objects.filter(is_superuser=True)
        admin_role = Role.objects.get(code='super_admin')
        
        for user in superusers:
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=admin_role,
                defaults={
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(f'为超级用户 {user.username} 分配角色: {admin_role.name}')
