from rest_framework import serializers
from .models import Category, Product

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'icon_name', 'image', 'is_active', 'product_count', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'price', 'cost_price', 'image', 'barcode', 'sku',
            'food_type', 'preparation_time', 'minimum_advance_time',
            'current_stock', 'minimum_stock', 'maximum_stock',
            'availability_status', 'is_active', 'created_at', 'updated_at'
        ]
