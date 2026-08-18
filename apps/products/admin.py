from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'food_type', 'preparation_time', 'current_stock', 'minimum_stock', 'availability_status', 'is_active')
    list_filter = ('food_type', 'availability_status', 'is_active', 'category')
    search_fields = ('name', 'sku', 'barcode')
