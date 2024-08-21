from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from api.v1.permissions import IsStudentOrIsAdmin, ReadOnlyOrIsAdmin
from api.v1.serializers.course_serializer import (CourseSerializer,
                                                  CreateCourseSerializer,
                                                  CreateGroupSerializer,
                                                  CreateLessonSerializer,
                                                  GroupSerializer,
                                                  LessonSerializer)
from courses.models import Course, Lesson
from users.models import Subscription


class LessonViewSet(viewsets.ModelViewSet):
    """Уроки."""

    permission_classes = (IsStudentOrIsAdmin,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return LessonSerializer
        return CreateLessonSerializer

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer.save(course=course)

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        user = self.request.user
        if user.is_superuser or Subscription.objects.filter(user=user, course=course).exists():
            return course.lessons.all()
        return Lesson.objects.none()


class GroupViewSet(viewsets.ModelViewSet):
    """Группы."""

    permission_classes = (permissions.IsAdminUser,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return GroupSerializer
        return CreateGroupSerializer

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer.save(course=course)

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        if self.request.user.is_superuser:
            return course.groups.all()
        return course.groups.filter(user=self.request.user)


class CourseViewSet(viewsets.ModelViewSet):
    """Курсы"""

    queryset = Course.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CourseSerializer
        return CreateCourseSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Course.objects.all()
        return Course.objects.filter(subscriptions__user=user)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def pay(self, request, pk):
        """Покупка доступа к курсу (подписка на курс)."""

        course = get_object_or_404(Course, pk=pk)
        user = request.user

        if Subscription.objects.filter(user=user, course=course).exists():
            return Response(
                data={
                    'message': 'You are already subscribed to this course'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.balance.amount < course.price:
            return Response(
                data={
                    'message': 'Not enough balance to subscribe to this course'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user.balance.amount -= course.price
        user.balance.save()

        subscription = Subscription.objects.create(
            user=user,
            course=course
        )

        data = {
            'message': 'You are subscribed to this course',
            'subscription_id': subscription.id
        }

        return Response(
            data=data,
            status=status.HTTP_201_CREATED
        )
