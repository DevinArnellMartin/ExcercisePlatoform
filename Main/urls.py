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
    path('deleteWorkout/<str:title>/<int:id>', v.delete_WorkoutSession, name='deleteWorkoutSession'),
    path('createWorkout/', v.create_WorkoutSession, name='createWorkoutSession'),
    path('updateWorkout/<int:id>',v.update_WorkoutSession,name="updateWorkoutSession"),
    path('detail/<str:title>/<int:id>',v.WorkoutSessionDetail.as_view(),name="WorkoutSessionDetail"),  
    
]
