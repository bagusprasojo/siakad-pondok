import uuid
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from apps.keuangan.models import Tagihan, Pembayaran, PosTarif
from apps.keuangan.services.pembayaran_service import PembayaranService
from apps.santri.models import Santri, Rombel, TahunAjaran


def pembayaran_list(request):
    """
    1. Daftar transaksi diawali dengan list pembayaran yang tersimpan.
    2. Ditampilkan dalam Pagination.
    3. Kolom terakhir memiliki tombol Hapus (dengan konfirmasi).
    4. Kolom No Bukti -> Link ke Detail Pembayaran.
    5. Kolom No Invoice -> Link ke Detail Invoice Tagihan.
    6. Kolom Santri -> Link ke Detail Santri.
    """
    search_query = request.GET.get('q', '').strip()
    metode_filter = request.GET.get('metode', '').strip()

    pembayaran_qs = Pembayaran.objects.select_related(
        'santri',
        'tagihan',
        'tagihan__pos_tarif',
        'petugas'
    ).all()

    if search_query:
        pembayaran_qs = pembayaran_qs.filter(
            Q(nomor_bukti__icontains=search_query) |
            Q(santri__nama_lengkap__icontains=search_query) |
            Q(santri__nis__icontains=search_query) |
            Q(tagihan__nomor_invoice__icontains=search_query)
        )

    if metode_filter:
        pembayaran_qs = pembayaran_qs.filter(metode_pembayaran=metode_filter)

    paginator = Paginator(pembayaran_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'metode_filter': metode_filter,
        'total_transaksi': paginator.count,
    }
    return render(request, 'keuangan/pembayaran_list.html', context)


def pembayaran_detail(request, uuid):
    """
    Halaman detail transaksi pembayaran.
    Menampilkan data transaksi lengkap dan tombol Edit & Cetak.
    """
    pembayaran = get_object_or_404(
        Pembayaran.objects.select_related(
            'santri',
            'tagihan',
            'tagihan__pos_tarif',
            'tagihan__tahun_ajaran',
            'petugas'
        ),
        uuid=uuid
    )
    return render(request, 'keuangan/pembayaran_detail.html', {'pembayaran': pembayaran})


def pembayaran_create(request):
    """
    Form kasir pembayaran baru dengan proteksi Anti-Race Condition dan Idempotency.
    """
    tagihan_uuid = request.GET.get('tagihan')
    selected_tagihan = None
    if tagihan_uuid:
        selected_tagihan = Tagihan.objects.filter(uuid=tagihan_uuid, sisa_tagihan__gt=0).first()

    if request.method == 'POST':
        tagihan_input = request.POST.get('tagihan_uuid')
        nominal_input = request.POST.get('nominal', '0')
        metode_input = request.POST.get('metode_pembayaran', Pembayaran.MetodePembayaran.TUNAI)
        catatan_input = request.POST.get('catatan', '').strip()
        idempotency_key = request.POST.get('idempotency_key', '').strip()

        if not idempotency_key:
            idempotency_key = str(uuid.uuid4())

        try:
            target_tagihan = get_object_or_404(Tagihan, uuid=tagihan_input)
            petugas = request.user if request.user.is_authenticated else None
            if not petugas:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                petugas = User.objects.filter(role__in=['bendahara', 'superadmin']).first()

            pembayaran, is_new = PembayaranService.proses_pembayaran(
                tagihan_id_or_uuid=target_tagihan.uuid,
                nominal=nominal_input,
                metode_pembayaran=metode_input,
                petugas=petugas,
                idempotency_key=idempotency_key,
                catatan=catatan_input
            )

            if is_new:
                messages.success(request, f"Pembayaran {pembayaran.nomor_bukti} berhasil diproses.")
            else:
                messages.info(request, f"Transaksi dengan kunci idempotensi ini telah tercatat sebelumnya: {pembayaran.nomor_bukti}.")

            return redirect('keuangan:pembayaran-detail', uuid=pembayaran.uuid)

        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, 'message') else e))
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")

    # Ambil daftar tagihan yang belum lunas untuk dropdown kasir
    tagihan_belum_lunas = Tagihan.objects.select_related(
        'santri', 'pos_tarif'
    ).filter(sisa_tagihan__gt=0).order_by('santri__nama_lengkap', '-created_at')[:100]

    context = {
        'selected_tagihan': selected_tagihan,
        'tagihan_belum_lunas': tagihan_belum_lunas,
        'metode_choices': Pembayaran.MetodePembayaran.choices,
    }
    return render(request, 'keuangan/pembayaran_form.html', context)


