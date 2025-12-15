"""
认证相关API接口
包含3个接口：登录、注册、登出
"""
from ninja import Router
from .auth_schemas import UserLoginSchema, UserRegisterSchema
from app.user.flows.auth_flow import (
    login_user_flow,
    register_user_flow,
    logout_user_flow
)
from app.utils.responses import success_response, error_response


def create_auth_api_router():
    """创建认证API路由"""
    router = Router()

    @router.post("/auth/login")
    def login_user(request, data: UserLoginSchema):
        """用户登录"""
        result = login_user_flow(request, data.username, data.password)

        if not result.success:
            return error_response(message=result.message, status_code=400)

        return success_response(data=result.data, message=result.message)

    @router.post("/auth/register")
    def register_user(request, data: UserRegisterSchema):
        """用户注册"""
        result = register_user_flow(
            request=request,
            username=data.username,
            email=data.email,
            password=data.password1,
            nickname=data.nickname,
            gender=data.gender,
            birth_date=data.birth_date,
            phone=data.phone
        )

        if not result.success:
            return error_response(message=result.message, status_code=400)

        return success_response(
            data=result.data,
            message=result.message,
            status_code=201
        )

    @router.post("/auth/logout")
    def logout_user(request):
        """用户登出"""
        result = logout_user_flow(request)

        if not result.success:
            return error_response(message=result.message, status_code=401)

        return success_response(message=result.message)

    return router
