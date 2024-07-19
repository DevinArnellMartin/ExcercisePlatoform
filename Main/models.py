from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.db.models import Count

"""
to_field attr => lets Django know which field to reference of the relationship default would be the primary key which is usually a number
Idea - forced to log weight before signing off
"""
class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    height = models.FloatField()  
    weight = models.FloatField()  
    BMI = models.FloatField(null=True, blank=True)  
    Goal_BMI = models.FloatField(null=True , blank=True)
    Goal_Weight = models.FloatField(null=True, blank=True)
    send_reminders = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        """Converts into appopriate units to calculate BMI"""
        if self.height and self.weight:
            self.height = self.height /100
            self.weight = self.weight * .4535 
            self.BMI = self.weight / (self.height ** 2) #TODO Keep track of change in BMI. This is initial BMI
        super(Profile, self).save(*args, **kwargs)

    def get_favorite_exercise(self):
        favorite_exercise = (
            Set.objects.filter(workout_session__profile=self)
            .values('exercise__name')
            .annotate(exercise_count=Count('exercise'))
            .order_by('-exercise_count')
            .first()
        )
        return favorite_exercise['exercise__name'] if favorite_exercise else None

    def get_favorite_type(self):
        favorite_type = (
            WorkoutSession.objects.filter(profile=self)
            .values('workout_type')  # Adjust this line if workout_type is a foreign key
            .annotate(type_count=Count('workout_type'))
            .order_by('-type_count')
            .first()
        )
        return favorite_type['workout_type'] if favorite_type else None
        
    def __str__(self):
        return self.user.username

#Fix model redundancy?
class Exercise(models.Model):
    class ExerciseType(models.TextChoices):
        CARDIO = 'Cardio', _('Cardio')
        WEIGHT_LIFTING = 'Weight-Lifting', _('Weight-Lifting')
        CALISTHENICS = 'Calisthenics', _('Calisthenics')
        HIIT = 'HIIT', _('HIIT')
        CROSSFIT = 'Crossfit', _('Crossfit')

    name = models.CharField(max_length=100,unique=True)
    exercises = models.ManyToOneRel("WorkoutSession","WorkoutSession",
                                    field_name="exercise",related_name="exercises")
    exercise_type = models.CharField(
        max_length=20,
        choices=ExerciseType.choices,
        default=ExerciseType.CARDIO,
    )

    def __str__(self):
        return self.name

class WorkoutSession(models.Model):
    class WorkoutType(models.TextChoices):
        CARDIO = 'Cardio', _('Cardio')
        WEIGHT_LIFTING = 'Weight-Lifting', _('Weight-Lifting')
        CALISTHENICS = 'Calisthenics', _('Calisthenics')
        HIIT = 'HIIT', _('HIIT')
        CROSSFIT = 'Crossfit', _('Crossfit')

    title = models.CharField(blank=True , null=False,max_length=100) 
    id = models.AutoField(primary_key=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    curr_body_weight = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)
    start_time = models.TimeField(blank=True,null=False) 
    end_time = models.TimeField(blank=True,null=False)
    duration = models.DurationField(blank=False,null=False)
    workout_type = models.CharField(
        max_length=20,
        choices=WorkoutType.choices,
        blank=True,
    )

    def __str__(self):
        return f"{self.profile.user.username} - {self.date}"
    
    def determine_workout_type(self):
        exercise_types = self.exercises.values_list('exercise_type', flat=True)
        if exercise_types:
            return max(set(exercise_types), key=exercise_types.count)
        return WorkoutSession.WorkoutType.CARDIO 

class Set(models.Model):
    workout_session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise,blank=True , on_delete=models.CASCADE)
    reps = models.IntegerField()
    weight = models.FloatField() # of equipment
    

    
    def __str__(self):
        return f"{self.workout_session.profile.user.username} - {self.exercise.name} - {self.reps} reps @ {self.weight} lbs"

#TODO Redundant but figure out how to integrate into things. Form in forms.py and render through home view and bmi.html
class WeightHeightEntry(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE) #Migrate:Every model connects to Profile and only the Profile connects to the User
    weight = models.FloatField()
    height = models.FloatField()
    date_recorded = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.weight} kg at {self.height} on {self.date_recorded}"
