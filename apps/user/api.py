"""用户模块 API：扁平化路由（认证/个人/管理/验证码）。"""

import psutil
from typing import Optional
from uuid import UUID

from captcha.helpers import captcha_image_url
from captcha.models import CaptchaStore
from ninja import File, Query, Router
from ninja.files import UploadedFile
from ninja_extra import ControllerBase, api_controller, http_delete, http_get, http_put

from apps.core.api.permissions import IsStaffOrSuperuser
from apps.core.api.responses import error_response, success_response
from .schemas import (
    AdminCreateUserSchema,
    CaptchaVerifySchema,
    ChangePasswordSchema,
    SeedUserSchema,
    UserLoginSchema,
    UserProfileUpdateSchema,
    UserRegisterSchema,
    UserUpdateSchema,
)
from .services import (
    change_password,
    create_user_admin,
    delete_user_admin,
    get_dashboard_chart_data,
    get_dashboard_data,
    get_profile,
    get_user_detail,
    list_user_activities,
    list_users,
    login_user,
    logout_user,
    register_user,
    seed_users_service,
    toggle_user_status,
    update_profile,
    update_user_admin,
    upload_avatar,
)


# ====== 路由工厂 ======
def create_user_router() -> Router:
    router = Router(tags=["用户"])
    router.add_router("", _create_auth_router())
    router.add_router("", _create_profile_router())
    router.add_router("", _create_captcha_router())
    return router


def create_admin_api_router() -> Router:
    return _create_admin_router()


# ====== 认证路由 ======
def _create_auth_router() -> Router:
    router = Router(tags=["认证管理"])

    @router.post("/auth/login")
    def login_api(request, data: UserLoginSchema):
        payload = login_user(request, data.username, data.password)
        return success_response(data=payload, message="登录成功")

    @router.post("/auth/register")
    def register_api(request, data: UserRegisterSchema):
        payload = register_user(
            request,
            username=data.username,
            email=data.email,
            password=data.password1,
            nickname=data.nickname,
            gender=data.gender,
            birth_date=data.birth_date,
            phone=data.phone,
        )
        return success_response(data=payload, message="注册成功", status_code=201)

    @router.post("/auth/logout")
    def logout_api(request):
        logout_user(request)
        return success_response(message="登出成功")

    return router


# ====== 个人路由 ======
def _create_profile_router() -> Router:
    router = Router(tags=["个人中心"])

    @router.get("/user/profile")
    @router.get("/user/home")
    def profile_api(request):
        payload = get_profile(request.user)
        return success_response(data=payload, message="获取用户信息成功")

    @router.get("/user/change-password")
    def change_password_page(request):
        if not request.user.is_authenticated:
            return error_response(message="需要登录访问", status_code=401)
        captcha_key = CaptchaStore.pick()
        captcha_image_url_path = captcha_image_url(captcha_key)
        return success_response(
            data={
                "message": "请通过POST方法修改密码",
                "captcha_key": captcha_key,
                "captcha_image_url": captcha_image_url_path,
            },
            message="获取成功",
        )

    @router.post("/user/change-password")
    def change_password_api(request, data: ChangePasswordSchema):
        change_password(
            request,
            user=request.user,
            old_password=data.old_password,
            new_password=data.new_password1,
            captcha=data.captcha,
            captcha_key=data.captcha_key,
        )
        return success_response(message="密码修改成功")

    @router.post("/user/upload-avatar")
    def upload_avatar_api(request, file: UploadedFile = File(...)):
        avatar_url = upload_avatar(request.user, file)
        return success_response(data={"avatar_url": avatar_url}, message="头像上传成功")

    @router.get("/user/activities")
    def user_activities_api(request, page: int = 1, page_size: int = 10, activity_type: Optional[str] = Query(None)):
        payload = list_user_activities(request.user, page=page, page_size=page_size, activity_type=activity_type)
        return success_response(data=payload, message="获取活动记录成功")

    @router.post("/user/update-profile")
    def update_profile_api(request, data: UserProfileUpdateSchema):
        update_profile(
            request.user,
            nickname=data.nickname,
            gender=data.gender,
            birth_date=data.birth_date,
            phone=data.phone,
        )
        profile = get_profile(request.user).get("profile") or {}
        return success_response(
            data={
                "phone": profile.get("phone"),
                "nickname": profile.get("nickname"),
                "gender": profile.get("gender"),
                "birth_date": profile.get("birth_date"),
            },
            message="资料更新成功",
        )

    return router


