from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import BusinessDay
from .serializers import BusinessDaySerializer
from .services import check_ordering_available, get_current_business_day

class CurrentBusinessDayStatusView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        now = timezone.localtime()
        is_open, message, b_day = check_ordering_available(now)
        
        response_data = {
            "date": now.date().isoformat(),
            "time": now.time().strftime("%H:%M:%S"),
            "is_ordering_open": is_open,
            "message": message,
            "status": b_day.status if b_day else "NOT_SCHEDULED",
            "opening_time": b_day.opening_time.strftime("%H:%M") if b_day else "10:00",
            "closing_time": b_day.closing_time.strftime("%H:%M") if b_day else "15:30",
            "reason": b_day.reason if b_day else None,
            "daily_order_sequence": b_day.daily_order_sequence if b_day else 0,
        }
        return Response(response_data)

class AdminBusinessDayCalendarView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = BusinessDay.objects.all().order_by('-date')
    serializer_class = BusinessDaySerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class AdminBusinessDayDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = BusinessDay.objects.all()
    serializer_class = BusinessDaySerializer

class BulkBusinessDayScheduleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        dates = request.data.get('dates', [])
        status_choice = request.data.get('status', BusinessDay.Status.WORKING_DAY)
        opening_time = request.data.get('opening_time', '10:00')
        closing_time = request.data.get('closing_time', '15:30')
        reason = request.data.get('reason', '')

        updated_count = 0
        for d in dates:
            obj, created = BusinessDay.objects.update_or_create(
                date=d,
                defaults={
                    'status': status_choice,
                    'opening_time': opening_time,
                    'closing_time': closing_time,
                    'reason': reason,
                    'created_by': request.user
                }
            )
            updated_count += 1

        return Response({"message": f"Successfully updated {updated_count} calendar dates."}, status=status.HTTP_200_OK)
