from rest_framework import serializers
from .models import Order, OrderItem
from apps.products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'unit_price', 'quantity', 'total_price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.SerializerMethodField()
    customer_role = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'business_day', 'user', 'customer_name', 'customer_role',
            'customer_type', 'order_source', 'order_type', 'status', 'payment_status',
            'pickup_time', 'created_at', 'confirmed_at', 'completed_at',
            'subtotal', 'discount_amount', 'total_amount', 'notes', 'items'
        ]

    def get_customer_name(self, obj):
        if obj.user:
            return obj.user.full_name
        return "Walk-in Counter Customer"

    def get_customer_role(self, obj):
        if obj.user:
            return obj.user.role
        return "WALK_IN"

class OrderCreateSerializer(serializers.Serializer):
    customer_type = serializers.ChoiceField(choices=Order.CustomerType.choices, default=Order.CustomerType.STUDENT)
    order_source = serializers.ChoiceField(choices=Order.OrderSource.choices, default=Order.OrderSource.MOBILE)
    items = serializers.ListField(child=serializers.DictField())
    pickup_time = serializers.DateTimeField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_paid = serializers.BooleanField(default=False)
    payment_method = serializers.CharField(default='CASH')
