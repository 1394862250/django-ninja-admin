"""
管理相关API接口 - 保留需要 Flow 的业务接口
纯 CRUD 接口已迁移到 admin_extra.py 使用 ninja-extra 自动暴露
"""
from ninja import Router

from .admin_schemas import AdminCreateUserSchema
from app.user.flows.admin_flow import (
    get_admin_dashboard_flow,
    list_users_flow,
    create_user_flow,
    toggle_user_status_flow,
    delete_user_flow
)
from app.utils.responses import success_response, error_response


def create_admin_api_router():
    """创建管理API路由 - 仅包含需要 Flow 的业务接口"""
    router = Router()

    @router.get("/manage/dashboard")
    def admin_dashboard(request):
        """管理后台首页 - 使用 Flow 处理业务逻辑"""
        result = get_admin_dashboard_flow(request)

        if not result.success:
            return error_response(message=result.message, status_code=403)

        return success_response(data=result.data, message=result.message)

    @router.get("/manage/users")
    def list_users(request, page: int = 1, page_size: int = 10, search=None):
        """用户列表 - 使用 Flow 处理业务逻辑"""
        result = list_users_flow(request, page, page_size, search)

        if not result.success:
            return error_response(message=result.message, status_code=403)

        return success_response(data=result.data, message=result.message)

    @router.post("/manage/users")
    def create_user(request, data: AdminCreateUserSchema):
        """创建用户 - 有业务逻辑(创建 profile 等),必须使用 Flow"""
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

    @router.delete("/manage/users/{user_id}")
    def delete_user(request, user_id: int):
        """删除用户 - 敏感操作,必须使用 Flow"""
        result = delete_user_flow(request, user_id)

        if not result.success:
            return error_response(message=result.message, status_code=403)

        return success_response(message=result.message)

    @router.post("/manage/users/{user_id}/toggle-status")
    def toggle_user_status(request, user_id: int):
        """切换用户激活状态 - 状态变更有业务含义,必须使用 Flow"""
        result = toggle_user_status_flow(request, user_id)

        if not result.success:
            return error_response(message=result.message, status_code=400)

        return success_response(
            data={'is_active': result.is_active},
            message=result.message
        )

    return router
