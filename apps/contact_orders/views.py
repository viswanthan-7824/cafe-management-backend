import uuid
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.orders.services import create_order
from apps.orders.models import Order
from .models import ContactOrderRequest
from .serializers import ContactOrderRequestSerializer

class ContactOrderRequestListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role in ['ADMIN', 'CASHIER']:
            requests = ContactOrderRequest.objects.all().order_by('-created_at')
        else:
            requests = ContactOrderRequest.objects.filter(user=request.user).order_by('-created_at')
        return Response(ContactOrderRequestSerializer(requests, many=True).data)

    def post(self, request):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        preferred_pickup_time = request.data.get('preferred_pickup_time')
        special_instructions = request.data.get('special_instructions', '')

        req_no = f"REQ-{uuid.uuid4().hex[:6].upper()}"

        req = ContactOrderRequest.objects.create(
            request_number=req_no,
            user=request.user,
            product_id=product_id,
            quantity=quantity,
            preferred_pickup_time=preferred_pickup_time,
            special_instructions=special_instructions,
            status=ContactOrderRequest.Status.PENDING
        )
        return Response(ContactOrderRequestSerializer(req).data, status=status.HTTP_201_CREATED)

class ContactOrderApprovalView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if request.user.role not in ['ADMIN', 'CASHIER']:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        try:
            req = ContactOrderRequest.objects.get(pk=pk)
        except ContactOrderRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action') # 'ACCEPT' or 'REJECT'
        rejection_reason = request.data.get('rejection_reason', '')

        if action == 'ACCEPT':
            req.status = ContactOrderRequest.Status.ACCEPTED
            # Create corresponding Order with status AWAITING_PAYMENT
            items_data = [{'product_id': req.product.id, 'quantity': req.quantity}]
            order = create_order(
                user=req.user,
                customer_type=Order.CustomerType(req.user.role) if req.user.role in Order.CustomerType.values else Order.CustomerType.STUDENT,
                order_source=Order.OrderSource.MOBILE,
                items_data=items_data,
                pickup_time=req.preferred_pickup_time,
                notes=f"Special Request #{req.request_number}: {req.special_instructions}",
                is_paid=False,
                order_type=Order.OrderType.CONTACT_ORDER
            )
            order.status = Order.Status.AWAITING_PAYMENT
            order.save()
            req.order = order
        else:
            req.status = ContactOrderRequest.Status.REJECTED
            req.rejection_reason = rejection_reason

        req.save()
        return Response(ContactOrderRequestSerializer(req).data)
