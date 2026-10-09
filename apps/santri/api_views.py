from rest_framework import viewsets, filters
from apps.santri.models import Santri, Rombel
from .serializers import SantriSerializer, RombelSerializer


class SantriViewSet(viewsets.ReadOnlyModelViewSet):
    """
    REST API ViewSet untuk Santri (Mobile App Ready).
    Menggunakan uuid sebagai parameter pencarian publik.
    """
    queryset = Santri.objects.all()
    serializer_class = SantriSerializer
    lookup_field = 'uuid'
    filter_backends = [filters.SearchFilter]
    search_fields = ['nis', 'nama_lengkap', 'telepon_wali']


class RombelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Rombel.objects.select_related('wali_rombel').all()
    serializer_class = RombelSerializer
    lookup_field = 'uuid'
