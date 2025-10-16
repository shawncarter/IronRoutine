from django.test import TestCase, Client
from django.urls import reverse
from exercises.models import Exercise, MuscleGroup


class ExerciseModelTests(TestCase):
    """Test Exercise model"""

    def setUp(self):
        self.muscle_group = MuscleGroup.objects.create(name='Chest')
        self.exercise = Exercise.objects.create(
            title='Push-up',
            name='push-up',
            slug='push-up',
            equipment='bodyweight',
            muscle='chest',
            difficulty='Beginner',
            description='A basic bodyweight exercise'
        )

    def test_exercise_creation(self):
        """Test exercise is created correctly"""
        self.assertEqual(self.exercise.title, 'Push-up')
        self.assertEqual(self.exercise.equipment, 'bodyweight')
        self.assertEqual(self.exercise.difficulty, 'Beginner')

    def test_exercise_str_method(self):
        """Test exercise string representation"""
        self.assertEqual(str(self.exercise), 'Push-up')


class ExerciseListViewTests(TestCase):
    """Test exercise list view"""

    def setUp(self):
        self.client = Client()
        self.list_url = reverse('exercises:exercise_list')

        # Create test exercises
        Exercise.objects.create(
            title='Push-up',
            name='push-up',
            slug='push-up',
            equipment='bodyweight',
            muscle='chest',
            difficulty='Beginner'
        )
        Exercise.objects.create(
            title='Bench Press',
            name='bench-press',
            slug='bench-press',
            equipment='barbell',
            muscle='chest',
            difficulty='Intermediate'
        )
        Exercise.objects.create(
            title='Squat',
            name='squat',
            slug='squat',
            equipment='barbell',
            muscle='legs',
            difficulty='Intermediate'
        )

    def test_exercise_list_page_loads(self):
        """Test that exercise list page loads successfully"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Push-up')
        self.assertContains(response, 'Bench Press')
        self.assertContains(response, 'Squat')

    def test_exercise_list_search(self):
        """Test exercise search functionality"""
        response = self.client.get(self.list_url, {'search': 'push'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Push-up')
        self.assertNotContains(response, 'Squat')

    def test_exercise_list_filter_by_muscle(self):
        """Test filtering exercises by muscle group"""
        response = self.client.get(self.list_url, {'muscle_group': 'chest'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Push-up')
        self.assertContains(response, 'Bench Press')
        self.assertNotContains(response, 'Squat')

    def test_exercise_list_filter_by_equipment(self):
        """Test filtering exercises by equipment"""
        response = self.client.get(self.list_url, {'equipment': 'barbell'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bench Press')
        self.assertContains(response, 'Squat')
        self.assertNotContains(response, 'Push-up')

    def test_exercise_list_filter_by_difficulty(self):
        """Test filtering exercises by difficulty"""
        response = self.client.get(self.list_url, {'difficulty': 'Beginner'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Push-up')
        self.assertNotContains(response, 'Bench Press')

    def test_exercise_list_links_include_equipment_filter(self):
        """Test that exercise detail links include equipment filter parameter"""
        response = self.client.get(self.list_url, {'equipment': 'barbell'})
        self.assertEqual(response.status_code, 200)
        # Check that exercise detail links contain the equipment filter
        self.assertContains(response, 'equipment=barbell')

    def test_exercise_list_links_include_muscle_group_filter(self):
        """Test that exercise detail links include muscle group filter parameter"""
        response = self.client.get(self.list_url, {'muscle_group': 'chest'})
        self.assertEqual(response.status_code, 200)
        # Check that exercise detail links contain the muscle group filter
        self.assertContains(response, 'muscle_group=chest')

    def test_exercise_list_links_include_difficulty_filter(self):
        """Test that exercise detail links include difficulty filter parameter"""
        response = self.client.get(self.list_url, {'difficulty': 'Beginner'})
        self.assertEqual(response.status_code, 200)
        # Check that exercise detail links contain the difficulty filter
        self.assertContains(response, 'difficulty=Beginner')

    def test_exercise_list_links_include_search_filter(self):
        """Test that exercise detail links include search filter parameter"""
        response = self.client.get(self.list_url, {'search': 'push'})
        self.assertEqual(response.status_code, 200)
        # Check that exercise detail links contain the search filter
        self.assertContains(response, 'search=push')

    def test_exercise_list_links_include_multiple_filters(self):
        """Test that exercise detail links include all active filters"""
        response = self.client.get(self.list_url, {
            'equipment': 'barbell',
            'muscle_group': 'chest',
            'difficulty': 'Intermediate'
        })
        self.assertEqual(response.status_code, 200)
        # Check that exercise detail links contain all filters
        self.assertContains(response, 'equipment=barbell')
        self.assertContains(response, 'muscle_group=chest')
        self.assertContains(response, 'difficulty=Intermediate')


class ExerciseDetailViewTests(TestCase):
    """Test exercise detail view"""

    def setUp(self):
        self.client = Client()
        self.exercise = Exercise.objects.create(
            title='Push-up',
            name='push-up',
            slug='push-up',
            equipment='bodyweight',
            muscle='chest',
            difficulty='Beginner',
            description='A basic bodyweight exercise'
        )
        self.detail_url = reverse('exercises:exercise_detail', kwargs={'exercise_id': self.exercise.id})

    def test_exercise_detail_page_loads(self):
        """Test that exercise detail page loads successfully"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Push-up')
        self.assertContains(response, 'Bodyweight')  # Capitalized in template
        self.assertContains(response, 'Beginner')

    def test_exercise_detail_404_for_nonexistent_exercise(self):
        """Test that 404 is returned for nonexistent exercise"""
        url = reverse('exercises:exercise_detail', kwargs={'exercise_id': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_exercise_detail_preserves_equipment_filter(self):
        """Test that equipment filter is preserved in back URL"""
        response = self.client.get(self.detail_url, {'equipment': 'dumbbells'})
        self.assertEqual(response.status_code, 200)
        # Check that back URL contains the equipment filter
        self.assertContains(response, 'equipment=dumbbells')

    def test_exercise_detail_preserves_muscle_group_filter(self):
        """Test that muscle group filter is preserved in back URL"""
        response = self.client.get(self.detail_url, {'muscle_group': 'chest'})
        self.assertEqual(response.status_code, 200)
        # Check that back URL contains the muscle group filter
        self.assertContains(response, 'muscle_group=chest')

    def test_exercise_detail_preserves_difficulty_filter(self):
        """Test that difficulty filter is preserved in back URL"""
        response = self.client.get(self.detail_url, {'difficulty': 'Beginner'})
        self.assertEqual(response.status_code, 200)
        # Check that back URL contains the difficulty filter
        self.assertContains(response, 'difficulty=Beginner')

    def test_exercise_detail_preserves_search_filter(self):
        """Test that search filter is preserved in back URL"""
        response = self.client.get(self.detail_url, {'search': 'push'})
        self.assertEqual(response.status_code, 200)
        # Check that back URL contains the search filter
        self.assertContains(response, 'search=push')

    def test_exercise_detail_preserves_multiple_filters(self):
        """Test that multiple filters are preserved in back URL"""
        response = self.client.get(self.detail_url, {
            'equipment': 'dumbbells',
            'muscle_group': 'chest',
            'difficulty': 'Intermediate',
            'search': 'press'
        })
        self.assertEqual(response.status_code, 200)
        # Check that back URL contains all filters
        self.assertContains(response, 'equipment=dumbbells')
        self.assertContains(response, 'muscle_group=chest')
        self.assertContains(response, 'difficulty=Intermediate')
        self.assertContains(response, 'search=press')


class MuscleGroupModelTests(TestCase):
    """Test MuscleGroup model"""

    def test_muscle_group_creation(self):
        """Test muscle group is created correctly"""
        muscle_group = MuscleGroup.objects.create(name='Chest')
        self.assertEqual(muscle_group.name, 'Chest')

    def test_muscle_group_str_method(self):
        """Test muscle group string representation"""
        muscle_group = MuscleGroup.objects.create(name='Chest')
        self.assertEqual(str(muscle_group), 'Chest')


class ExerciseAPIViewTests(TestCase):
    """Test exercise API views"""

    def setUp(self):
        self.client = Client()
        # Create test exercises
        self.exercise1 = Exercise.objects.create(
            title='Barbell Bench Press',
            name='barbell-bench-press',
            slug='barbell-bench-press',
            equipment='barbell',
            muscle='chest',
            difficulty='Intermediate',
            description='A compound chest exercise',
            has_videos=True
        )
        self.exercise2 = Exercise.objects.create(
            title='Dumbbell Curl',
            name='dumbbell-curl',
            slug='dumbbell-curl',
            equipment='dumbbells',
            muscle='biceps',
            difficulty='Beginner',
            description='An isolation bicep exercise'
        )
        self.muscle_group = MuscleGroup.objects.create(
            name='Chest',
            description='Chest muscles'
        )
        self.muscle_group.exercises.add(self.exercise1)

    def test_exercise_api_list(self):
        """Test exercise API list endpoint"""
        response = self.client.get('/exercises/api/exercises/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('count', data)
        self.assertIn('exercises', data)
        self.assertEqual(data['count'], 2)

    def test_exercise_api_list_with_search(self):
        """Test exercise API list with search filter"""
        response = self.client.get('/exercises/api/exercises/', {'search': 'bench'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['exercises'][0]['title'], 'Barbell Bench Press')

    def test_exercise_api_list_with_muscle_filter(self):
        """Test exercise API list with muscle group filter"""
        response = self.client.get('/exercises/api/exercises/', {'muscle_group': 'chest'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['exercises'][0]['muscle'], 'chest')

    def test_exercise_api_list_with_equipment_filter(self):
        """Test exercise API list with equipment filter"""
        response = self.client.get('/exercises/api/exercises/', {'equipment': 'dumbbells'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['exercises'][0]['equipment'], 'dumbbells')

    def test_exercise_api_list_with_difficulty_filter(self):
        """Test exercise API list with difficulty filter"""
        response = self.client.get('/exercises/api/exercises/', {'difficulty': 'Beginner'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['exercises'][0]['difficulty'], 'Beginner')

    def test_exercise_api_list_with_limit(self):
        """Test exercise API list with limit parameter"""
        response = self.client.get('/exercises/api/exercises/', {'limit': '1'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)

    def test_exercise_api_detail(self):
        """Test exercise API detail endpoint"""
        response = self.client.get(f'/exercises/api/exercises/{self.exercise1.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], 'Barbell Bench Press')
        self.assertEqual(data['equipment'], 'barbell')
        self.assertEqual(data['muscle'], 'chest')

    def test_exercise_api_detail_not_found(self):
        """Test exercise API detail with non-existent exercise"""
        response = self.client.get('/exercises/api/exercises/99999/')
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)

    def test_muscle_groups_api(self):
        """Test muscle groups API endpoint"""
        response = self.client.get('/exercises/api/muscle-groups/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('count', data)
        self.assertIn('muscle_groups', data)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['muscle_groups'][0]['name'], 'Chest')
