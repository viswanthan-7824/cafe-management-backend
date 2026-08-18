from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_number', 'user', 'customer_type', 'order_source', 'status', 'payment_status', 'total_amount', 'created_at')
    list_filter = ('status', 'payment_status', 'customer_type', 'order_source', 'created_at')
    search_fields = ('order_number', 'user__email', 'user__full_name')
    inlines = [OrderItemInline]
