from django.urls import path
from .views import (
    SupplierListCreateView,
    SupplierDetailView,
    InventoryTransactionListCreateView
)

urlpatterns = [
    path('transactions/', InventoryTransactionListCreateView.as_view(), name='inventory_transactions'),
    path('suppliers/', SupplierListCreateView.as_view(), name='supplier_list_create'),
    path('suppliers/<int:pk>/', SupplierDetailView.as_view(), name='supplier_detail'),
]
