from django.urls import path
from .views import (
    DashboardOverviewAnalyticsView,
    ComprehensiveAnalyticsView,
    SalesAnalyticsView,
    ProductPerformanceAnalyticsView,
    PeakHoursAnalyticsView
)

urlpatterns = [
    path('overview/', DashboardOverviewAnalyticsView.as_view(), name='analytics_overview'),
    path('dashboard/', ComprehensiveAnalyticsView.as_view(), name='analytics_dashboard'),
    path('sales/', SalesAnalyticsView.as_view(), name='analytics_sales'),
    path('products/', ProductPerformanceAnalyticsView.as_view(), name='analytics_products'),
    path('peak-hours/', PeakHoursAnalyticsView.as_view(), name='analytics_peak_hours'),
]
