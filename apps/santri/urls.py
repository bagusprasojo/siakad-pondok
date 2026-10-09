from django.urls import path
from . import views

app_name = 'santri'

urlpatterns = [
    # Master Kalender Akademik (Tahun Ajaran & Semester)
    path('tahun-ajaran/', views.tahun_ajaran_list, name='tahun-ajaran-list'),
    path('tahun-ajaran/tambah/', views.tahun_ajaran_create, name='tahun-ajaran-create'),
    path('tahun-ajaran/<uuid:uuid>/', views.tahun_ajaran_detail, name='tahun-ajaran-detail'),
    path('tahun-ajaran/<uuid:uuid>/edit/', views.tahun_ajaran_edit, name='tahun-ajaran-edit'),
    path('tahun-ajaran/<uuid:uuid>/aktifkan/', views.tahun_ajaran_activate, name='tahun-ajaran-activate'),
    path('tahun-ajaran/<uuid:uuid>/hapus/', views.tahun_ajaran_delete, name='tahun-ajaran-delete'),
    path('semester/<uuid:uuid>/aktifkan/', views.semester_activate, name='semester-activate'),

    # Data Santri
    path('', views.santri_list, name='santri-list'),
    path('tambah/', views.santri_create, name='santri-create'),
    path('<uuid:uuid>/', views.santri_detail, name='santri-detail'),
    path('<uuid:uuid>/edit/', views.santri_edit, name='santri-edit'),
    path('<uuid:uuid>/hapus/', views.santri_delete, name='santri-delete'),

    # Rombongan Belajar (Rombel / Kelas)
    path('rombel/', views.rombel_list, name='rombel-list'),
    path('rombel/tambah/', views.rombel_create, name='rombel-create'),
    path('rombel/salin/', views.rombel_salin, name='rombel-salin'),
    path('rombel/<uuid:uuid>/', views.rombel_detail, name='rombel-detail'),
    path('rombel/<uuid:uuid>/edit/', views.rombel_edit, name='rombel-edit'),
    path('rombel/<uuid:uuid>/hapus/', views.rombel_delete, name='rombel-delete'),
    path('rombel/<uuid:uuid>/tambah-anggota/', views.rombel_tambah_anggota, name='rombel-tambah-anggota'),
    path('rombel/<uuid:uuid>/keluarkan-anggota/<uuid:santri_uuid>/', views.rombel_keluarkan_anggota, name='rombel-keluarkan-anggota'),

    # Kenaikan Kelas & Kelulusan
    path('kenaikan-kelas/', views.kenaikan_kelas, name='kenaikan-kelas'),
]
