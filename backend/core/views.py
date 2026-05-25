from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    ActivityAuditLog,
    DataSource,
    EmissionActivity,
    IngestionBatch,
    Organization,
    OrganizationMembership,
    PlantLookup,
)
from .permissions import IsOrgMember
from .serializers import (
    ActivityAuditLogSerializer,
    DashboardStatsSerializer,
    DataSourceSerializer,
    EmissionActivitySerializer,
    EmissionActivityUpdateSerializer,
    IngestionBatchSerializer,
    OrganizationSerializer,
    PlantLookupSerializer,
    UserSerializer,
)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(username=username, password=password)
    if not user:
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    token, _ = Token.objects.get_or_create(user=user)
    orgs = Organization.objects.filter(
        id__in=OrganizationMembership.objects.filter(user=user).values_list(
            "organization_id", flat=True
        )
    )
    return Response(
        {
            "token": token.key,
            "user": UserSerializer(user).data,
            "organizations": OrganizationSerializer(orgs, many=True).data,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    orgs = Organization.objects.filter(
        id__in=OrganizationMembership.objects.filter(user=request.user).values_list(
            "organization_id", flat=True
        )
    )
    return Response(
        {
            "user": UserSerializer(request.user).data,
            "organizations": OrganizationSerializer(orgs, many=True).data,
        }
    )


class OrgScopedViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsOrgMember]

    def get_org(self):
        return Organization.objects.get(pk=self.kwargs["org_id"])

    def get_queryset(self):
        return self.queryset.filter(organization_id=self.kwargs["org_id"])


class DataSourceViewSet(OrgScopedViewSet):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer


class PlantLookupViewSet(OrgScopedViewSet):
    queryset = PlantLookup.objects.all()
    serializer_class = PlantLookupSerializer


class IngestionBatchViewSet(OrgScopedViewSet):
    queryset = IngestionBatch.objects.select_related("data_source").all()
    serializer_class = IngestionBatchSerializer


class EmissionActivityViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOrgMember]
    serializer_class = EmissionActivitySerializer

    def get_queryset(self):
        qs = EmissionActivity.objects.filter(
            organization_id=self.kwargs["org_id"]
        ).select_related("data_source", "batch", "reviewed_by").prefetch_related("audit_logs")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(review_status=status_filter)
        scope = self.request.query_params.get("scope")
        if scope:
            qs = qs.filter(scope=scope)
        source = self.request.query_params.get("source")
        if source:
            qs = qs.filter(data_source__source_type=source)
        flagged = self.request.query_params.get("flagged")
        if flagged == "true":
            qs = qs.exclude(suspicion_flags=[])
        return qs

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return EmissionActivityUpdateSerializer
        return EmissionActivitySerializer

    def _log(self, activity, action, field_changes=None, note=""):
        ActivityAuditLog.objects.create(
            activity=activity,
            user=self.request.user,
            action=action,
            field_changes=field_changes or {},
            note=note,
        )

    def partial_update(self, request, *args, **kwargs):
        activity = self.get_object()
        if activity.review_status == EmissionActivity.ReviewStatus.LOCKED:
            return Response(
                {"detail": "Locked rows cannot be edited"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = EmissionActivityUpdateSerializer(activity, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        changes = {}
        for field, new_val in serializer.validated_data.items():
            old_val = getattr(activity, field)
            if str(old_val) != str(new_val):
                changes[field] = {"old": str(old_val), "new": str(new_val)}
        serializer.save(is_edited=True)
        if changes:
            self._log(activity, ActivityAuditLog.Action.EDITED, field_changes=changes)
        return Response(EmissionActivitySerializer(activity).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, org_id=None, pk=None):
        activity = self.get_object()
        if activity.review_status == EmissionActivity.ReviewStatus.LOCKED:
            return Response({"detail": "Already locked"}, status=status.HTTP_400_BAD_REQUEST)
        activity.review_status = EmissionActivity.ReviewStatus.APPROVED
        activity.reviewed_by = request.user
        activity.reviewed_at = timezone.now()
        activity.save()
        self._log(activity, ActivityAuditLog.Action.APPROVED, note=request.data.get("note", ""))
        return Response(EmissionActivitySerializer(activity).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, org_id=None, pk=None):
        activity = self.get_object()
        if activity.review_status == EmissionActivity.ReviewStatus.LOCKED:
            return Response({"detail": "Already locked"}, status=status.HTTP_400_BAD_REQUEST)
        activity.review_status = EmissionActivity.ReviewStatus.REJECTED
        activity.reviewed_by = request.user
        activity.reviewed_at = timezone.now()
        if request.data.get("note"):
            activity.analyst_notes = request.data["note"]
        activity.save()
        self._log(activity, ActivityAuditLog.Action.REJECTED, note=request.data.get("note", ""))
        return Response(EmissionActivitySerializer(activity).data)

    @action(detail=True, methods=["post"])
    def flag(self, request, org_id=None, pk=None):
        activity = self.get_object()
        activity.review_status = EmissionActivity.ReviewStatus.FLAGGED
        activity.save()
        self._log(activity, ActivityAuditLog.Action.FLAGGED, note=request.data.get("note", ""))
        return Response(EmissionActivitySerializer(activity).data)

    @action(detail=True, methods=["post"])
    def lock(self, request, org_id=None, pk=None):
        activity = self.get_object()
        if activity.review_status != EmissionActivity.ReviewStatus.APPROVED:
            return Response(
                {"detail": "Only approved rows can be locked for audit"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        activity.review_status = EmissionActivity.ReviewStatus.LOCKED
        activity.locked_at = timezone.now()
        activity.save()
        self._log(activity, ActivityAuditLog.Action.LOCKED)
        return Response(EmissionActivitySerializer(activity).data)

    @action(detail=False, methods=["post"])
    def bulk_approve(self, request, org_id=None):
        ids = request.data.get("ids", [])
        updated = 0
        for activity in self.get_queryset().filter(
            id__in=ids,
            review_status__in=[
                EmissionActivity.ReviewStatus.PENDING,
                EmissionActivity.ReviewStatus.FLAGGED,
            ],
        ):
            activity.review_status = EmissionActivity.ReviewStatus.APPROVED
            activity.reviewed_by = request.user
            activity.reviewed_at = timezone.now()
            activity.save()
            self._log(activity, ActivityAuditLog.Action.APPROVED, note="Bulk approve")
            updated += 1
        return Response({"updated": updated})


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOrgMember])
def dashboard_view(request, org_id):
    org_qs = EmissionActivity.objects.filter(organization_id=org_id)
    data = {
        "total_activities": org_qs.count(),
        "pending_review": org_qs.filter(review_status="pending").count(),
        "flagged": org_qs.filter(review_status="flagged").count(),
        "approved": org_qs.filter(review_status="approved").count(),
        "locked": org_qs.filter(review_status="locked").count(),
        "failed_batches": IngestionBatch.objects.filter(
            organization_id=org_id, status="failed"
        ).count(),
        "recent_batches": IngestionBatch.objects.filter(organization_id=org_id)[:10],
    }
    return Response(DashboardStatsSerializer(data).data)
