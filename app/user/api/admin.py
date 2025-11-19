"""
管理相关API接口
包含9个接口：dashboard、用户管理、系统信息等
"""

from .base import BaseUserAPI, success_response, error_response
from app.user.schemas import AdminCreateUserSchema, UserUpdateSchema
from app.user.models import UserActivity, UserProfile
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
import psutil
import os
import time
import markdown
import re
from app.utils.log_utils import log_admin_action, log_user_action
from app.log.model import Log

class AdminAPI(BaseUserAPI):
    """管理相关API"""
    
    def _setup_routes(self):
        @self.router.get("/manage/dashboard")
        def admin_dashboard(request):
            return self._admin_dashboard(request)
        
        @self.router.get("/manage/dashboard/charts")
        def get_dashboard_charts(request, days: int = 30):
            return self._get_dashboard_charts(request, days)
        
        @self.router.get("/manage/system/info")
        def get_system_info(request):
            return self._get_system_info(request)
        
        @self.router.get("/manage/readme")
        def get_readme(request):
            return self._get_readme(request)
        
        @self.router.get("/manage/users")
        def list_users(request, page: int = 1, page_size: int = 10, search=None):
            return self._list_users(request, page, page_size, search)
        
        @self.router.get("/manage/users/{user_id}")
        def get_user_detail(request, user_id: int):
            return self._get_user_detail(request, user_id)
        
        @self.router.post("/manage/users")
        def create_user(request, data: AdminCreateUserSchema):
            return self._create_user(request, data)
        
        @self.router.put("/manage/users/{user_id}")
        def update_user(request, user_id: int, data: UserUpdateSchema):
            return self._update_user(request, user_id, data)
        
        @self.router.delete("/manage/users/{user_id}")
        def delete_user(request, user_id: int):
            return self._delete_user(request, user_id)
        
        @self.router.post("/manage/users/{user_id}/toggle-status")
        def toggle_user_status(request, user_id: int):
            return self._toggle_user_status(request, user_id)
    
    def _admin_dashboard(self, request):
        """管理后台首页"""
        try:
            # 检查管理员权限
            admin_check = self.check_admin_permission(request)
            if admin_check:
                return admin_check
            
            # 获取统计数据
            User = get_user_model()
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            staff_users = User.objects.filter(is_staff=True).count()
            new_users_today = User.objects.filter(date_joined__date=timezone.now().date()).count()
            
            # 活动统计
            activities_today = UserActivity.objects.filter(created__date=timezone.now().date()).count()
            logins_today = UserActivity.objects.filter(
                activity_type='login', 
                created__date=timezone.now().date()
            ).count()
            
            return success_response(
                data={
                    'total_users': total_users,
                    'active_users': active_users,
                    'staff_users': staff_users,
                    'new_users_today': new_users_today,
                    'activities_today': activities_today,
                    'logins_today': logins_today,
                    'regular_users': total_users - staff_users
                },
                message="获取管理数据成功"
            )
            
        except Exception as exc:
            return error_response(
                message=f"获取管理数据失败: {str(exc)}",
                status_code=500
            )
    
    def _get_dashboard_charts(self, request, days: int = 30):
        """获取dashboard图表数据"""
        try:
            # 检查管理员权限
            admin_check = self.check_admin_permission(request)
            if admin_check:
                return admin_check
            
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
            
        except Exception as exc:
            return error_response(
                message=f"获取图表数据失败: {str(exc)}",
                status_code=500
            )
    
    def _get_system_info(self, request):
        """获取系统信息"""
        try:
            # 检查管理员权限
            admin_check = self.check_admin_permission(request)
            if admin_check:
                return admin_check
            
            # 获取内存信息
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / (1024 * 1024)
            memory_total_mb = memory.total / (1024 * 1024)
            memory_percent = memory.percent
            
            # 获取进程信息（Django进程）
            process = psutil.Process(os.getpid())
            process_memory_mb = process.memory_info().rss / (1024 * 1024)
            
            # 获取系统运行时长（从进程创建时间计算）
            process_create_time = process.create_time()
            uptime_seconds = time.time() - process_create_time
            
            # 格式化运行时长
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)
            
            uptime_str = f"{days}天 {hours}小时 {minutes}分钟 {seconds}秒"
            
            return success_response(
                data={
                    'memory': {
                        'used_mb': round(memory_used_mb, 2),
                        'total_mb': round(memory_total_mb, 2),
                        'percent': memory_percent,
                        'process_mb': round(process_memory_mb, 2)
                    },
                    'uptime': {
                        'seconds': int(uptime_seconds),
                        'formatted': uptime_str,
                        'days': days,
                        'hours': hours,
                        'minutes': minutes,
                        'seconds_remainder': seconds
                    }
                },
                message="获取系统信息成功"
            )
            
        except Exception as exc:
            return error_response(
                message=f"获取系统信息失败: {str(exc)}",
                status_code=500
            )
    
    def _get_readme(self, request):
        """获取README.md内容并转换为HTML"""
        try:
            # 检查管理员权限
            admin_check = self.check_admin_permission(request)
            if admin_check:
                return admin_check
            
            # 读取README.md文件
            readme_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'README.md')
            
            if not os.path.exists(readme_path):
                return error_response(
                    message="README.md文件不存在",
                    status_code=404
                )
            
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            
            # 转换为HTML
            html_content = markdown.markdown(readme_content, extensions=['extra', 'codehilite'])
            
            return success_response(
                data={
                    'html': html_content,
                    'raw': readme_content
                },
                message="获取README成功"
            )
            
        except Exception as exc:
            return error_response(
                message=f"获取README失败: {str(exc)}",
                status_code=500
            )
    
    def _list_users(self, request, page: int = 1, page_size: int = 10, search=None):
        """用户管理列表"""
        try:
            # 检查管理员权限
            admin_check = self.check_admin_permission(request)
            if admin_check:
                return admin_check
            
            User = get_user_model()
            
            # 查询用户
            users_query = User.objects.all().order_by('-date_joined')
            
            if search:
                users_query = users_query.filter(
                    Q(username__icontains=search) |
                    Q(email__icontains=search)
                )
            
            # 分页
            paginator = Paginator(users_query, page_size)
            users_page = paginator.get_page(page)
            
            # 转换为字典列表
            users_data = []
            for user in users_page:
                profile = user.profile if hasattr(user, 'profile') else None
                users_data.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                    'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
                    'profile': {
                        'status': profile.status if profile else 'active',
                        'phone': profile.phone if profile and profile.phone else None,
                        'nickname': profile.nickname if profile and profile.nickname else None,
                        'gender': profile.gender if profile and profile.gender else None,
                        'login_count': profile.login_count if profile else 0,
                        'avatar': profile.avatar.url if profile and profile.avatar else None,
                    }
                })
            
            return success_response(
                data={
                    'users': users_data,
                    'page': page,
                    'page_size': page_size,
                    'total_count': paginator.count,
                    'total_pages': paginator.num_pages
                },
                message="获取用户列表成功"
            )
            
        except Exception as exc:
            return error_response(
                message=f"获取用户列表失败: {str(exc)}",
                status_code=500
            )
    
    def _get_user_detail(self, request, user_id: int):
        """获取用户详情"""
        try:
            # 检查管理员权限
            admin_check = self.check_admin_permission(request)
            if admin_check:
                return admin_check
            
            User = get_user_model()
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return error_response(
                    message="用户不存在",
                    status_code=404
                )
            
            profile = target_user.profile if hasattr(target_user, 'profile') else None
            
            return success_response(
                data={
                    'id': target_user.id,
                    'username': target_user.username,
                    'email': target_user.email,
                    'is_active': target_user.is_active,
                    'is_staff': target_user.is_staff,
                    'is_superuser': target_user.is_superuser,
                    'date_joined': target_user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                    'last_login': target_user.last_login.strftime('%Y-%m-%d %H:%M:%S') if target_user.last_login else None,
                    'profile': {
                        'phone': profile.phone if profile else None,
                        'nickname': profile.nickname if profile else None,
                        'gender': profile.gender if profile else None,
                        'birth_date': profile.birth_date.strftime('%Y-%m-%d') if profile and profile.birth_date else None,
                        'status': profile.status if profile else 'active',
                        'login_count': profile.login_count if profile else 0,
                        'last_activity': profile.last_activity.strftime('%Y-%m-%d %H:%M:%S') if profile and profile.last_activity else None,
                        'avatar': profile.avatar.url if profile and profile.avatar else None,
                        'avatar_thumbnail': profile.avatar.url if profile and profile.avatar else None,
                    }
                },
                message="获取用户详情成功"
            )
            
        except Exception as exc:
            return error_response(
                message=f"获取用户详情失败: {str(exc)}",
                status_code=500
            )
    
    def _create_user(self, request, data: AdminCreateUserSchema):
        """创建新用户"""
        try:
            # 检查管理员权限
            admin_check = self.check_admin_permission(request)
            if admin_check:
                return admin_check
            
            User = get_user_model()
            
            # 检查用户名是否已存在
            if User.objects.filter(username=data.username).exists():
                log_admin_action(
                    action="创建用户",
                    message=f"管理员 {request.user.username} 尝试创建用户失败：用户名已存在",
                    level=Log.LEVEL.WARNING,
                    user=request.user,
                    request=request,
                    extra_data={"username": data.username, "reason": "用户名已存在"}
                )
                return error_response(
                    message="用户名已存在",
                    status_code=400
                )
            
            # 检查邮箱是否已存在
            if User.objects.filter(email=data.email).exists():
                log_admin_action(
                    action="创建用户",
                    message=f"管理员 {request.user.username} 尝试创建用户失败：邮箱已被注册",
                    level=Log.LEVEL.WARNING,
                    user=request.user,
                    request=request,
                    extra_data={"username": data.username, "email": data.email, "reason": "邮箱已被注册"}
                )
                return error_response(
                    message="邮箱已被注册",
                    status_code=400
                )
            
            # 创建用户（UserProfile会通过信号处理器自动创建）
            user = User.objects.create_user(
                username=data.username,
                email=data.email,
                password=data.password,
                is_staff=data.is_staff if data.is_staff is not None else False,
                is_active=data.is_active if data.is_active is not None else True
            )
            
            # 刷新用户对象以确保 profile 已创建（信号处理器已执行）
            user.refresh_from_db()
            
            # 如果提供了昵称，更新用户资料
            if data.nickname:
                if hasattr(user, 'profile'):
                    profile = user.profile
                    profile.nickname = data.nickname
                    profile.save()
            
            # 记录创建用户成功日志
            log_admin_action(
                action="创建用户",
                message=f"管理员 {request.user.username} 创建了用户：{user.username}",
                user=request.user,
                request=request,
                extra_data={
                    "created_user_id": user.id,
                    "created_username": user.username,
                    "created_email": user.email,
                    "is_staff": user.is_staff
                }
            )
            
            return success_response(
                data={
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                    'profile': {
                        'nickname': user.profile.nickname if hasattr(user, 'profile') else None
                    }
                },
                message="用户创建成功",
                status_code=201
            )
            
        except Exception as exc:
            # 记录创建用户异常日志
            log_admin_action(
                action="创建用户",
                message=f"管理员 {request.user.username} 创建用户异常：{str(exc)}",
                level=Log.LEVEL.ERROR,
                user=request.user,
                request=request,
                extra_data={"username": data.username, "error": str(exc)}
            )
            return error_response(
                message=f"用户创建失败: {str(exc)}",
                status_code=400
            )
    
    def _update_user(self, request, user_id: int, data: UserUpdateSchema):
        """更新用户信息"""
        try:
            # 检查管理员权限
            admin_check = self.check_admin_permission(request)
            if admin_check:
                return admin_check
            
            User = get_user_model()
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                log_admin_action(
                    action="更新用户",
                    message=f"管理员 {request.user.username} 尝试更新用户失败：用户不存在",
                    level=Log.LEVEL.WARNING,
                    user=request.user,
                    request=request,
                    extra_data={"target_user_id": user_id, "reason": "用户不存在"}
                )
                return error_response(
                    message="用户不存在",
                    status_code=404
                )
            
            # 验证邮箱格式
            if data.email:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, data.email):
                    log_admin_action(
                        action="更新用户",
                        message=f"管理员 {request.user.username} 尝试更新用户失败：邮箱格式不正确",
                        level=Log.LEVEL.WARNING,
                        user=request.user,
                        request=request,
                        extra_data={"target_user_id": user_id, "email": data.email, "reason": "邮箱格式不正确"}
                    )
                    return error_response(
                        message="邮箱格式不正确",
                        status_code=400
                    )
            
            # 检查用户名是否已存在（排除当前用户）
            if data.username and User.objects.filter(username=data.username).exclude(id=user_id).exists():
                log_admin_action(
                    action="更新用户",
                    message=f"管理员 {request.user.username} 尝试更新用户失败：用户名已存在",
                    level=Log.LEVEL.WARNING,
                    user=request.user,
                    request=request,
                    extra_data={"target_user_id": user_id, "username": data.username, "reason": "用户名已存在"}
                )
                return error_response(
                    message="用户名已存在",
                    status_code=400
                )
            
            # 检查邮箱是否已存在（排除当前用户）
            if data.email and User.objects.filter(email=data.email).exclude(id=user_id).exists():
                log_admin_action(
                    action="更新用户",
                    message=f"管理员 {request.user.username} 尝试更新用户失败：邮箱已被注册",
                    level=Log.LEVEL.WARNING,
                    user=request.user,
                    request=request,
                    extra_data={"target_user_id": user_id, "email": data.email, "reason": "邮箱已被注册"}
                )
                return error_response(
                    message="邮箱已被注册",
                    status_code=400
                )
            
            # 更新用户信息
            if data.username:
                target_user.username = data.username
            if data.email:
                target_user.email = data.email
            if data.is_active is not None:
                target_user.is_active = data.is_active
            if data.is_staff is not None:
                target_user.is_staff = data.is_staff
            if data.password:
                target_user.set_password(data.password)
            
            target_user.save()
            
            # 更新用户资料（昵称）
            if hasattr(target_user, 'profile'):
                profile = target_user.profile
                if data.nickname is not None:
                    # 如果提供了昵称且不为空，则更新；如果为 None，则自动生成
                    if data.nickname:
                        profile.nickname = data.nickname
                    else:
                        # None 表示自动生成
                        profile.nickname = None  # 触发自动生成
                    profile.save()
            
            # 记录更新用户成功日志
            log_admin_action(
                action="更新用户",
                message=f"管理员 {request.user.username} 更新了用户信息：{target_user.username}",
                user=request.user,
                request=request,
                extra_data={
                    "target_user_id": target_user.id,
                    "target_username": target_user.username,
                    "updated_fields": {
                        "username": data.username is not None,
                        "email": data.email is not None,
                        "is_active": data.is_active is not None,
                        "is_staff": data.is_staff is not None,
                        "password": data.password is not None
                    }
                }
            )
            
            return success_response(
                data={
                    'id': target_user.id,
                    'username': target_user.username,
                    'email': target_user.email,
                    'is_active': target_user.is_active,
                    'is_staff': target_user.is_staff,
                    'is_superuser': target_user.is_superuser,
                    'profile': {
                        'nickname': target_user.profile.nickname if hasattr(target_user, 'profile') else None
                    }
                },
                message="用户信息更新成功"
            )
            
        except Exception as exc:
            # 记录更新用户异常日志
            log_admin_action(
                action="更新用户",
                message=f"管理员 {request.user.username} 更新用户异常：{str(exc)}",
                level=Log.LEVEL.ERROR,
                user=request.user,
                request=request,
                extra_data={"target_user_id": user_id, "error": str(exc)}
            )
            return error_response(
                message=f"用户信息更新失败: {str(exc)}",
                status_code=500
            )
    
    def _delete_user(self, request, user_id: int):
        """删除用户"""
        try:
            # 检查管理员权限
            admin_check = self.check_admin_permission(request)
            if admin_check:
                return admin_check
            
            User = get_user_model()
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                log_admin_action(
                    action="删除用户",
                    message=f"管理员 {request.user.username} 尝试删除用户失败：用户不存在",
                    level=Log.LEVEL.WARNING,
                    user=request.user,
                    request=request,
                    extra_data={"target_user_id": user_id, "reason": "用户不存在"}
                )
                return error_response(
                    message="用户不存在",
                    status_code=404
                )
            
            # 防止删除自己
            if target_user.id == request.user.id:
                log_admin_action(
                    action="删除用户",
                    message=f"管理员 {request.user.username} 尝试删除自己失败：不允许删除自己",
                    level=Log.LEVEL.WARNING,
                    user=request.user,
                    request=request,
                    extra_data={"target_user_id": user_id, "reason": "不允许删除自己"}
                )
                return error_response(
                    message="不能删除自己的账户",
                    status_code=400
                )
            
            # 删除用户
            username = target_user.username
            target_user.delete()
            
            # 记录删除用户成功日志
            log_admin_action(
                action="删除用户",
                message=f"管理员 {request.user.username} 删除了用户：{username}",
                user=request.user,
                request=request,
                extra_data={
                    "deleted_user_id": target_user.id,
                    "deleted_username": username
                }
            )
            
            return success_response(
                message=f"用户 {username} 删除成功"
            )
            
        except Exception as exc:
            # 记录删除用户异常日志
            log_admin_action(
                action="删除用户",
                message=f"管理员 {request.user.username} 删除用户异常：{str(exc)}",
                level=Log.LEVEL.ERROR,
                user=request.user,
                request=request,
                extra_data={"target_user_id": user_id, "error": str(exc)}
            )
            return error_response(
                message=f"用户删除失败: {str(exc)}",
                status_code=500
            )
    
    def _toggle_user_status(self, request, user_id: int):
        """启用/禁用用户"""
        try:
            # 检查管理员权限
            admin_check = self.check_admin_permission(request)
            if admin_check:
                return admin_check
            
            User = get_user_model()
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                log_admin_action(
                    action="切换用户状态",
                    message=f"管理员 {request.user.username} 尝试切换用户状态失败：用户不存在",
                    level=Log.LEVEL.WARNING,
                    user=request.user,
                    request=request,
                    extra_data={"target_user_id": user_id, "reason": "用户不存在"}
                )
                return error_response(
                    message="用户不存在",
                    status_code=404
                )
            
            # 防止修改自己的状态
            if target_user.id == request.user.id:
                log_admin_action(
                    action="切换用户状态",
                    message=f"管理员 {request.user.username} 尝试切换自己状态失败：不允许修改自己的状态",
                    level=Log.LEVEL.WARNING,
                    user=request.user,
                    request=request,
                    extra_data={"target_user_id": user_id, "reason": "不允许修改自己的状态"}
                )
                return error_response(
                    message="不能修改自己的状态",
                    status_code=400
                )
            
            # 切换状态
            target_user.is_active = not target_user.is_active
            target_user.save()
            
            status_text = "启用" if target_user.is_active else "禁用"
            
            # 记录切换用户状态成功日志
            log_admin_action(
                action="切换用户状态",
                message=f"管理员 {request.user.username} {status_text}了用户：{target_user.username}",
                user=request.user,
                request=request,
                extra_data={
                    "target_user_id": target_user.id,
                    "target_username": target_user.username,
                    "new_status": target_user.is_active
                }
            )
            
            return success_response(
                data={'is_active': target_user.is_active},
                message=f"用户 {target_user.username} 状态已{status_text}"
            )
            
        except Exception as exc:
            # 记录切换用户状态异常日志
            log_admin_action(
                action="切换用户状态",
                message=f"管理员 {request.user.username} 切换用户状态异常：{str(exc)}",
                level=Log.LEVEL.ERROR,
                user=request.user,
                request=request,
                extra_data={"target_user_id": user_id, "error": str(exc)}
            )
            return error_response(
                message=f"修改用户状态失败: {str(exc)}",
                status_code=500
            )
