from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from apps.santri.models import Santri, Rombel, TahunAjaran, Semester, AnggotaRombel
from apps.keuangan.models import Tagihan, Pembayaran

User = get_user_model()


def santri_list(request):
    """
    Daftar master santri dengan pagination, filter status dan rombel, serta pencarian.
    """
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    rombel_filter = request.GET.get('rombel', '').strip()

    santri_qs = Santri.objects.all()

    if search_query:
        santri_qs = santri_qs.filter(
            Q(nama_lengkap__icontains=search_query) |
            Q(nis__icontains=search_query) |
            Q(nisn__icontains=search_query) |
            Q(nama_ayah__icontains=search_query)
        )

    if status_filter:
        santri_qs = santri_qs.filter(status=status_filter)

    if rombel_filter:
        santri_qs = santri_qs.filter(
            riwayat_rombel__rombel__uuid=rombel_filter,
            riwayat_rombel__status=AnggotaRombel.StatusKeanggotaan.AKTIF
        )

    paginator = Paginator(santri_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    rombel_list = Rombel.objects.filter(tahun_ajaran__is_active=True)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'rombel_filter': rombel_filter,
        'rombel_list': rombel_list,
        'status_choices': Santri.Status.choices,
        'total_santri': paginator.count,
    }
    return render(request, 'santri/santri_list.html', context)


def santri_detail(request, uuid):
    """
    Halaman Detail Santri (Kartu Induk Santri).
    Menampilkan data diri, data wali, riwayat rombel,
    serta riwayat keuangan (Tagihan dan Pembayaran yang cross-linked ke detail masing-masing).
    """
    santri = get_object_or_404(Santri, uuid=uuid)
    riwayat_rombel = santri.riwayat_rombel.select_related('rombel', 'tahun_ajaran').order_by('-tahun_ajaran__tanggal_mulai')
    tagihan_list = santri.tagihan_list.select_related('pos_tarif', 'tahun_ajaran').order_by('-created_at')
    pembayaran_list = santri.riwayat_pembayaran.select_related('tagihan', 'petugas').order_by('-tanggal_bayar')

    context = {
        'santri': santri,
        'riwayat_rombel': riwayat_rombel,
        'tagihan_list': tagihan_list,
        'pembayaran_list': pembayaran_list,
    }
    return render(request, 'santri/santri_detail.html', context)


