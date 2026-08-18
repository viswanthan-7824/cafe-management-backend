from django.urls import path
from .views import (
    PaymentSupportTicketListCreateView,
    PaymentSupportTicketVerifyView,
    CustomerIssueListCreateView,
    CustomerIssueDetailView
)

urlpatterns = [
    path('', PaymentSupportTicketListCreateView.as_view(), name='payment_support_list_create'),
    path('<int:pk>/verify/', PaymentSupportTicketVerifyView.as_view(), name='payment_support_verify'),
    path('issues/', CustomerIssueListCreateView.as_view(), name='customer_issue_list_create'),
    path('issues/<int:pk>/', CustomerIssueDetailView.as_view(), name='customer_issue_detail'),
]
