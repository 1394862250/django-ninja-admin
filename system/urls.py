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
from ninja import NinjaAPI

# 导入User微服务API
from app.user.api import api as user_api

# 创建主API实例
api = NinjaAPI(
    title="Django Ninja Admin API",
    description="Django Ninja管理后台API - 微服务架构 + 工具集成 + 验证码",
    version="1.0.0",
    docs_url="/docs/",  # 显式指定文档URL（Swagger UI）
    openapi_url="/openapi.json",  # 显式指定OpenAPI Schema URL
)

# 注册User微服务API到根路径
api.add_router("", user_api)  # 移除了"/api/"前缀

urlpatterns = [
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),  # Simple Captcha URL
    path('accounts/', include('allauth.urls')),  # Allauth URLs
    path('api/', api.urls),         # 注册Ninja API路由（包含/docs/和/redoc/）
]

# 在开发环境中提供媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)