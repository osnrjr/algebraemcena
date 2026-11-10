from django.contrib.auth.models import AbstractUser

from apps.core.models import UUIDModel


class User(UUIDModel, AbstractUser):
    """Usuário do sistema (professor, administrador, desenvolvedor) com PK UUID."""

    class Meta:
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'
