"""
认证相关API接口
包含3个接口：登录、注册、登出
"""

from .base import BaseUserAPI, success_response, error_response
from app.user.schemas import UserLoginSchema, UserRegisterSchema
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.hashers import check_password
from app.user.models import UserActivity
from app.utils.log_utils import log_auth_action
from app.log.model import Log
from datetime import datetime

class AuthAPI(BaseUserAPI):
    """认证相关API"""
    
    def _setup_routes(self):
        @self.router.post("/auth/login")
        def login_user(request, data: UserLoginSchema):
            return self._login_user(request, data)
        
        @self.router.post("/auth/register")
        def register_user(request, data: UserRegisterSchema):
            return self._register_user(request, data)
        
        @self.router.post("/auth/logout")
        def logout_user(request):
            return self._logout_user(request)
    
    def _login_user(self, request, data: UserLoginSchema):
        """用户登录"""
        try:
            # 验证用户
            user = authenticate(request, username=data.username, password=data.password)
            
            if user is not None:
                if not user.is_active:
                    # 记录登录失败日志
                    log_auth_action(
                        action="用户登录",
                        message=f"用户 {data.username} 登录失败：账户已被禁用",
                        level=Log.LEVEL.WARNING,
                        user=user,
                        request=request,
                        extra_data={"username": data.username, "reason": "账户已禁用"}
                    )
                    return error_response(
                        message="用户账户已被禁用",
                        status_code=403
                    )
                
                # 登录
                login(request, user)
                
                # 更新用户扩展信息（安全访问）
                try:
                    if hasattr(user, 'profile') and user.profile:
                        user.profile.update_login_count()
                except Exception:
                    pass  # 如果profile不存在，跳过更新
                
                # 记录登录活动（安全处理）
                try:
                    UserActivity.objects.create(
                        user=user,
                        activity_type='login',
                        description=f'用户 {user.username} 登录成功',
                        ip_address=request.META.get('REMOTE_ADDR', ''),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                except Exception:
                    pass  # 如果记录失败，继续执行
                
                # 记录登录成功日志
                log_auth_action(
                    action="用户登录",
                    message=f"用户 {user.username} 登录成功",
                    user=user,
                    request=request,
                    extra_data={"username": data.username}
                )
                
                return success_response(
                    data={
                        'user_id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser,
                        'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
                        'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                        'profile': {
                            'phone': user.profile.phone if hasattr(user, 'profile') and user.profile else None,
                            'nickname': user.profile.nickname if hasattr(user, 'profile') and user.profile else None,
                            'gender': user.profile.gender if hasattr(user, 'profile') and user.profile else None,
                            'birth_date': user.profile.birth_date.strftime('%Y-%m-%d') if hasattr(user, 'profile') and user.profile and user.profile.birth_date else None,
                            'status': user.profile.status if hasattr(user, 'profile') and user.profile else 'active',
                            'login_count': user.profile.login_count if hasattr(user, 'profile') and user.profile else 0,
                        },
                    },
                    message="登录成功"
                )
            else:
                # 记录登录失败日志
                log_auth_action(
                    action="用户登录",
                    message=f"用户 {data.username} 登录失败：用户名或密码错误",
                    level=Log.LEVEL.WARNING,
                    request=request,
                    extra_data={"username": data.username, "reason": "用户名或密码错误"}
                )
                return error_response(
                    message="用户名或密码错误",
                    status_code=400
                )
                
        except Exception as exc:
            # 记录登录异常日志
            log_auth_action(
                action="用户登录",
                message=f"用户 {data.username} 登录异常：{str(exc)}",
                level=Log.LEVEL.ERROR,
                request=request,
                extra_data={"username": data.username, "error": str(exc)}
            )
            return error_response(
                message=f"登录失败: {str(exc)}",
                status_code=500
            )
    
    def _register_user(self, request, data: UserRegisterSchema):
        """用户注册"""
        try:
            User = get_user_model()
            
            # 检查用户名是否已存在
            if User.objects.filter(username=data.username).exists():
                # 记录注册失败日志
                log_auth_action(
                    action="用户注册",
                    message=f"用户 {data.username} 注册失败：用户名已存在",
                    level=Log.LEVEL.WARNING,
                    request=request,
                    extra_data={"username": data.username, "email": data.email, "reason": "用户名已存在"}
                )
                return error_response(
                    message="用户名已存在",
                    status_code=400
                )
            
            # 检查邮箱是否已存在
            if User.objects.filter(email=data.email).exists():
                # 记录注册失败日志
                log_auth_action(
                    action="用户注册",
                    message=f"用户 {data.username} 注册失败：邮箱已被注册",
                    level=Log.LEVEL.WARNING,
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
                password=data.password1
            )
            
            # 刷新用户对象以确保 profile 已创建（信号处理器已执行）
            user.refresh_from_db()
            
            # 更新用户资料（如果提供了额外信息）
            if hasattr(user, 'profile'):
                profile = user.profile
                # 如果用户提供了昵称，覆盖自动生成的昵称
                if data.nickname:
                    profile.nickname = data.nickname
                if data.gender:
                    profile.gender = data.gender
                if data.birth_date:
                    profile.birth_date = datetime.strptime(data.birth_date, '%Y-%m-%d').date()
                if data.phone:
                    profile.phone = data.phone
                profile.save()
            
            # 记录注册活动
            UserActivity.objects.create(
                user=user,
                activity_type='register',
                description=f'用户 {user.username} 注册成功',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # 记录注册成功日志
            log_auth_action(
                action="用户注册",
                message=f"用户 {user.username} 注册成功",
                user=user,
                request=request,
                extra_data={"username": user.username, "email": user.email}
            )
            
            return success_response(
                data={
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                    'profile': {
                        'nickname': user.profile.nickname if hasattr(user, 'profile') else None,
                    },
                    'message': '注册成功，请检查邮箱进行验证'
                },
                message="注册成功",
                status_code=201
            )
            
        except Exception as exc:
            # 记录注册异常日志
            log_auth_action(
                action="用户注册",
                message=f"用户 {data.username} 注册异常：{str(exc)}",
                level=Log.LEVEL.ERROR,
                request=request,
                extra_data={"username": data.username, "email": data.email, "error": str(exc)}
            )
            return error_response(
                message=f"注册失败: {str(exc)}",
                status_code=400
            )
    
    def _logout_user(self, request):
        """用户登出"""
        try:
            # 检查用户是否已登录
            if not request.user.is_authenticated:
                # 记录登出失败日志
                log_auth_action(
                    action="用户登出",
                    message="用户登出失败：用户未登录",
                    level=Log.LEVEL.WARNING,
                    request=request
                )
                return error_response(
                    message="用户未登录",
                    status_code=401
                )
            
            # 记录登出活动（安全访问）
            try:
                UserActivity.objects.create(
                    user=request.user,
                    activity_type='logout',
                    description=f'用户 {request.user.username} 登出',
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception:
                pass  # 如果记录失败，继续执行登出
            
            # 记录登出成功日志
            log_auth_action(
                action="用户登出",
                message=f"用户 {request.user.username} 登出成功",
                user=request.user,
                request=request
            )
            
            # 登出（安全处理session）
            try:
                if hasattr(request, 'session'):
                    logout(request)
            except Exception:
                pass  # 如果没有session，跳过登出
            
            return success_response(
                message="登出成功"
            )
            
        except Exception as exc:
            # 记录登出异常日志
            log_auth_action(
                action="用户登出",
                message=f"用户登出异常：{str(exc)}",
                level=Log.LEVEL.ERROR,
                request=request,
                extra_data={"error": str(exc)}
            )
            return error_response(
                message=f"登出失败: {str(exc)}",
                status_code=500
            )
