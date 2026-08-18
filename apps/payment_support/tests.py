from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.business_days.models import BusinessDay
from apps.products.models import Category, Product
from apps.orders.models import Order
from apps.payment_support.models import PaymentSupportTicket

User = get_user_model()

class PaymentSupportTicketTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.today = timezone.localtime().date()
        self.business_day = BusinessDay.objects.create(
            date=self.today,
            status=BusinessDay.Status.WORKING_DAY
        )
        self.student = User.objects.create_user(
            email='student_ticket@saec.ac.in',
            password='password123',
            full_name='Ticket Student',
            mobile_number='9876543220',
            role=User.Role.STUDENT
        )
        self.admin = User.objects.create_user(
            email='admin_ticket@saec.ac.in',
            password='password123',
            full_name='Admin Ticket',
            mobile_number='9876543221',
            role=User.Role.ADMIN
        )
        self.order = Order.objects.create(
            order_number='SAEC-999',
            business_day=self.business_day,
            user=self.student,
            total_amount=Decimal('50.00'),
            status=Order.Status.AWAITING_PAYMENT,
            payment_status=Order.PaymentStatus.PENDING
        )

    def test_ticket_creation_and_admin_verification(self):
        # 1. Create ticket
        self.client.force_authenticate(user=self.student)
        response = self.client.post('/api/payment-support/', {
            'order_id': self.order.id,
            'transaction_id': 'UPI-REF-123456'
        })
        self.assertEqual(response.status_code, 201)
        ticket_id = response.data['id']
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAYMENT_SUPPORT_REQUIRED)

        # 2. Admin verifies ticket
        self.client.force_authenticate(user=self.admin)
        verify_resp = self.client.post(f'/api/payment-support/{ticket_id}/verify/', {
            'action': 'VERIFY',
            'notes': 'Verified payment screenshot'
        })
        self.assertEqual(verify_resp.status_code, 200)

        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)
        self.assertIsNotNone(self.order.confirmed_at)
