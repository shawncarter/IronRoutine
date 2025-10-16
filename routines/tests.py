from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from routines.models import Routine, RoutineExercise
from exercises.models import Exercise


class RoutineModelTests(TestCase):
    """Test Routine model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )
        self.routine = Routine.objects.create(
            name='Test Routine',
            description='A test routine',
            user=self.user,
            is_public=True
        )

    def test_routine_creation(self):
        """Test routine is created correctly"""
        self.assertEqual(self.routine.name, 'Test Routine')
        self.assertEqual(self.routine.user, self.user)
        self.assertTrue(self.routine.is_public)

    def test_routine_str_method(self):
        """Test routine string representation"""
        self.assertEqual(str(self.routine), 'Test Routine - testuser')

    def test_get_estimated_duration(self):
        """Test estimated duration calculation"""
        # Create exercises
        exercise1 = Exercise.objects.create(
            title='Push-up',
            slug='push-up',
            equipment='bodyweight'
        )
        exercise2 = Exercise.objects.create(
            title='Squat',
            slug='squat',
            equipment='bodyweight'
        )

        # Add exercises to routine
        RoutineExercise.objects.create(
            routine=self.routine,
            exercise=exercise1,
            sets_count=3,
            rest_time_seconds=60,
            order=0
        )
        RoutineExercise.objects.create(
            routine=self.routine,
            exercise=exercise2,
            sets_count=3,
            rest_time_seconds=60,
            order=1
        )

        # Estimated duration should be calculated
        duration = self.routine.get_estimated_duration()
        self.assertIsNotNone(duration)
        self.assertGreater(duration, 0)


class RoutineListViewTests(TestCase):
    """Test routine list view"""

    def setUp(self):
        self.client = Client()
        self.list_url = reverse('routines:routine_list')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )

        # Create public and private routines
        self.public_routine = Routine.objects.create(
            name='Public Routine',
            user=self.user,
            is_public=True
        )
        self.private_routine = Routine.objects.create(
            name='Private Routine',
            user=self.user,
            is_public=False
        )

    def test_routine_list_page_loads(self):
        """Test that routine list page loads successfully"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_routine_list_shows_public_routines(self):
        """Test that public routines are visible to all users"""
        response = self.client.get(self.list_url)
        self.assertContains(response, 'Public Routine')

    def test_routine_list_hides_private_routines_from_anonymous(self):
        """Test that private routines are hidden from anonymous users"""
        response = self.client.get(self.list_url)
        self.assertNotContains(response, 'Private Routine')

    def test_routine_list_shows_own_private_routines(self):
        """Test that users can see their own private routines"""
        self.client.login(username='testuser', password='testpass123!@#')
        response = self.client.get(self.list_url)
        self.assertContains(response, 'Public Routine')
        self.assertContains(response, 'Private Routine')


