from rest_framework.routers import DefaultRouter
from apps.santri.api_views import SantriViewSet, RombelViewSet
from apps.keuangan.api_views import TagihanViewSet, PembayaranViewSet

router = DefaultRouter()
router.register(r'santri', SantriViewSet, basename='api-santri')
router.register(r'rombel', RombelViewSet, basename='api-rombel')
router.register(r'tagihan', TagihanViewSet, basename='api-tagihan')
router.register(r'pembayaran', PembayaranViewSet, basename='api-pembayaran')

urlpatterns = router.urls
