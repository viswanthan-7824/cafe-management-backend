from django.db.models import Sum, Count, Avg, F
from django.db.models.functions import ExtractHour
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from apps.inventory.models import InventoryTransaction
from apps.payment_support.models import PaymentSupportTicket

class DashboardOverviewAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        today_orders = Order.objects.filter(created_at__date=today, payment_status=Order.PaymentStatus.PAID)
        
        today_sales = today_orders.aggregate(total=Sum('total_amount'))['total'] or 0.00
        today_order_count = today_orders.count()
        
        total_products = Product.objects.filter(is_active=True).count()
        low_stock_count = Product.objects.filter(current_stock__lte=F('minimum_stock'), current_stock__gt=0).count()
        out_of_stock_count = Product.objects.filter(current_stock=0).count()
        
        pending_support = PaymentSupportTicket.objects.filter(status=PaymentSupportTicket.Status.OPEN).count()

        return Response({
            "today_sales": float(today_sales),
            "today_orders": today_order_count,
            "total_products": total_products,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "pending_support_tickets": pending_support,
        })

class SalesAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        paid_orders = Order.objects.filter(payment_status=Order.PaymentStatus.PAID)
        
        source_breakdown = paid_orders.values('order_source').annotate(
            total_sales=Sum('total_amount'),
            count=Count('id')
        )
        
        customer_breakdown = paid_orders.values('customer_type').annotate(
            total_sales=Sum('total_amount'),
            count=Count('id')
        )

        return Response({
            "total_revenue": float(paid_orders.aggregate(total=Sum('total_amount'))['total'] or 0.00),
            "total_orders": paid_orders.count(),
            "average_order_value": float(paid_orders.aggregate(avg=Avg('total_amount'))['avg'] or 0.00),
            "source_breakdown": list(source_breakdown),
            "customer_breakdown": list(customer_breakdown),
        })

class ProductPerformanceAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        top_products = OrderItem.objects.filter(order__payment_status=Order.PaymentStatus.PAID)\
            .values('product_name')\
            .annotate(total_quantity=Sum('quantity'), total_revenue=Sum('total_price'))\
            .order_by('-total_quantity')[:10]
            
        return Response({"top_products": list(top_products)})

class PeakHoursAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        hourly_orders = Order.objects.annotate(hour=ExtractHour('created_at'))\
            .values('hour')\
            .annotate(order_count=Count('id'), revenue=Sum('total_amount'))\
            .order_by('hour')
            
        return Response({"peak_hours": list(hourly_orders)})
