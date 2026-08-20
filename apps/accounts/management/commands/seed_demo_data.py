import random
from datetime import datetime, timedelta, time
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.accounts.models import StudentProfile, FacultyProfile
from apps.products.models import Category, Product
from apps.business_days.models import BusinessDay
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment
from apps.payment_support.models import PaymentSupportTicket, CustomerIssue
from apps.contact_orders.models import ContactOrderRequest

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds realistic, idempotent demo data into PostgreSQL for SAEC CAFÉ testing.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forces re-seeding even if demo data already exists',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=" * 70))
        self.stdout.write(self.style.NOTICE("   SAEC CAFE - SEEDING IDEMPOTENT DEMO DATA (PostgreSQL)"))
        self.stdout.write(self.style.NOTICE("=" * 70))

        # 1. SEED DEMO USERS
        self.stdout.write(self.style.HTTP_INFO("\n[1/5] Creating Demo User Accounts..."))
        demo_users_data = [
            # Standard Institutional Accounts
            {
                'email': 'student@saec.ac.in',
                'password': 'student123',
                'full_name': 'Student User',
                'mobile_number': '9876543210',
                'role': User.Role.STUDENT,
                'is_staff': False,
                'is_superuser': False,
                'profile_type': 'STUDENT',
                'profile_data': {'register_number': '912821104001', 'department': 'Computer Science & Engineering', 'year': 4}
            },
            {
                'email': 'faculty@saec.ac.in',
                'password': 'faculty123',
                'full_name': 'Faculty Member',
                'mobile_number': '9876543211',
                'role': User.Role.FACULTY,
                'is_staff': False,
                'is_superuser': False,
                'profile_type': 'FACULTY',
                'profile_data': {'staff_number': 'SAEC-FAC-101', 'department': 'Information Technology'}
            },
            {
                'email': 'cashier@saec.ac.in',
                'password': 'cashier123',
                'full_name': 'Canteen Cashier',
                'mobile_number': '9876543212',
                'role': User.Role.CASHIER,
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'admin@saec.ac.in',
                'password': 'admin123',
                'full_name': 'Canteen Admin',
                'mobile_number': '9876543213',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            },

            # Explicit Demo Accounts
            {
                'email': 'student.demo@example.com',
                'password': 'DemoStudent@123',
                'full_name': 'Demo Student',
                'mobile_number': '9876500001',
                'role': User.Role.STUDENT,
                'is_staff': False,
                'is_superuser': False,
                'profile_type': 'STUDENT',
                'profile_data': {'register_number': 'DEMO-REG-9128001', 'department': 'Computer Science & Engineering', 'year': 4}
            },
            {
                'email': 'faculty.demo@example.com',
                'password': 'DemoFaculty@123',
                'full_name': 'Demo Faculty',
                'mobile_number': '9876500002',
                'role': User.Role.FACULTY,
                'is_staff': False,
                'is_superuser': False,
                'profile_type': 'FACULTY',
                'profile_data': {'staff_number': 'DEMO-FAC-9128001', 'department': 'Information Technology'}
            },
            {
                'email': 'cashier.demo@example.com',
                'password': 'DemoCashier@123',
                'full_name': 'Demo Cashier',
                'mobile_number': '9876500003',
                'role': User.Role.CASHIER,
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'admin.demo@example.com',
                'password': 'DemoAdmin@123',
                'full_name': 'Demo Admin',
                'mobile_number': '9876500004',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            },
        ]

        created_users = {}
        for u_data in demo_users_data:
            user, created = User.objects.get_or_create(
                email=u_data['email'],
                defaults={
                    'username': u_data['email'],
                    'full_name': u_data['full_name'],
                    'mobile_number': u_data['mobile_number'],
                    'role': u_data['role'],
                    'is_staff': u_data.get('is_staff', False),
                    'is_superuser': u_data.get('is_superuser', False),
                    'is_active': True,
                    'is_demo': True,
                }
            )
            user.set_password(u_data['password'])
            user.is_demo = True
            user.save()
            created_users[u_data['role']] = user

            # Profile creation
            if u_data.get('profile_type') == 'STUDENT':
                StudentProfile.objects.update_or_create(
                    user=user,
                    defaults=u_data['profile_data']
                )
            elif u_data.get('profile_type') == 'FACULTY':
                FacultyProfile.objects.update_or_create(
                    user=user,
                    defaults=u_data['profile_data']
                )

            status_str = "Created" if created else "Updated"
            self.stdout.write(f"  * [{status_str}] {u_data['role']:<10} : {u_data['email']} (Password: {u_data['password']})")

        # 2. SEED DEMO CATEGORIES & FOOD ITEMS
        self.stdout.write(self.style.HTTP_INFO("\n[2/5] Creating Demo Food Categories & Menu..."))
        categories_data = [
            ('Tea & Coffee', 'Hot and refreshing canteen brews', 'coffee'),
            ('Snacks & Savouries', 'Hot fried snacks, puffs, and savouries', 'cookie'),
            ('Fast Food & Meals', 'Sandwiches, burgers, pizzas, and quick meals', 'utensils'),
            ('Cool Drinks & Juices', 'Chilled soft drinks and fresh juices', 'glass-water'),
            ('Bakery & Sweets', 'Freshly baked cakes, buns, and desserts', 'cake'),
        ]

        cat_objs = {}
        for name, desc, icon in categories_data:
            cat, _ = Category.objects.get_or_create(
                name=name,
                defaults={'description': desc, 'icon_name': icon, 'is_active': True}
            )
            cat_objs[name] = cat

        demo_products_data = [
            # Tea & Coffee
            ('Tea', 'Traditional south indian spiced tea', 'Tea & Coffee', 12.00, 6.00, 'READY_FOOD', 3, 50, 'AVAILABLE'),
            ('Filter Coffee', 'Authentic fresh filter coffee', 'Tea & Coffee', 15.00, 8.00, 'READY_FOOD', 3, 40, 'AVAILABLE'),
            ('Hot Masala Tea', 'Spiced ginger & cardamom milk tea', 'Tea & Coffee', 15.00, 7.50, 'READY_FOOD', 3, 35, 'AVAILABLE'),
            ('Fresh Milk', 'Boiled pure hot milk with sugar', 'Tea & Coffee', 15.00, 8.00, 'READY_FOOD', 2, 25, 'AVAILABLE'),
            
            # Snacks & Savouries
            ('Veg Samosa', 'Crispy triangular potato samosa (2 pcs)', 'Snacks & Savouries', 15.00, 8.00, 'READY_FOOD', 5, 45, 'AVAILABLE'),
            ('Veg Puff', 'Flaky pastry stuffed with spiced vegetables', 'Snacks & Savouries', 20.00, 11.00, 'READY_FOOD', 5, 50, 'AVAILABLE'),
            ('Egg Puff', 'Golden puff pastry with seasoned boiled egg', 'Snacks & Savouries', 25.00, 14.00, 'READY_FOOD', 5, 30, 'AVAILABLE'),
            ('Paneer Puff', 'Rich cottage cheese filling in flaky crust', 'Snacks & Savouries', 30.00, 16.00, 'READY_FOOD', 5, 25, 'AVAILABLE'),

            # Fast Food & Meals
            ('Veg Grilled Sandwich', 'Toasted bread with butter, veggies & green chutney', 'Fast Food & Meals', 45.00, 22.00, 'MADE_TO_ORDER', 10, 20, 'AVAILABLE'),
            ('Cheese Burger', 'Sesame bun with veggie patty & melted cheese', 'Fast Food & Meals', 65.00, 32.00, 'MADE_TO_ORDER', 12, 15, 'AVAILABLE'),
            ('Mini Veg Pizza', 'Cheesy 6-inch pizza with capsicum & sweetcorn', 'Fast Food & Meals', 80.00, 42.00, 'MADE_TO_ORDER', 15, 12, 'AVAILABLE'),

            # Cool Drinks & Juices
            ('Fresh Lime Juice', 'Freshly squeezed sweet & salt lemonade', 'Cool Drinks & Juices', 30.00, 12.00, 'READY_FOOD', 4, 30, 'AVAILABLE'),
            ('Mango Juice', 'Thick mango pulp drink', 'Cool Drinks & Juices', 35.00, 16.00, 'READY_FOOD', 3, 25, 'AVAILABLE'),
            ('Bovonto 250ml', 'Chilled local grape cola beverage', 'Cool Drinks & Juices', 25.00, 18.00, 'READY_FOOD', 1, 40, 'AVAILABLE'),

            # Bakery & Sweets
            ('Chocolate Cake Slice', 'Moist chocolate fudge cake slice', 'Bakery & Sweets', 35.00, 18.00, 'READY_FOOD', 2, 20, 'AVAILABLE'),
            ('Special Badam Milk', 'Chilled almond saffron milk (Restocking)', 'Bakery & Sweets', 30.00, 15.00, 'READY_FOOD', 2, 0, 'UNAVAILABLE'),
        ]

        created_products = []
        for name, desc, cat_name, price, cost_p, f_type, prep_m, stock, avail in demo_products_data:
            sku_code = f"SKU-{name.upper().replace(' ', '')[:6]}"
            prod, _ = Product.objects.update_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'category': cat_objs[cat_name],
                    'price': Decimal(str(price)),
                    'cost_price': Decimal(str(cost_p)),
                    'food_type': f_type,
                    'preparation_time': prep_m,
                    'current_stock': stock,
                    'minimum_stock': 5,
                    'maximum_stock': 100,
                    'availability_status': avail,
                    'sku': sku_code,
                    'is_active': True,
                    'is_demo': True,
                }
            )
            created_products.append(prod)

        self.stdout.write(f"  * Seeded {len(created_products)} demo menu items (15 Available, 1 Unavailable).")

        # 3. SEED DEMO BUSINESS DAYS
        self.stdout.write(self.style.HTTP_INFO("\n[3/5] Setting Up Canteen Operating Days & Hours..."))
        now = timezone.localtime()
        today = now.date()

        # Seed past 30 days of business days
        bday_objs = {}
        for i in range(30):
            d = today - timedelta(days=i)
            # Sunday as Holiday
            is_sunday = (d.weekday() == 6)
            b_status = BusinessDay.Status.HOLIDAY if is_sunday else BusinessDay.Status.WORKING_DAY
            reason_str = "Sunday College Holiday" if is_sunday else ""

            bday, _ = BusinessDay.objects.update_or_create(
                date=d,
                defaults={
                    'status': b_status,
                    'opening_time': time(10, 0),
                    'closing_time': time(15, 30),
                    'reason': reason_str,
                    'is_ordering_enabled': not is_sunday,
                    'daily_order_sequence': 1000 + (30 - i) * 15,
                    'is_demo': True,
                }
            )
            bday_objs[d] = bday

        self.stdout.write(f"  * Seeded 30 business day calendar records (10:00 AM - 3:30 PM window).")

        # 4. SEED REALISTIC DEMO HISTORICAL ORDERS & PAYMENTS
        self.stdout.write(self.style.HTTP_INFO("\n[4/5] Generating Realistic Historical Orders for PostgreSQL Analytics..."))
        
        student_user = created_users[User.Role.STUDENT]
        faculty_user = created_users[User.Role.FACULTY]
        cashier_user = created_users[User.Role.CASHIER]

        demo_order_scenarios = [
            # Day offset, User, Source, CustType, Status, PayStatus, PayMethod, Items [(ProdIndex, Qty)]
            (0, student_user, Order.OrderSource.MOBILE, Order.CustomerType.STUDENT, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(0, 2), (5, 2)]), # Tea + Veg Puff
            (0, faculty_user, Order.OrderSource.MOBILE, Order.CustomerType.FACULTY, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(1, 2), (8, 1)]), # Coffee + Sandwich
            (0, None, Order.OrderSource.POS, Order.CustomerType.WALK_IN, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'CASH', [(4, 2), (13, 1)]), # Samosa + Bovonto
            (0, student_user, Order.OrderSource.MOBILE, Order.CustomerType.STUDENT, Order.Status.READY, Order.PaymentStatus.PAID, 'UPI', [(9, 1), (11, 1)]), # Burger + Lime Juice
            (0, student_user, Order.OrderSource.MOBILE, Order.CustomerType.STUDENT, Order.Status.CONFIRMED, Order.PaymentStatus.PAID, 'UPI', [(6, 2)]), # Egg Puff
            (0, student_user, Order.OrderSource.MOBILE, Order.CustomerType.STUDENT, Order.Status.AWAITING_PAYMENT, Order.PaymentStatus.PENDING, 'CASH', [(10, 1)]), # Pizza

            (1, student_user, Order.OrderSource.MOBILE, Order.CustomerType.STUDENT, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(0, 3), (4, 3)]),
            (1, faculty_user, Order.OrderSource.MOBILE, Order.CustomerType.FACULTY, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(1, 2), (14, 2)]),
            (1, None, Order.OrderSource.POS, Order.CustomerType.WALK_IN, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'CASH', [(5, 4), (13, 2)]),
            (1, student_user, Order.OrderSource.MOBILE, Order.CustomerType.STUDENT, Order.Status.CANCELLED, Order.PaymentStatus.FAILED, 'UPI', [(9, 2)]),

            (2, student_user, Order.OrderSource.MOBILE, Order.CustomerType.STUDENT, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(2, 2), (5, 2)]),
            (2, None, Order.OrderSource.POS, Order.CustomerType.WALK_IN, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'CASH', [(0, 4), (4, 4)]),
            (2, faculty_user, Order.OrderSource.MOBILE, Order.CustomerType.FACULTY, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(8, 2), (12, 2)]),

            (3, student_user, Order.OrderSource.MOBILE, Order.CustomerType.STUDENT, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(1, 2), (7, 2)]),
            (3, None, Order.OrderSource.POS, Order.CustomerType.WALK_IN, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'CASH', [(5, 3), (13, 3)]),
            (3, student_user, Order.OrderSource.MOBILE, Order.CustomerType.STUDENT, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(10, 1), (14, 1)]),

            (4, student_user, Order.OrderSource.MOBILE, Order.CustomerType.STUDENT, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(0, 2), (4, 2)]),
            (4, faculty_user, Order.OrderSource.MOBILE, Order.CustomerType.FACULTY, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(1, 3), (8, 1)]),
            (4, None, Order.OrderSource.POS, Order.CustomerType.WALK_IN, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'CASH', [(6, 2), (13, 2)]),

            (5, student_user, Order.OrderSource.MOBILE, Order.CustomerType.STUDENT, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(9, 2), (11, 2)]),
            (5, None, Order.OrderSource.POS, Order.CustomerType.WALK_IN, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'CASH', [(0, 5), (5, 5)]),

            (6, student_user, Order.OrderSource.MOBILE, Order.CustomerType.STUDENT, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(1, 2), (4, 2), (14, 1)]),
            (6, faculty_user, Order.OrderSource.MOBILE, Order.CustomerType.FACULTY, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(8, 2), (12, 1)]),

            # Older historical orders (10 to 25 days ago)
            (10, student_user, Order.OrderSource.MOBILE, Order.CustomerType.STUDENT, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(0, 4), (5, 4)]),
            (12, None, Order.OrderSource.POS, Order.CustomerType.WALK_IN, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'CASH', [(1, 4), (4, 4)]),
            (15, faculty_user, Order.OrderSource.MOBILE, Order.CustomerType.FACULTY, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(8, 3), (11, 3)]),
            (18, student_user, Order.OrderSource.MOBILE, Order.CustomerType.STUDENT, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(9, 2), (10, 1)]),
            (20, None, Order.OrderSource.POS, Order.CustomerType.WALK_IN, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'CASH', [(0, 6), (5, 6)]),
            (25, student_user, Order.OrderSource.MOBILE, Order.CustomerType.STUDENT, Order.Status.DELIVERED, Order.PaymentStatus.PAID, 'UPI', [(1, 3), (6, 3)]),
        ]

        order_seq = 1001
        for day_offset, u, src, c_type, o_stat, p_stat, p_method, items_tuples in demo_order_scenarios:
            target_date = today - timedelta(days=day_offset)
            order_code = f"CAN-{order_seq}"
            order_seq += 1

            # Realistic timestamps between 10:15 AM and 3:15 PM
            order_hour = 10 + (order_seq % 5)
            order_min = (order_seq * 7) % 55
            order_created_dt = timezone.make_aware(datetime.combine(target_date, time(order_hour, order_min)))
            
            b_day = bday_objs.get(target_date, bday_objs[today])

            order, created = Order.objects.update_or_create(
                order_number=order_code,
                defaults={
                    'business_day': b_day,
                    'user': u,
                    'customer_type': c_type,
                    'order_source': src,
                    'order_type': Order.OrderType.READY_FOOD,
                    'status': o_stat,
                    'payment_status': p_stat,
                    'confirmed_at': order_created_dt if p_stat == Order.PaymentStatus.PAID else None,
                    'completed_at': order_created_dt + timedelta(minutes=15) if o_stat == Order.Status.DELIVERED else None,
                    'is_demo': True,
                }
            )

            # Manually set auto_now_add creation date for analytics backfill
            Order.objects.filter(id=order.id).update(created_at=order_created_dt)

            subtotal = Decimal('0.00')
            for p_idx, qty in items_tuples:
                prod = created_products[p_idx % len(created_products)]
                total_p = prod.price * qty
                subtotal += total_p

                OrderItem.objects.update_or_create(
                    order=order,
                    product=prod,
                    defaults={
                        'product_name': prod.name,
                        'unit_price': prod.price,
                        'quantity': qty,
                        'total_price': total_p,
                    }
                )

            order.subtotal = subtotal
            order.total_amount = subtotal
            order.save()

            if p_stat == Order.PaymentStatus.PAID:
                Payment.objects.update_or_create(
                    order=order,
                    defaults={
                        'amount': subtotal,
                        'method': Payment.Method.UPI if p_method == 'UPI' else Payment.Method.CASH,
                        'status': Payment.Status.PAID,
                        'transaction_id': f"DEMO-TXN-{order_code}",
                        'paid_at': order_created_dt,
                        'is_demo': True,
                    }
                )

        self.stdout.write(f"  * Seeded {len(demo_order_scenarios)} realistic demo orders across date ranges with full item breakdown.")

        # 5. SEED DEMO SUPPORT & CATERING TICKETS
        self.stdout.write(self.style.HTTP_INFO("\n[5/5] Creating Demo Support Tickets & Bulk Catering Requests..."))
        
        # Payment support ticket
        target_demo_order = Order.objects.filter(is_demo=True, payment_status=Order.PaymentStatus.PAID).first()
        if target_demo_order:
            PaymentSupportTicket.objects.update_or_create(
                ticket_number="PAY-DEMO01",
                defaults={
                    'order': target_demo_order,
                    'user': student_user,
                    'amount': target_demo_order.total_amount,
                    'transaction_id': "DEMO-UPI-REF-998877",
                    'status': PaymentSupportTicket.Status.RESOLVED,
                    'admin_notes': "Demo verified: Payment captured in bank ledger.",
                    'is_demo': True,
                }
            )

            CustomerIssue.objects.update_or_create(
                issue_number="ISSUE-DEMO01",
                defaults={
                    'order_code': target_demo_order.order_number,
                    'order': target_demo_order,
                    'user': student_user,
                    'category': CustomerIssue.Category.ORDER_ISSUE,
                    'description': "Demo Issue: Extra straw requested with fresh juice.",
                    'status': CustomerIssue.Status.RESOLVED,
                    'admin_response': "Straw provided with order pickup.",
                    'resolved_by': created_users[User.Role.ADMIN],
                    'is_demo': True,
                }
            )

        # Catering request
        catering_prod = created_products[5] # Veg Puff
        pickup_time_dt = timezone.now() + timedelta(days=2)
        ContactOrderRequest.objects.update_or_create(
            request_number="REQ-DEMO01",
            defaults={
                'user': faculty_user,
                'product': catering_prod,
                'quantity': 50,
                'preferred_pickup_time': pickup_time_dt,
                'special_instructions': "Demo Catering: Department Workshop - 50 Veg Puffs required at 11:00 AM",
                'status': ContactOrderRequest.Status.ACCEPTED,
                'is_demo': True,
            }
        )

        self.stdout.write("  * Seeded demo payment tickets and faculty bulk catering requests.")

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write(self.style.SUCCESS(">> DEMO DATA SEEDING COMPLETE: DATABASE IS FULLY TESTABLE (PASS) <<"))
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write("Demo accounts created:")
        self.stdout.write("  - Student : student.demo@example.com / DemoStudent@123")
        self.stdout.write("  - Faculty : faculty.demo@example.com / DemoFaculty@123")
        self.stdout.write("  - Cashier : cashier.demo@example.com / DemoCashier@123")
        self.stdout.write("  - Admin   : admin.demo@example.com   / DemoAdmin@123")
        self.stdout.write(self.style.WARNING("\nTo remove all demo data before production: python manage.py remove_demo_data"))
