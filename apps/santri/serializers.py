from rest_framework import serializers
from apps.santri.models import Santri, Rombel, TahunAjaran, Semester


class TahunAjaranSerializer(serializers.ModelSerializer):
    class Meta:
        model = TahunAjaran
        fields = ['uuid', 'nama', 'tanggal_mulai', 'tanggal_selesai', 'is_active']


class RombelSerializer(serializers.ModelSerializer):
    wali_nama = serializers.ReadOnlyField(source='wali_rombel.get_full_name')

    class Meta:
        model = Rombel
        fields = ['uuid', 'nama', 'tingkat', 'wali_nama', 'kapasitas', 'total_santri']


class SantriSerializer(serializers.ModelSerializer):
    rombel_aktif_nama = serializers.SerializerMethodField()
    nama_wali_efektif = serializers.ReadOnlyField(source='get_nama_wali_efektif')
    telepon_wali_efektif = serializers.ReadOnlyField(source='get_telepon_wali_efektif')
    alamat_lengkap = serializers.ReadOnlyField(source='get_alamat_santri_lengkap')
    alamat_wali_lengkap = serializers.ReadOnlyField(source='get_alamat_wali_lengkap')

    class Meta:
        model = Santri
        fields = [
            'uuid', 'nis', 'nisn', 'nik', 'no_kk', 'nama_lengkap', 'panggilan',
            'jenis_kelamin', 'tempat_lahir', 'tanggal_lahir', 'golongan_darah',
            'riwayat_penyakit', 'status', 'rombel_aktif_nama', 'alamat_lengkap',
            'nama_ayah', 'status_ayah', 'pekerjaan_ayah', 'telepon_ayah',
            'nama_ibu', 'status_ibu', 'pekerjaan_ibu', 'telepon_ibu',
            'hubungan_wali', 'nama_wali_efektif', 'telepon_wali_efektif',
            'alamat_wali_lengkap'
        ]

    def get_rombel_aktif_nama(self, obj):
        rombel = obj.rombel_aktif
        return rombel.nama if rombel else None
