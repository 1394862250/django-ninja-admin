"""
管理后台 Extra 控制器 - 纯 CRUD 接口自动暴露
使用 ninja-extra 减少重复代码
"""
from ninja_extra import (
    api_controller,
    http_get,
    http_put,
    ControllerBase
)
from ninja_extra.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
import psutil
import os
import markdown

from .permissions import IsStaffOrSuperuser
from .admin_schemas import UserUpdateSchema
from app.user.models import UserActivity
from app.utils.responses import success_response, error_response


@api_controller('/manage', tags=['管理后台'], permissions=[IsStaffOrSuperuser])
class AdminExtraController(ControllerBase):
    """管理后台纯查询/统计接口 - 资源型接口豁免 Flow/Action"""

    @http_get("/users/{user_id}", url_name='admin_user_detail')
    def get_user_detail(self, user_id: int):
        """用户详情 - 纯查询,无业务逻辑"""
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

    @http_put("/users/{user_id}", url_name='admin_update_user')
    def update_user(self, user_id: int, data: UserUpdateSchema):
        """更新用户 - 纯字段更新,无业务语义"""
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

    @http_get("/dashboard/charts", url_name='admin_dashboard_charts')
    def get_dashboard_charts(self, days: int = 30):
        """获取dashboard图表数据 - 纯统计查询"""
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

    @http_get("/system/info", url_name='admin_system_info')
    def get_system_info(self):
        """获取系统信息 - 纯系统资源查询"""
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

    @http_get("/readme", url_name='admin_readme')
    def get_readme(self):
        """获取README内容 - 纯文件读取"""
        readme_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'README.md'
        )
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            html_content = markdown.markdown(content)
            return success_response(data={'content': html_content}, message="获取README成功")

        return error_response(message="README文件不存在", status_code=404)
