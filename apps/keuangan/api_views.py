from rest_framework import viewsets, status
from rest_framework.response import Response
from apps.keuangan.models import Tagihan, Pembayaran, PosTarif
from .serializers import TagihanSerializer, PembayaranSerializer, PosTarifSerializer
from apps.keuangan.services.pembayaran_service import PembayaranService


class TagihanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    REST API Tagihan (Mobile App Ready).
    """
    queryset = Tagihan.objects.select_related('santri', 'pos_tarif').all()
    serializer_class = TagihanSerializer
    lookup_field = 'uuid'


class PembayaranViewSet(viewsets.ModelViewSet):
    """
    REST API Transaksi Pembayaran.
    Mendukung Header X-Idempotency-Key untuk mobile clients.
    """
    queryset = Pembayaran.objects.select_related('santri', 'tagihan', 'petugas').all()
    serializer_class = PembayaranSerializer
    lookup_field = 'uuid'

    def create(self, request, *args, **kwargs):
        idempotency_key = request.headers.get('X-Idempotency-Key') or request.data.get('idempotency_key')
        tagihan_uuid = request.data.get('tagihan_uuid')
        nominal = request.data.get('nominal')
        metode = request.data.get('metode_pembayaran', Pembayaran.MetodePembayaran.TRANSFER)
        catatan = request.data.get('catatan', '')

        if not idempotency_key or not tagihan_uuid or not nominal:
            return Response(
                {'error': 'idempotency_key, tagihan_uuid, dan nominal wajib disertakan.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            petugas = request.user if request.user.is_authenticated else None
            pembayaran, is_new = PembayaranService.proses_pembayaran(
                tagihan_id_or_uuid=tagihan_uuid,
                nominal=nominal,
                metode_pembayaran=metode,
                petugas=petugas,
                idempotency_key=idempotency_key,
                catatan=catatan
            )
            serializer = self.get_serializer(pembayaran)
            http_status = status.HTTP_201_CREATED if is_new else status.HTTP_200_OK
            return Response(serializer.data, status=http_status)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
