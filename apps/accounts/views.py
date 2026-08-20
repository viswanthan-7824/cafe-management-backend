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

from rest_framework import serializers
from .models import StudentProfile, FacultyProfile

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.username_field in self.fields:
            self.fields[self.username_field].required = False
        self.fields['username'] = serializers.CharField(required=False, allow_blank=True)
        self.fields['email'] = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        login_identifier = attrs.get('email') or attrs.get('username') or attrs.get('login') or self.initial_data.get('email') or self.initial_data.get('username')
        password = attrs.get('password') or self.initial_data.get('password')

        if not login_identifier:
            raise serializers.ValidationError({"detail": "Please provide an Email or User ID."})
        if not password:
            raise serializers.ValidationError({"detail": "Please provide a Password."})

        login_str = str(login_identifier).strip()

        # Look up user across multiple institutional identifiers
        user = None

        # 1. Exact or case-insensitive email match
        user = User.objects.filter(email__iexact=login_str).first()

        # 2. Username match
        if not user:
            user = User.objects.filter(username__iexact=login_str).first()

        # 3. Mobile number match
        if not user:
            user = User.objects.filter(mobile_number=login_str).first()

        # 4. Student register number
        if not user:
            sp = StudentProfile.objects.filter(register_number__iexact=login_str).first()
            if sp:
                user = sp.user

        # 5. Faculty staff number
        if not user:
            fp = FacultyProfile.objects.filter(staff_number__iexact=login_str).first()
            if fp:
                user = fp.user

        # Fallback keyword match for quick testing (e.g., typing just 'admin' or 'cashier')
        if not user:
            if login_str.lower() in ('admin', 'administrator'):
                user = User.objects.filter(role=User.Role.ADMIN, is_active=True).first()
            elif login_str.lower() in ('cashier', 'pos'):
                user = User.objects.filter(role=User.Role.CASHIER, is_active=True).first()

        if not user:
            raise serializers.ValidationError({"detail": f"No account found matching '{login_str}'."})

        if not user.check_password(password):
            raise serializers.ValidationError({"detail": "Invalid password. Please check your credentials."})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "This account has been deactivated. Please contact the administrator."})

        self.user = user
        refresh = self.get_token(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data
        }

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

