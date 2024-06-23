from django.shortcuts import render, redirect, get_object_or_404
from Main.models import *
from .forms import *
from django.contrib.auth import login,authenticate
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.db.models import Q
from django.views import View
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import FormMixin
from django.http import HttpResponse
from django.contrib.auth.models import User
import plotly


User = get_user_model()

"""
"id" is a the PK (actually called "id" ) of the Member field
"""

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

    #def get(self):
       
    def get_queryset(self):
        """Return results by all fields 
        iexact = case insensitive
        Might be able to use slug-slug matches any ASCII characters & i think any field"""
        keyword = self.request.GET.get('keyword') #keyword is value in the URL definition in urls.py <str:keyword>
        if keyword is not None:
            try:
                matching_date = list(WorkoutSession.objects.filter(date__iexact=keyword)) 
                matching_duration = list(WorkoutSession.objects.filter(duration__iexact=keyword))
                # matching_title = list(WorkoutSession.objects.filter(title__iexact=keyword))

                date_condition = Q(date__iexact=keyword)
                duration_condition = Q(duration__iexact=keyword)
                #TODO Toggle EXACT search with combined_condition = & with all these 
                combined_condition =  date_condition | duration_condition

                matching_WorkoutSessions = WorkoutSession.objects.filter(combined_condition) 
                return matching_WorkoutSessions
            except Exception as e:   
                messages.warning(self.request,f'{e}')
                pass

        else: 
            return WorkoutSession.objects.all()
    
    def get_context_data(self, *args,**kwargs):
        context = super().get_context_data(**kwargs)
        context['keyword'] = self.request.GET.get('keyword','None')
        return context

def home(request):
    context = {'title':"Welcome to Excercise",
                'UserWorkoutSessions':None,'updateWorkoutSession':None ,'createWorkoutSession':None , 
                'registration':RegistrationForm(request.POST)}
    if request.user.is_authenticated:
        context['title'] = f"{request.user}'s Gym"
        context['UserWorkoutSessions'] =  WorkoutSession.objects.filter(profile_id=request.user.id)     
        context['createWorkoutSession']= WorkoutSessionForm()
        context['registration'] = None
    
        
    return render(request,"home.html",context)

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
    messages.success(request,"Logout Successful")
   
def create_WorkoutSession(request):
    title ="Create Workout"
    if request.method == 'POST':
        form = WorkoutSessionForm(request.POST)
        if form.is_valid():
            form = form.save(commit=False)
            form.submission_user = request.user
            form.save()
            return redirect('main:home')
    else:
        form = WorkoutSessionForm()
    
    return render(request, 'home.html', {'createWorkoutSession': form, "title":title })

def update_WorkoutSession(request,WorkoutSession_id):
    WorkoutSession = get_object_or_404(WorkoutSession, WorkoutSession_id=WorkoutSession_id )
    title = f"Updating:{WorkoutSession.title}"
    form = WorkoutSessionForm(request.POST, instance=WorkoutSession)
    if form.is_valid():
            form.save()
            return redirect('main:home')

    return render(request, 'update.html', {'updateWorkoutSession': form, 'title': title , 'WorkoutSession':WorkoutSession})

def delete_WorkoutSession(request, title , WorkoutSession_id):
    """On button,click delete the WorkoutSession associated with the button""" 
    WorkoutSession = get_object_or_404(WorkoutSession, WorkoutSession_id=WorkoutSession_id , title=title)
    WorkoutSession.delete()
    return redirect('main:home')
    
class WorkoutSessionDetail(DetailView):
    """Detail already has PK handling"""
    model = WorkoutSession
    template_name = "WorkoutSession_detail.html"
    pk_url_kwarg = "WorkoutSession_id" #need to actually tell the DetailView that this is explicitly the PK

    def get_context_data(self, **kwargs):
        context = super(WorkoutSessionDetail, self).get_context_data(**kwargs)
        #context['object'] = WorkoutSession.objects.filter(WorkoutSession_id= self.kwargs.WorkoutSession_id, title = self.kwargs.title) 
        return context


# NEW STUFF FOR PROJECT!
def bmi_chart_view(request):
    height = [150, 160, 170, 180, 190]
    weight = [50, 60, 70, 80, 90]
    bmi = [w / (h / 100) ** 2 for w, h in zip(weight, height)]
    
    fig = plotly.express.scatter(x=height, y=weight, size=bmi, title='BMI Scatter Plot', labels={'x': 'Height', 'y': 'Weight'})
    bmi_plot = fig.to_html(full_html=False)

    return render(request, 'home.html', context={'bmi_plot': bmi_plot})


def weight_chart_view(request):
    """Fix"""
    weight = [50, 60, 70, 80, 90]
    
    fig = plotly.express.scatter(x=weight, y=weight, title='Weight Scatter Plot', labels={'x': 'TODO', 'y': 'Weight'})
    bmi_plot = fig.to_html(full_html=False)

    return render(request, 'home.html', context={'bmi_plot': bmi_plot})

