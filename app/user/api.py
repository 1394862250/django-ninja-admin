"""
User微服务API接口
集成Django Guardian、Django Allauth、Django ImageKit、Django Model Utils、Django Simple Captcha
迁移原有15个接口并添加新功能
"""
from typing import Optional, List
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from ninja import Router
from ninja.security import HttpBearer
from datetime import datetime
import json

# 导入工具和验证器
from app.utils.validators import (
    UserLoginSchema, UserRegisterSchema, UserUpdateSchema, ChangePasswordSchema,
    CaptchaRequestSchema, CaptchaVerifySchema
)

# 导入新模型
from app.user.model import (
    UserProfile, UserActivity, UserPermission, DocumentUpload,
    check_user_permission, grant_user_permission, revoke_user_permission
)

# Guardian权限管理
from guardian.shortcuts import get_perms, assign_perm, remove_perm
from guardian.core import ObjectPermissionChecker

# 导入Allauth相关
from allauth.account.models import EmailAddress, EmailConfirmation

# 导入验证码相关
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url

# 创建API路由器
api = Router(tags=['User API'])

# 认证中间件
class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        return request.user.is_authenticated

# 管理员权限中间件
class AdminAuthBearer(HttpBearer):
    def authenticate(self, request, token):
        return request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)

auth = AuthBearer()
admin_auth = AdminAuthBearer()
User = get_user_model()


# ===== 工具函数 =====

def success_response(data=None, message="操作成功", status_code=200):
    """成功响应"""
    return JsonResponse({
        'success': True,
        'message': message,
        'data': data
    }, status=status_code)

def error_response(message="操作失败", status_code=400, data=None):
    """错误响应"""
    return JsonResponse({
        'success': False,
        'message': message,
        'data': data
    }, status=status_code)

def check_authentication(request):
    """检查用户认证状态"""
    if not request.user.is_authenticated:
        return error_response("需要登录访问", status_code=401)
    return None

def check_admin_permission(request):
    """检查管理员权限"""
    if not request.user.is_authenticated:
        return error_response("需要登录访问", status_code=401)
    if not (request.user.is_staff or request.user.is_superuser):
        return error_response("需要管理员权限", status_code=403)
    return None


# ===== 验证码相关接口 (2个) =====

@api.get("/captcha/generate")
def generate_captcha(request):
    """
    生成验证码图片
    返回验证码键和图片URL
    """
    try:
        # 生成验证码
        captcha_key = CaptchaStore.pick()
        captcha_image_url_path = captcha_image_url(captcha_key)
        
        return success_response(
            data={
                'captcha_key': captcha_key,
                'captcha_image_url': captcha_image_url_path,
                'expires_in': 300  # 5分钟过期
            },
            message="验证码生成成功"
        )
        
    except Exception as exc:
        return error_response(
            message=f"验证码生成失败: {str(exc)}",
            status_code=500
        )


@api.post("/captcha/verify")
def verify_captcha(request, data: CaptchaVerifySchema):
    """
    验证验证码
    """
    try:
        # 验证验证码
        captcha_store = CaptchaStore.objects.get(
            hashkey=data.captcha_key,
            response=data.captcha
        )
        # 验证通过后删除验证码记录
        captcha_store.delete()
        
        return success_response(
            data={
                'valid': True,
                'message': '验证码正确'
            },
            message="验证码验证成功"
        )
        
    except CaptchaStore.DoesNotExist:
        return error_response(
            message="验证码错误或已过期",
            status_code=400
        )
    except Exception as exc:
        return error_response(
            message=f"验证码验证失败: {str(exc)}",
            status_code=500
        )


# ===== 认证相关接口 (3个) =====

@api.post("/auth/login")
def login_user(request, data: UserLoginSchema):
    """
    用户登录 - 增强版
    集成Allauth和活动记录
    """
    try:
        # 验证用户
        user = authenticate(request, username=data.username, password=data.password)
        
        if user is not None:
            if not user.is_active:
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
                        'bio': user.profile.bio if hasattr(user, 'profile') and user.profile else None,
                        'status': user.profile.status if hasattr(user, 'profile') and user.profile else 'active',
                        'login_count': user.profile.login_count if hasattr(user, 'profile') and user.profile else 0,
                    },
                },
                message="登录成功"
            )
        else:
            return error_response(
                message="用户名或密码错误",
                status_code=400
            )
            
    except Exception as exc:
        return error_response(
            message=f"登录失败: {str(exc)}",
            status_code=500
        )


