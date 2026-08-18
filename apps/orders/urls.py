from django.urls import path
from .views import (
    OrderListCreateView,
    OrderDetailView,
    OrderStatusUpdateView,
    FCFSQueueView
)

urlpatterns = [
    path('', OrderListCreateView.as_view(), name='order_list_create'),
    path('create/', OrderListCreateView.as_view(), name='order_create_alias'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('<int:pk>/status/', OrderStatusUpdateView.as_view(), name='order_status_update'),
    path('queue/fcfs/', FCFSQueueView.as_view(), name='fcfs_queue'),
]
