from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    StudentRegisterView,
    FacultyRegisterView,
    CashierRegisterView,
    UserProfileView,
    UserStatsView,
    UserManagementListView,
    UserToggleStatusView,
    UserActivateView,
    UserRejectView,
    ChangePasswordView,
    PasswordResetRequestView,
    PasswordResetConfirmView
)

urlpatterns = [
    # Authentication & JWT
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Self-Registration (Pending Admin Approval)
    path('register/student/', StudentRegisterView.as_view(), name='register_student'),
    path('register/faculty/', FacultyRegisterView.as_view(), name='register_faculty'),
    path('register/cashier/', CashierRegisterView.as_view(), name='register_cashier'),
    
    # Profile & Password Operations
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Admin User Management & Lifecycle
    path('users/stats/', UserStatsView.as_view(), name='users_stats'),
    path('users/', UserManagementListView.as_view(), name='users_list'),
    path('users/<int:pk>/status/', UserToggleStatusView.as_view(), name='user_toggle_status'),
    path('users/<int:pk>/activate/', UserActivateView.as_view(), name='user_activate'),
    path('users/<int:pk>/reject/', UserRejectView.as_view(), name='user_reject'),
]
