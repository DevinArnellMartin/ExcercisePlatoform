from django.db.models.base import Model as Model
from django.shortcuts import render, redirect, get_object_or_404
from Main.models import *
from .forms import *
from django.contrib.auth import login,authenticate,logout as dj_logout
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import  HttpResponseNotAllowed
import pandas  as pd
import plotly.express as px
import datetime
from django.db.models import Count
from django.core.mail import send_mail
import DatabaseProject.settings as settings


User = get_user_model()
context = {
      'title': "Welcome to Gymcel-Hell",
        'registration': RegistrationForm(),
        'bmi': None,
        'bmi_plot': None,
        'weight_plot': None,
        "goal_bmi": None,
        "H-W plot":None,
        "conglomerate_plot":None,
        "exercise_circle_graph":None,
}

statistical_context ={
    "favorite_exercise" : None ,
    "custom-plot": CustomGraphForm(),
    "favorite_type": None,
    "bmi_plot":None,
}

class CustomLoginView(LoginView):
    template_name = 'login.html'
    form_class = CustomLoginForm

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, context={'form': form})
        
    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
            else:
                messages.error(request, "Invalid credentials")
        return render(request, self.template_name, context={'form': form})


class WorkoutSessionListSearch(ListView):
    template_name = "search.html"
    model= WorkoutSession
    
    def get_queryset(self):
        """Return results by all fields 
        iexact = case insensitive
        Might be able to use slug-slug matches any ASCII characters & i think any field
        """
        keyword = self.request.GET.get('keyword') 
        user = self.request.user
        if keyword is not None:
            try:
                date_condition = Q(date__iexact=keyword,profile__iexact=user)
                duration_condition = Q(duration__iexact=keyword,profile__iexact=user)
                title_condition = Q(title__iexact=keyword,profile__iexact=user)
                #Extra Feauture:EXACT search with combined_condition = & with all these . | means "OR"
                combined_condition =  date_condition | duration_condition | title_condition

                matching_WorkoutSessions = WorkoutSession.objects.filter(combined_condition,profile__user=user) #TODO Check if can filter by both
                return matching_WorkoutSessions
            except Exception as e:   
                messages.warning(self.request,f'{e}')
                pass

        else: 
            return WorkoutSession.objects.filter(profile__user=user)
    
    def get_context_data(self, *args,**kwargs):
        context = super().get_context_data(**kwargs)
        context['keyword'] = self.request.GET.get('keyword','None')
        return context
    
@login_required
def log_weight(request):
    if request.method == 'POST':
        form = WeightHeightEntryForm(request.POST)
        if form.is_valid():
            weight_entry = form.save(commit=False)
            weight_entry.user = request.user
            weight_entry.save()
            return redirect('weight_history')
    else:
        form = WeightHeightEntryForm()
    
    return render(request, 'totalHistory.html', {'form': form})


def view_statistics(request):
    #TODO Extra Could be moved to next sprint cycle - Make a chart-based on X and Y and Z axis
    profile = Profile.objects.get(user=request.user)
    #TODO Fix these relationships: Should display most commonly done exercise and type of execerise. #GOTO model.py and fix these methods
    statistical_context['favorite_type'] = profile.get_favorite_type()
    statistical_context['favorite_exercise'] = profile.get_favorite_exercise()
    return render(request,'statistics.html', statistical_context)


def tutorial_view(request):
    return render(request, 'tutorial.html')

def bug(request):
    if request.method == "POST":
        form = BugForm(request.POST)
        if form.is_valid():
            subject = f"{form.cleaned_data['bug_type']} Bug Report: {request.user}"
            message = form.cleaned_data['desc']
            from_email = form.cleaned_data['email']
            try:
                send_mail(subject, message, from_email, recipient_list=['devin.martin.lpa@gmail.com'])
                return redirect("main:home")
            except Exception as e:
                print(f"Failed to send email: {e}")
                form.add_error(None, "Failed to send email. Please try again later.")
    else:
        form = BugForm()

    return render(request, 'bug.html', {"bug": form})

def remind(request):
    #TODO Check if it works
    """"""
    if request.method == "POST":
        form = ReminderForm(request.POST)
        if form.is_valid():
            workout_types = form.cleaned_data['workout_type']
            time_duration = form.cleaned_data['time_duration']
            receiver = form.cleaned_data['receiver']
            
           
            subject = "Workout Reminder"
            workout_names = ", ".join([workout.name for workout in workout_types])
            message = f"Reminder: Your workout session for {workout_names} is scheduled at {time_duration}."
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [receiver]
            
            send_mail(subject, message, from_email, recipient_list)
            
            messages.success(request, "Reminder set successfully! An email will be sent to the provided address.")
            return redirect('main:home')  

    else:
        form = ReminderForm()
    
    return render(request, 'reminder_form.html', {'form': form})


