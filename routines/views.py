from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import json
from .models import Routine, RoutineExercise
from exercises.models import Exercise, MuscleGroup
from workouts.models import WorkoutSession


def routine_list(request):
    if request.user.is_authenticated:
        # Show user's own routines + public routines from others
        user_routines = Routine.objects.filter(user=request.user, is_active=True)
        public_routines = Routine.objects.filter(is_public=True, is_active=True).exclude(user=request.user)
        
        context = {
            'user_routines': user_routines,
            'public_routines': public_routines,
            'user': request.user,
        }
    else:
        # Anonymous users see only public routines
        public_routines = Routine.objects.filter(is_public=True, is_active=True)
        
        context = {
            'public_routines': public_routines,
            'user': None,
        }
    
    return render(request, 'routines/routine_list.html', context)


def routine_detail(request, routine_id):
    routine = get_object_or_404(Routine, id=routine_id)
    
    # Check if user can view this routine
    can_view = (
        routine.is_public or 
        (request.user.is_authenticated and routine.user == request.user)
    )
    
    if not can_view:
        messages.error(request, 'You do not have permission to view this routine.')
        return redirect('routines:routine_list')
    
    routine_exercises = routine.routine_exercises.all().order_by('order')
    
    # Calculate total sets and estimated duration
    total_sets = sum([re.sets_count for re in routine_exercises])
    estimated_duration = routine.get_estimated_duration()
    
    # Check if user can edit this routine
    can_edit = request.user.is_authenticated and routine.user == request.user
    
    context = {
        'routine': routine,
        'routine_exercises': routine_exercises,
        'total_sets': total_sets,
        'estimated_duration': estimated_duration,
        'can_edit': can_edit,
    }
    return render(request, 'routines/routine_detail.html', context)


