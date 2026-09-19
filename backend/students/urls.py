from django.urls import path

from .views import StudentRegistrationView
from .views import StudentHomeworkCompleteView
from .views import StudentXPView
from .views import StudentXPLeaderboardView
from .student_records_views_14day import Student14DayHistoryView

urlpatterns = [
    path(
        "register/",
        StudentRegistrationView.as_view(),
        name="student-register",
    ),

    path(
        "homework/<int:homework_id>/complete/",
        StudentHomeworkCompleteView.as_view(),
        name="student-homework-complete",
    ),

    path(
        "<int:student_id>/xp/",
        StudentXPView.as_view(),
        name="student-xp",
    ),

    path(
        "xp/leaderboard/",
        StudentXPLeaderboardView.as_view(),
        name="student-xp-leaderboard",
    ),

    path(
        "<int:student_id>/14-day-history/",
        Student14DayHistoryView.as_view(),
        name="student-14-day-history",
    ),
]
