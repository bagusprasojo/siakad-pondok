from django.shortcuts import render
from django.db.models import Sum, Count
from decimal import Decimal
from apps.santri.models import Santri, Rombel
from apps.keuangan.models import Tagihan, Pembayaran


def dashboard(request):
    """
    Dashboard Eksekutif Pondok Pesantren:
    Statistik santri, keuangan real-time, dan transaksi terbaru.
    """
    total_santri_aktif = Santri.objects.filter(status=Santri.Status.AKTIF).count()
    total_rombel = Rombel.objects.filter(tahun_ajaran__is_active=True).count()

    total_kas_masuk = Pembayaran.objects.aggregate(total=Sum('nominal'))['total'] or Decimal('0.00')
    total_tunggakan = Tagihan.objects.filter(sisa_tagihan__gt=0).aggregate(total=Sum('sisa_tagihan'))['total'] or Decimal('0.00')

    # 5 Transaksi Pembayaran Terakhir
    transaksi_terbaru = Pembayaran.objects.select_related(
        'santri', 'tagihan', 'tagihan__pos_tarif', 'petugas'
    ).order_by('-tanggal_bayar')[:5]

    # 5 Tagihan Terakhir yang Belum Lunas
    tagihan_terbaru = Tagihan.objects.select_related(
        'santri', 'pos_tarif'
    ).filter(sisa_tagihan__gt=0).order_by('-created_at')[:5]

    context = {
        'total_santri_aktif': total_santri_aktif,
        'total_rombel': total_rombel,
        'total_kas_masuk': total_kas_masuk,
        'total_tunggakan': total_tunggakan,
        'transaksi_terbaru': transaksi_terbaru,
        'tagihan_terbaru': tagihan_terbaru,
    }
    return render(request, 'core/dashboard.html', context)
