"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from forensic import views


urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "",
        views.home,
        name="home"
    ),

    path(
        "upload/",
        views.upload_image,
        name="upload_image"
    ),

    path(
        "analyze/<int:image_id>/",
        views.analyze_image,
        name="analyze_image"
    ),

    path(
        "report/<int:image_id>/",
        views.download_report,
        name="download_report"
    ),
]


# Serve uploaded media files
urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)