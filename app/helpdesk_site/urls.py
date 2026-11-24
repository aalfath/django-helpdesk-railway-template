from django.conf import settings
from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.cache import never_cache


@never_cache
def healthz(request):
    """Unauthenticated health check for Railway: the app is up and Postgres answers."""
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except Exception:
        return JsonResponse({"status": "error", "database": "unreachable"}, status=503)
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz", healthz),
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("", include("helpdesk.urls", namespace="helpdesk")),
]

if settings.STORAGES["default"]["BACKEND"].endswith("FileSystemStorage"):
    # Local-disk fallback only (no bucket configured): serve uploads as downloads.
    from django.views.static import serve as _serve
    from django.urls import re_path

    def _download(request, path, document_root=None):
        resp = _serve(request, path, document_root=document_root)
        resp["Content-Disposition"] = "attachment"
        resp["X-Content-Type-Options"] = "nosniff"
        return resp

    urlpatterns.insert(1, re_path(r"^media/(?P<path>.*)$", _download, {"document_root": settings.MEDIA_ROOT}))
