
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from core.validators import (
    validate_phone,
    validate_safe_email,
    validate_safe_text,
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _make(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")

        email = self.normalize_email(email.strip()).lower()

        user = self.model(
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        return self._make(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superutilisateur doit avoir is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superutilisateur doit avoir is_superuser=True.")

        return self._make(email, password, **extra_fields)


class User(AbstractUser):

    ROLES = [
        ("client", "Client"),
        ("artisan", "Soudeur"),
        ("admin", "Administrateur"),
    ]

    # Suppression des champs inutilisés d'AbstractUser
    username = None
    first_name = None
    last_name = None

    # Identité
    email = models.EmailField(
        "e-mail",
        unique=True,
        max_length=120,
        validators=[validate_safe_email],
    )

    full_name = models.CharField(
        "nom complet",
        max_length=80,
        validators=[validate_safe_text],
    )

    phone = models.CharField(
        "téléphone",
        max_length=12,
        blank=True,
        validators=[validate_phone],
    )

    role = models.CharField(
        max_length=10,
        choices=ROLES,
        default="client",
    )

    # Authentification
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def save(self, *args, **kwargs):
        self.email = (self.email or "").strip().lower()
        super().save(*args, **kwargs)

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return (
            self.full_name.split(" ")[0]
            if self.full_name
            else self.email
        )

    def __str__(self):
        return f"{self.full_name} <{self.email}>"
