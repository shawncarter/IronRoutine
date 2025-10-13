from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Exercise, MuscleGroup


def exercise_list(request):
    exercises = Exercise.objects.all().order_by('title', 'name')
    muscle_groups = MuscleGroup.objects.all().order_by('name')
    
    # Apply filters
    search = request.GET.get('search', '')
    muscle_group = request.GET.get('muscle_group', '')
    equipment = request.GET.get('equipment', '')
    difficulty = request.GET.get('difficulty', '')
    
    if search:
        exercises = exercises.filter(
            Q(name__icontains=search) | 
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(muscle_groups__name__icontains=search) |
            Q(muscle__icontains=search)
        ).distinct()
    
    if muscle_group:
        exercises = exercises.filter(
            Q(muscle_groups__name__icontains=muscle_group) |
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
    return render(request, 'exercises/exercise_list.html', context)


def exercise_detail(request, exercise_id):
    exercise = get_object_or_404(Exercise, id=exercise_id)
    
    # Get related exercises (same muscle groups or equipment)
    related_exercises = Exercise.objects.filter(
        Q(muscle_groups__in=exercise.muscle_groups.all()) |
        Q(muscle=exercise.muscle) |
        Q(equipment=exercise.equipment)
    ).exclude(id=exercise.id).distinct()[:6]
    
    # Get instructions as a clean list
    instructions = exercise.get_instructions_list()
    
    # Get video URLs
    male_videos = exercise.get_video_urls('male')
    female_videos = exercise.get_video_urls('female')
    
    # Determine preferred gender for display (default to male)
    preferred_gender = request.GET.get('gender', 'male')
    videos = male_videos if preferred_gender == 'male' else female_videos
    
    # Check if we're coming from a routine
    from_routine = request.GET.get('from_routine')
    back_url = None
    back_text = "← Back"
    
    if from_routine:
        try:
            from routines.models import Routine
            routine = Routine.objects.get(id=from_routine)
            # Check if user can view this routine
            can_view = (
                routine.is_public or 
                (request.user.is_authenticated and routine.user == request.user)
            )
            if can_view:
                back_url = f"/routines/{routine.id}/"
                back_text = f"← Back to {routine.name}"
        except (Routine.DoesNotExist, ValueError):
            pass
    
    if not back_url:
        back_url = "/exercises/"
        back_text = "← Back to Exercises"
    
    context = {
        'exercise': exercise,
        'related_exercises': related_exercises,
        'instructions': instructions,
        'male_videos': male_videos,
        'female_videos': female_videos,
        'videos': videos,
        'preferred_gender': preferred_gender,
        'back_url': back_url,
        'back_text': back_text,
    }
    return render(request, 'exercises/exercise_detail.html', context)


def exercise_search(request):
    query = request.GET.get('q', '')
    exercises = []
    
    if query:
        exercises = Exercise.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(muscle_groups__name__icontains=query)
        ).distinct()[:10]
    
    context = {
        'exercises': exercises,
        'query': query,
    }
    return render(request, 'exercises/exercise_search.html', context)
