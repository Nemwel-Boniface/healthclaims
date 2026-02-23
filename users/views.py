from django.shortcuts import render

from typing import Any
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from users.serializers import (
    LogoutSerializer,
    UserSerializer,
)

User = get_user_model()


class UserRegisterView(APIView):
    """
    Register a new user and return JWT tokens.
    """
    
    def post(self, request: Request, format: str = "json") -> Response:
        serializer = UserSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        response = serializer.data
        response["refresh"] = str(refresh)
        response["access"] = str(refresh.access_token)
        
        return Response(response, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Custom login view that returns user details along with tokens.
    """
    
    def post(self, request: Request) -> Response:
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=email, password=password)
        
        if user is None:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {"error": "User account is disabled"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        refresh = RefreshToken.for_user(user)
        
        response_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class LogoutView(GenericAPIView):
    """
    Logout user by blacklisting their refresh token.
    """
    serializer_class = LogoutSerializer
    permission_classes = (IsAuthenticated,)
    
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Logout successful"},
            status=status.HTTP_200_OK,
        )
