from rest_framework import serializers
from .models import PaymentSupportTicket, CustomerIssue

class PaymentSupportTicketSerializer(serializers.ModelSerializer):
    order_number = serializers.ReadOnlyField(source='order.order_number')
    user_name = serializers.ReadOnlyField(source='user.full_name')
    user_mobile = serializers.ReadOnlyField(source='user.mobile_number')

    class Meta:
        model = PaymentSupportTicket
        fields = [
            'id', 'ticket_number', 'order', 'order_number', 'user', 'user_name', 'user_mobile',
            'amount', 'transaction_id', 'screenshot', 'status', 'admin_notes', 'created_at', 'updated_at'
        ]

class CustomerIssueSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.full_name')
    user_mobile = serializers.ReadOnlyField(source='user.mobile_number')

    class Meta:
        model = CustomerIssue
        fields = [
            'id', 'issue_number', 'order_code', 'order', 'user', 'user_name', 'user_mobile',
            'category', 'description', 'status', 'admin_response', 'resolved_by', 'created_at', 'updated_at'
        ]
