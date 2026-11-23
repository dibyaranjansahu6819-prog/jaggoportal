from django.urls import path

from .demo import DemoLoginView
from .views import (
    CurrentUserView,
    LoginView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

urlpatterns = [
    # Common login
    path(
        "login/",
        LoginView.as_view(),
        name="login",
    ),

    # Demo-mode one-click login (only when DEMO_MODE=true)
    path(
        "demo-login/",
        DemoLoginView.as_view(),
        name="demo-login",
    ),

    # Forgot password
    path(
        "forgot-password/",
        PasswordResetRequestView.as_view(),
        name="forgot-password",
    ),

    # Set a new password from the email link
    path(
        "reset-password/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="reset-password-confirm",
    ),

    # Current authenticated user
    path(
        "me/",
        CurrentUserView.as_view(),
        name="current-user",
    ),
]
