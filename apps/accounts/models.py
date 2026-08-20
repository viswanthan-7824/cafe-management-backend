from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        return self.create_user(email, password, **extra_fields)

import uuid
from datetime import timedelta
from django.utils import timezone

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        CASHIER = 'CASHIER', 'Canteen Cashier'
        STUDENT = 'STUDENT', 'Student'
        FACULTY = 'FACULTY', 'Faculty / Staff'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        REJECTED = 'REJECTED', 'Rejected'

    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    must_change_password = models.BooleanField(default=False)
    activated_at = models.DateTimeField(null=True, blank=True)
    activated_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='activated_users'
    )
    rejection_reason = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    is_demo = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'mobile_number']

    objects = UserManager()

    def __str__(self):
        return f"{self.full_name} ({self.role}) - {self.email} [{self.status}]"

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    register_number = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    year = models.IntegerField(default=1)

    def __str__(self):
        return f"Student: {self.register_number} - {self.user.full_name}"

class FacultyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty_profile')
    staff_number = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)

    def __str__(self):
        return f"Faculty: {self.staff_number} - {self.user.full_name}"

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @classmethod
    def create_for_user(cls, user, expires_in_minutes=30):
        token_str = uuid.uuid4().hex
        expires = timezone.now() + timedelta(minutes=expires_in_minutes)
        return cls.objects.create(user=user, token=token_str, expires_at=expires)

    @property
    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at

    def __str__(self):
        return f"Reset token for {self.user.email} (used={self.is_used})"