# ====== 验证码路由 ======
def _create_captcha_router() -> Router:
    router = Router(tags=["验证码"])

    @router.get("/captcha/generate")
    def generate_captcha(request):
        captcha_key = CaptchaStore.pick()
        captcha_image_url_path = captcha_image_url(captcha_key)
        return success_response(
            data={
                "captcha_key": captcha_key,
                "captcha_image_url": captcha_image_url_path,
                "expires_in": 300,
            },
            message="验证码生成成功",
        )

    @router.post("/captcha/verify")
    def verify_captcha(request, data: CaptchaVerifySchema):
        try:
            captcha_store = CaptchaStore.objects.get(hashkey=data.captcha_key, response=data.captcha)
            captcha_store.delete()
            return success_response(
                data={"valid": True, "message": "验证码正确"},
                message="验证码验证成功",
            )
        except CaptchaStore.DoesNotExist:
            return error_response(message="验证码错误或已过期", status_code=400)

    return router


# ====== 管理路由 ======
def _create_admin_router() -> Router:
    router = Router(tags=["用户管理"])

    @router.get("/manage/dashboard")
    def admin_dashboard(request):
        data = get_dashboard_data(request.user)
        return success_response(data=data, message="获取管理数据成功")

    @router.get("/manage/users")
    def list_users_api(request, page: int = 1, page_size: int = 10, search: Optional[str] = None):
        data = list_users(request.user, page, page_size, search)
        return success_response(data=data, message="获取用户列表成功")

    @router.post("/manage/users")
    def create_user_api(request, data: AdminCreateUserSchema):
        payload = create_user_admin(
            request.user,
            username=data.username,
            email=data.email,
            password=data.password,
            is_staff=bool(data.is_staff),
            is_active=bool(data.is_active),
            nickname=data.nickname,
        )
        return success_response(data=payload, message="用户创建成功", status_code=201)

    @router.post("/manage/users/seed")
    def seed_users_api(request, data: SeedUserSchema):
        payload = seed_users_service(
            request.user,
            count=data.count,
            default_password=data.default_password,
            role_id=data.role_id,
        )
        return success_response(data=payload, message=f"成功生成 {payload.get('created', 0)} 个测试用户")

    @router.get("/manage/users/{user_id}")
    def get_user_detail_api(request, user_id: UUID):
        data = get_user_detail(request.user, user_id)
        return success_response(data=data, message="获取用户详情成功")

    @router.put("/manage/users/{user_id}")
    def update_user_api(request, user_id: UUID, data: UserUpdateSchema):
        update_user_admin(request.user, user_id, email=data.email, is_staff=data.is_staff)
        return success_response(message="用户信息已更新")

    @router.delete("/manage/users/{user_id}")
    def delete_user_api(request, user_id: UUID):
        delete_user_admin(request.user, user_id)
        return success_response(message="用户已删除")

    @router.post("/manage/users/{user_id}/toggle-status")
    def toggle_user_status_api(request, user_id: UUID):
        payload = toggle_user_status(request.user, user_id)
        return success_response(data=payload, message="状态已更新")

    return router


# ====== ninja-extra Controller（保留文档/兼容） ======
@api_controller("/manage", tags=["管理后台"], permissions=[IsStaffOrSuperuser])
class AdminExtraController(ControllerBase):
    """管理后台纯查询/统计接口。"""

    @http_get("/dashboard/charts", url_name="admin_dashboard_charts")
    def get_dashboard_charts(self, request, days: int = 30):
        data = get_dashboard_chart_data(request.user, days=days)
        return success_response(data=data, message="获取图表数据成功")

    @http_get("/system/info", url_name="admin_system_info")
    def get_system_info(self):
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return success_response(
            data={
                "cpu": {"percent": cpu_percent, "count": psutil.cpu_count()},
                "memory": {"total": memory.total, "used": memory.used, "percent": memory.percent},
                "disk": {"total": disk.total, "used": disk.used, "percent": disk.percent},
            },
            message="获取系统信息成功",
        )


__all__ = ["create_user_router", "create_admin_api_router", "AdminExtraController"]
