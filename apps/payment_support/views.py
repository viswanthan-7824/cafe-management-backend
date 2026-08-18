import uuid
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.orders.models import Order
from apps.payments.models import Payment
from .models import PaymentSupportTicket, CustomerIssue
from .serializers import PaymentSupportTicketSerializer, CustomerIssueSerializer

class PaymentSupportTicketListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role in ['ADMIN', 'CASHIER']:
            tickets = PaymentSupportTicket.objects.all().order_by('-created_at')
        else:
            tickets = PaymentSupportTicket.objects.filter(user=request.user).order_by('-created_at')
        return Response(PaymentSupportTicketSerializer(tickets, many=True).data)

    def post(self, request):
        order_id = request.data.get('order_id')
        transaction_id = request.data.get('transaction_id')
        screenshot = request.FILES.get('screenshot')

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        ticket_no = f"PAY-{uuid.uuid4().hex[:6].upper()}"

        ticket = PaymentSupportTicket.objects.create(
            ticket_number=ticket_no,
            order=order,
            user=request.user,
            amount=order.total_amount,
            transaction_id=transaction_id,
            screenshot=screenshot,
            status=PaymentSupportTicket.Status.OPEN
        )

        order.status = Order.Status.PAYMENT_SUPPORT_REQUIRED
        order.save()

        return Response(PaymentSupportTicketSerializer(ticket).data, status=status.HTTP_201_CREATED)

class PaymentSupportTicketVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if request.user.role not in ['ADMIN', 'CASHIER']:
            return Response({"error": "Only admins/cashiers can verify tickets."}, status=status.HTTP_403_FORBIDDEN)

        try:
            ticket = PaymentSupportTicket.objects.get(pk=pk)
        except PaymentSupportTicket.DoesNotExist:
            return Response({"error": "Ticket not found"}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action') # 'VERIFY' or 'REJECT'
        admin_notes = request.data.get('notes', '')

        ticket.admin_notes = admin_notes
        order = ticket.order

        if action == 'VERIFY':
            ticket.status = PaymentSupportTicket.Status.VERIFIED
            order.payment_status = Order.PaymentStatus.PAID
            order.status = Order.Status.CONFIRMED
            if not order.confirmed_at:
                order.confirmed_at = timezone.now()
            order.save()

            Payment.objects.update_or_create(
                order=order,
                defaults={
                    'amount': ticket.amount,
                    'method': Payment.Method.UPI,
                    'status': Payment.Status.PAID,
                    'transaction_id': ticket.transaction_id,
                    'paid_at': timezone.now()
                }
            )
        else:
            ticket.status = PaymentSupportTicket.Status.REJECTED
            order.payment_status = Order.PaymentStatus.FAILED
            order.status = Order.Status.CANCELLED
            order.save()

        ticket.save()
        return Response(PaymentSupportTicketSerializer(ticket).data)


class CustomerIssueListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role in ['ADMIN', 'CASHIER']:
            issues = CustomerIssue.objects.all().order_by('-created_at')
        else:
            issues = CustomerIssue.objects.filter(user=request.user).order_by('-created_at')
        return Response(CustomerIssueSerializer(issues, many=True).data)

    def post(self, request):
        order_code = request.data.get('order_code', '').strip().upper()
        category = request.data.get('category', CustomerIssue.Category.ORDER_ISSUE)
        description = request.data.get('description', '')

        if not order_code:
            return Response({"error": "Order code is required (e.g. CAN-4821)"}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.filter(order_number__iexact=order_code).first()

        issue_no = f"ISSUE-{uuid.uuid4().hex[:6].upper()}"

        issue = CustomerIssue.objects.create(
            issue_number=issue_no,
            order_code=order_code,
            order=order,
            user=request.user,
            category=category,
            description=description,
            status=CustomerIssue.Status.OPEN
        )

        return Response(CustomerIssueSerializer(issue).data, status=status.HTTP_201_CREATED)


class CustomerIssueDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        if request.user.role not in ['ADMIN', 'CASHIER']:
            return Response({"error": "Only admins/cashiers can update customer issues."}, status=status.HTTP_403_FORBIDDEN)

        try:
            issue = CustomerIssue.objects.get(pk=pk)
        except CustomerIssue.DoesNotExist:
            return Response({"error": "Issue not found"}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        admin_response = request.data.get('admin_response')

        if new_status and new_status in CustomerIssue.Status.values:
            issue.status = new_status
            if new_status == CustomerIssue.Status.RESOLVED:
                issue.resolved_by = request.user

        if admin_response is not None:
            issue.admin_response = admin_response

        issue.save()
        return Response(CustomerIssueSerializer(issue).data)
