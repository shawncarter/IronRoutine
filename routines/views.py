from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import json
import random
from .models import Routine, RoutineExercise
from exercises.models import Exercise, MuscleGroup
from workouts.models import WorkoutSession

# Constants for URL names and templates
ROUTINE_DETAIL_URL = 'routines:routine_detail'
ROUTINE_GENERATOR_TEMPLATE = 'routines/routine_generator.html'
ROUTINE_LIST_URL = 'routines:routine_list'
LOGIN_URL = 'accounts:login'


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
        return redirect(ROUTINE_LIST_URL)
    
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


def _add_exercises_to_routine(request, routine):
    """Add exercises from POST data to the routine"""
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


def _get_filtered_exercises(search, muscle_group, equipment, difficulty):
    """Apply filters to exercise queryset"""
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

    return exercises


def _get_popular_exercises():
    """Get a curated list of popular exercises for initial display"""
    return Exercise.objects.filter(
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


def routine_create(request):
    # Require authentication to create routines
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to create a routine.')
        return redirect(LOGIN_URL)
    
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
        _add_exercises_to_routine(request, routine)
        
        messages.success(request, f'Routine "{name}" created successfully!')
        return redirect(ROUTINE_DETAIL_URL, routine_id=routine.id)
    
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
        exercises = _get_filtered_exercises(search, muscle_group, equipment, difficulty)
    else:
        # Show only 12 popular exercises initially (no filters applied)
        exercises = _get_popular_exercises()
    
    context = {
        'exercises': exercises,
        'muscle_groups': muscle_groups,
        'current_search': search,
        'current_muscle_group': muscle_group,
        'current_equipment': equipment,
        'current_difficulty': difficulty,
    }
    return render(request, 'routines/routine_create.html', context)


def _process_routine_exercises(request, routine):
    """Process and save exercises from the edit form"""
    # Clear existing exercises
    routine.routine_exercises.all().delete()

    # Add new exercises
    exercise_order = 0
    for key, value in request.POST.items():
        if not key.startswith('exercise_'):
            continue

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


def _apply_exercise_filters(request):
    """Apply search and filter criteria to exercises"""
    search = request.GET.get('search', '')
    muscle_group = request.GET.get('muscle_group', '')
    equipment = request.GET.get('equipment', '')
    difficulty = request.GET.get('difficulty', '')

    exercises = Exercise.objects.all().order_by('title', 'name')

    if search:
        exercises = exercises.filter(
            Q(name__icontains=search) |
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(muscle__icontains=search)
        ).distinct()

    if muscle_group:
        exercises = exercises.filter(Q(muscle__icontains=muscle_group)).distinct()

    if equipment:
        exercises = exercises.filter(equipment=equipment)

    if difficulty:
        exercises = exercises.filter(difficulty=difficulty)

    return exercises


def routine_edit(request, routine_id):
    routine = get_object_or_404(Routine, id=routine_id)

    # Check if user can edit this routine
    if not request.user.is_authenticated or routine.user != request.user:
        messages.error(request, 'You do not have permission to edit this routine.')
        return redirect(ROUTINE_DETAIL_URL, routine_id=routine.id)

    if request.method == 'POST':
        routine.name = request.POST.get('name', routine.name)
        routine.description = request.POST.get('description', routine.description)
        routine.is_public = request.POST.get('is_public') == 'on'
        routine.save()

        # Process exercises
        _process_routine_exercises(request, routine)

        messages.success(request, f'Routine "{routine.name}" updated successfully!')
        return redirect(ROUTINE_DETAIL_URL, routine_id=routine.id)

    # GET request - Add filtering like routine_create
    muscle_values = Exercise.objects.exclude(muscle='').values_list('muscle', flat=True).distinct().order_by('muscle')
    muscle_groups = [{'name': muscle} for muscle in muscle_values if muscle]

    # Apply filters to exercises
    exercises = _apply_exercise_filters(request)
    current_exercises = routine.routine_exercises.all().order_by('order')
    
    context = {
        'routine': routine,
        'exercises': exercises,
        'muscle_groups': muscle_groups,
        'current_exercises': current_exercises,
        'current_search': search,
        'current_muscle_group': muscle_group,
        'current_equipment': equipment,
        'current_difficulty': difficulty,
    }
    return render(request, 'routines/routine_edit.html', context)


def routine_delete(request, routine_id):
    routine = get_object_or_404(Routine, id=routine_id)
    
    if request.method == 'POST':
        routine_name = routine.name
        routine.delete()
        messages.success(request, f'Routine "{routine_name}" deleted successfully!')
        return redirect(ROUTINE_LIST_URL)
    
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
        return redirect(ROUTINE_LIST_URL)

    # Require authentication to track workouts
    if not request.user.is_authenticated:
        messages.info(request, 'Please log in to track your workouts.')
        return redirect(LOGIN_URL)
    
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
        return redirect(ROUTINE_LIST_URL)

    # Require authentication
    if not request.user.is_authenticated:
        messages.info(request, 'Please log in to copy this routine.')
        return redirect(LOGIN_URL)
    
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
    return redirect(ROUTINE_DETAIL_URL, routine_id=new_routine.id)


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


def _validate_routine_generator_form(request, routine_name, equipment_list, category, custom_muscles, muscle_group_categories):
    """Validate routine generator form inputs"""
    context = {
        'muscle_group_categories': muscle_group_categories,
        'equipment_options': _get_equipment_options(),
        'special_splits': _get_special_splits(),
        'all_muscles': get_available_muscles(),
    }

    if not routine_name:
        messages.error(request, 'Please provide a routine name')
        return False, context

    if not equipment_list:
        messages.error(request, 'Please select at least one equipment type')
        return False, context

    if not category and not custom_muscles:
        messages.error(request, 'Please select muscle groups')
        return False, context

    return True, context


def _get_target_muscles_and_equipment(category, custom_muscles, equipment_list, muscle_group_categories):
    """Determine target muscles and equipment based on category or custom selection"""
    target_muscles = None
    final_equipment_list = equipment_list

    if category and category in muscle_group_categories:
        category_data = muscle_group_categories[category]
        target_muscles = category_data['muscles']
        # Override equipment for special categories
        if 'equipment_override' in category_data:
            final_equipment_list = [category_data['equipment_override']]
    elif custom_muscles:
        target_muscles = custom_muscles

    return target_muscles, final_equipment_list


def _create_routine_with_exercises(user, routine_name, target_muscles, final_equipment_list,
                                   selected_exercises, sets_per_exercise, rest_time):
    """Create a routine and add exercises to it"""
    equipment_options = _get_equipment_options()
    equipment_names = [dict(equipment_options).get(eq, eq) for eq in final_equipment_list]
    equipment_description = ', '.join(equipment_names).lower()

    routine = Routine.objects.create(
        name=routine_name,
        user=user,
        description=f"Generated {equipment_description} routine targeting: {', '.join(target_muscles)}"
    )

    # Add exercises to routine
    for i, exercise in enumerate(selected_exercises):
        RoutineExercise.objects.create(
            routine=routine,
            exercise=exercise,
            sets_count=sets_per_exercise,
            rest_time_seconds=rest_time,
            order=i + 1
        )

    return routine


def _get_equipment_options():
    """Get available equipment options"""
    return [
        ('dumbbells', 'Dumbbells'),
        ('barbell', 'Barbell'),
        ('bodyweight', 'Bodyweight'),
        ('machine', 'Machine'),
        ('kettlebells', 'Kettlebells'),
        ('stretches', 'Yoga/Stretches'),
        ('mixed', 'Mixed Equipment'),
    ]


def _get_special_splits():
    """Get special workout split configurations"""
    return {
        '3_day_split': {
            'name': '3-Day Full Body Split',
            'description': 'Creates 3 complementary routines for a complete weekly program (15 exercises total)',
            'routines': [
                {
                    'name': 'Upper Body Push',
                    'muscles': ['chest', 'shoulders', 'triceps', 'anterior-deltoid', 'upper-trapezius'],
                    'description': 'Day 1: Chest, shoulders, and triceps'
                },
                {
                    'name': 'Back & Biceps Pull',
                    'muscles': ['lats', 'traps', 'biceps', 'rear-shoulders', 'forearms'],
                    'description': 'Day 2: Back, biceps, and rear delts'
                },
                {
                    'name': 'Legs & Core',
                    'muscles': ['quads', 'hamstrings', 'glutes', 'calves', 'abdominals'],
                    'description': 'Day 3: Full legs and core strengthening'
                }
            ]
        }
    }


def _get_muscle_group_categories():
    """Get muscle group category definitions"""
    return {
        'arms': {
            'name': 'Arms',
            'muscles': ['biceps', 'triceps', 'forearms', 'shoulders'],
            'description': 'Complete arm workout targeting biceps, triceps, forearms, and shoulders'
        },
        'legs': {
            'name': 'Legs',
            'muscles': ['quads', 'hamstrings', 'calves', 'glutes'],
            'description': 'Full leg workout targeting quads, hamstrings, calves, and glutes'
        },
        'back': {
            'name': 'Back',
            'muscles': ['lats', 'traps', 'lowerback', 'rear-shoulders'],
            'description': 'Complete back workout targeting lats, traps, lower back, and rear delts'
        },
        'chest': {
            'name': 'Chest',
            'muscles': ['chest', 'anterior-deltoid', 'triceps'],
            'description': 'Chest-focused workout targeting pecs, front delts, and triceps'
        },
        'core': {
            'name': 'Core',
            'muscles': ['abdominals', 'obliques', 'lower-abdominals', 'lowerback'],
            'description': 'Core strengthening targeting abs, obliques, and lower back'
        },
        'upper_body': {
            'name': 'Upper Body',
            'muscles': ['chest', 'lats', 'shoulders', 'biceps', 'triceps'],
            'description': 'Complete upper body workout targeting chest, back, and arms'
        },
        'full_body': {
            'name': 'Full Body',
            'muscles': ['chest', 'lats', 'shoulders', 'biceps', 'triceps', 'quads', 'hamstrings', 'abdominals'],
            'description': 'Complete full body workout hitting all major muscle groups'
        },
        'yoga_flow': {
            'name': 'Yoga Flow',
            'muscles': ['abdominals', 'lowerback', 'shoulders', 'hamstrings', 'calves', 'hips'],
            'description': 'Flexibility and strength flow targeting core, back, and mobility',
            'equipment_override': 'bodyweight'
        },
        'bodyweight_blast': {
            'name': 'Bodyweight Blast',
            'muscles': ['chest', 'shoulders', 'triceps', 'abdominals', 'quads', 'glutes'],
            'description': 'High-intensity bodyweight workout requiring no equipment',
            'equipment_override': 'bodyweight'
        }
    }


def routine_generator(request):
    """Generate a routine based on muscle groups and equipment selection"""
    muscle_group_categories = _get_muscle_group_categories()
    special_splits = _get_special_splits()

    if request.method == 'POST':
        # Get form data
        routine_name = request.POST.get('routine_name', '').strip()
        category = request.POST.get('category')
        equipment_list = request.POST.getlist('equipment')
        exercise_count = int(request.POST.get('exercise_count', 5))
        sets_per_exercise = int(request.POST.get('sets_per_exercise', 3))
        rest_time = int(request.POST.get('rest_time', 60))
        custom_muscles = request.POST.getlist('custom_muscles')

        # Handle 3-Day Split special case
        if category == '3_day_split':
            equipment = equipment_list[0] if equipment_list else 'mixed'
            return handle_3_day_split(request, routine_name, equipment, sets_per_exercise, rest_time, special_splits)

        # Validate form
        is_valid, context = _validate_routine_generator_form(
            request, routine_name, equipment_list, category, custom_muscles, muscle_group_categories
        )
        if not is_valid:
            return render(request, ROUTINE_GENERATOR_TEMPLATE, context)

        # Get target muscles and equipment
        target_muscles, final_equipment_list = _get_target_muscles_and_equipment(
            category, custom_muscles, equipment_list, muscle_group_categories
        )

        # Generate exercises
        selected_exercises = generate_routine_exercises(target_muscles, final_equipment_list, exercise_count)

        if not selected_exercises:
            messages.error(request, 'No exercises found for the selected criteria. Try different muscle groups or equipment.')
            context = {
                'muscle_group_categories': muscle_group_categories,
                'equipment_options': _get_equipment_options(),
                'special_splits': special_splits,
                'all_muscles': get_available_muscles(),
            }
            return render(request, ROUTINE_GENERATOR_TEMPLATE, context)

        # Get or create user
        user = request.user if request.user.is_authenticated else User.objects.get_or_create(
            username='default_user',
            defaults={'first_name': 'Demo', 'last_name': 'User', 'email': 'demo@example.com'}
        )[0]

        # Create routine with exercises
        routine = _create_routine_with_exercises(
            user, routine_name, target_muscles, final_equipment_list,
            selected_exercises, sets_per_exercise, rest_time
        )

        messages.success(request, f'Generated routine "{routine_name}" with {len(selected_exercises)} exercises!')
        return redirect(ROUTINE_DETAIL_URL, routine_id=routine.id)

    # GET request - show form
    context = {
        'muscle_group_categories': muscle_group_categories,
        'equipment_options': _get_equipment_options(),
        'special_splits': special_splits,
        'all_muscles': get_available_muscles(),
    }
    return render(request, ROUTINE_GENERATOR_TEMPLATE, context)


def handle_3_day_split(request, routine_name, equipment, sets_per_exercise, rest_time, special_splits):
    """Handle 3-Day Split generation - creates 3 complementary routines"""
    
    # Define muscle group categories for consistency
    muscle_group_categories = {
        'arms': {
            'name': 'Arms',
            'muscles': ['biceps', 'triceps', 'forearms', 'shoulders'],
            'description': 'Complete arm workout targeting biceps, triceps, forearms, and shoulders'
        },
        'legs': {
            'name': 'Legs', 
            'muscles': ['quads', 'hamstrings', 'calves', 'glutes'],
            'description': 'Full leg workout targeting quads, hamstrings, calves, and glutes'
        },
        'back': {
            'name': 'Back',
            'muscles': ['lats', 'traps', 'lowerback', 'rear-shoulders'],
            'description': 'Complete back workout targeting lats, traps, lower back, and rear delts'
        },
        'chest': {
            'name': 'Chest',
            'muscles': ['chest', 'anterior-deltoid', 'triceps'],
            'description': 'Chest-focused workout targeting pecs, front delts, and triceps'
        },
        'core': {
            'name': 'Core',
            'muscles': ['abdominals', 'obliques', 'lower-abdominals', 'lowerback'],
            'description': 'Core strengthening targeting abs, obliques, and lower back'
        },
        'upper_body': {
            'name': 'Upper Body',
            'muscles': ['chest', 'lats', 'shoulders', 'biceps', 'triceps'],
            'description': 'Complete upper body workout targeting chest, back, and arms'
        },
        'full_body': {
            'name': 'Full Body',
            'muscles': ['chest', 'lats', 'shoulders', 'biceps', 'triceps', 'quads', 'hamstrings', 'abdominals'],
            'description': 'Complete full body workout hitting all major muscle groups'
        },
        'yoga_flow': {
            'name': 'Yoga Flow',
            'muscles': ['abdominals', 'lowerback', 'shoulders', 'hamstrings', 'calves', 'hips'],
            'description': 'Flexibility and strength flow targeting core, back, and mobility',
            'equipment_override': 'bodyweight'
        },
        'bodyweight_blast': {
            'name': 'Bodyweight Blast',
            'muscles': ['chest', 'shoulders', 'triceps', 'abdominals', 'quads', 'glutes'],
            'description': 'High-intensity bodyweight workout requiring no equipment',
            'equipment_override': 'bodyweight'
        }
    }
    
    # Available equipment options
    equipment_options = [
        ('dumbbells', 'Dumbbells'),
        ('barbell', 'Barbell'),
        ('bodyweight', 'Bodyweight'),
        ('machine', 'Machine'),
        ('kettlebells', 'Kettlebells'),
        ('stretches', 'Yoga/Stretches'),
        ('mixed', 'Mixed Equipment'),
    ]
    
    if not routine_name:
        messages.error(request, 'Please provide a base routine name for the 3-day split')
        context = {
            'muscle_group_categories': muscle_group_categories,
            'equipment_options': equipment_options,
            'special_splits': special_splits,
            'all_muscles': get_available_muscles(),
        }
        return render(request, ROUTINE_GENERATOR_TEMPLATE, context)

    # Get or create user
    if request.user.is_authenticated:
        user = request.user
    else:
        user, _ = User.objects.get_or_create(username='default_user', defaults={
            'first_name': 'Demo',
            'last_name': 'User',
            'email': 'demo@example.com'
        })
    
    created_routines = []
    split_data = special_splits['3_day_split']
    
    # Create each routine in the split
    for i, routine_data in enumerate(split_data['routines']):
        # Generate 5 exercises for each routine (15 total)
        selected_exercises = generate_routine_exercises(
            routine_data['muscles'], equipment, 5
        )
        
        if not selected_exercises:
            continue
        
        # Create routine with day number
        full_name = f"{routine_name} - {routine_data['name']}"
        routine = Routine.objects.create(
            name=full_name,
            user=user,
            description=f"{routine_data['description']} - Part of 3-day split program"
        )
        
        # Add exercises to routine
        for j, exercise in enumerate(selected_exercises):
            RoutineExercise.objects.create(
                routine=routine,
                exercise=exercise,
                sets_count=sets_per_exercise,
                rest_time_seconds=rest_time,
                order=j + 1
            )
        
        created_routines.append(routine)
    
    if created_routines:
        messages.success(request, f'Generated 3-day split program "{routine_name}" with {len(created_routines)} routines and {sum(r.routine_exercises.count() for r in created_routines)} total exercises!')
        # Redirect to the first routine
        return redirect(ROUTINE_DETAIL_URL, routine_id=created_routines[0].id)
    else:
        messages.error(request, 'Could not generate exercises for the 3-day split. Try different equipment.')
        context = {
            'muscle_group_categories': muscle_group_categories,
            'equipment_options': equipment_options,
            'special_splits': special_splits,
            'all_muscles': get_available_muscles(),
        }
        return render(request, ROUTINE_GENERATOR_TEMPLATE, context)


def generate_routine_exercises(target_muscles, equipment, max_exercises=5):
    """Generate a list of exercises based on target muscles and equipment"""
    selected_exercises = []
    used_exercises = set()
    
    # Handle mixed equipment or equipment list
    if isinstance(equipment, list):
        equipment_list = equipment
        # If mixed is in the list, expand it
        if 'mixed' in equipment_list:
            equipment_list = ['dumbbells', 'barbell', 'bodyweight', 'machine', 'kettlebells']
    elif equipment == 'mixed':
        equipment_list = ['dumbbells', 'barbell', 'bodyweight', 'machine', 'kettlebells']
    else:
        equipment_list = [equipment]
    
    # Try to get one exercise per muscle group
    for muscle in target_muscles:
        if len(selected_exercises) >= max_exercises:
            break
        
        # Find exercises for this muscle group with any of the specified equipment
        exercises = Exercise.objects.filter(
            muscle=muscle,
            equipment__in=equipment_list
        ).exclude(
            id__in=used_exercises
        )
        
        if exercises.exists():
            exercise = random.choice(exercises)
            selected_exercises.append(exercise)
            used_exercises.add(exercise.id)
    
    # If we don't have enough exercises, fill with random ones from target muscles
    while len(selected_exercises) < max_exercises:
        remaining_exercises = Exercise.objects.filter(
            muscle__in=target_muscles,
            equipment__in=equipment_list
        ).exclude(
            id__in=used_exercises
        )
        
        if not remaining_exercises.exists():
            break
        
        exercise = random.choice(remaining_exercises)
        selected_exercises.append(exercise)
        used_exercises.add(exercise.id)
    
    return selected_exercises


def get_available_muscles():
    """Get all available muscle groups for custom selection"""
    muscles = Exercise.objects.exclude(muscle='').values_list('muscle', flat=True).distinct()
    return sorted(set(muscles))
