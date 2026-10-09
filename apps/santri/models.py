from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class TahunAjaran(BaseModel):
    """
    Master Tahun Ajaran (contoh: 2026/2027).
    """
    nama = models.CharField(max_length=20, unique=True, verbose_name="Tahun Ajaran")
    tanggal_mulai = models.DateField(verbose_name="Tanggal Mulai")
    tanggal_selesai = models.DateField(verbose_name="Tanggal Selesai")
    is_active = models.BooleanField(default=False, verbose_name="Status Aktif")

    class Meta:
        verbose_name = "Tahun Ajaran"
        verbose_name_plural = "Daftar Tahun Ajaran"
        ordering = ['-tanggal_mulai']

    def __str__(self):
        return f"{self.nama} {'(Aktif)' if self.is_active else ''}"

    def save(self, *args, **kwargs):
        # Jika di-set aktif, nonaktifkan tahun ajaran lain
        if self.is_active:
            TahunAjaran.objects.exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)


class Semester(BaseModel):
    """
    Semester dalam satu Tahun Ajaran (Ganjil / Genap).
    """
    class Jenis(models.TextChoices):
        GANJIL = 'ganjil', 'Ganjil'
        GENAP = 'genap', 'Genap'

    tahun_ajaran = models.ForeignKey(
        TahunAjaran,
        on_delete=models.CASCADE,
        related_name='semester_list',
        verbose_name="Tahun Ajaran"
    )
    jenis = models.CharField(max_length=10, choices=Jenis.choices, verbose_name="Semester")
    is_active = models.BooleanField(default=False, verbose_name="Status Aktif")

    class Meta:
        verbose_name = "Semester"
        verbose_name_plural = "Daftar Semester"
        constraints = [
            models.UniqueConstraint(fields=['tahun_ajaran', 'jenis'], name='unique_semester_per_tahun')
        ]
        ordering = ['-tahun_ajaran__tanggal_mulai', 'jenis']

    def __str__(self):
        return f"{self.tahun_ajaran.nama} - {self.get_jenis_display()}"

    def save(self, *args, **kwargs):
        if self.is_active:
            Semester.objects.exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)


class Rombel(BaseModel):
    """
    Rombongan Belajar (Kelas/Kelompok Belajar per Tahun Ajaran).
    """
    nama = models.CharField(max_length=50, verbose_name="Nama Rombel")
    tingkat = models.PositiveSmallIntegerField(default=1, verbose_name="Tingkat / Kelas")
    tahun_ajaran = models.ForeignKey(
        TahunAjaran,
        on_delete=models.PROTECT,
        related_name='rombel_list',
        verbose_name="Tahun Ajaran"
    )
    wali_rombel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rombel_diampu',
        verbose_name="Wali Rombel / Wali Kelas"
    )
    kapasitas = models.PositiveSmallIntegerField(default=30, verbose_name="Kapasitas Maksimal")
    keterangan = models.TextField(blank=True, verbose_name="Keterangan")

    class Meta:
        verbose_name = "Rombongan Belajar"
        verbose_name_plural = "Daftar Rombongan Belajar"
        constraints = [
            models.UniqueConstraint(fields=['nama', 'tahun_ajaran'], name='unique_rombel_per_tahun_ajaran')
        ]
        ordering = ['tingkat', 'nama']

    def __str__(self):
        return f"{self.nama} ({self.tahun_ajaran.nama})"

    @property
    def total_santri(self):
        return self.anggota_list.filter(status='aktif').count()