def santri_create(request):
    """
    Form penambahan santri baru, data orang tua & wali, serta penempatan rombel awal.
    """
    if request.method == 'POST':
        nis = request.POST.get('nis', '').strip()
        nama = request.POST.get('nama_lengkap', '').strip()
        gender = request.POST.get('jenis_kelamin')
        rombel_uuid = request.POST.get('rombel_uuid')

        if not nis or not nama:
            messages.error(request, "NIS dan Nama Lengkap wajib diisi.")
        elif Santri.objects.filter(nis=nis).exists():
            messages.error(request, f"Santri dengan NIS {nis} sudah terdaftar.")
        else:
            with transaction.atomic():
                # Tanggal lahir jika diisi
                tgl_lahir = request.POST.get('tanggal_lahir') or None

                santri = Santri.objects.create(
                    # 1. Identitas Pokok Santri
                    nis=nis,
                    nisn=request.POST.get('nisn', '').strip() or None,
                    nik=request.POST.get('nik', '').strip() or None,
                    no_kk=request.POST.get('no_kk', '').strip() or None,
                    nama_lengkap=nama,
                    panggilan=request.POST.get('panggilan', '').strip(),
                    jenis_kelamin=gender,
                    tempat_lahir=request.POST.get('tempat_lahir', '').strip(),
                    tanggal_lahir=tgl_lahir,
                    anak_ke=int(request.POST.get('anak_ke') or 1),
                    jumlah_saudara=int(request.POST.get('jumlah_saudara') or 1),
                    golongan_darah=request.POST.get('golongan_darah', '-'),
                    riwayat_penyakit=request.POST.get('riwayat_penyakit', '').strip(),

                    # 2. Alamat Santri
                    alamat=request.POST.get('alamat', '').strip(),
                    desa_kelurahan_santri=request.POST.get('desa_kelurahan_santri', '').strip(),
                    kecamatan_santri=request.POST.get('kecamatan_santri', '').strip(),
                    kabupaten_kota_santri=request.POST.get('kabupaten_kota_santri', '').strip(),
                    provinsi_santri=request.POST.get('provinsi_santri', '').strip(),
                    kode_pos_santri=request.POST.get('kode_pos_santri', '').strip(),

                    # 3. Data Ayah Kandung
                    nama_ayah=request.POST.get('nama_ayah', '').strip(),
                    nik_ayah=request.POST.get('nik_ayah', '').strip(),
                    status_ayah=request.POST.get('status_ayah', 'hidup'),
                    pendidikan_ayah=request.POST.get('pendidikan_ayah', '').strip(),
                    pekerjaan_ayah=request.POST.get('pekerjaan_ayah', '').strip(),
                    penghasilan_ayah=request.POST.get('penghasilan_ayah', '').strip(),
                    telepon_ayah=request.POST.get('telepon_ayah', '').strip(),
                    alamat_ayah_sama=request.POST.get('alamat_ayah_sama') == 'on',
                    alamat_ayah=request.POST.get('alamat_ayah', '').strip(),
                    desa_kelurahan_ayah=request.POST.get('desa_kelurahan_ayah', '').strip(),
                    kecamatan_ayah=request.POST.get('kecamatan_ayah', '').strip(),
                    kabupaten_kota_ayah=request.POST.get('kabupaten_kota_ayah', '').strip(),
                    provinsi_ayah=request.POST.get('provinsi_ayah', '').strip(),
                    kode_pos_ayah=request.POST.get('kode_pos_ayah', '').strip(),

                    # 4. Data Ibu Kandung
                    nama_ibu=request.POST.get('nama_ibu', '').strip(),
                    nik_ibu=request.POST.get('nik_ibu', '').strip(),
                    status_ibu=request.POST.get('status_ibu', 'hidup'),
                    pendidikan_ibu=request.POST.get('pendidikan_ibu', '').strip(),
                    pekerjaan_ibu=request.POST.get('pekerjaan_ibu', '').strip(),
                    penghasilan_ibu=request.POST.get('penghasilan_ibu', '').strip(),
                    telepon_ibu=request.POST.get('telepon_ibu', '').strip(),
                    alamat_ibu_sama=request.POST.get('alamat_ibu_sama') == 'on',
                    alamat_ibu=request.POST.get('alamat_ibu', '').strip(),
                    desa_kelurahan_ibu=request.POST.get('desa_kelurahan_ibu', '').strip(),
                    kecamatan_ibu=request.POST.get('kecamatan_ibu', '').strip(),
                    kabupaten_kota_ibu=request.POST.get('kabupaten_kota_ibu', '').strip(),
                    provinsi_ibu=request.POST.get('provinsi_ibu', '').strip(),
                    kode_pos_ibu=request.POST.get('kode_pos_ibu', '').strip(),

                    # 5. Data Wali
                    hubungan_wali=request.POST.get('hubungan_wali', 'sama_ayah'),
                    nama_wali=request.POST.get('nama_wali', '').strip(),
                    nik_wali=request.POST.get('nik_wali', '').strip(),
                    pekerjaan_wali=request.POST.get('pekerjaan_wali', '').strip(),
                    penghasilan_wali=request.POST.get('penghasilan_wali', '').strip(),
                    telepon_wali=request.POST.get('telepon_wali', '').strip(),
                    alamat_wali_sama=request.POST.get('alamat_wali_sama') == 'on',
                    alamat_wali=request.POST.get('alamat_wali', '').strip(),
                    desa_kelurahan_wali=request.POST.get('desa_kelurahan_wali', '').strip(),
                    kecamatan_wali=request.POST.get('kecamatan_wali', '').strip(),
                    kabupaten_kota_wali=request.POST.get('kabupaten_kota_wali', '').strip(),
                    provinsi_wali=request.POST.get('provinsi_wali', '').strip(),
                    kode_pos_wali=request.POST.get('kode_pos_wali', '').strip(),

                    status=Santri.Status.AKTIF
                )

                if rombel_uuid:
                    rombel = Rombel.objects.filter(uuid=rombel_uuid).first()
                    if rombel:
                        AnggotaRombel.objects.create(
                            santri=santri,
                            rombel=rombel,
                            tahun_ajaran=rombel.tahun_ajaran,
                            status=AnggotaRombel.StatusKeanggotaan.AKTIF
                        )

            messages.success(request, f"Data santri {santri.nama_lengkap} beserta data orang tua berhasil disimpan.")
            return redirect('santri:santri-detail', uuid=santri.uuid)

    rombel_aktif = Rombel.objects.filter(tahun_ajaran__is_active=True)
    context = {
        'rombel_list': rombel_aktif,
        'status_hidup_choices': Santri.StatusHidup.choices,
        'hubungan_wali_choices': Santri.HubunganWali.choices,
    }
    return render(request, 'santri/santri_form.html', context)


