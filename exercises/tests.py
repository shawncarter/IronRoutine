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
