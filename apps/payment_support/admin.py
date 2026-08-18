from django.contrib import admin
from .models import PaymentSupportTicket, CustomerIssue

@admin.register(PaymentSupportTicket)
class PaymentSupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'user', 'order', 'transaction_id', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('ticket_number', 'transaction_id', 'user__email')

@admin.register(CustomerIssue)
class CustomerIssueAdmin(admin.ModelAdmin):
    list_display = ('issue_number', 'user', 'order_code', 'category', 'status', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('issue_number', 'order_code', 'user__email', 'description')
