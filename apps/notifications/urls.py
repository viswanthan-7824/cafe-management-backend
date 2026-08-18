from django.urls import path
from .views import NotificationListView, AuditLogListView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('audit-logs/', AuditLogListView.as_view(), name='audit_logs'),
]
