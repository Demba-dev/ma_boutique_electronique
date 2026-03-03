from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

# Manager personnalisé
class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, email=None, password=None, **extra_fields):
        """
        Crée un utilisateur normal.
        """
        if not username:
            raise ValueError('Le username est obligatoire')
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """
        Crée un superuser et force role='admin'.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')  # <- important !

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser doit avoir is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


# Modèle utilisateur personnalisé
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('manager', 'Gestionnaire'),
        ('seller', 'Vendeur'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='seller'
    )

    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()  # <- important pour utiliser notre manager

    def __str__(self):
        return f"{self.username} ({self.role})"