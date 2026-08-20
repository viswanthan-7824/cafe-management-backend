from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import TruncDate, ExtractHour
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.contrib.auth import get_user_model

from apps.accounts.permissions import IsAdminUserRole
from apps.orders.models import Order, OrderItem
from apps.products.models import Product, Category
from apps.payment_support.models import PaymentSupportTicket

User = get_user_model()


def get_date_range_filter(range_type, start_date_str=None, end_date_str=None):
    """
    Parses date range filters for authoritative PostgreSQL analytics queries.
    Returns (start_dt, end_dt) aware datetimes in local timezone.
    """
    now = timezone.localtime()
    today = now.date()

    if range_type == 'today':
        start_date = today
        end_date = today
    elif range_type == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif range_type == '7days':
        start_date = today - timedelta(days=6)
        end_date = today
    elif range_type == '30days':
        start_date = today - timedelta(days=29)
        end_date = today
    elif range_type == 'this_month':
        start_date = today.replace(day=1)
        end_date = today
    elif range_type == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = today - timedelta(days=6)
            end_date = today
    else:
        start_date = today - timedelta(days=6)
        end_date = today

    start_dt = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    end_dt = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

    return start_dt, end_dt, start_date, end_date


class DashboardOverviewAnalyticsView(APIView):
    """
    Overview stats for main management dashboard.
    Restricted to Administrator role.
    """
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        today = timezone.localdate()
        today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))

        # Today's orders & revenue
        today_orders_qs = Order.objects.filter(created_at__range=(today_start, today_end))
        today_paid_qs = today_orders_qs.filter(payment_status=Order.PaymentStatus.PAID)
        
        today_sales = today_paid_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        today_order_count = today_orders_qs.count()

        # All-time orders & revenue
        all_orders = Order.objects.all()
        paid_orders = all_orders.filter(payment_status=Order.PaymentStatus.PAID)
        total_revenue = paid_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_orders_count = all_orders.count()

        # Status breakdown
        completed_orders_count = all_orders.filter(
            status__in=[Order.Status.DELIVERED, Order.Status.CONFIRMED, Order.Status.READY, Order.Status.PREPARING],
            payment_status=Order.PaymentStatus.PAID
        ).count()
        pending_orders_count = all_orders.filter(
            status__in=[Order.Status.AWAITING_PAYMENT, Order.Status.AWAITING_APPROVAL, Order.Status.REQUESTED]
        ).count()
        cancelled_orders_count = all_orders.filter(
            status__in=[Order.Status.CANCELLED, Order.Status.REJECTED]
        ).count()

        # Average Order Value (AOV)
        aov = paid_orders.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00')

        # Product availability metrics
        active_products = Product.objects.filter(is_active=True)
        total_products = active_products.count()
        available_products = active_products.filter(availability_status='AVAILABLE').count()
        unavailable_products = active_products.filter(availability_status='UNAVAILABLE').count()
        low_stock_count = active_products.filter(current_stock__lte=F('minimum_stock'), current_stock__gt=0).count()
        out_of_stock_count = active_products.filter(current_stock=0).count()

        # User metrics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()

        # Support
        pending_support = PaymentSupportTicket.objects.filter(status=PaymentSupportTicket.Status.OPEN).count()

        # Breakdown by customer role
        customer_breakdown = paid_orders.values('customer_type').annotate(
            total_sales=Sum('total_amount'),
            count=Count('id')
        ).order_by('-count')

        return Response({
            "today_sales": float(today_sales),
            "today_orders": today_order_count,
            "total_revenue": float(total_revenue),
            "total_orders": total_orders_count,
            "completed_orders": completed_orders_count,
            "pending_orders": pending_orders_count,
            "cancelled_orders": cancelled_orders_count,
            "average_order_value": round(float(aov), 2),
            "total_products": total_products,
            "available_products": available_products,
            "unavailable_products": unavailable_products,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "total_users": total_users,
            "active_users": active_users,
            "pending_support_tickets": pending_support,
            "customer_breakdown": list(customer_breakdown),
        })


