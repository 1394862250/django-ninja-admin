"""
Web应用视图 - 用于映射HTML模板
提供传统的Django视图功能，支持HTML页面渲染
"""
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required


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

