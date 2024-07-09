from typing import Any
from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm ,AuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.forms.models import inlineformset_factory
from django.forms import formset_factory
from django.db.models.query import QuerySet
import plotly.express as px
import pandas as pd 
from django.core.exceptions import ValidationError
from django.apps import apps
import datetime


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
    #TODO Provide help text: For Registration Fields
    class Meta: 
        model = User
        fields = ['username', 'password1', 'password2', "email" ,'height', 'weight']
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
        return user

class ReminderForm(forms.Form):
    #TODO Check if works copied 
    workout_type = forms.ModelMultipleChoiceField(
        queryset=WorkoutSession.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        help_text="Select the types of workouts you want to be reminded about"
    )
    time_duration = forms.DateTimeField(
        help_text="Enter the date and time for the reminder (format: YYYY-MM-DD HH:MM:SS)",
        input_formats=['%Y-%m-%d %H:%M:%S']
    )
    receiver = forms.EmailField(help_text="Enter the email address to receive the reminder")
    
    def clean_time_duration(self):
        time_duration = self.cleaned_data['time_duration']
        if time_duration < datetime.now():
            raise forms.ValidationError("The reminder time must be in the future.")
        return time_duration

class WorkoutSessionForm(forms.ModelForm):
    class Meta:
        model = WorkoutSession
        fields = ['title',"workout_type" , "curr_body_weight","start_time","end_time"]
        #TODO Fix Curr_body_weight label make it more readible

class SetForm(forms.ModelForm):
    new_exercise = forms.CharField(
        label="New Exercise",
        help_text="Do not see an exercise? Add one here",
        required=False,
    )

    class Meta:
        model = Set
        fields = ['exercise', 'reps', 'weight', 'new_exercise']
    
    def clean(self):
        cleaned_data = super().clean()
        exercise_name = cleaned_data.get('new_exercise')
        exercise = cleaned_data.get('exercise')
        reps = cleaned_data.get('reps')
        
        if exercise and exercise.type == "CARDIO":
            cleaned_data['reps'] = 0  # or disable reps fields
        if not exercise_name and not exercise:
            raise forms.ValidationError("Must list an exercise")
        if exercise_name and Exercise.objects.filter(name=exercise_name).exists():
            raise forms.ValidationError("Exercise with this name already exists")
        
        if exercise_name and not Exercise.objects.filter(name=exercise_name).exists():
            exercise, created = Exercise.objects.get_or_create(name=exercise_name)
            self.instance.exercise = exercise

        return cleaned_data

    def save(self, commit=True):
        exercise_name = self.cleaned_data.get('new_exercise')
        if exercise_name:
            exercise, created = Exercise.objects.get_or_create(name=exercise_name)
            self.instance.exercise = exercise
        return super().save(commit=commit)

SetFormSet = inlineformset_factory(
    WorkoutSession, 
    Set, 
    form=SetForm,
    extra=5,
    validate_min=True, 
    min_num=1, 
    max_num=5, 
    can_delete=False,
    exclude=('workout_session',)
)
        
class BugForm(forms.Form):
    """Does not need a model; send straight to email"""
    #Extra : Next sprint cycle => autopopulate to user whom has an account their email address
    email = forms.EmailField(required=False,
                             help_text="Enter email incase we need to follow up on the bug",
                             error_messages={"Invalid":"Invalid Email Address"}
                             ,empty_value="Your email")
    desc = forms.CharField(widget=forms.Textarea) 
    severity = {"Severe":"Severe","Not Severe":"Not Severe", "Suggestion":"Suggestion"}
    
    bug_type = forms.ChoiceField(widget=forms.RadioSelect,choices = severity)
    
    def clean(self) -> dict[str, Any]:
        """If valid, send. Else throw error."""
        return super().clean()

class WeightHeightEntryForm(forms.ModelForm):
    class Meta:
        model = WeightHeightEntry
        fields = ['weight','height']
        labels = {'weight': 'Current Weight (kg)' ,'height': "Current Height (m)"}

#TODO LATER- Extra Functionality - Creates Graph User Wants To See
class CustomGraphForm(forms.Form):
    """Form so user can create custom graph to display data
    Y disabled in case they don't want a graph"""
    x = forms.CharField(max_length=25, help_text="Enter independent variable")
    y = forms.CharField(max_length=25, help_text="Enter dependent variable", required=False)

    def clean(self):
        cleaned_data = super().clean()
        x = cleaned_data.get("x")
        y = cleaned_data.get("y")

        if not x:
            raise ValidationError("The independent variable (x) is required.")

        return cleaned_data

    def save(self):
        cleaned_data = self.cleaned_data
        x = cleaned_data.get("x")
        y = cleaned_data.get("y")

        matching_models = []
        for model in apps.get_models():
            fields = [f.name for f in model._meta.get_fields()]
            if x in fields and (y in fields or y is None):
                matching_models.append(model)

        if not matching_models:
            raise ValidationError("No matching models found for the provided fields.")

        data_frames = []
        for model in matching_models:
            if y:
                data = model.objects.values(x, y)
                df = pd.DataFrame(list(data), columns=[x, y])
            else:
                data = model.objects.values_list(x, flat=True)
                df = pd.DataFrame(list(data), columns=[x])
            data_frames.append(df)

        if not data_frames:
            raise ValidationError("No data found for the provided fields.")

        combined_df = pd.concat(data_frames, ignore_index=True)

        if y:
            fig = px.scatter(combined_df, x=x, y=y)
        else:
            fig = px.histogram(combined_df, x=x)

        return fig.to_html()
