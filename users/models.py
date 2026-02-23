from django.db import models
import uuid
from typing import Any, Literal
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.utils.translation import gettext_lazy as _
from app.abstracts import TimeStampedModel


class UserManager(BaseUserManager):
    use_in_migrations: Literal[True]
    
    def _create_user(
        self, username: str, email: str, password: str, **kwargs: Any
    ) -> Any:
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError("The given username must be set")
        if not email:
            raise ValueError("The given email must be set")
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **kwargs)
        user.set_password(password)
        user.save()
        return user
    
    def create_user(
        self, username: str, email: str, password: str, **kwargs: Any
    ) -> Any:
        kwargs.setdefault("is_staff", False)
        kwargs.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **kwargs)
    
    def create_superuser(
        self, username: str, email: str, password: str, **kwargs: Any
    ) -> Any:
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)
        
        if not password:
            raise ValueError("Password is required")
        if kwargs.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if kwargs.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        
        return self._create_user(username, email, password, **kwargs)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
   
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        max_length=255,
    )
    
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
    )
    email = models.EmailField(
        unique=True,
    )
    first_name = models.CharField(
        _("first name"),
        max_length=150,
        blank=True,
    )
    last_name = models.CharField(
        _("last name"),
        max_length=150,
        blank=True,
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=True,
        help_text=_(
            "Designates whether the user can log into this admin site."
        ),
    )
    
    objects = UserManager()
    
    REQUIRED_FIELDS = ["username", "password"]
    USERNAME_FIELD = "email"
    
    class Meta:
        db_table = "users"
        ordering = ['username'] 
    
    def __str__(self) -> str:
        return self.username
    