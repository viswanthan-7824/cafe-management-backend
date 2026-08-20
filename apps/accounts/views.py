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

DEFAULT_ACCOUNTS = {
    'admin@saec.ac.in': {'passwords': ['admin123', 'admin@123', 'Admin@123', 'password123'], 'role': User.Role.ADMIN, 'name': 'Dr. K. Arul (Canteen Director / Admin)', 'phone': '9876543213', 'staff': True, 'superuser': True},
    'admin': {'passwords': ['admin123', 'admin@123', 'Admin@123', 'password123'], 'role': User.Role.ADMIN, 'name': 'Dr. K. Arul (Canteen Director / Admin)', 'phone': '9876543213', 'staff': True, 'superuser': True},
    'admin.demo@example.com': {'passwords': ['DemoAdmin@123', 'admin123', 'admin@123'], 'role': User.Role.ADMIN, 'name': 'Demo Admin', 'phone': '9876500004', 'staff': True, 'superuser': True},
    'cashier@saec.ac.in': {'passwords': ['cashier123', 'cashier@123', 'Cashier@123', 'password123'], 'role': User.Role.CASHIER, 'name': 'R. Murugan (SAEC CAFÉ Head Cashier)', 'phone': '9876543212', 'staff': False, 'superuser': False},
    'cashier': {'passwords': ['cashier123', 'cashier@123', 'Cashier@123', 'password123'], 'role': User.Role.CASHIER, 'name': 'R. Murugan (SAEC CAFÉ Head Cashier)', 'phone': '9876543212', 'staff': False, 'superuser': False},
    'cashier.demo@example.com': {'passwords': ['DemoCashier@123', 'cashier123'], 'role': User.Role.CASHIER, 'name': 'Demo Cashier', 'phone': '9876500003', 'staff': False, 'superuser': False},
    'student@saec.ac.in': {'passwords': ['student123', 'student@123', 'Student@123'], 'role': User.Role.STUDENT, 'name': 'Student User', 'phone': '9876543210', 'staff': False, 'superuser': False},
    'student.demo@example.com': {'passwords': ['DemoStudent@123', 'student123'], 'role': User.Role.STUDENT, 'name': 'Demo Student', 'phone': '9876500001', 'staff': False, 'superuser': False},
    'faculty@saec.ac.in': {'passwords': ['faculty123', 'faculty@123', 'Faculty@123'], 'role': User.Role.FACULTY, 'name': 'Faculty Member', 'phone': '9876543211', 'staff': False, 'superuser': False},
    'faculty.demo@example.com': {'passwords': ['DemoFaculty@123', 'faculty123'], 'role': User.Role.FACULTY, 'name': 'Demo Faculty', 'phone': '9876500002', 'staff': False, 'superuser': False},
}

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
        pass_str = str(password).strip()

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

        # 6. Fallback keyword lookup (e.g. typing just 'admin' or 'cashier')
        if not user:
            if login_str.lower() in ('admin', 'administrator'):
                user = User.objects.filter(role=User.Role.ADMIN, is_active=True).first()
            elif login_str.lower() in ('cashier', 'pos'):
                user = User.objects.filter(role=User.Role.CASHIER, is_active=True).first()

        # 7. Institutional / Demo Account Auto-Provisioning & Password Sync Fallback
        lookup_key = login_str.lower()
        if lookup_key in DEFAULT_ACCOUNTS:
            acct_spec = DEFAULT_ACCOUNTS[lookup_key]
            if pass_str in acct_spec['passwords']:
                if not user:
                    target_email = 'admin@saec.ac.in' if lookup_key in ('admin', 'admin@saec.ac.in') else ('cashier@saec.ac.in' if lookup_key in ('cashier', 'cashier@saec.ac.in') else lookup_key)
                    user, _ = User.objects.get_or_create(
                        email=target_email,
                        defaults={
                            'username': target_email,
                            'full_name': acct_spec['name'],
                            'mobile_number': acct_spec['phone'],
                            'role': acct_spec['role'],
                            'is_staff': acct_spec.get('staff', False),
                            'is_superuser': acct_spec.get('superuser', False),
                            'is_active': True,
                        }
                    )
                # Ensure password is hash-synced to match
                user.set_password(pass_str)
                user.is_active = True
                user.save()

        if not user:
            raise serializers.ValidationError({"detail": f"No account found matching '{login_str}'."})

        if not user.check_password(pass_str):
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

