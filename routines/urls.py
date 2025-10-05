from django.urls import path
from . import views

app_name = 'routines'

urlpatterns = [
    path('', views.routine_list, name='routine_list'),
    path('create/', views.routine_create, name='routine_create'),
    path('<int:routine_id>/', views.routine_detail, name='routine_detail'),
    path('<int:routine_id>/edit/', views.routine_edit, name='routine_edit'),
    path('<int:routine_id>/delete/', views.routine_delete, name='routine_delete'),
    path('<int:routine_id>/start/', views.routine_start, name='routine_start'),
]