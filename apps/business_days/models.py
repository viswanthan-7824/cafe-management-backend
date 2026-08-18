from django.db import models
from django.conf import settings
from datetime import time

class BusinessDay(models.Model):
    class Status(models.TextChoices):
        WORKING_DAY = 'WORKING_DAY', 'Normal Working Day'
        HOLIDAY = 'HOLIDAY', 'Holiday (Closed)'
        CLOSED = 'CLOSED', 'Canteen Closed (Maintenance/Event)'
        SPECIAL_WORKING_DAY = 'SPECIAL_WORKING_DAY', 'Special Working Day'

    date = models.DateField(unique=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.WORKING_DAY)
    opening_time = models.TimeField(default=time(10, 0))
    closing_time = models.TimeField(default=time(15, 30))
    reason = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_ordering_enabled = models.BooleanField(default=True)
    daily_order_sequence = models.PositiveIntegerField(default=4820)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"BusinessDay {self.date} [{self.status}] ({self.opening_time.strftime('%H:%M')} - {self.closing_time.strftime('%H:%M')})"
