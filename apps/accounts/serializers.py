from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import StudentProfile, FacultyProfile, PasswordResetToken

User = get_user_model()

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ['register_number', 'department', 'year']

class FacultyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacultyProfile
        fields = ['staff_number', 'department']

class UserSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=True)
    faculty_profile = FacultyProfileSerializer(read_only=True)
    activated_by_name = serializers.CharField(source='activated_by.full_name', read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'mobile_number', 'role',
            'status', 'must_change_password', 'is_active', 'is_demo',
            'created_at', 'activated_at', 'activated_by', 'activated_by_name',
            'rejection_reason', 'student_profile', 'faculty_profile'
        ]

class StudentRegistrationSerializer(serializers.ModelSerializer):
    register_number = serializers.CharField(max_length=50)
    department = serializers.CharField(max_length=100)
    year = serializers.IntegerField(default=1)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, default='')

    class Meta:
        model = User
        fields = ['email', 'full_name', 'mobile_number', 'password', 'register_number', 'department', 'year']

    def validate_register_number(self, value):
        if StudentProfile.objects.filter(register_number__iexact=value.strip()).exists():
            raise serializers.ValidationError("A student with this Register Number is already registered.")
        return value.strip()

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value.strip()).exists():
            raise serializers.ValidationError("An account with this email address already exists.")
        return value.strip().lower()

    def validate_mobile_number(self, value):
        if User.objects.filter(mobile_number=value.strip()).exists():
            raise serializers.ValidationError("An account with this mobile number already exists.")
        return value.strip()

    def create(self, validated_data):
        reg_num = validated_data.pop('register_number')
        dept = validated_data.pop('department')
        yr = validated_data.pop('year', 1)
        password = validated_data.pop('password', '') or 'PendingApproval@2026'

        validated_data['role'] = User.Role.STUDENT
        validated_data['status'] = User.Status.PENDING
        user = User.objects.create_user(password=password, **validated_data)
        StudentProfile.objects.create(user=user, register_number=reg_num, department=dept, year=yr)
        return user

    def to_representation(self, instance):
        return UserSerializer(instance).data

class FacultyRegistrationSerializer(serializers.ModelSerializer):
    staff_number = serializers.CharField(max_length=50)
    department = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, default='')

    class Meta:
        model = User
        fields = ['email', 'full_name', 'mobile_number', 'password', 'staff_number', 'department']

    def validate_staff_number(self, value):
        if FacultyProfile.objects.filter(staff_number__iexact=value.strip()).exists():
            raise serializers.ValidationError("A faculty member with this Staff Number is already registered.")
        return value.strip()

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value.strip()).exists():
            raise serializers.ValidationError("An account with this email address already exists.")
        return value.strip().lower()

    def validate_mobile_number(self, value):
        if User.objects.filter(mobile_number=value.strip()).exists():
            raise serializers.ValidationError("An account with this mobile number already exists.")
        return value.strip()

    def create(self, validated_data):
        staff_num = validated_data.pop('staff_number')
        dept = validated_data.pop('department')
        password = validated_data.pop('password', '') or 'PendingApproval@2026'

        validated_data['role'] = User.Role.FACULTY
        validated_data['status'] = User.Status.PENDING
        user = User.objects.create_user(password=password, **validated_data)
        FacultyProfile.objects.create(user=user, staff_number=staff_num, department=dept)
        return user

    def to_representation(self, instance):
        return UserSerializer(instance).data

class CashierRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'mobile_number', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data['role'] = User.Role.CASHIER
        validated_data['status'] = User.Status.ACTIVE
        user = User.objects.create_user(password=password, **validated_data)
        return user

    def to_representation(self, instance):
        return UserSerializer(instance).data

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New passwords do not match."})
        return data

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New passwords do not match."})
        return data

class UserActivateSerializer(serializers.Serializer):
    temporary_password = serializers.CharField(required=False, allow_blank=True, default='')

class UserRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default='')
