from django.apps import AppConfig


class NotificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.notification"
    verbose_name = "Notification Service"

    def ready(self):
        # Place for future signals imports
        pass
