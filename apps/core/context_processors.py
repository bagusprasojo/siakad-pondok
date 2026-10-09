from apps.santri.models import TahunAjaran, Semester


def academic_context(request):
    """
    Context processor global untuk menyediakan informasi Tahun Ajaran & Semester aktif
    ke seluruh template SIAKAD Pesantren.
    """
    try:
        active_ta = TahunAjaran.objects.filter(is_active=True).first()
        active_semester = Semester.objects.filter(is_active=True).first()
    except Exception:
        active_ta = None
        active_semester = None

    return {
        'global_active_ta': active_ta,
        'global_active_semester': active_semester,
    }
