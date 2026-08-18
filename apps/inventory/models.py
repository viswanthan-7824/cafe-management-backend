from django.db import models
from django.conf import settings
from apps.products.models import Product

class Supplier(models.Model):
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class SupplierProduct(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='suppliers')
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    supplied_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.supplier.name} - {self.product.name} (₹{self.purchase_price})"

class InventoryTransaction(models.Model):
    class TransactionType(models.TextChoices):
        STOCK_IN = 'STOCK_IN', 'Stock In (Purchase)'
        STOCK_OUT = 'STOCK_OUT', 'Stock Out (Manual Removal)'
        SALE = 'SALE', 'Sale (Order Confirmation)'
        ADJUSTMENT = 'ADJUSTMENT', 'Audit Adjustment'
        RETURN = 'RETURN', 'Customer Return / Restock'
        DAMAGE = 'DAMAGE', 'Damaged / Expired Item'

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_transactions')
    transaction_type = models.CharField(max_length=30, choices=TransactionType.choices)
    quantity = models.IntegerField(help_text="Positive for addition, negative for reduction")
    previous_stock = models.IntegerField()
    new_stock = models.IntegerField()
    reference_id = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Order # or Invoice #")
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.transaction_type}: {self.product.name} ({self.quantity:+d}) -> New Stock: {self.new_stock}"