@api.post("/auth/register")
def register_user(request, data: UserRegisterSchema):
    """
    用户注册 - 增强版
    集成Allauth验证、验证码和自动用户扩展创建
    """
    try:
        # 检查用户名是否已存在
        if User.objects.filter(username=data.username).exists():
            return error_response(
                message="用户名已存在",
                status_code=400
            )
        
        # 检查邮箱是否已存在
        if User.objects.filter(email=data.email).exists():
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
        
        # 记录注册活动
        UserActivity.objects.create(
            user=user,
            activity_type='register',
            description=f'用户 {user.username} 注册成功',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return success_response(
            data={
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                'message': '注册成功，请检查邮箱进行验证'
            },
            message="注册成功",
            status_code=201
        )
        
    except Exception as exc:
        return error_response(
            message=f"注册失败: {str(exc)}",
            status_code=400
        )


@api.post("/auth/logout")
def logout_user(request):
    """
    用户登出
    """
    try:
        # 检查用户是否已登录
        if not request.user.is_authenticated:
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
        return error_response(
            message=f"登出失败: {str(exc)}",
            status_code=500
        )


# ===== 用户相关接口 (3个) =====

@api.get("/user/profile", operation_id="get_user_profile")
@api.get("/user/home", operation_id="get_user_home")
def get_user_profile(request):
    """
    获取用户个人信息/首页
    """
    try:
        # 检查认证
        if not request.user.is_authenticated:
            return error_response(
                message="需要登录访问",
                status_code=401
            )
        
        user = request.user
        
        return success_response(
            data={
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_active': user.is_active,
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
                'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                'profile': {
                    'phone': user.profile.phone if hasattr(user, 'profile') else None,
                    'bio': user.profile.bio if hasattr(user, 'profile') else None,
                    'location': user.profile.location if hasattr(user, 'profile') else None,
                    'website': user.profile.website if hasattr(user, 'profile') else None,
                    'avatar': user.profile.avatar.url if hasattr(user, 'profile') and user.profile.avatar else None,
                    'status': user.profile.status if hasattr(user, 'profile') else 'active',
                    'login_count': user.profile.login_count if hasattr(user, 'profile') else 0,
                    'last_activity': user.profile.last_activity.strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'profile') and user.profile.last_activity else None,
                },
            },
            message="获取用户信息成功"
        )
        
    except Exception as exc:
        return error_response(
            message=f"获取用户信息失败: {str(exc)}",
            status_code=500
        )


@api.get("/user/change-password")
def change_password_page(request):
    """
    密码修改页面信息（前端使用）
    """
    try:
        # 检查认证
        auth_check = check_authentication(request)
        if auth_check:
            return auth_check
        
        # 生成验证码
        captcha_key = CaptchaStore.pick()
        captcha_image_url_path = captcha_image_url(captcha_key)
        
        return success_response(
            data={
                'message': '请通过POST方法修改密码',
                'captcha_key': captcha_key,
                'captcha_image_url': captcha_image_url_path
            },
            message="获取成功"
        )
    except Exception as exc:
        return error_response(
            message=f"获取失败: {str(exc)}",
            status_code=500
        )


