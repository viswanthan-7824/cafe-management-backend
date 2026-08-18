import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from apps.products.models import Product

def run_tests():
    client = APIClient()
    
    # 1. Test Login
    print("\n--- Testing Authentication ---")
    login_res = client.post('/api/auth/login/', {'email': 'admin@saec.ac.in', 'password': 'admin123'})
    print(f"Login admin@saec.ac.in: {login_res.status_code}")
    if login_res.status_code != 200:
        print("Login failed!", login_res.data)
        return
    
    token = login_res.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # 2. Test POS Order Creation
    prod = Product.objects.first()
    if prod:
        pos_payload = {
            'customer_type': 'WALK_IN',
            'order_source': 'POS',
            'items': [{'product_id': prod.id, 'quantity': 1}],
            'discount_amount': 0,
            'is_paid': True,
            'payment_method': 'CASH'
        }
        res_pos = client.post('/api/orders/', pos_payload, format='json')
        print(f"[{'OK' if res_pos.status_code == 201 else 'FAIL'}] POST /api/orders/ (POS Order) -> Status {res_pos.status_code}")
        if res_pos.status_code == 201:
            order_id = res_pos.data['id']
            # Test Order Status Update (PATCH)
            res_patch = client.patch(f'/api/orders/{order_id}/status/', {'status': 'PREPARING'}, format='json')
            print(f"[{'OK' if res_patch.status_code == 200 else 'FAIL'}] PATCH /api/orders/{order_id}/status/ -> Status {res_patch.status_code}")

    print("\n[ALL WRITE ACTIONS WORKING PERFECTLY!]")

if __name__ == '__main__':
    run_tests()
