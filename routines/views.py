from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Routine, RoutineExercise
from exercises.models import Exercise, MuscleGroup
from workouts.models import WorkoutSession


def routine_list(request):
    # For now, we'll use a default user (since auth is later)
    user, created = User.objects.get_or_create(username='default_user', defaults={
        'first_name': 'Demo',
        'last_name': 'User',
        'email': 'demo@example.com'
    })
    
    routines = Routine.objects.filter(user=user, is_active=True)
    
    context = {
        'routines': routines,
        'user': user,
    }
    return render(request, 'routines/routine_list.html', context)


def routine_detail(request, routine_id):
    routine = get_object_or_404(Routine, id=routine_id)
    routine_exercises = routine.routine_exercises.all().order_by('order')
    
    # Calculate total sets and estimated duration
    total_sets = sum([re.sets_count for re in routine_exercises])
    estimated_duration = routine.get_estimated_duration()
    
    context = {
        'routine': routine,
        'routine_exercises': routine_exercises,
        'total_sets': total_sets,
        'estimated_duration': estimated_duration,
    }
    return render(request, 'routines/routine_detail.html', context)


def routine_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if not name:
            messages.error(request, 'Routine name is required')
            return redirect('routines:routine_create')
        
        # Get default user
        user, created = User.objects.get_or_create(username='default_user', defaults={
            'first_name': 'Demo',
            'last_name': 'User',
            'email': 'demo@example.com'
        })
        
        # Create routine
        routine = Routine.objects.create(
            name=name,
            description=description,
            user=user
        )
        
        # Add exercises to routine
        exercise_order = 0
        for key, value in request.POST.items():
            if key.startswith('exercise_'):
                exercise_id = key.split('_')[1]
                try:
                    exercise = Exercise.objects.get(id=exercise_id)
                    sets_count = int(request.POST.get(f'sets_{exercise_id}', 3))
                    rest_time = int(request.POST.get(f'rest_{exercise_id}', 60))
                    
                    RoutineExercise.objects.create(
                        routine=routine,
                        exercise=exercise,
                        sets_count=sets_count,
                        rest_time_seconds=rest_time,
                        order=exercise_order
                    )
                    exercise_order += 1
                except (Exercise.DoesNotExist, ValueError):
                    continue
        
        messages.success(request, f'Routine "{name}" created successfully!')
        return redirect('routines:routine_detail', routine_id=routine.id)
    
    # GET request - show form with filtering (using same logic as exercise_list)
    exercises = Exercise.objects.all().order_by('title', 'name')
    
    # Get unique muscle groups from actual exercises
    muscle_values = Exercise.objects.exclude(muscle='').values_list('muscle', flat=True).distinct().order_by('muscle')
    muscle_groups = [{'name': muscle} for muscle in muscle_values if muscle]
    
    # Apply filters (exact same logic as exercise_list view)
    search = request.GET.get('search', '')
    muscle_group = request.GET.get('muscle_group', '')
    equipment = request.GET.get('equipment', '')
    difficulty = request.GET.get('difficulty', '')
    
    if search:
        exercises = exercises.filter(
            Q(name__icontains=search) | 
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(muscle__icontains=search)
        ).distinct()
    
    if muscle_group:
        exercises = exercises.filter(
            Q(muscle__icontains=muscle_group)
        ).distinct()
    
    if equipment:
        exercises = exercises.filter(equipment=equipment)
    
    if difficulty:
        exercises = exercises.filter(difficulty=difficulty)
    
    context = {
        'exercises': exercises,
        'muscle_groups': muscle_groups,
        'current_search': search,
        'current_muscle_group': muscle_group,
        'current_equipment': equipment,
        'current_difficulty': difficulty,
    }
    return render(request, 'routines/routine_create.html', context)


def routine_edit(request, routine_id):
    routine = get_object_or_404(Routine, id=routine_id)
    
    if request.method == 'POST':
        routine.name = request.POST.get('name', routine.name)
        routine.description = request.POST.get('description', routine.description)
        routine.save()
        
        # Clear existing exercises
        routine.routine_exercises.all().delete()
        
        # Add new exercises
        exercise_order = 0
        for key, value in request.POST.items():
            if key.startswith('exercise_'):
                exercise_id = key.split('_')[1]
                try:
                    exercise = Exercise.objects.get(id=exercise_id)
                    sets_count = int(request.POST.get(f'sets_{exercise_id}', 3))
                    rest_time = int(request.POST.get(f'rest_{exercise_id}', 60))
                    
                    RoutineExercise.objects.create(
                        routine=routine,
                        exercise=exercise,
                        sets_count=sets_count,
                        rest_time_seconds=rest_time,
                        order=exercise_order
                    )
                    exercise_order += 1
                except (Exercise.DoesNotExist, ValueError):
                    continue
        
        messages.success(request, f'Routine "{routine.name}" updated successfully!')
        return redirect('routines:routine_detail', routine_id=routine.id)
    
    # GET request
    exercises = Exercise.objects.all().order_by('name')
    muscle_groups = MuscleGroup.objects.all().order_by('name')
    current_exercises = routine.routine_exercises.all().order_by('order')
    
    context = {
        'routine': routine,
        'exercises': exercises,
        'muscle_groups': muscle_groups,
        'current_exercises': current_exercises,
    }
    return render(request, 'routines/routine_edit.html', context)


def routine_delete(request, routine_id):
    routine = get_object_or_404(Routine, id=routine_id)
    
    if request.method == 'POST':
        routine_name = routine.name
        routine.delete()
        messages.success(request, f'Routine "{routine_name}" deleted successfully!')
        return redirect('routines:routine_list')
    
    context = {'routine': routine}
    return render(request, 'routines/routine_delete.html', context)


def routine_start(request, routine_id):
    routine = get_object_or_404(Routine, id=routine_id)
    
    # Get default user
    user, created = User.objects.get_or_create(username='default_user', defaults={
        'first_name': 'Demo',
        'last_name': 'User',
        'email': 'demo@example.com'
    })
    
    # Create workout session
    session = WorkoutSession.objects.create(
        routine=routine,
        user=user,
        status='in_progress'
    )
    
    messages.success(request, f'Started workout: {routine.name}')
    return redirect('workouts:workout_session', session_id=session.id)
