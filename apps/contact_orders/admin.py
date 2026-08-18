from django.contrib import admin
from .models import ContactOrderRequest

@admin.register(ContactOrderRequest)
class ContactOrderRequestAdmin(admin.ModelAdmin):
    list_display = ('request_number', 'user', 'product', 'quantity', 'preferred_pickup_time', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('request_number', 'product__name', 'user__email')