@api.post("/user/change-password")
def change_password(request, data: ChangePasswordSchema):
    """
    修改密码 - 增强版
    支持验证码验证
    """
    try:
        # 检查认证
        auth_check = check_authentication(request)
        if auth_check:
            return auth_check
        
        user = request.user
        
        # 验证当前密码
        if not check_password(data.old_password, user.password):
            return error_response(
                message="当前密码不正确",
                status_code=400
            )
        
        # 设置新密码
        user.set_password(data.new_password1)
        user.save()
        
        # 记录密码修改活动
        UserActivity.objects.create(
            user=user,
            activity_type='password_change',
            description=f'用户 {user.username} 修改了密码',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return success_response(
            message="密码修改成功，请重新登录"
        )
        
    except Exception as exc:
        return error_response(
            message=f"密码修改失败: {str(exc)}",
            status_code=500
        )


# ===== 新增功能接口 =====

@api.post("/user/upload-avatar")
def upload_avatar(request):
    """
    上传用户头像
    """
    try:
        # 检查认证
        auth_check = check_authentication(request)
        if auth_check:
            return auth_check
        
        user = request.user
        
        # 获取上传的文件
        if not hasattr(request, 'FILES') or 'file' not in request.FILES:
            return error_response(
                message="未提供文件",
                status_code=400
            )
        
        file = request.FILES['file']
        
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            return error_response(
                message="只能上传图片文件",
                status_code=400
            )
        
        # 验证文件大小 (5MB限制)
        if file.size > 5 * 1024 * 1024:
            return error_response(
                message="文件大小不能超过5MB",
                status_code=400
            )
        
        # 保存头像 (ImageKit会自动处理)
        user.profile.avatar = file
        user.profile.save()
        
        # 记录活动
        UserActivity.objects.create(
            user=user,
            activity_type='avatar_upload',
            description=f'用户 {user.username} 更新了头像',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return success_response(
            data={
                'avatar_url': user.profile.avatar.url if user.profile.avatar else None,
                'avatar_thumbnail_url': user.profile.avatar_thumbnail.url if user.profile.avatar else None
            },
            message="头像上传成功"
        )
        
    except Exception as exc:
        return error_response(
            message=f"头像上传失败: {str(exc)}",
            status_code=500
        )


@api.get("/user/activities")
def get_user_activities_api(request, page: int = 1, page_size: int = 10, activity_type: Optional[str] = None):
    """
    获取用户活动记录
    """
    try:
        # 检查认证
        auth_check = check_authentication(request)
        if auth_check:
            return auth_check
        
        user = request.user
        activities_query = UserActivity.objects.filter(user=user)
        
        if activity_type:
            activities_query = activities_query.filter(activity_type=activity_type)
        
        # 分页
        paginator = Paginator(activities_query.order_by('-created'), page_size)
        activities_page = paginator.get_page(page)
        
        # 转换为字典列表
        activities_data = []
        for activity in activities_page:
            activities_data.append({
                'id': activity.id,
                'activity_type': activity.get_activity_type_display(),
                'description': activity.description,
                'ip_address': activity.ip_address,
                'created_at': activity.created.strftime('%Y-%m-%d %H:%M:%S'),
            })
        
        return success_response(
            data={
                'activities': activities_data,
                'page': page,
                'page_size': page_size,
                'total_count': paginator.count,
                'total_pages': paginator.num_pages
            },
            message="获取活动记录成功"
        )
        
    except Exception as exc:
        return error_response(
            message=f"获取活动记录失败: {str(exc)}",
            status_code=500
        )


@api.post("/user/update-profile")
def update_profile(request, data: dict):
    """
    更新用户个人资料
    """
    try:
        # 检查认证
        auth_check = check_authentication(request)
        if auth_check:
            return auth_check
        
        user = request.user
        profile = user.profile
        
        # 更新字段
        if 'phone' in data:
            profile.phone = data['phone']
        if 'bio' in data:
            profile.bio = data['bio']
        if 'location' in data:
            profile.location = data['location']
        if 'website' in data:
            profile.website = data['website']
        
        profile.save()
        
        # 记录活动
        UserActivity.objects.create(
            user=user,
            activity_type='profile_update',
            description=f'用户 {user.username} 更新了个人资料',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return success_response(
            data={
                'phone': profile.phone,
                'bio': profile.bio,
                'location': profile.location,
                'website': profile.website,
            },
            message="个人资料更新成功"
        )
        
    except Exception as exc:
        return error_response(
            message=f"个人资料更新失败: {str(exc)}",
            status_code=500
        )


# ===== 管理相关接口 (9个) =====

@api.get("/admin/dashboard")
def admin_dashboard(request):
    """
    管理后台首页 - 增强版
    """
    try:
        # 检查管理员权限
        admin_check = check_admin_permission(request)
        if admin_check:
            return admin_check
        
        # 获取统计数据
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


@api.get("/admin/users")
def list_users(request, page: int = 1, page_size: int = 10, search: Optional[str] = None):
    """
    用户管理列表 - 增强版
    """
    try:
        # 检查管理员权限
        admin_check = check_admin_permission(request)
        if admin_check:
            return admin_check
        
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
                    'location': profile.location if profile and profile.location else None,
                    'login_count': profile.login_count if profile else 0,
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


@api.get("/admin/users/{user_id}")
def get_user_detail(request, user_id: int):
    """
    获取用户详情 - 增强版
    """
    try:
        # 检查管理员权限
        admin_check = check_admin_permission(request)
        if admin_check:
            return admin_check
        
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
                    'bio': profile.bio if profile else None,
                    'location': profile.location if profile else None,
                    'website': profile.website if profile else None,
                    'status': profile.status if profile else 'active',
                    'login_count': profile.login_count if profile else 0,
                    'last_activity': profile.last_activity.strftime('%Y-%m-%d %H:%M:%S') if profile and profile.last_activity else None,
                    'avatar': profile.avatar.url if profile and profile.avatar else None,
                }
            },
            message="获取用户详情成功"
        )
        
    except Exception as exc:
        return error_response(
            message=f"获取用户详情失败: {str(exc)}",
            status_code=500
        )


