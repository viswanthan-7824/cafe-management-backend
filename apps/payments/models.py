from django.db import models
from apps.orders.models import Order

class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = 'CASH', 'Cash Counter'
        UPI = 'UPI', 'UPI Payment (GPay / PhonePe / Paytm)'
        ONLINE = 'ONLINE', 'Online Banking / Gateway'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.UPI)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    transaction_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    is_demo = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return f"Payment #{self.id} for Order {self.order.order_number} (₹{self.amount}) - [{self.status}]"
