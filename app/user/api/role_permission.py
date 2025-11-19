"""
角色和权限管理API接口
"""
from .base import BaseUserAPI, success_response, error_response
from app.user.schemas import (
    PermissionSchema, RoleSchema, UserRoleSchema,
    RoleCreateSchema, RoleUpdateSchema, UserRoleCreateSchema, UserRoleUpdateSchema,
    PermissionCreateSchema, PermissionUpdateSchema
)
from app.user.models import Permission, Role, UserRole
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from app.utils.validators import permission_required, role_required
from ninja import Router, Query
from typing import List, Optional
from pydantic import Field

User = get_user_model()

class RolePermissionAPI(BaseUserAPI):
    """角色和权限管理API"""
    
    def _setup_routes(self):
        # 权限管理路由
        @self.router.get("/permissions", response=List[PermissionSchema])
        def list_permissions(request, scope: Optional[str] = None, is_active: Optional[bool] = None):
            return self._list_permissions(request, scope, is_active)
        
        @self.router.get("/permissions/{permission_id}", response=PermissionSchema)
        def get_permission(request, permission_id: int):
            return self._get_permission(request, permission_id)
        
        @self.router.post("/permissions", response=PermissionSchema)
        def create_permission(request, data: PermissionCreateSchema):
            return self._create_permission(request, data)
        
        @self.router.put("/permissions/{permission_id}", response=PermissionSchema)
        def update_permission(request, permission_id: int, data: PermissionUpdateSchema):
            return self._update_permission(request, permission_id, data)
        
        @self.router.delete("/permissions/{permission_id}")
        def delete_permission(request, permission_id: int):
            return self._delete_permission(request, permission_id)
        
        # 角色管理路由
        @self.router.get("/roles", response=List[RoleSchema])
        def list_roles(request, is_active: Optional[bool] = None, is_system: Optional[bool] = None):
            return self._list_roles(request, is_active, is_system)
        
        @self.router.get("/roles/{role_id}", response=RoleSchema)
        def get_role(request, role_id: int):
            return self._get_role(request, role_id)
        
        @self.router.post("/roles", response=RoleSchema)
        def create_role(request, data: RoleCreateSchema):
            return self._create_role(request, data)
        
        @self.router.put("/roles/{role_id}", response=RoleSchema)
        def update_role(request, role_id: int, data: RoleUpdateSchema):
            return self._update_role(request, role_id, data)
        
        @self.router.delete("/roles/{role_id}")
        def delete_role(request, role_id: int):
            return self._delete_role(request, role_id)
        
        # 用户角色管理路由
        @self.router.get("/user-roles", response=List[UserRoleSchema])
        def list_user_roles(request, user_id: Optional[int] = None, role_id: Optional[int] = None):
            return self._list_user_roles(request, user_id, role_id)
        
        @self.router.get("/user-roles/{user_role_id}", response=UserRoleSchema)
        def get_user_role(request, user_role_id: int):
            return self._get_user_role(request, user_role_id)
        
        @self.router.post("/user-roles", response=UserRoleSchema)
        def assign_role_to_user(request, data: UserRoleCreateSchema):
            return self._assign_role_to_user(request, data)
        
        @self.router.put("/user-roles/{user_role_id}", response=UserRoleSchema)
        def update_user_role(request, user_role_id: int, data: UserRoleUpdateSchema):
            return self._update_user_role(request, user_role_id, data)
        
        @self.router.delete("/user-roles/{user_role_id}")
        def remove_role_from_user(request, user_role_id: int):
            return self._remove_role_from_user(request, user_role_id)
        
        # 用户权限查询路由
        @self.router.get("/users/{user_id}/permissions", response=List[str])
        def get_user_permissions(request, user_id: int):
            return self._get_user_permissions(request, user_id)
        
        @self.router.get("/users/{user_id}/roles", response=List[RoleSchema])
        def get_user_roles(request, user_id: int):
            return self._get_user_roles(request, user_id)
    
    @permission_required('permission.view')
    def _list_permissions(self, request, scope=None, is_active=None):
        """获取权限列表"""
        try:
            permissions = Permission.objects.all()
            
            if scope is not None:
                permissions = permissions.filter(scope=scope)
            
            if is_active is not None:
                permissions = permissions.filter(is_active=is_active)
            
            permissions = permissions.order_by('scope', 'permission_type', 'code')
            
            return success_response(
                data=list(permissions.values()),
                message="获取权限列表成功"
            )
        except Exception as exc:
            return error_response(
                message=f"获取权限列表失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('permission.view')
    def _get_permission(self, request, permission_id):
        """获取单个权限"""
        try:
            permission = Permission.objects.get(id=permission_id)
            
            return success_response(
                data={
                    'id': permission.id,
                    'name': permission.name,
                    'code': permission.code,
                    'description': permission.description,
                    'permission_type': permission.permission_type,
                    'scope': permission.scope,
                    'is_active': permission.is_active,
                },
                message="获取权限成功"
            )
        except Permission.DoesNotExist:
            return error_response(
                message="权限不存在",
                status_code=404
            )
        except Exception as exc:
            return error_response(
                message=f"获取权限失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('permission.add')
    def _create_permission(self, request, data):
        """创建权限"""
        try:
            # 检查权限代码是否已存在
            if Permission.objects.filter(code=data.code).exists():
                return error_response(
                    message="权限代码已存在",
                    status_code=400
                )
            
            # 创建权限
            permission = Permission.objects.create(
                name=data.name,
                code=data.code,
                description=data.description,
                permission_type=data.permission_type,
                scope=data.scope
            )
            
            return success_response(
                data={
                    'id': permission.id,
                    'name': permission.name,
                    'code': permission.code,
                    'description': permission.description,
                    'permission_type': permission.permission_type,
                    'scope': permission.scope,
                    'is_active': permission.is_active,
                },
                message="创建权限成功",
                status_code=201
            )
        except Exception as exc:
            return error_response(
                message=f"创建权限失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('permission.change')
    def _update_permission(self, request, permission_id, data):
        """更新权限"""
        try:
            permission = Permission.objects.get(id=permission_id)
            
            # 更新字段
            if data.name is not None:
                permission.name = data.name
            if data.description is not None:
                permission.description = data.description
            if data.is_active is not None:
                permission.is_active = data.is_active
            
            permission.save()
            
            return success_response(
                data={
                    'id': permission.id,
                    'name': permission.name,
                    'code': permission.code,
                    'description': permission.description,
                    'permission_type': permission.permission_type,
                    'scope': permission.scope,
                    'is_active': permission.is_active,
                },
                message="更新权限成功"
            )
        except Permission.DoesNotExist:
            return error_response(
                message="权限不存在",
                status_code=404
            )
        except Exception as exc:
            return error_response(
                message=f"更新权限失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('permission.delete')
    def _delete_permission(self, request, permission_id):
        """删除权限"""
        try:
            permission = Permission.objects.get(id=permission_id)
            
            # 检查是否有角色使用此权限
            if permission.roles.exists():
                return error_response(
                    message="无法删除权限，有角色正在使用此权限",
                    status_code=400
                )
            
            permission.delete()
            
            return success_response(
                message="删除权限成功"
            )
        except Permission.DoesNotExist:
            return error_response(
                message="权限不存在",
                status_code=404
            )
        except Exception as exc:
            return error_response(
                message=f"删除权限失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('role.view')
    def _list_roles(self, request, is_active=None, is_system=None):
        """获取角色列表"""
        try:
            roles = Role.objects.all()
            
            if is_active is not None:
                roles = roles.filter(is_active=is_active)
            
            if is_system is not None:
                roles = roles.filter(is_system=is_system)
            
            roles = roles.prefetch_related('permissions').order_by('is_system', 'name')
            
            result = []
            for role in roles:
                role_data = {
                    'id': role.id,
                    'name': role.name,
                    'code': role.code,
                    'description': role.description,
                    'is_active': role.is_active,
                    'is_system': role.is_system,
                    'permissions': list(role.permissions.values('id', 'name', 'code', 'permission_type', 'scope'))
                }
                result.append(role_data)
            
            return success_response(
                data=result,
                message="获取角色列表成功"
            )
        except Exception as exc:
            return error_response(
                message=f"获取角色列表失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('role.view')
    def _get_role(self, request, role_id):
        """获取单个角色"""
        try:
            role = Role.objects.prefetch_related('permissions').get(id=role_id)
            
            return success_response(
                data={
                    'id': role.id,
                    'name': role.name,
                    'code': role.code,
                    'description': role.description,
                    'is_active': role.is_active,
                    'is_system': role.is_system,
                    'permissions': list(role.permissions.values('id', 'name', 'code', 'permission_type', 'scope'))
                },
                message="获取角色成功"
            )
        except Role.DoesNotExist:
            return error_response(
                message="角色不存在",
                status_code=404
            )
        except Exception as exc:
            return error_response(
                message=f"获取角色失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('role.add')
    def _create_role(self, request, data):
        """创建角色"""
        try:
            # 检查角色代码是否已存在
            if Role.objects.filter(code=data.code).exists():
                return error_response(
                    message="角色代码已存在",
                    status_code=400
                )
            
            with transaction.atomic():
                # 创建角色
                role = Role.objects.create(
                    name=data.name,
                    code=data.code,
                    description=data.description
                )
                
                # 添加权限
                if data.permission_codes:
                    permissions = Permission.objects.filter(
                        code__in=data.permission_codes,
                        is_active=True
                    )
                    role.permissions.add(*permissions)
            
            return success_response(
                data={
                    'id': role.id,
                    'name': role.name,
                    'code': role.code,
                    'description': role.description,
                    'is_active': role.is_active,
                    'is_system': role.is_system,
                    'permissions': list(role.permissions.values('id', 'name', 'code', 'permission_type', 'scope'))
                },
                message="创建角色成功",
                status_code=201
            )
        except Exception as exc:
            return error_response(
                message=f"创建角色失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('role.change')
    def _update_role(self, request, role_id, data):
        """更新角色"""
        try:
            role = Role.objects.get(id=role_id)
            
            with transaction.atomic():
                # 更新字段
                if data.name is not None:
                    role.name = data.name
                if data.description is not None:
                    role.description = data.description
                if data.is_active is not None:
                    role.is_active = data.is_active
                
                # 更新权限
                if data.permission_codes is not None:
                    # 清除现有权限
                    role.permissions.clear()
                    # 添加新权限
                    if data.permission_codes:
                        permissions = Permission.objects.filter(
                            code__in=data.permission_codes,
                            is_active=True
                        )
                        role.permissions.add(*permissions)
                
                role.save()
            
            return success_response(
                data={
                    'id': role.id,
                    'name': role.name,
                    'code': role.code,
                    'description': role.description,
                    'is_active': role.is_active,
                    'is_system': role.is_system,
                    'permissions': list(role.permissions.values('id', 'name', 'code', 'permission_type', 'scope'))
                },
                message="更新角色成功"
            )
        except Role.DoesNotExist:
            return error_response(
                message="角色不存在",
                status_code=404
            )
        except Exception as exc:
            return error_response(
                message=f"更新角色失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('role.delete')
    def _delete_role(self, request, role_id):
        """删除角色"""
        try:
            role = Role.objects.get(id=role_id)
            
            # 检查是否有用户使用此角色
            if role.role_users.exists():
                return error_response(
                    message="无法删除角色，有用户正在使用此角色",
                    status_code=400
                )
            
            with transaction.atomic():
                # 清除权限关联
                role.permissions.clear()
                # 删除角色
                role.delete()
            
            return success_response(
                message="删除角色成功"
            )
        except Role.DoesNotExist:
            return error_response(
                message="角色不存在",
                status_code=404
            )
        except Exception as exc:
            return error_response(
                message=f"删除角色失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('user_role.view')
    def _list_user_roles(self, request, user_id=None, role_id=None):
        """获取用户角色列表"""
        try:
            user_roles = UserRole.objects.all()
            
            if user_id is not None:
                user_roles = user_roles.filter(user_id=user_id)
            
            if role_id is not None:
                user_roles = user_roles.filter(role_id=role_id)
            
            user_roles = user_roles.select_related('user', 'role', 'assigned_by').order_by('-created')
            
            result = []
            for user_role in user_roles:
                user_role_data = {
                    'id': user_role.id,
                    'user_id': user_role.user.id,
                    'username': user_role.user.username,
                    'role_id': user_role.role.id,
                    'role_name': user_role.role.name,
                    'role_code': user_role.role.code,
                    'is_active': user_role.is_active,
                    'assigned_by': user_role.assigned_by.username if user_role.assigned_by else None,
                    'assigned_at': user_role.assigned_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'expires_at': user_role.expires_at.strftime('%Y-%m-%d %H:%M:%S') if user_role.expires_at else None,
                }
                result.append(user_role_data)
            
            return success_response(
                data=result,
                message="获取用户角色列表成功"
            )
        except Exception as exc:
            return error_response(
                message=f"获取用户角色列表失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('user_role.view')
    def _get_user_role(self, request, user_role_id):
        """获取单个用户角色"""
        try:
            user_role = UserRole.objects.select_related('user', 'role', 'assigned_by').get(id=user_role_id)
            
            return success_response(
                data={
                    'id': user_role.id,
                    'user_id': user_role.user.id,
                    'username': user_role.user.username,
                    'role_id': user_role.role.id,
                    'role_name': user_role.role.name,
                    'role_code': user_role.role.code,
                    'is_active': user_role.is_active,
                    'assigned_by': user_role.assigned_by.username if user_role.assigned_by else None,
                    'assigned_at': user_role.assigned_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'expires_at': user_role.expires_at.strftime('%Y-%m-%d %H:%M:%S') if user_role.expires_at else None,
                },
                message="获取用户角色成功"
            )
        except UserRole.DoesNotExist:
            return error_response(
                message="用户角色不存在",
                status_code=404
            )
        except Exception as exc:
            return error_response(
                message=f"获取用户角色失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('user_role.add')
    def _assign_role_to_user(self, request, data):
        """为用户分配角色"""
        try:
            # 检查用户是否存在
            try:
                user = User.objects.get(id=data.user_id)
            except User.DoesNotExist:
                return error_response(
                    message="用户不存在",
                    status_code=404
                )
            
            # 检查角色是否存在
            try:
                role = Role.objects.get(code=data.role_code, is_active=True)
            except Role.DoesNotExist:
                return error_response(
                    message="角色不存在或已禁用",
                    status_code=404
                )
            
            # 检查是否已分配
            if UserRole.objects.filter(user=user, role=role).exists():
                return error_response(
                    message="用户已拥有此角色",
                    status_code=400
                )
            
            # 解析过期时间
            expires_at = None
            if data.expires_at:
                try:
                    expires_at = datetime.strptime(data.expires_at, '%Y-%m-%d %H:%M:%S')
                    if expires_at <= timezone.now():
                        return error_response(
                            message="过期时间必须是未来时间",
                            status_code=400
                        )
                except ValueError:
                    return error_response(
                        message="过期时间格式不正确，请使用 YYYY-MM-DD HH:MM:SS 格式",
                        status_code=400
                    )
            
            # 创建用户角色
            user_role = UserRole.objects.create(
                user=user,
                role=role,
                assigned_by=request.user,
                expires_at=expires_at
            )
            
            return success_response(
                data={
                    'id': user_role.id,
                    'user_id': user_role.user.id,
                    'username': user_role.user.username,
                    'role_id': user_role.role.id,
                    'role_name': user_role.role.name,
                    'role_code': user_role.role.code,
                    'is_active': user_role.is_active,
                    'assigned_by': user_role.assigned_by.username if user_role.assigned_by else None,
                    'assigned_at': user_role.assigned_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'expires_at': user_role.expires_at.strftime('%Y-%m-%d %H:%M:%S') if user_role.expires_at else None,
                },
                message="分配角色成功",
                status_code=201
            )
        except Exception as exc:
            return error_response(
                message=f"分配角色失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('user_role.change')
    def _update_user_role(self, request, user_role_id, data):
        """更新用户角色"""
        try:
            user_role = UserRole.objects.get(id=user_role_id)
            
            # 更新字段
            if data.is_active is not None:
                user_role.is_active = data.is_active
            
            if data.expires_at is not None:
                if data.expires_at:
                    try:
                        expires_at = datetime.strptime(data.expires_at, '%Y-%m-%d %H:%M:%S')
                        if expires_at <= timezone.now():
                            return error_response(
                                message="过期时间必须是未来时间",
                                status_code=400
                            )
                        user_role.expires_at = expires_at
                    except ValueError:
                        return error_response(
                            message="过期时间格式不正确，请使用 YYYY-MM-DD HH:MM:SS 格式",
                            status_code=400
                        )
                else:
                    user_role.expires_at = None
            
            user_role.save()
            
            return success_response(
                data={
                    'id': user_role.id,
                    'user_id': user_role.user.id,
                    'username': user_role.user.username,
                    'role_id': user_role.role.id,
                    'role_name': user_role.role.name,
                    'role_code': user_role.role.code,
                    'is_active': user_role.is_active,
                    'assigned_by': user_role.assigned_by.username if user_role.assigned_by else None,
                    'assigned_at': user_role.assigned_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'expires_at': user_role.expires_at.strftime('%Y-%m-%d %H:%M:%S') if user_role.expires_at else None,
                },
                message="更新用户角色成功"
            )
        except UserRole.DoesNotExist:
            return error_response(
                message="用户角色不存在",
                status_code=404
            )
        except Exception as exc:
            return error_response(
                message=f"更新用户角色失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('user_role.delete')
    def _remove_role_from_user(self, request, user_role_id):
        """移除用户角色"""
        try:
            user_role = UserRole.objects.get(id=user_role_id)
            user_role.delete()
            
            return success_response(
                message="移除用户角色成功"
            )
        except UserRole.DoesNotExist:
            return error_response(
                message="用户角色不存在",
                status_code=404
            )
        except Exception as exc:
            return error_response(
                message=f"移除用户角色失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('user.view')
    def _get_user_permissions(self, request, user_id):
        """获取用户的所有权限"""
        try:
            user = User.objects.get(id=user_id)
            
            try:
                profile = user.profile
                permissions = profile.get_permissions()
                
                return success_response(
                    data=permissions,
                    message="获取用户权限成功"
                )
            except Exception:
                return success_response(
                    data=[],
                    message="获取用户权限成功"
                )
        except User.DoesNotExist:
            return error_response(
                message="用户不存在",
                status_code=404
            )
        except Exception as exc:
            return error_response(
                message=f"获取用户权限失败: {str(exc)}",
                status_code=500
            )
    
    @permission_required('user.view')
    def _get_user_roles(self, request, user_id):
        """获取用户的所有角色"""
        try:
            user = User.objects.get(id=user_id)
            
            try:
                profile = user.profile
                user_roles = profile.get_valid_roles()
                
                result = []
                for user_role in user_roles:
                    role_data = {
                        'id': user_role.role.id,
                        'name': user_role.role.name,
                        'code': user_role.role.code,
                        'description': user_role.role.description,
                        'is_active': user_role.role.is_active,
                        'is_system': user_role.role.is_system,
                        'permissions': list(user_role.role.permissions.values('id', 'name', 'code', 'permission_type', 'scope'))
                    }
                    result.append(role_data)
                
                return success_response(
                    data=result,
                    message="获取用户角色成功"
                )
            except Exception:
                return success_response(
                    data=[],
                    message="获取用户角色成功"
                )
        except User.DoesNotExist:
            return error_response(
                message="用户不存在",
                status_code=404
            )
        except Exception as exc:
            return error_response(
                message=f"获取用户角色失败: {str(exc)}",
                status_code=500
            )
