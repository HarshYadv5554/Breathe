from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("api/", include("ingest.urls")),
]

if (settings.BASE_DIR.parent / "frontend" / "dist" / "index.html").exists():
    urlpatterns += [
        re_path(
            r"^(?!api/|admin/|static/).*$",
            TemplateView.as_view(template_name="index.html"),
            name="frontend",
        ),
    ]
