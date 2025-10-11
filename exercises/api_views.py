from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Exercise, MuscleGroup


@require_http_methods(["GET"])
def exercise_api_list(request):
    """
    API endpoint to fetch exercises with filtering
    Query params:
    - search: Search by title
    - muscle: Filter by muscle group
    - equipment: Filter by equipment type
    - difficulty: Filter by difficulty level
    - limit: Limit results (default 50)
    """
    exercises = Exercise.objects.all()
    
    # Apply filters
    search = request.GET.get('search', '')
    muscle = request.GET.get('muscle', '')
    equipment = request.GET.get('equipment', '')
    difficulty = request.GET.get('difficulty', '')
    limit = int(request.GET.get('limit', 50))
    
    if search:
        exercises = exercises.filter(title__icontains=search)
    
    if muscle:
        exercises = exercises.filter(muscle__icontains=muscle)
    
    if equipment:
        exercises = exercises.filter(equipment=equipment)
    
    if difficulty:
        exercises = exercises.filter(difficulty=difficulty)
    
    # Limit results
    exercises = exercises[:limit]
    
    # Serialize data
    data = []
    for exercise in exercises:
        data.append({
            'id': exercise.id,
            'title': exercise.title,
            'slug': exercise.slug,
            'equipment': exercise.equipment,
            'muscle': exercise.muscle,
            'difficulty': exercise.difficulty,
            'has_videos': exercise.has_videos,
            'instructions': exercise.get_instructions_list(),
            'male_url': exercise.male_url,
            'female_url': exercise.female_url,
        })
    
    return JsonResponse({
        'count': len(data),
        'exercises': data
    })


@require_http_methods(["GET"])
def exercise_api_detail(request, exercise_id):
    """
    API endpoint to fetch a single exercise with full details
    """
    try:
        exercise = Exercise.objects.get(id=exercise_id)
    except Exercise.DoesNotExist:
        return JsonResponse({'error': 'Exercise not found'}, status=404)
    
    data = {
        'id': exercise.id,
        'title': exercise.title,
        'slug': exercise.slug,
        'equipment': exercise.equipment,
        'muscle': exercise.muscle,
        'difficulty': exercise.difficulty,
        'has_videos': exercise.has_videos,
        'instructions': exercise.get_instructions_list(),
        'male_url': exercise.male_url,
        'female_url': exercise.female_url,
        'male_videos': exercise.male_videos,
        'female_videos': exercise.female_videos,
        'force': exercise.force,
        'grips': exercise.grips,
        'mechanic': exercise.mechanic,
    }
    
    return JsonResponse(data)


@require_http_methods(["GET"])
def muscle_groups_api(request):
    """
    API endpoint to fetch all muscle groups
    """
    muscle_groups = MuscleGroup.objects.all().order_by('name')
    
    data = [
        {
            'id': mg.id,
            'name': mg.name,
            'description': mg.description,
            'exercise_count': mg.exercises.count()
        }
        for mg in muscle_groups
    ]
    
    return JsonResponse({
        'count': len(data),
        'muscle_groups': data
    })
