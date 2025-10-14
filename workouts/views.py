from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import WorkoutSession, WorkoutSet
from routines.models import RoutineExercise
from exercises.models import Exercise
import json


def workout_history(request):
    # Get default user
    user, created = User.objects.get_or_create(username='default_user', defaults={
        'first_name': 'Demo',
        'last_name': 'User',
        'email': 'demo@example.com'
    })
    
    sessions = WorkoutSession.objects.filter(user=user).order_by('-started_at')
    
    context = {
        'sessions': sessions,
        'user': user,
    }
    return render(request, 'workouts/workout_history.html', context)


def workout_session(request, session_id):
    session = get_object_or_404(WorkoutSession, id=session_id)
    routine_exercises = session.routine.routine_exercises.all().order_by('order')
    
    # Calculate progress for each exercise
    exercise_progress = []
    current_exercise = None
    
    for re in routine_exercises:
        completed_sets_count = session.workout_sets.filter(exercise=re.exercise).count()
        progress_data = {
            'routine_exercise': re,
            'completed_sets_count': completed_sets_count,
            'progress_percent': int((completed_sets_count / re.sets_count) * 100) if re.sets_count > 0 else 0,
            'is_complete': completed_sets_count >= re.sets_count,
        }
        exercise_progress.append(progress_data)
        
        # Set current exercise (first one without all sets completed)
        if current_exercise is None and completed_sets_count < re.sets_count:
            current_exercise = re
            progress_data['is_current'] = True
        else:
            progress_data['is_current'] = False
    
    # If no current exercise, workout is complete
    if not current_exercise and routine_exercises.exists():
        return redirect('workouts:workout_complete', session_id=session.id)
    
    context = {
        'session': session,
        'routine_exercises': routine_exercises,
        'current_exercise': current_exercise,
        'exercise_progress': exercise_progress,
    }
    return render(request, 'workouts/workout_session.html', context)


def workout_exercise(request, session_id, exercise_id):
    session = get_object_or_404(WorkoutSession, id=session_id)
    exercise = get_object_or_404(Exercise, id=exercise_id)
    
    # Get routine exercise info
    try:
        routine_exercise = session.routine.routine_exercises.get(exercise=exercise)
    except RoutineExercise.DoesNotExist:
        messages.error(request, 'Exercise not found in this routine')
        return redirect('workouts:workout_session', session_id=session.id)
    
    # Get completed sets
    completed_sets = session.workout_sets.filter(exercise=exercise).order_by('set_number')
    next_set_number = completed_sets.count() + 1
    
    context = {
        'session': session,
        'exercise': exercise,
        'routine_exercise': routine_exercise,
        'completed_sets': completed_sets,
        'next_set_number': next_set_number,
        'sets_remaining': routine_exercise.sets_count - completed_sets.count(),
    }
    return render(request, 'workouts/workout_exercise.html', context)


@require_POST
def save_workout_set(request):
    try:
        session_id = request.POST.get('session_id')
        exercise_id = request.POST.get('exercise_id')
        set_number = int(request.POST.get('set_number'))
        weight = float(request.POST.get('weight'))
        reps = int(request.POST.get('reps'))
        
        session = get_object_or_404(WorkoutSession, id=session_id)
        exercise = get_object_or_404(Exercise, id=exercise_id)
        
        # Get routine exercise for rest time
        routine_exercise = session.routine.routine_exercises.get(exercise=exercise)
        
        # Create workout set
        workout_set = WorkoutSet.objects.create(
            session=session,
            exercise=exercise,
            set_number=set_number,
            weight=weight,
            reps=reps
        )
        
        return JsonResponse({
            'success': True,
            'volume': float(workout_set.volume),
            'rest_time': routine_exercise.rest_time_seconds,
            'message': f'Set {set_number} saved successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def workout_exercise_sets_api(request, session_id, exercise_id):
    """API endpoint to fetch completed sets for an exercise in a workout session"""
    session = get_object_or_404(WorkoutSession, id=session_id)
    exercise = get_object_or_404(Exercise, id=exercise_id)
    
    # Get completed sets
    completed_sets = session.workout_sets.filter(exercise=exercise).order_by('set_number')
    
    sets_data = []
    for workout_set in completed_sets:
        sets_data.append({
            'set_number': workout_set.set_number,
            'weight': float(workout_set.weight),
            'reps': workout_set.reps,
            'volume': float(workout_set.volume),
            'completed_at': workout_set.completed_at.strftime('%I:%M %p'),
        })
    
    return JsonResponse({
        'success': True,
        'sets': sets_data,
        'total_sets': len(sets_data)
    })


def workout_complete(request, session_id):
    session = get_object_or_404(WorkoutSession, id=session_id)
    
    if request.method == 'POST':
        session.status = 'completed'
        session.completed_at = timezone.now()
        session.save()
        
        # Calculate final total volume
        session.calculate_total_volume()
        
        messages.success(request, 'Workout completed! Great job! 💪')
        return redirect('workouts:workout_history')
    
    # Get workout statistics
    total_sets = session.workout_sets.count()
    total_volume = session.total_volume
    duration = session.get_duration()
    exercises_completed = session.get_exercises_completed()
    
    context = {
        'session': session,
        'total_sets': total_sets,
        'total_volume': total_volume,
        'duration': duration,
        'exercises_completed': exercises_completed,
    }
    return render(request, 'workouts/workout_complete.html', context)
