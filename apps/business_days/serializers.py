from rest_framework import serializers
from .models import BusinessDay

class BusinessDaySerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source='created_by.full_name')

    class Meta:
        model = BusinessDay
        fields = [
            'id', 'date', 'status', 'opening_time', 'closing_time',
            'reason', 'notes', 'is_ordering_enabled', 'daily_order_sequence',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
