"""
URL configuration for system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from ninja_extra import NinjaExtraAPI

# 导入User微服务API
from app.user.api import create_user_api_router, create_captcha_api_router, create_auth_api_router, create_user_feature_api_router, create_admin_api_router, create_role_api_router
from app.user.api.admin_extra import AdminExtraController
from app.notification.api import NotificationController
from app.setting.api import create_setting_api_router
from app.log.api import LogController

# 创建主API实例
api = NinjaExtraAPI(
    title="Django Ninja Admin API",
    description="Django Ninja管理后台API - 微服务架构 + 工具集成 + 验证码",
    version="1.0.0",
    docs_url="/docs/",  # 显式指定文档URL（Swagger UI）
    openapi_url="/openapi.json",  # 显式指定OpenAPI Schema URL
)

# 注册 Extra 控制器（自动CRUD + 统计）
api.register_controllers(LogController)
api.register_controllers(NotificationController)
api.register_controllers(AdminExtraController)  # 管理后台纯CRUD接口

# 注册User微服务API到根路径
api.add_router("", create_user_api_router())
api.add_router("", create_captcha_api_router())
api.add_router("", create_auth_api_router())
api.add_router("", create_user_feature_api_router())
api.add_router("", create_admin_api_router())
api.add_router("", create_role_api_router())
api.add_router("", create_setting_api_router())  # 设置API路由


# 注册角色API到独立路径
urlpatterns = [
    # Web应用路由
    path('', include('app.web.urls')),
    
    # Django Admin
    path('admin/', admin.site.urls),
    
    # 第三方应用URL
    path('captcha/', include('captcha.urls')),  # Simple Captcha URL
    path('accounts/', include('allauth.urls')),  # Allauth URLs
    
    # API路由
    path('api/', api.urls),         # 注册Ninja API路由（包含/docs/和/redoc/）
]

# 在开发环境中提供媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)