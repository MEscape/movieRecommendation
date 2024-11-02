from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class UserAuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')

    def test_user_registration_success(self):
        """
        Test user registration with valid data.
        """
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'password123',
            'password_verify': 'password123',
            'role': 'user'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_registration_passwords_do_not_match(self):
        """
        Test user registration with mismatched passwords.
        """
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_verify': 'differentpassword',
        }
        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertIn('password', response.data['detail'])
        self.assertEqual(response.data['detail']['password'][0], 'Passwords must match.')

    def test_user_registration_existing_email(self):
        """
        Test user registration with an existing email.
        """
        User.objects.create_user(username='existinguser', email='testuser@example.com', password='password123')
        data = {
            'username': 'newuser',
            'email': 'testuser@example.com',
            'password': 'password123',
            'password_verify': 'password123',
        }
        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertIn('email', response.data['detail'])
        self.assertEqual(response.data['detail']['email'][0], 'user with this email already exists.')

    def test_user_registration_existing_username(self):
        """
        Test user registration with an existing username.
        """
        User.objects.create_user(username='existinguser', email='testuser@example.com', password='password123')
        data = {
            'username': 'existinguser',  # Using an existing username
            'email': 'newuser@example.com',  # Different email
            'password': 'password123',
            'password_verify': 'password123',
        }
        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertIn('username', response.data['detail'])
        self.assertEqual(response.data['detail']['username'][0], 'A user with that username already exists.')

    def test_user_login_success(self):
        """
        Test user login with valid credentials.
        """
        self.client.post(self.register_url, {
            'username': 'testuser3',
            'email': 'testuser3@example.com',
            'password': 'password123',
            'password_verify': 'password123',
        })
        data = {
            'username_or_email': 'testuser3',
            'password': 'password123',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_login_invalid_credentials(self):
        """
        Test user login with invalid credentials.
        """
        data = {
            'username_or_email': 'nonexistentuser',
            'password': 'wrongpassword',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
