from django.urls import path

from .views import upload_view

urlpatterns = [
    path(
        "orgs/<int:org_id>/sources/<int:source_id>/upload/",
        upload_view,
        name="ingest-upload",
    ),
]
