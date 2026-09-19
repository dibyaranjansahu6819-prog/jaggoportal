from django.urls import path

from .views import (
    TeacherLoginView,
    TeacherRegistrationView,
)

from .volunteer_views import (
    VolunteerDashboardView,
    VolunteerTodayAssignmentView,
    VolunteerWorkSessionStartView,
    VolunteerWorkSessionEndView,
)

from .volunteer_progress_views import (
    VolunteerProgressStudentsView,
    VolunteerProgressSaveView,
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
    
     path(
        "dashboard/",
        VolunteerDashboardView.as_view(),
        name="volunteer-dashboard",
    ),

    path(
        "today-assignment/",
        VolunteerTodayAssignmentView.as_view(),
        name="volunteer-today-assignment",
    ),

    # Work timer
    path(
        "session/start/",
        VolunteerWorkSessionStartView.as_view(),
        name="volunteer-session-start",
    ),

    path(
        "session/end/",
        VolunteerWorkSessionEndView.as_view(),
        name="volunteer-session-end",
    ),
    
    path(
    "students/",
    VolunteerProgressStudentsView.as_view(),
    name="volunteer-progress-students",
    ),

    path(
    "progress/",
    VolunteerProgressSaveView.as_view(),
    name="volunteer-progress-save",
    ),

]