class RoutineDetailViewTests(TestCase):
    """Test routine detail view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123!@#'
        )

        self.public_routine = Routine.objects.create(
            name='Public Routine',
            user=self.user,
            is_public=True
        )
        self.private_routine = Routine.objects.create(
            name='Private Routine',
            user=self.user,
            is_public=False
        )

    def test_public_routine_detail_accessible_to_all(self):
        """Test that public routine detail is accessible to all users"""
        url = reverse('routines:routine_detail', kwargs={'routine_id': self.public_routine.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Public Routine')

    def test_private_routine_detail_requires_ownership(self):
        """Test that private routine detail requires ownership"""
        url = reverse('routines:routine_detail', kwargs={'routine_id': self.private_routine.id})
        response = self.client.get(url)
        # Should redirect (not authorized)
        self.assertEqual(response.status_code, 302)

    def test_private_routine_detail_accessible_to_owner(self):
        """Test that private routine detail is accessible to owner"""
        self.client.login(username='testuser', password='testpass123!@#')
        url = reverse('routines:routine_detail', kwargs={'routine_id': self.private_routine.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Private Routine')


class RoutineCreateViewTests(TestCase):
    """Test routine creation view"""

    def setUp(self):
        self.client = Client()
        self.create_url = reverse('routines:routine_create')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )

        # Create test exercises
        self.exercise1 = Exercise.objects.create(
            title='Push-up',
            slug='push-up',
            equipment='bodyweight'
        )
        self.exercise2 = Exercise.objects.create(
            title='Squat',
            slug='squat',
            equipment='bodyweight'
        )

    def test_routine_create_requires_login(self):
        """Test that routine creation requires authentication"""
        response = self.client.get(self.create_url)
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_routine_create_page_loads_for_authenticated_user(self):
        """Test that routine creation page loads for authenticated user"""
        self.client.login(username='testuser', password='testpass123!@#')
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)

    def test_successful_routine_creation(self):
        """Test successful routine creation"""
        self.client.login(username='testuser', password='testpass123!@#')
        response = self.client.post(self.create_url, {
            'name': 'New Routine',
            'description': 'A new test routine',
            'is_public': 'on',
            f'exercise_{self.exercise1.id}': 'on',
            f'sets_{self.exercise1.id}': '3',
            f'rest_{self.exercise1.id}': '60',
        })
        # Should redirect after creation
        self.assertEqual(response.status_code, 302)
        # Routine should be created
        self.assertTrue(Routine.objects.filter(name='New Routine').exists())
        routine = Routine.objects.get(name='New Routine')
        self.assertEqual(routine.user, self.user)
        self.assertTrue(routine.is_public)
        # Exercise should be added to routine
        self.assertEqual(routine.routine_exercises.count(), 1)

    def test_routine_creation_without_name_fails(self):
        """Test that routine creation fails without a name"""
        self.client.login(username='testuser', password='testpass123!@#')
        response = self.client.post(self.create_url, {
            'description': 'A test routine',
        })
        # Should redirect back to create page
        self.assertEqual(response.status_code, 302)
        # Routine should not be created
        self.assertEqual(Routine.objects.count(), 0)


class RoutineEditViewTests(TestCase):
    """Test routine editing view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123!@#'
        )

        self.routine = Routine.objects.create(
            name='Test Routine',
            user=self.user,
            is_public=False
        )
        self.edit_url = reverse('routines:routine_edit', kwargs={'routine_id': self.routine.id})

        # Create test exercise
        self.exercise = Exercise.objects.create(
            title='Push-up',
            slug='push-up',
            equipment='bodyweight'
        )

    def test_routine_edit_requires_login(self):
        """Test that routine editing requires authentication"""
        response = self.client.get(self.edit_url)
        # Should redirect to routine detail (not authorized)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f'/routines/{self.routine.id}/', response.url)

    def test_routine_edit_requires_ownership(self):
        """Test that routine editing requires ownership"""
        self.client.login(username='otheruser', password='testpass123!@#')
        response = self.client.get(self.edit_url)
        # Should redirect (not authorized)
        self.assertEqual(response.status_code, 302)

    def test_routine_edit_page_loads_for_owner(self):
        """Test that routine edit page loads for owner"""
        self.client.login(username='testuser', password='testpass123!@#')
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Routine')

    def test_successful_routine_edit(self):
        """Test successful routine editing"""
        self.client.login(username='testuser', password='testpass123!@#')
        response = self.client.post(self.edit_url, {
            'name': 'Updated Routine',
            'description': 'Updated description',
            'is_public': 'on',
        })
        # Should redirect after edit
        self.assertEqual(response.status_code, 302)
        # Routine should be updated
        self.routine.refresh_from_db()
        self.assertEqual(self.routine.name, 'Updated Routine')
        self.assertEqual(self.routine.description, 'Updated description')
        self.assertTrue(self.routine.is_public)


