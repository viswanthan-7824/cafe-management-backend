from django.urls import path
from .views import (
    DashboardOverviewAnalyticsView,
    SalesAnalyticsView,
    ProductPerformanceAnalyticsView,
    PeakHoursAnalyticsView
)

urlpatterns = [
    path('overview/', DashboardOverviewAnalyticsView.as_view(), name='analytics_overview'),
    path('sales/', SalesAnalyticsView.as_view(), name='analytics_sales'),
    path('products/', ProductPerformanceAnalyticsView.as_view(), name='analytics_products'),
    path('peak-hours/', PeakHoursAnalyticsView.as_view(), name='analytics_peak_hours'),
]