def santri_edit(request, uuid):
    """
    Form edit profil, biodata lengkap, dan data orang tua/wali santri.
    """
    santri = get_object_or_404(Santri, uuid=uuid)

    if request.method == 'POST':
        # 1. Identitas Pokok Santri
        santri.nisn = request.POST.get('nisn', '').strip() or None
        santri.nik = request.POST.get('nik', '').strip() or None
        santri.no_kk = request.POST.get('no_kk', '').strip() or None
        santri.nama_lengkap = request.POST.get('nama_lengkap', '').strip()
        santri.panggilan = request.POST.get('panggilan', '').strip()
        santri.jenis_kelamin = request.POST.get('jenis_kelamin', santri.jenis_kelamin)
        santri.tempat_lahir = request.POST.get('tempat_lahir', '').strip()
        tgl_lahir = request.POST.get('tanggal_lahir')
        santri.tanggal_lahir = tgl_lahir if tgl_lahir else None
        santri.anak_ke = int(request.POST.get('anak_ke') or 1)
        santri.jumlah_saudara = int(request.POST.get('jumlah_saudara') or 1)
        santri.golongan_darah = request.POST.get('golongan_darah', '-')
        santri.riwayat_penyakit = request.POST.get('riwayat_penyakit', '').strip()
        santri.status = request.POST.get('status', santri.status)

        # 2. Alamat Santri
        santri.alamat = request.POST.get('alamat', '').strip()
        santri.desa_kelurahan_santri = request.POST.get('desa_kelurahan_santri', '').strip()
        santri.kecamatan_santri = request.POST.get('kecamatan_santri', '').strip()
        santri.kabupaten_kota_santri = request.POST.get('kabupaten_kota_santri', '').strip()
        santri.provinsi_santri = request.POST.get('provinsi_santri', '').strip()
        santri.kode_pos_santri = request.POST.get('kode_pos_santri', '').strip()

        # 3. Data Ayah
        santri.nama_ayah = request.POST.get('nama_ayah', '').strip()
        santri.nik_ayah = request.POST.get('nik_ayah', '').strip()
        santri.status_ayah = request.POST.get('status_ayah', 'hidup')
        santri.pendidikan_ayah = request.POST.get('pendidikan_ayah', '').strip()
        santri.pekerjaan_ayah = request.POST.get('pekerjaan_ayah', '').strip()
        santri.penghasilan_ayah = request.POST.get('penghasilan_ayah', '').strip()
        santri.telepon_ayah = request.POST.get('telepon_ayah', '').strip()
        santri.alamat_ayah_sama = request.POST.get('alamat_ayah_sama') == 'on'
        santri.alamat_ayah = request.POST.get('alamat_ayah', '').strip()
        santri.desa_kelurahan_ayah = request.POST.get('desa_kelurahan_ayah', '').strip()
        santri.kecamatan_ayah = request.POST.get('kecamatan_ayah', '').strip()
        santri.kabupaten_kota_ayah = request.POST.get('kabupaten_kota_ayah', '').strip()
        santri.provinsi_ayah = request.POST.get('provinsi_ayah', '').strip()
        santri.kode_pos_ayah = request.POST.get('kode_pos_ayah', '').strip()

        # 4. Data Ibu
        santri.nama_ibu = request.POST.get('nama_ibu', '').strip()
        santri.nik_ibu = request.POST.get('nik_ibu', '').strip()
        santri.status_ibu = request.POST.get('status_ibu', 'hidup')
        santri.pendidikan_ibu = request.POST.get('pendidikan_ibu', '').strip()
        santri.pekerjaan_ibu = request.POST.get('pekerjaan_ibu', '').strip()
        santri.penghasilan_ibu = request.POST.get('penghasilan_ibu', '').strip()
        santri.telepon_ibu = request.POST.get('telepon_ibu', '').strip()
        santri.alamat_ibu_sama = request.POST.get('alamat_ibu_sama') == 'on'
        santri.alamat_ibu = request.POST.get('alamat_ibu', '').strip()
        santri.desa_kelurahan_ibu = request.POST.get('desa_kelurahan_ibu', '').strip()
        santri.kecamatan_ibu = request.POST.get('kecamatan_ibu', '').strip()
        santri.kabupaten_kota_ibu = request.POST.get('kabupaten_kota_ibu', '').strip()
        santri.provinsi_ibu = request.POST.get('provinsi_ibu', '').strip()
        santri.kode_pos_ibu = request.POST.get('kode_pos_ibu', '').strip()

        # 5. Data Wali
        santri.hubungan_wali = request.POST.get('hubungan_wali', 'sama_ayah')
        santri.nama_wali = request.POST.get('nama_wali', '').strip()
        santri.nik_wali = request.POST.get('nik_wali', '').strip()
        santri.pekerjaan_wali = request.POST.get('pekerjaan_wali', '').strip()
        santri.penghasilan_wali = request.POST.get('penghasilan_wali', '').strip()
        santri.telepon_wali = request.POST.get('telepon_wali', '').strip()
        santri.alamat_wali_sama = request.POST.get('alamat_wali_sama') == 'on'
        santri.alamat_wali = request.POST.get('alamat_wali', '').strip()
        santri.desa_kelurahan_wali = request.POST.get('desa_kelurahan_wali', '').strip()
        santri.kecamatan_wali = request.POST.get('kecamatan_wali', '').strip()
        santri.kabupaten_kota_wali = request.POST.get('kabupaten_kota_wali', '').strip()
        santri.provinsi_wali = request.POST.get('provinsi_wali', '').strip()
        santri.kode_pos_wali = request.POST.get('kode_pos_wali', '').strip()

        santri.save()

        messages.success(request, f"Perubahan data santri {santri.nama_lengkap} berhasil disimpan.")
        return redirect('santri:santri-detail', uuid=santri.uuid)

    context = {
        'santri': santri,
        'status_choices': Santri.Status.choices,
        'status_hidup_choices': Santri.StatusHidup.choices,
        'hubungan_wali_choices': Santri.HubunganWali.choices,
    }
    return render(request, 'santri/santri_edit.html', context)


