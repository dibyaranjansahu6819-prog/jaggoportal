from django.urls import path

from .views import CourseListView, SubjectListView


urlpatterns = [
    path("courses/", CourseListView.as_view(), name="course-list"),
    path("subjects/", SubjectListView.as_view(), name="subject-list"),
]