def home(request):
    """ EVERYTHING IS RENDERED FROM THIS LOGIC ON THE HOMEPAGE """
    context["registration"] =  RegistrationForm(request.POST)
    if request.user.is_authenticated:
        profile = get_object_or_404(Profile, user=request.user)

        context['title'] = f"{request.user}'s Gym"
        context['UserWorkoutSessions'] = WorkoutSession.objects.filter(profile__user=request.user.id)
        context['createWorkoutSession'] = WorkoutSessionForm()
        context['bmi'] = profile.BMI
        context['registration'] = None
        context["goal_bmi"] = profile.Goal_BMI
        context["formset"] = SetFormSet()
        context["H-W form"] = WeightHeightEntryForm(request.POST)
      
        #TODO Slice [:x] making X an adjustable parameter
        bmi_data = {
        'weight': [getattr(session, "curr_body_weight") for session in context['UserWorkoutSessions'][:7]],
        'height': [profile.height for _ in range(len(context['UserWorkoutSessions'][:7]))]
        }

        # Creating DataFrame and calculating BMI
        df_bmi = pd.DataFrame(bmi_data)
        df_bmi['bmi'] = df_bmi['weight'] / (df_bmi['height'] / 100) ** 2

        fig_bmi = px.scatter(df_bmi, x='height', y='weight', size='bmi', title='Height vs. Weight', labels={'height': 'Height (m)', 'weight': 'Weight (kg)'})

        context['bmi_plot'] = fig_bmi.to_html(full_html=False)

        # Weight Chart
        # weight_data = [getattr(session, "curr_body_weight") for session in context['UserWorkoutSessions']] 
        # fig_weight = px.scatter(x=weight_data, y=weight_data, title='Weight Scatter Plot', labels={'x': 'Weight @ Workout', 'y': 'Weight'})
        # context['weight_plot'] = fig_weight.to_html(full_html=False)

        #TODO Height-to-weight Chart && Before Logout is Clicked =>> Force User to Enter Weight

    return render(request, 'home.html', context)

def registration(request):
    title = ""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('main:home')
        else:
            messages.error(request, 'Those credentials do not work') 
    else:
        form = RegistrationForm()
    return render(request, 'home.html', {'title': title, 'registration': form})

def logout(request):
    if request.method == 'POST' or request.method == 'GET':
        #redirect()
        dj_logout(request)
        messages.success(request,"Logout Successful")
    else:
        return HttpResponseNotAllowed(['POST', 'GET'])

def create_WorkoutSession(request):
    #TODO Graphs do no show up after submit becuase   - maybe use global context dictionary?
    title = "Create Workout" 
    if request.method == 'POST':
        form = WorkoutSessionForm(request.POST)
        formset = SetFormSet(request.POST) 
        #TODO:Actually test if the SetForm works as intended
        if form.is_valid() and formset.is_valid():
            profile = get_object_or_404(Profile, user=request.user)
            workout_session = form.save(commit=False)
            workout_session.profile = profile
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            workout_session.curr_body_weight = profile.weight
            duration = datetime.datetime.combine(datetime.date.today(), end_time) - datetime.datetime.combine(datetime.date.today(), start_time) #Added 
            workout_session.duration = duration 
            workout_session.save()
            sets = formset.save(commit=False)
            for set in sets:
                set.workout_session = workout_session
                set.save()
            formset.save_m2m()
            return redirect('main:home')
    else:  
        form = WorkoutSessionForm()
        formset = SetFormSet()
    
    return render(request, 'home.html', {'createWorkoutSession': form, "formset": formset, "title": title})


def update_WorkoutSession(request, WorkoutSession_id):
    workout_session = get_object_or_404(WorkoutSession, pk=WorkoutSession_id)
    title = f"Updating: {workout_session.title}"
    if request.method == "POST":
        form = WorkoutSessionForm(request.POST, instance=workout_session)
        if form.is_valid():
            form.save()
            return redirect('main:home')
    else:
        form = WorkoutSessionForm(instance=workout_session)
    return render(request, 'update.html', {'updateWorkoutSession': form, 'title': title, 'WorkoutSession': workout_session})


def delete_WorkoutSession(request, title, WorkoutSession_id):
    """On button click, delete the WorkoutSession associated with the button"""
    workout_session = get_object_or_404(WorkoutSession, pk=WorkoutSession_id, title=title)
    workout_session.delete()
    return redirect('main:home')
    
class WorkoutSessionDetail(DetailView):
    """Detail already has PK handling"""
    model = WorkoutSession
    template_name = "WorkoutSession_detail.html"
    slug_url_kwarg = "title"
    pk_url_kwarg = "id" #need to actually tell the DetailView that this is explicitly the PK

    def get_context_data(self, **kwargs):
        context = super(WorkoutSessionDetail, self).get_context_data(**kwargs)
        workout_session = self.get_object()
        context['sets'] = Set.objects.filter(workout_session=workout_session)
        return context
    