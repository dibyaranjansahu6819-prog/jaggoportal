from rest_framework import status
from rest_framework.test import APITestCase

from .models import Student, StudentRegistrationSequence


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