def pembayaran_edit(request, uuid):
    """
    Halaman edit transaksi (catatan transaksi dan metode bayar).
    """
    pembayaran = get_object_or_404(Pembayaran, uuid=uuid)

    if request.method == 'POST':
        metode_input = request.POST.get('metode_pembayaran')
        catatan_input = request.POST.get('catatan', '').strip()

        if metode_input in dict(Pembayaran.MetodePembayaran.choices):
            pembayaran.metode_pembayaran = metode_input
        pembayaran.catatan = catatan_input
        pembayaran.save()

        messages.success(request, f"Catatan transaksi {pembayaran.nomor_bukti} berhasil diperbarui.")
        return redirect('keuangan:pembayaran-detail', uuid=pembayaran.uuid)

    return render(request, 'keuangan/pembayaran_edit.html', {'pembayaran': pembayaran})


@require_POST
def pembayaran_delete(request, uuid):
    """
    Kolom aksi tombol hapus transaksi pembayaran.
    Secara aman mengembalikan saldo sisa tagihan dan status tagihan dalam transaction.atomic().
    """
    with transaction.atomic():
        pembayaran = get_object_or_404(Pembayaran, uuid=uuid)
        tagihan = Tagihan.objects.select_for_update().get(id=pembayaran.tagihan_id)

        # Kembalikan saldo tagihan
        tagihan.total_terbayar -= pembayaran.nominal
        tagihan.sisa_tagihan += pembayaran.nominal

        if tagihan.total_terbayar == Decimal('0.00'):
            tagihan.status = Tagihan.Status.BELUM_BAYAR
        else:
            tagihan.status = Tagihan.Status.SEBAGIAN

        tagihan.save()
        nomor_bukti = pembayaran.nomor_bukti
        pembayaran.delete()

    messages.success(request, f"Transaksi {nomor_bukti} telah dihapus dan sisa tagihan berhasil dikembalikan.")
    return redirect('keuangan:pembayaran-list')


# --- MANAJEMEN TAGIHAN ---

def tagihan_list(request):
    """
    Daftar tagihan santri dengan filter, pagination, dan cross-linking ke detail invoice & detail santri.
    """
    status_filter = request.GET.get('status', '').strip()
    pos_filter = request.GET.get('pos', '').strip()
    search_query = request.GET.get('q', '').strip()

    tagihan_qs = Tagihan.objects.select_related(
        'santri',
        'pos_tarif',
        'tahun_ajaran'
    ).all()

    if search_query:
        tagihan_qs = tagihan_qs.filter(
            Q(nomor_invoice__icontains=search_query) |
            Q(santri__nama_lengkap__icontains=search_query) |
            Q(santri__nis__icontains=search_query)
        )

    if status_filter:
        tagihan_qs = tagihan_qs.filter(status=status_filter)

    if pos_filter:
        tagihan_qs = tagihan_qs.filter(pos_tarif__uuid=pos_filter)

    paginator = Paginator(tagihan_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    pos_tarif_list = PosTarif.objects.filter(is_active=True)

    context = {
        'page_obj': page_obj,
        'pos_tarif_list': pos_tarif_list,
        'status_filter': status_filter,
        'pos_filter': pos_filter,
        'search_query': search_query,
        'status_choices': Tagihan.Status.choices,
    }
    return render(request, 'keuangan/tagihan_list.html', context)


def tagihan_detail(request, uuid):
    """
    Halaman detail invoice tagihan santri.
    Menampilkan rincian tagihan dan tabel riwayat pembayaran (dengan link ke detail bukti pembayaran).
    """
    tagihan = get_object_or_404(
        Tagihan.objects.select_related('santri', 'pos_tarif', 'tahun_ajaran', 'semester'),
        uuid=uuid
    )
    riwayat_pembayaran = tagihan.pembayaran_list.select_related('petugas').order_by('-tanggal_bayar')

    context = {
        'tagihan': tagihan,
        'riwayat_pembayaran': riwayat_pembayaran,
    }
    return render(request, 'keuangan/tagihan_detail.html', context)


def laporan_keuangan(request):
    """
    Laporan keuangan: Rekapitulasi kas masuk dan rekap tunggakan santri.
    """
    total_masuk = Pembayaran.objects.aggregate(total=Sum('nominal'))['total'] or Decimal('0.00')
    total_tunggakan = Tagihan.objects.filter(sisa_tagihan__gt=0).aggregate(total=Sum('sisa_tagihan'))['total'] or Decimal('0.00')

    # Rekap per metode bayar
    rekap_metode = Pembayaran.objects.values('metode_pembayaran').annotate(total=Sum('nominal')).order_by('-total')

    # 10 Tunggakan santri terbesar
    tunggakan_list = Tagihan.objects.filter(sisa_tagihan__gt=0).select_related('santri', 'pos_tarif').order_by('-sisa_tagihan')[:10]

    context = {
        'total_masuk': total_masuk,
        'total_tunggakan': total_tunggakan,
        'rekap_metode': rekap_metode,
        'tunggakan_list': tunggakan_list,
    }
    return render(request, 'keuangan/laporan.html', context)