class Santri(BaseModel):
    """
    Master Data Santri Pesantren Terpadu.
    Mencakup data pribadi, riwayat kesehatan, data ayah, ibu, wali, dan struktur alamat lengkap.
    """
    class JenisKelamin(models.TextChoices):
        LAKI_LAKI = 'L', 'Laki-laki'
        PEREMPUAN = 'P', 'Perempuan'

    class Status(models.TextChoices):
        AKTIF = 'aktif', 'Aktif'
        LULUS = 'lulus', 'Lulus'
        MUTASI = 'mutasi', 'Mutasi / Pindah'
        KELUAR = 'keluar', 'Keluar / DO'
        ALUMNI = 'alumni', 'Alumni'

    class StatusHidup(models.TextChoices):
        HIDUP = 'hidup', 'Masih Hidup'
        MENINGGAL = 'meninggal', 'Meninggal Dunia (Alm/Almh)'

    class HubunganWali(models.TextChoices):
        SAMA_AYAH = 'sama_ayah', 'Sama dengan Ayah Kandung'
        SAMA_IBU = 'sama_ibu', 'Sama dengan Ibu Kandung'
        KAKEK_NENEK = 'kakek_nenek', 'Kakek / Nenek'
        PAMAN_BIBI = 'paman_bibi', 'Paman / Bibi'
        SAUDARA = 'saudara', 'Kakak Kandung / Saudara'
        LAINNYA = 'lainnya', 'Wali Lainnya'

    # 1. Identitas Pokok Santri
    nis = models.CharField(max_length=30, unique=True, db_index=True, verbose_name="Nomor Induk Santri (NIS)")
    nisn = models.CharField(max_length=20, blank=True, null=True, db_index=True, verbose_name="NISN")
    nik = models.CharField(max_length=20, blank=True, null=True, verbose_name="NIK Santri")
    no_kk = models.CharField(max_length=20, blank=True, null=True, verbose_name="No. Kartu Keluarga (KK)")
    nama_lengkap = models.CharField(max_length=150, verbose_name="Nama Lengkap")
    panggilan = models.CharField(max_length=50, blank=True, verbose_name="Nama Panggilan")
    jenis_kelamin = models.CharField(max_length=1, choices=JenisKelamin.choices, verbose_name="Jenis Kelamin")
    tempat_lahir = models.CharField(max_length=100, blank=True, verbose_name="Tempat Lahir")
    tanggal_lahir = models.DateField(null=True, blank=True, verbose_name="Tanggal Lahir")
    anak_ke = models.PositiveSmallIntegerField(default=1, verbose_name="Anak ke-")
    jumlah_saudara = models.PositiveSmallIntegerField(default=1, verbose_name="Dari Jumlah Saudara")
    golongan_darah = models.CharField(
        max_length=5,
        choices=[('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O'), ('-', 'Tidak Tahu')],
        default='-',
        verbose_name="Golongan Darah"
    )
    riwayat_penyakit = models.TextField(blank=True, verbose_name="Riwayat Penyakit / Alergi")

    # 2. Alamat Santri
    alamat = models.TextField(blank=True, verbose_name="Alamat / Jalan / RT / RW")
    desa_kelurahan_santri = models.CharField(max_length=100, blank=True, verbose_name="Desa / Kelurahan")
    kecamatan_santri = models.CharField(max_length=100, blank=True, verbose_name="Kecamatan")
    kabupaten_kota_santri = models.CharField(max_length=100, blank=True, verbose_name="Kabupaten / Kota")
    provinsi_santri = models.CharField(max_length=100, blank=True, verbose_name="Provinsi")
    kode_pos_santri = models.CharField(max_length=10, blank=True, verbose_name="Kode Pos")

    # 3. Data Ayah Kandung
    nama_ayah = models.CharField(max_length=100, blank=True, verbose_name="Nama Ayah")
    nik_ayah = models.CharField(max_length=20, blank=True, verbose_name="NIK Ayah")
    status_ayah = models.CharField(
        max_length=15,
        choices=StatusHidup.choices,
        default=StatusHidup.HIDUP,
        verbose_name="Status Ayah"
    )
    pendidikan_ayah = models.CharField(max_length=50, blank=True, verbose_name="Pendidikan Terakhir Ayah")
    pekerjaan_ayah = models.CharField(max_length=100, blank=True, verbose_name="Pekerjaan Ayah")
    penghasilan_ayah = models.CharField(max_length=50, blank=True, verbose_name="Penghasilan Bulanan Ayah")
    telepon_ayah = models.CharField(max_length=25, blank=True, verbose_name="No. HP / WA Ayah")
    alamat_ayah_sama = models.BooleanField(default=True, verbose_name="Alamat Ayah Sama dengan Santri")
    alamat_ayah = models.TextField(blank=True, verbose_name="Alamat Lengkap Ayah")
    desa_kelurahan_ayah = models.CharField(max_length=100, blank=True, verbose_name="Desa / Kelurahan Ayah")
    kecamatan_ayah = models.CharField(max_length=100, blank=True, verbose_name="Kecamatan Ayah")
    kabupaten_kota_ayah = models.CharField(max_length=100, blank=True, verbose_name="Kabupaten / Kota Ayah")
    provinsi_ayah = models.CharField(max_length=100, blank=True, verbose_name="Provinsi Ayah")
    kode_pos_ayah = models.CharField(max_length=10, blank=True, verbose_name="Kode Pos Ayah")

    # 4. Data Ibu Kandung
    nama_ibu = models.CharField(max_length=100, blank=True, verbose_name="Nama Ibu")
    nik_ibu = models.CharField(max_length=20, blank=True, verbose_name="NIK Ibu")
    status_ibu = models.CharField(
        max_length=15,
        choices=StatusHidup.choices,
        default=StatusHidup.HIDUP,
        verbose_name="Status Ibu"
    )
    pendidikan_ibu = models.CharField(max_length=50, blank=True, verbose_name="Pendidikan Terakhir Ibu")
    pekerjaan_ibu = models.CharField(max_length=100, blank=True, verbose_name="Pekerjaan Ibu")
    penghasilan_ibu = models.CharField(max_length=50, blank=True, verbose_name="Penghasilan Bulanan Ibu")
    telepon_ibu = models.CharField(max_length=25, blank=True, verbose_name="No. HP / WA Ibu")
    alamat_ibu_sama = models.BooleanField(default=True, verbose_name="Alamat Ibu Sama dengan Santri")
    alamat_ibu = models.TextField(blank=True, verbose_name="Alamat Lengkap Ibu")
    desa_kelurahan_ibu = models.CharField(max_length=100, blank=True, verbose_name="Desa / Kelurahan Ibu")
    kecamatan_ibu = models.CharField(max_length=100, blank=True, verbose_name="Kecamatan Ibu")
    kabupaten_kota_ibu = models.CharField(max_length=100, blank=True, verbose_name="Kabupaten / Kota Ibu")
    provinsi_ibu = models.CharField(max_length=100, blank=True, verbose_name="Provinsi Ibu")
    kode_pos_ibu = models.CharField(max_length=10, blank=True, verbose_name="Kode Pos Ibu")

    # 5. Data Wali Santri & Kontak Darurat
    hubungan_wali = models.CharField(
        max_length=25,
        choices=HubunganWali.choices,
        default=HubunganWali.SAMA_AYAH,
        verbose_name="Hubungan Wali dengan Santri"
    )
    nama_wali = models.CharField(max_length=100, blank=True, verbose_name="Nama Wali")
    nik_wali = models.CharField(max_length=20, blank=True, verbose_name="NIK Wali")
    pekerjaan_wali = models.CharField(max_length=100, blank=True, verbose_name="Pekerjaan Wali")
    penghasilan_wali = models.CharField(max_length=50, blank=True, verbose_name="Penghasilan Bulanan Wali")
    telepon_wali = models.CharField(max_length=25, blank=True, verbose_name="No. HP / WhatsApp Wali")
    alamat_wali_sama = models.BooleanField(default=True, verbose_name="Alamat Wali Sama dengan Santri")
    alamat_wali = models.TextField(blank=True, verbose_name="Alamat Lengkap Wali")
    desa_kelurahan_wali = models.CharField(max_length=100, blank=True, verbose_name="Desa / Kelurahan Wali")
    kecamatan_wali = models.CharField(max_length=100, blank=True, verbose_name="Kecamatan Wali")
    kabupaten_kota_wali = models.CharField(max_length=100, blank=True, verbose_name="Kabupaten / Kota Wali")
    provinsi_wali = models.CharField(max_length=100, blank=True, verbose_name="Provinsi Wali")
    kode_pos_wali = models.CharField(max_length=10, blank=True, verbose_name="Kode Pos Wali")

    wali_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='anak_santri',
        verbose_name="Akun User Wali Santri"
    )

    # Status & Administrasi
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.AKTIF, verbose_name="Status Santri")
    tanggal_masuk = models.DateField(null=True, blank=True, verbose_name="Tanggal Masuk")
    tanggal_lulus = models.DateField(null=True, blank=True, verbose_name="Tanggal Kelulusan")
    no_ijazah = models.CharField(max_length=60, blank=True, null=True, verbose_name="No. Ijazah / Syahadah")
    foto = models.ImageField(upload_to='santri/foto/', blank=True, null=True, verbose_name="Foto Santri")

    class Meta:
        verbose_name = "Santri"
        verbose_name_plural = "Daftar Santri"
        ordering = ['nama_lengkap']

    def __str__(self):
        return f"{self.nis} - {self.nama_lengkap}"

    @property
    def rombel_aktif(self):
        anggota = self.riwayat_rombel.filter(status='aktif', rombel__tahun_ajaran__is_active=True).select_related('rombel').first()
        return anggota.rombel if anggota else None

    @property
    def get_nama_wali_efektif(self):
        if self.hubungan_wali == self.HubunganWali.SAMA_AYAH:
            return self.nama_ayah or "Ayah Kandung"
        elif self.hubungan_wali == self.HubunganWali.SAMA_IBU:
            return self.nama_ibu or "Ibu Kandung"
        return self.nama_wali or "-"

    @property
    def get_telepon_wali_efektif(self):
        if self.hubungan_wali == self.HubunganWali.SAMA_AYAH:
            return self.telepon_ayah or self.telepon_wali or "-"
        elif self.hubungan_wali == self.HubunganWali.SAMA_IBU:
            return self.telepon_ibu or self.telepon_wali or "-"
        return self.telepon_wali or "-"

    def get_alamat_santri_lengkap(self):
        parts = [self.alamat, self.desa_kelurahan_santri, self.kecamatan_santri, self.kabupaten_kota_santri, self.provinsi_santri]
        parts = [p for p in parts if p]
        text = ", ".join(parts)
        if self.kode_pos_santri:
            text += f" ({self.kode_pos_santri})"
        return text or "-"

    def get_alamat_ayah_lengkap(self):
        if self.alamat_ayah_sama:
            return self.get_alamat_santri_lengkap()
        parts = [self.alamat_ayah, self.desa_kelurahan_ayah, self.kecamatan_ayah, self.kabupaten_kota_ayah, self.provinsi_ayah]
        parts = [p for p in parts if p]
        text = ", ".join(parts)
        if self.kode_pos_ayah:
            text += f" ({self.kode_pos_ayah})"
        return text or "-"

    def get_alamat_ibu_lengkap(self):
        if self.alamat_ibu_sama:
            return self.get_alamat_santri_lengkap()
        parts = [self.alamat_ibu, self.desa_kelurahan_ibu, self.kecamatan_ibu, self.kabupaten_kota_ibu, self.provinsi_ibu]
        parts = [p for p in parts if p]
        text = ", ".join(parts)
        if self.kode_pos_ibu:
            text += f" ({self.kode_pos_ibu})"
        return text or "-"

    def get_alamat_wali_lengkap(self):
        if self.hubungan_wali == self.HubunganWali.SAMA_AYAH:
            return self.get_alamat_ayah_lengkap()
        elif self.hubungan_wali == self.HubunganWali.SAMA_IBU:
            return self.get_alamat_ibu_lengkap()
        elif self.alamat_wali_sama:
            return self.get_alamat_santri_lengkap()
        parts = [self.alamat_wali, self.desa_kelurahan_wali, self.kecamatan_wali, self.kabupaten_kota_wali, self.provinsi_wali]
        parts = [p for p in parts if p]
        text = ", ".join(parts)
        if self.kode_pos_wali:
            text += f" ({self.kode_pos_wali})"
        return text or "-"


