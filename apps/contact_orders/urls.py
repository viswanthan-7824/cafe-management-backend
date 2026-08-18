from django.urls import path
from .views import ContactOrderRequestListCreateView, ContactOrderApprovalView

urlpatterns = [
    path('', ContactOrderRequestListCreateView.as_view(), name='contact_order_list_create'),
    path('<int:pk>/approval/', ContactOrderApprovalView.as_view(), name='contact_order_approval'),
]
