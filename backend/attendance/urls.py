from django.urls import path

from .views import (
    AdminAttendanceView,
    StudentAttendanceSaveView,
    TeacherAttendanceSaveView,
    AvailableVolunteerView,
    VolunteerAttendanceAddView,
    VolunteerAttendanceSaveView,
    VolunteerAttendanceDeleteView,
    AttendancePhotoUploadView,
    AttendancePhotoDeleteView,
)


urlpatterns = [

    # Main Admin 1 attendance toolkit
    path(
        "",
        AdminAttendanceView.as_view(),
        name="admin-attendance"
    ),

    # Student attendance
    path(
        "students/save/",
        StudentAttendanceSaveView.as_view(),
        name="student-attendance-save"
    ),

    # Teacher attendance
    path(
        "teachers/save/",
        TeacherAttendanceSaveView.as_view(),
        name="teacher-attendance-save"
    ),

    # Volunteers available for adding
    path(
        "volunteers/available/",
        AvailableVolunteerView.as_view(),
        name="available-volunteers"
    ),

    # Add volunteer to today's attendance
    path(
        "volunteers/add/",
        VolunteerAttendanceAddView.as_view(),
        name="volunteer-attendance-add"
    ),

    # Update volunteer attendance
    path(
        "volunteers/save/",
        VolunteerAttendanceSaveView.as_view(),
        name="volunteer-attendance-save"
    ),

    # Remove volunteer from daily attendance
    path(
        "volunteers/<int:attendance_id>/delete/",
        VolunteerAttendanceDeleteView.as_view(),
        name="volunteer-attendance-delete"
    ),

    # Attendance photos
   path(
    "photos/upload/",
    AttendancePhotoUploadView.as_view(),
    name="attendance-photo-upload"
),

path(
    "photos/<int:photo_id>/delete/",
    AttendancePhotoDeleteView.as_view(),
    name="attendance-photo-delete"
),

]

