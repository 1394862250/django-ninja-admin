"""
用户相关API接口
包含3个接口：获取用户信息、修改密码相关
"""

from .base import BaseUserAPI, success_response, error_response
from app.user.schemas import ChangePasswordSchema
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url
from django.utils import timezone
from datetime import datetime, timedelta
from app.utils.log_utils import log_user_action
from app.log.model import Log

class UserAPI(BaseUserAPI):
    """用户相关API"""
    
    def _setup_routes(self):
        @self.router.get("/user/profile", operation_id="get_user_profile")
        @self.router.get("/user/home", operation_id="get_user_home")
        def get_user_profile(request):
            return self._get_user_profile(request)
        
        @self.router.get("/user/change-password")
        def change_password_page(request):
            return self._change_password_page(request)
        
        @self.router.post("/user/change-password")
        def change_password(request, data: ChangePasswordSchema):
            return self._change_password(request, data)
    
    def _get_user_profile(self, request):
        """获取用户个人信息/首页"""
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
                        'nickname': user.profile.nickname if hasattr(user, 'profile') else None,
                        'gender': user.profile.gender if hasattr(user, 'profile') else None,
                        'birth_date': user.profile.birth_date.strftime('%Y-%m-%d') if hasattr(user, 'profile') and user.profile.birth_date else None,
                        'avatar': user.profile.avatar.url if user.profile and user.profile.avatar else None,
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
    
    def _change_password_page(self, request):
        """密码修改页面信息（前端使用）"""
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
    
    def _change_password(self, request, data: ChangePasswordSchema):
        """修改密码 - 增强版"""
        try:
            # 检查认证
            auth_check = self.check_authentication(request)
            if auth_check:
                return auth_check
            
            user = request.user
            
            # 验证验证码（如果提供了验证码）
            if data.captcha and data.captcha_key:
                try:
                    captcha_store = CaptchaStore.objects.get(
                        hashkey=data.captcha_key,
                        response=data.captcha
                    )
                    # 验证通过后删除验证码记录
                    captcha_store.delete()
                except CaptchaStore.DoesNotExist:
                    log_user_action(
                        action="修改密码",
                        message=f"用户 {user.username} 修改密码失败：验证码错误或已过期",
                        level=Log.LEVEL.WARNING,
                        user=user,
                        request=request,
                        extra_data={"reason": "验证码错误或已过期"}
                    )
                    return error_response(
                        message="验证码错误或已过期",
                        status_code=400
                    )
            elif data.captcha or data.captcha_key:
                # 如果只提供了其中一个，说明验证码不完整
                log_user_action(
                    action="修改密码",
                    message=f"用户 {user.username} 修改密码失败：请提供完整的验证码信息",
                    level=Log.LEVEL.WARNING,
                    user=user,
                    request=request,
                    extra_data={"reason": "验证码信息不完整"}
                )
                return error_response(
                    message="请提供完整的验证码信息",
                    status_code=400
                )
            else:
                # 如果没有提供验证码，返回错误
                log_user_action(
                    action="修改密码",
                    message=f"用户 {user.username} 修改密码失败：未提供验证码",
                    level=Log.LEVEL.WARNING,
                    user=user,
                    request=request,
                    extra_data={"reason": "未提供验证码"}
                )
                return error_response(
                    message="请提供验证码",
                    status_code=400
                )
            
            # 验证当前密码
            if not check_password(data.old_password, user.password):
                log_user_action(
                    action="修改密码",
                    message=f"用户 {user.username} 修改密码失败：当前密码不正确",
                    level=Log.LEVEL.WARNING,
                    user=user,
                    request=request,
                    extra_data={"reason": "当前密码不正确"}
                )
                return error_response(
                    message="当前密码不正确",
                    status_code=400
                )
            
            # 设置新密码
            user.set_password(data.new_password1)
            user.save()
            
            # 记录密码修改活动
            try:
                from app.user.model import UserActivity
                UserActivity.objects.create(
                    user=user,
                    activity_type='password_change',
                    description=f'用户 {user.username} 修改了密码',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception:
                pass  # 活动记录失败不影响主流程
            
            # 记录密码修改成功日志
            log_user_action(
                action="修改密码",
                message=f"用户 {user.username} 修改密码成功",
                user=user,
                request=request
            )
            
            return success_response(
                message="密码修改成功，请重新登录"
            )
            
        except Exception as exc:
            # 记录密码修改异常日志
            log_user_action(
                action="修改密码",
                message=f"用户 {request.user.username} 修改密码异常：{str(exc)}",
                level=Log.LEVEL.ERROR,
                user=request.user,
                request=request,
                extra_data={"error": str(exc)}
            )
            return error_response(
                message=f"密码修改失败: {str(exc)}",
                status_code=500
            )

def check_authentication(request):
    """检查用户认证状态（兼容性函数）"""
    if not request.user.is_authenticated:
        return error_response("需要登录访问", status_code=401)
    return None
