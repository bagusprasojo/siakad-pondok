import uuid
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.keuangan.models import Tagihan, Pembayaran


class PembayaranService:
    """
    Service Layer untuk mengelola transaksi pembayaran.
    Menjamin:
    1. Idempotency: Menolak/mengembalikan transaksi yang sudah ada bila idempotency_key berulang.
    2. Anti Race Condition: Menggunakan Pessimistic Locking (select_for_update) dalam transaction.atomic().
    3. Konsistensi Sisa Tagihan dan Status Tagihan.
    """

    @classmethod
    def generate_nomor_kuitansi(cls):
        now = timezone.now()
        prefix = f"KWT-{now.strftime('%Y%m')}-"
        last_payment = Pembayaran.objects.filter(nomor_bukti__startswith=prefix).order_by('-id').first()
        if last_payment:
            try:
                last_number = int(last_payment.nomor_bukti.split('-')[-1])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1
        return f"{prefix}{new_number:04d}"

    @classmethod
    def proses_pembayaran(cls, tagihan_id_or_uuid, nominal, metode_pembayaran, petugas, idempotency_key, catatan=""):
        nominal = Decimal(str(nominal))
        if nominal <= Decimal('0.00'):
            raise ValidationError("Nominal pembayaran harus lebih besar dari 0.")

        if not idempotency_key:
            raise ValidationError("Idempotency key wajib disertakan.")

        # IDEMPOTENCY CHECK: Cek apakah request dengan key ini sudah pernah sukses
        existing = Pembayaran.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing, False  # Return existing payment, is_new=False

        # EKSEKUSI TRANSAKSI ATOMIK DENGAN ROW-LEVEL LOCK
        with transaction.atomic():
            # Kunci baris Tagihan di level database (MySQL InnoDB)
            query = Tagihan.objects.select_for_update()
            if isinstance(tagihan_id_or_uuid, uuid.UUID) or (isinstance(tagihan_id_or_uuid, str) and len(str(tagihan_id_or_uuid)) == 36):
                tagihan = query.get(uuid=tagihan_id_or_uuid)
            else:
                tagihan = query.get(id=tagihan_id_or_uuid)

            if tagihan.status == Tagihan.Status.LUNAS:
                raise ValidationError("Tagihan ini sudah lunas.")

            if tagihan.status == Tagihan.Status.BATAL:
                raise ValidationError("Tagihan ini telah dibatalkan.")

            if nominal > tagihan.sisa_tagihan:
                raise ValidationError(f"Nominal pembayaran (Rp {nominal:,.0f}) melebihi sisa tagihan (Rp {tagihan.sisa_tagihan:,.0f}).")

            nomor_kuitansi = cls.generate_nomor_kuitansi()

            # Buat record pembayaran
            pembayaran = Pembayaran.objects.create(
                nomor_bukti=nomor_kuitansi,
                idempotency_key=idempotency_key,
                santri=tagihan.santri,
                tagihan=tagihan,
                nominal=nominal,
                metode_pembayaran=metode_pembayaran,
                petugas=petugas,
                catatan=catatan
            )

            # Update tagihan
            tagihan.total_terbayar += nominal
            tagihan.sisa_tagihan -= nominal

            if tagihan.sisa_tagihan == Decimal('0.00'):
                tagihan.status = Tagihan.Status.LUNAS
            else:
                tagihan.status = Tagihan.Status.SEBAGIAN

            tagihan.save()

            return pembayaran, True
