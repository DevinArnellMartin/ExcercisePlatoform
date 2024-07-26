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
import logging
logger = logging.getLogger(__name__)
User = get_user_model()
context = {
        'title': "Welcome to Gymcel",
        'registration': RegistrationForm(),
        'bmi': None,
        'bmi_plot': None,
        'weight_plot': None,
        "goal_bmi": None,
        "H-W plot":None,
        "conglomerate_plot":None,
        "exercise_circle_graph":None, #TODO Circle graph of ratio of all different exercises done
        'UserWorkoutSessions':None,
        "form": None,
        "formset":None,
        "goal_weight":None,
}

statistical_context ={
    "favorite_exercise" : None ,
    "bmi-plot": None, #TODO Implement again or delete
    "create": CustomGraphForm(),
    "favorite_type": None,
    "custom_plot":None,
    "goal_weight":context["goal_weight"],
    "goal_bmi": context["goal_bmi"],
    "custom":"None",
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
        #TODO Fix so that is parses through keywords in Workout Title. Extra: Make exact
        keyword = self.request.GET.get('keyword') 
        user = self.request.user
        if keyword is not None:
            try:
                date_condition = Q(date__iexact=keyword, profile__user__exact=user)
                duration_condition = Q(duration__iexact=keyword, profile__user__exact=user)
                title_condition = Q(title__iexact=keyword,profile__user__exact=user)
                combined_condition =  date_condition | duration_condition | title_condition

                matching_WorkoutSessions = WorkoutSession.objects.filter(combined_condition,profile__user=user) 
                return matching_WorkoutSessions
            except Exception as e:   
                messages.warning(self.request,"Internal Error")
                # raise ValidationError(e)

        else: 
            return WorkoutSession.objects.filter(profile__user=user)
    
    def get_context_data(self, *args,**kwargs):
        context = super().get_context_data(**kwargs)
        context['keyword'] = self.request.GET.get('keyword','None')
        return context
    
@login_required
def log_weight(request):
    """Redundant=> dont use"""
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

def generate_custom_chart(chart_data):
    df = pd.DataFrame(chart_data) 
    fig = px.line(df, x='x_axis', y='y_axis') 
    return fig.to_html(full_html=False)

def view_statistics(request):
    profile = Profile.objects.get(user=request.user)
    statistical_context['favorite_type'] = profile.get_favorite_type() 
    statistical_context['favorite_exercise'] = profile.get_favorite_exercise()

    if request.method == "POST":
        form = CustomGraphForm(request.POST)
        if form.is_valid():
            chart_data = form.cleaned_data
            custom_chart = generate_custom_chart(chart_data)
            statistical_context['custom_chart'] = custom_chart
        else:
            statistical_context['create'] = form
    else:
        statistical_context['create'] = CustomGraphForm()

    return render(request, 'statistics.html', statistical_context)

def tutorial_view(request):
    return render(request, 'tutorial.html')

def bug(request):
    if request.method == "POST":
        form = BugForm(request.POST)
        if form.is_valid():
            subject = f"{form.cleaned_data['Bug_Type']}-Type Bug Report: {request.user}"
            message = form.cleaned_data['Description']
            try:
                send_mail(subject, message, "devinmartin45654@yahoo.com", recipient_list=['devin.martin.lpa@gmail.com'])
                return redirect("main:home")
            except Exception as e:
                 messages.error(request,e)
        else:
            messages.error(request,form.errors.values())
    else:
        form = BugForm()

    return render(request, 'bug.html', {"bug": form})

def edit_settings(request):
    profile = get_object_or_404(Profile, user=request.user)
    remind = ReminderForm(request.POST)
    edit = ProfileForm(request.POST, instance=profile)
    if edit.is_valid():
            email = edit.cleaned_data["Email"]
            profile.user.email = email
            edit.save()
            messages.success(request,"Settings Saved!")
            redirect("main:home")

    if remind.is_valid():
            workout_types = remind.cleaned_data['workout_type']
            time_duration = remind.cleaned_data['time_duration']
            receiver = remind.cleaned_data['receiver']
            
            subject = "Workout Reminder"
            workout_names = ", ".join([workout.name for workout in workout_types])
            message = f"Reminder: Your workout session for {workout_names} is scheduled at {time_duration}."
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [receiver]
            
            send_mail(subject, message, from_email, recipient_list)
            
            messages.success(request,"Reminder Sent")
            redirect("main:home")
    else:
        form = ProfileForm()
        remind = ReminderForm()
    return render(request, 'edit_profile.html', {'edit': edit, 'remind':remind})

def home(request):
    """Everything rendered from here"""
    context["registration"] =  RegistrationForm(request.POST)
    graph_type_form = GraphTypeForm(request.POST)
    context["graph_type_form"] = graph_type_form
    if request.user.is_authenticated:
        profile = get_object_or_404(Profile, user=request.user)

        context['title'] = f"{request.user}'s Gym"
        context['UserWorkoutSessions'] = WorkoutSession.objects.filter(profile__user=request.user.id).order_by('date')[:5]
        context['createWorkoutSession'] = WorkoutSessionForm(request.POST)
        context['bmi'] = profile.BMI
        context['registration'] = None
        context["goal_bmi"] = profile.Goal_BMI
        context["H-W form"] = WeightHeightEntryForm(request.POST)
      
        adjustable_param = 7 #TODO
        bmi_data = {
            'weight': [getattr(session, "curr_body_weight") for session in context['UserWorkoutSessions'][:adjustable_param]],
            'height': [profile.height for _ in range(len(context['UserWorkoutSessions'][:adjustable_param]))]
        }

        df_bmi = pd.DataFrame(bmi_data)
        df_bmi['bmi'] = df_bmi['weight'] / (df_bmi['height'] / 100) ** 2

        # Determine graph type
        if graph_type_form.is_valid():
            graph_type = graph_type_form.cleaned_data['graph_type']
        else:
            graph_type = 'scatter' 

        if graph_type == 'line':
            fig_bmi = px.line(df_bmi, x='height', y='weight', title='Height vs. Weight', labels={'height': 'Height (m)', 'weight': 'Weight (kg)'})
            fig_weight = px.line(x=list(range(len(bmi_data['weight']))), y=bmi_data['weight'], title='Weight Over Time', labels={'x': 'Session', 'y': 'Weight (kg)'})
            fig_height_weight = px.line(df_bmi, x='height', y='weight', title='Height to Weight', labels={'height': 'Height (cm)', 'weight': 'Weight (kg)'})
        else:
            fig_bmi = px.scatter(df_bmi, x='height', y='weight', size='bmi', title='Height vs. Weight', labels={'height': 'Height (cm)', 'weight': 'Weight (kg)'})
            fig_weight = px.scatter(x=list(range(len(bmi_data['weight']))), y=bmi_data['weight'], title='Weight Over Time', labels={'x': 'Session', 'y': 'Weight (kg)'})
            fig_height_weight = px.scatter(df_bmi, x='height', y='weight', title='Height to Weight', labels={'height': 'Height (cm)', 'weight': 'Weight (kg)'})

        context['bmi_plot'] = fig_bmi.to_html(full_html=False)
        context['weight_plot'] = fig_weight.to_html(full_html=False)
        context['height_weight_plot'] = fig_height_weight.to_html(full_html=False)

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
            errors = form.errors.values()
            messages.error(request, errors) 
    else:
        form = RegistrationForm()
    return render(request, 'home.html', {'title': title, 'registration': form})

def logout(request):
    if request.method == 'POST' or request.method == 'GET':
        context["title"] = "Welcome to Gymcell"
        dj_logout(request)
        messages.success(request,"Logout Successful")
    else:
        return HttpResponseNotAllowed(['POST', 'GET'])

def create_WorkoutSession(request):
    #TODO Fixed- make sure to show erroes on Tempalte
    if request.method == 'POST':
        form = WorkoutSessionForm(request.POST)
        formset = SetFormSet(request.POST) 
        if form.is_valid() and formset.is_valid():
            profile = get_object_or_404(Profile, user=request.user)
            workout_session = form.save(commit=False)
            workout_session.profile = profile

            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            workout_session.curr_body_weight = profile.weight

            duration = datetime.datetime.combine(
                datetime.date.today(), end_time
            ) - datetime.datetime.combine(
                datetime.date.today(), start_time
            )
            workout_session.duration = duration
            workout_session.save()

            sets = formset.save(commit=False)
            for set_instance in sets:
                set_instance.workout_session = workout_session
                set_instance.save()
            
            formset.save_m2m()   
            messages.success(request, "Workout Created")
            return redirect('main:home')
        else:
            #TODO Print on HTML.
            print(form.errors)
            print(formset.errors)
    else:
        form = WorkoutSessionForm()
        formset = SetFormSet(queryset=Set.objects.none())  
    
    return render(request, 'create.html', {"form": form, "formset": formset , "form_err": form.errors, "formset_err":formset.errors})

def update_WorkoutSession(request, WorkoutSession_id):
    workout_session = get_object_or_404(WorkoutSession, id=WorkoutSession_id)
    if request.method == 'POST':
        form = WorkoutSessionForm(request.POST, instance=workout_session)
        if form.is_valid():
            form.save()
            return redirect('main:home')
    else:
        form = WorkoutSessionForm(instance=workout_session)
    
    return render(request, 'update.html', {'updateWorkoutSession': form, 'workout_session': workout_session})

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
    