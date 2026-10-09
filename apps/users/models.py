import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User Model untuk mendukung RBAC dan fleksibilitas autentikasi.
    Memiliki UUID publik untuk URL profil/user dan role-based profiling.
    """
    class Role(models.TextChoices):
        SUPERADMIN = 'superadmin', 'Super Admin / Pengasuh'
        ADMIN_AKADEMIK = 'admin_akademik', 'Tata Usaha / Admin Akademik'
        BENDAHARA = 'bendahara', 'Bendahara / Kasir Keuangan'
        GURU = 'guru', 'Asatidz / Guru'
        WALI_SANTRI = 'wali_santri', 'Wali Santri'
        SANTRI = 'santri', 'Santri'

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN_AKADEMIK,
        verbose_name="Peran Pengguna"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Nomor WhatsApp/HP"
    )
    foto = models.ImageField(
        upload_to='users/foto/',
        blank=True,
        null=True,
        verbose_name="Foto Profil"
    )

    class Meta:
        verbose_name = "Pengguna"
        verbose_name_plural = "Daftar Pengguna"
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_bendahara(self):
        return self.role == self.Role.BENDAHARA or self.is_superuser

    @property
    def is_admin_akademik(self):
        return self.role == self.Role.ADMIN_AKADEMIK or self.is_superuser

    @property
    def is_guru(self):
        return self.role == self.Role.GURU

    @property
    def is_wali_santri(self):
        return self.role == self.Role.WALI_SANTRI
