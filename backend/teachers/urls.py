from django.urls import path

from .views import (
    TeacherRegistrationView,
    TeacherLoginView,
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

from .work_mode_views import (
    VolunteerWorkModeView,
)

from .volunteer_checking_views import (
    VolunteerCheckingDashboardView,
    VolunteerCheckingStudentDetailView,
    VolunteerCheckingSaveView,
)

from .special_added_views import (
    SpecialAddedAvailableWorkView,
    SpecialAddedSelectWorkView,
    SpecialAddedCurrentWorkView,
)


urlpatterns = [

    # ========================================================
    # VOLUNTEER AUTHENTICATION
    # ========================================================

    path(
        "register/",
        TeacherRegistrationView.as_view(),
        name="teacher-register",
    ),

    path(
        "login/",
        TeacherLoginView.as_view(),
        name="teacher-login",
    ),


    # ========================================================
    # VOLUNTEER DASHBOARD
    # ========================================================

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

    path(
        "work-mode/",
        VolunteerWorkModeView.as_view(),
        name="volunteer-work-mode",
    ),


    # ========================================================
    # GENERIC WORK SESSION
    # ========================================================

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


    # ========================================================
    # TEACHING
    # ========================================================

    # Existing endpoint expected by Teaching tests/frontend
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

    # Compatibility aliases for the newer route naming
    path(
        "progress/students/",
        VolunteerProgressStudentsView.as_view(),
        name="volunteer-progress-students-new",
    ),

    path(
        "progress/save/",
        VolunteerProgressSaveView.as_view(),
        name="volunteer-progress-save-new",
    ),


    # ========================================================
    # SPECIAL ADDED WORK
    # ========================================================

    path(
        "special-added/available-work/",
        SpecialAddedAvailableWorkView.as_view(),
        name="special-added-available-work",
    ),

    path(
        "special-added/select-work/",
        SpecialAddedSelectWorkView.as_view(),
        name="special-added-select-work",
    ),

    path(
        "special-added/current-work/",
        SpecialAddedCurrentWorkView.as_view(),
        name="special-added-current-work",
    ),


    # ========================================================
    # CHECKING
    # ========================================================

    path(
        "checking/",
        VolunteerCheckingDashboardView.as_view(),
        name="volunteer-checking-dashboard",
    ),

    path(
        "checking/students/<int:student_id>/",
        VolunteerCheckingStudentDetailView.as_view(),
        name="volunteer-checking-student-detail",
    ),

    path(
        "checking/students/<int:student_id>/save/",
        VolunteerCheckingSaveView.as_view(),
        name="volunteer-checking-save",
    ),
]