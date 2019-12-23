from django.contrib import admin
from django.conf import settings
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    # Serve media from development server
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_URL)
