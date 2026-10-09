import uuid
from django.db import models


class BaseModel(models.Model):
    """
    Base model abstrak untuk seluruh entitas di SIAKAD Pondok.
    - id: Primary Key internal (BIGINT) untuk performa relasi Foreign Key di MySQL InnoDB.
    - uuid: Unique identifier publik (UUID v4) untuk parameter URL dan endpoint REST API.
    - created_at: Timestamp pembuatan data.
    - updated_at: Timestamp update terakhir data.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat Pada")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Diperbarui Pada")

    class Meta:
        abstract = True
