import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.santri.models import Santri, TahunAjaran, Semester


class PosTarif(BaseModel):
    """
    Pos Pembayaran / Kategori Tagihan (misal: SPP Bulanan, Uang Gedung, Seragam).
    """
    class TipeTagihan(models.TextChoices):
        RUTIN = 'rutin', 'Rutin (Bulanan)'
        NON_RUTIN = 'non_rutin', 'Non-Rutin (Bebas / Sekali Bayar)'

    kode = models.CharField(max_length=20, unique=True, verbose_name="Kode Pos")
    nama = models.CharField(max_length=100, verbose_name="Nama Pos Pembayaran")
    tipe = models.CharField(max_length=15, choices=TipeTagihan.choices, default=TipeTagihan.RUTIN, verbose_name="Tipe Tagihan")
    tarif_standar = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Tarif Standar (Rp)")
    is_active = models.BooleanField(default=True, verbose_name="Status Aktif")
    keterangan = models.TextField(blank=True, verbose_name="Keterangan")

    class Meta:
        verbose_name = "Pos Tarif"
        verbose_name_plural = "Daftar Pos Tarif"
        ordering = ['tipe', 'nama']

    def __str__(self):
        return f"[{self.kode}] {self.nama} ({self.get_tipe_display()})"


class TarifKhususSantri(BaseModel):
    """
    Penyesuaian Tarif Khusus / Beasiswa per santri (anak yatim, anak asatidz, dsb).
    """
    santri = models.ForeignKey(Santri, on_delete=models.CASCADE, related_name='tarif_khusus_list', verbose_name="Santri")
    pos_tarif = models.ForeignKey(PosTarif, on_delete=models.PROTECT, related_name='tarif_khusus_santri', verbose_name="Pos Tarif")
    tahun_ajaran = models.ForeignKey(TahunAjaran, on_delete=models.PROTECT, verbose_name="Tahun Ajaran")
    nominal_tarif = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Nominal Khusus (Rp)")
    keterangan = models.CharField(max_length=200, blank=True, verbose_name="Alasan / Jenis Beasiswa")

    class Meta:
        verbose_name = "Tarif Khusus Santri"
        verbose_name_plural = "Daftar Tarif Khusus Santri"
        constraints = [
            models.UniqueConstraint(fields=['santri', 'pos_tarif', 'tahun_ajaran'], name='unique_tarif_khusus_santri_per_pos')
        ]

    def __str__(self):
        return f"{self.santri.nama_lengkap} - {self.pos_tarif.nama}: Rp {self.nominal_tarif:,.0f}"


class Tagihan(BaseModel):
    """
    Tagihan Santri (Baik Tagihan Rutin Bulanan maupun Non-Rutin / Bebas).
    """
    class Status(models.TextChoices):
        BELUM_BAYAR = 'belum_bayar', 'Belum Bayar'
        SEBAGIAN = 'sebagian', 'Sebagian / Dicicil'
        LUNAS = 'lunas', 'Lunas'
        BATAL = 'batal', 'Dibatalkan'

    nomor_invoice = models.CharField(max_length=40, unique=True, db_index=True, verbose_name="Nomor Invoice")
    santri = models.ForeignKey(Santri, on_delete=models.PROTECT, related_name='tagihan_list', verbose_name="Santri")
    pos_tarif = models.ForeignKey(PosTarif, on_delete=models.PROTECT, related_name='tagihan_pos_list', verbose_name="Pos Pembayaran")
    tahun_ajaran = models.ForeignKey(TahunAjaran, on_delete=models.PROTECT, verbose_name="Tahun Ajaran")
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Semester")

    # Untuk tagihan rutin bulanan (bulan 1 = Januari, 12 = Desember)
    bulan = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Bulan Tagihan")
    tahun = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Tahun Kalender")

    # Nilai Finansial
    nominal_awal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Nominal Asli (Rp)")
    diskon = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Potongan / Beasiswa (Rp)")
    total_tagihan = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Total Wajib Bayar (Rp)")
    total_terbayar = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Total Terbayar (Rp)")
    sisa_tagihan = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Sisa Tagihan (Rp)")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.BELUM_BAYAR, db_index=True, verbose_name="Status Tagihan")
    tanggal_jatuh_tempo = models.DateField(null=True, blank=True, verbose_name="Jatuh Tempo")
    keterangan = models.TextField(blank=True, verbose_name="Keterangan Tagihan")

    class Meta:
        verbose_name = "Tagihan Santri"
        verbose_name_plural = "Daftar Tagihan Santri"
        constraints = [
            # Mencegah anomali sisa tagihan negatif di level storage engine
            models.CheckConstraint(
                condition=models.Q(sisa_tagihan__gte=0),
                name='sisa_tagihan_tidak_boleh_negatif'
            ),
            # Mencegah pembuatan invoice SPP dobel untuk santri di bulan & tahun yang sama
            models.UniqueConstraint(
                fields=['santri', 'pos_tarif', 'bulan', 'tahun'],
                condition=models.Q(bulan__isnull=False, tahun__isnull=False),
                name='unique_tagihan_rutin_santri'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nomor_invoice} - {self.santri.nama_lengkap} ({self.pos_tarif.nama})"

    def save(self, *args, **kwargs):
        # Otomatis kalkulasi total_tagihan dan sisa_tagihan
        if not self.total_tagihan:
            self.total_tagihan = self.nominal_awal - self.diskon
        if self.sisa_tagihan is None:
            self.sisa_tagihan = self.total_tagihan - self.total_terbayar
        super().save(*args, **kwargs)


class Pembayaran(BaseModel):
    """
    Transaksi Pembayaran Tagihan Santri.
    Mendukung Idempotency Key dan Pessimistic Locking untuk anti race condition.
    """
    class MetodePembayaran(models.TextChoices):
        TUNAI = 'tunai', 'Tunai / Kasir'
        TRANSFER = 'transfer', 'Transfer Bank'
        QRIS = 'qris', 'QRIS'
        VIRTUAL_ACCOUNT = 'va', 'Virtual Account'

    nomor_bukti = models.CharField(max_length=40, unique=True, db_index=True, verbose_name="Nomor Kuitansi")
    idempotency_key = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="Idempotency Key",
        help_text="Kunci idempotensi untuk menjamin tidak ada duplikasi transaksi"
    )
    santri = models.ForeignKey(Santri, on_delete=models.PROTECT, related_name='riwayat_pembayaran', verbose_name="Santri")
    tagihan = models.ForeignKey(Tagihan, on_delete=models.PROTECT, related_name='pembayaran_list', verbose_name="Tagihan Terkait")
    nominal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Nominal Bayar (Rp)")
    metode_pembayaran = models.CharField(
        max_length=20,
        choices=MetodePembayaran.choices,
        default=MetodePembayaran.TUNAI,
        verbose_name="Metode Pembayaran"
    )
    petugas = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transaksi_diterima',
        verbose_name="Petugas Kasir"
    )
    tanggal_bayar = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Pembayaran")
    catatan = models.TextField(blank=True, verbose_name="Catatan Transaksi")

    class Meta:
        verbose_name = "Transaksi Pembayaran"
        verbose_name_plural = "Daftar Transaksi Pembayaran"
        ordering = ['-tanggal_bayar']

    def __str__(self):
        return f"{self.nomor_bukti} - Rp {self.nominal:,.0f} ({self.santri.nama_lengkap})"
