from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import StudentProfile, FacultyProfile

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

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'mobile_number', 'role', 'is_active', 'created_at', 'student_profile', 'faculty_profile']

class StudentRegistrationSerializer(serializers.ModelSerializer):
    register_number = serializers.CharField(max_length=50)
    department = serializers.CharField(max_length=100)
    year = serializers.IntegerField(default=1)
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'mobile_number', 'password', 'register_number', 'department', 'year']

    def validate_register_number(self, value):
        if StudentProfile.objects.filter(register_number=value).exists():
            raise serializers.ValidationError("Student with this Register Number already exists.")
        return value

    def create(self, validated_data):
        reg_num = validated_data.pop('register_number')
        dept = validated_data.pop('department')
        yr = validated_data.pop('year', 1)
        password = validated_data.pop('password')
        
        validated_data['role'] = User.Role.STUDENT
        user = User.objects.create_user(password=password, **validated_data)
        StudentProfile.objects.create(user=user, register_number=reg_num, department=dept, year=yr)
        return user

    def to_representation(self, instance):
        return UserSerializer(instance).data

class FacultyRegistrationSerializer(serializers.ModelSerializer):
    staff_number = serializers.CharField(max_length=50)
    department = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'mobile_number', 'password', 'staff_number', 'department']

    def validate_staff_number(self, value):
        if FacultyProfile.objects.filter(staff_number=value).exists():
            raise serializers.ValidationError("Faculty with this Staff Number already exists.")
        return value

    def create(self, validated_data):
        staff_num = validated_data.pop('staff_number')
        dept = validated_data.pop('department')
        password = validated_data.pop('password')
        
        validated_data['role'] = User.Role.FACULTY
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
        user = User.objects.create_user(password=password, **validated_data)
        return user

    def to_representation(self, instance):
        return UserSerializer(instance).data


