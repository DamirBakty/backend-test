from django.db.models import Count
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from users.models import Subscription


@receiver(post_save, sender=Subscription)
def post_save_subscription(sender, instance: Subscription, created, **kwargs):
    """
    Распределение нового студента в группу курса.

    """

    if created:
        course = instance.course
        user = instance.user

        groups = course.groups.annotate(
            user_count=Count('users')
        ).order_by('user_count')

        if groups.exists():
            group = groups.first()
            group.users.add(user)
