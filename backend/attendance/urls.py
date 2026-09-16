from django.urls import path

from .views import (
    StartAttendanceSessionView,
    CurrentAttendanceSessionView,
    EndAttendanceSessionView,

    StudentAttendanceListView,
    SaveStudentAttendanceView,

    VolunteerListView,
    CurrentVolunteerAttendanceView,
    AddVolunteerAttendanceView,
    SaveVolunteerAttendanceView,

    TodayAttendanceSummaryView,
    AttendanceHistoryView,
)


urlpatterns = [

    # ========================================================
    # ATTENDANCE SESSION
    # ========================================================

    path(
        "session/start/",
        StartAttendanceSessionView.as_view(),
        name="attendance-session-start",
    ),

    path(
        "session/current/",
        CurrentAttendanceSessionView.as_view(),
        name="attendance-session-current",
    ),

    path(
        "session/end/",
        EndAttendanceSessionView.as_view(),
        name="attendance-session-end",
    ),

    # ========================================================
    # STUDENT ATTENDANCE
    # ========================================================

    path(
        "students/",
        StudentAttendanceListView.as_view(),
        name="student-attendance-list",
    ),

    path(
        "students/save/",
        SaveStudentAttendanceView.as_view(),
        name="student-attendance-save",
    ),

    # ========================================================
    # VOLUNTEERS
    # ========================================================

    path(
        "volunteers/",
        VolunteerListView.as_view(),
        name="volunteer-list",
    ),

    path(
        "volunteers/current/",
        CurrentVolunteerAttendanceView.as_view(),
        name="current-volunteer-attendance",
    ),

    path(
        "volunteers/add/",
        AddVolunteerAttendanceView.as_view(),
        name="add-volunteer-attendance",
    ),

    path(
        "volunteers/save/",
        SaveVolunteerAttendanceView.as_view(),
        name="save-volunteer-attendance",
    ),

    # ========================================================
    # SUMMARY / HISTORY
    # ========================================================

    path(
        "today/",
        TodayAttendanceSummaryView.as_view(),
        name="today-attendance-summary",
    ),

    path(
        "history/",
        AttendanceHistoryView.as_view(),
        name="attendance-history",
    ),
]