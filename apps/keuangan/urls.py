from django.urls import path
from . import views

app_name = 'keuangan'

urlpatterns = [
    # Transaksi Pembayaran
    path('pembayaran/', views.pembayaran_list, name='pembayaran-list'),
    path('pembayaran/tambah/', views.pembayaran_create, name='pembayaran-create'),
    path('pembayaran/<uuid:uuid>/', views.pembayaran_detail, name='pembayaran-detail'),
    path('pembayaran/<uuid:uuid>/edit/', views.pembayaran_edit, name='pembayaran-edit'),
    path('pembayaran/<uuid:uuid>/hapus/', views.pembayaran_delete, name='pembayaran-delete'),

    # Tagihan & SPP
    path('tagihan/', views.tagihan_list, name='tagihan-list'),
    path('tagihan/<uuid:uuid>/', views.tagihan_detail, name='tagihan-detail'),

    # Laporan
    path('laporan/', views.laporan_keuangan, name='laporan-keuangan'),
]
