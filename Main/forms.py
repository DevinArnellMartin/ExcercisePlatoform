from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm ,AuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.forms.models import inlineformset_factory
from django.forms import formset_factory


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
        labels = {
            'height': 'Meters', #TODO Add label next to fields.
            'weight': 'Kilograms'
            }
    #TODO Check with save method in model for Profile to make sure it is not doing the BMI twice
    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            profile = Profile.objects.create(
                user=user,
                height=self.cleaned_data['height'],
                weight=self.cleaned_data['weight'],
                BMI=self.cleaned_data['weight'] / ((self.cleaned_data['height'] / 100) ** 2)  
            )
        return user

#TODO With model consolidation - make so form is concise with more fields and add exercises to it 
class WorkoutSessionForm(forms.ModelForm):
    class Meta:
        model = WorkoutSession
        fields = ['title',"workout_type","start_time","end_time"]

class SetForm(forms.ModelForm):
    class Meta:
        model = Set
        fields = ['exercise', 'reps', 'weight']
        
# SetFormSet = formset_factory( Set, extra=5, can_delete=True,max_num=5 ,min_num= 2) # makes extra=n amount of forms
SetFormSet = inlineformset_factory(WorkoutSession,Set,extra=5,can_delete=True,validate_max=5,validate_min=2 , 
                                   min_num=2, max_num=5,exclude=('workout_session',))