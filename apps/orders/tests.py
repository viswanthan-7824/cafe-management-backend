from datetime import time
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.business_days.models import BusinessDay
from apps.products.models import Category, Product
from apps.orders.models import Order
from apps.orders.services import create_order, get_fcfs_queue

User = get_user_model()

class OrdersServiceAndLogicTest(TestCase):
    def setUp(self):
        self.today = timezone.localtime().date()
        self.business_day = BusinessDay.objects.create(
            date=self.today,
            status=BusinessDay.Status.WORKING_DAY,
            opening_time=time(0, 0),
            closing_time=time(23, 59, 59),
            notes="Regular Academic Working Day"
        )
        self.user = User.objects.create_user(
            email='order_test@saec.ac.in',
            password='password123',
            full_name='Order Tester',
            mobile_number='9876543211',
            role=User.Role.STUDENT
        )
        self.category = Category.objects.create(name='Snacks', is_active=True)
        self.product = Product.objects.create(
            name='Veg Puff',
            category=self.category,
            price=Decimal('20.00'),
            current_stock=50,
            food_type=Product.FoodType.READY_FOOD,
            is_active=True
        )

    def test_create_order_success(self):
        items_data = [{'product_id': self.product.id, 'quantity': 2}]
        order = create_order(
            user=self.user,
            customer_type=Order.CustomerType.STUDENT,
            order_source=Order.OrderSource.MOBILE,
            items_data=items_data,
            is_paid=True
        )

        self.assertIsNotNone(order.order_number)
        self.assertTrue(order.order_number.startswith('CAN-'))
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(order.total_amount, Decimal('40.00'))

        # Check inventory stock deduction
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 48)

    def test_fcfs_queue_sorting(self):
        items_data = [{'product_id': self.product.id, 'quantity': 1}]
        order1 = create_order(
            user=self.user,
            customer_type=Order.CustomerType.STUDENT,
            order_source=Order.OrderSource.MOBILE,
            items_data=items_data,
            is_paid=True
        )
        order2 = create_order(
            user=self.user,
            customer_type=Order.CustomerType.STUDENT,
            order_source=Order.OrderSource.POS,
            items_data=items_data,
            is_paid=True
        )

        queue = list(get_fcfs_queue())
        self.assertIn(order1, queue)
        self.assertIn(order2, queue)
        self.assertLessEqual(order1.confirmed_at, order2.confirmed_at)
