from django.urls import path
from . import views

app_name = 'workouts'

urlpatterns = [
    path('', views.workout_history, name='workout_history'),
    path('session/<int:session_id>/', views.workout_session, name='workout_session'),
    path('session/<int:session_id>/exercise/<int:exercise_id>/', views.workout_exercise, name='workout_exercise'),
    path('session/<int:session_id>/complete/', views.workout_complete, name='workout_complete'),
    path('set/save/', views.save_workout_set, name='save_workout_set'),
]