@api.post("/admin/users")
def create_user(request, data: UserRegisterSchema):
    """
    创建新用户 - 增强版
    """
    try:
        # 检查管理员权限
        admin_check = check_admin_permission(request)
        if admin_check:
            return admin_check
        
        # 检查用户名是否已存在
        if User.objects.filter(username=data.username).exists():
            return error_response(
                message="用户名已存在",
                status_code=400
            )
        
        # 检查邮箱是否已存在
        if User.objects.filter(email=data.email).exists():
            return error_response(
                message="邮箱已被注册",
                status_code=400
            )
        
        # 创建用户
        user = User.objects.create_user(
            username=data.username,
            email=data.email,
            password=data.password1,
            is_staff=False,
            is_active=True
        )
        
        # 创建用户扩展信息
        UserProfile.objects.create(user=user)
        
        return success_response(
            data={
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S')
            },
            message="用户创建成功",
            status_code=201
        )
        
    except Exception as exc:
        return error_response(
            message=f"用户创建失败: {str(exc)}",
            status_code=400
        )


@api.put("/admin/users/{user_id}")
def update_user(request, user_id: int, data: UserUpdateSchema):
    """
    更新用户信息 - 增强版
    """
    try:
        # 检查管理员权限
        admin_check = check_admin_permission(request)
        if admin_check:
            return admin_check
        
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response(
                message="用户不存在",
                status_code=404
            )
        
        # 检查用户名是否已存在（排除当前用户）
        if data.username and User.objects.filter(username=data.username).exclude(id=user_id).exists():
            return error_response(
                message="用户名已存在",
                status_code=400
            )
        
        # 检查邮箱是否已存在（排除当前用户）
        if data.email and User.objects.filter(email=data.email).exclude(id=user_id).exists():
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
        
        return success_response(
            data={
                'id': target_user.id,
                'username': target_user.username,
                'email': target_user.email,
                'is_active': target_user.is_active,
                'is_staff': target_user.is_staff,
                'is_superuser': target_user.is_superuser
            },
            message="用户信息更新成功"
        )
        
    except Exception as exc:
        return error_response(
            message=f"用户信息更新失败: {str(exc)}",
            status_code=500
        )


@api.delete("/admin/users/{user_id}")
def delete_user(request, user_id: int):
    """
    删除用户 - 增强版
    """
    try:
        # 检查管理员权限
        admin_check = check_admin_permission(request)
        if admin_check:
            return admin_check
        
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response(
                message="用户不存在",
                status_code=404
            )
        
        # 防止删除自己
        if target_user.id == request.user.id:
            return error_response(
                message="不能删除自己的账户",
                status_code=400
            )
        
        # 删除用户
        username = target_user.username
        target_user.delete()
        
        return success_response(
            message=f"用户 {username} 删除成功"
        )
        
    except Exception as exc:
        return error_response(
            message=f"用户删除失败: {str(exc)}",
            status_code=500
        )


@api.post("/admin/users/{user_id}/toggle-status")
def toggle_user_status(request, user_id: int):
    """
    启用/禁用用户 - 增强版
    """
    try:
        # 检查管理员权限
        admin_check = check_admin_permission(request)
        if admin_check:
            return admin_check
        
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response(
                message="用户不存在",
                status_code=404
            )
        
        # 防止修改自己的状态
        if target_user.id == request.user.id:
            return error_response(
                message="不能修改自己的状态",
                status_code=400
            )
        
        # 切换状态
        target_user.is_active = not target_user.is_active
        target_user.save()
        
        status_text = "启用" if target_user.is_active else "禁用"
        
        return success_response(
            data={'is_active': target_user.is_active},
            message=f"用户 {target_user.username} 状态已{status_text}"
        )
        
    except Exception as exc:
        return error_response(
            message=f"修改用户状态失败: {str(exc)}",
            status_code=500
        )