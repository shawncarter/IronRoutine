from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from workouts.models import WorkoutSession, WorkoutSet
from routines.models import Routine, RoutineExercise
from exercises.models import Exercise


class WorkoutSessionModelTests(TestCase):
    """Test WorkoutSession model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )
        self.routine = Routine.objects.create(
            name='Test Routine',
            user=self.user
        )
        self.session = WorkoutSession.objects.create(
            routine=self.routine,
            user=self.user
        )

    def test_workout_session_creation(self):
        """Test workout session is created correctly"""
        self.assertEqual(self.session.routine, self.routine)
        self.assertEqual(self.session.user, self.user)
        self.assertIsNotNone(self.session.started_at)
        self.assertIsNone(self.session.completed_at)

    def test_workout_session_str_method(self):
        """Test workout session string representation"""
        expected = f"Test Routine - {self.session.started_at.strftime('%Y-%m-%d')}"
        self.assertEqual(str(self.session), expected)

    def test_workout_session_completion(self):
        """Test workout session can be completed"""
        self.session.completed_at = timezone.now()
        self.session.save()
        self.assertIsNotNone(self.session.completed_at)


class WorkoutSetModelTests(TestCase):
    """Test WorkoutSet model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )
        self.routine = Routine.objects.create(
            name='Test Routine',
            user=self.user
        )
        self.exercise = Exercise.objects.create(
            title='Push-up',
            name='push-up',
            slug='push-up',
            equipment='bodyweight'
        )
        self.session = WorkoutSession.objects.create(
            routine=self.routine,
            user=self.user
        )
        self.workout_set = WorkoutSet.objects.create(
            session=self.session,
            exercise=self.exercise,
            set_number=1,
            reps=10,
            weight=0
        )

    def test_workout_set_creation(self):
        """Test workout set is created correctly"""
        self.assertEqual(self.workout_set.session, self.session)
        self.assertEqual(self.workout_set.exercise, self.exercise)
        self.assertEqual(self.workout_set.set_number, 1)
        self.assertEqual(self.workout_set.reps, 10)
        self.assertEqual(self.workout_set.weight, 0)

    def test_workout_set_str_method(self):
        """Test workout set string representation"""
        expected = "push-up - Set 1: 0kg × 10 reps"
        self.assertEqual(str(self.workout_set), expected)


class WorkoutSessionViewTests(TestCase):
    """Test workout session views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )

        # Create routine with exercises
        self.routine = Routine.objects.create(
            name='Test Routine',
            user=self.user,
            is_public=True
        )
        self.exercise = Exercise.objects.create(
            title='Push-up',
            name='push-up',
            slug='push-up',
            equipment='bodyweight'
        )
        self.routine_exercise = RoutineExercise.objects.create(
            routine=self.routine,
            exercise=self.exercise,
            sets_count=3,
            order=0
        )

    def test_start_workout_creates_session(self):
        """Test that starting a workout creates a session when logged in"""
        self.client.login(username='testuser', password='testpass123!@#')
        url = reverse('routines:routine_start', kwargs={'routine_id': self.routine.id})
        response = self.client.get(url)
        # Should redirect to workout session
        self.assertEqual(response.status_code, 302)
        # Session should be created
        self.assertEqual(WorkoutSession.objects.count(), 1)
        session = WorkoutSession.objects.first()
        self.assertEqual(session.routine, self.routine)
        self.assertEqual(session.user, self.user)

    def test_workout_session_page_loads(self):
        """Test that workout session page loads when logged in"""
        self.client.login(username='testuser', password='testpass123!@#')
        session = WorkoutSession.objects.create(
            routine=self.routine,
            user=self.user
        )
        url = reverse('workouts:workout_session', kwargs={'session_id': session.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Routine')
        self.assertContains(response, 'push-up')  # Lowercase in template


class WorkoutHistoryViewTests(TestCase):
    """Test workout history views"""

    def setUp(self):
        self.client = Client()
        # Create default user (used by workout_history view)
        self.default_user = User.objects.create_user(
            username='default_user',
            password='testpass123!@#'
        )
        self.routine = Routine.objects.create(
            name='Test Routine',
            user=self.default_user
        )

        # Create completed workout session for default user
        self.completed_session = WorkoutSession.objects.create(
            routine=self.routine,
            user=self.default_user,
            completed_at=timezone.now()
        )

    def test_workout_history_page_loads(self):
        """Test that workout history page loads"""
        url = reverse('workouts:workout_history')
        response = self.client.get(url)
        # Should load successfully (no auth required)
        self.assertEqual(response.status_code, 200)

    def test_workout_history_shows_completed_sessions(self):
        """Test that workout history shows completed sessions"""
        url = reverse('workouts:workout_history')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Should show completed session
        self.assertContains(response, 'Test Routine')
