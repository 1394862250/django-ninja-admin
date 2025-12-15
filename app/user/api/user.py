"""
用户相关API接口
包含4个接口：获取用户信息、修改密码相关
"""
from ninja import Router
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url

from .user_schemas import ChangePasswordSchema
from app.user.flows.user_flow import change_password_flow
from app.utils.responses import success_response, error_response


def create_user_api_router():
    """创建用户API路由"""
    router = Router()

    @router.get("/user/profile")
    @router.get("/user/home")
    def get_user_profile(request):
        """获取用户个人信息/首页"""
        # 权限检查：必须已登录
        if not request.user.is_authenticated:
            return error_response(message="需要登录访问", status_code=401)

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
                    'avatar': user.profile.avatar.url if hasattr(user, 'profile') and user.profile and user.profile.avatar else None,
                    'status': user.profile.status if hasattr(user, 'profile') else 'active',
                    'login_count': user.profile.login_count if hasattr(user, 'profile') else 0,
                    'last_activity': user.profile.last_activity.strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'profile') and user.profile.last_activity else None,
                },
            },
            message="获取用户信息成功"
        )

    @router.get("/user/change-password")
    def change_password_page(request):
        """密码修改页面信息（前端使用）"""
        # 权限检查：必须已登录
        if not request.user.is_authenticated:
            return error_response(message="需要登录访问", status_code=401)

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

    @router.post("/user/change-password")
    def change_password(request, data: ChangePasswordSchema):
        """修改密码"""
        result = change_password_flow(
            request=request,
            old_password=data.old_password,
            new_password=data.new_password1,  # 使用 new_password1
            captcha=data.captcha,
            captcha_key=data.captcha_key
        )

        if not result.success:
            return error_response(message=result.message, status_code=400)

        return success_response(message=result.message)

    return router
