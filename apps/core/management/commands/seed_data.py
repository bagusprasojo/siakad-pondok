import uuid
from decimal import Decimal
from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.santri.models import TahunAjaran, Semester, Rombel, Santri, AnggotaRombel
from apps.keuangan.models import PosTarif, Tagihan, Pembayaran
from apps.keuangan.services.pembayaran_service import PembayaranService

User = get_user_model()


class Command(BaseCommand):
    help = "Seed initial sample data for SIAKAD Pondok Pesantren"

    def handle(self, *args, **options):
        self.stdout.write("Memulai seeding data awal...")

        # 1. Superuser & Asatidz & Bendahara
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@pesantren.id',
                'role': User.Role.SUPERADMIN,
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Mudir',
                'last_name': 'Pesantren'
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()

        bendahara, _ = User.objects.get_or_create(
            username='bendahara',
            defaults={
                'email': 'keuangan@pesantren.id',
                'role': User.Role.BENDAHARA,
                'is_staff': True,
                'first_name': 'Ust. Fauzan',
                'last_name': 'Bendahara'
            }
        )
        bendahara.set_password('bendahara123')
        bendahara.save()

        ustadz_ahmad, _ = User.objects.get_or_create(
            username='ustadz_ahmad',
            defaults={
                'email': 'ahmad@pesantren.id',
                'role': User.Role.GURU,
                'is_staff': False,
                'first_name': 'Ust. Ahmad',
                'last_name': 'Al-Hafizh'
            }
        )
        ustadz_ahmad.set_password('guru123')
        ustadz_ahmad.save()

        self.stdout.write(self.style.SUCCESS("[OK] User berhasil dibuat: admin (pass: admin123), bendahara (pass: bendahara123)"))

        # 2. Tahun Ajaran & Semester
        ta_2026, _ = TahunAjaran.objects.get_or_create(
            nama='2026/2027',
            defaults={
                'tanggal_mulai': date(2026, 7, 1),
                'tanggal_selesai': date(2027, 6, 30),
                'is_active': True
            }
        )
        sem_ganjil, _ = Semester.objects.get_or_create(
            tahun_ajaran=ta_2026,
            jenis=Semester.Jenis.GANJIL,
            defaults={'is_active': True}
        )
        Semester.objects.get_or_create(
            tahun_ajaran=ta_2026,
            jenis=Semester.Jenis.GENAP,
            defaults={'is_active': False}
        )

        self.stdout.write(self.style.SUCCESS(f"[OK] Tahun Ajaran {ta_2026.nama} & Semester {sem_ganjil.get_jenis_display()} aktif."))

        # 3. Rombel
        rombel_7a, _ = Rombel.objects.get_or_create(
            nama='Kelas 7A (Putra)',
            tahun_ajaran=ta_2026,
            defaults={'tingkat': 7, 'wali_rombel': ustadz_ahmad, 'kapasitas': 30}
        )
        rombel_7b, _ = Rombel.objects.get_or_create(
            nama='Kelas 7B (Putra)',
            tahun_ajaran=ta_2026,
            defaults={'tingkat': 7, 'wali_rombel': ustadz_ahmad, 'kapasitas': 30}
        )
        rombel_8a, _ = Rombel.objects.get_or_create(
            nama='Kelas 8A (Putra)',
            tahun_ajaran=ta_2026,
            defaults={'tingkat': 8, 'kapasitas': 30}
        )
        rombel_9a, _ = Rombel.objects.get_or_create(
            nama='Kelas 9A (Putra)',
            tahun_ajaran=ta_2026,
            defaults={'tingkat': 9, 'kapasitas': 30}
        )

        self.stdout.write(self.style.SUCCESS("[OK] Rombel berhasil dibuat."))

        # 4. Master Data Santri
        santri_list_data = [
            {
                'nis': '2026001',
                'nama': 'Muhammad Alfian Pratama',
                'gender': 'L',
                'ayah': 'Bambang Pratama',
                'hp': '081234567890',
                'rombel': rombel_7a
            },
            {
                'nis': '2026002',
                'nama': 'Ahmad Zaidan Robbani',
                'gender': 'L',
                'ayah': 'Robbani',
                'hp': '081234567891',
                'rombel': rombel_7a
            },
            {
                'nis': '2026003',
                'nama': 'Bilal Fathurrahman',
                'gender': 'L',
                'ayah': 'Fathurrahman',
                'hp': '081234567892',
                'rombel': rombel_7a
            },
            {
                'nis': '2026004',
                'nama': 'Faris Al-Ghifari',
                'gender': 'L',
                'ayah': 'Al-Ghifari',
                'hp': '081234567893',
                'rombel': rombel_7b
            },
            {
                'nis': '2025001',
                'nama': 'Habibie Rahman Hakim',
                'gender': 'L',
                'ayah': 'Lukman Hakim',
                'hp': '081234567894',
                'rombel': rombel_8a
            },
            {
                'nis': '2024001',
                'nama': 'Salman Al-Farisi',
                'gender': 'L',
                'ayah': 'Farisi',
                'hp': '081234567895',
                'rombel': rombel_9a
            },
        ]

        created_santri = []
        for sdata in santri_list_data:
            s, _ = Santri.objects.get_or_create(
                nis=sdata['nis'],
                defaults={
                    'nama_lengkap': sdata['nama'],
                    'jenis_kelamin': sdata['gender'],
                    'nama_ayah': sdata['ayah'],
                    'telepon_wali': sdata['hp'],
                    'status': Santri.Status.AKTIF,
                    'tanggal_masuk': date(2026, 7, 10),
                }
            )
            # Penempatan rombel
            AnggotaRombel.objects.get_or_create(
                santri=s,
                tahun_ajaran=ta_2026,
                defaults={'rombel': sdata['rombel'], 'status': AnggotaRombel.StatusKeanggotaan.AKTIF}
            )
            created_santri.append(s)

        self.stdout.write(self.style.SUCCESS(f"[OK] {len(created_santri)} Santri dan keanggotaan rombel tersimpan."))

        # 5. Pos Tarif Keuangan
        spp_pos, _ = PosTarif.objects.get_or_create(
            kode='SPP',
            defaults={
                'nama': 'SPP / Syahriyah Bulanan',
                'tipe': PosTarif.TipeTagihan.RUTIN,
                'tarif_standar': Decimal('500000.00'),
                'keterangan': 'Iuran operasional bulanan pendidikan dan asrama'
            }
        )
        makan_pos, _ = PosTarif.objects.get_or_create(
            kode='MAKAN',
            defaults={
                'nama': 'Uang Makan Bulanan',
                'tipe': PosTarif.TipeTagihan.RUTIN,
                'tarif_standar': Decimal('450000.00'),
                'keterangan': 'Katering makan santri 3x sehari'
            }
        )
        gedung_pos, _ = PosTarif.objects.get_or_create(
            kode='GEDUNG',
            defaults={
                'nama': 'Infaq Pembangunan Gedung',
                'tipe': PosTarif.TipeTagihan.NON_RUTIN,
                'tarif_standar': Decimal('3000000.00'),
                'keterangan': 'Biaya pembangunan sarana prasarana santri baru'
            }
        )
        seragam_pos, _ = PosTarif.objects.get_or_create(
            kode='SERAGAM',
            defaults={
                'nama': 'Seragam & Perlengkapan',
                'tipe': PosTarif.TipeTagihan.NON_RUTIN,
                'tarif_standar': Decimal('1200000.00'),
                'keterangan': 'Paket seragam santri, peci, sarung, kitab pegangan'
            }
        )

        self.stdout.write(self.style.SUCCESS("[OK] Master Pos Tarif keuangan tersimpan."))

        # 6. Generate Tagihan Contoh
        # Tagihan Rutin SPP Bulan Oktober 2026 untuk santri
        santri1 = created_santri[0]
        santri2 = created_santri[1]

        tagihan1, _ = Tagihan.objects.get_or_create(
            nomor_invoice='INV-202610-SPP-001',
            defaults={
                'santri': santri1,
                'pos_tarif': spp_pos,
                'tahun_ajaran': ta_2026,
                'semester': sem_ganjil,
                'bulan': 10,
                'tahun': 2026,
                'nominal_awal': Decimal('500000.00'),
                'diskon': Decimal('0.00'),
                'total_tagihan': Decimal('500000.00'),
                'sisa_tagihan': Decimal('500000.00'),
                'status': Tagihan.Status.BELUM_BAYAR,
                'tanggal_jatuh_tempo': date(2026, 10, 15)
            }
        )

        tagihan2, _ = Tagihan.objects.get_or_create(
            nomor_invoice='INV-202610-SPP-002',
            defaults={
                'santri': santri2,
                'pos_tarif': spp_pos,
                'tahun_ajaran': ta_2026,
                'semester': sem_ganjil,
                'bulan': 10,
                'tahun': 2026,
                'nominal_awal': Decimal('500000.00'),
                'diskon': Decimal('0.00'),
                'total_tagihan': Decimal('500000.00'),
                'sisa_tagihan': Decimal('500000.00'),
                'status': Tagihan.Status.BELUM_BAYAR,
                'tanggal_jatuh_tempo': date(2026, 10, 15)
            }
        )

        # Tagihan Non-Rutin Gedung untuk Santri 1
        tagihan_gedung, _ = Tagihan.objects.get_or_create(
            nomor_invoice='INV-2026-GDG-001',
            defaults={
                'santri': santri1,
                'pos_tarif': gedung_pos,
                'tahun_ajaran': ta_2026,
                'semester': sem_ganjil,
                'nominal_awal': Decimal('3000000.00'),
                'diskon': Decimal('0.00'),
                'total_tagihan': Decimal('3000000.00'),
                'sisa_tagihan': Decimal('3000000.00'),
                'status': Tagihan.Status.BELUM_BAYAR,
                'tanggal_jatuh_tempo': date(2026, 12, 31)
            }
        )

        # 7. Pembayaran Contoh dengan Service Layer (Anti Race Condition & Idempotent)
        if tagihan1.status == Tagihan.Status.BELUM_BAYAR:
            idempotency_sample_1 = str(uuid.uuid4())
            pembayaran1, is_new1 = PembayaranService.proses_pembayaran(
                tagihan_id_or_uuid=tagihan1.id,
                nominal=Decimal('500000.00'),
                metode_pembayaran=Pembayaran.MetodePembayaran.TUNAI,
                petugas=bendahara,
                idempotency_key=idempotency_sample_1,
                catatan="Pembayaran tunai SPP Oktober lunas di kasir"
            )
            self.stdout.write(self.style.SUCCESS(f"[OK] Pembayaran berhasil dicatat: {pembayaran1.nomor_bukti} (Lunas)"))

        # Cicilan Gedung untuk Santri 1
        if tagihan_gedung.sisa_tagihan == Decimal('3000000.00'):
            idempotency_sample_2 = str(uuid.uuid4())
            pembayaran2, is_new2 = PembayaranService.proses_pembayaran(
                tagihan_id_or_uuid=tagihan_gedung.id,
                nominal=Decimal('1000000.00'),
                metode_pembayaran=Pembayaran.MetodePembayaran.TRANSFER,
                petugas=bendahara,
                idempotency_key=idempotency_sample_2,
                catatan="Cicilan ke-1 Infaq Pembangunan transfer BSI"
            )
            self.stdout.write(self.style.SUCCESS(f"[OK] Cicilan berhasil dicatat: {pembayaran2.nomor_bukti} (Sisa: Rp {tagihan_gedung.sisa_tagihan:,.0f})"))

        self.stdout.write(self.style.SUCCESS("--- SEEDING SELESAI DENGAN SUKSES ---"))
