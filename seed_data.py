import os
import sys
import django
from datetime import time, timedelta
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.accounts.models import StudentProfile, FacultyProfile
from apps.business_days.models import BusinessDay
from apps.products.models import Category, Product
from apps.inventory.models import Supplier, SupplierProduct, InventoryTransaction
from apps.inventory.services import record_inventory_transaction
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment
from apps.payment_support.models import PaymentSupportTicket, CustomerIssue

User = get_user_model()

def run_seed():
    print("[+] Seeding SAEC CAFÉ database...")

    # 1. Create Users
    admin, _ = User.objects.get_or_create(
        email='admin@saec.ac.in',
        defaults={
            'full_name': 'Dr. K. Arul (Canteen Director / Admin)',
            'mobile_number': '9876543210',
            'role': User.Role.ADMIN,
            'is_staff': True,
            'is_superuser': True
        }
    )
    admin.set_password('admin123')
    admin.save()

    cashier, _ = User.objects.get_or_create(
        email='cashier@saec.ac.in',
        defaults={
            'full_name': 'R. Murugan (SAEC CAFÉ Head Cashier)',
            'mobile_number': '9876543211',
            'role': User.Role.CASHIER,
            'is_staff': True
        }
    )
    cashier.set_password('cashier123')
    cashier.save()

    student_user, _ = User.objects.get_or_create(
        email='student@saec.ac.in',
        defaults={
            'full_name': 'V. Ashwin (CSE Final Year)',
            'mobile_number': '9876543212',
            'role': User.Role.STUDENT
        }
    )
    student_user.set_password('student123')
    student_user.save()
    StudentProfile.objects.get_or_create(
        user=student_user,
        defaults={'register_number': '912821104001', 'department': 'Computer Science & Engineering', 'year': 4}
    )

    faculty_user, _ = User.objects.get_or_create(
        email='faculty@saec.ac.in',
        defaults={
            'full_name': 'Prof. M. Selvam (HOD CSE)',
            'mobile_number': '9876543213',
            'role': User.Role.FACULTY
        }
    )
    faculty_user.set_password('faculty123')
    faculty_user.save()
    FacultyProfile.objects.get_or_create(
        user=faculty_user,
        defaults={'staff_number': 'SAEC-FAC-042', 'department': 'Computer Science & Engineering'}
    )

    print("[+] Users seeded (Admin, Cashier, Student, Faculty).")

    # 2. Seed Admin Calendar / Working Days (10:00 AM - 3:30 PM)
    today = timezone.localdate()
    for i in range(-5, 25):
        d = today + timedelta(days=i)
        status_choice = BusinessDay.Status.WORKING_DAY
        reason = None

        if d.weekday() == 6: # Sunday default closed/special
            status_choice = BusinessDay.Status.CLOSED
            reason = "Weekly Canteen Maintenance"
        elif i == 10: # Special holiday test
            status_choice = BusinessDay.Status.HOLIDAY
            reason = "College Public Holiday"

        BusinessDay.objects.get_or_create(
            date=d,
            defaults={
                'status': status_choice,
                'opening_time': time(10, 0),
                'closing_time': time(15, 30),
                'reason': reason,
                'is_ordering_enabled': (status_choice == BusinessDay.Status.WORKING_DAY),
                'daily_order_sequence': 4820,
                'created_by': admin
            }
        )

    print("[+] Canteen calendar seeded (Working Days 10:00 AM - 3:30 PM, Holidays, Maintenance Days).")

    # 3. Seed Categories
    categories_data = [
        ("Tea & Coffee", "Hot beverages brewed fresh", "Coffee"),
        ("Snacks & Savouries", "Puffs, samosas, biscuits", "UtensilsCrossed"),
        ("Fast Food", "Burgers, pizzas, french fries", "Pizza"),
        ("Cool Drinks & Juices", "Pepsi, Bovonto, fresh lime & mango juices", "CupSoda"),
        ("Bakery & Desserts", "Brownies, cream cakes, muffins", "Cake"),
        ("Special Catering", "Bulk biryani, catering meals", "Utensils")
    ]

    cat_objs = {}
    for name, desc, icon in categories_data:
        c, _ = Category.objects.get_or_create(name=name, defaults={'description': desc, 'icon_name': icon})
        cat_objs[name] = c

    print("[+] Product categories seeded.")

    # 4. Seed Products (Single Common Food Menu)
    products_list = [
        ("Cardamom Tea", "Freshly brewed hot milk tea with cardamom", "Tea & Coffee", 15.00, 7.00, Product.FoodType.MADE_TO_ORDER, 5, 100, 15),
        ("Filter Coffee", "Authentic South Indian hot filter coffee", "Tea & Coffee", 20.00, 9.00, Product.FoodType.MADE_TO_ORDER, 5, 80, 15),
        ("Veg Puff", "Crispy hot bakery veg puff", "Snacks & Savouries", 20.00, 12.00, Product.FoodType.READY_FOOD, 0, 50, 10),
        ("Egg Puff", "Spicy baked egg puff", "Snacks & Savouries", 25.00, 15.00, Product.FoodType.READY_FOOD, 0, 45, 10),
        ("Samosa (2 Pcs)", "Traditional potato pea fried samosa", "Snacks & Savouries", 20.00, 10.00, Product.FoodType.READY_FOOD, 0, 30, 8),
        ("Pepsi 250ml", "Chilled carbonated soft drink", "Cool Drinks & Juices", 20.00, 14.00, Product.FoodType.READY_FOOD, 0, 60, 15),
        ("Bovonto 250ml", "South Indian famous grape drink", "Cool Drinks & Juices", 25.00, 18.00, Product.FoodType.READY_FOOD, 0, 50, 10),
        ("Fresh Lime Juice", "Fresh squeezed lime water with mint", "Cool Drinks & Juices", 25.00, 10.00, Product.FoodType.MADE_TO_ORDER, 5, 50, 10),
        ("Veg Cheese Burger", "Grilled veg patty with cheese & lettuce", "Fast Food", 80.00, 45.00, Product.FoodType.MADE_TO_ORDER, 10, 25, 5),
        ("Personal Cheese Pizza", "6-inch mozzarella cheese corn pizza", "Fast Food", 120.00, 70.00, Product.FoodType.MADE_TO_ORDER, 15, 20, 4),
        ("Chocolate Brownie", "Rich chocolate walnut brownie", "Bakery & Desserts", 50.00, 25.00, Product.FoodType.READY_FOOD, 0, 20, 5),
    ]

    for name, desc, cat_name, price, cost, food_type, prep_min, stock, min_s in products_list:
        p, created = Product.objects.get_or_create(
            name=name,
            defaults={
                'description': desc,
                'category': cat_objs[cat_name],
                'price': Decimal(str(price)),
                'cost_price': Decimal(str(cost)),
                'food_type': food_type,
                'preparation_time': prep_min,
                'minimum_advance_time': prep_min,
                'current_stock': stock,
                'minimum_stock': min_s,
                'maximum_stock': stock * 3,
                'is_active': True
            }
        )
        p.update_availability_status()

    print("[+] Core canteen products created under single common food menu.")

    # 5. Suppliers
    sup, _ = Supplier.objects.get_or_create(
        name="Ramanathapuram Bakery & Wholesale",
        defaults={'contact_person': 'K. Ramanathan', 'phone': '9894012345', 'email': 'wholesale@ramnadbakery.com'}
    )
    print("[+] Supplier records created.")

    # 6. Create Historical Orders with CAN-XXXX format
    curr_bday = BusinessDay.objects.get(date=today)
    curr_bday.daily_order_sequence = 4824
    curr_bday.save()

    if not Order.objects.filter(order_number="CAN-4821").exists():
        Order.objects.create(
            order_number="CAN-4821",
            business_day=curr_bday,
            user=student_user,
            customer_type=Order.CustomerType.STUDENT,
            order_source=Order.OrderSource.MOBILE,
            order_type=Order.OrderType.READY_FOOD,
            status=Order.Status.DELIVERED,
            payment_status=Order.PaymentStatus.PAID,
            confirmed_at=timezone.now() - timedelta(hours=2),
            completed_at=timezone.now() - timedelta(hours=1, minutes=45),
            subtotal=Decimal('40.00'),
            total_amount=Decimal('40.00')
        )

    if not Order.objects.filter(order_number="CAN-4822").exists():
        Order.objects.create(
            order_number="CAN-4822",
            business_day=curr_bday,
            user=faculty_user,
            customer_type=Order.CustomerType.FACULTY,
            order_source=Order.OrderSource.MOBILE,
            order_type=Order.OrderType.MADE_TO_ORDER,
            status=Order.Status.PREPARING,
            payment_status=Order.PaymentStatus.PAID,
            confirmed_at=timezone.now() - timedelta(minutes=20),
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00')
        )

    if not Order.objects.filter(order_number="CAN-4823").exists():
        Order.objects.create(
            order_number="CAN-4823",
            business_day=curr_bday,
            user=None,
            customer_type=Order.CustomerType.WALK_IN,
            order_source=Order.OrderSource.POS,
            order_type=Order.OrderType.READY_FOOD,
            status=Order.Status.CONFIRMED,
            payment_status=Order.PaymentStatus.PAID,
            confirmed_at=timezone.now() - timedelta(minutes=10),
            subtotal=Decimal('35.00'),
            total_amount=Decimal('35.00')
        )

    # 7. Customer Issue Report Sample (CAN-4821)
    if not CustomerIssue.objects.filter(order_code="CAN-4821").exists():
        CustomerIssue.objects.create(
            issue_number="ISSUE-8821",
            order_code="CAN-4821",
            user=student_user,
            category=CustomerIssue.Category.BILLING_ISSUE,
            description="Incorrect bill amount calculated during peak lunch hour.",
            status=CustomerIssue.Status.OPEN
        )

    print("[+] Sample historical orders with CAN-XXXX format and customer issue reported.")
    
    try:
        from populate_product_images import main as populate_images
        populate_images()
    except Exception as e:
        print(f"[!] Note on image population: {e}")

    print("[SUCCESS] Seed script execution finished successfully!")

if __name__ == '__main__':
    run_seed()
