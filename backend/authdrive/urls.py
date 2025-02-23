# urls.py
from django.urls import path
from rest_framework.authtoken import views as auth_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    path('api/register/', views.RegisterView.as_view(), name='user-register'),
    path('api/verify-otp/', views.OTPVerificationView.as_view(), name='verify-otp'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/logout/', views.LogoutView.as_view(), name='logout'),
]
