from typing import Any
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    username = serializers.CharField(
        max_length=150,
        min_length=3,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
    )
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    is_staff = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "is_staff",
            "is_active",
        )
        read_only_fields = ("id", "created_at", "is_staff")
    
    def create(self, validated_data: Any) -> Any:
        
        user = User.objects.create_user(**validated_data)              
        
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class LoginResponseSerializer(serializers.ModelSerializer):
    refresh = serializers.CharField()
    access = serializers.CharField()
    
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "refresh",
            "access",
        )
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    
    def validate(self, attrs):
        self.token = attrs["refresh"]
        return attrs
    
    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            raise serializers.ValidationError(
                "Invalid or expired token", code="invalid_token"
            )
        