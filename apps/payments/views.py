import uuid
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.orders.models import Order
from .models import Payment
from .serializers import PaymentSerializer

class PaymentCreateVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        method = request.data.get('method', Payment.Method.UPI)
        simulate_failure = request.data.get('simulate_failure', False)

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        tx_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"

        if simulate_failure:
            payment = Payment.objects.create(
                order=order,
                amount=order.total_amount,
                method=method,
                status=Payment.Status.FAILED,
                transaction_id=tx_id
            )
            order.payment_status = Order.PaymentStatus.FAILED
            order.status = Order.Status.PAYMENT_SUPPORT_REQUIRED
            order.save()
            return Response({"message": "Payment failed", "payment": PaymentSerializer(payment).data}, status=status.HTTP_400_BAD_REQUEST)

        # Successful payment simulation / verification
        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount,
            method=method,
            status=Payment.Status.PAID,
            transaction_id=tx_id,
            paid_at=timezone.now()
        )

        order.payment_status = Order.PaymentStatus.PAID
        order.status = Order.Status.CONFIRMED
        if not order.confirmed_at:
            order.confirmed_at = timezone.now()
        order.save()

        return Response({
            "message": "Payment verified successfully",
            "payment": PaymentSerializer(payment).data,
            "order_number": order.order_number
        }, status=status.HTTP_200_OK)
