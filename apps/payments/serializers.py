from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.ReadOnlyField(source='order.order_number')

    class Meta:
        model = Payment
        fields = ['id', 'order', 'order_number', 'amount', 'method', 'status', 'transaction_id', 'created_at', 'paid_at']
