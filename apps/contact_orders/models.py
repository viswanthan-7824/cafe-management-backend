from django.db import models
from django.conf import settings
from apps.products.models import Product
from apps.orders.models import Order

class ContactOrderRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        ACCEPTED = 'ACCEPTED', 'Accepted by Cashier'
        REJECTED = 'REJECTED', 'Rejected'

    request_number = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contact_requests')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    preferred_pickup_time = models.DateTimeField()
    special_instructions = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField(blank=True, null=True)
    order = models.OneToOneField(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='contact_request')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Special Request #{self.request_number} - {self.product.name} ({self.quantity}) [{self.status}]"
