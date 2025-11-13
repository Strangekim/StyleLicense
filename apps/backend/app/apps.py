from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"
    verbose_name = "Style License"

    def ready(self):
        """Import signals when app is ready."""
        import app.signals  # noqa: F401
