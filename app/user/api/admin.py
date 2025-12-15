"""
管理相关API接口
包含管理后台相关接口：dashboard、用户管理等
"""
from ninja import Router
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
import psutil
import os
import markdown

from .admin_schemas import AdminCreateUserSchema, UserUpdateSchema
from app.user.models import UserActivity, UserProfile
from app.user.flows.admin_flow import (
    get_admin_dashboard_flow,
    list_users_flow,
    create_user_flow,
    toggle_user_status_flow,
    delete_user_flow
)
from app.utils.responses import success_response, error_response


def create_admin_api_router():
    """创建管理API路由"""
    router = Router()

    @router.get("/manage/dashboard")
    def admin_dashboard(request):
        """管理后台首页"""
        result = get_admin_dashboard_flow(request)

        if not result.success:
            return error_response(message=result.message, status_code=403)

        return success_response(data=result.data, message=result.message)

    @router.get("/manage/dashboard/charts")
    def get_dashboard_charts(request, days: int = 30):
        """获取dashboard图表数据"""
        # 权限检查：必须是 staff 或 superuser
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return error_response(message="需要管理员权限", status_code=403)

        User = get_user_model()
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # 用户注册频率（按天统计）
        registration_data = defaultdict(int)
        users = User.objects.filter(date_joined__date__gte=start_date, date_joined__date__lte=end_date)
        for user in users:
            date_str = user.date_joined.date().strftime('%Y-%m-%d')
            registration_data[date_str] += 1

        # 生成完整的日期列表
        registration_dates = []
        registration_counts = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            registration_dates.append(date_str)
            registration_counts.append(registration_data[date_str])
            current_date += timedelta(days=1)

        # 用户活跃频率（按天统计登录活动）
        activity_data = defaultdict(int)
        activities = UserActivity.objects.filter(
            activity_type='login',
            created__date__gte=start_date,
            created__date__lte=end_date
        )
        for activity in activities:
            date_str = activity.created.date().strftime('%Y-%m-%d')
            activity_data[date_str] += 1

        # 生成完整的日期列表
        activity_dates = []
        activity_counts = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            activity_dates.append(date_str)
            activity_counts.append(activity_data[date_str])
            current_date += timedelta(days=1)

        # 平台用户量（累计）
        total_users_by_date = []
        current_date = start_date
        while current_date <= end_date:
            count = User.objects.filter(date_joined__date__lte=current_date).count()
            total_users_by_date.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': count
            })
            current_date += timedelta(days=1)

        return success_response(
            data={
                'registration': {
                    'dates': registration_dates,
                    'counts': registration_counts
                },
                'activity': {
                    'dates': activity_dates,
                    'counts': activity_counts
                },
                'total_users': {
                    'data': total_users_by_date
                }
            },
            message="获取图表数据成功"
        )

    @router.get("/manage/system/info")
    def get_system_info(request):
        """获取系统信息"""
        # 权限检查：必须是 staff 或 superuser
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return error_response(message="需要管理员权限", status_code=403)

        # 获取系统资源信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return success_response(
            data={
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'used': memory.used,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'percent': disk.percent
                }
            },
            message="获取系统信息成功"
        )

    @router.get("/manage/readme")
    def get_readme(request):
        """获取README内容"""
        # 权限检查：必须是 staff 或 superuser
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return error_response(message="需要管理员权限", status_code=403)

        readme_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'README.md')
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            html_content = markdown.markdown(content)
            return success_response(data={'content': html_content}, message="获取README成功")

        return error_response(message="README文件不存在", status_code=404)

    @router.get("/manage/users")
    def list_users(request, page: int = 1, page_size: int = 10, search=None):
        """用户列表"""
        result = list_users_flow(request, page, page_size, search)

        if not result.success:
            return error_response(message=result.message, status_code=403)

        return success_response(data=result.data, message=result.message)

    @router.get("/manage/users/{user_id}")
    def get_user_detail(request, user_id: int):
        """用户详情"""
        # 权限检查：必须是 staff 或 superuser
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return error_response(message="需要管理员权限", status_code=403)

        User = get_user_model()
        try:
            user = User.objects.select_related('profile').get(id=user_id)
        except User.DoesNotExist:
            return error_response(message="用户不存在", status_code=404)

        return success_response(
            data={
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
                'profile': {
                    'nickname': user.profile.nickname if hasattr(user, 'profile') else None,
                    'phone': user.profile.phone if hasattr(user, 'profile') else None,
                    'gender': user.profile.gender if hasattr(user, 'profile') else None,
                    'login_count': user.profile.login_count if hasattr(user, 'profile') else 0,
                }
            },
            message="获取用户详情成功"
        )

    @router.post("/manage/users")
    def create_user(request, data: AdminCreateUserSchema):
        """创建用户"""
        result = create_user_flow(
            request=request,
            username=data.username,
            email=data.email,
            password=data.password,
            is_staff=data.is_staff if hasattr(data, 'is_staff') else False,
            is_active=data.is_active if hasattr(data, 'is_active') else True
        )

        if not result.success:
            return error_response(message=result.message, status_code=400)

        return success_response(
            data={'user_id': result.user.id, 'username': result.user.username},
            message=result.message,
            status_code=201
        )

    @router.put("/manage/users/{user_id}")
    def update_user(request, user_id: int, data: UserUpdateSchema):
        """更新用户"""
        # 权限检查：必须是 staff 或 superuser
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return error_response(message="需要管理员权限", status_code=403)

        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response(message="用户不存在", status_code=404)

        # 更新用户信息
        if hasattr(data, 'email') and data.email:
            user.email = data.email
        if hasattr(data, 'is_staff') and data.is_staff is not None:
            user.is_staff = data.is_staff
        user.save()

        return success_response(message="用户信息已更新")

    @router.delete("/manage/users/{user_id}")
    def delete_user(request, user_id: int):
        """删除用户"""
        result = delete_user_flow(request, user_id)

        if not result.success:
            return error_response(message=result.message, status_code=403)

        return success_response(message=result.message)

    @router.post("/manage/users/{user_id}/toggle-status")
    def toggle_user_status(request, user_id: int):
        """切换用户激活状态"""
        result = toggle_user_status_flow(request, user_id)

        if not result.success:
            return error_response(message=result.message, status_code=400)

        return success_response(
            data={'is_active': result.is_active},
            message=result.message
        )

    return router
