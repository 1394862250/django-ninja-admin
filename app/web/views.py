"""
Web应用视图 - 用于映射HTML模板
提供传统的Django视图功能，支持HTML页面渲染
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from app.user.model import Permission, Role
from app.utils.validators import permission_required

User = get_user_model()


def render_template(request, template_path: str, context: dict = None):
    """
    通用模板渲染函数
    
    Args:
        request: HTTP请求对象
        template_path: 模板路径（相对于templates目录）
        context: 模板上下文字典
    
    Returns:
        HttpResponse: 渲染后的HTML响应
    """
    if context is None:
        context = {}
    
    # 添加默认上下文
    context.setdefault('user', request.user)
    context.setdefault('is_authenticated', request.user.is_authenticated)
    
    return render(request, template_path, context)


# ===== 认证相关视图 =====

@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    登录页面视图
    """
    if request.user.is_authenticated:
        return redirect('web:user_home')
    
    return render_template(request, 'auth/login.html')


@require_http_methods(["GET", "POST"])
def register_view(request):
    """
    注册页面视图
    """
    if request.user.is_authenticated:
        return redirect('web:user_home')
    
    return render_template(request, 'auth/register.html')


# ===== 用户相关视图 =====

@login_required
def user_home_view(request):
    """
    用户首页视图
    如果是管理员，重定向到管理后台
    """
    if request.user.is_staff or request.user.is_superuser:
        return redirect('web:admin_dashboard')
    
    context = {
        'page_title': '用户首页',
    }
    return render_template(request, 'user/home.html', context)


@login_required
def user_profile_view(request):
    """
    用户个人资料页面视图
    """
    context = {
        'page_title': '个人资料',
        'active_menu': 'profile',  # 设置活动菜单
    }
    return render_template(request, 'user/profile.html', context)


# ===== 管理相关视图 =====

@staff_member_required
def admin_dashboard_view(request):
    """
    管理后台首页视图
    """
    context = {
        'page_title': '管理后台',
        'active_menu': 'dashboard',  # 设置活动菜单
    }
    return render_template(request, 'manage/admin.html', context)


@staff_member_required
def user_management_view(request):
    """
    用户管理页面视图
    数据通过API动态加载，不在这里传递
    """
    context = {
        'page_title': '用户管理',
        'active_menu': 'users',  # 设置活动菜单
    }
    return render_template(request, 'manage/user_management.html', context)


@staff_member_required
def api_docs_view(request):
    """
    API文档页面视图
    使用iframe嵌入Django Ninja的Swagger UI文档
    """
    from django.http import HttpResponse
    response = render_template(request, 'manage/api_docs.html', {
        'page_title': 'API接口文档',
        'active_menu': 'api_docs',  # 设置活动菜单
    })
    # 确保允许iframe嵌入
    response['X-Frame-Options'] = 'SAMEORIGIN'
    return response


@staff_member_required
def notification_management_view(request):
    """
    通知管理页面视图
    显示通知列表和管理功能
    """
    context = {
        'page_title': '通知管理',
        'active_menu': 'notifications',  # 设置活动菜单
    }
    return render_template(request, 'manage/notification_management.html', context)


@staff_member_required
def notification_create_view(request):
    """
    通知发布页面视图
    创建新通知的表单页面
    """
    context = {
        'page_title': '发布通知',
        'active_menu': 'notifications',  # 设置活动菜单
    }
    return render_template(request, 'manage/notification_create.html', context)


@staff_member_required
def log_management_view(request):
    """
    日志管理页面视图
    显示系统日志列表和管理功能
    """
    context = {
        'page_title': '日志管理',
        'active_menu': 'logs',  # 设置活动菜单
    }
    return render_template(request, 'manage/log_management.html', context)


@login_required
@permission_required('role.view')
def role_management(request):
    """角色管理页面"""
    # 获取所有角色
    roles = Role.objects.prefetch_related('permissions').all()
    
    # 获取所有权限并按范围分组
    permissions = Permission.objects.filter(is_active=True).order_by('scope', 'permission_type', 'name')
    permissions_by_scope = {}
    for perm in permissions:
        if perm.scope not in permissions_by_scope:
            permissions_by_scope[perm.scope] = []
        permissions_by_scope[perm.scope].append(perm)
    
    # 获取所有权限类型
    permission_types = Permission.PERMISSION_TYPES
    
    # 准备角色数据，包括权限信息
    roles_data = []
    for role in roles:
        role_permissions = []
        for perm in role.permissions.all():
            role_permissions.append({
                'id': perm.id,
                'name': perm.name,
                'code': perm.code,
                'permission_type': perm.permission_type,
                'scope': perm.scope,
                'is_active': perm.is_active,
            })
        
        roles_data.append({
            'id': role.id,
            'name': role.name,
            'code': role.code,
            'description': role.description,
            'is_active': role.is_active,
            'is_system': role.is_system,
            'created': role.created.strftime('%Y-%m-%d %H:%M:%S') if role.created else '',
            'modified': role.modified.strftime('%Y-%m-%d %H:%M:%S') if role.modified else '',
            'permissions': role_permissions,
        })
    
    context = {
        'roles': roles_data,
        'permissions_by_scope': permissions_by_scope,
        'permission_types': [choice[0] for choice in permission_types]
    }
    
    return render(request, 'manage/role_management.html', context)

# ===== 通用视图函数 =====

def index_view(request):
    """
    首页视图 - 根据用户状态重定向
    """
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('web:admin_dashboard')
        else:
            return redirect('web:user_home')
    else:
        return redirect('web:login')

