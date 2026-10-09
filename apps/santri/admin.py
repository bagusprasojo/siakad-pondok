from django.contrib import admin
from .models import TahunAjaran, Semester, Rombel, Santri, AnggotaRombel


@admin.register(TahunAjaran)
class TahunAjaranAdmin(admin.ModelAdmin):
    list_display = ('nama', 'tanggal_mulai', 'tanggal_selesai', 'is_active', 'uuid')
    list_filter = ('is_active',)
    search_fields = ('nama',)
    readonly_fields = ('uuid', 'created_at', 'updated_at')


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('tahun_ajaran', 'jenis', 'is_active', 'uuid')
    list_filter = ('jenis', 'is_active')
    readonly_fields = ('uuid', 'created_at', 'updated_at')


@admin.register(Rombel)
class RombelAdmin(admin.ModelAdmin):
    list_display = ('nama', 'tingkat', 'tahun_ajaran', 'wali_rombel', 'kapasitas', 'total_santri', 'uuid')
    list_filter = ('tingkat', 'tahun_ajaran')
    search_fields = ('nama', 'wali_rombel__username')
    readonly_fields = ('uuid', 'created_at', 'updated_at')


class AnggotaRombelInline(admin.TabularInline):
    model = AnggotaRombel
    extra = 1
    readonly_fields = ('uuid',)


@admin.register(Santri)
class SantriAdmin(admin.ModelAdmin):
    list_display = ('nis', 'nama_lengkap', 'jenis_kelamin', 'status', 'telepon_ayah', 'telepon_ibu', 'telepon_wali', 'uuid')
    list_filter = ('status', 'jenis_kelamin', 'hubungan_wali', 'status_ayah', 'status_ibu')
    search_fields = ('nis', 'nama_lengkap', 'nisn', 'nik', 'no_kk', 'nama_ayah', 'nama_ibu', 'telepon_wali')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    inlines = [AnggotaRombelInline]
    fieldsets = (
        ('Identitas Pokok Santri', {
            'fields': (
                'uuid', 'nis', 'nisn', 'nik', 'no_kk', 'nama_lengkap', 'panggilan',
                'jenis_kelamin', 'tempat_lahir', 'tanggal_lahir', 'anak_ke', 'jumlah_saudara',
                'golongan_darah', 'riwayat_penyakit', 'foto'
            )
        }),
        ('Alamat Domisili Santri', {
            'fields': (
                'alamat', 'desa_kelurahan_santri', 'kecamatan_santri',
                'kabupaten_kota_santri', 'provinsi_santri', 'kode_pos_santri'
            )
        }),
        ('Data Ayah Kandung', {
            'fields': (
                'nama_ayah', 'nik_ayah', 'status_ayah', 'pendidikan_ayah',
                'pekerjaan_ayah', 'penghasilan_ayah', 'telepon_ayah',
                'alamat_ayah_sama', 'alamat_ayah', 'desa_kelurahan_ayah',
                'kecamatan_ayah', 'kabupaten_kota_ayah', 'provinsi_ayah', 'kode_pos_ayah'
            )
        }),
        ('Data Ibu Kandung', {
            'fields': (
                'nama_ibu', 'nik_ibu', 'status_ibu', 'pendidikan_ibu',
                'pekerjaan_ibu', 'penghasilan_ibu', 'telepon_ibu',
                'alamat_ibu_sama', 'alamat_ibu', 'desa_kelurahan_ibu',
                'kecamatan_ibu', 'kabupaten_kota_ibu', 'provinsi_ibu', 'kode_pos_ibu'
            )
        }),
        ('Data Wali & Penanggung Jawab', {
            'fields': (
                'hubungan_wali', 'nama_wali', 'nik_wali', 'pekerjaan_wali',
                'penghasilan_wali', 'telepon_wali', 'alamat_wali_sama',
                'alamat_wali', 'desa_kelurahan_wali', 'kecamatan_wali',
                'kabupaten_kota_wali', 'provinsi_wali', 'kode_pos_wali', 'wali_user'
            )
        }),
        ('Status & Administrasi', {
            'fields': ('status', 'tanggal_masuk', 'tanggal_lulus', 'no_ijazah')
        }),
        ('Informasi Sistem', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AnggotaRombel)
class AnggotaRombelAdmin(admin.ModelAdmin):
    list_display = ('santri', 'rombel', 'tahun_ajaran', 'status', 'uuid')
    list_filter = ('tahun_ajaran', 'rombel', 'status')
    search_fields = ('santri__nama_lengkap', 'santri__nis', 'rombel__nama')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
