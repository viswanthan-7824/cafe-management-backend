from django.contrib import admin
from .models import BusinessDay

@admin.register(BusinessDay)
class BusinessDayAdmin(admin.ModelAdmin):
    list_display = ('date', 'status', 'opening_time', 'closing_time', 'reason')
    list_filter = ('status',)
    search_fields = ('date', 'reason')
