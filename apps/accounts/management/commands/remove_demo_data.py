from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.accounts.models import StudentProfile, FacultyProfile
from apps.products.models import Product
from apps.business_days.models import BusinessDay
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment
from apps.payment_support.models import PaymentSupportTicket, CustomerIssue
from apps.contact_orders.models import ContactOrderRequest

User = get_user_model()


class Command(BaseCommand):
    help = 'Safely removes ONLY demo records (is_demo=True) while strictly preserving all real production data.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=" * 70))
        self.stdout.write(self.style.WARNING("   [WARNING] SAEC CAFE - REMOVING DEMO DATA ONLY [WARNING]"))
        self.stdout.write(self.style.WARNING("=" * 70))
        self.stdout.write(self.style.NOTICE("This operation will safely delete ONLY demo records (is_demo=True).\nAll real production user accounts, orders, and products are strictly preserved.\n"))

        # 1. Purge Demo Support & Catering Tickets
        c_issue_count, _ = CustomerIssue.objects.filter(is_demo=True).delete()
        p_ticket_count, _ = PaymentSupportTicket.objects.filter(is_demo=True).delete()
        cat_req_count, _ = ContactOrderRequest.objects.filter(is_demo=True).delete()

        # 2. Purge Demo Payments & Orders
        pay_count, _ = Payment.objects.filter(is_demo=True).delete()
        demo_orders = Order.objects.filter(is_demo=True)
        order_items_count, _ = OrderItem.objects.filter(order__in=demo_orders).delete()
        orders_count, _ = demo_orders.delete()

        # 3. Purge Demo Business Days
        bday_count, _ = BusinessDay.objects.filter(is_demo=True).delete()

        # 4. Purge Demo Products
        prod_count, _ = Product.objects.filter(is_demo=True).delete()

        # 5. Purge Demo Users & Profiles
        demo_users = User.objects.filter(is_demo=True) | User.objects.filter(email__endswith='.demo@example.com')
        stud_prof_count, _ = StudentProfile.objects.filter(user__in=demo_users).delete()
        fac_prof_count, _ = FacultyProfile.objects.filter(user__in=demo_users).delete()
        users_count, _ = demo_users.delete()

        self.stdout.write(self.style.SUCCESS("Demo cleanup summary:"))
        self.stdout.write(f"  - Demo Orders deleted         : {orders_count} orders ({order_items_count} items)")
        self.stdout.write(f"  - Demo Payments deleted       : {pay_count}")
        self.stdout.write(f"  - Demo Support Tickets deleted: {p_ticket_count} tickets, {c_issue_count} issues")
        self.stdout.write(f"  - Demo Catering Requests      : {cat_req_count}")
        self.stdout.write(f"  - Demo Business Days deleted  : {bday_count}")
        self.stdout.write(f"  - Demo Food Products deleted  : {prod_count}")
        self.stdout.write(f"  - Demo User Accounts deleted  : {users_count}")

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write(self.style.SUCCESS(">> DEMO DATA CLEANUP COMPLETE: ALL DEMO RECORDS PURGED (PASS) <<"))
        self.stdout.write(self.style.SUCCESS("=" * 70))
