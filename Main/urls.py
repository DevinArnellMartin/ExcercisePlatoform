from django.urls import path
from django.conf.urls import include
from . import views as v

urlpatterns = [
    path('', include("django.contrib.auth.urls")),
    path('',v.home , name='home'),  
    path('workouts/',v.WorkoutSessionListSearch.as_view(),name="WorkoutSessionSearch"),
    path('workouts/<str:keyword>',v.WorkoutSessionListSearch.as_view(),name="WorkoutSessionSearch"),
    path('registration/', v.registration, name='registration'),
    path('login/', v.CustomLoginView.as_view(), name='login'),
    path('logout/', v.logout, name='logout'),
    path('deleteWorkout/<str:title>/<int:WorkoutSession_id>/', v.delete_WorkoutSession, name='delete_WorkoutSession'),
    path('createWorkout/', v.create_WorkoutSession, name='createWorkoutSession'),
    path('updateWorkout/<int:WorkoutSession_id>/', v.update_WorkoutSession, name='update_WorkoutSession'),
    path('detail/<int:id>/<str:title>',v.WorkoutSessionDetail.as_view(),name="WorkoutSessionDetail"), 
    path('bug/',v.bug, name="bug_report"),
    path('workout-statistics/',v.view_statistics, name="statistics"),
    path('tutorial/', v.tutorial_view, name='tutorial'),
    path('remind/', v.remind, name='remind'),
]
