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
