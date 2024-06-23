from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


"""
to_field attr => lets Django know which field to reference of the relationship default would be the primary key which is usually a number

"""
class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)
    BMI = models.FloatField(null=True, blank=True)  # Allow null and blank values initially

    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    height = models.IntegerField()  # Height in centimeters
    weight = models.IntegerField()  # Weight in kilograms
    BMI = models.FloatField(null=True, blank=True)  

    def save(self, *args, **kwargs):
        if self.height and self.weight:
            height_in_meters = self.height / 100
            self.BMI = self.weight / (height_in_meters ** 2)
        super(Profile, self).save(*args, **kwargs)

    def __str__(self):
        return self.user.username


class Exercise(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class WorkoutSession(models.Model):
    title = models.TextField(blank=True , null=False)
    id = models.AutoField(primary_key=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    duration = models.TimeField()
    

    def __str__(self):
        return f"{self.profile.user.username} - {self.date}"

class Set(models.Model):
    workout_session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    reps = models.IntegerField()
    weight = models.FloatField()

    def __str__(self):
        return f"{self.workout_session.profile.user.username} - {self.exercise.name} - {self.reps} reps @ {self.weight} lbs"

