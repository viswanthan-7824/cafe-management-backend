from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.products.models import Category, Product
from apps.inventory.models import InventoryTransaction, Supplier
from apps.inventory.services import record_inventory_transaction

class InventoryServiceTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Beverages', is_active=True)
        self.product = Product.objects.create(
            name='Cold Coffee',
            category=self.category,
            price=Decimal('35.00'),
            current_stock=20,
            is_active=True
        )

    def test_stock_in_transaction(self):
        trx = record_inventory_transaction(
            product_id=self.product.id,
            transaction_type=InventoryTransaction.TransactionType.STOCK_IN,
            quantity=15,
            reference_id='INV-1001',
            notes='Restock delivery'
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 35)
        self.assertEqual(trx.previous_stock, 20)
        self.assertEqual(trx.new_stock, 35)

    def test_stock_out_insufficient_error(self):
        with self.assertRaises(ValidationError):
            record_inventory_transaction(
                product_id=self.product.id,
                transaction_type=InventoryTransaction.TransactionType.STOCK_OUT,
                quantity=-50,
                notes='Invalid reduction'
            )
