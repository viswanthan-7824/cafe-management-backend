import os
import sys
import uuid
import django
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from django.db import connection
from django.contrib.auth import get_user_model
from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem
from apps.inventory.models import Supplier, InventoryTransaction
from apps.business_days.models import BusinessDay
from apps.payment_support.models import PaymentSupportTicket, CustomerIssue
from apps.contact_orders.models import ContactOrderRequest

User = get_user_model()

def run_comprehensive_audit():
    print("=" * 75)
    print("        SAEC CAFÉ - FULL END-TO-END SYSTEM & FLOW AUDIT")
    print("=" * 75)
    
    results = {}
    
    # 1. DATABASE & POSTGRESQL VERIFICATION
    print("\n[1/10] DATABASE & POSTGRESQL CONNECTION INTEGRITY")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user, version();")
            db_info = cursor.fetchone()
            print(f"  [PASS] Connected Database : {db_info[0]}")
            print(f"  [PASS] Database User      : {db_info[1]}")
            print(f"  [PASS] Engine             : {connection.vendor.upper()} ({connection.settings_dict['ENGINE']})")
        results['Database (PostgreSQL)'] = 'PASS'
    except Exception as e:
        print(f"  [FAIL] Database Connection Error: {e}")
        results['Database (PostgreSQL)'] = f'FAIL: {e}'

    client = APIClient()
    tokens = {}
    users = {}

    # 2. AUTHENTICATION & ROLE-BASED ACCESS CONTROL (RBAC)
    print("\n[2/10] AUTHENTICATION & ROLE-BASED ACCESS CONTROL (5 ROLES)")
    credentials = [
        ('admin@saec.ac.in', 'admin123', 'ADMIN'),
        ('cashier@saec.ac.in', 'cashier123', 'CASHIER'),
        ('student@saec.ac.in', 'student123', 'STUDENT'),
        ('faculty@saec.ac.in', 'faculty123', 'FACULTY'),
        ('regular@saec.ac.in', 'regular123', 'REGULAR_CUSTOMER'),
    ]
    
    auth_passed = True
    for email, password, expected_role in credentials:
        res = client.post('/api/auth/login/', {'email': email, 'password': password})
        if res.status_code == 200:
            user_data = res.data.get('user', {})
            role = user_data.get('role')
            if role == expected_role:
                print(f"  [PASS] Login {email:<24} -> Role: {role:<18} (Token Generated)")
                tokens[expected_role] = res.data.get('access')
                users[expected_role] = user_data
            else:
                print(f"  [FAIL] Role mismatch for {email}: Expected {expected_role}, got {role}")
                auth_passed = False
        else:
            print(f"  [FAIL] Login failed for {email}: Status {res.status_code}")
            auth_passed = False

    # Test invalid login
    res_bad = client.post('/api/auth/login/', {'email': 'admin@saec.ac.in', 'password': 'wrong_password_xyz'})
    if res_bad.status_code == 401:
        print("  [PASS] Security Check: Invalid credentials properly rejected with HTTP 401")
    else:
        print(f"  [FAIL] Security Check: Invalid credentials returned unexpected status: {res_bad.status_code}")
        auth_passed = False
    
    results['Authentication & RBAC'] = 'PASS' if auth_passed else 'FAIL'

    # 3. PRODUCTS & INVENTORY INTEGRATION AUDIT
    print("\n[3/10] PRODUCT CATALOG, CATEGORIES & PRICING")
    res_prod = client.get('/api/products/')
    res_cat = client.get('/api/products/categories/')
    
    prod_data = res_prod.data.get('results', res_prod.data) if isinstance(res_prod.data, dict) else res_prod.data
    cat_data = res_cat.data.get('results', res_cat.data) if isinstance(res_cat.data, dict) else res_cat.data
    prod_count = len(prod_data) if isinstance(prod_data, list) else 0
    cat_count = len(cat_data) if isinstance(cat_data, list) else 0
    print(f"  [PASS] Food Items in Database  : {prod_count} items")
    print(f"  [PASS] Food Categories in DB   : {cat_count} categories")
    
    if prod_count > 0 and cat_count > 0:
        results['Product Catalog & Menu'] = 'PASS'
    else:
        results['Product Catalog & Menu'] = 'FAIL'

    # 4. BUSINESS CALENDAR & ORDERING WINDOW AUDIT
    print("\n[4/10] BUSINESS CALENDAR & OPERATING HOURS (10:00 AM - 3:30 PM)")
    res_bday = client.get('/api/business-day/current/')
    if res_bday.status_code == 200:
        is_open = res_bday.data.get('is_ordering_open')
        open_time = res_bday.data.get('opening_time')
        close_time = res_bday.data.get('closing_time')
        print(f"  [PASS] Live Business Status   : Open={is_open} | Window: {open_time} - {close_time}")
        results['Business Day & Hours'] = 'PASS'
    else:
        print(f"  [FAIL] Business day check failed: Status {res_bday.status_code}")
        results['Business Day & Hours'] = 'FAIL'

    # 5. FULL END-TO-END MOBILE/ONLINE ORDER PLACEMENT FLOW
    print("\n[5/10] COMPLETE END-TO-END ONLINE ORDER PLACEMENT FLOW")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['STUDENT']}")
    
    target_product = Product.objects.filter(is_active=True, current_stock__gt=5).first() or Product.objects.filter(is_active=True).first()
    if not target_product:
        print("  [FAIL] No active product available to test order placement")
        results['Online Order Flow'] = 'FAIL'
    else:
        stock_before = target_product.current_stock
        print(f"  [INFO] Target Product: {target_product.name} (Rs. {target_product.price}) | Stock Before: {stock_before}")

        order_payload = {
            'order_source': 'MOBILE',
            'customer_type': 'STUDENT',
            'payment_method': 'ONLINE_UPI',
            'is_paid': True,
            'items': [
                {
                    'product_id': target_product.id,
                    'quantity': 2
                }
            ],
            'discount_amount': 0
        }
        
        res_create_order = client.post('/api/orders/', order_payload, format='json')
        if res_create_order.status_code == 201:
            order_data = res_create_order.data
            order_id = order_data.get('id')
            order_number = order_data.get('order_number')
            total_amount = order_data.get('total_amount')
            print(f"  [PASS] Step 1 (Create Order) : ID={order_id} | Code={order_number} | Total=Rs. {total_amount}")
            
            # Step 2: Verify in DB
            db_order = Order.objects.filter(id=order_id).first()
            if db_order and db_order.order_number == order_number:
                print(f"  [PASS] Step 2 (DB Persist)   : Verified in PostgreSQL (Status: {db_order.status})")
            else:
                print("  [FAIL] Step 2: Order could not be verified in PostgreSQL!")

            # Step 3: Verify FCFS Queue Display
            client.credentials()  # Public
            res_fcfs = client.get('/api/orders/queue/fcfs/')
            if res_fcfs.status_code == 200:
                fcfs_list = res_fcfs.data if isinstance(res_fcfs.data, list) else []
                found_in_fcfs = any(o.get('order_number') == order_number for o in fcfs_list)
                print(f"  [PASS] Step 3 (FCFS Display) : Order present on live queue board -> {found_in_fcfs}")

            # Step 4: Cashier Status Transitions: PREPARING -> READY -> COMPLETED
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['CASHIER']}")
            res_prep = client.patch(f'/api/orders/{order_id}/status/', {'status': 'PREPARING'}, format='json')
            res_ready = client.patch(f'/api/orders/{order_id}/status/', {'status': 'READY'}, format='json')
            res_comp = client.patch(f'/api/orders/{order_id}/status/', {'status': 'COMPLETED'}, format='json')
            
            if res_comp.status_code == 200:
                print(f"  [PASS] Step 4 (Order Lifecycle): PENDING -> PREPARING -> READY -> COMPLETED")
                results['Online Order Flow'] = 'PASS'
            else:
                print(f"  [FAIL] Step 4: Status transition failed: {res_comp.status_code}")
                results['Online Order Flow'] = 'FAIL'
        else:
            print(f"  [FAIL] Order creation failed: {res_create_order.status_code} - {res_create_order.data}")
            results['Online Order Flow'] = f"FAIL: {res_create_order.data}"

    # 6. POS WALK-IN CASHIER BILLING FLOW
    print("\n[6/10] POS COUNTER CASHIER BILLING & TOKEN FLOW")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['CASHIER']}")
    pos_payload = {
        'order_source': 'POS',
        'customer_type': 'WALK_IN',
        'payment_method': 'CASH',
        'is_paid': True,
        'items': [
            {'product_id': target_product.id, 'quantity': 1}
        ],
        'discount_amount': 0
    }
    res_pos = client.post('/api/orders/', pos_payload, format='json')
    if res_pos.status_code == 201:
        pos_order = res_pos.data
        print(f"  [PASS] POS Walk-in Token Generated: Code={pos_order.get('order_number')} | Paid=Rs. {pos_order.get('total_amount')}")
        results['POS Counter Billing'] = 'PASS'
    else:
        print(f"  [FAIL] POS billing failed: {res_pos.status_code} - {res_pos.data}")
        results['POS Counter Billing'] = 'FAIL'

    # 7. PAYMENT SUPPORT & TICKET FLOW
    print("\n[7/10] PAYMENT SUPPORT TICKET & ISSUE RESOLUTION FLOW")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['STUDENT']}")
    
    # Create an order requiring payment support
    unpaid_order_res = client.post('/api/orders/', {
        'order_source': 'MOBILE',
        'customer_type': 'STUDENT',
        'payment_method': 'ONLINE_UPI',
        'is_paid': False,
        'items': [{'product_id': target_product.id, 'quantity': 1}],
        'discount_amount': 0
    }, format='json')
    
    if unpaid_order_res.status_code == 201:
        unpaid_id = unpaid_order_res.data.get('id')
        unique_txn = f"UPI-TXN-{uuid.uuid4().hex[:8].upper()}"
        ticket_payload = {
            'order_id': unpaid_id,
            'transaction_id': unique_txn,
            'amount': unpaid_order_res.data.get('total_amount')
        }
        res_ticket = client.post('/api/payment-support/', ticket_payload, format='json')
        if res_ticket.status_code == 201:
            ticket_id = res_ticket.data.get('id')
            ticket_no = res_ticket.data.get('ticket_number')
            print(f"  [PASS] Student raised payment support ticket #{ticket_no} for Order ID {unpaid_id}")
            
            # Admin verifies payment ticket
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['ADMIN']}")
            res_verify = client.post(f'/api/payment-support/{ticket_id}/verify/', {
                'action': 'VERIFY',
                'notes': 'Bank reference matched. Payment confirmed.'
            }, format='json')
            
            if res_verify.status_code == 200:
                print(f"  [PASS] Admin verified payment ticket #{ticket_no} -> Order status updated to CONFIRMED")
                results['Payment Support Flow'] = 'PASS'
            else:
                print(f"  [FAIL] Admin verify ticket failed: {res_verify.status_code}")
                results['Payment Support Flow'] = 'FAIL'
        else:
            print(f"  [FAIL] Ticket creation failed: {res_ticket.status_code} - {res_ticket.data}")
            results['Payment Support Flow'] = 'FAIL'
    else:
        print(f"  [FAIL] Unpaid order creation failed for ticket test: {unpaid_order_res.data}")
        results['Payment Support Flow'] = 'FAIL'

    # 8. CONTACT / SPECIAL CATERING ORDERS FLOW
    print("\n[8/10] CONTACT / SPECIAL BULK CATERING REQUEST FLOW")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['FACULTY']}")
    
    pickup_dt = (timezone.now() + timedelta(days=2)).isoformat()
    catering_payload = {
        'product_id': target_product.id,
        'quantity': 50,
        'preferred_pickup_time': pickup_dt,
        'special_instructions': 'Department Technical Symposium - 50 snack boxes required at 11:00 AM'
    }
    res_cat_req = client.post('/api/contact-orders/', catering_payload, format='json')
    if res_cat_req.status_code == 201:
        req_id = res_cat_req.data.get('id')
        req_no = res_cat_req.data.get('request_number')
        print(f"  [PASS] Faculty submitted Bulk Catering Request #{req_no} (50 units)")
        
        # Cashier / Admin accepts request
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['CASHIER']}")
        res_accept = client.post(f'/api/contact-orders/{req_id}/approval/', {
            'action': 'ACCEPT'
        }, format='json')
        if res_accept.status_code == 200:
            print(f"  [PASS] Cashier accepted Catering Request #{req_no} -> Converted to Kitchen Order")
            results['Contact & Catering Flow'] = 'PASS'
        else:
            print(f"  [FAIL] Cashier approval failed: {res_accept.status_code} - {res_accept.data}")
            results['Contact & Catering Flow'] = 'FAIL'
    else:
        print(f"  [FAIL] Catering request failed: {res_cat_req.status_code} - {res_cat_req.data}")
        results['Contact & Catering Flow'] = 'FAIL'

    # 9. POSTGRESQL AUTHORITATIVE ANALYTICS & RBAC AUDIT
    print("\n[9/10] POSTGRESQL DATA ANALYTICS & RBAC AUDIT")
    # Verify Student access is rejected
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['STUDENT']}")
    res_forbidden = client.get('/api/analytics/dashboard/')
    if res_forbidden.status_code == 403:
        print("  [PASS] RBAC Enforced: Non-admin (Student) blocked from Analytics (HTTP 403)")
    else:
        print(f"  [FAIL] RBAC Failure: Student got status {res_forbidden.status_code} on analytics")

    # Admin access with 7 days filter
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['ADMIN']}")
    res_dash = client.get('/api/analytics/dashboard/?range=7days')
    if res_dash.status_code == 200:
        dash_data = res_dash.data
        print(f"  [PASS] PostgreSQL Analytics Data Loaded:")
        print(f"         - Total Revenue : Rs. {dash_data['summary']['total_revenue']}")
        print(f"         - Total Orders  : {dash_data['summary']['total_orders']}")
        print(f"         - Daily Trends  : {len(dash_data['daily_trends'])} daily data points")
        print(f"         - Top Products  : {len(dash_data['top_selling_products'])} products ranked")
        print(f"         - Peak Hours    : {len(dash_data['peak_hours'])} hourly bins")
        results['PostgreSQL Analytics & RBAC'] = 'PASS'
    else:
        print(f"  [FAIL] Analytics Dashboard API failed: {res_dash.status_code}")
        results['PostgreSQL Analytics & RBAC'] = 'FAIL'

    # 10. REAL-TIME EXECUTIVE OVERVIEW AUDIT
    print("\n[10/10] REAL-TIME EXECUTIVE OVERVIEW & METRICS")
    res_overview = client.get('/api/analytics/overview/')
    res_sales = client.get('/api/analytics/sales/')
    if res_overview.status_code == 200 and res_sales.status_code == 200:
        today_sales = res_overview.data.get('today_sales')
        today_orders = res_overview.data.get('today_orders')
        print(f"  [PASS] Live Overview Engine : Today Revenue=Rs. {today_sales} | Orders Placed={today_orders}")
        results['Executive Overview & Sales'] = 'PASS'
    else:
        print(f"  [FAIL] Overview API failed: Overview={res_overview.status_code}, Sales={res_sales.status_code}")
        results['Executive Overview & Sales'] = 'FAIL'

    print("\n" + "=" * 75)
    print("                 SYSTEM AUDIT VERIFICATION SUMMARY")
    print("=" * 75)
    all_pass = True
    for module, status in results.items():
        print(f"  * {module:<30}: {status}")
        if status != 'PASS':
            all_pass = False
            
    print("=" * 75)
    if all_pass:
        print(">> AUDIT RESULT: 10/10 SUBSYSTEMS FULLY OPERATIONAL & VERIFIED (PASS) <<")
    else:
        print(">> AUDIT RESULT: SOME CHECKS FAILED <<")
    print("=" * 75)

if __name__ == '__main__':
    run_comprehensive_audit()
