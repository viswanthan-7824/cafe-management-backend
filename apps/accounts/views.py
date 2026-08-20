from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.db import models
from .permissions import IsAdminUserRole
from .serializers import (
    UserSerializer,
    StudentRegistrationSerializer,
    FacultyRegistrationSerializer,
    CashierRegistrationSerializer
)

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class StudentRegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = StudentRegistrationSerializer

class FacultyRegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = FacultyRegistrationSerializer

class CashierRegisterView(generics.CreateAPIView):
    permission_classes = [IsAdminUserRole]
    serializer_class = CashierRegistrationSerializer

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class UserManagementListView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        role_filter = request.query_params.get('role')
        search_query = request.query_params.get('search')
        
        queryset = User.objects.all().order_by('-created_at')
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        if search_query:
            queryset = queryset.filter(
                models.Q(email__icontains=search_query) |
                models.Q(full_name__icontains=search_query) |
                models.Q(mobile_number__icontains=search_query)
            )
        serializer = UserSerializer(queryset[:200], many=True)
        return Response(serializer.data)

class UserToggleStatusView(APIView):
    permission_classes = [IsAdminUserRole]

    def patch(self, request, pk):
        try:
            target_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if target_user.id == request.user.id:
            return Response({"error": "Cannot deactivate your own administrator account"}, status=status.HTTP_400_BAD_REQUEST)
        
        target_user.is_active = not target_user.is_active
        target_user.save()
        return Response(UserSerializer(target_user).data)

