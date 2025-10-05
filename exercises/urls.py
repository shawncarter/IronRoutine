from django.urls import path
from . import views

app_name = 'exercises'

urlpatterns = [
    path('', views.exercise_list, name='exercise_list'),
    path('<int:exercise_id>/', views.exercise_detail, name='exercise_detail'),
    path('search/', views.exercise_search, name='exercise_search'),
]