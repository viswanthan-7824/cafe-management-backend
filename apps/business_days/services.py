from datetime import datetime, date, time
from django.utils import timezone
from django.db import transaction
from .models import BusinessDay

def get_current_business_day(target_date=None):
    """Retrieves business day configuration for a given date (defaults to today in Asia/Kolkata)."""
    if target_date is None:
        target_date = timezone.localdate()
    try:
        return BusinessDay.objects.get(date=target_date)
    except BusinessDay.DoesNotExist:
        return None

def check_ordering_available(now=None):
    """
    Validates whether ordering is currently open based on admin calendar & server clock (10:00 AM - 3:30 PM).
    Returns (is_open: bool, message: str, business_day: BusinessDay or None)
    """
    if now is None:
        now = timezone.localtime()
    
    today_date = now.date()
    current_time = now.time()
    
    b_day = get_current_business_day(today_date)
    
    if not b_day:
        return False, "Ordering has not been scheduled for today by the canteen administration.", None
        
    if b_day.status == BusinessDay.Status.HOLIDAY:
        reason = b_day.reason or "College Holiday"
        return False, f"Today is a holiday ({reason}). Ordering is unavailable.", b_day
        
    if b_day.status == BusinessDay.Status.CLOSED:
        reason = b_day.reason or "Maintenance / Emergency Closure"
        return False, f"🔴 CANTEEN CLOSED\nReason: {reason}. Ordering is unavailable today.", b_day

    if not b_day.is_ordering_enabled:
        return False, "🔴 CANTEEN CLOSED\nOrdering is currently disabled by admin.", b_day
        
    if b_day.status in [BusinessDay.Status.WORKING_DAY, BusinessDay.Status.SPECIAL_WORKING_DAY]:
        if current_time < b_day.opening_time:
            return False, "🔒 ORDERING CLOSED\nOrdering starts at 10:00 AM.", b_day
            
        if current_time >= b_day.closing_time:
            return False, "🔴 ORDERING CLOSED\nToday's ordering has ended. Ordering will reopen on the next working day.", b_day
            
        return True, "🟢 ORDERING OPEN (10:00 AM – 3:30 PM)", b_day

    return False, "Ordering is currently unavailable.", b_day

@transaction.atomic
def generate_next_daily_order_number(target_date=None):
    """
    Generates the next order code atomically in format CAN-XXXX (e.g., CAN-4821, CAN-4822).
    """
    if target_date is None:
        target_date = timezone.localdate()
        
    b_day, created = BusinessDay.objects.select_for_update().get_or_create(
        date=target_date,
        defaults={
            'status': BusinessDay.Status.WORKING_DAY,
            'opening_time': time(10, 0),
            'closing_time': time(15, 30),
            'is_ordering_enabled': True,
            'daily_order_sequence': 4820,
        }
    )
    
    if b_day.daily_order_sequence < 4800:
        b_day.daily_order_sequence = 4820

    b_day.daily_order_sequence += 1
    b_day.save()
    
    seq_str = f"CAN-{b_day.daily_order_sequence}"
    return seq_str, b_day
