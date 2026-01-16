"""
URL configuration for system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_apps.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .api import api


# 注册角色API到独立路径
urlpatterns = [
    # Web应用路由
    path('', include('apps.web.urls')),
    
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
