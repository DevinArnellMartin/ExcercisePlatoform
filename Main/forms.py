from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm ,AuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

User = get_user_model()


class CustomLoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    class Meta:
        model = Profile 
        
class RegistrationForm(UserCreationForm):
    height = forms.IntegerField()
    weight = forms.IntegerField()

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'height', 'weight']

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            profile = Profile.objects.create(
                user=user,
                height=self.cleaned_data['height'],
                weight=self.cleaned_data['weight'],
                BMI=self.cleaned_data['weight'] / ((self.cleaned_data['height'] / 100) ** 2)  # Calculate BMI
            )
        return user


class WorkoutSessionForm(forms.ModelForm):
    class Meta:
        model = WorkoutSession
        fields = ['title']