from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

@shared_task
def send_workout_reminders():
    now = timezone.now().time()
    users = User.objects.filter(profile__send_reminders=True, profile__preferred_workout_time__lte=now, profile__preferred_workout_time__gte=(now - timedelta(minutes=30)))
    for user in users:
        send_mail(
            'Workout Reminder',
            'It\'s time for your workout!',
            'from@example.com',
            [user.email],
            fail_silently=False,
        )
