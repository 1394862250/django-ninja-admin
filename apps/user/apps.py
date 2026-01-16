from django.apps import AppConfig


class UserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.user"
    verbose_name = "用户管理"

    def ready(self):
        import apps.user.signals  # noqa: F401


__all__ = ["UserConfig"]
