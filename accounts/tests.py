from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class UserRegistrationTests(TestCase):
    """Test user registration functionality"""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')

    def test_register_page_loads(self):
        """Test that registration page loads successfully"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Register')

    def test_successful_registration(self):
        """Test successful user registration"""
        response = self.client.post(self.register_url, {
            'username': 'testuser',
            'password1': 'testpass123!@#',
            'password2': 'testpass123!@#',
        })
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        # User should be created
        self.assertTrue(User.objects.filter(username='testuser').exists())
        # User should be logged in
        user = User.objects.get(username='testuser')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_registration_with_mismatched_passwords(self):
        """Test registration fails with mismatched passwords"""
        response = self.client.post(self.register_url, {
            'username': 'testuser',
            'password1': 'testpass123!@#',
            'password2': 'differentpass123!@#',
        })
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        # User should not be created
        self.assertFalse(User.objects.filter(username='testuser').exists())

    def test_registration_with_existing_username(self):
        """Test registration fails with existing username"""
        # Create existing user
        User.objects.create_user(username='testuser', password='testpass123!@#')

        response = self.client.post(self.register_url, {
            'username': 'testuser',
            'password1': 'newpass123!@#',
            'password2': 'newpass123!@#',
        })
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        # Should only have one user with this username
        self.assertEqual(User.objects.filter(username='testuser').count(), 1)


class UserLoginTests(TestCase):
    """Test user login functionality"""

    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )

    def test_login_page_loads(self):
        """Test that login page loads successfully"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')

    def test_successful_login(self):
        """Test successful user login"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123!@#',
        })
        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)
        # User should be logged in
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_login_with_wrong_password(self):
        """Test login fails with wrong password"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        # User should not be logged in
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_with_nonexistent_user(self):
        """Test login fails with nonexistent user"""
        response = self.client.post(self.login_url, {
            'username': 'nonexistent',
            'password': 'testpass123!@#',
        })
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        # User should not be logged in
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_redirect_to_next_page(self):
        """Test login redirects to 'next' parameter if provided"""
        next_url = reverse('routines:routine_list')
        response = self.client.post(f'{self.login_url}?next={next_url}', {
            'username': 'testuser',
            'password': 'testpass123!@#',
        })
        # Should redirect to the next URL
        self.assertRedirects(response, next_url)


class UserLogoutTests(TestCase):
    """Test user logout functionality"""

    def setUp(self):
        self.client = Client()
        self.logout_url = reverse('accounts:logout')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )
        # Log in the user
        self.client.login(username='testuser', password='testpass123!@#')

    def test_logout(self):
        """Test user logout"""
        # Verify user is logged in
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

        response = self.client.get(self.logout_url)
        # Should redirect after logout
        self.assertEqual(response.status_code, 302)
        # User should be logged out
        self.assertNotIn('_auth_user_id', self.client.session)


class UserProfileTests(TestCase):
    """Test user profile functionality"""

    def setUp(self):
        self.client = Client()
        self.profile_url = reverse('accounts:profile')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123!@#'
        )

    def test_profile_requires_login(self):
        """Test that profile page requires authentication"""
        response = self.client.get(self.profile_url)
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_profile_page_loads_for_authenticated_user(self):
        """Test that profile page loads for authenticated user"""
        self.client.login(username='testuser', password='testpass123!@#')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
