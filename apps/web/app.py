"""
Web应用配置
"""
from django.apps import AppConfig


class WebConfig(AppConfig):
    """Web应用配置"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.web'
    verbose_name = 'Web视图'

