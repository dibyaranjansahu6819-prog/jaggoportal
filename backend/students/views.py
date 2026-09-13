from rest_framework import generics

from .models import Student
from .serializers import StudentRegistrationSerializer


class StudentRegistrationView(
    generics.CreateAPIView
):

    queryset = Student.objects.all()

    serializer_class = StudentRegistrationSerializer