class ComprehensiveAnalyticsView(APIView):
    """
    Authoritative PostgreSQL Data Analytics with Date Range filtering.
    Calculates summary, daily trends, top selling foods, category performance,
    payment method distribution, order statuses, and peak hours.
    """
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        range_type = request.query_params.get('range', '7days')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        start_dt, end_dt, start_date, end_date = get_date_range_filter(
            range_type, start_date_str, end_date_str
        )

        orders_in_range = Order.objects.filter(created_at__range=(start_dt, end_dt))
        paid_orders = orders_in_range.filter(payment_status=Order.PaymentStatus.PAID)

        # Summary calculations
        total_revenue = paid_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_orders_count = orders_in_range.count()
        paid_orders_count = paid_orders.count()
        aov = paid_orders.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00')

        completed_count = orders_in_range.filter(
            status__in=[Order.Status.DELIVERED, Order.Status.CONFIRMED, Order.Status.READY, Order.Status.PREPARING],
            payment_status=Order.PaymentStatus.PAID
        ).count()
        pending_count = orders_in_range.filter(
            status__in=[Order.Status.AWAITING_PAYMENT, Order.Status.AWAITING_APPROVAL, Order.Status.REQUESTED]
        ).count()
        cancelled_count = orders_in_range.filter(
            status__in=[Order.Status.CANCELLED, Order.Status.REJECTED]
        ).count()

        # 1. Daily Orders & Revenue Trend
        daily_trends_raw = paid_orders.annotate(
            order_date=TruncDate('created_at')
        ).values('order_date').annotate(
            orders_count=Count('id'),
            revenue=Sum('total_amount')
        ).order_by('order_date')

        # Populate all days in range for continuous charts
        trend_map = {item['order_date']: item for item in daily_trends_raw}
        daily_trends = []
        curr_date = start_date
        while curr_date <= end_date:
            item = trend_map.get(curr_date)
            daily_trends.append({
                "date": curr_date.strftime("%d %b"),
                "full_date": curr_date.strftime("%Y-%m-%d"),
                "orders": item['orders_count'] if item else 0,
                "revenue": float(item['revenue']) if item else 0.0,
            })
            curr_date += timedelta(days=1)

        # 2. Top Selling Food Products (sorted by quantity sold)
        top_products = OrderItem.objects.filter(
            order__created_at__range=(start_dt, end_dt),
            order__payment_status=Order.PaymentStatus.PAID
        ).values(
            'product__id',
            'product_name',
            'product__category__name'
        ).annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum('total_price')
        ).order_by('-quantity_sold')[:15]

        top_selling_list = []
        for p in top_products:
            top_selling_list.append({
                "product_id": p['product__id'],
                "product_name": p['product_name'],
                "category_name": p['product__category__name'] or 'General',
                "quantity_sold": p['quantity_sold'] or 0,
                "revenue": float(p['revenue'] or 0.0),
            })

        # 3. Category Performance Breakdown
        category_perf = OrderItem.objects.filter(
            order__created_at__range=(start_dt, end_dt),
            order__payment_status=Order.PaymentStatus.PAID
        ).values(
            'product__category__name'
        ).annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum('total_price'),
            orders_count=Count('order', distinct=True)
        ).order_by('-revenue')

        category_list = []
        for c in category_perf:
            cat_name = c['product__category__name'] or 'Snacks & Beverages'
            cat_rev = float(c['revenue'] or 0.0)
            category_list.append({
                "category_name": cat_name,
                "quantity_sold": c['quantity_sold'] or 0,
                "revenue": cat_rev,
                "orders_count": c['orders_count'] or 0,
                "percentage": round((cat_rev / float(total_revenue) * 100) if total_revenue > 0 else 0, 1)
            })

        # 4. Payment Method Distribution
        payment_distribution = []
        # From Order Source / Payments
        cash_orders = paid_orders.filter(order_source=Order.OrderSource.POS)
        online_orders = paid_orders.filter(order_source=Order.OrderSource.MOBILE)
        
        cash_rev = cash_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        online_rev = online_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

        payment_distribution = [
            {
                "method": "Cash (Counter POS)",
                "orders_count": cash_orders.count(),
                "revenue": float(cash_rev),
                "percentage": round(float(cash_rev) / float(total_revenue) * 100 if total_revenue > 0 else 0, 1)
            },
            {
                "method": "Online / UPI (Mobile App)",
                "orders_count": online_orders.count(),
                "revenue": float(online_rev),
                "percentage": round(float(online_rev) / float(total_revenue) * 100 if total_revenue > 0 else 0, 1)
            }
        ]

        # 5. Order Status Breakdown
        status_counts = orders_in_range.values('status').annotate(
            count=Count('id')
        ).order_by('-count')

        order_statuses = []
        for st in status_counts:
            order_statuses.append({
                "status": st['status'],
                "count": st['count'],
                "percentage": round(st['count'] / total_orders_count * 100 if total_orders_count > 0 else 0, 1)
            })

        # 6. Peak Hours Distribution
        peak_hours_raw = paid_orders.annotate(
            hour=ExtractHour('created_at')
        ).values('hour').annotate(
            order_count=Count('id'),
            revenue=Sum('total_amount')
        ).order_by('hour')

        peak_hours_map = {item['hour']: item for item in peak_hours_raw}
        peak_hours = []
        for h in range(8, 18):  # 8 AM to 5 PM
            item = peak_hours_map.get(h)
            formatted_h = f"{12 if h == 12 else h % 12} {'AM' if h < 12 else 'PM'}"
            peak_hours.append({
                "hour": h,
                "label": formatted_h,
                "orders": item['order_count'] if item else 0,
                "revenue": float(item['revenue']) if item else 0.0
            })

        # 7. Customer Type Breakdown
        customer_breakdown = paid_orders.values('customer_type').annotate(
            total_sales=Sum('total_amount'),
            count=Count('id')
        ).order_by('-count')

        return Response({
            "date_range": {
                "range_type": range_type,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            },
            "summary": {
                "total_revenue": float(total_revenue),
                "total_orders": total_orders_count,
                "paid_orders": paid_orders_count,
                "average_order_value": round(float(aov), 2),
                "completed_orders": completed_count,
                "pending_orders": pending_count,
                "cancelled_orders": cancelled_count,
            },
            "daily_trends": daily_trends,
            "top_selling_products": top_selling_list,
            "category_performance": category_list,
            "payment_methods": payment_distribution,
            "order_statuses": order_statuses,
            "peak_hours": peak_hours,
            "customer_breakdown": list(customer_breakdown),
        })


