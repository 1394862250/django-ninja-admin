"""
Ninja API 聚合入口
集中注册各业务 App 的 Router/Controller，保证统一入口和解耦。
"""
from ninja_extra import NinjaExtraAPI

from apps.user.api import AdminExtraController, create_admin_api_router, create_user_router
from apps.notification.api import NotificationController
from apps.setting.api import create_setting_api_router
from apps.log.api import LogController
from apps.core.api.exceptions import APIException
from apps.core.api.responses import ApiResponse

# 单实例 API，对外暴露给 Django URLConf
api = NinjaExtraAPI(
    title="Django Ninja Admin API",
    description="Django Ninja管理后台API - 微服务架构 + 工具集成 + 验证码",
    version="1.0.0",
    docs_url="/docs/",
    openapi_url="/openapi.json",
)

# 注册各 App Router（统一入口，便于未来分组/前缀调整）
api.add_router("", create_user_router())  # 内含认证、个人资料、验证码
api.add_router("", create_admin_api_router())
api.add_router("", create_setting_api_router())

# 注册 Controllers（自动 CRUD）
api.register_controllers(LogController)
api.register_controllers(NotificationController)
api.register_controllers(AdminExtraController)


@api.exception_handler(APIException)
def api_exception_handler(request, exc: APIException):
    """统一处理 APIException，返回标准响应外壳"""
    resp = ApiResponse(
        message=exc.message,
        status_code=exc.status_code,
        data=exc.data,
        success=False,
        code=exc.code,
    )
    return api.create_response(request, resp.to_dict(), status=resp.status_code)


__all__ = ["api"]
