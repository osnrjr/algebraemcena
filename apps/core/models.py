import uuid

from django.db import models


class UUIDModel(models.Model):
    """Modelo-base com chave primária UUIDv4 (Doc ① §10.4)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
