from django.urls import path
from .views import (
    CurrentBusinessDayStatusView,
    AdminBusinessDayCalendarView,
    AdminBusinessDayDetailView,
    BulkBusinessDayScheduleView
)

urlpatterns = [
    path('current/', CurrentBusinessDayStatusView.as_view(), name='business_day_current'),
    path('calendar/', AdminBusinessDayCalendarView.as_view(), name='business_day_calendar'),
    path('calendar/<int:pk>/', AdminBusinessDayDetailView.as_view(), name='business_day_detail'),
    path('calendar/bulk/', BulkBusinessDayScheduleView.as_view(), name='business_day_bulk'),
]
