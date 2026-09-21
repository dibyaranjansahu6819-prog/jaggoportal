from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import Course, Subject
from .serializers import CourseSerializer, SubjectSerializer


class CourseListView(generics.ListAPIView):
    queryset = Course.objects.all().order_by("name")
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]


class SubjectListView(generics.ListAPIView):
    queryset = Subject.objects.all().order_by("name")
    serializer_class = SubjectSerializer
    permission_classes = [AllowAny]