@require_POST
def santri_delete(request, uuid):
    """
    Hapus santri jika tidak memiliki relasi transaksi pembayaran yang terkunci.
    """
    santri = get_object_or_404(Santri, uuid=uuid)
    if santri.riwayat_pembayaran.exists():
        messages.error(request, f"Santri {santri.nama_lengkap} tidak dapat dihapus karena sudah memiliki riwayat transaksi pembayaran.")
        return redirect('santri:santri-detail', uuid=santri.uuid)

    nama = santri.nama_lengkap
    santri.delete()
    messages.success(request, f"Data santri {nama} berhasil dihapus.")
    return redirect('santri:santri-list')


# ==========================================
# MASTER TAHUN AJARAN & SEMESTER
# ==========================================

def tahun_ajaran_list(request):
    """
    Daftar Master Tahun Ajaran dengan format Table & Pagination.
    Mendukung pencarian nama tahun ajaran dan filter status aktif.
    """
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    ta_qs = TahunAjaran.objects.prefetch_related('semester_list', 'rombel_list').all().order_by('-tanggal_mulai')

    if search_query:
        ta_qs = ta_qs.filter(nama__icontains=search_query)

    if status_filter == 'aktif':
        ta_qs = ta_qs.filter(is_active=True)
    elif status_filter == 'nonaktif':
        ta_qs = ta_qs.filter(is_active=False)

    paginator = Paginator(ta_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    active_ta = TahunAjaran.objects.filter(is_active=True).first()
    active_semester = Semester.objects.filter(is_active=True).first()

    total_rombel_aktif = active_ta.rombel_list.count() if active_ta else 0
    total_santri_aktif = AnggotaRombel.objects.filter(
        rombel__tahun_ajaran=active_ta,
        status=AnggotaRombel.StatusKeanggotaan.AKTIF
    ).count() if active_ta else 0

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'active_ta': active_ta,
        'active_semester': active_semester,
        'total_rombel_aktif': total_rombel_aktif,
        'total_santri_aktif': total_santri_aktif,
        'total_ta': paginator.count,
    }
    return render(request, 'santri/tahun_ajaran_list.html', context)


def tahun_ajaran_detail(request, uuid):
    """
    Halaman Detail Tahun Ajaran.
    Menampilkan info periode, status aktif, daftar semester, dan daftar rombel di dalamnya.
    Memiliki button edit dan aksi cepat aktivasi/hapus.
    """
    ta = get_object_or_404(TahunAjaran.objects.prefetch_related('semester_list', 'rombel_list'), uuid=uuid)
    rombel_list = ta.rombel_list.select_related('wali_rombel').all()

    total_santri = AnggotaRombel.objects.filter(
        rombel__tahun_ajaran=ta,
        status=AnggotaRombel.StatusKeanggotaan.AKTIF
    ).count()

    context = {
        'ta': ta,
        'rombel_list': rombel_list,
        'total_santri': total_santri,
    }
    return render(request, 'santri/tahun_ajaran_detail.html', context)


def tahun_ajaran_create(request):
    """
    Form penambahan Tahun Ajaran baru.
    Opsi: Otomatis generate semester Ganjil dan Genap.
    """
    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        tanggal_mulai = request.POST.get('tanggal_mulai')
        tanggal_selesai = request.POST.get('tanggal_selesai')
        is_active = request.POST.get('is_active') == 'on'
        auto_semester = request.POST.get('auto_semester') == 'on'

        if not nama or not tanggal_mulai or not tanggal_selesai:
            messages.error(request, "Nama, Tanggal Mulai, dan Tanggal Selesai wajib diisi.")
        elif TahunAjaran.objects.filter(nama=nama).exists():
            messages.error(request, f"Tahun Ajaran '{nama}' sudah terdaftar.")
        else:
            with transaction.atomic():
                ta = TahunAjaran.objects.create(
                    nama=nama,
                    tanggal_mulai=tanggal_mulai,
                    tanggal_selesai=tanggal_selesai,
                    is_active=is_active
                )
                if auto_semester:
                    Semester.objects.create(
                        tahun_ajaran=ta,
                        jenis=Semester.Jenis.GANJIL,
                        is_active=is_active
                    )
                    Semester.objects.create(
                        tahun_ajaran=ta,
                        jenis=Semester.Jenis.GENAP,
                        is_active=False
                    )

            messages.success(request, f"Tahun Ajaran '{ta.nama}' berhasil ditambahkan.")
            return redirect('santri:tahun-ajaran-list')

    return render(request, 'santri/tahun_ajaran_form.html', {'is_edit': False})


