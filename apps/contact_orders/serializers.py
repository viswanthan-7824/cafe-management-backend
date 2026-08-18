from rest_framework import serializers
from .models import ContactOrderRequest

class ContactOrderRequestSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.full_name')
    user_mobile = serializers.ReadOnlyField(source='user.mobile_number')
    product_name = serializers.ReadOnlyField(source='product.name')
    product_price = serializers.ReadOnlyField(source='product.price')

    class Meta:
        model = ContactOrderRequest
        fields = [
            'id', 'request_number', 'user', 'user_name', 'user_mobile',
            'product', 'product_name', 'product_price', 'quantity',
            'preferred_pickup_time', 'special_instructions', 'status',
            'rejection_reason', 'order', 'created_at', 'updated_at'
        ]