def routine_create(request):
    # Require authentication to create routines
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to create a routine.')
        return redirect('accounts:login')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_public = request.POST.get('is_public') == 'on'
        
        if not name:
            messages.error(request, 'Routine name is required')
            return redirect('routines:routine_create')
        
        # Create routine
        routine = Routine.objects.create(
            name=name,
            description=description,
            user=request.user,
            is_public=is_public
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
    
    # GET request - show form with limited initial exercises for performance
    # Get unique muscle groups from actual exercises (for filter dropdowns)
    muscle_values = Exercise.objects.exclude(muscle='').values_list('muscle', flat=True).distinct().order_by('muscle')
    muscle_groups = [{'name': muscle} for muscle in muscle_values if muscle]

    # Check if any filters are applied
    search = request.GET.get('search', '')
    muscle_group = request.GET.get('muscle_group', '')
    equipment = request.GET.get('equipment', '')
    difficulty = request.GET.get('difficulty', '')

    # If no filters applied, show popular exercises; otherwise use AJAX
    has_filters = any([search, muscle_group, equipment, difficulty])

    if has_filters:
        # Apply filters (same logic as exercise_list view)
        exercises = Exercise.objects.all().order_by('title', 'name')

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
    else:
        # Show only 12 popular exercises initially (no filters applied)
        # Choose common exercises across different muscle groups for better UX
        popular_exercises = [
            'push-up', 'squat', 'pull-up', 'plank', 'deadlift', 'bench press',
            'bicep curl', 'tricep', 'shoulder press', 'lunge', 'crunch', 'row'
        ]

        exercises = Exercise.objects.filter(
            Q(name__icontains='push') | Q(title__icontains='push') |
            Q(name__icontains='squat') | Q(title__icontains='squat') |
            Q(name__icontains='pull') | Q(title__icontains='pull') |
            Q(name__icontains='plank') | Q(title__icontains='plank') |
            Q(name__icontains='curl') | Q(title__icontains='curl') |
            Q(name__icontains='press') | Q(title__icontains='press') |
            Q(name__icontains='lunge') | Q(title__icontains='lunge') |
            Q(name__icontains='crunch') | Q(title__icontains='crunch') |
            Q(name__icontains='row') | Q(title__icontains='row') |
            Q(name__icontains='deadlift') | Q(title__icontains='deadlift')
        ).distinct().order_by('title', 'name')[:12]
    
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
    
    # Check if user can edit this routine
    if not request.user.is_authenticated or routine.user != request.user:
        messages.error(request, 'You do not have permission to edit this routine.')
        return redirect('routines:routine_detail', routine_id=routine.id)
    
    if request.method == 'POST':
        routine.name = request.POST.get('name', routine.name)
        routine.description = request.POST.get('description', routine.description)
        routine.is_public = request.POST.get('is_public') == 'on'
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
    
    # Check if user can view this routine
    can_view = (
        routine.is_public or 
        (request.user.is_authenticated and routine.user == request.user)
    )
    
    if not can_view:
        messages.error(request, 'You do not have permission to start this routine.')
        return redirect('routines:routine_list')
    
    # Require authentication to track workouts
    if not request.user.is_authenticated:
        messages.info(request, 'Please log in to track your workouts.')
        return redirect('accounts:login')
    
    # Create workout session
    session = WorkoutSession.objects.create(
        routine=routine,
        user=request.user,
        status='in_progress'
    )
    
    messages.success(request, f'Started workout: {routine.name}')
    return redirect('workouts:workout_session', session_id=session.id)


def routine_copy(request, routine_id):
    """Copy a public routine to the user's account"""
    original_routine = get_object_or_404(Routine, id=routine_id)
    
    # Check if routine is public
    if not original_routine.is_public:
        messages.error(request, 'This routine is not available for copying.')
        return redirect('routines:routine_list')
    
    # Require authentication
    if not request.user.is_authenticated:
        messages.info(request, 'Please log in to copy this routine.')
        return redirect('accounts:login')
    
    # Create a copy of the routine
    new_routine = Routine.objects.create(
        name=f"{original_routine.name} (Copy)",
        description=original_routine.description,
        user=request.user,
        is_public=False  # User's copy is private by default
    )
    
    # Copy all exercises
    for original_exercise in original_routine.routine_exercises.all():
        RoutineExercise.objects.create(
            routine=new_routine,
            exercise=original_exercise.exercise,
            sets_count=original_exercise.sets_count,
            rest_time_seconds=original_exercise.rest_time_seconds,
            order=original_exercise.order,
            target_reps=original_exercise.target_reps,
            target_weight=original_exercise.target_weight,
        )
    
    messages.success(request, f'Routine "{original_routine.name}" copied to your account!')
    return redirect('routines:routine_detail', routine_id=new_routine.id)


def user_routines_api(request):
    """API endpoint to get user's routines for add-to-routine modal"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    routines = Routine.objects.filter(user=request.user, is_active=True)
    routine_data = []
    
    for routine in routines:
        routine_data.append({
            'id': routine.id,
            'name': routine.name,
            'description': routine.description,
            'exercise_count': routine.get_total_exercises(),
            'estimated_duration': routine.get_estimated_duration(),
        })
    
    return JsonResponse({'routines': routine_data})


@require_POST
def add_exercise_to_routine(request, routine_id):
    """API endpoint to add exercise to existing routine"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    routine = get_object_or_404(Routine, id=routine_id, user=request.user)
    
    try:
        data = json.loads(request.body)
        exercise_id = data.get('exercise_id')
        
        if not exercise_id:
            return JsonResponse({'error': 'Exercise ID required'}, status=400)
        
        exercise = get_object_or_404(Exercise, id=exercise_id)
        
        # Check if exercise already exists in routine
        existing = RoutineExercise.objects.filter(routine=routine, exercise=exercise).first()
        if existing:
            return JsonResponse({'success': False, 'message': 'Exercise already in routine'})
        
        # Get the next order number
        last_exercise = routine.routine_exercises.order_by('order').last()
        next_order = (last_exercise.order + 1) if last_exercise else 0
        
        # Add exercise to routine
        RoutineExercise.objects.create(
            routine=routine,
            exercise=exercise,
            sets_count=3,  # Default
            rest_time_seconds=60,  # Default
            order=next_order
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Exercise added to {routine.name}',
            'routine_id': routine.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
