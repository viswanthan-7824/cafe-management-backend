from rest_framework import generics, permissions, filters
from rest_framework.response import Response
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer

class CategoryListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Category.objects.filter(is_active=True).order_by('name')
    serializer_class = CategorySerializer

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'sku', 'barcode', 'category__name']
    ordering_fields = ['name', 'price', 'current_stock', 'category']

    def get_queryset(self):
        queryset = Product.objects.all()
        category_id = self.request.query_params.get('category')
        food_type = self.request.query_params.get('food_type')
        availability = self.request.query_params.get('availability')

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if food_type:
            queryset = queryset.filter(food_type=food_type)
        if availability:
            queryset = queryset.filter(availability_status=availability)
            
        return queryset.order_by('name')

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
