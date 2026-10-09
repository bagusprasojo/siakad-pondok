from django.contrib import admin
from .models import PosTarif, TarifKhususSantri, Tagihan, Pembayaran


@admin.register(PosTarif)
class PosTarifAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama', 'tipe', 'tarif_standar', 'is_active', 'uuid')
    list_filter = ('tipe', 'is_active')
    search_fields = ('kode', 'nama')
    readonly_fields = ('uuid', 'created_at', 'updated_at')


@admin.register(TarifKhususSantri)
class TarifKhususSantriAdmin(admin.ModelAdmin):
    list_display = ('santri', 'pos_tarif', 'tahun_ajaran', 'nominal_tarif', 'keterangan', 'uuid')
    list_filter = ('tahun_ajaran', 'pos_tarif')
    search_fields = ('santri__nama_lengkap', 'santri__nis', 'keterangan')
    readonly_fields = ('uuid', 'created_at', 'updated_at')


class PembayaranInline(admin.TabularInline):
    model = Pembayaran
    extra = 0
    readonly_fields = ('nomor_bukti', 'nominal', 'metode_pembayaran', 'petugas', 'tanggal_bayar', 'uuid')
    can_delete = False


@admin.register(Tagihan)
class TagihanAdmin(admin.ModelAdmin):
    list_display = ('nomor_invoice', 'santri', 'pos_tarif', 'bulan', 'tahun', 'total_tagihan', 'total_terbayar', 'sisa_tagihan', 'status', 'uuid')
    list_filter = ('status', 'pos_tarif', 'tahun_ajaran', 'bulan')
    search_fields = ('nomor_invoice', 'santri__nama_lengkap', 'santri__nis')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    inlines = [PembayaranInline]


@admin.register(Pembayaran)
class PembayaranAdmin(admin.ModelAdmin):
    list_display = ('nomor_bukti', 'santri', 'tagihan', 'nominal', 'metode_pembayaran', 'petugas', 'tanggal_bayar', 'uuid')
    list_filter = ('metode_pembayaran', 'tanggal_bayar')
    search_fields = ('nomor_bukti', 'santri__nama_lengkap', 'santri__nis', 'tagihan__nomor_invoice')
    readonly_fields = ('nomor_bukti', 'idempotency_key', 'uuid', 'tanggal_bayar', 'created_at', 'updated_at')
