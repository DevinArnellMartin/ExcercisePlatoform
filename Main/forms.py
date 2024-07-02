from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm ,AuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.forms.models import inlineformset_factory
from django.forms import formset_factory
from django.db.models.query import QuerySet


User = get_user_model()


class CustomLoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    class Meta:
        model = Profile 
        
class RegistrationForm(UserCreationForm):
    height = forms.FloatField(label="Height (m)")
    weight = forms.FloatField(label="Weight (kg)")
    goal_weight = forms.FloatField(label="Goal Weight")
    goal_bmi = forms.FloatField(label="Goal BMI")
    #TODO Not required: Radio button to convert to meters/kilograms 
    class Meta: 
        model = User
        fields = ['username', 'password1', 'password2', 'height', 'weight']
    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            profile=Profile.objects.create(
                user=user,
                height=self.cleaned_data['height'],
                weight=self.cleaned_data['weight'],
                Goal_BMI = self.cleaned_data['goal_bmi'],
                Goal_Weight = self.cleaned_data['goal_weight']
            )
            #Might be redundant BMI calc: Done in model.py Profile.save() method 
            #BMI=self.cleaned_data['weight'] / ((self.cleaned_data['height'] / 100) ** 2),
        return user

#TODO With model consolidation - make so form is concise with more fields and add exercises to it 
class WorkoutSessionForm(forms.ModelForm):
    class Meta:
        model = WorkoutSession
        fields = ['title',"workout_type","start_time","end_time"]

class SetForm(forms.ModelForm):
    exercise_name = forms.CharField(max_length=100, required=False,label=" New Exercise (?)")

    class Meta:
        model = Set
        fields = ['exercise', 'reps', 'weight']

    def save(self, commit=True):
        exercise_name = self.cleaned_data.get('exercise_name')
        if exercise_name:
            exercise, created = Exercise.objects.get_or_create(name=exercise_name)
            self.instance.exercise = exercise
        return super(SetForm, self).save(commit=commit)
        
SetFormSet = inlineformset_factory(WorkoutSession,Set,extra=5,can_delete=True,validate_min=True , 
                                   min_num=2, max_num=5,exclude=('workout_session',)) #add validate_max=True?

class WeightHeightEntryForm(forms.ModelForm):
    class Meta:
        model = WeightHeightEntry
        fields = ['weight','height']
        labels = {'weight': 'Current Weight (kg)' ,'height': "Current Height (m)"}