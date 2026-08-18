from django.db import models
from django.conf import settings
from apps.orders.models import Order

class PaymentSupportTicket(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        VERIFIED = 'VERIFIED', 'Payment Verified'
        REJECTED = 'REJECTED', 'Ticket Rejected'
        RESOLVED = 'RESOLVED', 'Resolved'

    ticket_number = models.CharField(max_length=50, unique=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='support_tickets')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_tickets')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100)
    screenshot = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket #{self.ticket_number} - Order {self.order.order_number} [{self.status}]"


class CustomerIssue(models.Model):
    class Category(models.TextChoices):
        BILLING_ISSUE = 'BILLING', 'Billing Issue'
        PAYMENT_ISSUE = 'PAYMENT', 'Payment Issue'
        MISSING_ITEM = 'MISSING_ITEM', 'Missing Item'
        INCORRECT_ITEM = 'INCORRECT_ITEM', 'Incorrect Item'
        ORDER_ISSUE = 'ORDER_ISSUE', 'Order Issue'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        RESOLVED = 'RESOLVED', 'Resolved'

    issue_number = models.CharField(max_length=50, unique=True)
    order_code = models.CharField(max_length=50)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='customer_issues')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_issues')
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.ORDER_ISSUE)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    admin_response = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_issues')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Issue #{self.issue_number} - {self.order_code} [{self.category}]"
