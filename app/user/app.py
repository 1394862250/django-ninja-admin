from django.apps import AppConfig

class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user'  # 修复：应该只是'user'，不是'app.user'
    verbose_name = "用户管理"

    def ready(self):
        import app.user.signals  # noqa