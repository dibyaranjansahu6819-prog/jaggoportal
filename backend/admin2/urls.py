from django.urls import path

from .views import (
    Admin2DashboardView,
    AssignmentHistoryView,
    CautionListView,
    DailyReportPNGView,
    DecideAccessRequestView,
    PresentStudentsTodayView,
    RegisteredVolunteersView,
    RemoveVolunteerView,
    SendAssignmentView,
    TodayAssignmentsView,
    TotalStudentsView,
    VolunteerStatusView,
    VolunteerXPView,
    ManualXPView,
    AccessRequestListView,
)
from .volunteer_access_views import (
    VolunteerRequestAccessView,
)


urlpatterns = [
    # Dashboard
    path(
        "dashboard/",
        Admin2DashboardView.as_view(),
        name="admin2-dashboard",
    ),

    # Students
    path(
        "students/total/",
        TotalStudentsView.as_view(),
        name="admin2-total-students",
    ),

    path(
        "students/present-today/",
        PresentStudentsTodayView.as_view(),
        name="admin2-present-students",
    ),

    # Volunteers
    path(
        "volunteers/",
        RegisteredVolunteersView.as_view(),
        name="admin2-volunteers",
    ),

    # Assignments
    path(
        "assignments/today/",
        TodayAssignmentsView.as_view(),
        name="admin2-today-assignments",
    ),

    path(
        "assignments/history/",
        AssignmentHistoryView.as_view(),
        name="admin2-assignment-history",
    ),

    path(
        "assignments/send/",
        SendAssignmentView.as_view(),
        name="admin2-send-assignment",
    ),

    path(
        "assignments/export-png/",
        DailyReportPNGView.as_view(),
        name="admin2-daily-report-png",
    ),

    # XP
    path(
        "xp/<int:volunteer_id>/",
        VolunteerXPView.as_view(),
        name="admin2-volunteer-xp",
    ),

    path(
        "xp/adjust/",
        ManualXPView.as_view(),
        name="admin2-manual-xp",
    ),

    # Caution
    path(
        "cautions/",
        CautionListView.as_view(),
        name="admin2-cautions",
    ),

    # Volunteer access status
    path(
        "volunteers/<int:volunteer_id>/status/",
        VolunteerStatusView.as_view(),
        name="admin2-volunteer-status",
    ),

    path(
        "volunteers/<int:volunteer_id>/remove/",
        RemoveVolunteerView.as_view(),
        name="admin2-remove-volunteer",
    ),

    # Access requests
    path(
        "access-requests/",
        AccessRequestListView.as_view(),
        name="admin2-access-requests",
    ),

    path(
        "access-requests/<int:request_id>/decide/",
        DecideAccessRequestView.as_view(),
        name="admin2-decide-access-request",
    ),

    # Public removed-volunteer request
    path(
        "volunteer/request-access/",
        VolunteerRequestAccessView.as_view(),
        name="volunteer-request-access",
    ),
]