from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import DataSource, IngestionBatch
from core.permissions import IsOrgMember
from core.serializers import IngestionBatchSerializer
from ingest.pipeline import run_ingestion


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOrgMember])
def upload_view(request, org_id, source_id):
    try:
        data_source = DataSource.objects.get(pk=source_id, organization_id=org_id)
    except DataSource.DoesNotExist:
        return Response({"detail": "Source not found"}, status=status.HTTP_404_NOT_FOUND)

    uploaded = request.FILES.get("file")
    if not uploaded:
        return Response({"detail": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

    content = uploaded.read().decode("utf-8-sig", errors="replace")

    batch = IngestionBatch.objects.create(
        organization_id=org_id,
        data_source=data_source,
        uploaded_by=request.user,
        filename=uploaded.name,
        status=IngestionBatch.Status.PENDING,
    )

    run_ingestion(batch, content)
    batch.refresh_from_db()
    return Response(IngestionBatchSerializer(batch).data, status=status.HTTP_201_CREATED)