class SalesAnalyticsView(APIView):
    """Authoritative sales breakdown view."""
    permission_classes = [IsAdminUserRole]

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
            "total_revenue": float(paid_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')),
            "total_orders": paid_orders.count(),
            "average_order_value": round(float(paid_orders.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00')), 2),
            "source_breakdown": list(source_breakdown),
            "customer_breakdown": list(customer_breakdown),
        })


class ProductPerformanceAnalyticsView(APIView):
    """Authoritative product sales breakdown view."""
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        top_products = OrderItem.objects.filter(order__payment_status=Order.PaymentStatus.PAID)\
            .values('product__id', 'product_name', 'product__category__name')\
            .annotate(total_quantity=Sum('quantity'), total_revenue=Sum('total_price'))\
            .order_by('-total_quantity')[:20]
            
        return Response({"top_products": list(top_products)})


class PeakHoursAnalyticsView(APIView):
    """Authoritative peak hours breakdown view."""
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        hourly_orders = Order.objects.filter(payment_status=Order.PaymentStatus.PAID)\
            .annotate(hour=ExtractHour('created_at'))\
            .values('hour')\
            .annotate(order_count=Count('id'), revenue=Sum('total_amount'))\
            .order_by('hour')
            
        return Response({"peak_hours": list(hourly_orders)})