def tahun_ajaran_edit(request, uuid):
    """
    Edit data Tahun Ajaran.
    """
    ta = get_object_or_404(TahunAjaran, uuid=uuid)

    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        tanggal_mulai = request.POST.get('tanggal_mulai')
        tanggal_selesai = request.POST.get('tanggal_selesai')
        is_active = request.POST.get('is_active') == 'on'

        if not nama or not tanggal_mulai or not tanggal_selesai:
            messages.error(request, "Semua field wajib diisi.")
        elif TahunAjaran.objects.filter(nama=nama).exclude(id=ta.id).exists():
            messages.error(request, f"Tahun Ajaran '{nama}' sudah digunakan.")
        else:
            ta.nama = nama
            ta.tanggal_mulai = tanggal_mulai
            ta.tanggal_selesai = tanggal_selesai
            ta.is_active = is_active
            ta.save()
            messages.success(request, f"Tahun Ajaran '{ta.nama}' berhasil diperbarui.")
            return redirect('santri:tahun-ajaran-list')

    return render(request, 'santri/tahun_ajaran_form.html', {'ta': ta, 'is_edit': True})


@require_POST
def tahun_ajaran_activate(request, uuid):
    """
    Aktivasi Tahun Ajaran secara instan.
    Model save() otomatis menonaktifkan tahun ajaran lainnya.
    """
    ta = get_object_or_404(TahunAjaran, uuid=uuid)
    ta.is_active = True
    ta.save()

    active_sem_in_ta = ta.semester_list.filter(is_active=True).first()
    if not active_sem_in_ta:
        sem_ganjil = ta.semester_list.filter(jenis=Semester.Jenis.GANJIL).first()
        if sem_ganjil:
            sem_ganjil.is_active = True
            sem_ganjil.save()

    messages.success(request, f"Tahun Ajaran '{ta.nama}' sekarang aktif sebagai kalender akademik utama.")
    return redirect('santri:tahun-ajaran-list')


@require_POST
def tahun_ajaran_delete(request, uuid):
    """
    Hapus Tahun Ajaran jika belum memiliki rombel atau tagihan.
    """
    ta = get_object_or_404(TahunAjaran, uuid=uuid)
    if ta.rombel_list.exists():
        messages.error(request, f"Tidak dapat menghapus '{ta.nama}' karena masih memiliki rombel di dalamnya.")
        return redirect('santri:tahun-ajaran-list')
    if hasattr(ta, 'tagihan_list') and ta.tagihan_list.exists():
        messages.error(request, f"Tidak dapat menghapus '{ta.nama}' karena masih memiliki data tagihan.")
        return redirect('santri:tahun-ajaran-list')

    nama = ta.nama
    ta.delete()
    messages.success(request, f"Tahun Ajaran '{nama}' berhasil dihapus.")
    return redirect('santri:tahun-ajaran-list')


@require_POST
def semester_activate(request, uuid):
    """
    Aktivasi Semester (Ganjil / Genap).
    Otomatis mengaktifkan tahun ajarannya jika belum aktif.
    """
    semester = get_object_or_404(Semester, uuid=uuid)
    semester.is_active = True
    semester.save()

    if not semester.tahun_ajaran.is_active:
        semester.tahun_ajaran.is_active = True
        semester.tahun_ajaran.save()

    messages.success(request, f"Semester '{semester}' berhasil diaktifkan.")
    return redirect('santri:tahun-ajaran-list')


# ==========================================
# ROMBEL & KELAS CRUD & FITUR SALIN
# ==========================================

