
from datetime import date

from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from students.models import Student
from teachers.models import Teacher

from .models import (
    StudentAttendance,
    TeacherAttendance,
    Volunteer,
    VolunteerDailyAttendance,
)

from .models import AttendancePhoto
from .serializers import AttendancePhotoSerializer


# ============================================================
# ATTENDANCE TOOLKIT
# ============================================================

class AdminAttendanceView(APIView):

    def get(self, request):

        selected_date = request.query_params.get(
            "date"
        )

        if not selected_date:
            selected_date = date.today().isoformat()


        # ----------------------------------------------------
        # STUDENTS
        # ----------------------------------------------------

        students = (
            Student.objects
            .all()
            .order_by("roll_no")
        )

        student_data = []

        for student in students:

            attendance = (
                StudentAttendance.objects
                .filter(
                    student=student,
                    date=selected_date
                )
                .first()
            )

            student_data.append({

                "student": student.id,

                "roll_no": student.roll_no,

                "name": student.name,

                "student_class":
                    student.student_class,

                "status":
                    attendance.status
                    if attendance
                    else "ABSENT",

            })


        # ----------------------------------------------------
        # VOLUNTEERS
        # ----------------------------------------------------

        volunteers = (
            VolunteerDailyAttendance.objects
            .select_related("volunteer")
            .filter(
                date=selected_date
            )
            .order_by(
                "volunteer__name"
            )
        )

        volunteer_data = []

        for attendance in volunteers:

            volunteer_data.append({

                "id": attendance.id,

                "volunteer":
                    attendance.volunteer.id,

                "name":
                    attendance.volunteer.name,

                "status":
                    attendance.status,

            })


        # ----------------------------------------------------
        # PHOTOS
        # ----------------------------------------------------

        photos = (
            AttendanceSessionPhoto.objects
            .filter(
                date=selected_date
            )
            .order_by(
                "-uploaded_at"
            )
        )

        student_photos = []
        volunteer_photos = []

        for photo in photos:

            data = {
                "id": photo.id,
                "photo_type": photo.photo_type,
                "url": request.build_absolute_uri(
                    photo.photo.url
                ),
            }

            if photo.photo_type == "STUDENT":
                student_photos.append(data)

            else:
                volunteer_photos.append(data)


        return Response({

            "date":
                selected_date,

            "students":
                student_data,

            "volunteers":
                volunteer_data,

            "student_photos":
                student_photos,

            "volunteer_photos":
                volunteer_photos,

        })


# ============================================================
# STUDENT ATTENDANCE SAVE
# ============================================================

