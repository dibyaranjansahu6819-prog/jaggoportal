from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import UserProfile
from attendance.models import AttendanceSession, VolunteerAttendance
from admin2.models import VolunteerAssignment
from courses.models import Course, Subject
from teachers.models import Teacher, SpecialAddedWorkAccess


class SpecialAddedWorkAccessTests(TestCase):
    """
    Module 1 tests:

    Admin1 adds a volunteer as SPECIAL_ADDED and marks them PRESENT.
    That volunteer can see work belonging to an assigned volunteer
    who is ABSENT today, and can select exactly one assignment.
    """

    def setUp(self):
        self.client = APIClient()

        # ========================================================
        # COURSE / SUBJECT
        # ========================================================

        self.course = Course.objects.create(
            name="Science"
        )

        self.subject = Subject.objects.create(
            name="Mathematics"
        )

        # ========================================================
        # ADMIN 1
        # ========================================================

        self.admin_user = User.objects.create_user(
            username="module1_admin",
            email="module1_admin@example.com",
            password="AdminPassword123",
        )

        UserProfile.objects.create(
            user=self.admin_user,
            role="ADMIN1",
            is_active=True,
        )

        # ========================================================
        # ORIGINAL VOLUNTEER
        # ========================================================

        self.original_user = User.objects.create_user(
            username="original@example.com",
            email="original@example.com",
            password="VolunteerPassword123",
        )

        UserProfile.objects.create(
            user=self.original_user,
            role="TEACHER_VOLUNTEER",
            is_active=True,
        )

        # ========================================================
        # SPECIAL ADDED VOLUNTEER
        # ========================================================

        self.special_user = User.objects.create_user(
            username="special@example.com",
            email="special@example.com",
            password="VolunteerPassword123",
        )

        UserProfile.objects.create(
            user=self.special_user,
            role="TEACHER_VOLUNTEER",
            is_active=True,
        )

        # ========================================================
        # OTHER VOLUNTEER
        # ========================================================

        self.other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="VolunteerPassword123",
        )

        UserProfile.objects.create(
            user=self.other_user,
            role="TEACHER_VOLUNTEER",
            is_active=True,
        )

        # ========================================================
        # COMMON TEACHER DATA
        # ========================================================

        common = {
            "course": self.course,
            "joining_year": 2026,
            "subject": self.subject,
            "whatsapp_number": "9876543210",
            "free_days": [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
            ],
            "password": "",
        }

        # ========================================================
        # TEACHERS
        # ========================================================

        self.original = Teacher.objects.create(
            auth_user=self.original_user,
            user_id="ORIG001",
            name="Original Volunteer",
            email="original@example.com",
            **common,
        )

        self.special = Teacher.objects.create(
            auth_user=self.special_user,
            user_id="SPEC001",
            name="Special Volunteer",
            email="special@example.com",
            **common,
        )

        self.other = Teacher.objects.create(
            auth_user=self.other_user,
            user_id="OTHR001",
            name="Other Volunteer",
            email="other@example.com",
            **common,
        )

        # ========================================================
        # TODAY
        # ========================================================

        self.today = timezone.localdate()

        # ========================================================
        # ORIGINAL VOLUNTEER ASSIGNMENT
        # ========================================================

        self.assignment = VolunteerAssignment.objects.create(
            volunteer=self.original,
            assignment_date=self.today,
            assigned_class="ClassA",
            task="TEACHING",
            instruction="Teach mathematics.",
            email_status="SENT",
            created_by=self.admin_user,
        )

        # ========================================================
        # SECOND VOLUNTEER ASSIGNMENT
        # ========================================================

        self.second_assignment = VolunteerAssignment.objects.create(
            volunteer=self.other,
            assignment_date=self.today,
            assigned_class="ClassB",
            task="CHECKING",
            instruction="Check homework.",
            email_status="SENT",
            created_by=self.admin_user,
        )

        # ========================================================
        # ATTENDANCE SESSION
        # ========================================================

        self.attendance_session = AttendanceSession.objects.create(
            admin=self.admin_user,
            session_date=self.today,
            expires_at=timezone.now() + timedelta(minutes=10),
            is_active=True,
        )

        # ========================================================
        # ORIGINAL VOLUNTEER = ABSENT
        # ========================================================

        VolunteerAttendance.objects.create(
            session=self.attendance_session,
            volunteer=self.original,
            task="TEACHING",
            status="ABSENT",
            attendance_source="ASSIGNED",
        )

        # ========================================================
        # OTHER VOLUNTEER = ABSENT
        # ========================================================

        VolunteerAttendance.objects.create(
            session=self.attendance_session,
            volunteer=self.other,
            task="CHECKING",
            status="ABSENT",
            attendance_source="ASSIGNED",
        )

        # ========================================================
        # SPECIAL ADDED VOLUNTEER = PRESENT
        # ========================================================

        VolunteerAttendance.objects.create(
            session=self.attendance_session,
            volunteer=self.special,
            task="TEACHING",
            status="PRESENT",
            attendance_source="SPECIAL_ADDED",
        )

        # Authenticate as Special Added volunteer
        self.client.force_authenticate(
            user=self.special_user
        )

    # ============================================================
    # TEST 1
    # ============================================================

    def test_special_added_present_can_see_absent_assigned_work(self):
        response = self.client.get(
            "/api/teachers/special-added/available-work/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        data = response.json()

        self.assertTrue(
            data["eligible"]
        )

        self.assertFalse(
            data["selected"]
        )

        self.assertEqual(
            len(data["available_work"]),
            2,
        )

        assignment_ids = {
            item["id"]
            for item in data["available_work"]
        }

        self.assertIn(
            self.assignment.id,
            assignment_ids,
        )

        self.assertIn(
            self.second_assignment.id,
            assignment_ids,
        )

    # ============================================================
    # TEST 2
    # ============================================================

    def test_special_added_absent_cannot_access_work(self):
        special_attendance = VolunteerAttendance.objects.get(
            volunteer=self.special
        )

        special_attendance.status = "ABSENT"

        special_attendance.save(
            update_fields=["status"]
        )

        response = self.client.get(
            "/api/teachers/special-added/available-work/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        data = response.json()

        self.assertFalse(
            data["eligible"]
        )

        self.assertEqual(
            data["available_work"],
            [],
        )

    # ============================================================
    # TEST 3
    # ============================================================

    def test_present_original_volunteer_work_is_not_available(self):
        original_attendance = VolunteerAttendance.objects.get(
            volunteer=self.original
        )

        original_attendance.status = "PRESENT"

        original_attendance.save(
            update_fields=["status"]
        )

        response = self.client.get(
            "/api/teachers/special-added/available-work/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        ids = {
            item["id"]
            for item in response.json()["available_work"]
        }

        self.assertNotIn(
            self.assignment.id,
            ids,
        )

        self.assertIn(
            self.second_assignment.id,
            ids,
        )

    # ============================================================
    # TEST 4
    # ============================================================

    def test_special_added_can_select_one_work(self):
        response = self.client.post(
            "/api/teachers/special-added/select-work/",
            {
                "assignment": self.assignment.id
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        access = SpecialAddedWorkAccess.objects.get(
            special_volunteer=self.special
        )

        self.assertEqual(
            access.assignment,
            self.assignment,
        )

        self.assertEqual(
            access.attendance.volunteer,
            self.special,
        )

        self.assertEqual(
            access.status,
            "ACTIVE",
        )

    # ============================================================
    # TEST 5
    # ============================================================

    def test_special_added_cannot_select_second_work(self):
        first = self.client.post(
            "/api/teachers/special-added/select-work/",
            {
                "assignment": self.assignment.id
            },
            format="json",
        )

        self.assertEqual(
            first.status_code,
            status.HTTP_201_CREATED,
        )

        second = self.client.post(
            "/api/teachers/special-added/select-work/",
            {
                "assignment": self.second_assignment.id
            },
            format="json",
        )

        self.assertEqual(
            second.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            second.json()["code"],
            "WORK_ALREADY_SELECTED",
        )

    # ============================================================
    # TEST 6
    # ============================================================

    def test_same_work_cannot_be_taken_by_second_special_added_volunteer(self):
        first = self.client.post(
            "/api/teachers/special-added/select-work/",
            {
                "assignment": self.assignment.id
            },
            format="json",
        )

        self.assertEqual(
            first.status_code,
            status.HTTP_201_CREATED,
        )

        # Create another volunteer
        another_user = User.objects.create_user(
            username="special2@example.com",
            email="special2@example.com",
            password="VolunteerPassword123",
        )

        UserProfile.objects.create(
            user=another_user,
            role="TEACHER_VOLUNTEER",
            is_active=True,
        )

        another = Teacher.objects.create(
            auth_user=another_user,
            user_id="SPEC002",
            name="Second Special Volunteer",
            course=self.course,
            joining_year=2026,
            subject=self.subject,
            email="special2@example.com",
            whatsapp_number="9876543211",
            free_days=["Monday"],
            password="",
        )

        # The second Special Added volunteer must also be
        # PRESENT in the same attendance session.
        VolunteerAttendance.objects.create(
            session=self.attendance_session,
            volunteer=another,
            task="CHECKING",
            status="PRESENT",
            attendance_source="SPECIAL_ADDED",
        )

        self.client.force_authenticate(
            user=another_user
        )

        response = self.client.post(
            "/api/teachers/special-added/select-work/",
            {
                "assignment": self.assignment.id
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )

        self.assertEqual(
            response.json()["code"],
            "WORK_ALREADY_TAKEN",
        )

    # ============================================================
    # TEST 7
    # ============================================================

    def test_own_assignment_cannot_be_selected(self):
        """
        A Special Added volunteer must never be allowed to select
        an assignment that belongs to themselves.

        Important:
        The attendance session already contains the Special Added
        volunteer's attendance record from setUp(). Because the
        database correctly enforces one attendance record per
        volunteer per session, we must NOT create another
        attendance record here.
        """

        own_assignment = VolunteerAssignment.objects.create(
            volunteer=self.special,
            assignment_date=self.today,
            assigned_class="ClassC",
            task="TEACHING",
            instruction="Own work.",
            email_status="SENT",
            created_by=self.admin_user,
        )

        response = self.client.post(
            "/api/teachers/special-added/select-work/",
            {
                "assignment": own_assignment.id
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.json()["code"],
            "OWN_ASSIGNMENT_NOT_ALLOWED",
        )

    # ============================================================
    # TEST 8
    # ============================================================

    def test_current_work_returns_selected_assignment(self):
        self.client.post(
            "/api/teachers/special-added/select-work/",
            {
                "assignment": self.assignment.id
            },
            format="json",
        )

        response = self.client.get(
            "/api/teachers/special-added/current-work/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        data = response.json()

        self.assertTrue(
            data["eligible"]
        )

        self.assertTrue(
            data["selected"]
        )

        self.assertEqual(
            data["work"]["id"],
            self.assignment.id,
        )