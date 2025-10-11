from django.urls import path
from . import views, api_views

app_name = 'exercises'

urlpatterns = [
    # Web views
    path('', views.exercise_list, name='exercise_list'),
    path('<int:exercise_id>/', views.exercise_detail, name='exercise_detail'),
    path('search/', views.exercise_search, name='exercise_search'),
    
    # API endpoints
    path('api/exercises/', api_views.exercise_api_list, name='api_exercise_list'),
    path('api/exercises/<int:exercise_id>/', api_views.exercise_api_detail, name='api_exercise_detail'),
    path('api/muscle-groups/', api_views.muscle_groups_api, name='api_muscle_groups'),
]