class StudentAttendanceSaveView(APIView):

    def post(self, request):

        student_id = request.data.get(
            "student"
        )

        attendance_date = request.data.get(
            "date"
        )

        attendance_status = request.data.get(
            "status"
        )


        if not student_id:

            return Response(
                {
                    "error":
                        "Student is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        if not attendance_date:

            return Response(
                {
                    "error":
                        "Date is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        if attendance_status not in [
            "PRESENT",
            "ABSENT",
        ]:

            return Response(
                {
                    "error":
                        "Invalid attendance status."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        student = get_object_or_404(
            Student,
            id=student_id
        )


        attendance, created = (
            StudentAttendance.objects
            .update_or_create(

                student=student,

                date=attendance_date,

                defaults={
                    "status":
                        attendance_status
                }

            )
        )


        return Response({

            "id":
                attendance.id,

            "student":
                attendance.student.id,

            "status":
                attendance.status,

        })


# ============================================================
# TEACHER ATTENDANCE SAVE
# ============================================================

class TeacherAttendanceSaveView(APIView):

    def post(self, request):

        teacher_id = request.data.get(
            "teacher"
        )

        attendance_date = request.data.get(
            "date"
        )

        attendance_status = request.data.get(
            "status"
        )


        if attendance_status not in [
            "PRESENT",
            "ABSENT",
        ]:

            return Response(
                {
                    "error":
                        "Invalid attendance status."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        teacher = get_object_or_404(
            Teacher,
            id=teacher_id
        )


        attendance, created = (
            TeacherAttendance.objects
            .update_or_create(

                teacher=teacher,

                date=attendance_date,

                defaults={
                    "status":
                        attendance_status
                }

            )
        )


        return Response({

            "id":
                attendance.id,

            "teacher":
                attendance.teacher.id,

            "status":
                attendance.status,

        })


# ============================================================
# AVAILABLE VOLUNTEERS
# ============================================================

class AvailableVolunteerView(APIView):

    def get(self, request):

        selected_date = request.query_params.get(
            "date"
        )

        if not selected_date:
            selected_date = date.today().isoformat()


        already_added = (
            VolunteerDailyAttendance.objects
            .filter(
                date=selected_date
            )
            .values_list(
                "volunteer_id",
                flat=True
            )
        )


        volunteers = (
            Volunteer.objects
            .filter(
                is_active=True
            )
            .exclude(
                id__in=already_added
            )
            .order_by("name")
        )


        return Response([

            {
                "id":
                    volunteer.id,

                "name":
                    volunteer.name,

                "phone":
                    volunteer.phone,

                "email":
                    volunteer.email,

            }

            for volunteer in volunteers

        ])


# ============================================================
# ADD VOLUNTEER FOR TODAY
# ============================================================

class VolunteerAttendanceAddView(APIView):

    def post(self, request):

        volunteer_id = request.data.get(
            "volunteer"
        )

        attendance_date = request.data.get(
            "date"
        )


        if not volunteer_id:
            return Response(
                {
                    "error":
                        "Volunteer is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        if not attendance_date:
            attendance_date = date.today().isoformat()


        volunteer = get_object_or_404(
            Volunteer,
            id=volunteer_id,
            is_active=True
        )


        attendance, created = (
            VolunteerDailyAttendance.objects
            .get_or_create(

                volunteer=volunteer,

                date=attendance_date,

                defaults={
                    "status":
                        "PRESENT"
                }

            )
        )


        if not created:

            return Response(
                {
                    "error":
                        "Volunteer is already added for this date."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        return Response({

            "id":
                attendance.id,

            "volunteer":
                volunteer.id,

            "name":
                volunteer.name,

            "status":
                attendance.status,

        }, status=status.HTTP_201_CREATED)


# ============================================================
# VOLUNTEER ATTENDANCE STATUS
# ============================================================

class VolunteerAttendanceSaveView(APIView):

    def post(self, request):

        attendance_id = request.data.get(
            "id"
        )

        attendance_status = request.data.get(
            "status"
        )


        if attendance_status not in [
            "PRESENT",
            "ABSENT",
        ]:

            return Response(
                {
                    "error":
                        "Invalid attendance status."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        attendance = get_object_or_404(
            VolunteerDailyAttendance,
            id=attendance_id
        )


        attendance.status = attendance_status

        attendance.save()


        return Response({

            "id":
                attendance.id,

            "status":
                attendance.status,

        })


# ============================================================
# DELETE VOLUNTEER FROM DAILY LIST
# ============================================================

class VolunteerAttendanceDeleteView(APIView):

    def delete(self, request, attendance_id):

        attendance = get_object_or_404(
            VolunteerDailyAttendance,
            id=attendance_id
        )

        attendance.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


# ============================================================
# UPLOAD ATTENDANCE PHOTO
# ============================================================

class AttendancePhotoUploadView(APIView):

    def post(
        self,
        request
    ):

        uploaded_photo = request.FILES.get(
            "photo"
        )

        photo_type = request.data.get(
            "photo_type"
        )

        attendance_date = request.data.get(
            "date"
        )


        if not uploaded_photo:

            return Response(
                {
                    "error":
                        "Photo is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        if photo_type not in [
            "STUDENT",
            "VOLUNTEER",
        ]:

            return Response(
                {
                    "error":
                        "Invalid photo type."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        if not attendance_date:

            attendance_date = date.today()


        if not uploaded_photo.content_type.startswith(
            "image/"
        ):

            return Response(
                {
                    "error":
                        "Only image files are allowed."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        if uploaded_photo.size > (
            10 * 1024 * 1024
        ):

            return Response(
                {
                    "error":
                        "Photo must be smaller than 10 MB."
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        photo = AttendancePhoto.objects.create(

            photo=uploaded_photo,

            photo_type=photo_type,

            date=attendance_date,
        )


        serializer = AttendancePhotoSerializer(
            photo,
            context={
                "request": request
            }
        )


        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


class AttendancePhotoDeleteView(APIView):

    def delete(
        self,
        request,
        photo_id
    ):

        try:

            photo = AttendancePhoto.objects.get(
                id=photo_id
            )

        except AttendancePhoto.DoesNotExist:

            return Response(
                {
                    "error":
                        "Photo not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )


        if photo.photo:

            photo.photo.delete(
                save=False
            )


        photo.delete()


        return Response(
            {
                "message":
                    "Photo deleted successfully."
            },
            status=status.HTTP_200_OK
        )