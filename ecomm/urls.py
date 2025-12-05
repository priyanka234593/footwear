from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [

    # ---------- API ROUTES (PUT THESE FIRST) ----------
    path("api/accounts/", include("accounts.api.urls")),  # <-- Now Django sees it

    # ---------- FRONTEND AUTH ROUTES ----------
    path("accounts/", include("accounts.urls")),          # custom auth
    path("accounts/social/", include("allauth.urls")),    # Renamed to avoid conflict

    # ---------- WEBSITE ----------
    path("", include("home.urls")),
    path("product/", include("products.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()