def rombel_list(request):
    """
    Daftar rombongan belajar (kelas) dengan filter tahun ajaran, pencarian, dan persentase kapasitas.
    """
    ta_filter_uuid = request.GET.get('ta', '').strip()
    search_query = request.GET.get('q', '').strip()
    tingkat_filter = request.GET.get('tingkat', '').strip()

    daftar_ta = TahunAjaran.objects.all().order_by('-tanggal_mulai')
    active_ta = TahunAjaran.objects.filter(is_active=True).first()

    selected_ta = None
    if ta_filter_uuid:
        selected_ta = TahunAjaran.objects.filter(uuid=ta_filter_uuid).first()
    elif active_ta:
        selected_ta = active_ta

    rombel_qs = Rombel.objects.select_related('tahun_ajaran', 'wali_rombel')
    if selected_ta:
        rombel_qs = rombel_qs.filter(tahun_ajaran=selected_ta)

    if search_query:
        rombel_qs = rombel_qs.filter(
            Q(nama__icontains=search_query) |
            Q(wali_rombel__first_name__icontains=search_query) |
            Q(wali_rombel__username__icontains=search_query)
        )

    if tingkat_filter:
        rombel_qs = rombel_qs.filter(tingkat=tingkat_filter)

    paginator = Paginator(rombel_qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'daftar_ta': daftar_ta,
        'selected_ta': selected_ta,
        'active_ta': active_ta,
        'search_query': search_query,
        'tingkat_filter': tingkat_filter,
    }
    return render(request, 'santri/rombel_list.html', context)


def rombel_create(request):
    """
    Tambah Rombongan Belajar baru.
    """
    daftar_ta = TahunAjaran.objects.all().order_by('-tanggal_mulai')
    active_ta = TahunAjaran.objects.filter(is_active=True).first()
    guru_list = User.objects.filter(
        role__in=[User.Role.GURU, User.Role.ADMIN_AKADEMIK, User.Role.SUPERADMIN]
    ).order_by('first_name', 'username')

    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        tingkat = request.POST.get('tingkat', '1')
        ta_uuid = request.POST.get('tahun_ajaran_uuid')
        wali_id = request.POST.get('wali_rombel_id')
        kapasitas = request.POST.get('kapasitas', '30')
        keterangan = request.POST.get('keterangan', '').strip()

        ta = TahunAjaran.objects.filter(uuid=ta_uuid).first()
        if not nama or not ta:
            messages.error(request, "Nama Rombel dan Tahun Ajaran wajib diisi.")
        elif Rombel.objects.filter(nama=nama, tahun_ajaran=ta).exists():
            messages.error(request, f"Rombel dengan nama '{nama}' sudah ada di Tahun Ajaran {ta.nama}.")
        else:
            wali_user = User.objects.filter(id=wali_id).first() if wali_id else None
            rombel = Rombel.objects.create(
                nama=nama,
                tingkat=int(tingkat),
                tahun_ajaran=ta,
                wali_rombel=wali_user,
                kapasitas=int(kapasitas) if kapasitas else 30,
                keterangan=keterangan
            )
            messages.success(request, f"Rombel '{rombel.nama}' berhasil dibuat.")
            return redirect('santri:rombel-detail', uuid=rombel.uuid)

    context = {
        'daftar_ta': daftar_ta,
        'active_ta': active_ta,
        'guru_list': guru_list,
        'is_edit': False,
    }
    return render(request, 'santri/rombel_form.html', context)


def rombel_edit(request, uuid):
    """
    Edit data Rombel.
    """
    rombel = get_object_or_404(Rombel, uuid=uuid)
    daftar_ta = TahunAjaran.objects.all().order_by('-tanggal_mulai')
    guru_list = User.objects.filter(
        role__in=[User.Role.GURU, User.Role.ADMIN_AKADEMIK, User.Role.SUPERADMIN]
    ).order_by('first_name', 'username')

    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        tingkat = request.POST.get('tingkat', rombel.tingkat)
        wali_id = request.POST.get('wali_rombel_id')
        kapasitas = request.POST.get('kapasitas', rombel.kapasitas)
        keterangan = request.POST.get('keterangan', '').strip()

        if not nama:
            messages.error(request, "Nama Rombel wajib diisi.")
        elif Rombel.objects.filter(nama=nama, tahun_ajaran=rombel.tahun_ajaran).exclude(id=rombel.id).exists():
            messages.error(request, f"Nama rombel '{nama}' sudah digunakan di Tahun Ajaran ini.")
        else:
            rombel.nama = nama
            rombel.tingkat = int(tingkat)
            rombel.wali_rombel = User.objects.filter(id=wali_id).first() if wali_id else None
            rombel.kapasitas = int(kapasitas) if kapasitas else 30
            rombel.keterangan = keterangan
            rombel.save()
            messages.success(request, f"Data Rombel '{rombel.nama}' berhasil diperbarui.")
            return redirect('santri:rombel-detail', uuid=rombel.uuid)

    context = {
        'rombel': rombel,
        'daftar_ta': daftar_ta,
        'guru_list': guru_list,
        'is_edit': True,
    }
    return render(request, 'santri/rombel_form.html', context)


