from django.urls import path

from .views import (
    TeacherLoginView,
    TeacherRegistrationView,
)


urlpatterns = [

    path(
        "register/",
        TeacherRegistrationView.as_view(),
        name="teacher-register"
    ),

    path(
        "login/",
        TeacherLoginView.as_view(),
        name="teacher-login"
    ),

]