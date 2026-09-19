from django.urls import path

from .views import (
    Admin2DashboardView,
    DailySchoolStatusView,
    AssignmentHistoryView,
    CautionListView,
    DailyReportPNGView,
    AssignmentExcelExportView,
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
    RetryAssignmentEmailView,
)

from .volunteer_access_views import (
    VolunteerRequestAccessView,
)

from .holiday_views import (
    HolidayListCreateView,
    HolidayDetailView,
)


urlpatterns = [
    # ============================================================
    # DAILY SCHOOL STATUS
    # ============================================================

    path(
        "daily-status/",
        DailySchoolStatusView.as_view(),
        name="admin2-daily-status",
    ),

    # ============================================================
    # HOLIDAYS
    # ============================================================

    path(
        "holidays/",
        HolidayListCreateView.as_view(),
        name="admin2-holiday-list-create",
    ),

    path(
        "holidays/<int:holiday_id>/",
        HolidayDetailView.as_view(),
        name="admin2-holiday-detail",
    ),

    # ============================================================
    # DASHBOARD
    # ============================================================

    path(
        "dashboard/",
        Admin2DashboardView.as_view(),
        name="admin2-dashboard",
    ),

    # ============================================================
    # STUDENTS
    # ============================================================

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

    # ============================================================
    # VOLUNTEERS
    # ============================================================

    path(
        "volunteers/",
        RegisteredVolunteersView.as_view(),
        name="admin2-volunteers",
    ),

    # ============================================================
    # ASSIGNMENTS
    # ============================================================

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

    path(
        "assignments/export-excel/",
        AssignmentExcelExportView.as_view(),
        name="admin2-assignment-excel-export",
    ),

    path(
        "assignments/<int:assignment_id>/retry-email/",
        RetryAssignmentEmailView.as_view(),
        name="admin2-retry-assignment-email",
    ),

    # ============================================================
    # XP
    # ============================================================

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

    # ============================================================
    # CAUTION
    # ============================================================

    path(
        "cautions/",
        CautionListView.as_view(),
        name="admin2-cautions",
    ),

    # ============================================================
    # VOLUNTEER ACCOUNT STATUS
    # ============================================================

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

    # ============================================================
    # ACCESS REQUESTS
    # ============================================================

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

    # ============================================================
    # PUBLIC REMOVED-VOLUNTEER REQUEST
    # ============================================================

    path(
        "volunteer/request-access/",
        VolunteerRequestAccessView.as_view(),
        name="volunteer-request-access",
    ),
]