@require_POST
def rombel_delete(request, uuid):
    """
    Hapus rombel jika belum memiliki santri aktif.
    """
    rombel = get_object_or_404(Rombel, uuid=uuid)
    santri_count = rombel.anggota_list.filter(status='aktif').count()
    if santri_count > 0:
        messages.error(request, f"Rombel '{rombel.nama}' tidak dapat dihapus karena masih berisi {santri_count} santri aktif.")
        return redirect('santri:rombel-detail', uuid=rombel.uuid)

    nama = rombel.nama
    rombel.delete()
    messages.success(request, f"Rombel '{nama}' berhasil dihapus.")
    return redirect('santri:rombel-list')


def rombel_salin(request):
    """
    Fitur 1-Click Duplikasi Rombel dari Tahun Ajaran Sebelumnya ke Tahun Ajaran Baru.
    Sangat menghemat waktu persiapan tahun ajaran baru bagi administrator.
    """
    daftar_ta = TahunAjaran.objects.all().order_by('-tanggal_mulai')
    active_ta = TahunAjaran.objects.filter(is_active=True).first()

    if request.method == 'POST':
        ta_sumber_uuid = request.POST.get('ta_sumber_uuid')
        ta_tujuan_uuid = request.POST.get('ta_tujuan_uuid')
        salin_wali = request.POST.get('salin_wali') == 'on'

        if not ta_sumber_uuid or not ta_tujuan_uuid:
            messages.error(request, "Pilih Tahun Ajaran Sumber dan Tahun Ajaran Tujuan.")
        elif ta_sumber_uuid == ta_tujuan_uuid:
            messages.error(request, "Tahun Ajaran Sumber dan Tujuan tidak boleh sama.")
        else:
            ta_sumber = get_object_or_404(TahunAjaran, uuid=ta_sumber_uuid)
            ta_tujuan = get_object_or_404(TahunAjaran, uuid=ta_tujuan_uuid)

            rombel_sumber = Rombel.objects.filter(tahun_ajaran=ta_sumber)
            if not rombel_sumber.exists():
                messages.warning(request, f"Tidak ada rombel pada Tahun Ajaran sumber '{ta_sumber.nama}'.")
                return redirect('santri:rombel-salin')

            created_count = 0
            skipped_count = 0
            with transaction.atomic():
                for r in rombel_sumber:
                    if Rombel.objects.filter(nama=r.nama, tahun_ajaran=ta_tujuan).exists():
                        skipped_count += 1
                        continue

                    Rombel.objects.create(
                        nama=r.nama,
                        tingkat=r.tingkat,
                        tahun_ajaran=ta_tujuan,
                        wali_rombel=r.wali_rombel if salin_wali else None,
                        kapasitas=r.kapasitas,
                        keterangan=r.keterangan
                    )
                    created_count += 1

            messages.success(
                request,
                f"Berhasil menyalin {created_count} rombel ke Tahun Ajaran {ta_tujuan.nama} "
                f"({skipped_count} rombel dilewati karena sudah ada)."
            )
            return redirect(f"/santri/rombel/?ta={ta_tujuan.uuid}")

    context = {
        'daftar_ta': daftar_ta,
        'active_ta': active_ta,
    }
    return render(request, 'santri/rombel_salin.html', context)


def rombel_detail(request, uuid):
    """
    Detail rombel: wali kelas, kapasitas, dan daftar santri di dalamnya.
    Santri pada tabel memiliki link langsung ke detail santri,
    serta opsi cepat menambahkan santri belum berkelas ke rombel ini.
    """
    rombel = get_object_or_404(Rombel.objects.select_related('tahun_ajaran', 'wali_rombel'), uuid=uuid)
    anggota_list = rombel.anggota_list.select_related('santri').filter(status='aktif')

    # Cari santri aktif yang belum masuk rombel manapun di tahun ajaran ini
    santri_sudah_di_rombel = AnggotaRombel.objects.filter(
        tahun_ajaran=rombel.tahun_ajaran,
        status='aktif'
    ).values_list('santri_id', flat=True)

    santri_tersedia = Santri.objects.filter(
        status=Santri.Status.AKTIF
    ).exclude(id__in=santri_sudah_di_rombel).order_by('nama_lengkap')[:100]

    return render(request, 'santri/rombel_detail.html', {
        'rombel': rombel,
        'anggota_list': anggota_list,
        'santri_tersedia': santri_tersedia,
    })


