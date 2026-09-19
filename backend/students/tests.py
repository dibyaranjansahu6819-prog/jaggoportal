from django.contrib.auth.models import User
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from courses.models import Course, Subject
from admin2.models import VolunteerAssignment
from teachers.models import Teacher, VolunteerWorkSession

from .models import (
    Student,
    StudentRegistrationSequence,
    StudentHomework,
    StudentXPTransaction,
)

from .services import (
    get_student_xp,
    sync_homework_xp,
)

class StudentRegistrationTests(APITestCase):

    def test_student_registration_success(self):
        response = self.client.post(
            "/api/students/register/",
            {
                "name": "Rahul Das",
                "student_class": "9",
                "school_name": "Jaago School",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Student.objects.count(),
            1,
        )

        student = Student.objects.first()

        self.assertEqual(
            student.name,
            "Rahul Das",
        )

        self.assertEqual(
            student.student_class,
            "9",
        )

        self.assertEqual(
            student.school_name,
            "Jaago School",
        )

        self.assertTrue(
            student.roll_no.startswith("JAA09"),
        )

    def test_lkg_roll_number(self):
        response = self.client.post(
            "/api/students/register/",
            {
                "name": "LKG Student",
                "student_class": "LKG",
                "school_name": "Jaago School",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        student = Student.objects.first()

        self.assertTrue(
            student.roll_no.startswith("JAAK1"),
        )

    def test_ukg_roll_number(self):
        response = self.client.post(
            "/api/students/register/",
            {
                "name": "UKG Student",
                "student_class": "UKG",
                "school_name": "Jaago School",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        student = Student.objects.first()

        self.assertTrue(
            student.roll_no.startswith("JAAK2"),
        )

    def test_class_10_roll_number(self):
        response = self.client.post(
            "/api/students/register/",
            {
                "name": "Class Ten Student",
                "student_class": "10",
                "school_name": "Jaago School",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        student = Student.objects.first()

        self.assertTrue(
            student.roll_no.startswith("JAA10"),
        )

    def test_registration_sequence_is_global(self):
        response1 = self.client.post(
            "/api/students/register/",
            {
                "name": "Student One",
                "student_class": "9",
                "school_name": "Jaago School",
            },
            format="json",
        )

        response2 = self.client.post(
            "/api/students/register/",
            {
                "name": "Student Two",
                "student_class": "10",
                "school_name": "Jaago School",
            },
            format="json",
        )

        self.assertEqual(
            response1.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response2.status_code,
            status.HTTP_201_CREATED,
        )

        students = list(
            Student.objects.order_by("id")
        )

        self.assertEqual(
            len(students),
            2,
        )

        self.assertNotEqual(
            students[0].roll_no,
            students[1].roll_no,
        )

        sequence = StudentRegistrationSequence.objects.get(
            pk=1
        )

        self.assertEqual(
            sequence.value,
            2,
        )

    def test_student_name_required(self):
        response = self.client.post(
            "/api/students/register/",
            {
                "name": "",
                "student_class": "9",
                "school_name": "Jaago School",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Student.objects.count(),
            0,
        )

    def test_student_school_name_required(self):
        response = self.client.post(
            "/api/students/register/",
            {
                "name": "Rahul Das",
                "student_class": "9",
                "school_name": "",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Student.objects.count(),
            0,
        )

    def test_invalid_class_rejected(self):
        response = self.client.post(
            "/api/students/register/",
            {
                "name": "Rahul Das",
                "student_class": "11",
                "school_name": "Jaago School",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Student.objects.count(),
            0,
        )

    def test_roll_number_is_read_only(self):
        response = self.client.post(
            "/api/students/register/",
            {
                "roll_no": "FAKE9999",
                "name": "Rahul Das",
                "student_class": "9",
                "school_name": "Jaago School",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        student = Student.objects.first()

        self.assertNotEqual(
            student.roll_no,
            "FAKE9999",
        )

        self.assertTrue(
            student.roll_no.startswith("JAA09"),
        )

class StudentXPServiceTests(APITestCase):
    """
    Tests for automatic student XP.

    Student XP rules:
    - Pending homework = 0 XP
    - Completed homework = +10 XP
    - Same homework cannot award XP twice
    - Attendance has no role in student XP
    """

    def setUp(self):
        # ---------------------------------------------------------
        # STUDENT
        # ---------------------------------------------------------
        self.student = Student.objects.create(
            roll_no="JAATEST01",
            name="XP Test Student",
            student_class="9",
            group="ClassD",
            school_name="Jaago School",
        )

        # ---------------------------------------------------------
        # COURSE / SUBJECT
        # ---------------------------------------------------------
        self.course = Course.objects.create(
            name="Test Course",
        )

        self.subject = Subject.objects.create(
            name="Mathematics",
        )

        # ---------------------------------------------------------
        # VOLUNTEER USER
        # ---------------------------------------------------------
        self.volunteer_user = User.objects.create_user(
            username="xpvolunteer@example.com",
            email="xpvolunteer@example.com",
            password="VolunteerPassword123",
        )

        # ---------------------------------------------------------
        # VOLUNTEER
        # ---------------------------------------------------------
        self.volunteer = Teacher.objects.create(
            auth_user=self.volunteer_user,
            user_id="XPVOL001",
            name="XP Test Volunteer",
            course=self.course,
            joining_year=2026,
            subject=self.subject,
            email="xpvolunteer@example.com",
            whatsapp_number="9876543210",
            free_days=[
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
            ],
            password="",
        )

        # ---------------------------------------------------------
        # ASSIGNMENT
        # ---------------------------------------------------------
        self.assignment = VolunteerAssignment.objects.create(
            volunteer=self.volunteer,
            assignment_date=timezone.localdate(),
            assigned_class="ClassD",
            task="TEACHING",
            instruction="Complete mathematics homework.",
            email_status="SENT",
            created_by=self.volunteer_user,
        )

        # ---------------------------------------------------------
        # WORK SESSION
        # ---------------------------------------------------------
        self.work_session = VolunteerWorkSession.objects.create(
            assignment=self.assignment,
            volunteer=self.volunteer,
            status="COMPLETED",
            started_at=timezone.now(),
            ended_at=timezone.now(),
            total_seconds=1800,
        )

        # ---------------------------------------------------------
        # HOMEWORK
        # ---------------------------------------------------------
        self.homework = StudentHomework.objects.create(
            student=self.student,
            assignment=self.assignment,
            work_session=self.work_session,
            status="PENDING",
        )

    def test_pending_homework_gives_zero_xp(self):
        """
        Pending homework must not award XP.
        """

        result = sync_homework_xp(self.homework)

        self.assertIsNone(result)

        self.assertEqual(
            get_student_xp(self.student),
            0,
        )

        self.assertEqual(
            StudentXPTransaction.objects.filter(
                student=self.student
            ).count(),
            0,
        )

    def test_completed_homework_gives_ten_xp(self):
        """
        Completing homework must automatically award +10 XP.
        """

        self.homework.status = "COMPLETED"
        self.homework.completed_at = timezone.now()
        self.homework.save()

        result = sync_homework_xp(self.homework)

        self.assertIsNotNone(result)

        self.assertEqual(
            result.points,
            10,
        )

        self.assertEqual(
            result.source,
            "HOMEWORK_COMPLETED",
        )

        self.assertEqual(
            get_student_xp(self.student),
            10,
        )

    def test_completed_homework_creates_one_transaction(self):
        """
        One completed homework must create exactly one XP transaction.
        """

        self.homework.status = "COMPLETED"
        self.homework.completed_at = timezone.now()
        self.homework.save()

        sync_homework_xp(self.homework)

        self.assertEqual(
            StudentXPTransaction.objects.filter(
                homework=self.homework
            ).count(),
            1,
        )

    def test_same_homework_cannot_double_award_xp(self):
        """
        Calling the synchronization service repeatedly
        must not accumulate duplicate XP.
        """

        self.homework.status = "COMPLETED"
        self.homework.completed_at = timezone.now()
        self.homework.save()

        sync_homework_xp(self.homework)

        self.assertEqual(
            get_student_xp(self.student),
            10,
        )

        sync_homework_xp(self.homework)

        self.assertEqual(
            get_student_xp(self.student),
            10,
        )

        self.assertEqual(
            StudentXPTransaction.objects.filter(
                homework=self.homework
            ).count(),
            1,
        )

    def test_homework_transaction_contains_correct_student(self):
        """
        XP transaction must belong to the student who completed
        the homework.
        """

        self.homework.status = "COMPLETED"
        self.homework.completed_at = timezone.now()
        self.homework.save()

        transaction = sync_homework_xp(self.homework)

        self.assertEqual(
            transaction.student,
            self.student,
        )

        self.assertEqual(
            transaction.homework,
            self.homework,
        )

    def test_homework_transaction_is_exactly_ten_xp(self):
        """
        Automatic homework XP must always be exactly +10.
        """

        self.homework.status = "COMPLETED"
        self.homework.completed_at = timezone.now()
        self.homework.save()

        transaction = sync_homework_xp(self.homework)

        self.assertEqual(
            transaction.points,
            10,
        )

    def test_pending_after_completed_removes_homework_xp(self):
        """
        If homework is changed back to PENDING and synchronized,
        its automatic homework XP is removed.
        """

        self.homework.status = "COMPLETED"
        self.homework.completed_at = timezone.now()
        self.homework.save()

        sync_homework_xp(self.homework)

        self.assertEqual(
            get_student_xp(self.student),
            10,
        )

        self.homework.status = "PENDING"
        self.homework.completed_at = None
        self.homework.save()

        sync_homework_xp(self.homework)

        self.assertEqual(
            get_student_xp(self.student),
            0,
        )

        self.assertEqual(
            StudentXPTransaction.objects.filter(
                homework=self.homework
            ).count(),
            0,
        )

    def test_manual_admin_xp_sources_do_not_exist(self):
        """
        Student XP must only support automatic homework XP.
        """

        sources = dict(
            StudentXPTransaction.SOURCE_CHOICES
        )

        self.assertIn(
            "HOMEWORK_COMPLETED",
            sources,
        )

        self.assertNotIn(
            "ADMIN_INCREASE",
            sources,
        )

        self.assertNotIn(
            "ADMIN_DECREASE",
            sources,
        )