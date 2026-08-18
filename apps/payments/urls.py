from django.urls import path
from .views import PaymentCreateVerifyView

urlpatterns = [
    path('verify/', PaymentCreateVerifyView.as_view(), name='payment_verify'),
]
