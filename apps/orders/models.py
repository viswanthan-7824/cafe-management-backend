from django.db import models
from django.conf import settings
from apps.business_days.models import BusinessDay
from apps.products.models import Product

class Order(models.Model):
    class CustomerType(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        FACULTY = 'FACULTY', 'Faculty'
        WALK_IN = 'WALK_IN', 'Walk-in Counter Customer'

    class OrderSource(models.TextChoices):
        MOBILE = 'MOBILE', 'Flutter Mobile App'
        POS = 'POS', 'Cashier POS Counter'

    class OrderType(models.TextChoices):
        READY_FOOD = 'READY_FOOD', 'Ready Food'
        MADE_TO_ORDER = 'MADE_TO_ORDER', 'Made to Order'
        CONTACT_ORDER = 'CONTACT_ORDER', 'Contact & Order'

    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', 'Requested'
        AWAITING_APPROVAL = 'AWAITING_APPROVAL', 'Awaiting Cashier Approval'
        AWAITING_PAYMENT = 'AWAITING_PAYMENT', 'Awaiting Payment'
        PAYMENT_SUPPORT_REQUIRED = 'PAYMENT_SUPPORT_REQUIRED', 'Payment Support Required'
        CONFIRMED = 'CONFIRMED', 'Confirmed (In FCFS Queue)'
        PREPARING = 'PREPARING', 'Preparing in Kitchen'
        READY = 'READY', 'Ready for Pickup'
        DELIVERED = 'DELIVERED', 'Delivered to Customer'
        REJECTED = 'REJECTED', 'Rejected by Canteen'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'
        EXPIRED = 'EXPIRED', 'Expired'

    order_number = models.CharField(max_length=50, help_text="e.g. SAEC-001")
    business_day = models.ForeignKey(BusinessDay, on_delete=models.CASCADE, related_name='orders')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    customer_type = models.CharField(max_length=30, choices=CustomerType.choices, default=CustomerType.STUDENT)
    order_source = models.CharField(max_length=20, choices=OrderSource.choices, default=OrderSource.MOBILE)
    order_type = models.CharField(max_length=30, choices=OrderType.choices, default=OrderType.READY_FOOD)
    
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.CONFIRMED)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    
    pickup_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when payment is verified and order enters FCFS queue")
    completed_at = models.DateTimeField(null=True, blank=True)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number} [{self.status}] - ₹{self.total_amount}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=150)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x {self.quantity} (Order #{self.order.order_number})"
