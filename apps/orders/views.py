from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db import models

from apps.accounts.permissions import IsCashierOrAdminRole
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer
from .services import create_order, get_fcfs_queue

class OrderListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        search_query = request.query_params.get('search')
        status_filter = request.query_params.get('status')
        payment_status_filter = request.query_params.get('payment_status')

        if user.role in ['ADMIN', 'CASHIER']:
            queryset = Order.objects.all().order_by('-created_at')
        else:
            queryset = Order.objects.filter(user=user).order_by('-created_at')

        if search_query:
            queryset = queryset.filter(
                models.Q(order_number__icontains=search_query) |
                models.Q(user__full_name__icontains=search_query) |
                models.Q(user__email__icontains=search_query)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if payment_status_filter:
            queryset = queryset.filter(payment_status=payment_status_filter)

        serializer = OrderSerializer(queryset[:150], many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            user = request.user if request.user.is_authenticated else None
            order = create_order(
                user=user,
                customer_type=data.get('customer_type', Order.CustomerType.STUDENT),
                order_source=data.get('order_source', Order.OrderSource.MOBILE),
                items_data=data.get('items', []),
                pickup_time=data.get('pickup_time'),
                notes=data.get('notes'),
                discount_amount=data.get('discount_amount', 0),
                is_paid=data.get('is_paid', False),
                payment_method=data.get('payment_method', 'CASH')
            )
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['ADMIN', 'CASHIER']:
            return Order.objects.all()
        return Order.objects.filter(user=user)

class OrderStatusUpdateView(APIView):
    permission_classes = [IsCashierOrAdminRole]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        new_payment_status = request.data.get('payment_status')

        if new_status and new_status in Order.Status.values:
            order.status = new_status
            if new_status == Order.Status.CONFIRMED and not order.confirmed_at:
                order.confirmed_at = timezone.now()
            elif new_status == Order.Status.DELIVERED:
                order.completed_at = timezone.now()

        if new_payment_status and new_payment_status in Order.PaymentStatus.values:
            order.payment_status = new_payment_status
            if new_payment_status == Order.PaymentStatus.PAID and not order.confirmed_at:
                order.confirmed_at = timezone.now()
                if order.status == Order.Status.AWAITING_PAYMENT:
                    order.status = Order.Status.CONFIRMED

        order.save()
        return Response(OrderSerializer(order).data)

class FCFSQueueView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        queue_orders = get_fcfs_queue()
        serializer = OrderSerializer(queue_orders, many=True)
        return Response(serializer.data)