@require_POST
def rombel_tambah_anggota(request, uuid):
    """
    Menambahkan santri ke rombel secara langsung dari halaman detail rombel.
    """
    rombel = get_object_or_404(Rombel, uuid=uuid)
    santri_uuid = request.POST.get('santri_uuid')
    santri = get_object_or_404(Santri, uuid=santri_uuid)

    existing = AnggotaRombel.objects.filter(
        santri=santri,
        tahun_ajaran=rombel.tahun_ajaran,
        status=AnggotaRombel.StatusKeanggotaan.AKTIF
    ).first()

    if existing:
        messages.error(request, f"Santri {santri.nama_lengkap} sudah aktif di rombel {existing.rombel.nama} pada TA {rombel.tahun_ajaran.nama}.")
    else:
        AnggotaRombel.objects.create(
            santri=santri,
            rombel=rombel,
            tahun_ajaran=rombel.tahun_ajaran,
            status=AnggotaRombel.StatusKeanggotaan.AKTIF
        )
        messages.success(request, f"Santri {santri.nama_lengkap} berhasil dimasukkan ke rombel {rombel.nama}.")

    return redirect('santri:rombel-detail', uuid=rombel.uuid)


@require_POST
def rombel_keluarkan_anggota(request, uuid, santri_uuid):
    """
    Mengeluarkan santri dari rombel.
    """
    rombel = get_object_or_404(Rombel, uuid=uuid)
    santri = get_object_or_404(Santri, uuid=santri_uuid)

    keanggotaan = AnggotaRombel.objects.filter(
        santri=santri,
        rombel=rombel,
        status=AnggotaRombel.StatusKeanggotaan.AKTIF
    ).first()

    if keanggotaan:
        keanggotaan.delete()
        messages.success(request, f"Santri {santri.nama_lengkap} berhasil dikeluarkan dari {rombel.nama}.")
    else:
        messages.warning(request, "Data keanggotaan aktif tidak ditemukan.")

    return redirect('santri:rombel-detail', uuid=rombel.uuid)


# ==========================================
# KENAIKAN KELAS & KELULUSAN
# ==========================================

def kenaikan_kelas(request):
    """
    Fitur Kenaikan Kelas & Kelulusan Massal.
    Alur:
    1. Pilih Rombel Asal.
    2. Tampilkan seluruh santri aktif dalam rombel tersebut.
    3. Pilih Aksi: 'Naik Kelas ke Rombel Tujuan' ATAU 'Kelulusan Santri'.
    4. Proses batch dalam transaction.atomic().
    """
    rombel_asal_uuid = request.GET.get('rombel_asal')
    selected_rombel_asal = None
    santri_anggota = []

    if rombel_asal_uuid:
        selected_rombel_asal = Rombel.objects.filter(uuid=rombel_asal_uuid).first()
        if selected_rombel_asal:
            santri_anggota = selected_rombel_asal.anggota_list.select_related('santri').filter(status='aktif')

    if request.method == 'POST':
        tipe_proses = request.POST.get('tipe_proses')  # 'kenaikan' atau 'kelulusan'
        santri_ids = request.POST.getlist('santri_ids')
        rombel_tujuan_uuid = request.POST.get('rombel_tujuan_uuid')

        if not santri_ids:
            messages.error(request, "Pilih setidaknya satu santri untuk diproses.")
        elif tipe_proses == 'kenaikan' and not rombel_tujuan_uuid:
            messages.error(request, "Pilih rombel tujuan untuk kenaikan kelas.")
        else:
            with transaction.atomic():
                if tipe_proses == 'kenaikan':
                    rombel_tujuan = get_object_or_404(Rombel, uuid=rombel_tujuan_uuid)
                    count = 0
                    for s_id in santri_ids:
                        santri = Santri.objects.get(id=s_id)
                        AnggotaRombel.objects.filter(santri=santri, status='aktif').update(
                            status=AnggotaRombel.StatusKeanggotaan.NAIK_KELAS
                        )
                        AnggotaRombel.objects.create(
                            santri=santri,
                            rombel=rombel_tujuan,
                            tahun_ajaran=rombel_tujuan.tahun_ajaran,
                            status=AnggotaRombel.StatusKeanggotaan.AKTIF
                        )
                        count += 1
                    messages.success(request, f"Berhasil memindahkan {count} santri ke {rombel_tujuan.nama}.")

                elif tipe_proses == 'kelulusan':
                    count = 0
                    for s_id in santri_ids:
                        santri = Santri.objects.get(id=s_id)
                        santri.status = Santri.Status.LULUS
                        santri.save()
                        AnggotaRombel.objects.filter(santri=santri, status='aktif').update(
                            status=AnggotaRombel.StatusKeanggotaan.LULUS
                        )
                        count += 1
                    messages.success(request, f"Berhasil memproses kelulusan {count} santri menjadi alumni.")

            return redirect('santri:santri-list')

    daftar_rombel = Rombel.objects.select_related('tahun_ajaran').all()
    context = {
        'daftar_rombel': daftar_rombel,
        'selected_rombel_asal': selected_rombel_asal,
        'santri_anggota': santri_anggota,
    }
    return render(request, 'santri/kenaikan_kelas.html', context)
