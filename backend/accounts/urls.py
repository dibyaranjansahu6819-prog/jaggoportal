from django.urls import path

from .views import (
    CurrentUserView,
    LoginView,
)


urlpatterns = [

    # Common login
    path(
        "login/",
        LoginView.as_view(),
        name="login",
    ),

    # Current authenticated user
    path(
        "me/",
        CurrentUserView.as_view(),
        name="current-user",
    ),
]