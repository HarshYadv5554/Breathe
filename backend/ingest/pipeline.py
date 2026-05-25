from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from core.models import (
    ActivityAuditLog,
    DataSource,
    EmissionActivity,
    IngestionBatch,
    PlantLookup,
    RawRecord,
)
from ingest.parsers import PARSERS


def _plant_lookup_dict(organization_id: int) -> dict:
    return {
        p.plant_code: p.site_name
        for p in PlantLookup.objects.filter(organization_id=organization_id)
    }


@transaction.atomic
def run_ingestion(batch: IngestionBatch, file_content: str) -> IngestionBatch:
    batch.status = IngestionBatch.Status.PROCESSING
    batch.save(update_fields=["status"])

    source_type = batch.data_source.source_type
    parser = PARSERS.get(source_type)
    if not parser:
        batch.status = IngestionBatch.Status.FAILED
        batch.error_summary = f"No parser for source type: {source_type}"
        batch.completed_at = timezone.now()
        batch.save()
        return batch

    kwargs = {}
    if source_type == "sap_mm":
        kwargs["plant_lookup"] = _plant_lookup_dict(batch.organization_id)

    try:
        parsed_rows = parser(file_content, **kwargs)
    except Exception as exc:
        batch.status = IngestionBatch.Status.FAILED
        batch.error_summary = str(exc)
        batch.completed_at = timezone.now()
        batch.save()
        return batch

    batch.row_count = len(parsed_rows)
    success = error = warning = 0

    for item in parsed_rows:
        raw = RawRecord.objects.create(
            batch=batch,
            row_number=item["row_number"],
            raw_payload=item["raw_payload"],
            parse_errors=item.get("parse_errors", []),
        )

        norm = item.get("normalized", {})
        if item.get("parse_errors") or not norm.get("activity_date"):
            error += 1
            if not norm.get("activity_date"):
                raw.parse_errors = list(raw.parse_errors) + ["Missing activity date after normalization"]
                raw.save(update_fields=["parse_errors"])
            continue

        flags = norm.get("suspicion_flags", [])
        if flags:
            warning += 1

        review_status = EmissionActivity.ReviewStatus.FLAGGED if flags else EmissionActivity.ReviewStatus.PENDING

        activity = EmissionActivity.objects.create(
            organization=batch.organization,
            batch=batch,
            raw_record=raw,
            data_source=batch.data_source,
            scope=norm["scope"],
            category=norm["category"],
            subcategory=norm.get("subcategory", ""),
            activity_date=norm["activity_date"],
            period_start=norm.get("period_start"),
            period_end=norm.get("period_end"),
            site_name=norm.get("site_name", ""),
            plant_code=norm.get("plant_code", ""),
            vendor_or_carrier=norm.get("vendor_or_carrier", ""),
            description=norm.get("description", ""),
            quantity_raw=Decimal(norm["quantity_raw"]) if norm.get("quantity_raw") else None,
            unit_raw=norm.get("unit_raw", ""),
            quantity_normalized=Decimal(norm.get("quantity_normalized", "0")),
            unit_normalized=norm.get("unit_normalized", ""),
            source_reference=norm.get("source_reference", ""),
            source_row_hash=norm.get("source_row_hash", ""),
            review_status=review_status,
            suspicion_flags=flags,
        )

        ActivityAuditLog.objects.create(
            activity=activity,
            user=batch.uploaded_by,
            action=ActivityAuditLog.Action.CREATED,
            note=f"Ingested from {batch.filename}",
        )
        success += 1

    batch.success_count = success
    batch.error_count = error
    batch.warning_count = warning
    batch.status = IngestionBatch.Status.COMPLETED
    batch.completed_at = timezone.now()
    batch.save()
    return batch
