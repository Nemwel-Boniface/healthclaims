"""
URL configuration for the healthclaims project.
All API endpoints are versioned under /api/v1/ for future-proofing.
"""
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

# User Authentication Views
from users.views import (
    LoginView,
    LogoutView,
    UserRegisterView,
)

# Claims Domain Views
from claims.views import (
    ClaimCreateView, 
    ClaimDetailView
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication Endpoints for Hospital staff 
    path("api/v1/auth/register/", UserRegisterView.as_view(), name="user-register"),
    path("api/v1/auth/login/", LoginView.as_view(), name="user-login"), 
    path("api/v1/auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/v1/auth/logout/", LogoutView.as_view(), name="user-logout"),

    # This is our Claims Engine Endpoints
    # POST /api/v1/claims/ - Submit a new claim
    path("api/v1/claims/", ClaimCreateView.as_view(), name="claim-create"),
    
    # GET /api/v1/claims/{id}/ - Retrieve specific claim details
    path("api/v1/claims/<uuid:id>/", ClaimDetailView.as_view(), name="claim-detail"),
]