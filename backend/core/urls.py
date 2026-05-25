from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DataSourceViewSet,
    EmissionActivityViewSet,
    IngestionBatchViewSet,
    PlantLookupViewSet,
    dashboard_view,
    login_view,
    me_view,
)

router = DefaultRouter()
router.register(r"orgs/(?P<org_id>\d+)/sources", DataSourceViewSet, basename="sources")
router.register(r"orgs/(?P<org_id>\d+)/plants", PlantLookupViewSet, basename="plants")
router.register(r"orgs/(?P<org_id>\d+)/batches", IngestionBatchViewSet, basename="batches")
router.register(r"orgs/(?P<org_id>\d+)/activities", EmissionActivityViewSet, basename="activities")

urlpatterns = [
    path("auth/login/", login_view),
    path("auth/me/", me_view),
    path("orgs/<int:org_id>/dashboard/", dashboard_view),
    path("", include(router.urls)),
]
