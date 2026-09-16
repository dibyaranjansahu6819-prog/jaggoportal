from django.apps import AppConfig


class Admin2Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin2"

    def ready(self):
        import admin2.signals