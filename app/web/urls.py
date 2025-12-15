"""
Web应用URL配置
"""
from django.urls import path
from . import views

app_name = 'web'

urlpatterns = [
    # 首页 - 根据用户状态自动重定向
    path('', views.index_view, name='index'),
    
    # 认证相关页面
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    
    # 用户相关页面
    path('user/home/', views.user_home_view, name='user_home'),
    path('user/profile/', views.user_profile_view, name='user_profile'),
    
    # 管理相关页面
    path('manage/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('manage/users/', views.user_management_view, name='user_management'),
    # path('manage/roles/', views.role_management, name='role_management'),  # RBAC 已废弃
    path('manage/api-docs/', views.api_docs_view, name='api_docs'),
    path('manage/notifications/', views.notification_management_view, name='notification_management'),
    path('manage/notifications/create/', views.notification_create_view, name='notification_create'),
    path('manage/logs/', views.log_management_view, name='log_management'),
    path('manage/settings/', views.setting_management_view, name='setting_management'),
]

