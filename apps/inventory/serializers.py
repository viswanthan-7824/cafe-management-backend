from rest_framework import serializers
from .models import Supplier, SupplierProduct, InventoryTransaction
from apps.products.serializers import ProductSerializer

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact_person', 'phone', 'email', 'address', 'created_at']

class SupplierProductSerializer(serializers.ModelSerializer):
    supplier_name = serializers.ReadOnlyField(source='supplier.name')
    product_name = serializers.ReadOnlyField(source='product.name')

    class Meta:
        model = SupplierProduct
        fields = ['id', 'supplier', 'supplier_name', 'product', 'product_name', 'purchase_price', 'supplied_date']

class InventoryTransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    created_by_name = serializers.ReadOnlyField(source='created_by.full_name')

    class Meta:
        model = InventoryTransaction
        fields = [
            'id', 'product', 'product_name', 'transaction_type',
            'quantity', 'previous_stock', 'new_stock',
            'reference_id', 'notes', 'created_by', 'created_by_name', 'timestamp'
        ]
