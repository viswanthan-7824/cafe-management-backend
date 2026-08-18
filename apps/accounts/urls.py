from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    StudentRegisterView,
    FacultyRegisterView,
    UserProfileView
)

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/student/', StudentRegisterView.as_view(), name='register_student'),
    path('register/faculty/', FacultyRegisterView.as_view(), name='register_faculty'),
    path('profile/', UserProfileView.as_view(), name='profile'),
]
