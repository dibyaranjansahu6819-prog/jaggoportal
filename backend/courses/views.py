from rest_framework import generics

from .models import Course, Subject
from .serializers import CourseSerializer, SubjectSerializer


class CourseListView(generics.ListAPIView):
    queryset = Course.objects.all().order_by("name")
    serializer_class = CourseSerializer


class SubjectListView(generics.ListAPIView):
    queryset = Subject.objects.all().order_by("name")
    serializer_class = SubjectSerializer