class RoutineDeleteViewTests(TestCase):
    """Test routine deletion view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123!@#'
        )

        self.routine = Routine.objects.create(
            name='Test Routine',
            user=self.user
        )
        self.delete_url = reverse('routines:routine_delete', kwargs={'routine_id': self.routine.id})

    def test_successful_routine_deletion(self):
        """Test successful routine deletion"""
        self.client.login(username='testuser', password='testpass123!@#')
        # Verify routine exists before deletion
        self.assertTrue(Routine.objects.filter(id=self.routine.id).exists())

        response = self.client.post(self.delete_url)
        # Should redirect after deletion
        self.assertEqual(response.status_code, 302)
        # Routine should be deleted
        self.assertFalse(Routine.objects.filter(id=self.routine.id).exists())


class RoutineStartViewTests(TestCase):
    """Test routine start view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )
        self.routine = Routine.objects.create(
            name='Test Routine',
            user=self.user,
            is_public=True
        )
        self.start_url = reverse('routines:routine_start', kwargs={'routine_id': self.routine.id})

    def test_routine_start_requires_login(self):
        """Test starting a routine requires authentication"""
        response = self.client.get(self.start_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_routine_start_creates_workout_session(self):
        """Test starting a routine creates a workout session"""
        self.client.login(username='testuser', password='testpass123!@#')

        response = self.client.get(self.start_url)
        self.assertEqual(response.status_code, 302)

        # Verify workout session was created
        from workouts.models import WorkoutSession
        session = WorkoutSession.objects.filter(user=self.user, routine=self.routine).first()
        self.assertIsNotNone(session)
        self.assertEqual(session.status, 'in_progress')

    def test_routine_start_private_routine_requires_ownership(self):
        """Test starting a private routine requires ownership"""
        # Create another user and private routine
        other_user = User.objects.create_user(username='otheruser', password='testpass123!@#')
        private_routine = Routine.objects.create(
            name='Private Routine',
            user=other_user,
            is_public=False
        )

        self.client.login(username='testuser', password='testpass123!@#')
        response = self.client.get(reverse('routines:routine_start', kwargs={'routine_id': private_routine.id}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/routines/', response.url)


class RoutineCopyViewTests(TestCase):
    """Test routine copy view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123!@#'
        )

        # Create a public routine with exercises
        self.public_routine = Routine.objects.create(
            name='Public Routine',
            user=self.other_user,
            is_public=True
        )

        self.exercise = Exercise.objects.create(
            title='Push-up',
            slug='push-up',
            equipment='bodyweight'
        )

        RoutineExercise.objects.create(
            routine=self.public_routine,
            exercise=self.exercise,
            sets_count=3,
            rest_time_seconds=60,
            order=0
        )

        self.copy_url = reverse('routines:routine_copy', kwargs={'routine_id': self.public_routine.id})

    def test_routine_copy_requires_login(self):
        """Test copying a routine requires authentication"""
        response = self.client.get(self.copy_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_routine_copy_creates_new_routine(self):
        """Test copying a routine creates a new routine for the user"""
        self.client.login(username='testuser', password='testpass123!@#')

        initial_count = Routine.objects.filter(user=self.user).count()
        response = self.client.get(self.copy_url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Routine.objects.filter(user=self.user).count(), initial_count + 1)

        # Verify the copied routine
        copied_routine = Routine.objects.filter(user=self.user).first()
        self.assertIn('Copy', copied_routine.name)
        self.assertFalse(copied_routine.is_public)  # Copies are private by default

    def test_routine_copy_copies_exercises(self):
        """Test copying a routine also copies all exercises"""
        self.client.login(username='testuser', password='testpass123!@#')

        response = self.client.get(self.copy_url)
        self.assertEqual(response.status_code, 302)

        # Verify exercises were copied
        copied_routine = Routine.objects.filter(user=self.user).first()
        self.assertEqual(copied_routine.routine_exercises.count(), 1)

        copied_exercise = copied_routine.routine_exercises.first()
        original_exercise = self.public_routine.routine_exercises.first()

        self.assertEqual(copied_exercise.exercise, original_exercise.exercise)
        self.assertEqual(copied_exercise.sets_count, original_exercise.sets_count)
        self.assertEqual(copied_exercise.rest_time_seconds, original_exercise.rest_time_seconds)

    def test_routine_copy_private_routine_fails(self):
        """Test copying a private routine is not allowed"""
        private_routine = Routine.objects.create(
            name='Private Routine',
            user=self.other_user,
            is_public=False
        )

        self.client.login(username='testuser', password='testpass123!@#')
        response = self.client.get(reverse('routines:routine_copy', kwargs={'routine_id': private_routine.id}))

        self.assertEqual(response.status_code, 302)
        # Should not create a new routine
        self.assertEqual(Routine.objects.filter(user=self.user).count(), 0)


class RoutineAPIViewTests(TestCase):
    """Test routine API endpoints"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )
        self.routine = Routine.objects.create(
            name='Test Routine',
            user=self.user,
            is_public=False
        )
        self.exercise = Exercise.objects.create(
            title='Push-up',
            slug='push-up',
            equipment='bodyweight'
        )

    def test_user_routines_api_requires_authentication(self):
        """Test user routines API requires authentication"""
        response = self.client.get(reverse('routines:user_routines_api'))
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn('error', data)

    def test_user_routines_api_returns_user_routines(self):
        """Test user routines API returns user's routines"""
        self.client.login(username='testuser', password='testpass123!@#')

        response = self.client.get(reverse('routines:user_routines_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('routines', data)
        self.assertEqual(len(data['routines']), 1)
        self.assertEqual(data['routines'][0]['name'], 'Test Routine')

    def test_add_exercise_to_routine_requires_authentication(self):
        """Test adding exercise to routine requires authentication"""
        import json
        response = self.client.post(
            reverse('routines:add_exercise_to_routine', kwargs={'routine_id': self.routine.id}),
            data=json.dumps({'exercise_id': self.exercise.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

    def test_add_exercise_to_routine_success(self):
        """Test successfully adding exercise to routine"""
        import json
        self.client.login(username='testuser', password='testpass123!@#')

        response = self.client.post(
            reverse('routines:add_exercise_to_routine', kwargs={'routine_id': self.routine.id}),
            data=json.dumps({'exercise_id': self.exercise.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify exercise was added
        self.assertEqual(self.routine.routine_exercises.count(), 1)

    def test_add_exercise_to_routine_duplicate_fails(self):
        """Test adding duplicate exercise to routine fails gracefully"""
        import json
        self.client.login(username='testuser', password='testpass123!@#')

        # Add exercise first time
        RoutineExercise.objects.create(
            routine=self.routine,
            exercise=self.exercise,
            sets_count=3,
            rest_time_seconds=60,
            order=0
        )

        # Try to add again
        response = self.client.post(
            reverse('routines:add_exercise_to_routine', kwargs={'routine_id': self.routine.id}),
            data=json.dumps({'exercise_id': self.exercise.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('already in routine', data['message'])

    def test_add_exercise_to_routine_missing_exercise_id(self):
        """Test adding exercise without exercise_id fails"""
        import json
        self.client.login(username='testuser', password='testpass123!@#')

        response = self.client.post(
            reverse('routines:add_exercise_to_routine', kwargs={'routine_id': self.routine.id}),
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    def test_add_exercise_to_routine_invalid_json(self):
        """Test adding exercise with invalid JSON fails"""
        self.client.login(username='testuser', password='testpass123!@#')

        response = self.client.post(
            reverse('routines:add_exercise_to_routine', kwargs={'routine_id': self.routine.id}),
            data='invalid json',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)


class RoutineCreateWithFiltersTests(TestCase):
    """Test routine create view with exercise filters"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )
        # Create exercises with different attributes
        self.exercise1 = Exercise.objects.create(
            title='Barbell Bench Press',
            slug='barbell-bench-press',
            equipment='barbell',
            muscle='chest',
            difficulty='Intermediate'
        )
        self.exercise2 = Exercise.objects.create(
            title='Dumbbell Curl',
            slug='dumbbell-curl',
            equipment='dumbbells',
            muscle='biceps',
            difficulty='Beginner'
        )

    def test_routine_create_with_search_filter(self):
        """Test routine create page with search filter"""
        self.client.login(username='testuser', password='testpass123!@#')

        response = self.client.get(reverse('routines:routine_create'), {'search': 'bench'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Barbell Bench Press')
        self.assertNotContains(response, 'Dumbbell Curl')

    def test_routine_create_with_equipment_filter(self):
        """Test routine create page with equipment filter"""
        self.client.login(username='testuser', password='testpass123!@#')

        response = self.client.get(reverse('routines:routine_create'), {'equipment': 'dumbbells'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dumbbell Curl')

    def test_routine_create_with_muscle_filter(self):
        """Test routine create page with muscle group filter"""
        self.client.login(username='testuser', password='testpass123!@#')

        response = self.client.get(reverse('routines:routine_create'), {'muscle_group': 'chest'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Barbell Bench Press')

    def test_routine_create_with_difficulty_filter(self):
        """Test routine create page with difficulty filter"""
        self.client.login(username='testuser', password='testpass123!@#')

        response = self.client.get(reverse('routines:routine_create'), {'difficulty': 'Beginner'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dumbbell Curl')
