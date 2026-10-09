from rest_framework import serializers
from apps.keuangan.models import Tagihan, Pembayaran, PosTarif


class PosTarifSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosTarif
        fields = ['uuid', 'kode', 'nama', 'tipe', 'tarif_standar']


class TagihanSerializer(serializers.ModelSerializer):
    santri_nama = serializers.ReadOnlyField(source='santri.nama_lengkap')
    santri_nis = serializers.ReadOnlyField(source='santri.nis')
    pos_nama = serializers.ReadOnlyField(source='pos_tarif.nama')

    class Meta:
        model = Tagihan
        fields = [
            'uuid', 'nomor_invoice', 'santri_nama', 'santri_nis', 'pos_nama',
            'bulan', 'tahun', 'total_tagihan', 'total_terbayar', 'sisa_tagihan',
            'status', 'tanggal_jatuh_tempo'
        ]


class PembayaranSerializer(serializers.ModelSerializer):
    santri_nama = serializers.ReadOnlyField(source='santri.nama_lengkap')
    invoice_nomor = serializers.ReadOnlyField(source='tagihan.nomor_invoice')
    petugas_nama = serializers.ReadOnlyField(source='petugas.get_full_name')

    class Meta:
        model = Pembayaran
        fields = [
            'uuid', 'nomor_bukti', 'santri_nama', 'invoice_nomor',
            'nominal', 'metode_pembayaran', 'petugas_nama',
            'tanggal_bayar', 'catatan'
        ]