class AnggotaRombel(BaseModel):
    """
    Riwayat Penempatan Santri di Rombel per Tahun Ajaran.
    Mendukung riwayat kenaikan kelas, tinggal kelas, dan kelulusan.
    """
    class StatusKeanggotaan(models.TextChoices):
        AKTIF = 'aktif', 'Aktif'
        NAIK_KELAS = 'naik_kelas', 'Naik Kelas'
        TINGGAL_KELAS = 'tinggal_kelas', 'Tinggal Kelas'
        LULUS = 'lulus', 'Lulus'
        PINDAH = 'pindah', 'Pindah Rombel'

    santri = models.ForeignKey(
        Santri,
        on_delete=models.CASCADE,
        related_name='riwayat_rombel',
        verbose_name="Santri"
    )
    rombel = models.ForeignKey(
        Rombel,
        on_delete=models.PROTECT,
        related_name='anggota_list',
        verbose_name="Rombel"
    )
    tahun_ajaran = models.ForeignKey(
        TahunAjaran,
        on_delete=models.PROTECT,
        related_name='riwayat_anggota_rombel',
        verbose_name="Tahun Ajaran"
    )
    status = models.CharField(
        max_length=20,
        choices=StatusKeanggotaan.choices,
        default=StatusKeanggotaan.AKTIF,
        verbose_name="Status Keanggotaan"
    )
    catatan = models.CharField(max_length=255, blank=True, verbose_name="Catatan")

    class Meta:
        verbose_name = "Anggota Rombel"
        verbose_name_plural = "Daftar Anggota Rombel"
        constraints = [
            models.UniqueConstraint(fields=['santri', 'tahun_ajaran'], name='unique_santri_per_tahun_ajaran')
        ]
        ordering = ['rombel', 'santri__nama_lengkap']

    def __str__(self):
        return f"{self.santri.nama_lengkap} -> {self.rombel.nama} ({self.tahun_ajaran.nama})"
