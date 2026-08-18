from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.accounts.models import StudentProfile, FacultyProfile

User = get_user_model()

class AccountsModelAndAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.student_user = User.objects.create_user(
            email='student_test@saec.ac.in',
            password='password123',
            full_name='Test Student',
            mobile_number='9876543210',
            role=User.Role.STUDENT
        )
        StudentProfile.objects.create(
            user=self.student_user,
            register_number='912821104999',
            department='CSE',
            year=4
        )

    def test_user_creation(self):
        self.assertEqual(self.student_user.email, 'student_test@saec.ac.in')
        self.assertEqual(self.student_user.role, User.Role.STUDENT)
        self.assertTrue(self.student_user.check_password('password123'))
        self.assertEqual(self.student_user.student_profile.register_number, '912821104999')

    def test_jwt_token_login(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'student_test@saec.ac.in',
            'password': 'password123'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'student_test@saec.ac.in')
