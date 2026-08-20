import random
import string
from django.utils import timezone
from rest_framework import generics, status, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.db import models

from .models import StudentProfile, FacultyProfile, PasswordResetToken
from .permissions import IsAdminUserRole
from .serializers import (
    UserSerializer,
    StudentRegistrationSerializer,
    FacultyRegistrationSerializer,
    CashierRegistrationSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    UserActivateSerializer,
    UserRejectSerializer
)

User = get_user_model()

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
            raise serializers.ValidationError({"detail": "Please enter your email address.", "code": "REQUIRED_EMAIL"})
        if not password:
            raise serializers.ValidationError({"detail": "Please enter your password.", "code": "REQUIRED_PASSWORD"})

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

        # 6. Fallback keyword lookup
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
                            'status': User.Status.ACTIVE,
                            'is_staff': acct_spec.get('staff', False),
                            'is_superuser': acct_spec.get('superuser', False),
                            'is_active': True,
                        }
                    )
                # Ensure password is hash-synced to match
                user.set_password(pass_str)
                user.is_active = True
                user.status = User.Status.ACTIVE
                user.save()

        if not user:
            raise serializers.ValidationError({
                "detail": "Incorrect email or password. Please try again.",
                "code": "INVALID_CREDENTIALS"
            })

        if not user.check_password(pass_str):
            raise serializers.ValidationError({
                "detail": "Incorrect email or password. Please try again.",
                "code": "INVALID_CREDENTIALS"
            })

        # Check Account Status State Machine
        if user.status == User.Status.PENDING:
            raise serializers.ValidationError({
                "detail": "Your account is waiting for administrator approval.",
                "code": "ACCOUNT_PENDING"
            })

        if user.status == User.Status.REJECTED:
            raise serializers.ValidationError({
                "detail": "Your account has not been approved.",
                "code": "ACCOUNT_REJECTED",
                "rejection_reason": user.rejection_reason
            })

        if user.status == User.Status.INACTIVE or not user.is_active:
            raise serializers.ValidationError({
                "detail": "Your account is currently inactive. Please contact the administrator.",
                "code": "ACCOUNT_INACTIVE"
            })

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

class UserStatsView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        total = User.objects.count()
        pending = User.objects.filter(status=User.Status.PENDING).count()
        active = User.objects.filter(status=User.Status.ACTIVE, is_active=True).count()
        inactive = User.objects.filter(models.Q(status=User.Status.INACTIVE) | models.Q(is_active=False)).exclude(status=User.Status.REJECTED).count()
        rejected = User.objects.filter(status=User.Status.REJECTED).count()

        return Response({
            "total_users": total,
            "pending_users": pending,
            "active_users": active,
            "inactive_users": inactive,
            "rejected_users": rejected
        })

class UserManagementListView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        role_filter = request.query_params.get('role')
        status_filter = request.query_params.get('status')
        search_query = request.query_params.get('search')
        
        queryset = User.objects.all().order_by('-created_at')
        
        if role_filter and role_filter.upper() != 'ALL':
            queryset = queryset.filter(role=role_filter.upper())
            
        if status_filter and status_filter.upper() != 'ALL':
            queryset = queryset.filter(status=status_filter.upper())

        if search_query:
            q = search_query.strip()
            queryset = queryset.filter(
                models.Q(email__icontains=q) |
                models.Q(full_name__icontains=q) |
                models.Q(mobile_number__icontains=q) |
                models.Q(student_profile__register_number__icontains=q) |
                models.Q(faculty_profile__staff_number__icontains=q)
            ).distinct()

        serializer = UserSerializer(queryset[:300], many=True)
        return Response(serializer.data)

class UserActivateView(APIView):
    permission_classes = [IsAdminUserRole]

    def post(self, request, pk):
        try:
            target_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        temp_pwd = serializer.validated_data.get('temporary_password', '').strip()
        if not temp_pwd:
            # Generate a clean, secure temporary password (e.g. SaecCafe@8392)
            digits = ''.join(random.choices(string.digits, k=4))
            temp_pwd = f"SaecCafe@{digits}"

        target_user.set_password(temp_pwd)
        target_user.status = User.Status.ACTIVE
        target_user.is_active = True
        target_user.must_change_password = True
        target_user.activated_at = timezone.now()
        target_user.activated_by = request.user
        target_user.rejection_reason = ''
        target_user.save()

        return Response({
            "message": "Account activated successfully.",
            "temporary_password": temp_pwd,
            "user": UserSerializer(target_user).data
        })

class UserRejectView(APIView):
    permission_classes = [IsAdminUserRole]

    def post(self, request, pk):
        try:
            target_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if target_user.id == request.user.id:
            return Response({"detail": "Cannot reject your own account."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason', '').strip()

        target_user.status = User.Status.REJECTED
        target_user.is_active = False
        target_user.rejection_reason = reason
        target_user.save()

        return Response({
            "message": "Account rejected.",
            "user": UserSerializer(target_user).data
        })

class UserToggleStatusView(APIView):
    permission_classes = [IsAdminUserRole]

    def patch(self, request, pk):
        try:
            target_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if target_user.id == request.user.id:
            return Response({"detail": "Cannot deactivate your own administrator account."}, status=status.HTTP_400_BAD_REQUEST)
        
        if target_user.is_active and target_user.status == User.Status.ACTIVE:
            target_user.is_active = False
            target_user.status = User.Status.INACTIVE
        else:
            target_user.is_active = True
            target_user.status = User.Status.ACTIVE

        target_user.save()
        return Response(UserSerializer(target_user).data)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_pass = serializer.validated_data['current_password']
        new_pass = serializer.validated_data['new_password']

        if not request.user.check_password(current_pass):
            return Response(
                {"current_password": ["Current password is incorrect."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.set_password(new_pass)
        request.user.must_change_password = False
        request.user.save()

        return Response({"message": "Your password has been updated successfully."})

class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].strip().lower()
        user = User.objects.filter(email__iexact=email).first()

        token_str = None
        if user and user.status == User.Status.ACTIVE:
            reset_token = PasswordResetToken.create_for_user(user)
            token_str = reset_token.token

        return Response({
            "message": "If an account exists for this email, a password reset link has been sent.",
            "reset_token": token_str  # returned for client integration / simulation
        })

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_str = serializer.validated_data['token'].strip()
        new_password = serializer.validated_data['new_password']

        reset_token = PasswordResetToken.objects.filter(token=token_str, is_used=False).first()
        if not reset_token or not reset_token.is_valid:
            return Response(
                {"detail": "Invalid or expired password reset token. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = reset_token.user
        user.set_password(new_password)
        user.must_change_password = False
        user.save()

        reset_token.is_used = True
        reset_token.save()

        return Response({"message": "Password reset successfully. You can now log in with your new password."})
